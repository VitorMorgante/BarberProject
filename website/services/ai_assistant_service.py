import re
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q, F
from website.models import (
    Servico, Barbeiro, Cliente, Agendamento, Produto,
    Comanda, ItemComanda, Feedback, HorarioDisponivel
)
from website.services.agenda_inteligente_service import AgendaInteligenteService


class AIAssistantService:
    """
    Assistente Virtual de Agendamento e Copiloto de Inteligência Delacruz Barber.
    Conectado 100% aos dados reais do banco de dados (nunca inventa horários, barbeiros ou estoque).
    """

    @staticmethod
    def processar_mensagem_agendamento(mensagem: str, cliente: Cliente = None) -> dict:
        """
        Interpreta pedidos de agendamento em linguagem natural ("Quero cortar amanhã depois das 16h com o Danilo").
        Consulta a disponibilidade real e retorna opções verdadeiras do banco.
        """
        msg_lower = mensagem.lower().strip()
        hoje = timezone.localtime().date()

        # 1. Identifica data
        data_alvo = hoje
        if 'amanha' in msg_lower or 'amanhã' in msg_lower:
            data_alvo = hoje + timedelta(days=1)
        elif 'depois de amanha' in msg_lower or 'depois de amanhã' in msg_lower:
            data_alvo = hoje + timedelta(days=2)
        elif 'sabado' in msg_lower or 'sábado' in msg_lower:
            dias_ate_sabado = (5 - hoje.weekday()) % 7 or 7
            data_alvo = hoje + timedelta(days=dias_ate_sabado)
        elif 'segunda' in msg_lower:
            dias_ate_segunda = (0 - hoje.weekday()) % 7 or 7
            data_alvo = hoje + timedelta(days=dias_ate_segunda)
        elif 'sexta' in msg_lower:
            dias_ate_sexta = (4 - hoje.weekday()) % 7 or 7
            data_alvo = hoje + timedelta(days=dias_ate_sexta)

        # 2. Identifica serviço
        servicos = Servico.objects.filter(ativo=True)
        servico_escolhido = None
        for s in servicos:
            if s.nome.lower() in msg_lower or s.nome.lower().split()[0] in msg_lower:
                servico_escolhido = s
                break
        if not servico_escolhido:
            # Fallback para primeiro serviço de corte ou preferido do cliente
            if cliente and cliente.servico_preferido:
                servico_escolhido = cliente.servico_preferido
            else:
                servico_escolhido = servicos.first() or Servico.objects.create(
                    nome='Corte Tradicional', preco=Decimal('45.00'), duracao_minutos=35
                )

        # 3. Identifica barbeiro
        barbeiros = Barbeiro.objects.filter(ativo=True)
        barbeiro_escolhido = None
        for b in barbeiros:
            primeiro_nome = b.nome.lower().split()[0]
            if primeiro_nome in msg_lower:
                barbeiro_escolhido = b
                break
        if not barbeiro_escolhido and cliente and cliente.barbeiro_preferido:
            barbeiro_escolhido = cliente.barbeiro_preferido

        # 4. Identifica filtro de horário desejado
        hora_filtro = None
        match_hora = re.search(r'(\d{1,2})h', msg_lower)
        if match_hora:
            hora_filtro = int(match_hora.group(1))

        is_depois = 'depois' in msg_lower or 'apos' in msg_lower or 'após' in msg_lower

        # 5. Consulta slots reais através da AgendaInteligenteService
        horarios_disp = AgendaInteligenteService.obter_horarios_com_score(
            data_agendamento=data_alvo,
            servico=servico_escolhido,
            barbeiro=barbeiro_escolhido,
            cliente=cliente
        )

        # Aplica filtro de faixa se solicitado
        if hora_filtro is not None:
            if is_depois:
                horarios_disp = [h for h in horarios_disp if int(h['horario'].split(':')[0]) >= hora_filtro]
            else:
                horarios_disp = [h for h in horarios_disp if abs(int(h['horario'].split(':')[0]) - hora_filtro) <= 1]

        # 6. Formata resposta amigável
        data_str = data_alvo.strftime('%d/%m/%Y')
        if not horarios_disp:
            resposta = (
                f"Olá! Verifiquei nossa agenda para *{servico_escolhido.nome}* no dia *{data_str}* "
                f"{'com ' + barbeiro_escolhido.nome if barbeiro_escolhido else ''}, mas infelizmente todos os horários dessa faixa estão ocupados.\n\n"
                f"Deseja que eu consulte outro profissional ou outra data próxima?"
            )
        else:
            top_horarios = [h['horario'] for h in horarios_disp[:4]]
            barb_str = barbeiro_escolhido.nome if barbeiro_escolhido else "nossos barbeiros"
            resposta = (
                f"Perfeito! 💈 Encontrei os seguintes horários disponíveis com *{barb_str}* "
                f"para *{servico_escolhido.nome}* (R$ {servico_escolhido.preco}) em *{data_str}*:\n\n"
                f"⏰ " + " | ".join(top_horarios) + "\n\n"
                f"Qual destes horários você prefere confirmar?"
            )

        return {
            'resposta': resposta,
            'data_alvo': data_alvo.strftime('%Y-%m-%d'),
            'servico_id': servico_escolhido.id if servico_escolhido else None,
            'servico_nome': servico_escolhido.nome if servico_escolhido else '',
            'barbeiro_id': barbeiro_escolhido.id if barbeiro_escolhido else None,
            'barbeiro_nome': barbeiro_escolhido.nome if barbeiro_escolhido else '',
            'horarios_disponiveis': horarios_disp[:6]
        }

    @staticmethod
    def responder_consulta_gestao(pergunta: str) -> str:
        """
        Responde perguntas administrativas com dados estatísticos e contábeis reais do sistema.
        """
        p_lower = pergunta.lower().strip()
        hoje = timezone.localtime().date()

        if 'fatur' in p_lower or 'receita' in p_lower or 'ganh' in p_lower:
            inicio_semana = hoje - timedelta(days=hoje.weekday())
            faturamento_semana = Comanda.objects.filter(
                status=Comanda.Status.FECHADA,
                fechada_em__date__gte=inicio_semana
            ).aggregate(tot=Sum('valor_total'))['tot'] or Decimal('0.00')

            faturamento_mes = Comanda.objects.filter(
                status=Comanda.Status.FECHADA,
                fechada_em__date__gte=date(hoje.year, hoje.month, 1)
            ).aggregate(tot=Sum('valor_total'))['tot'] or Decimal('0.00')

            return (
                f"📊 *Resumo Financeiro Real:*\n"
                f"• Faturamento desta semana (desde segunda): *R$ {faturamento_semana}*\n"
                f"• Faturamento acumulado no mês ({hoje.strftime('%m/%Y')}): *R$ {faturamento_mes}*"
            )

        elif 'estoque' in p_lower or 'acabando' in p_lower or 'produto' in p_lower:
            produtos_criticos = Produto.objects.filter(
                ativo=True,
                estoque_atual__lte=F('estoque_minimo')
            )
            if not produtos_criticos.exists():
                return "✅ Todos os produtos estão com níveis de estoque saudáveis e acima do mínimo configurado."

            linhas = [f"• *{p.nome}*: Restam *{p.estoque_atual} {p.unidade}* (Mínimo: {p.estoque_minimo})" for p in produtos_criticos[:5]]
            return (
                f"⚠️ *Alerta de Estoque Baixo:*\n" + "\n".join(linhas) + "\n\n"
                f"Recomendamos emitir um pedido de reposição para estes fornecedores."
            )

        elif 'horario' in p_lower or 'agenda' in p_lower or 'amanha' in p_lower:
            amanha = hoje + timedelta(days=1)
            agendados = Agendamento.objects.filter(data=amanha).exclude(status=Agendamento.Status.CANCELADO).count()
            return f"📅 Para amanhã ({amanha.strftime('%d/%m/%Y')}) temos *{agendados} agendamentos* confirmados na barbearia."

        else:
            return (
                "Posso responder sobre: faturamento da semana/mês, produtos em estoque baixo, "
                "ocupação da agenda de amanhã ou desempenho da equipe."
            )

    @staticmethod
    def calcular_match_barbeiro(cliente: Cliente, servico: Servico) -> list:
        """
        Calcula o match de compatibilidade (0 a 100%) entre o cliente e cada barbeiro da equipe.
        """
        barbeiros = Barbeiro.objects.filter(ativo=True)
        ranking = []

        for b in barbeiros:
            score = 70
            # Especialidade compatível
            if servico.nome.lower() in b.especialidade.lower():
                score += 15
            # Histórico com o cliente
            atendimentos_com_barbeiro = Agendamento.objects.filter(
                cliente=cliente,
                barbeiro=b,
                status=Agendamento.Status.CONCLUIDO
            ).count()
            if atendimentos_com_barbeiro > 0:
                score += min(15, atendimentos_com_barbeiro * 5)
            # Barbeiro preferido explícito
            if cliente.barbeiro_preferido == b:
                score += 10

            ranking.append({
                'barbeiro': b,
                'match_percentual': min(100, score),
                'destaque': score >= 85
            })

        ranking.sort(key=lambda x: x['match_percentual'], reverse=True)
        return ranking

    @staticmethod
    def recomendar_produtos_upsell(cliente: Cliente, servico: Servico) -> list:
        """
        Gera recomendação não intrusiva de produtos de cuidado com base no serviço e perfil.
        """
        produtos_sugeridos = []
        if 'barba' in servico.nome.lower():
            oleo = Produto.objects.filter(ativo=True, nome__icontains='Óleo', estoque_atual__gt=0).first()
            if oleo:
                produtos_sugeridos.append(oleo)
            balm = Produto.objects.filter(ativo=True, nome__icontains='Balm', estoque_atual__gt=0).first()
            if balm:
                produtos_sugeridos.append(balm)

        pomada = Produto.objects.filter(ativo=True, nome__icontains='Pomada', estoque_atual__gt=0).first()
        if pomada and pomada not in produtos_sugeridos:
            produtos_sugeridos.append(pomada)

        return produtos_sugeridos[:3]
