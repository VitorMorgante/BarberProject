from django.contrib import admin
from .models import (
    UnidadeBarbearia, Servico, Barbeiro, BarbeiroServico, EscalaBarbeiro, BloqueioAgenda,
    Cliente, PerfilDependente, ContaCorrenteCliente, MovimentacaoContaCorrente,
    HorarioDisponivel, Agendamento, MensagemContato, PerfilUsuario, Feedback, AvaliacaoDetalhada,
    FotoTrabalho, PlanoAssinatura, AssinaturaCliente, MovimentacaoCredito, PacoteServico,
    ProgramaFidelidade, ProgressoFidelidade, RecompensaFidelidade, LocalEstoque,
    Produto, SaldoEstoqueLocal, TransferenciaEstoque, PerdaEstoque, KitConsumoServico,
    ItemKitConsumo, Fornecedor, PedidoCompra, ItemPedidoCompra, InventarioEstoque,
    ItemInventarioEstoque, LoteValidade, MovimentacaoEstoque, Comanda, ItemComanda,
    PagamentoDividido, Gorjeta, RegraComissao, Comissao, RepasseComissao, MetaBarbeiro,
    MetaGlobal, RegistroPontoBarbeiro, CaixaDiario, MovimentacaoCaixa, CategoriaDespesa,
    Despesa, TaxaMetodoPagamento, ConfiguracaoEstabelecimento, Pagamento, EventoWebhookPagamento,
    ListaEspera, Notificacao, RegraAutomacao, EstiloCorte, AnaliseEstilo, HistoricoVisualCliente,
    FichaTecnicaCorte, TarefaRecepcao, HandoffTurno, OcorrenciaOperacional, ChecklistOperacional,
    ItemChecklistOperacional, RegistroHigienizacao, Equipamento, ManutencaoEquipamento,
    RegistroAuditoria, AprovacaoAcaoSensivel, ConsentimentoCliente, DadosFiscaisEmpresa,
    PushSubscription, CupomDesconto
)


@admin.register(UnidadeBarbearia)
class UnidadeBarbeariaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cidade', 'estado', 'telefone', 'is_matriz', 'ativo']
    list_filter = ['is_matriz', 'ativo']


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'preco', 'duracao_minutos', 'categoria', 'ativo', 'destaque', 'ordem']
    list_filter = ['ativo', 'destaque', 'categoria']
    search_fields = ['nome']


@admin.register(Barbeiro)
class BarbeiroAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cargo', 'nivel', 'tempo_buffer_depois', 'ativo']
    list_filter = ['ativo', 'nivel', 'cargo']


@admin.register(BarbeiroServico)
class BarbeiroServicoAdmin(admin.ModelAdmin):
    list_display = ['barbeiro', 'servico', 'duracao_minutos', 'preco_customizado', 'comissao_customizada', 'ativo']
    list_filter = ['barbeiro', 'servico', 'ativo']


@admin.register(EscalaBarbeiro)
class EscalaBarbeiroAdmin(admin.ModelAdmin):
    list_display = ['barbeiro', 'dia_semana', 'horario_inicio_1', 'horario_fim_1', 'horario_inicio_2', 'horario_fim_2', 'folga', 'ativo']
    list_filter = ['barbeiro', 'dia_semana', 'folga', 'ativo']


@admin.register(BloqueioAgenda)
class BloqueioAgendaAdmin(admin.ModelAdmin):
    list_display = ['barbeiro', 'tipo', 'data_inicio', 'data_fim', 'horario_inicio', 'horario_fim', 'ativo']
    list_filter = ['tipo', 'ativo', 'barbeiro']


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'telefone', 'email', 'codigo_indicacao', 'canal_origem', 'cadastrado_em']
    search_fields = ['nome', 'telefone', 'email', 'codigo_indicacao']


@admin.register(PerfilDependente)
class PerfilDependenteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cliente_titular', 'parentesco', 'data_nascimento']
    search_fields = ['nome', 'cliente_titular__nome']


@admin.register(ContaCorrenteCliente)
class ContaCorrenteClienteAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'saldo', 'atualizado_em']
    search_fields = ['cliente__nome']


@admin.register(MovimentacaoContaCorrente)
class MovimentacaoContaCorrenteAdmin(admin.ModelAdmin):
    list_display = ['conta_corrente', 'tipo', 'valor', 'saldo_anterior', 'saldo_posterior', 'criado_em']
    list_filter = ['tipo']


@admin.register(HorarioDisponivel)
class HorarioDisponivelAdmin(admin.ModelAdmin):
    list_display = ['barbeiro', 'horario', 'ativo']
    list_filter = ['barbeiro', 'ativo']


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'dependente', 'servico', 'barbeiro', 'data', 'horario', 'status', 'is_walkin', 'criado_em']
    list_filter = ['status', 'barbeiro', 'data', 'is_walkin']
    search_fields = ['cliente__nome', 'dependente__nome']


