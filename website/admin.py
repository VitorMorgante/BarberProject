from django.contrib import admin
from .models import (
    Servico, Barbeiro, Cliente, HorarioDisponivel, Agendamento,
    MensagemContato, PerfilUsuario, Feedback, FotoTrabalho,
    PlanoAssinatura, AssinaturaCliente, MovimentacaoCredito,
    ProgramaFidelidade, ProgressoFidelidade, RecompensaFidelidade,
    Produto, MovimentacaoEstoque, Comanda, ItemComanda,
    RegraComissao, Comissao, RepasseComissao, MetaBarbeiro,
    ConfiguracaoEstabelecimento, Pagamento, EventoWebhookPagamento,
    ListaEspera, Notificacao, EstiloCorte, AnaliseEstilo,
    HistoricoVisualCliente, PushSubscription, CupomDesconto
)


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'preco', 'duracao_minutos', 'categoria', 'ativo', 'destaque', 'ordem']
    list_filter = ['ativo', 'destaque', 'categoria']
    search_fields = ['nome']


@admin.register(Barbeiro)
class BarbeiroAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cargo', 'especialidade', 'ativo']
    list_filter = ['ativo', 'cargo']


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'telefone', 'email', 'cadastrado_em']
    search_fields = ['nome', 'telefone', 'email']


@admin.register(HorarioDisponivel)
class HorarioDisponivelAdmin(admin.ModelAdmin):
    list_display = ['barbeiro', 'horario', 'ativo']
    list_filter = ['barbeiro', 'ativo']


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'servico', 'barbeiro', 'data', 'horario', 'status', 'criado_em']
    list_filter = ['status', 'barbeiro', 'data']
    search_fields = ['cliente__nome']


@admin.register(MensagemContato)
class MensagemContatoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'email', 'telefone', 'lida', 'enviada_em']
    list_filter = ['lida']


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'tipo_usuario', 'telefone', 'criado_em']
    list_filter = ['tipo_usuario']


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'barbeiro', 'nota', 'criado_em', 'aprovado']
    list_filter = ['nota', 'aprovado', 'barbeiro']


@admin.register(FotoTrabalho)
class FotoTrabalhoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'barbeiro', 'categoria', 'publicado', 'criado_em']
    list_filter = ['categoria', 'publicado', 'barbeiro']


@admin.register(PlanoAssinatura)
class PlanoAssinaturaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'preco_mensal', 'quantidade_creditos', 'desconto_produtos', 'ativo', 'destaque']
    list_filter = ['ativo', 'destaque']


@admin.register(AssinaturaCliente)
class AssinaturaClienteAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'plano', 'status', 'creditos_disponiveis', 'creditos_utilizados', 'data_renovacao']
    list_filter = ['status', 'plano']
    search_fields = ['cliente__nome']


@admin.register(MovimentacaoCredito)
class MovimentacaoCreditoAdmin(admin.ModelAdmin):
    list_display = ['assinatura', 'tipo', 'quantidade', 'saldo_posterior', 'criado_em']
    list_filter = ['tipo']


@admin.register(ProgramaFidelidade)
class ProgramaFidelidadeAdmin(admin.ModelAdmin):
    list_display = ['nome', 'servicos_necessarios', 'tipo_recompensa', 'valor_desconto', 'ativo']


@admin.register(ProgressoFidelidade)
class ProgressoFidelidadeAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'servicos_concluidos', 'total_historico', 'recompensas_acumuladas']


@admin.register(RecompensaFidelidade)
class RecompensaFidelidadeAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'descricao', 'status', 'data_gerada', 'data_utilizada']
    list_filter = ['status']


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'sku', 'categoria', 'custo', 'preco', 'estoque_atual', 'estoque_minimo', 'ativo']
    list_filter = ['categoria', 'ativo']
    search_fields = ['nome', 'sku']


@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ['produto', 'tipo', 'quantidade', 'saldo_anterior', 'saldo_posterior', 'usuario', 'criado_em']
    list_filter = ['tipo', 'produto']


class ItemComandaInline(admin.TabularInline):
    model = ItemComanda
    extra = 1


@admin.register(Comanda)
class ComandaAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'barbeiro', 'status', 'subtotal', 'desconto', 'valor_total', 'criada_em']
    list_filter = ['status', 'barbeiro']
    inlines = [ItemComandaInline]


@admin.register(RegraComissao)
class RegraComissaoAdmin(admin.ModelAdmin):
    list_display = ['barbeiro', 'percentual_servico', 'percentual_produto', 'ativo']


@admin.register(Comissao)
class ComissaoAdmin(admin.ModelAdmin):
    list_display = ['barbeiro', 'tipo', 'valor_base', 'percentual_aplicado', 'valor_comissao', 'status', 'criado_em']
    list_filter = ['status', 'tipo', 'barbeiro']


@admin.register(RepasseComissao)
class RepasseComissaoAdmin(admin.ModelAdmin):
    list_display = ['barbeiro', 'valor', 'periodo_inicio', 'periodo_fim', 'data_repasse']


@admin.register(MetaBarbeiro)
class MetaBarbeiroAdmin(admin.ModelAdmin):
    list_display = ['barbeiro', 'mes', 'ano', 'meta_faturamento', 'meta_atendimentos', 'meta_produtos']
    list_filter = ['ano', 'mes', 'barbeiro']


@admin.register(ConfiguracaoEstabelecimento)
class ConfiguracaoEstabelecimentoAdmin(admin.ModelAdmin):
    list_display = ['tipo_sinal', 'valor_sinal', 'minutos_expiracao_pix', 'chave_pix', 'titular_pix']


@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ['identificador_interno', 'valor', 'tipo', 'metodo', 'status', 'gateway', 'criado_em', 'pago_em']
    list_filter = ['status', 'tipo', 'metodo', 'gateway']


@admin.register(EventoWebhookPagamento)
class EventoWebhookPagamentoAdmin(admin.ModelAdmin):
    list_display = ['gateway', 'evento_id', 'processado', 'data_recebimento']
    list_filter = ['processado', 'gateway']


@admin.register(ListaEspera)
class ListaEsperaAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'servico', 'barbeiro', 'data_desejada', 'horario_inicio', 'horario_fim', 'status']
    list_filter = ['status', 'data_desejada']


@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'canal', 'tipo', 'status', 'data_prevista', 'enviada_em']
    list_filter = ['status', 'canal', 'tipo']


@admin.register(EstiloCorte)
class EstiloCorteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo_cabelo', 'formato_rosto', 'manutencao', 'ativo']
    list_filter = ['ativo']


@admin.register(AnaliseEstilo)
class AnaliseEstiloAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'formato_rosto_detectado', 'confianca', 'criado_em']
    search_fields = ['cliente__nome', 'formato_rosto_detectado']


@admin.register(HistoricoVisualCliente)
class HistoricoVisualClienteAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'barbeiro', 'agendamento', 'consentimento', 'data']
    list_filter = ['barbeiro', 'data']
    search_fields = ['cliente__nome']


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'criada_em']


@admin.register(CupomDesconto)
class CupomDescontoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'tipo', 'valor', 'usos_atuais', 'limite_usos', 'valido_ate', 'ativo']
    list_filter = ['tipo', 'ativo', 'valido_ate']
    search_fields = ['codigo', 'descricao']
