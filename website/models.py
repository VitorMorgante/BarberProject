import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone


# ==============================================================================
# MODELOS EXISTENTES (PRESERVADOS E EXPANDIDOS)
# ==============================================================================

class Servico(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    nome = models.CharField(max_length=200)
    descricao = models.TextField()
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    duracao_minutos = models.PositiveIntegerField()
    categoria = models.CharField(max_length=100, default='Geral')
    icone = models.CharField(max_length=100, default='bi bi-scissors')
    ativo = models.BooleanField(default=True)
    destaque = models.BooleanField(default=False)
    ordem = models.PositiveIntegerField(default=0)
    cadastrado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ordem', 'nome']
        verbose_name = 'Serviço'
        verbose_name_plural = 'Serviços'

    def __str__(self):
        return f"{self.nome} (R$ {self.preco})"


class Barbeiro(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    nome = models.CharField(max_length=200)
    cargo = models.CharField(max_length=100)
    especialidade = models.CharField(max_length=300)
    descricao_curta = models.TextField(blank=True)
    imagem_url = models.URLField(blank=True)
    ativo = models.BooleanField(default=True)
    cadastrado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Barbeiro'
        verbose_name_plural = 'Barbeiros'

    def __str__(self):
        return self.nome


class Cliente(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    nome = models.CharField(max_length=200)
    telefone = models.CharField(max_length=20)
    email = models.EmailField()
    observacoes = models.TextField(blank=True)
    cadastrado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} - {self.telefone}'


class HorarioDisponivel(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.PROTECT, related_name='horarios')
    horario = models.TimeField()
    ativo = models.BooleanField(default=True)
    observacao = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Horário Disponível'
        verbose_name_plural = 'Horários Disponíveis'
        unique_together = ['barbeiro', 'horario']
        ordering = ['horario']

    def __str__(self):
        return f'{self.barbeiro.nome} - {self.horario.strftime("%H:%M")}'


class Agendamento(models.Model):
    class Status(models.TextChoices):
        PENDENTE = 'Pendente', 'Pendente'
        CONFIRMADO = 'Confirmado', 'Confirmado'
        EM_ATENDIMENTO = 'Em Atendimento', 'Em Atendimento'
        CONCLUIDO = 'Concluído', 'Concluído'
        CANCELADO = 'Cancelado', 'Cancelado'
        NAO_COMPARECEU = 'Não Compareceu', 'Não Compareceu'

    usuario = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='agendamentos')
    servico = models.ForeignKey(Servico, on_delete=models.PROTECT, related_name='agendamentos')
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.PROTECT, related_name='agendamentos')
    data = models.DateField()
    horario = models.TimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE)
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Agendamento'
        verbose_name_plural = 'Agendamentos'
        ordering = ['-data', '-horario']
        constraints = [
            models.UniqueConstraint(
                fields=['barbeiro', 'data', 'horario'],
                condition=~Q(status='Cancelado'),
                name='unique_agendamento_ativo_por_horario',
            )
        ]

    def __str__(self):
        return (
            f'{self.cliente.nome} - {self.servico.nome} com {self.barbeiro.nome} '
            f'em {self.data.strftime("%d/%m/%Y")} às {self.horario.strftime("%H:%M")} [{self.status}]'
        )


class MensagemContato(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    nome = models.CharField(max_length=200)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    mensagem = models.TextField()
    lida = models.BooleanField(default=False)
    enviada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Mensagem de Contato'
        verbose_name_plural = 'Mensagens de Contato'
        ordering = ['-enviada_em']

    def __str__(self):
        return f'{self.nome} - {self.enviada_em.strftime("%d/%m/%Y")}'


class PerfilUsuario(models.Model):
    TIPO_CHOICES = [
        ('cliente', 'Cliente'),
        ('barbeiro', 'Barbeiro'),
        ('administrador', 'Administrador'),
    ]
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_CHOICES, default='cliente')
    telefone = models.CharField(max_length=20)
    foto_perfil = models.ImageField(upload_to='perfis/', blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'

    def __str__(self):
        return f'{self.usuario.username} - {self.tipo_usuario}'


class Feedback(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='feedbacks')
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.CASCADE, related_name='feedbacks')
    agendamento = models.OneToOneField(Agendamento, on_delete=models.CASCADE, related_name='feedback')
    nota = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comentario = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    aprovado = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Feedback'
        verbose_name_plural = 'Feedbacks'

    def __str__(self):
        return f'Feedback de {self.cliente.nome} para {self.barbeiro.nome} - Nota {self.nota}'


