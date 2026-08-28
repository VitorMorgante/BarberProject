from datetime import date, datetime, timedelta
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, Count, Q, Avg
from django.core.exceptions import ValidationError
from website.models import (
    CaixaDiario, MovimentacaoCaixa, Despesa, CategoriaDespesa,
    Comanda, ItemComanda, Comissao, AssinaturaCliente, Servico,
    Barbeiro, PagamentoDividido, TaxaMetodoPagamento, Agendamento
)


class FinanceService:
    """
    Motor Financeiro completo da Delacruz Barber:
    Caixa Diário, DRE Simplificada, Conciliação, Rentabilidade por Serviço e Barbeiro,
    Simuladores e Análise de Margens.
    """

    # --------------------------------------------------------------------------
    # 1. CAIXA DIÁRIO
    # --------------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def abrir_caixa(operador, saldo_inicial: Decimal = Decimal('100.00'), observacoes: str = '') -> CaixaDiario:
        """Abre uma nova sessão de caixa diário para o operador."""
        caixa_aberto = CaixaDiario.objects.filter(operador=operador, status=CaixaDiario.Status.ABERTO).first()
        if caixa_aberto:
            return caixa_aberto

        caixa = CaixaDiario.objects.create(
            operador=operador,
            saldo_inicial=saldo_inicial,
            saldo_esperado=saldo_inicial,
            status=CaixaDiario.Status.ABERTO,
            observacoes=observacoes
        )
        MovimentacaoCaixa.objects.create(
            caixa=caixa,
            tipo=MovimentacaoCaixa.Tipo.SUPRIMENTO,
            valor=saldo_inicial,
            motivo="Saldo inicial / Fundo de troco de abertura"
        )
        return caixa

    @staticmethod
    @transaction.atomic
    def registrar_movimentacao_caixa(caixa: CaixaDiario, tipo: str, valor: Decimal, motivo: str) -> MovimentacaoCaixa:
        """Registra sangria, suprimento ou despesa local no caixa aberto."""
        caixa = CaixaDiario.objects.select_for_update().get(pk=caixa.pk)
        if caixa.status != CaixaDiario.Status.ABERTO:
            raise ValidationError("O caixa não está aberto para movimentações.")

        mov = MovimentacaoCaixa.objects.create(
            caixa=caixa,
            tipo=tipo,
            valor=valor,
            motivo=motivo
        )

        if tipo in [MovimentacaoCaixa.Tipo.SUPRIMENTO, MovimentacaoCaixa.Tipo.VENDA]:
            caixa.saldo_esperado += valor
        elif tipo in [MovimentacaoCaixa.Tipo.SANGRIA, MovimentacaoCaixa.Tipo.DESPESA]:
            caixa.saldo_esperado -= valor

        caixa.save(update_fields=['saldo_esperado'])
        return mov

    @staticmethod
    @transaction.atomic
    def fechar_caixa(caixa: CaixaDiario, saldo_informado: Decimal, observacoes: str = '') -> CaixaDiario:
        """Fecha o caixa conferindo o valor informado pelo operador (conferência cega)."""
        caixa = CaixaDiario.objects.select_for_update().get(pk=caixa.pk)
        caixa.data_fechamento = timezone.now()
        caixa.saldo_dinheiro_informado = saldo_informado
        caixa.diferenca_quebra = saldo_informado - caixa.saldo_esperado
        caixa.status = CaixaDiario.Status.FECHADO
        if observacoes:
            caixa.observacoes = (caixa.observacoes + f" [Fechamento: {observacoes}]").strip()
        caixa.save()
        return caixa

    # --------------------------------------------------------------------------
    # 2. DRE SIMPLIFICADA & RESULTADO
    # --------------------------------------------------------------------------

    @staticmethod
    def gerar_dre_simplificado(mes: int = None, ano: int = None) -> dict:
        """
        Gera o Demonstrativo de Resultado do Exercício (DRE) para o período:
        Receita Bruta:
          + Receita de Serviços (Comandas)
          + Receita de Produtos (Comandas)
          + Receita de Assinaturas (Barber Club)
        Deduções:
          - Comissões de Barbeiros
          - Taxas de Pagamento / Gateways
          - Custo de Mercadorias / Insumos
        Despesas Operacionais:
          - Aluguel, Energia, Internet, Marketing, Manutenção, etc.
        = Resultado Líquido (Lucro / Prejuízo)
        """
        hoje = timezone.localtime().date()
        mes = mes or hoje.month
        ano = ano or hoje.year

        data_inicio = date(ano, mes, 1)
        if mes == 12:
            data_fim = date(ano + 1, 1, 1) - timedelta(days=1)
        else:
            data_fim = date(ano, mes + 1, 1) - timedelta(days=1)

        comandas = Comanda.objects.filter(
            status=Comanda.Status.FECHADA,
            fechada_em__date__gte=data_inicio,
            fechada_em__date__lte=data_fim
        )

        rec_servicos = ItemComanda.objects.filter(
            comanda__in=comandas,
            tipo__in=[ItemComanda.Tipo.SERVICO, ItemComanda.Tipo.ADICIONAL]
        ).aggregate(tot=Sum('total'))['tot'] or Decimal('0.00')

        rec_produtos = ItemComanda.objects.filter(
            comanda__in=comandas,
            tipo=ItemComanda.Tipo.PRODUTO
        ).aggregate(tot=Sum('total'))['tot'] or Decimal('0.00')

        rec_assinaturas = AssinaturaCliente.objects.filter(
            status=AssinaturaCliente.Status.ATIVA,
            data_inicio__lte=data_fim
        ).aggregate(tot=Sum('plano__preco_mensal'))['tot'] or Decimal('0.00')

        receita_bruta = rec_servicos + rec_produtos + rec_assinaturas

        # Comissões
        comissoes = Comissao.objects.filter(
            criado_em__date__gte=data_inicio,
            criado_em__date__lte=data_fim
        ).exclude(status=Comissao.Status.CANCELADA).aggregate(tot=Sum('valor_comissao'))['tot'] or Decimal('0.00')

        # Taxas de Cartão/Gateways
        taxas_total = Decimal('0.00')
        pagamentos_div = PagamentoDividido.objects.filter(
            comanda__in=comandas
        )
        for pg in pagamentos_div:
            if pg.taxa_percentual > 0:
                taxas_total += (pg.valor * pg.taxa_percentual) / Decimal('100.00')
        if taxas_total == Decimal('0.00'):
            # Estimativa de 2.5% sobre faturamento comanda
            taxas_total = (rec_servicos + rec_produtos) * Decimal('0.025')

        # Custo dos produtos vendidos (CMV)
        custo_produtos = Decimal('0.00')
        for item in ItemComanda.objects.filter(comanda__in=comandas, tipo=ItemComanda.Tipo.PRODUTO):
            if item.produto:
                custo_produtos += (item.produto.custo or Decimal('0.00')) * item.quantidade

        # Despesas Operacionais por Categoria
        despesas_qs = Despesa.objects.filter(
            status=Despesa.Status.PAGO,
            data_pagamento__gte=data_inicio,
            data_pagamento__lte=data_fim
        )
        despesas_por_cat = {}
        for desp in despesas_qs:
            cat_nome = desp.categoria.nome
            despesas_por_cat[cat_nome] = despesas_por_cat.get(cat_nome, Decimal('0.00')) + desp.valor

        total_despesas = sum(despesas_por_cat.values(), Decimal('0.00'))

        # Margem de Contribuição e Lucro Líquido
        margem_contribuicao = receita_bruta - comissoes - taxas_total - custo_produtos
        lucro_liquido = margem_contribuicao - total_despesas
        margem_lucro_percentual = (lucro_liquido / receita_bruta * 100) if receita_bruta > 0 else Decimal('0.00')

        return {
            'mes': mes,
            'ano': ano,
            'periodo': f"{mes:02d}/{ano}",
            'receita_servicos': rec_servicos,
            'receita_produtos': rec_produtos,
            'receita_assinaturas': rec_assinaturas,
            'receita_bruta': receita_bruta,
            'deducoes_comissoes': comissoes,
            'deducoes_taxas': taxas_total,
            'deducoes_cmv': custo_produtos,
            'total_deducoes': comissoes + taxas_total + custo_produtos,
            'margem_contribuicao': margem_contribuicao,
            'despesas_por_categoria': despesas_por_cat,
            'total_despesas': total_despesas,
            'lucro_liquido': lucro_liquido,
            'margem_lucro_percentual': round(margem_lucro_percentual, 2),
            'is_positivo': lucro_liquido >= 0
        }

    # --------------------------------------------------------------------------
    # 3. RENTABILIDADE POR SERVIÇO & BARBEIRO
    # --------------------------------------------------------------------------

    @staticmethod
    def calcular_rentabilidade_servicos() -> list:
        """
        Calcula a rentabilidade unitária e por hora de cada serviço ativo:
        Preço - Comissão Padrão (50%) - Taxa Cartão (2.5%) - Insumos Médios = Margem Unitária e Margem/Hora
        """
        servicos = Servico.objects.filter(ativo=True)
        relatorio = []

        for s in servicos:
            preco = s.preco
            duracao_min = s.duracao_minutos or 30
            comissao_estimada = preco * Decimal('0.50')
            taxa_estimada = preco * Decimal('0.025')
            custo_insumos = Decimal('3.50')  # Custo médio estimado de insumos

            margem = preco - comissao_estimada - taxa_estimada - custo_insumos
            margem_perc = (margem / preco * 100) if preco > 0 else Decimal('0.00')
            receita_por_hora = (preco / duracao_min) * 60
            margem_por_hora = (margem / duracao_min) * 60

            relatorio.append({
                'servico': s,
                'preco': preco,
                'duracao_min': duracao_min,
                'comissao': comissao_estimada,
                'taxas': taxa_estimada,
                'insumos': custo_insumos,
                'margem_unitaria': margem,
                'margem_percentual': round(margem_perc, 1),
                'receita_por_hora': round(receita_por_hora, 2),
                'margem_por_hora': round(margem_por_hora, 2)
            })

        relatorio.sort(key=lambda x: x['margem_por_hora'], reverse=True)
        return relatorio

    # --------------------------------------------------------------------------
    # 4. SIMULADORES FINANCEIROS
    # --------------------------------------------------------------------------

    @staticmethod
    def simular_reajuste_preco(servico_id: int, novo_preco: Decimal, variacao_demanda: float = 0.0) -> dict:
        """
        Simula o impacto financeiro de alterar o preço de um serviço sem persistir no banco.
        """
        servico = Servico.objects.get(pk=servico_id)
        preco_antigo = servico.preco
        atendimentos_mes = Agendamento.objects.filter(
            servico=servico,
            status=Agendamento.Status.CONCLUIDO,
            data__gte=timezone.now().date() - timedelta(days=30)
        ).count() or 40

        volume_projetado = int(round(atendimentos_mes * (1 + variacao_demanda)))
        receita_antiga = preco_antigo * atendimentos_mes
        receita_nova = novo_preco * volume_projetado
        diferenca_receita = receita_nova - receita_antiga

        return {
            'servico': servico,
            'preco_antigo': preco_antigo,
            'novo_preco': novo_preco,
            'volume_base': atendimentos_mes,
            'volume_projetado': volume_projetado,
            'receita_atual_mes': receita_antiga,
            'receita_projetada_mes': receita_nova,
            'impacto_faturamento': diferenca_receita,
            'percentual_variacao': round(((diferenca_receita / max(1, receita_antiga)) * 100), 2)
        }

    @staticmethod
    def simular_comissao(barbeiro_id: int, novo_percentual_servico: Decimal) -> dict:
        """
        Simula a alteração do percentual de comissão de um profissional.
        """
        barbeiro = Barbeiro.objects.get(pk=barbeiro_id)
        comissoes_30d = Comissao.objects.filter(
            barbeiro=barbeiro,
            tipo='servico',
            criado_em__gte=timezone.now() - timedelta(days=30)
        )
        base_faturamento = comissoes_30d.aggregate(tot=Sum('valor_base'))['tot'] or Decimal('4000.00')
        comissao_atual = comissoes_30d.aggregate(tot=Sum('valor_comissao'))['tot'] or Decimal('2000.00')

        comissao_simulada = (base_faturamento * novo_percentual_servico) / Decimal('100.00')
        diferenca_barbearia = comissao_atual - comissao_simulada  # Positivo = barbearia lucra mais

        return {
            'barbeiro': barbeiro,
            'base_faturamento_30d': base_faturamento,
            'comissao_atual_30d': comissao_atual,
            'novo_percentual': novo_percentual_servico,
            'comissao_simulada_30d': comissao_simulada,
            'impacto_caixa_barbearia': diferenca_barbearia
        }

    @staticmethod
    def simular_promocao(servico_id: int, percentual_desconto: Decimal, elasticidade: float = 1.3) -> dict:
        """
        Simula o impacto de uma promoção com desconto na margem e volume de vendas.
        """
        servico = Servico.objects.get(pk=servico_id)
        preco_cheio = servico.preco
        preco_promo = preco_cheio * (Decimal('100.00') - percentual_desconto) / Decimal('100.00')

        atendimentos_base = 30
        aumento_volume = (float(percentual_desconto) / 100.0) * elasticidade
        volume_estimado = int(round(atendimentos_base * (1 + aumento_volume)))

        receita_base = preco_cheio * atendimentos_base
        receita_promo = preco_promo * volume_estimado

        return {
            'servico': servico,
            'preco_original': preco_cheio,
            'preco_promocional': preco_promo,
            'desconto_percentual': percentual_desconto,
            'volume_base': atendimentos_base,
            'volume_projetado': volume_estimado,
            'receita_base': receita_base,
            'receita_projetada': receita_promo,
            'resultado_impacto': receita_promo - receita_base
        }