@admin.register(MensagemContato)
class MensagemContatoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'email', 'telefone', 'lida', 'enviada_em']
    list_filter = ['lida']


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'tipo_usuario', 'telefone', 'pode_aplicar_desconto', 'pode_estornar', 'pode_ver_financeiro', 'criado_em']
    list_filter = ['tipo_usuario', 'pode_aplicar_desconto', 'pode_ver_financeiro']


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'barbeiro', 'nota', 'criado_em', 'aprovado']
    list_filter = ['nota', 'aprovado', 'barbeiro']


@admin.register(AvaliacaoDetalhada)
class AvaliacaoDetalhadaAdmin(admin.ModelAdmin):
    list_display = ['feedback', 'nota_atendimento', 'nota_pontualidade', 'nota_resultado', 'nota_ambiente']


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


@admin.register(PacoteServico)
class PacoteServicoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'preco_original', 'preco_promocional', 'ativo', 'destaque']
    list_filter = ['ativo', 'destaque']


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


@admin.register(LocalEstoque)
class LocalEstoqueAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'barbeiro_responsavel', 'ativo']
    list_filter = ['tipo', 'ativo']


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'sku', 'categoria', 'custo', 'preco', 'estoque_atual', 'estoque_minimo', 'is_insumo_interno', 'ativo']
    list_filter = ['categoria', 'is_insumo_interno', 'ativo']
    search_fields = ['nome', 'sku']


@admin.register(SaldoEstoqueLocal)
class SaldoEstoqueLocalAdmin(admin.ModelAdmin):
    list_display = ['produto', 'local', 'quantidade']
    list_filter = ['local']


@admin.register(TransferenciaEstoque)
class TransferenciaEstoqueAdmin(admin.ModelAdmin):
    list_display = ['produto', 'origem', 'destino', 'quantidade', 'criada_em']
    list_filter = ['origem', 'destino']


@admin.register(PerdaEstoque)
class PerdaEstoqueAdmin(admin.ModelAdmin):
    list_display = ['produto', 'local', 'quantidade', 'motivo', 'usuario', 'criada_em']
    list_filter = ['motivo', 'local']


class ItemKitConsumoInline(admin.TabularInline):
    model = ItemKitConsumo
    extra = 1


@admin.register(KitConsumoServico)
class KitConsumoServicoAdmin(admin.ModelAdmin):
    list_display = ['servico', 'ativo']
    inlines = [ItemKitConsumoInline]


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ['nome_empresa', 'contato_nome', 'telefone', 'email', 'prazo_entrega_dias', 'ativo']
    search_fields = ['nome_empresa', 'cnpj']


class ItemPedidoCompraInline(admin.TabularInline):
    model = ItemPedidoCompra
    extra = 1


@admin.register(PedidoCompra)
class PedidoCompraAdmin(admin.ModelAdmin):
    list_display = ['id', 'fornecedor', 'status', 'data_pedido', 'data_entrega_prevista', 'valor_total']
    list_filter = ['status', 'fornecedor']
    inlines = [ItemPedidoCompraInline]


class ItemInventarioEstoqueInline(admin.TabularInline):
    model = ItemInventarioEstoque
    extra = 1


@admin.register(InventarioEstoque)
class InventarioEstoqueAdmin(admin.ModelAdmin):
    list_display = ['id', 'local', 'data_inventario', 'status', 'usuario_responsavel']
    list_filter = ['status', 'local']
    inlines = [ItemInventarioEstoqueInline]


@admin.register(LoteValidade)
class LoteValidadeAdmin(admin.ModelAdmin):
    list_display = ['produto', 'numero_lote', 'data_validade', 'quantidade', 'ativo']
    list_filter = ['ativo', 'data_validade']


@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ['produto', 'tipo', 'quantidade', 'saldo_anterior', 'saldo_posterior', 'usuario', 'criado_em']
    list_filter = ['tipo', 'produto']


class ItemComandaInline(admin.TabularInline):
    model = ItemComanda
    extra = 1


class PagamentoDivididoInline(admin.TabularInline):
    model = PagamentoDividido
    extra = 1


@admin.register(Comanda)
class ComandaAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'barbeiro', 'status', 'subtotal', 'desconto', 'valor_total', 'metodo_pagamento', 'criada_em']
    list_filter = ['status', 'barbeiro']
    inlines = [ItemComandaInline, PagamentoDivididoInline]


@admin.register(Gorjeta)
class GorjetaAdmin(admin.ModelAdmin):
    list_display = ['barbeiro', 'comanda', 'valor', 'repassada', 'data_repasse', 'criada_em']
    list_filter = ['repassada', 'barbeiro']


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


@admin.register(MetaGlobal)
class MetaGlobalAdmin(admin.ModelAdmin):
    list_display = ['mes', 'ano', 'meta_faturamento', 'meta_atendimentos', 'meta_produtos', 'meta_ocupacao_percentual']
    list_filter = ['ano', 'mes']