class FotoTrabalho(models.Model):
    CATEGORIA_CHOICES = [
        ('Corte', 'Corte'),
        ('Barba', 'Barba'),
        ('Corte + Barba', 'Corte + Barba'),
        ('Infantil', 'Infantil'),
        ('Outro', 'Outro'),
    ]
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.CASCADE, related_name='fotos')
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    imagem = models.ImageField(upload_to='galeria/')
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES, default='Corte')
    publicado = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Foto de Trabalho (Portfólio)'
        verbose_name_plural = 'Fotos de Trabalho (Portfólio)'

    def __str__(self):
        return self.titulo


# ==============================================================================
# 1. BARBER CLUB (ASSINATURA E CRÉDITOS RECORRENTES)
# ==============================================================================

class PlanoAssinatura(models.Model):
    nome = models.CharField(max_length=200)
    descricao = models.TextField()
    preco_mensal = models.DecimalField(max_digits=8, decimal_places=2)
    quantidade_creditos = models.PositiveIntegerField(default=4, help_text="Cortes/serviços inclusos por mês")
    servicos = models.ManyToManyField(Servico, related_name='planos_assinatura', blank=True)
    desconto_produtos = models.DecimalField(max_digits=5, decimal_places=2, default=10.00, help_text="% de desconto em produtos")
    permite_acumular = models.BooleanField(default=False)
    validade_dias = models.PositiveIntegerField(default=30)
    ativo = models.BooleanField(default=True)
    destaque = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Plano de Assinatura (Barber Club)'
        verbose_name_plural = 'Planos de Assinatura (Barber Club)'
        ordering = ['preco_mensal']

    def __str__(self):
        return f"{self.nome} - R$ {self.preco_mensal}/mês ({self.quantidade_creditos} créditos)"


class AssinaturaCliente(models.Model):
    class Status(models.TextChoices):
        ATIVA = 'Ativa', 'Ativa'
        PENDENTE = 'Pendente', 'Pendente'
        ATRASADA = 'Atrasada', 'Atrasada'
        CANCELADA = 'Cancelada', 'Cancelada'
        EXPIRADA = 'Expirada', 'Expirada'

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='assinaturas')
    plano = models.ForeignKey(PlanoAssinatura, on_delete=models.PROTECT, related_name='assinaturas_clientes')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ATIVA)
    data_inicio = models.DateField(default=timezone.now)
    data_renovacao = models.DateField()
    data_termino = models.DateField(null=True, blank=True)
    creditos_disponiveis = models.PositiveIntegerField(default=0)
    creditos_utilizados = models.PositiveIntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Assinatura de Cliente'
        verbose_name_plural = 'Assinaturas de Clientes'
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.cliente.nome} - {self.plano.nome} [{self.status}] ({self.creditos_disponiveis} créditos)"

    @property
    def is_active(self):
        return self.status == self.Status.ATIVA


class MovimentacaoCredito(models.Model):
    class Tipo(models.TextChoices):
        CREDITO_MENSAL = 'credito_mensal', 'Crédito Mensal'
        CONSUMO = 'consumo', 'Consumo em Agendamento'
        ESTORNO = 'estorno', 'Estorno de Cancelamento'
        AJUSTE = 'ajuste', 'Ajuste Manual'

    assinatura = models.ForeignKey(AssinaturaCliente, on_delete=models.CASCADE, related_name='movimentacoes')
    agendamento = models.ForeignKey(Agendamento, on_delete=models.SET_NULL, null=True, blank=True, related_name='movimentacoes_credito')
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    quantidade = models.IntegerField(help_text="Positivo para adição, negativo para consumo")
    saldo_anterior = models.IntegerField()
    saldo_posterior = models.IntegerField()
    descricao = models.CharField(max_length=255)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Movimentação de Crédito'
        verbose_name_plural = 'Movimentações de Crédito'
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.assinatura.cliente.nome}: {self.tipo} ({self.quantidade:+d}) => Saldo: {self.saldo_posterior}"


# ==============================================================================
# 2. FIDELIDADE DIGITAL
# ==============================================================================

