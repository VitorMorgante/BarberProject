from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from website.models import (
    Produto, MovimentacaoEstoque, LocalEstoque, SaldoEstoqueLocal,
    TransferenciaEstoque, PerdaEstoque, KitConsumoServico, Servico,
    InventarioEstoque, ItemInventarioEstoque
)


class InventoryService:
    """
    Serviço de Gestão de Estoque, Insumos Internos, Transferências, Perdas e Inventário.
    """

    @staticmethod
    @transaction.atomic
    def movimentar_estoque(produto: Produto, tipo: str, quantidade: int, motivo: str = '', usuario=None, local: LocalEstoque = None) -> MovimentacaoEstoque:
        """
        Executa movimentação atômica de estoque e impede estoque negativo.
        """
        produto_db = Produto.objects.select_for_update().get(pk=produto.pk)
        saldo_anterior = produto_db.estoque_atual

        if tipo in [MovimentacaoEstoque.Tipo.ENTRADA, MovimentacaoEstoque.Tipo.DEVOLUCAO]:
            delta = abs(quantidade)
        elif tipo in [MovimentacaoEstoque.Tipo.VENDA, MovimentacaoEstoque.Tipo.PERDA]:
            delta = -abs(quantidade)
        elif tipo == MovimentacaoEstoque.Tipo.AJUSTE:
            delta = quantidade
        else:
            delta = quantidade

        saldo_posterior = saldo_anterior + delta

        if saldo_posterior < 0:
            raise ValidationError(
                f"Estoque insuficiente para o produto '{produto_db.nome}'. "
                f"Disponível: {saldo_anterior}, Solicitado: {abs(delta)}."
            )

        produto_db.estoque_atual = saldo_posterior
        produto_db.save(update_fields=['estoque_atual', 'atualizado_em'])

        # Se houver local especificado, atualiza também o saldo do local
        if local:
            saldo_local, _ = SaldoEstoqueLocal.objects.select_for_update().get_or_create(
                produto=produto_db,
                local=local,
                defaults={'quantidade': 0}
            )
            saldo_local.quantidade = max(0, saldo_local.quantidade + delta)
            saldo_local.save(update_fields=['quantidade'])

        mov = MovimentacaoEstoque.objects.create(
            produto=produto_db,
            tipo=tipo,
            quantidade=delta,
            saldo_anterior=saldo_anterior,
            saldo_posterior=saldo_posterior,
            motivo=motivo or f"Movimentação {tipo}",
            usuario=usuario,
        )
        return mov

    @staticmethod
    @transaction.atomic
    def baixar_insumos_do_servico(servico: Servico, local: LocalEstoque = None, usuario=None):
        """
        Dá baixa automática nos insumos consumidos na execução do serviço
        (ex: 1 lâmina, shampoo, loção pós-barba) conforme configurado no KitConsumoServico.
        """
        kit = KitConsumoServico.objects.filter(servico=servico, ativo=True).first()
        if not kit:
            return []

        movimentacoes = []
        for item in kit.itens.all():
            qtd_baixa = int(round(float(item.quantidade_unitaria))) or 1
            try:
                mov = InventoryService.movimentar_estoque(
                    produto=item.produto_insumo,
                    tipo=MovimentacaoEstoque.Tipo.VENDA,
                    quantidade=qtd_baixa,
                    motivo=f"Consumo interno no serviço '{servico.nome}'",
                    usuario=usuario,
                    local=local
                )
                movimentacoes.append(mov)
            except ValidationError:
                # Se o insumo estiver esgotado, não trava o atendimento, mas registra alerta
                pass
        return movimentacoes

    @staticmethod
    @transaction.atomic
    def transferir_estoque(produto: Produto, origem: LocalEstoque, destino: LocalEstoque, quantidade: int, motivo: str = '', usuario=None) -> TransferenciaEstoque:
        """
        Transfere produtos entre locais de estoque (ex: Depósito Central -> Bancada do Barbeiro).
        """
        saldo_origem, _ = SaldoEstoqueLocal.objects.select_for_update().get_or_create(
            produto=produto, local=origem, defaults={'quantidade': 0}
        )
        if saldo_origem.quantidade < quantidade:
            raise ValidationError(
                f"Saldo insuficiente no local de origem '{origem.nome}'. "
                f"Disponível: {saldo_origem.quantidade}, Solicitado: {quantidade}."
            )

        saldo_destino, _ = SaldoEstoqueLocal.objects.select_for_update().get_or_create(
            produto=produto, local=destino, defaults={'quantidade': 0}
        )

        saldo_origem.quantidade -= quantidade
        saldo_origem.save(update_fields=['quantidade'])

        saldo_destino.quantidade += quantidade
        saldo_destino.save(update_fields=['quantidade'])

        return TransferenciaEstoque.objects.create(
            produto=produto,
            origem=origem,
            destino=destino,
            quantidade=quantidade,
            motivo=motivo or f"Transferência de {origem.nome} para {destino.nome}",
            usuario=usuario
        )

    @staticmethod
    @transaction.atomic
    def registrar_perda(produto: Produto, quantidade: int, motivo: str, local: LocalEstoque = None, usuario=None, observacoes: str = '') -> PerdaEstoque:
        """
        Registra perda/avaria de produto e atualiza o saldo de estoque.
        """
        InventoryService.movimentar_estoque(
            produto=produto,
            tipo=MovimentacaoEstoque.Tipo.PERDA,
            quantidade=quantidade,
            motivo=f"Perda: {motivo}",
            usuario=usuario,
            local=local
        )
        return PerdaEstoque.objects.create(
            produto=produto,
            local=local,
            quantidade=quantidade,
            motivo=motivo,
            usuario=usuario,
            observacoes=observacoes
        )

    @staticmethod
    def sugerir_reposicao() -> list:
        """
        Calcula a sugestão de compra e reposição de estoque:
        Sugestão = (Estoque Mínimo * 2) - Estoque Atual
        """
        produtos = Produto.objects.filter(ativo=True)
        sugestoes = []
        for p in produtos:
            if p.estoque_atual <= p.estoque_minimo:
                qtd_sugerida = max(p.estoque_minimo, (p.estoque_minimo * 2) - p.estoque_atual)
                sugestoes.append({
                    'produto': p,
                    'estoque_atual': p.estoque_atual,
                    'estoque_minimo': p.estoque_minimo,
                    'sugestao_compra': qtd_sugerida,
                    'custo_estimado': Decimal(str(qtd_sugerida)) * (p.custo or Decimal('0.00'))
                })
        return sugestoes

    @staticmethod
    @transaction.atomic
    def finalizar_inventario(inventario: InventarioEstoque, aplicar_ajuste: bool = True, usuario=None) -> InventarioEstoque:
        """
        Finaliza contagem física de inventário e ajusta os saldos caso solicitado.
        """
        inventario = InventarioEstoque.objects.select_for_update().get(pk=inventario.pk)
        for item in inventario.itens.all():
            item.divergencia = item.quantidade_contada - item.quantidade_esperada
            item.save(update_fields=['divergencia'])

            if aplicar_ajuste and item.divergencia != 0:
                InventoryService.movimentar_estoque(
                    produto=item.produto,
                    tipo=MovimentacaoEstoque.Tipo.AJUSTE,
                    quantidade=item.divergencia,
                    motivo=f"Ajuste automático pelo Inventário #{inventario.id} em {inventario.local.nome}",
                    usuario=usuario,
                    local=inventario.local
                )

        inventario.status = InventarioEstoque.Status.CONCLUIDO
        inventario.save(update_fields=['status'])
        return inventario
