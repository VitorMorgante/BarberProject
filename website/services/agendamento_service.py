from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from website.models import (
    Agendamento, Cliente, Barbeiro, Servico,
    Comanda, ItemComanda, ListaEspera, Notificacao
)
from website.services.subscription_service import SubscriptionService
from website.services.loyalty_service import LoyaltyService
from website.services.inventory_service import InventoryService
from website.services.comissao_service import ComissaoService
from website.services.whatsapp_service import WhatsAppService


class AgendamentoService:
    @staticmethod
    @transaction.atomic
    def concluir_atendimento(agendamento: Agendamento, comanda: Comanda = None, usuario_responsavel=None) -> Agendamento:
        """
        Executa atomicamente todas as ações de conclusão de atendimento:
        1. Atualiza o status do agendamento para 'Concluído'
        2. Consome créditos do Barber Club caso o cliente tenha assinatura compatível
        3. Contabiliza pontos no programa de Fidelidade Digital (+1 corte / gera recompensa)
        4. Cria/Fecha a Comanda correspondente com os serviços e produtos consumidos
        5. Atualiza o estoque de cada produto vendido
        6. Calcula e registra a comissão do barbeiro com snapshot do percentual do momento
        """
        agendamento = Agendamento.objects.select_for_update().get(pk=agendamento.pk)
        agendamento.status = Agendamento.Status.CONCLUIDO
        agendamento.save(update_fields=['status', 'atualizado_em'])

        # 1. Barber Club: tenta consumir crédito se elegível
        credito_consumido = SubscriptionService.consumir_credito(
            cliente=agendamento.cliente,
            servico=agendamento.servico,
            agendamento=agendamento
        )

        # 2. Fidelidade Digital: incrementa progresso e gera recompensa se atingir 10
        LoyaltyService.processar_atendimento_concluido(agendamento)

        # 3. Comanda & PDV
        if not comanda:
            comanda, _ = Comanda.objects.select_for_update().get_or_create(
                agendamento=agendamento,
                defaults={
                    'cliente': agendamento.cliente,
                    'barbeiro': agendamento.barbeiro,
                    'subtotal': agendamento.servico.preco,
                    'valor_total': agendamento.servico.preco,
                    'status': Comanda.Status.ABERTA,
                }
            )

        # Se o item principal de serviço ainda não estiver na comanda, adiciona
        if not comanda.itens.filter(tipo=ItemComanda.Tipo.SERVICO, servico=agendamento.servico).exists():
            ItemComanda.objects.create(
                comanda=comanda,
                tipo=ItemComanda.Tipo.SERVICO,
                servico=agendamento.servico,
                descricao=agendamento.servico.nome,
                quantidade=1,
                preco_unitario=agendamento.servico.preco,
                total=agendamento.servico.preco,
            )

        # Se usou crédito de assinatura, aplica desconto integral no serviço
        if credito_consumido:
            comanda.creditos_abatidos = agendamento.servico.preco

        # Abate estoque de todos os produtos na comanda que ainda não foram movimentados
        for item in comanda.itens.filter(tipo=ItemComanda.Tipo.PRODUTO):
            if item.produto:
                InventoryService.movimentar_estoque(
                    produto=item.produto,
                    tipo='venda',
                    quantidade=item.quantidade,
                    motivo=f"Venda na Comanda #{comanda.id} (Agendamento #{agendamento.id})",
                    usuario=usuario_responsavel
                )

        comanda.status = Comanda.Status.FECHADA
        comanda.fechada_em = timezone.now()
        comanda.recalcular()

        # 4. Comissões do Barbeiro
        # A. Comissão do serviço
        valor_base_servico = agendamento.servico.preco
        ComissaoService.registrar_comissao_servico(
            barbeiro=agendamento.barbeiro,
            agendamento=agendamento,
            valor_base=valor_base_servico
        )

        # B. Comissão dos produtos da comanda
        for item in comanda.itens.filter(tipo=ItemComanda.Tipo.PRODUTO):
            ComissaoService.registrar_comissao_produto(
                barbeiro=agendamento.barbeiro,
                comanda=comanda,
                item=item
            )

        return agendamento

    @staticmethod
    @transaction.atomic
    def cancelar_atendimento(agendamento: Agendamento, motivo: str = '') -> Agendamento:
        """
        Cancela o agendamento, estorna créditos de assinatura se aplicável,
        e dispara verificação da lista de espera para preencher o horário vago.
        """
        agendamento = Agendamento.objects.select_for_update().get(pk=agendamento.pk)
        agendamento.status = Agendamento.Status.CANCELADO
        if motivo:
            agendamento.observacoes = (agendamento.observacoes + f" [Cancelamento: {motivo}]").strip()
        agendamento.save(update_fields=['status', 'observacoes', 'atualizado_em'])

        # Estorna crédito do Barber Club caso tenha sido debitado
        SubscriptionService.estornar_credito(agendamento)

        # Cancela comanda aberta se existir
        if hasattr(agendamento, 'comanda') and agendamento.comanda and agendamento.comanda.status == Comanda.Status.ABERTA:
            agendamento.comanda.status = Comanda.Status.CANCELADA
            agendamento.comanda.save(update_fields=['status'])

        # Verifica candidatos na Lista de Espera compatíveis com este horário liberado
        AgendamentoService.notificar_lista_espera_vaga(
            data=agendamento.data,
            horario=agendamento.horario,
            barbeiro=agendamento.barbeiro
        )

        return agendamento

    @staticmethod
    def notificar_lista_espera_vaga(data, horario, barbeiro):
        """
        Identifica clientes na Lista de Espera que desejam a mesma data e faixa de horário,
        e gera notificações para oportunidade de encaixe.
        """
        candidatos = ListaEspera.objects.filter(
            data_desejada=data,
            status=ListaEspera.Status.AGUARDANDO,
            horario_inicio__lte=horario,
            horario_fim__gte=horario
        )
        if barbeiro:
            candidatos = candidatos.filter(models_q_barbeiro(barbeiro))

        for item in candidatos[:3]:  # Notifica os primeiros da fila
            item.status = ListaEspera.Status.NOTIFICADO
            item.notificado_em = timezone.now()
            item.save(update_fields=['status', 'notificado_em'])

            msg = WhatsAppService.gerar_mensagem_vaga_waitlist(item, horario.strftime('%H:%M'))
            Notificacao.objects.create(
                cliente=item.cliente,
                canal=Notificacao.Canal.WHATSAPP,
                tipo=Notificacao.Tipo.WAITLIST_VAGA,
                mensagem=msg,
                status=Notificacao.Status.PENDENTE,
                data_prevista=timezone.now()
            )


def models_q_barbeiro(barbeiro):
    from django.db.models import Q
    return Q(barbeiro=barbeiro) | Q(barbeiro__isnull=True)