class ProgramaFidelidade(models.Model):
    class TipoRecompensa(models.TextChoices):
        CORTE_GRATIS = 'corte_gratis', 'Corte Gratuito'
        DESCONTO_PERCENTUAL = 'desconto_percentual', 'Desconto Percentual'
        DESCONTO_FIXO = 'desconto_fixo', 'Desconto Fixo (R$)'

    nome = models.CharField(max_length=100, default='Fidelidade Delacruz')
    servicos_necessarios = models.PositiveIntegerField(default=10, help_text="Cortes concluídos para gerar recompensa")
    tipo_recompensa = models.CharField(max_length=30, choices=TipoRecompensa.choices, default=TipoRecompensa.CORTE_GRATIS)
    valor_desconto = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, help_text="Valor em % ou R$, se aplicável")
    servico_recompensa = models.ForeignKey(Servico, on_delete=models.SET_NULL, null=True, blank=True, related_name='recompensas_fidelidade')
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Programa de Fidelidade'
        verbose_name_plural = 'Programas de Fidelidade'

    def __str__(self):
        return f"{self.nome} ({self.servicos_necessarios} cortes = {self.get_tipo_recompensa_display()})"


class ProgressoFidelidade(models.Model):
    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE, related_name='fidelidade')
    servicos_concluidos = models.PositiveIntegerField(default=0, help_text="Progresso atual no ciclo")
    total_historico = models.PositiveIntegerField(default=0, help_text="Total acumulado desde o cadastro")
    recompensas_acumuladas = models.PositiveIntegerField(default=0)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Progresso de Fidelidade'
        verbose_name_plural = 'Progressos de Fidelidade'

    def __str__(self):
        return f"{self.cliente.nome}: {self.servicos_concluidos}/10 cortes (Total: {self.total_historico})"


class RecompensaFidelidade(models.Model):
    class Status(models.TextChoices):
        DISPONIVEL = 'Disponível', 'Disponível'
        UTILIZADA = 'Utilizada', 'Utilizada'
        EXPIRADA = 'Expirada', 'Expirada'

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='recompensas')
    agendamento_resgate = models.ForeignKey(Agendamento, on_delete=models.SET_NULL, null=True, blank=True, related_name='recompensa_utilizada')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DISPONIVEL)
    descricao = models.CharField(max_length=255, default='1 Corte Gratuito pelo Programa Fidelidade')
    data_gerada = models.DateTimeField(auto_now_add=True)
    data_utilizada = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Recompensa de Fidelidade'
        verbose_name_plural = 'Recompensas de Fidelidade'
        ordering = ['-data_gerada']

    def __str__(self):
        return f"{self.cliente.nome} - {self.descricao} [{self.status}]"


# ==============================================================================
# 3. PRODUTOS, ESTOQUE E PDV / COMANDAS
# ==============================================================================

class Produto(models.Model):
    nome = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True, null=True, blank=True)
    descricao = models.TextField(blank=True)
    categoria = models.CharField(max_length=100, default='Cabelo & Barba')
    custo = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    estoque_atual = models.IntegerField(default=0)
    estoque_minimo = models.IntegerField(default=5)
    unidade = models.CharField(max_length=20, default='un')
    imagem = models.ImageField(upload_to='produtos/', null=True, blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} - R$ {self.preco} (Estoque: {self.estoque_atual})"

    @property
    def is_estoque_baixo(self):
        return self.estoque_atual <= self.estoque_minimo


class MovimentacaoEstoque(models.Model):
    class Tipo(models.TextChoices):
        ENTRADA = 'entrada', 'Entrada de Estoque'
        VENDA = 'venda', 'Venda / Consumo'
        DEVOLUCAO = 'devolucao', 'Devolução / Estorno'
        AJUSTE = 'ajuste', 'Ajuste Manual'
        PERDA = 'perda', 'Perda / Avaria'

    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='movimentacoes')
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    quantidade = models.IntegerField(help_text="Positivo para entrada, negativo para saída")
    saldo_anterior = models.IntegerField()
    saldo_posterior = models.IntegerField()
    motivo = models.CharField(max_length=255, blank=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Movimentação de Estoque'
        verbose_name_plural = 'Movimentações de Estoque'
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.produto.nome}: {self.tipo} ({self.quantidade:+d}) => Saldo: {self.saldo_posterior}"


