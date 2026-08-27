from django.db import transaction
from django.utils import timezone
from website.models import Cliente, Agendamento, ProgramaFidelidade, ProgressoFidelidade, RecompensaFidelidade


class LoyaltyService:
    @staticmethod
    @transaction.atomic
    def processar_atendimento_concluido(agendamento: Agendamento) -> ProgressoFidelidade:
        """
        Contabiliza +1 corte elegível para o cliente após agendamento concluído.
        Se atingir a meta do programa (ex: 10 cortes), gera 1 RecompensaFidelidade.
        """
        cliente = agendamento.cliente
        programa = ProgramaFidelidade.objects.filter(ativo=True).first()
        meta = programa.servicos_necessarios if programa else 10

        progresso, _ = ProgressoFidelidade.objects.select_for_update().get_or_create(
            cliente=cliente,
            defaults={'servicos_concluidos': 0, 'total_historico': 0, 'recompensas_acumuladas': 0}
        )

        progresso.servicos_concluidos += 1
        progresso.total_historico += 1

        if progresso.servicos_concluidos >= meta:
            # Gera a recompensa
            progresso.servicos_concluidos -= meta
            progresso.recompensas_acumuladas += 1

            descricao = "1 Corte Gratuito pelo Programa Fidelidade"
            if programa and programa.tipo_recompensa == ProgramaFidelidade.TipoRecompensa.DESCONTO_PERCENTUAL:
                descricao = f"{programa.valor_desconto}% de Desconto pelo Programa Fidelidade"
            elif programa and programa.tipo_recompensa == ProgramaFidelidade.TipoRecompensa.DESCONTO_FIXO:
                descricao = f"R$ {programa.valor_desconto} de Desconto pelo Programa Fidelidade"

            RecompensaFidelidade.objects.create(
                cliente=cliente,
                status=RecompensaFidelidade.Status.DISPONIVEL,
                descricao=descricao,
            )

        progresso.save()
        return progresso

    @staticmethod
    @transaction.atomic
    def resgatar_recompensa(cliente: Cliente, agendamento: Agendamento = None) -> RecompensaFidelidade:
        """
        Aplica a primeira recompensa disponível do cliente a um agendamento.
        """
        recompensa = RecompensaFidelidade.objects.select_for_update().filter(
            cliente=cliente,
            status=RecompensaFidelidade.Status.DISPONIVEL
        ).first()

        if recompensa:
            recompensa.status = RecompensaFidelidade.Status.UTILIZADA
            recompensa.agendamento_resgate = agendamento
            recompensa.data_utilizada = timezone.now()
            recompensa.save()

        return recompensa

    @staticmethod
    def get_resumo_cliente(cliente: Cliente):
        """Retorna dados de fidelidade para renderização na Área do Cliente."""
        programa = ProgramaFidelidade.objects.filter(ativo=True).first()
        meta = programa.servicos_necessarios if programa else 10

        progresso, _ = ProgressoFidelidade.objects.get_or_create(
            cliente=cliente,
            defaults={'servicos_concluidos': 0, 'total_historico': 0}
        )

        atual = progresso.servicos_concluidos
        faltam = max(0, meta - atual)
        porcentagem = min(100, int((atual / meta) * 100)) if meta > 0 else 0

        recompensas_disponiveis = RecompensaFidelidade.objects.filter(
            cliente=cliente,
            status=RecompensaFidelidade.Status.DISPONIVEL
        )

        return {
            'progresso': progresso,
            'atual': atual,
            'meta': meta,
            'faltam': faltam,
            'porcentagem': porcentagem,
            'total_historico': progresso.total_historico,
            'tem_recompensa': recompensas_disponiveis.exists(),
            'recompensas_disponiveis': recompensas_disponiveis,
            'qtd_recompensas': recompensas_disponiveis.count(),
        }
