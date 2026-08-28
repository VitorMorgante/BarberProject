from datetime import date, datetime, timedelta, time
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from website.models import (
    Agendamento, Cliente, Notificacao, RegraAutomacao,
    Produto, Comissao, Feedback, CupomDesconto, Barbeiro
)
from website.services.whatsapp_service import WhatsAppService


class AutomationService:
    """
    Central de Automações, Réguas de Comunicação, Notificações e Central de Alertas.
    """

    @staticmethod
    def executar_reguas_automacao() -> dict:
        """
        Executa as réguas de automação ativas configuradas no sistema:
        1. Lembrete 24h antes do atendimento
        2. Lembrete 2h antes
        3. Recuperação de clientes inativos (45 dias sem corte)
        4. Solicitação de feedback pós-atendimento
        5. Alerta de produtos abaixo do estoque mínimo
        """
        hoje = timezone.localtime().date()
        agora = timezone.now()
        notificacoes_geradas = 0

        regras_ativas = {r.tipo: r for r in RegraAutomacao.objects.filter(ativo=True)}

        # 1. Lembrete 24 Horas Antes
        if RegraAutomacao.Tipo.LEMBRETE_24H in regras_ativas:
            amanha = hoje + timedelta(days=1)
            agendamentos_24h = Agendamento.objects.filter(
                data=amanha,
                status__in=[Agendamento.Status.PENDENTE, Agendamento.Status.CONFIRMADO]
            ).exclude(notificacoes__tipo=Notificacao.Tipo.LEMBRETE_24H)

            for ag in agendamentos_24h:
                mensagem = WhatsAppService.gerar_mensagem_lembrete_24h(ag)
                data_prevista = datetime.combine(amanha, time(9, 0))
                Notificacao.objects.create(
                    cliente=ag.cliente,
                    agendamento=ag,
                    canal=Notificacao.Canal.WHATSAPP,
                    tipo=Notificacao.Tipo.LEMBRETE_24H,
                    mensagem=mensagem,
                    data_prevista=data_prevista
                )
                notificacoes_geradas += 1

        # 2. Lembrete 2 Horas Antes
        if RegraAutomacao.Tipo.LEMBRETE_2H in regras_ativas:
            limite_2h = agora + timedelta(hours=2)
            agendamentos_2h = Agendamento.objects.filter(
                data=hoje,
                status__in=[Agendamento.Status.PENDENTE, Agendamento.Status.CONFIRMADO]
            ).exclude(notificacoes__tipo=Notificacao.Tipo.LEMBRETE_2H)

            for ag in agendamentos_2h:
                dt_ag = datetime.combine(ag.data, ag.horario)
                # Verifica se está na janela de 2h
                if 0 <= (dt_ag - agora.replace(tzinfo=None)).total_seconds() <= 7200:
                    mensagem = WhatsAppService.gerar_mensagem_lembrete_2h(ag)
                    Notificacao.objects.create(
                        cliente=ag.cliente,
                        agendamento=ag,
                        canal=Notificacao.Canal.WHATSAPP,
                        tipo=Notificacao.Tipo.LEMBRETE_2H,
                        mensagem=mensagem,
                        data_prevista=dt_ag
                    )
                    notificacoes_geradas += 1

        # 3. Solicitação de Feedback Pós-Atendimento
        if RegraAutomacao.Tipo.FEEDBACK_POS_CORTE in regras_ativas:
            concluidos_sem_feedback = Agendamento.objects.filter(
                data=hoje,
                status=Agendamento.Status.CONCLUIDO,
                feedback__isnull=True
            ).exclude(notificacoes__tipo=Notificacao.Tipo.FEEDBACK_POS_CORTE)

            for ag in concluidos_sem_feedback:
                mensagem = WhatsAppService.gerar_mensagem_pesquisa_satisfacao(ag)
                Notificacao.objects.create(
                    cliente=ag.cliente,
                    agendamento=ag,
                    canal=Notificacao.Canal.WHATSAPP,
                    tipo=Notificacao.Tipo.FEEDBACK_POS_CORTE,
                    mensagem=mensagem,
                    data_prevista=agora
                )
                notificacoes_geradas += 1

        # 4. Reativação de Clientes Inativos (30, 45, 60 dias)
        for tipo_reativacao, dias in [
            (RegraAutomacao.Tipo.REATIVACAO_30D, 30),
            (RegraAutomacao.Tipo.REATIVACAO_45D, 45),
            (RegraAutomacao.Tipo.REATIVACAO_60D, 60),
        ]:
            if tipo_reativacao in regras_ativas:
                data_corte = hoje - timedelta(days=dias)
                # Localiza clientes cujo último corte foi exatamente nessa data
                clientes_inativos = Cliente.objects.filter(
                    agendamentos__status=Agendamento.Status.CONCLUIDO,
                    agendamentos__data=data_corte
                ).distinct()

                for c in clientes_inativos:
                    # Garante que não fez corte mais recente
                    corte_mais_recente = Agendamento.objects.filter(
                        cliente=c,
                        status=Agendamento.Status.CONCLUIDO,
                        data__gt=data_corte
                    ).exists()

                    if not corte_mais_recente and not Notificacao.objects.filter(cliente=c, tipo=Notificacao.Tipo.REATIVACAO, criado_em__gte=agora-timedelta(days=15)).exists():
                        cupom = CupomDesconto.objects.filter(ativo=True).first()
                        codigo_cupom = cupom.codigo if cupom else 'VOLTA10'
                        mensagem = WhatsAppService.gerar_mensagem_reativacao_inativo(c, cupom_codigo=codigo_cupom)
                        Notificacao.objects.create(
                            cliente=c,
                            canal=Notificacao.Canal.WHATSAPP,
                            tipo=Notificacao.Tipo.REATIVACAO,
                            mensagem=mensagem,
                            data_prevista=agora
                        )
                        notificacoes_geradas += 1

        return {
            'sucesso': True,
            'notificacoes_geradas': notificacoes_geradas
        }

    @staticmethod
    def obter_resumo_executivo_dia(data_ref: date = None) -> dict:
        """
        Retorna o Resumo Executivo Diário e a Central de Alertas para o gestor em consultas SQL agregadas mínimas:
        - Total agendamentos hoje
        - Faturamento previsto no dia
        - Clientes aguardando confirmação
        - Horários livres restantes
        - Produtos abaixo do estoque mínimo
        - Comissões pendentes
        - Feedbacks com nota baixa (Service Recovery)
        """
        hoje = data_ref or timezone.localtime().date()
        agendamentos_hoje = Agendamento.objects.filter(data=hoje).exclude(status=Agendamento.Status.CANCELADO)

        ag_stats = agendamentos_hoje.aggregate(
            tot_agendamentos=Count('id'),
            faturamento_previsto=Sum('servico__preco'),
            aguardando_confirmacao=Count('id', filter=Q(status=Agendamento.Status.PENDENTE))
        )
        total_agendamentos = ag_stats['tot_agendamentos'] or 0
        faturamento_previsto = ag_stats['faturamento_previsto'] or Decimal('0.00')
        aguardando_confirmacao = ag_stats['aguardando_confirmacao'] or 0

        # Produtos em estoque crítico
        produtos_baixos = Produto.objects.filter(
            ativo=True,
            estoque_atual__lte=F('estoque_minimo')
        )

        # Feedbacks críticos (Notas 1 e 2 que exigem service recovery)
        feedbacks_criticos = Feedback.objects.filter(
            nota__lte=2,
            criado_em__gte=timezone.now() - timedelta(days=7)
        ).select_related('cliente', 'barbeiro')

        # Comissões pendentes de repasse
        comissoes_pendentes = Comissao.objects.filter(
            status=Comissao.Status.PENDENTE
        ).aggregate(tot=Sum('valor_comissao'))['tot'] or Decimal('0.00')

        return {
            'hoje': hoje,
            'total_agendamentos': total_agendamentos,
            'faturamento_previsto': faturamento_previsto,
            'aguardando_confirmacao': aguardando_confirmacao,
            'produtos_baixos_qtd': produtos_baixos.count(),
            'produtos_baixos': produtos_baixos,
            'feedbacks_criticos': feedbacks_criticos,
            'comissoes_pendentes_total': comissoes_pendentes
        }