class Comanda(models.Model):
    class Status(models.TextChoices):
        ABERTA = 'Aberta', 'Aberta'
        FECHADA = 'Fechada', 'Fechada'
        CANCELADA = 'Cancelada', 'Cancelada'

    agendamento = models.OneToOneField(Agendamento, on_delete=models.SET_NULL, null=True, blank=True, related_name='comanda')
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='comandas')
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.PROTECT, related_name='comandas')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ABERTA)
    subtotal = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    desconto = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    sinal_pago = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    creditos_abatidos = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    valor_total = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    metodo_pagamento = models.CharField(max_length=50, blank=True, default='Pix')
    observacoes = models.TextField(blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)
    fechada_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Comanda / Venda PDV'
        verbose_name_plural = 'Comandas / Vendas PDV'
        ordering = ['-criada_em']

    def __str__(self):
        return f"Comanda #{self.id} - {self.cliente.nome} ({self.barbeiro.nome}) - Total: R$ {self.valor_total} [{self.status}]"

    def recalcular(self):
        total_itens = sum(Decimal(str(item.total)) for item in self.itens.all())
        self.subtotal = Decimal(str(total_itens))
        desconto = Decimal(str(self.desconto or 0))
        sinal = Decimal(str(self.sinal_pago or 0))
        creditos = Decimal(str(self.creditos_abatidos or 0))
        final = self.subtotal - desconto - sinal - creditos
        self.valor_total = max(Decimal('0.00'), final)
        self.save()


class ItemComanda(models.Model):
    class Tipo(models.TextChoices):
        SERVICO = 'servico', 'Serviço'
        PRODUTO = 'produto', 'Produto'
        ADICIONAL = 'adicional', 'Adicional'

    comanda = models.ForeignKey(Comanda, on_delete=models.CASCADE, related_name='itens')
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    servico = models.ForeignKey(Servico, on_delete=models.SET_NULL, null=True, blank=True)
    produto = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True, blank=True)
    descricao = models.CharField(max_length=200)
    quantidade = models.PositiveIntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=8, decimal_places=2)
    total = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        verbose_name = 'Item de Comanda'
        verbose_name_plural = 'Itens de Comanda'

    def __str__(self):
        return f"{self.descricao} ({self.quantidade}x R$ {self.preco_unitario}) = R$ {self.total}"

    def save(self, *args, **kwargs):
        self.total = Decimal(str(self.quantidade)) * Decimal(str(self.preco_unitario))
        super().save(*args, **kwargs)


# ==============================================================================
# 4. COMISSÕES E METAS FINANCEIRAS
# ==============================================================================

class RegraComissao(models.Model):
    barbeiro = models.OneToOneField(Barbeiro, on_delete=models.CASCADE, related_name='regra_comissao')
    percentual_servico = models.DecimalField(max_digits=5, decimal_places=2, default=50.00, help_text="% de comissão em serviços")
    percentual_produto = models.DecimalField(max_digits=5, decimal_places=2, default=15.00, help_text="% de comissão em produtos")
    ativo = models.BooleanField(default=True)
    inicio_vigencia = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = 'Regra de Comissão'
        verbose_name_plural = 'Regras de Comissões'

    def __str__(self):
        return f"{self.barbeiro.nome}: {self.percentual_servico}% serviços / {self.percentual_produto}% produtos"


class Comissao(models.Model):
    class Status(models.TextChoices):
        PENDENTE = 'Pendente', 'Pendente'
        PAGA = 'Paga', 'Paga'
        CANCELADA = 'Cancelada', 'Cancelada'

    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.CASCADE, related_name='comissoes')
    agendamento = models.ForeignKey(Agendamento, on_delete=models.SET_NULL, null=True, blank=True, related_name='comissoes')
    comanda = models.ForeignKey(Comanda, on_delete=models.SET_NULL, null=True, blank=True, related_name='comissoes')
    item_comanda = models.ForeignKey(ItemComanda, on_delete=models.SET_NULL, null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=[('servico', 'Serviço'), ('produto', 'Produto')])
    valor_base = models.DecimalField(max_digits=8, decimal_places=2)
    percentual_aplicado = models.DecimalField(max_digits=5, decimal_places=2)
    valor_comissao = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Comissão'
        verbose_name_plural = 'Comissões'
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.barbeiro.nome}: R$ {self.valor_comissao} ({self.tipo} - {self.percentual_aplicado}%) [{self.status}]"


