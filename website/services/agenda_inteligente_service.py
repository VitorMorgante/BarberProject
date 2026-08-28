from datetime import date, datetime, time, timedelta
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Avg, F
from website.models import (
    Agendamento, Barbeiro, Servico, BarbeiroServico,
    EscalaBarbeiro, BloqueioAgenda, Cliente, ConfiguracaoEstabelecimento,
    Notificacao, Feedback
)
from website.services.whatsapp_service import WhatsAppService


class AgendaInteligenteService:
    """
    Motor inteligente de agendamento e operação da Delacruz Barber.
    Calcula horários disponíveis com score de eficiência, minimiza buracos,
    gerencia escalas, pausas, atrasos, check-in e fila em tempo real.
    """

    @staticmethod
    def calcular_score_no_show(cliente: Cliente) -> int:
        """
        Calcula o score de risco de no-show do cliente (0 a 100).
        0 = Confiável / Sempre comparece
        100 = Alto risco de falta
        """
        total = Agendamento.objects.filter(cliente=cliente).exclude(status=Agendamento.Status.CANCELADO).count()
        if total == 0:
            return 30  # Cliente novo: risco moderado padrão

        nao_compareceu = Agendamento.objects.filter(cliente=cliente, status=Agendamento.Status.NAO_COMPARECEU).count()
        concluidos = Agendamento.objects.filter(cliente=cliente, status=Agendamento.Status.CONCLUIDO).count()

        if concluidos == 0 and nao_compareceu > 0:
            return 95

        taxa_falta = (nao_compareceu / total) * 100
        return min(100, int(taxa_falta * 1.5))

    @staticmethod
    def obter_horarios_com_score(data_agendamento: date, servico: Servico, barbeiro: Barbeiro = None, cliente: Cliente = None):
        """
        Gera os horários disponíveis com score de eficiência operacional:
        - Score alto (90-100): Encaixe perfeito, colado a outro atendimento (evita buracos)
        - Score médio (70-89): Início de turno ou intervalo planejado
        - Score baixo (<70): Cria janela ociosa isolada
        """
        config = ConfiguracaoEstabelecimento.get_solo()
        duracao_servico = servico.duracao_minutos
        barbeiros = [barbeiro] if barbeiro else list(Barbeiro.objects.filter(ativo=True))
        dia_semana = data_agendamento.weekday()
        horarios_pontuados = []

        agora = timezone.localtime()
        hoje = agora.date()
        hora_minima_hoje = (agora + timedelta(minutes=config.antecedencia_minima_minutos)).time() if data_agendamento == hoje else time(0, 0)

        for barb in barbeiros:
            # 1. Verifica férias ou bloqueios do dia
            bloqueio_integral = BloqueioAgenda.objects.filter(
                Q(barbeiro=barb) | Q(barbeiro__isnull=True),
                ativo=True,
                data_inicio__lte=data_agendamento,
                data_fim__gte=data_agendamento,
                horario_inicio__isnull=True
            ).exists()
            if bloqueio_integral:
                continue

            # 2. Duração e buffer específicos deste barbeiro
            barb_servico = BarbeiroServico.objects.filter(barbeiro=barb, servico=servico, ativo=True).first()
            duracao = barb_servico.duracao_minutos if barb_servico and barb_servico.duracao_minutos else duracao_servico
            buffer_min = barb.tempo_buffer_depois or config.buffer_padrao_minutos

            # 3. Escala do dia da semana
            escala = EscalaBarbeiro.objects.filter(barbeiro=barb, dia_semana=dia_semana, ativo=True).first()
            turnos = []
            if escala and not escala.folga:
                turnos.append((escala.horario_inicio_1, escala.horario_fim_1))
                if escala.horario_inicio_2 and escala.horario_fim_2:
                    turnos.append((escala.horario_inicio_2, escala.horario_fim_2))
            else:
                # Fallback: se não tiver escala cadastrada, busca HorarioDisponivel legado ou padrão 09:00 - 19:00
                horarios_legados = list(barb.horarios.filter(ativo=True).order_by('horario'))
                if horarios_legados:
                    for hl in horarios_legados:
                        # Considera cada horário legado como slot
                        h_ini = hl.horario
                        dt_dummy = datetime.combine(data_agendamento, h_ini)
                        h_fim = (dt_dummy + timedelta(minutes=duracao)).time()
                        turnos.append((h_ini, h_fim))
                else:
                    turnos.append((time(9, 0), time(12, 0)))
                    turnos.append((time(13, 30), time(19, 0)))

            # 4. Agendamentos existentes do barbeiro neste dia
            agendamentos_dia = list(Agendamento.objects.filter(
                barbeiro=barb,
                data=data_agendamento
            ).exclude(status=Agendamento.Status.CANCELADO).select_related('servico', 'barbeiro').order_by('horario'))

            # Bloqueios parciais do dia
            bloqueios_parciais = list(BloqueioAgenda.objects.filter(
                Q(barbeiro=barb) | Q(barbeiro__isnull=True),
                ativo=True,
                data_inicio__lte=data_agendamento,
                data_fim__gte=data_agendamento,
                horario_inicio__isnull=False
            ))

            for h_inicio_turno, h_fim_turno in turnos:
                curr_dt = datetime.combine(data_agendamento, h_inicio_turno)
                fim_turno_dt = datetime.combine(data_agendamento, h_fim_turno)

                while curr_dt + timedelta(minutes=duracao) <= fim_turno_dt:
                    slot_inicio = curr_dt.time()
                    slot_fim_dt = curr_dt + timedelta(minutes=duracao)
                    slot_fim = slot_fim_dt.time()

                    if data_agendamento == hoje and slot_inicio < hora_minima_hoje:
                        curr_dt += timedelta(minutes=30)
                        continue

                    # Verifica conflito com agendamentos
                    conflito = False
                    colado_anterior = False
                    colado_posterior = False

                    for ag in agendamentos_dia:
                        ag_inicio_dt = datetime.combine(data_agendamento, ag.horario)
                        ag_dur = ag.servico.duracao_minutos
                        ag_fim_dt = ag_inicio_dt + timedelta(minutes=ag_dur + buffer_min)

                        # Colisão de intervalo
                        if not (slot_fim_dt <= ag_inicio_dt or curr_dt >= ag_fim_dt):
                            conflito = True
                            break

                        # Encaixe perfeito adjacente
                        if ag_fim_dt == curr_dt:
                            colado_anterior = True
                        if slot_fim_dt == ag_inicio_dt:
                            colado_posterior = True

                    # Verifica conflito com bloqueios parciais
                    if not conflito:
                        for bl in bloqueios_parciais:
                            bl_ini_dt = datetime.combine(data_agendamento, bl.horario_inicio)
                            bl_fim_dt = datetime.combine(data_agendamento, bl.horario_fim)
                            if not (slot_fim_dt <= bl_ini_dt or curr_dt >= bl_fim_dt):
                                conflito = True
                                break

                    if not conflito:
                        # Cálculo do score de inteligência operacional
                        score = 70  # Base
                        if colado_anterior and colado_posterior:
                            score = 100  # Preenche perfeitamente um buraco
                        elif colado_anterior or colado_posterior:
                            score = 90   # Encaixe contínuo otimizado
                        elif curr_dt == datetime.combine(data_agendamento, h_inicio_turno):
                            score = 85   # Abertura de turno
                        else:
                            score = 65   # Horário solto no meio do turno (pode criar buraco)

                        # Bônus de preferência do cliente
                        if cliente:
                            if cliente.barbeiro_preferido == barb:
                                score += 5
                            if cliente.preferencia_acabamento and 'manha' in cliente.preferencia_acabamento.lower() and slot_inicio < time(12, 0):
                                score += 5

                        horarios_pontuados.append({
                            'barbeiro_id': barb.id,
                            'barbeiro_nome': barb.nome,
                            'barbeiro_nivel': barb.get_nivel_display(),
                            'horario': slot_inicio.strftime('%H:%M'),
                            'duracao': duracao,
                            'score': min(100, score),
                            'recomendado': score >= 85
                        })

                    curr_dt += timedelta(minutes=30)

        # Ordena por horário e score decrescente
        horarios_pontuados.sort(key=lambda x: (x['horario'], -x['score']))
        return horarios_pontuados

    @staticmethod
    @transaction.atomic
    def registrar_checkin(agendamento: Agendamento, token: str = None) -> bool:
        """
        Registra o check-in do cliente (por QR Code na recepção ou confirmação de chegada).
        Atualiza o status para 'Aguardando' e entra na fila em tempo real.
        """
        agendamento = Agendamento.objects.select_for_update().get(pk=agendamento.pk)
        if token and str(agendamento.checkin_token) != str(token):
            return False

        agendamento.status = Agendamento.Status.AGUARDANDO
        agendamento.checkin_em = timezone.now()
        agendamento.save(update_fields=['status', 'checkin_em', 'atualizado_em'])
        return True

    @staticmethod
    def obter_fila_tempo_real(barbeiro: Barbeiro = None):
        """
        Retorna a situação da fila operacional do dia:
        - Em Atendimento
        - Aguardando (Check-in feito)
        - Próximos agendados
        - Previsão de espera em minutos e clientes à frente
        """
        hoje = timezone.localtime().date()
        qs = Agendamento.objects.filter(
            data=hoje
        ).exclude(status=Agendamento.Status.CANCELADO).select_related('cliente', 'barbeiro', 'servico', 'dependente')

        if barbeiro:
            qs = qs.filter(barbeiro=barbeiro)

        em_atendimento = qs.filter(status=Agendamento.Status.EM_ATENDIMENTO).order_by('horario')
        aguardando = qs.filter(status=Agendamento.Status.AGUARDANDO).order_by('checkin_em', 'horario')
        proximos = qs.filter(status__in=[Agendamento.Status.CONFIRMADO, Agendamento.Status.PENDENTE]).order_by('horario')

        fila_aguardando = []
        tempo_acumulado = 0

        # Considera tempo restante estimado de quem está na cadeira
        for item in em_atendimento:
            dur = item.servico.duracao_minutos
            tempo_acumulado += max(10, dur // 2)

        for idx, ag in enumerate(aguardando):
            dur = ag.servico.duracao_minutos
            fila_aguardando.append({
                'agendamento': ag,
                'nome': ag.dependente.nome if ag.dependente else ag.cliente.nome,
                'barbeiro': ag.barbeiro.nome,
                'servico': ag.servico.nome,
                'pessoas_a_frente': idx,
                'tempo_estimado_espera': tempo_acumulado,
                'horario_agendado': ag.horario.strftime('%H:%M'),
                'checkin_hora': ag.checkin_em.strftime('%H:%M') if ag.checkin_em else ''
            })
            tempo_acumulado += dur

        return {
            'em_atendimento': em_atendimento,
            'aguardando': fila_aguardando,
            'proximos': proximos,
            'total_fila': len(fila_aguardando),
            'tempo_estimado_proximo': tempo_acumulado
        }

    @staticmethod
    @transaction.atomic
    def registrar_pausa_rapida(barbeiro: Barbeiro, minutos: int, motivo: str = 'Pausa Rápida') -> BloqueioAgenda:
        """
        Insere uma pausa emergencial (5, 10, 15, 30 min) a partir do momento atual.
        """
        agora = timezone.localtime()
        hoje = agora.date()
        h_ini = agora.time()
        h_fim = (agora + timedelta(minutes=minutos)).time()

        bloqueio = BloqueioAgenda.objects.create(
            barbeiro=barbeiro,
            tipo=BloqueioAgenda.Tipo.PAUSA_RAPIDA,
            data_inicio=hoje,
            data_fim=hoje,
            horario_inicio=h_ini,
            horario_fim=h_fim,
            motivo=f"{motivo} ({minutos} min)",
            ativo=True
        )

        # Ajusta atraso operacional estimado para os próximos clientes
        AgendaInteligenteService.registrar_atraso_operacional(barbeiro, minutos)
        return bloqueio

    @staticmethod
    @transaction.atomic
    def registrar_atraso_operacional(barbeiro: Barbeiro, minutos_atraso: int):
        """
        Registra atraso operacional e atualiza previsão dos atendimentos seguintes do dia.
        Dispara notificações via WhatsApp/Push se o atraso for relevante (>= 15 min).
        """
        hoje = timezone.localtime().date()
        agora_hora = timezone.localtime().time()

        proximos = Agendamento.objects.filter(
            barbeiro=barbeiro,
            data=hoje,
            horario__gte=agora_hora,
            status__in=[Agendamento.Status.CONFIRMADO, Agendamento.Status.AGUARDANDO, Agendamento.Status.PENDENTE]
        )

        for ag in proximos:
            ag.atraso_estimado_minutos = minutos_atraso
            ag.save(update_fields=['atraso_estimado_minutos'])

            if minutos_atraso >= 15:
                msg = (
                    f"Olá, {ag.cliente.nome.split()[0]}! 💈 Informamos que a bancada de "
                    f"*{barbeiro.nome}* está com um pequeno atraso estimado de *{minutos_atraso} minutos* hoje. "
                    f"Seu horário foi recalibrado para maior conforto. Agradecemos sua compreensão!"
                )
                Notificacao.objects.create(
                    cliente=ag.cliente,
                    agendamento=ag,
                    canal=Notificacao.Canal.WHATSAPP,
                    tipo=Notificacao.Tipo.ATRASO,
                    mensagem=msg,
                    status=Notificacao.Status.PENDENTE,
                    data_prevista=timezone.now()
                )

    @staticmethod
    def detectar_agendamentos_afetados_por_ausencia(ausencia: BloqueioAgenda):
        """
        Identifica todos os agendamentos comprometidos quando uma ausência/férias é cadastrada.
        """
        if not ausencia.barbeiro:
            return Agendamento.objects.filter(
                data__gte=ausencia.data_inicio,
                data__lte=ausencia.data_fim
            ).exclude(status=Agendamento.Status.CANCELADO)

        qs = Agendamento.objects.filter(
            barbeiro=ausencia.barbeiro,
            data__gte=ausencia.data_inicio,
            data__lte=ausencia.data_fim
        ).exclude(status=Agendamento.Status.CANCELADO)

        if ausencia.horario_inicio and ausencia.horario_fim:
            qs = qs.filter(horario__gte=ausencia.horario_inicio, horario__lte=ausencia.horario_fim)

        return qs

    @staticmethod
    def sugerir_barbeiros_alternativos(agendamento: Agendamento):
        """
        Localiza outros profissionais ativos que atendem o mesmo serviço e têm horário livre no mesmo instante.
        """
        outros_barbeiros = Barbeiro.objects.filter(ativo=True).exclude(pk=agendamento.barbeiro.pk)
        compativeis = []

        for b in outros_barbeiros:
            tem_conflito = Agendamento.objects.filter(
                barbeiro=b,
                data=agendamento.data,
                horario=agendamento.horario
            ).exclude(status=Agendamento.Status.CANCELADO).exists()

            if not tem_conflito:
                compativeis.append(b)

        return compativeis

    @staticmethod
    def sugerir_revisao_duracao_servicos():
        """
        Compara a duração configurada dos serviços com a média real observada nos atendimentos concluídos.
        Retorna sugestões para calibragem se houver desvio >= 10 minutos.
        """
        sugestoes = []
        for serv in Servico.objects.filter(ativo=True):
            agendamentos_reais = Agendamento.objects.filter(
                servico=serv,
                status=Agendamento.Status.CONCLUIDO,
                duracao_real_minutos__isnull=False
            )
            if agendamentos_reais.count() >= 5:
                media_real = agendamentos_reais.aggregate(m=Avg('duracao_real_minutos'))['m'] or 0
                media_real = int(round(media_real))
                diferenca = media_real - serv.duracao_minutos

                if abs(diferenca) >= 10:
                    sugestoes.append({
                        'servico': serv,
                        'duracao_cadastrada': serv.duracao_minutos,
                        'media_real': media_real,
                        'diferenca': diferenca,
                        'sugestao': f"Ajustar de {serv.duracao_minutos} min para {media_real} min (Desvio: {diferenca:+d} min)"
                    })
        return sugestoes