@admin.register(RegistroPontoBarbeiro)
class RegistroPontoBarbeiroAdmin(admin.ModelAdmin):
    list_display = ['barbeiro', 'data', 'hora_entrada', 'hora_saida', 'total_horas']
    list_filter = ['barbeiro', 'data']


@admin.register(CaixaDiario)
class CaixaDiarioAdmin(admin.ModelAdmin):
    list_display = ['id', 'operador', 'data_abertura', 'saldo_inicial', 'saldo_esperado', 'saldo_dinheiro_informado', 'diferenca_quebra', 'status']
    list_filter = ['status', 'operador']


@admin.register(MovimentacaoCaixa)
class MovimentacaoCaixaAdmin(admin.ModelAdmin):
    list_display = ['caixa', 'tipo', 'valor', 'motivo', 'criada_em']
    list_filter = ['tipo']


@admin.register(CategoriaDespesa)
class CategoriaDespesaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'ativo']
    list_filter = ['tipo', 'ativo']


@admin.register(Despesa)
class DespesaAdmin(admin.ModelAdmin):
    list_display = ['descricao', 'categoria', 'valor', 'data_vencimento', 'status']
    list_filter = ['status', 'categoria']


@admin.register(TaxaMetodoPagamento)
class TaxaMetodoPagamentoAdmin(admin.ModelAdmin):
    list_display = ['metodo', 'taxa_percentual', 'taxa_fixa_reais', 'ativo']


@admin.register(ConfiguracaoEstabelecimento)
class ConfiguracaoEstabelecimentoAdmin(admin.ModelAdmin):
    list_display = ['tipo_sinal', 'valor_sinal', 'antecedencia_minima_minutos', 'janela_maxima_dias', 'meta_ocupacao_percentual']


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


@admin.register(RegraAutomacao)
class RegraAutomacaoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo', 'ativo', 'dias_disparo', 'atualizado_em']
    list_filter = ['tipo', 'ativo']


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


@admin.register(FichaTecnicaCorte)
class FichaTecnicaCorteAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'barbeiro', 'tipo_fade', 'acabamento', 'data', 'criada_em']
    list_filter = ['barbeiro', 'data']
    search_fields = ['cliente__nome']


@admin.register(TarefaRecepcao)
class TarefaRecepcaoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo', 'data_limite', 'concluida', 'responsavel']
    list_filter = ['tipo', 'concluida']


@admin.register(HandoffTurno)
class HandoffTurnoAdmin(admin.ModelAdmin):
    list_display = ['turno_origem', 'turno_destino', 'usuario_emissor', 'criado_em']


@admin.register(OcorrenciaOperacional)
class OcorrenciaOperacionalAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo', 'resolvida', 'usuario', 'criada_em']
    list_filter = ['tipo', 'resolvida']


@admin.register(ChecklistOperacional)
class ChecklistOperacionalAdmin(admin.ModelAdmin):
    list_display = ['tipo', 'data', 'usuario', 'concluido']
    list_filter = ['tipo', 'concluido']


@admin.register(RegistroHigienizacao)
class RegistroHigienizacaoAdmin(admin.ModelAdmin):
    list_display = ['tipo_procedimento', 'responsavel', 'data_hora']
    list_filter = ['tipo_procedimento']


@admin.register(Equipamento)
class EquipamentoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'numero_serie', 'barbeiro_responsavel', 'proxima_manutencao', 'ativo']
    list_filter = ['tipo', 'ativo']


@admin.register(ManutencaoEquipamento)
class ManutencaoEquipamentoAdmin(admin.ModelAdmin):
    list_display = ['equipamento', 'tipo', 'data_realizada', 'custo', 'prestador_servico']
    list_filter = ['tipo']


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'acao', 'tabela_afetada', 'registro_id', 'ip', 'data_hora']
    list_filter = ['acao', 'tabela_afetada']


@admin.register(AprovacaoAcaoSensivel)
class AprovacaoAcaoSensivelAdmin(admin.ModelAdmin):
    list_display = ['solicitante', 'tipo', 'status', 'aprovador', 'criado_em']
    list_filter = ['tipo', 'status']


@admin.register(ConsentimentoCliente)
class ConsentimentoClienteAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'fotos_privadas', 'fotos_portfolio', 'ia_visagismo', 'whatsapp_notificacoes', 'atualizado_em']


@admin.register(DadosFiscaisEmpresa)
class DadosFiscaisEmpresaAdmin(admin.ModelAdmin):
    list_display = ['razao_social', 'cnpj', 'regime_tributario', 'aliquota_iss']


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'criada_em']


@admin.register(CupomDesconto)
class CupomDescontoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'tipo', 'valor', 'usos_atuais', 'limite_usos', 'valido_ate', 'ativo']
    list_filter = ['tipo', 'ativo', 'valido_ate']
    search_fields = ['codigo', 'descricao']
