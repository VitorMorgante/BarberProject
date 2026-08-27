from datetime import date, timedelta
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from website.models import Cliente, Servico, Agendamento, PlanoAssinatura, AssinaturaCliente, MovimentacaoCredito


class SubscriptionService:
    @staticmethod
    @transaction.atomic
    def ativar_ou_renovar_assinatura(cliente: Cliente, plano: PlanoAssinatura) -> AssinaturaCliente:
        """
        Ativa ou renova a assinatura de um cliente no Barber Club.
        Gera os créditos correspondentes e registra no histórico.
        """
        hoje = timezone.now().date()
        validade = timedelta(days=plano.validade_dias or 30)
        proxima_renovacao = hoje + validade

        assinatura, created = AssinaturaCliente.objects.select_for_update().get_or_create(
            cliente=cliente,
            defaults={
                'plano': plano,
                'status': AssinaturaCliente.Status.ATIVA,
                'data_inicio': hoje,
                'data_renovacao': proxima_renovacao,
                'creditos_disponiveis': plano.quantidade_creditos,
                'creditos_utilizados': 0,
            }
        )

        if not created:
            saldo_ant = assinatura.creditos_disponiveis
            assinatura.plano = plano
            assinatura.status = AssinaturaCliente.Status.ATIVA
            assinatura.data_renovacao = proxima_renovacao

            if plano.permite_acumular:
                novo_saldo = saldo_ant + plano.quantidade_creditos
            else:
                novo_saldo = plano.quantidade_creditos

            assinatura.creditos_disponiveis = novo_saldo
            assinatura.save()

            MovimentacaoCredito.objects.create(
                assinatura=assinatura,
                tipo=MovimentacaoCredito.Tipo.CREDITO_MENSAL,
                quantidade=plano.quantidade_creditos,
                saldo_anterior=saldo_ant,
                saldo_posterior=novo_saldo,
                descricao=f"Renovação de plano: {plano.nome} (+{plano.quantidade_creditos} créditos)"
            )
        else:
            MovimentacaoCredito.objects.create(
                assinatura=assinatura,
                tipo=MovimentacaoCredito.Tipo.CREDITO_MENSAL,
                quantidade=plano.quantidade_creditos,
                saldo_anterior=0,
                saldo_posterior=plano.quantidade_creditos,
                descricao=f"Adesão inicial ao Barber Club: {plano.nome} (+{plano.quantidade_creditos} créditos)"
            )

        return assinatura

    @staticmethod
    @transaction.atomic
    def consumir_credito(cliente: Cliente, servico: Servico, agendamento: Agendamento = None) -> bool:
        """
        Verifica se o cliente tem assinatura ativa compatível com o serviço e debita 1 crédito atomicamente.
        Retorna True se o crédito foi consumido, False caso contrário.
        """
        assinatura = AssinaturaCliente.objects.select_for_update().filter(
            cliente=cliente,
            status=AssinaturaCliente.Status.ATIVA,
        ).first()

        if not assinatura:
            return False

        # Verifica se o serviço está contemplado pelo plano (se plano.servicos tiver itens)
        servicos_inclusos = assinatura.plano.servicos.all()
        if servicos_inclusos.exists() and not servicos_inclusos.filter(pk=servico.pk).exists():
            return False

        if assinatura.creditos_disponiveis < 1:
            return False

        # Evita debitar 2 vezes para o mesmo agendamento
        if agendamento and MovimentacaoCredito.objects.filter(
            assinatura=assinatura,
            agendamento=agendamento,
            tipo=MovimentacaoCredito.Tipo.CONSUMO
        ).exists():
            return True  # Já foi consumido anteriormente

        saldo_anterior = assinatura.creditos_disponiveis
        assinatura.creditos_disponiveis -= 1
        assinatura.creditos_utilizados += 1
        assinatura.save(update_fields=['creditos_disponiveis', 'creditos_utilizados', 'atualizado_em'])

        MovimentacaoCredito.objects.create(
            assinatura=assinatura,
            agendamento=agendamento,
            tipo=MovimentacaoCredito.Tipo.CONSUMO,
            quantidade=-1,
            saldo_anterior=saldo_anterior,
            saldo_posterior=assinatura.creditos_disponiveis,
            descricao=f"Consumo de crédito para o serviço: {servico.nome}"
        )
        return True

    @staticmethod
    @transaction.atomic
    def estornar_credito(agendamento: Agendamento) -> bool:
        """
        Estorna o crédito de um agendamento cancelado de volta para a assinatura do cliente.
        """
        mov_consumo = MovimentacaoCredito.objects.filter(
            agendamento=agendamento,
            tipo=MovimentacaoCredito.Tipo.CONSUMO
        ).first()

        if not mov_consumo:
            return False

        assinatura = AssinaturaCliente.objects.select_for_update().get(pk=mov_consumo.assinatura.pk)
        saldo_ant = assinatura.creditos_disponiveis
        assinatura.creditos_disponiveis += 1
        if assinatura.creditos_utilizados > 0:
            assinatura.creditos_utilizados -= 1
        assinatura.save(update_fields=['creditos_disponiveis', 'creditos_utilizados', 'atualizado_em'])

        MovimentacaoCredito.objects.create(
            assinatura=assinatura,
            agendamento=agendamento,
            tipo=MovimentacaoCredito.Tipo.ESTORNO,
            quantidade=1,
            saldo_anterior=saldo_ant,
            saldo_posterior=assinatura.creditos_disponiveis,
            descricao=f"Estorno de crédito por cancelamento do agendamento #{agendamento.id}"
        )
        return True

    @staticmethod
    def get_resumo_cliente(cliente: Cliente):
        """Retorna informações da assinatura ativa para a Área do Cliente."""
        assinatura = AssinaturaCliente.objects.filter(
            cliente=cliente,
            status=AssinaturaCliente.Status.ATIVA
        ).first()

        if not assinatura:
            return None

        total = assinatura.plano.quantidade_creditos or 1
        disponiveis = assinatura.creditos_disponiveis
        porcentagem = min(100, int((disponiveis / total) * 100)) if total > 0 else 0

        return {
            'assinatura': assinatura,
            'plano': assinatura.plano,
            'disponiveis': disponiveis,
            'total': total,
            'utilizados': assinatura.creditos_utilizados,
            'porcentagem': porcentagem,
            'renovacao': assinatura.data_renovacao,
            'status': assinatura.status,
        }