class RepasseComissao(models.Model):
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.CASCADE, related_name='repasses')
    valor = models.DecimalField(max_digits=8, decimal_places=2)
    periodo_inicio = models.DateField()
    periodo_fim = models.DateField()
    data_repasse = models.DateTimeField(auto_now_add=True)
    usuario_responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    observacao = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Repasse de Comissão'
        verbose_name_plural = 'Repasses de Comissões'
        ordering = ['-data_repasse']

    def __str__(self):
        return f"Repasse {self.barbeiro.nome} - R$ {self.valor} ({self.periodo_inicio} a {self.periodo_fim})"


class MetaBarbeiro(models.Model):
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.CASCADE, related_name='metas')
    mes = models.PositiveIntegerField()
    ano = models.PositiveIntegerField()
    meta_faturamento = models.DecimalField(max_digits=10, decimal_places=2, default=5000.00)
    meta_atendimentos = models.PositiveIntegerField(default=100)
    meta_produtos = models.PositiveIntegerField(default=20)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Meta do Barbeiro'
        verbose_name_plural = 'Metas dos Barbeiros'
        unique_together = ['barbeiro', 'mes', 'ano']

    def __str__(self):
        return f"Meta {self.barbeiro.nome} - {self.mes}/{self.ano} (R$ {self.meta_faturamento})"


# ==============================================================================
# 5. CONFIGURAÇÃO, PAGAMENTOS, SINAL E PIX
# ==============================================================================

class ConfiguracaoEstabelecimento(models.Model):
    class TipoSinal(models.TextChoices):
        NENHUM = 'nenhum', 'Sem Sinal Obrigatório'
        PERCENTUAL = 'percentual', 'Percentual do Serviço (%)'
        FIXO = 'fixo', 'Valor Fixo (R$)'
        INTEGRAL = 'integral', 'Pagamento Integral (100%)'

    tipo_sinal = models.CharField(max_length=20, choices=TipoSinal.choices, default=TipoSinal.NENHUM)
    valor_sinal = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, help_text="% ou R$ fixo")
    minutos_expiracao_pix = models.PositiveIntegerField(default=15)
    chave_pix = models.CharField(max_length=100, default='delacruzbarber@email.com')
    titular_pix = models.CharField(max_length=150, default='Delacruz Barber')
    cidade_pix = models.CharField(max_length=100, default='Paranavai')
    lembrete_horas_antes = models.PositiveIntegerField(default=24)
    cancelamento_antecedencia_horas = models.PositiveIntegerField(default=2)

    class Meta:
        verbose_name = 'Configuração do Estabelecimento'
        verbose_name_plural = 'Configurações do Estabelecimento'

    def __str__(self):
        return f"Configurações Delacruz Barber (Sinal: {self.get_tipo_sinal_display()})"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj


class Pagamento(models.Model):
    class Status(models.TextChoices):
        AGUARDANDO = 'Aguardando', 'Aguardando Pagamento'
        PAGO = 'Pago', 'Pago / Confirmado'
        EXPIRADO = 'Expirado', 'Expirado'
        CANCELADO = 'Cancelado', 'Cancelado'
        REEMBOLSADO = 'Reembolsado', 'Reembolsado'

    class Tipo(models.TextChoices):
        SINAL = 'sinal', 'Sinal de Agendamento'
        TOTAL = 'total', 'Pagamento Total Agendamento'
        COMANDA = 'comanda', 'Fechamento de Comanda'
        ASSINATURA = 'assinatura', 'Assinatura Barber Club'

    class Metodo(models.TextChoices):
        PIX = 'pix', 'PIX Dinâmico'
        CARTAO_CREDITO = 'cartao_credito', 'Cartão de Crédito'
        CARTAO_DEBITO = 'cartao_debito', 'Cartão de Débito'
        DINHEIRO = 'dinheiro', 'Dinheiro'

    identificador_interno = models.CharField(max_length=64, unique=True, default=uuid.uuid4, db_index=True)
    identificador_externo = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    agendamento = models.ForeignKey(Agendamento, on_delete=models.SET_NULL, null=True, blank=True, related_name='pagamentos')
    comanda = models.ForeignKey(Comanda, on_delete=models.SET_NULL, null=True, blank=True, related_name='pagamentos')
    assinatura = models.ForeignKey(AssinaturaCliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='pagamentos')
    valor = models.DecimalField(max_digits=8, decimal_places=2)
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.SINAL)
    metodo = models.CharField(max_length=30, choices=Metodo.choices, default=Metodo.PIX)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AGUARDANDO)
    qr_code_base64 = models.TextField(blank=True)
    pix_copia_cola = models.TextField(blank=True)
    gateway = models.CharField(max_length=50, default='mock')
    payload_resposta = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    pago_em = models.DateTimeField(null=True, blank=True)
    expiracao_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
        ordering = ['-criado_em']

    def __str__(self):
        return f"Pagamento #{self.id} - R$ {self.valor} [{self.status}] ({self.tipo})"


