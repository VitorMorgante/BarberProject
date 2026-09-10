from datetime import date, timedelta
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from website.models import Cliente, Servico, Agendamento, PlanoAssinatura, AssinaturaCliente, MovimentacaoCredito


class ConsumoResultado(int):
    """
    Representa o resultado do consumo de assinatura.
    Permite uso tanto como booleano simples (compatibilidade retroativa)
    quanto desempacotamento de tupla (sucesso, valor_abatido).
    """
    def __new__(cls, sucesso: bool, valor_abatido: Decimal = Decimal('0.00')):
        obj = super().__new__(cls, 1 if sucesso else 0)
        obj.sucesso = bool(sucesso)
        obj.valor_abatido = valor_abatido
        return obj

    def __bool__(self):
        return self.sucesso

    def __iter__(self):
        return iter((self.sucesso, self.valor_abatido))


class SubscriptionService:
    @staticmethod
    @transaction.atomic
    def solicitar_assinatura(cliente: Cliente, plano: PlanoAssinatura) -> AssinaturaCliente:
        """
        Registra solicitação de assinatura na área do cliente com status Pendente.
        NÃO concede créditos imediatos antes da confirmação de pagamento/administrativa.
        """
        hoje = timezone.now().date()
        validade = timedelta(days=plano.validade_dias or 30)
        proxima_renovacao = hoje + validade

        assinatura, created = AssinaturaCliente.objects.select_for_update().get_or_create(
            cliente=cliente,
            defaults={
                'plano': plano,
                'status': AssinaturaCliente.Status.PENDENTE,
                'data_inicio': hoje,
                'data_renovacao': proxima_renovacao,
                'creditos_disponiveis': 0,
                'creditos_utilizados': 0,
            }
        )
        if not created:
            assinatura.plano = plano
            assinatura.status = AssinaturaCliente.Status.PENDENTE
            assinatura.data_renovacao = proxima_renovacao
            assinatura.creditos_disponiveis = 0
            assinatura.save()

        return assinatura

    @staticmethod
    @transaction.atomic
    def ativar_ou_renovar_assinatura(cliente: Cliente, plano: PlanoAssinatura) -> AssinaturaCliente:
        """
        Ativa ou renova a assinatura de um cliente no Barber Club após confirmação.
        Gera os créditos correspondentes e registra no histórico.
        """
        hoje = timezone.now().date()
        validade = timedelta(days=plano.validade_dias or 30)
        proxima_renovacao = hoje + validade

        is_ilimitado = (plano.modalidade == PlanoAssinatura.Modalidade.ILIMITADO)
        creditos_iniciais = 9999 if is_ilimitado else (plano.limite_mensal or 4)

        assinatura, created = AssinaturaCliente.objects.select_for_update().get_or_create(
            cliente=cliente,
            defaults={
                'plano': plano,
                'status': AssinaturaCliente.Status.ATIVA,
                'data_inicio': hoje,
                'data_renovacao': proxima_renovacao,
                'creditos_disponiveis': creditos_iniciais,
                'creditos_utilizados': 0,
            }
        )

        if not created:
            saldo_ant = assinatura.creditos_disponiveis
            assinatura.plano = plano
            assinatura.status = AssinaturaCliente.Status.ATIVA
            assinatura.data_renovacao = proxima_renovacao

            if is_ilimitado:
                novo_saldo = 9999
            elif plano.permite_acumular:
                novo_saldo = saldo_ant + creditos_iniciais
            else:
                novo_saldo = creditos_iniciais

            assinatura.creditos_disponiveis = novo_saldo
            assinatura.save()

            MovimentacaoCredito.objects.create(
                assinatura=assinatura,
                tipo=MovimentacaoCredito.Tipo.CREDITO_MENSAL,
                quantidade=creditos_iniciais,
                saldo_anterior=saldo_ant,
                saldo_posterior=novo_saldo,
                descricao=f"Ativação/Renovação de plano: {plano.nome}"
            )
        else:
            MovimentacaoCredito.objects.create(
                assinatura=assinatura,
                tipo=MovimentacaoCredito.Tipo.CREDITO_MENSAL,
                quantidade=creditos_iniciais,
                saldo_anterior=0,
                saldo_posterior=creditos_iniciais,
                descricao=f"Adesão inicial ao Barber Club: {plano.nome}"
            )

        return assinatura

    @staticmethod
    @transaction.atomic
    def consumir_credito(cliente: Cliente, servico: Servico = None, agendamento: Agendamento = None, itens_servicos: list = None):
        """
        Verifica se o cliente tem assinatura ativa compatível com o(s) serviço(s) e debita 1 atendimento/visita atomicamente.
        Retorna ConsumoResultado (comporta-se como bool e permite desempacotamento de tupla).
        """
        assinatura = AssinaturaCliente.objects.select_for_update().filter(
            cliente=cliente,
            status=AssinaturaCliente.Status.ATIVA,
        ).first()

        if not assinatura:
            return ConsumoResultado(False, Decimal('0.00'))

        data_ref = agendamento.data if agendamento else date.today()
        pode, _ = assinatura.pode_utilizar(data_ref)
        if not pode:
            return ConsumoResultado(False, Decimal('0.00'))

        # Serviços contemplados pelo plano
        servicos_inclusos = set(assinatura.plano.servicos_inclusos.values_list('pk', flat=True))
        if not servicos_inclusos:
            servicos_inclusos = set(assinatura.plano.servicos.values_list('pk', flat=True))

        servicos_a_avaliar = []
        if itens_servicos:
            servicos_a_avaliar = itens_servicos
        elif agendamento and agendamento.itens.exists():
            servicos_a_avaliar = [it.servico for it in agendamento.itens.all()]
        elif servico:
            servicos_a_avaliar = [servico]
        elif agendamento and agendamento.servico:
            servicos_a_avaliar = [agendamento.servico]

        if servicos_inclusos:
            itens_cobertos = [s for s in servicos_a_avaliar if s and s.pk in servicos_inclusos]
            if not itens_cobertos:
                return ConsumoResultado(False, Decimal('0.00'))
        else:
            itens_cobertos = [s for s in servicos_a_avaliar if s]
            if not itens_cobertos:
                return ConsumoResultado(False, Decimal('0.00'))

        valor_abatido = sum(s.preco for s in itens_cobertos)

        # Evita debitar 2 vezes para o mesmo agendamento
        if agendamento and MovimentacaoCredito.objects.filter(
            assinatura=assinatura,
            agendamento=agendamento,
            tipo=MovimentacaoCredito.Tipo.CONSUMO
        ).exists():
            return ConsumoResultado(True, valor_abatido)

        is_ilimitado = (assinatura.plano.modalidade == PlanoAssinatura.Modalidade.ILIMITADO)
        saldo_anterior = assinatura.creditos_disponiveis

        if not is_ilimitado:
            if assinatura.creditos_disponiveis < 1:
                return ConsumoResultado(False, Decimal('0.00'))
            assinatura.creditos_disponiveis -= 1

        assinatura.creditos_utilizados += 1
        assinatura.save(update_fields=['creditos_disponiveis', 'creditos_utilizados', 'atualizado_em'])

        MovimentacaoCredito.objects.create(
            assinatura=assinatura,
            agendamento=agendamento,
            tipo=MovimentacaoCredito.Tipo.CONSUMO,
            quantidade=-1 if not is_ilimitado else 0,
            saldo_anterior=saldo_anterior,
            saldo_posterior=assinatura.creditos_disponiveis,
            descricao=f"Consumo de visita ({', '.join(s.nome for s in itens_cobertos)})"
        )

        if agendamento and agendamento.itens.exists():
            for it in agendamento.itens.all():
                if (not servicos_inclusos) or (it.servico.pk in servicos_inclusos):
                    it.coberto_por_assinatura = True
                    it.save(update_fields=['coberto_por_assinatura'])

        return ConsumoResultado(True, valor_abatido)


    @staticmethod
    @transaction.atomic
    def estornar_credito(agendamento: Agendamento) -> bool:
        """
        Estorna o crédito de um agendamento cancelado de volta para a assinatura do cliente.
        Garante idempotência estrita (apenas 1 estorno por agendamento).
        """
        if MovimentacaoCredito.objects.filter(
            agendamento=agendamento,
            tipo=MovimentacaoCredito.Tipo.ESTORNO
        ).exists():
            return False

        mov_consumo = MovimentacaoCredito.objects.filter(
            agendamento=agendamento,
            tipo=MovimentacaoCredito.Tipo.CONSUMO
        ).first()

        if not mov_consumo:
            return False

        assinatura = AssinaturaCliente.objects.select_for_update().get(pk=mov_consumo.assinatura.pk)
        is_ilimitado = (assinatura.plano.modalidade == PlanoAssinatura.Modalidade.ILIMITADO)
        saldo_ant = assinatura.creditos_disponiveis

        if not is_ilimitado:
            assinatura.creditos_disponiveis += 1

        if assinatura.creditos_utilizados > 0:
            assinatura.creditos_utilizados -= 1

        assinatura.save(update_fields=['creditos_disponiveis', 'creditos_utilizados', 'atualizado_em'])

        MovimentacaoCredito.objects.create(
            assinatura=assinatura,
            agendamento=agendamento,
            tipo=MovimentacaoCredito.Tipo.ESTORNO,
            quantidade=1 if not is_ilimitado else 0,
            saldo_anterior=saldo_ant,
            saldo_posterior=assinatura.creditos_disponiveis,
            descricao=f"Estorno de atendimento por cancelamento do agendamento #{agendamento.id}"
        )
        return True

    @staticmethod
    def get_resumo_cliente(cliente: Cliente):
        """Retorna informações da assinatura para a Área do Cliente."""
        assinatura = AssinaturaCliente.objects.filter(
            cliente=cliente,
        ).order_by('-atualizado_em').first()

        if not assinatura:
            return None

        is_ilimitado = (assinatura.plano.modalidade == PlanoAssinatura.Modalidade.ILIMITADO)
        total = "Ilimitado" if is_ilimitado else (assinatura.plano.limite_mensal or 4)
        disponiveis = "Ilimitado" if is_ilimitado else assinatura.creditos_disponiveis

        return {
            'assinatura': assinatura,
            'plano': assinatura.plano,
            'disponiveis': disponiveis,
            'total': total,
            'is_ilimitado': is_ilimitado,
            'utilizados': assinatura.creditos_utilizados,
            'renovacao': assinatura.data_renovacao,
            'status': assinatura.status,
        }

