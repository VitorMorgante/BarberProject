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
    def obter_horarios_com_score(
        data_agendamento: date,
        servico: Servico = None,
        barbeiro: Barbeiro = None,
        cliente: Cliente = None,
        servicos: list = None,
        plano = None,
        duracao_minutos: int = None
    ):
        """
        Gera os horários disponíveis com score de eficiência operacional:
        - Início permitido: de 08:00 até 21:30 (inclusive), passo de 5 minutos.
        - Duração total: calculada por serviço, lista de serviços ou plano.
        - Buffer fixo: 5 minutos de transição ao final do atendimento.
        - Detecção simétrica de colisão no intervalo de ocupação:
          [inicio, inicio + duracao + 5min)
        - Folga explícita (folga=True) retorna estritamente lista vazia.
        """
        config = ConfiguracaoEstabelecimento.get_solo()

        # Resolução da duração total
        if duracao_minutos:
            duracao_total = int(duracao_minutos)
        elif plano:
            duracao_total = plano.get_duracao_total_estimada()
        elif servicos:
            duracao_total = sum(s.duracao_minutos for s in servicos if s)
        elif servico:
            duracao_total = servico.duracao_minutos
        else:
            duracao_total = 30

        buffer_min = 5
        barbeiros = [barbeiro] if barbeiro else list(Barbeiro.objects.filter(ativo=True))
        dia_semana = data_agendamento.weekday()
        horarios_pontuados = []

        agora = timezone.localtime()
        hoje = agora.date()
        hora_minima_hoje = (agora + timedelta(minutes=config.antecedencia_minima_minutos)).time() if data_agendamento == hoje else time(0, 0)

        CANDIDATO_INICIO = time(8, 0)
        CANDIDATO_FIM = time(21, 30)

        for barb in barbeiros:
            # 1. Verifica bloqueios integrais do dia
            bloqueio_integral = BloqueioAgenda.objects.filter(
                Q(barbeiro=barb) | Q(barbeiro__isnull=True),
                ativo=True,
                data_inicio__lte=data_agendamento,
                data_fim__gte=data_agendamento,
                horario_inicio__isnull=True
            ).exists()
            if bloqueio_integral:
                continue

            # 2. Escala do dia da semana
            escala = EscalaBarbeiro.objects.filter(barbeiro=barb, dia_semana=dia_semana, ativo=True).first()
            turnos = []
            if escala:
                if escala.folga:
                    # Folga explícita: estritamente 0 horários disponíveis para este barbeiro
                    continue
                turnos.append((escala.horario_inicio_1, escala.horario_fim_1))
                if escala.horario_inicio_2 and escala.horario_fim_2:
                    turnos.append((escala.horario_inicio_2, escala.horario_fim_2))
            else:
                # Fallback: APENAS se NÃO houver nenhum registro de EscalaBarbeiro para este dia
                horarios_legados = list(barb.horarios.filter(ativo=True).order_by('horario'))
                if horarios_legados:
                    for hl in horarios_legados:
                        h_ini = hl.horario
                        dt_dummy = datetime.combine(data_agendamento, h_ini)
                        h_fim = (dt_dummy + timedelta(minutes=duracao_total + buffer_min)).time()
                        turnos.append((h_ini, h_fim))
                else:
                    turnos.append((time(8, 0), time(22, 40)))

            if not turnos:
                continue

            # 3. Agendamentos existentes do barbeiro neste dia
            agendamentos_dia = list(Agendamento.objects.filter(
                barbeiro=barb,
                data=data_agendamento
            ).exclude(status=Agendamento.Status.CANCELADO).select_related('servico', 'barbeiro').prefetch_related('itens').order_by('horario'))

            # Bloqueios parciais do dia
            bloqueios_parciais = list(BloqueioAgenda.objects.filter(
                Q(barbeiro=barb) | Q(barbeiro__isnull=True),
                ativo=True,
                data_inicio__lte=data_agendamento,
                data_fim__gte=data_agendamento,
                horario_inicio__isnull=False
            ))

            # 4. Geração de candidatos: estritamente das 08:00 às 21:30 em passos de 5 minutos
            candidate_dt = datetime.combine(data_agendamento, CANDIDATO_INICIO)
            max_candidate_dt = datetime.combine(data_agendamento, CANDIDATO_FIM)
            step = timedelta(minutes=5)

            while candidate_dt <= max_candidate_dt:
                slot_inicio = candidate_dt.time()
                novo_fim_ocupado_dt = candidate_dt + timedelta(minutes=duracao_total + buffer_min)

                if data_agendamento == hoje and slot_inicio < hora_minima_hoje:
                    candidate_dt += step
                    continue

                # Verifica se o atendimento + buffer cabe dentro de algum turno da escala do barbeiro
                cabe_no_expediente = False
                abertura_turno = False
                for h_ini_turno, h_fim_turno in turnos:
                    turno_ini_dt = datetime.combine(data_agendamento, h_ini_turno)
                    turno_fim_dt = datetime.combine(data_agendamento, h_fim_turno)
                    if candidate_dt >= turno_ini_dt and novo_fim_ocupado_dt <= turno_fim_dt:
                        cabe_no_expediente = True
                        if candidate_dt == turno_ini_dt:
                            abertura_turno = True
                        break

                if not cabe_no_expediente:
                    candidate_dt += step
                    continue

                # 5. Colisão simétrica no intervalo de ocupação
                conflito = False
                colado_anterior = False
                colado_posterior = False

                for ag in agendamentos_dia:
                    ag_ini_dt = datetime.combine(data_agendamento, ag.horario)
                    ag_dur = ag.get_duracao_total()
                    ag_fim_ocupado_dt = ag_ini_dt + timedelta(minutes=ag_dur + buffer_min)

                    # Há conflito se: novo_inicio < existente_fim_ocupado e novo_fim_ocupado > existente_inicio
                    if candidate_dt < ag_fim_ocupado_dt and novo_fim_ocupado_dt > ag_ini_dt:
                        conflito = True
                        break

                    # Encaixe perfeito adjacente
                    if ag_fim_ocupado_dt == candidate_dt:
                        colado_anterior = True
                    if novo_fim_ocupado_dt == ag_ini_dt:
                        colado_posterior = True

                if conflito:
                    candidate_dt += step
                    continue

                # Verifica conflito com bloqueios parciais
                for bl in bloqueios_parciais:
                    bl_ini_dt = datetime.combine(data_agendamento, bl.horario_inicio)
                    bl_fim_dt = datetime.combine(data_agendamento, bl.horario_fim)
                    if candidate_dt < bl_fim_dt and novo_fim_ocupado_dt > bl_ini_dt:
                        conflito = True
                        break

                if conflito:
                    candidate_dt += step
                    continue

                # Cálculo do score de inteligência operacional
                score = 70
                if colado_anterior and colado_posterior:
                    score = 100
                elif colado_anterior or colado_posterior:
                    score = 90
                elif abertura_turno:
                    score = 85
                else:
                    score = 65

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
                    'duracao': duracao_total,
                    'score': min(100, score),
                    'recomendado': score >= 85
                })

                candidate_dt += step

        # Ordena por horário e score decrescente
        horarios_pontuados.sort(key=lambda x: (x['horario'], -x['score']))
        return horarios_pontuados

    @staticmethod
    def validar_e_bloquear_horario(
        barbeiro: Barbeiro,
        data_agendamento: date,
        horario: time,
        duracao_minutos: int,
        agendamento_id: int = None
    ) -> bool:
        """
        Valida e bloqueia transacionalmente com select_for_update se o horário solicitado
        está estritamente livre para o barbeiro na data, considerando a duração, buffer de 5 minutos,
        expediente da escala e bloqueios de agenda.
        Retorna True se válido e reservável, False caso haja qualquer colisão ou restrição.
        """
        CANDIDATO_INICIO = time(8, 0)
        CANDIDATO_FIM = time(21, 30)
        if horario < CANDIDATO_INICIO or horario > CANDIDATO_FIM:
            return False

        dia_semana = data_agendamento.weekday()
        buffer_min = 5

        # 1. Escala e Folga
        escala = EscalaBarbeiro.objects.filter(barbeiro=barbeiro, dia_semana=dia_semana, ativo=True).first()
        turnos = []
        if escala:
            if escala.folga:
                return False
            turnos.append((escala.horario_inicio_1, escala.horario_fim_1))
            if escala.horario_inicio_2 and escala.horario_fim_2:
                turnos.append((escala.horario_inicio_2, escala.horario_fim_2))
        else:
            turnos.append((time(8, 0), time(22, 40)))

        novo_ini_dt = datetime.combine(data_agendamento, horario)
        novo_fim_ocupado_dt = novo_ini_dt + timedelta(minutes=duracao_minutos + buffer_min)

        cabe_no_expediente = False
        for h_ini_turno, h_fim_turno in turnos:
            turno_ini_dt = datetime.combine(data_agendamento, h_ini_turno)
            turno_fim_dt = datetime.combine(data_agendamento, h_fim_turno)
            if novo_ini_dt >= turno_ini_dt and novo_fim_ocupado_dt <= turno_fim_dt:
                cabe_no_expediente = True
                break

        if not cabe_no_expediente:
            return False

        # 2. Bloqueios integrais e parciais
        if BloqueioAgenda.objects.filter(
            Q(barbeiro=barbeiro) | Q(barbeiro__isnull=True),
            ativo=True,
            data_inicio__lte=data_agendamento,
            data_fim__gte=data_agendamento,
            horario_inicio__isnull=True
        ).exists():
            return False

        bloqueios_parciais = BloqueioAgenda.objects.filter(
            Q(barbeiro=barbeiro) | Q(barbeiro__isnull=True),
            ativo=True,
            data_inicio__lte=data_agendamento,
            data_fim__gte=data_agendamento,
            horario_inicio__isnull=False
        )
        for bl in bloqueios_parciais:
            bl_ini_dt = datetime.combine(data_agendamento, bl.horario_inicio)
            bl_fim_dt = datetime.combine(data_agendamento, bl.horario_fim)
            if novo_ini_dt < bl_fim_dt and novo_fim_ocupado_dt > bl_ini_dt:
                return False

        # 3. Concorrência: select_for_update nos agendamentos da data
        agendamentos_qs = Agendamento.objects.select_for_update().filter(
            barbeiro=barbeiro,
            data=data_agendamento
        ).exclude(status=Agendamento.Status.CANCELADO)

        if agendamento_id:
            agendamentos_qs = agendamentos_qs.exclude(pk=agendamento_id)

        agendamentos = list(agendamentos_qs.prefetch_related('itens', 'servico'))
        for ag in agendamentos:
            ag_ini_dt = datetime.combine(data_agendamento, ag.horario)
            ag_dur = ag.get_duracao_total()
            ag_fim_ocupado_dt = ag_ini_dt + timedelta(minutes=ag_dur + buffer_min)

            if novo_ini_dt < ag_fim_ocupado_dt and novo_fim_ocupado_dt > ag_ini_dt:
                return False

        return True


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