class EventoWebhookPagamento(models.Model):
    gateway = models.CharField(max_length=50)
    evento_id = models.CharField(max_length=150, unique=True)
    payload = models.TextField()
    processado = models.BooleanField(default=False)
    data_recebimento = models.DateTimeField(auto_now_add=True)
    erro = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Webhook de Pagamento'
        verbose_name_plural = 'Webhooks de Pagamentos'
        ordering = ['-data_recebimento']

    def __str__(self):
        return f"Webhook {self.gateway} #{self.evento_id} (Processado: {self.processado})"


# ==============================================================================
# 6. COMUNICAÇÃO, LEMBRETES E LISTA DE ESPERA
# ==============================================================================

class ListaEspera(models.Model):
    class Status(models.TextChoices):
        AGUARDANDO = 'Aguardando', 'Aguardando Vaga'
        NOTIFICADO = 'Notificado', 'Notificado sobre Vaga'
        AGENDADO = 'Agendado', 'Agendado com Sucesso'
        EXPIRADO = 'Expirado', 'Expirado'
        CANCELADO = 'Cancelado', 'Cancelado'

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='waitlist')
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE, related_name='waitlist')
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.SET_NULL, null=True, blank=True, related_name='waitlist')
    data_desejada = models.DateField()
    horario_inicio = models.TimeField()
    horario_fim = models.TimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AGUARDANDO)
    criado_em = models.DateTimeField(auto_now_add=True)
    notificado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Lista de Espera'
        verbose_name_plural = 'Listas de Espera'
        ordering = ['data_desejada', 'horario_inicio']

    def __str__(self):
        barbeiro_txt = self.barbeiro.nome if self.barbeiro else "Qualquer Barbeiro"
        return f"{self.cliente.nome} - {self.data_desejada.strftime('%d/%m/%Y')} ({self.horario_inicio.strftime('%H:%M')} às {self.horario_fim.strftime('%H:%M')}) [{self.status}]"


class Notificacao(models.Model):
    class Canal(models.TextChoices):
        WHATSAPP = 'whatsapp', 'WhatsApp'
        PUSH = 'push', 'Web Push'
        SISTEMA = 'sistema', 'Sistema'

    class Tipo(models.TextChoices):
        LEMBRETE_24H = 'lembrete_24h', 'Lembrete 24 Horas'
        LEMBRETE_2H = 'lembrete_2h', 'Lembrete 2 Horas'
        CONFIRMACAO = 'confirmacao', 'Confirmação de Horário'
        WAITLIST_VAGA = 'waitlist_vaga', 'Vaga em Lista de Espera'
        RECOMPENSA = 'recompensa', 'Recompensa de Fidelidade'

    class Status(models.TextChoices):
        PENDENTE = 'Pendente', 'Pendente'
        ENVIADA = 'Enviada', 'Enviada'
        ERRO = 'Erro', 'Erro no Envio'

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='notificacoes')
    agendamento = models.ForeignKey(Agendamento, on_delete=models.SET_NULL, null=True, blank=True, related_name='notificacoes')
    canal = models.CharField(max_length=20, choices=Canal.choices, default=Canal.WHATSAPP)
    tipo = models.CharField(max_length=30, choices=Tipo.choices, default=Tipo.LEMBRETE_24H)
    mensagem = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE)
    data_prevista = models.DateTimeField()
    enviada_em = models.DateTimeField(null=True, blank=True)
    erro = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Notificação / Lembrete'
        verbose_name_plural = 'Notificações e Lembretes'
        ordering = ['-data_prevista']

    def __str__(self):
        return f"Notificação {self.canal} para {self.cliente.nome} [{self.status}]"


# ==============================================================================
# 7. CONSULTORIA DE ESTILO / IA E HISTÓRICO VISUAL PRIVADO
# ==============================================================================

