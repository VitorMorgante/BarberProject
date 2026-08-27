from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from website.models import Produto, MovimentacaoEstoque


class InventoryService:
    @staticmethod
    @transaction.atomic
    def movimentar_estoque(produto: Produto, tipo: str, quantidade: int, motivo: str = '', usuario=None) -> MovimentacaoEstoque:
        """
        Executa movimentação atômica de estoque e impede estoque negativo.
        quantidade: positiva para entrada/devolução, positiva para saída (o método ajusta o sinal).
        """
        # Bloqueia a linha no banco para evitar race conditions
        produto_db = Produto.objects.select_for_update().get(pk=produto.pk)
        saldo_anterior = produto_db.estoque_atual

        if tipo in [MovimentacaoEstoque.Tipo.ENTRADA, MovimentacaoEstoque.Tipo.DEVOLUCAO]:
            delta = abs(quantidade)
        elif tipo in [MovimentacaoEstoque.Tipo.VENDA, MovimentacaoEstoque.Tipo.PERDA]:
            delta = -abs(quantidade)
        elif tipo == MovimentacaoEstoque.Tipo.AJUSTE:
            delta = quantidade  # pode ser positivo ou negativo
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
    def get_produtos_estoque_baixo():
        """Retorna produtos cujo estoque_atual <= estoque_minimo."""
        return Produto.objects.filter(ativo=True, estoque_atual__lte=models_f_expression())


def models_f_expression():
    from django.db.models import F
    return F('estoque_minimo')
