from datetime import date, datetime, timedelta
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q, F
from website.models import (
    Cliente, Agendamento, Comanda, ItemComanda, Feedback,
    AssinaturaCliente, HistoricoVisualCliente, ContaCorrenteCliente,
    MovimentacaoContaCorrente, Barbeiro, Servico, CupomDesconto
)


class CRMService:
    """
    Motor de CRM, inteligência de retenção, LTV, Churn e Perfil 360 do Cliente.
    """

    @staticmethod
    def calcular_metricas_cliente(cliente: Cliente, agendamentos_concluidos=None, total_gasto_comandas=None, total_gasto_assinaturas=None) -> dict:
        """
        Calcula as métricas de relacionamento do cliente com base no histórico real:
        - LTV Realizado (total gasto em serviços, produtos e assinaturas)
        - Frequência média de retorno em dias
        - Data prevista para o próximo corte
        - Churn score (probabilidade de abandono: 0 a 100)
        - LTV futuro projetado
        - Barbeiro e Serviço favoritos
        """
        hoje = timezone.localtime().date()
        if agendamentos_concluidos is None:
            agendamentos_concluidos = list(Agendamento.objects.filter(
                cliente=cliente,
                status=Agendamento.Status.CONCLUIDO
            ).select_related('barbeiro', 'servico').order_by('data'))

        total_cortes = len(agendamentos_concluidos)
        if total_gasto_comandas is None:
            total_gasto_comandas = Comanda.objects.filter(
                cliente=cliente,
                status=Comanda.Status.FECHADA
            ).aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')

        if total_gasto_assinaturas is None:
            total_gasto_assinaturas = AssinaturaCliente.objects.filter(
                cliente=cliente
            ).aggregate(total=Sum('plano__preco_mensal'))['total'] or Decimal('0.00')

        ltv_realizado = Decimal(str(total_gasto_comandas)) + Decimal(str(total_gasto_assinaturas))

        # Cálculo da frequência média de retorno
        intervalos = []
        if total_cortes >= 2:
            for i in range(1, total_cortes):
                delta = (agendamentos_concluidos[i].data - agendamentos_concluidos[i-1].data).days
                if delta > 0:
                    intervalos.append(delta)

        freq_media_dias = int(round(sum(intervalos) / len(intervalos))) if intervalos else 21

        # Data prevista de retorno
        ultimo_corte = agendamentos_concluidos[-1].data if agendamentos_concluidos else cliente.cadastrado_em.date()
        dias_desde_ultimo = (hoje - ultimo_corte).days
        proxima_data_prevista = ultimo_corte + timedelta(days=freq_media_dias)

        # Churn Score (0 a 100)
        if total_cortes == 0:
            churn_score = 40  # Não fez primeiro corte
        else:
            if dias_desde_ultimo <= freq_media_dias:
                churn_score = max(5, int((dias_desde_ultimo / max(1, freq_media_dias)) * 30))
            elif dias_desde_ultimo <= freq_media_dias * 2:
                churn_score = min(80, 30 + int(((dias_desde_ultimo - freq_media_dias) / freq_media_dias) * 50))
            else:
                churn_score = min(100, 80 + int((dias_desde_ultimo / (freq_media_dias * 2)) * 10))

        # LTV Futuro Estimado (Projeção para os próximos 12 meses)
        ticket_medio = (ltv_realizado / total_cortes) if total_cortes > 0 else Decimal('50.00')
        visitas_ano = 365 / max(7, freq_media_dias)
        probabilidade_retencao = max(Decimal('0.10'), Decimal(str(1 - (churn_score / 100.0))))
        ltv_futuro_estimado = Decimal(str(round(float(ticket_medio) * visitas_ano * float(probabilidade_retencao), 2)))

        # Barbeiro e serviço preferidos
        barbeiro_pref = None
        servico_pref = None
        if agendamentos_concluidos:
            barb_counts = {}
            serv_counts = {}
            for ag in agendamentos_concluidos:
                barb_counts[ag.barbeiro] = barb_counts.get(ag.barbeiro, 0) + 1
                serv_counts[ag.servico] = serv_counts.get(ag.servico, 0) + 1

            barbeiro_pref = max(barb_counts, key=barb_counts.get)
            servico_pref = max(serv_counts, key=serv_counts.get)

        return {
            'total_cortes': total_cortes,
            'ltv_realizado': ltv_realizado,
            'ltv_futuro_estimado': ltv_futuro_estimado,
            'freq_media_dias': freq_media_dias,
            'dias_desde_ultimo': dias_desde_ultimo,
            'ultimo_corte_data': ultimo_corte,
            'proxima_data_prevista': proxima_data_prevista,
            'churn_score': churn_score,
            'is_em_risco': churn_score >= 60,
            'is_inativo': dias_desde_ultimo >= 45,
            'barbeiro_favorito': barbeiro_pref,
            'servico_favorito': servico_pref,
            'ticket_medio': ticket_medio
        }

    @staticmethod
    def obter_segmentos_clientes():
        """
        Classifica automaticamente todos os clientes em segmentos operacionais em lote O(1) queries:
        - VIP (Ticket alto ou fidelidade contínua)
        - Novos (0 ou 1 atendimento)
        - Em Risco (Churn score >= 60)
        - Inativos (sem retorno há mais de 45 dias)
        - Aniversariantes do Mês
        - Clientes Recorrentes
        """
        hoje = timezone.localtime().date()
        mes_atual = hoje.month
        clientes = list(Cliente.objects.all())

        # Agregações em lote para eliminar N+1
        agendamentos_all = list(Agendamento.objects.filter(
            status=Agendamento.Status.CONCLUIDO
        ).select_related('barbeiro', 'servico').order_by('data'))

        ag_por_cliente = {}
        for ag in agendamentos_all:
            ag_por_cliente.setdefault(ag.cliente_id, []).append(ag)

        comandas_map = {
            item['cliente_id']: item['total']
            for item in Comanda.objects.filter(status=Comanda.Status.FECHADA).values('cliente_id').annotate(total=Sum('valor_total'))
        }

        assinaturas_map = {
            item['cliente_id']: item['total']
            for item in AssinaturaCliente.objects.values('cliente_id').annotate(total=Sum('plano__preco_mensal'))
        }

        vips = []
        novos = []
        em_risco = []
        inativos = []
        aniversariantes = []
        recorrentes = []

        for c in clientes:
            ag_list = ag_por_cliente.get(c.id, [])
            tot_com = comandas_map.get(c.id, Decimal('0.00'))
            tot_ass = assinaturas_map.get(c.id, Decimal('0.00'))

            metricas = CRMService.calcular_metricas_cliente(
                c,
                agendamentos_concluidos=ag_list,
                total_gasto_comandas=tot_com,
                total_gasto_assinaturas=tot_ass
            )
            c.metricas = metricas

            if c.data_nascimento and c.data_nascimento.month == mes_atual:
                aniversariantes.append(c)

            if metricas['total_cortes'] <= 1:
                novos.append(c)
            else:
                recorrentes.append(c)

            if metricas['ltv_realizado'] >= Decimal('300.00') or metricas['total_cortes'] >= 8:
                vips.append(c)

            if metricas['is_inativo']:
                inativos.append(c)
            elif metricas['is_em_risco']:
                em_risco.append(c)

        return {
            'total_clientes': len(clientes),
            'vips': vips,
            'novos': novos,
            'recorrentes': recorrentes,
            'em_risco': em_risco,
            'inativos': inativos,
            'aniversariantes': aniversariantes
        }

    @staticmethod
    def obter_perfil_360(cliente: Cliente) -> dict:
        """
        Consolida a visão 360º completa do cliente para exibição no dashboard/CRM.
        """
        metricas = CRMService.calcular_metricas_cliente(cliente)
        agendamentos = Agendamento.objects.filter(cliente=cliente).select_related('servico', 'barbeiro').order_by('-data', '-horario')
        comandas = Comanda.objects.filter(cliente=cliente).order_by('-criada_em')
        feedbacks = Feedback.objects.filter(cliente=cliente).order_by('-criado_em')
        assinatura = AssinaturaCliente.objects.filter(cliente=cliente, status=AssinaturaCliente.Status.ATIVA).first()
        fotos = HistoricoVisualCliente.objects.filter(cliente=cliente).order_by('-data')
        fichas = cliente.fichas_tecnicas.all().order_by('-data')
        dependentes = cliente.dependentes.all()

        # Constrói timeline unificada
        timeline = []
        for ag in agendamentos:
            timeline.append({
                'data': ag.criado_em,
                'tipo': 'Agendamento',
                'icone': 'bi-calendar-check',
                'cor': 'primary',
                'titulo': f"{ag.servico.nome} com {ag.barbeiro.nome}",
                'descricao': f"Data: {ag.data.strftime('%d/%m/%Y')} às {ag.horario.strftime('%H:%M')} [{ag.status}]"
            })
        for com in comandas:
            timeline.append({
                'data': com.criada_em,
                'tipo': 'Compra PDV',
                'icone': 'bi-receipt',
                'cor': 'success',
                'titulo': f"Comanda #{com.id} - R$ {com.valor_total}",
                'descricao': f"Método: {com.metodo_pagamento} [{com.status}]"
            })
        for fb in feedbacks:
            timeline.append({
                'data': fb.criado_em,
                'tipo': 'Feedback',
                'icone': 'bi-star-fill',
                'cor': 'warning',
                'titulo': f"Avaliação Nota {fb.nota}/5",
                'descricao': f'"{fb.comentario}"'
            })

        timeline.sort(key=lambda x: x['data'], reverse=True)

        return {
            'cliente': cliente,
            'metricas': metricas,
            'agendamentos': agendamentos,
            'comandas': comandas,
            'feedbacks': feedbacks,
            'assinatura': assinatura,
            'fotos': fotos,
            'fichas': fichas,
            'dependentes': dependentes,
            'timeline': timeline[:20]
        }

    @staticmethod
    @transaction.atomic
    def processar_recompensa_indicacao(agendamento_concluido: Agendamento) -> bool:
        """
        Concede benefício de indicação (ex: R$ 15,00 em saldo na Conta Corrente)
        ao indicador quando o indicado conclui seu primeiro corte no estabelecimento.
        Garante idempotência estrita.
        """
        cliente = agendamento_concluido.cliente
        if not cliente.indicado_por:
            return False

        # Verifica se este é realmente o primeiro corte concluído do indicado
        concluidos = Agendamento.objects.filter(
            cliente=cliente,
            status=Agendamento.Status.CONCLUIDO
        ).count()

        if concluidos != 1:
            return False  # Já foi processado ou não é o primeiro

        indicador = cliente.indicado_por
        conta_indicador, _ = ContaCorrenteCliente.objects.select_for_update().get_or_create(
            cliente=indicador,
            defaults={'saldo': Decimal('0.00')}
        )

        valor_premio = Decimal('15.00')

        # Verifica idempotência
        ja_recompensado = MovimentacaoContaCorrente.objects.filter(
            conta_corrente=conta_indicador,
            tipo=MovimentacaoContaCorrente.Tipo.RECOMPENSA_INDICACAO,
            descricao__icontains=f"Cliente #{cliente.id}"
        ).exists()

        if ja_recompensado:
            return False

        saldo_ant = conta_indicador.saldo
        conta_indicador.saldo += valor_premio
        conta_indicador.save(update_fields=['saldo', 'atualizado_em'])

        MovimentacaoContaCorrente.objects.create(
            conta_corrente=conta_indicador,
            tipo=MovimentacaoContaCorrente.Tipo.RECOMPENSA_INDICACAO,
            valor=valor_premio,
            saldo_anterior=saldo_ant,
            saldo_posterior=conta_indicador.saldo,
            descricao=f"Bônus de indicação do amigo {cliente.nome} (Cliente #{cliente.id})"
        )
        return True

    @staticmethod
    def calcular_funil_conversao() -> dict:
        """
        Mede o funil de conversão de clientes:
        Total Cadastrados -> Com Agendamento -> 1º Atendimento Concluído -> Recorrente (>=2)
        """
        total_cadastros = Cliente.objects.count()
        com_agendamento = Cliente.objects.filter(agendamentos__isnull=False).distinct().count()
        primeiro_atendimento = Cliente.objects.filter(agendamentos__status=Agendamento.Status.CONCLUIDO).distinct().count()
        recorrentes = Cliente.objects.annotate(
            qtd_concluidos=Count('agendamentos', filter=Q(agendamentos__status=Agendamento.Status.CONCLUIDO))
        ).filter(qtd_concluidos__gte=2).count()

        return {
            'total_cadastros': total_cadastros,
            'com_agendamento': com_agendamento,
            'primeiro_atendimento': primeiro_atendimento,
            'recorrentes': recorrentes,
            'taxa_cadastro_agendamento': int((com_agendamento / max(1, total_cadastros)) * 100),
            'taxa_primeiro_recorrente': int((recorrentes / max(1, primeiro_atendimento)) * 100) if primeiro_atendimento > 0 else 0
        }