class EstiloCorte(models.Model):
    nome = models.CharField(max_length=200)
    descricao = models.TextField()
    tipo_cabelo = models.CharField(max_length=100, default='Liso, Ondulado, Crespo')
    formato_rosto = models.CharField(max_length=100, default='Oval, Quadrado, Redondo')
    manutencao = models.CharField(max_length=100, default='A cada 15 a 20 dias')
    imagem = models.ImageField(upload_to='estilos/', null=True, blank=True)
    servico_relacionado = models.ForeignKey(Servico, on_delete=models.SET_NULL, null=True, blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Estilo de Corte (Catálogo)'
        verbose_name_plural = 'Estilos de Corte (Catálogo)'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} (Formatos: {self.formato_rosto})"


class AnaliseEstilo(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='analises_estilo')
    imagem = models.ImageField(upload_to='analises_ia/')
    formato_rosto_detectado = models.CharField(max_length=50)
    confianca = models.DecimalField(max_digits=5, decimal_places=2, default=0.85)
    recomendacao_texto = models.TextField()
    estilos_sugeridos = models.ManyToManyField(EstiloCorte, related_name='analises', blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Análise de Estilo por IA'
        verbose_name_plural = 'Análises de Estilos por IA'
        ordering = ['-criado_em']

    def __str__(self):
        return f"Análise de {self.cliente.nome} - Formato: {self.formato_rosto_detectado} ({self.criado_em.strftime('%d/%m/%Y')})"


class HistoricoVisualCliente(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='fotos_evolucao')
    agendamento = models.ForeignKey(Agendamento, on_delete=models.SET_NULL, null=True, blank=True, related_name='fotos_resultado')
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.PROTECT, related_name='fotos_clientes')
    imagem = models.ImageField(upload_to='historico_visual/')
    consentimento = models.BooleanField(default=True, help_text="Consentimento do cliente para registro privado")
    observacoes = models.TextField(blank=True)
    data = models.DateField(default=timezone.now)

    class Meta:
        verbose_name = 'Histórico Visual Privado do Cliente'
        verbose_name_plural = 'Históricos Visuais Privados dos Clientes'
        ordering = ['-data']

    def __str__(self):
        return f"Evolução {self.cliente.nome} com {self.barbeiro.nome} em {self.data.strftime('%d/%m/%Y')}"


# ==============================================================================
# 8. PWA / WEB PUSH NOTIFICATIONS
# ==============================================================================

class PushSubscription(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscriptions')
    endpoint = models.TextField()
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Inscrição Web Push'
        verbose_name_plural = 'Inscrições Web Push'

    def __str__(self):
        return f"Push para {self.usuario.username} ({self.criada_em.strftime('%d/%m/%Y')})"


# ==============================================================================
# 9. CUPONS DE DESCONTO & PROMOÇÕES
# ==============================================================================

class CupomDesconto(models.Model):
    class Tipo(models.TextChoices):
        PERCENTUAL = 'percentual', 'Percentual (%)'
        FIXO = 'fixo', 'Valor Fixo (R$)'

    codigo = models.CharField(max_length=30, unique=True, db_index=True)
    descricao = models.CharField(max_length=150, blank=True)
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.PERCENTUAL)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    valor_minimo_pedido = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    limite_usos = models.PositiveIntegerField(null=True, blank=True, help_text="Vazio = Ilimitado")
    usos_atuais = models.PositiveIntegerField(default=0)
    valido_ate = models.DateField(null=True, blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cupom de Desconto'
        verbose_name_plural = 'Cupons de Desconto'
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.codigo} - {self.get_tipo_display()} ({self.valor})"

    def is_valido(self, valor_total=Decimal('0.00')):
        if not self.ativo:
            return False, "Cupom inativo."
        if self.valido_ate and self.valido_ate < timezone.now().date():
            return False, "Cupom expirado."
        if self.limite_usos and self.usos_atuais >= self.limite_usos:
            return False, "Limite de usos do cupom atingido."
        if valor_total < self.valor_minimo_pedido:
            return False, f"Valor mínimo para este cupom é R$ {self.valor_minimo_pedido}."
        return True, "Cupom válido."

    def calcular_desconto(self, valor_total):
        valido, msg = self.is_valido(valor_total)
        if not valido:
            return Decimal('0.00'), msg
        if self.tipo == self.Tipo.PERCENTUAL:
            desconto = (valor_total * self.valor) / Decimal('100.00')
        else:
            desconto = min(valor_total, self.valor)
        return min(valor_total, Decimal(str(round(desconto, 2)))), "Desconto aplicado com sucesso."
