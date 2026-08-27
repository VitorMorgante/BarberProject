from decimal import Decimal
from datetime import date
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.utils import timezone
from website.models import (
    Barbeiro, Agendamento, Comanda, ItemComanda,
    RegraComissao, Comissao, RepasseComissao, MetaBarbeiro
)


class ComissaoService:
    @staticmethod
    @transaction.atomic
    def registrar_comissao_servico(barbeiro: Barbeiro, agendamento: Agendamento, valor_base: Decimal = None) -> Comissao:
        """
        Calcula e registra a comissão de serviço com snapshot do percentual do momento.
        """
        # Evita duplicidade
        if Comissao.objects.filter(agendamento=agendamento, tipo='servico').exists():
            return Comissao.objects.filter(agendamento=agendamento, tipo='servico').first()

        regra = RegraComissao.objects.filter(barbeiro=barbeiro, ativo=True).first()
        percentual = regra.percentual_servico if regra else Decimal('50.00')

        if valor_base is None:
            valor_base = agendamento.servico.preco

        valor_base = Decimal(str(valor_base))
        valor_comissao = (valor_base * percentual) / Decimal('100.00')

        comissao = Comissao.objects.create(
            barbeiro=barbeiro,
            agendamento=agendamento,
            tipo='servico',
            valor_base=valor_base,
            percentual_aplicado=percentual,
            valor_comissao=valor_comissao,
            status=Comissao.Status.PENDENTE,
        )
        return comissao

    @staticmethod
    @transaction.atomic
    def registrar_comissao_produto(barbeiro: Barbeiro, comanda: Comanda, item: ItemComanda) -> Comissao:
        """
        Calcula e registra a comissão de venda de produto por um barbeiro.
        """
        if item.tipo != ItemComanda.Tipo.PRODUTO or not item.produto:
            return None

        # Evita duplicidade
        if Comissao.objects.filter(item_comanda=item).exists():
            return Comissao.objects.filter(item_comanda=item).first()

        regra = RegraComissao.objects.filter(barbeiro=barbeiro, ativo=True).first()
        percentual = regra.percentual_produto if regra else Decimal('15.00')

        valor_base = Decimal(str(item.total))
        valor_comissao = (valor_base * percentual) / Decimal('100.00')

        comissao = Comissao.objects.create(
            barbeiro=barbeiro,
            comanda=comanda,
            item_comanda=item,
            tipo='produto',
            valor_base=valor_base,
            percentual_aplicado=percentual,
            valor_comissao=valor_comissao,
            status=Comissao.Status.PENDENTE,
        )
        return comissao

    @staticmethod
    def get_extrato_barbeiro(barbeiro: Barbeiro, data_inicio: date = None, data_fim: date = None):
        """
        Gera o extrato de faturamento e comissões do barbeiro para um período.
        """
        comissoes = Comissao.objects.filter(barbeiro=barbeiro)
        agendamentos = Agendamento.objects.filter(barbeiro=barbeiro, status='Concluído')

        if data_inicio:
            comissoes = comissoes.filter(criado_em__date__gte=data_inicio)
            agendamentos = agendamentos.filter(data__gte=data_inicio)
        if data_fim:
            comissoes = comissoes.filter(criado_em__date__lte=data_fim)
            agendamentos = agendamentos.filter(data__lte=data_fim)

        comissao_servicos = comissoes.filter(tipo='servico').aggregate(total=Sum('valor_comissao'))['total'] or Decimal('0.00')
        comissao_produtos = comissoes.filter(tipo='produto').aggregate(total=Sum('valor_comissao'))['total'] or Decimal('0.00')
        faturamento_servicos = comissoes.filter(tipo='servico').aggregate(total=Sum('valor_base'))['total'] or Decimal('0.00')
        faturamento_produtos = comissoes.filter(tipo='produto').aggregate(total=Sum('valor_base'))['total'] or Decimal('0.00')

        total_comissao = comissao_servicos + comissao_produtos
        total_faturamento = faturamento_servicos + faturamento_produtos
        qtd_atendimentos = agendamentos.count()

        repasses = RepasseComissao.objects.filter(barbeiro=barbeiro)
        if data_inicio:
            repasses = repasses.filter(data_repasse__date__gte=data_inicio)
        if data_fim:
            repasses = repasses.filter(data_repasse__date__lte=data_fim)

        total_repasses = repasses.aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        saldo_a_receber = max(Decimal('0.00'), total_comissao - total_repasses)

        return {
            'comissoes_lista': comissoes.order_by('-criado_em')[:50],
            'qtd_atendimentos': qtd_atendimentos,
            'faturamento_servicos': faturamento_servicos,
            'faturamento_produtos': faturamento_produtos,
            'faturamento_total': total_faturamento,
            'comissao_servicos': comissao_servicos,
            'comissao_produtos': comissao_produtos,
            'total_comissao': total_comissao,
            'total_repasses': total_repasses,
            'saldo_a_receber': saldo_a_receber,
        }

    @staticmethod
    def get_progresso_meta(barbeiro: Barbeiro, mes: int = None, ano: int = None):
        """
        Calcula o percentual de atingimento da meta mensal do barbeiro.
        """
        hoje = timezone.now().date()
        mes = mes or hoje.month
        ano = ano or hoje.year

        meta = MetaBarbeiro.objects.filter(barbeiro=barbeiro, mes=mes, ano=ano).first()
        meta_valor = meta.meta_faturamento if meta else Decimal('5000.00')
        meta_cortes = meta.meta_atendimentos if meta else 100

        agendamentos = Agendamento.objects.filter(
            barbeiro=barbeiro,
            status='Concluído',
            data__month=mes,
            data__year=ano
        )

        faturamento_real = Comissao.objects.filter(
            barbeiro=barbeiro,
            tipo='servico',
            criado_em__month=mes,
            criado_em__year=ano
        ).aggregate(total=Sum('valor_base'))['total'] or Decimal('0.00')

        cortes_real = agendamentos.count()
        porcentagem = min(100, int((faturamento_real / meta_valor) * 100)) if meta_valor > 0 else 0

        ticket_medio = (faturamento_real / cortes_real) if cortes_real > 0 else Decimal('0.00')

        return {
            'mes': mes,
            'ano': ano,
            'meta_faturamento': meta_valor,
            'faturamento_real': faturamento_real,
            'meta_cortes': meta_cortes,
            'cortes_real': cortes_real,
            'porcentagem': porcentagem,
            'ticket_medio': round(ticket_medio, 2),
        }
