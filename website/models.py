import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone


# ==============================================================================
# 0. UNIDADES E MULTIUNIDADE (PREPARAÇÃO ARQUITETURAL)
# ==============================================================================

class UnidadeBarbearia(models.Model):
    nome = models.CharField(max_length=200, default='Barber Heitor - Matriz')
    slug = models.SlugField(max_length=100, unique=True, default='matriz')
    cnpj = models.CharField(max_length=20, blank=True)
    endereco = models.CharField(max_length=255, default='Rua Terezinha Fortes Martins, 136')
    cidade = models.CharField(max_length=100, default='Paranavaí')
    estado = models.CharField(max_length=2, default='PR')
    telefone = models.CharField(max_length=20, default='(44) 99190-0997')
    is_matriz = models.BooleanField(default=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Unidade da Barbearia'
        verbose_name_plural = 'Unidades da Barbearia'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.cidade}/{self.estado})"


# ==============================================================================
# 1. SERVIÇOS, BARBEIROS, ESCALAS E DURAÇÕES
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
    class Nivel(models.TextChoices):
        JUNIOR = 'Junior', 'Júnior'
        PLENO = 'Pleno', 'Pleno'
        SENIOR = 'Senior', 'Sênior'
        ESPECIALISTA = 'Especialista', 'Especialista'

    usuario = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    nome = models.CharField(max_length=200)
    cargo = models.CharField(max_length=100)
    nivel = models.CharField(max_length=20, choices=Nivel.choices, default=Nivel.PLENO)
    especialidade = models.CharField(max_length=300)
    descricao_curta = models.TextField(blank=True)
    imagem_url = models.URLField(blank=True)
    tempo_buffer_depois = models.PositiveIntegerField(default=5, help_text="Buffer em minutos após cada serviço")
    ativo = models.BooleanField(default=True)
    cadastrado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Barbeiro'
        verbose_name_plural = 'Barbeiros'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.get_nivel_display()})"


class BarbeiroServico(models.Model):
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.CASCADE, related_name='servicos_customizados')
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE, related_name='barbeiros_customizados')
    duracao_minutos = models.PositiveIntegerField(null=True, blank=True, help_text="Duração específica deste barbeiro")
    preco_customizado = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Preço específico deste barbeiro")
    comissao_customizada = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="% de comissão específica")
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Duração e Preço por Barbeiro'
        verbose_name_plural = 'Durações e Preços por Barbeiro'
        unique_together = ['barbeiro', 'servico']

    def __str__(self):
        return f"{self.barbeiro.nome} - {self.servico.nome} ({self.duracao_minutos or self.servico.duracao_minutos} min)"

    def get_duracao(self):
        return self.duracao_minutos or self.servico.duracao_minutos

    def get_preco(self):
        return self.preco_customizado or self.servico.preco


class EscalaBarbeiro(models.Model):
    DIA_SEMANA_CHOICES = [
        (0, 'Segunda-feira'),
        (1, 'Terça-feira'),
        (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),
        (4, 'Sexta-feira'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.CASCADE, related_name='escalas')
    dia_semana = models.PositiveSmallIntegerField(choices=DIA_SEMANA_CHOICES)
    horario_inicio_1 = models.TimeField(default='09:00')
    horario_fim_1 = models.TimeField(default='12:00')
    horario_inicio_2 = models.TimeField(default='13:30', null=True, blank=True)
    horario_fim_2 = models.TimeField(default='19:00', null=True, blank=True)
    folga = models.BooleanField(default=False)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Escala de Trabalho'
        verbose_name_plural = 'Escalas de Trabalho'
        unique_together = ['barbeiro', 'dia_semana']
        ordering = ['barbeiro', 'dia_semana']

    def __str__(self):
        dia_nome = dict(self.DIA_SEMANA_CHOICES).get(self.dia_semana, '')
        if self.folga:
            return f"{self.barbeiro.nome} - {dia_nome} [Folga]"
        return f"{self.barbeiro.nome} - {dia_nome}: {self.horario_inicio_1.strftime('%H:%M')} às {self.horario_fim_2.strftime('%H:%M') if self.horario_fim_2 else self.horario_fim_1.strftime('%H:%M')}"


class BloqueioAgenda(models.Model):
    class Tipo(models.TextChoices):
        PAUSA_RAPIDA = 'pausa_rapida', 'Pausa Rápida (5-30 min)'
        FERIAS = 'ferias', 'Férias'
        FOLGA = 'folga', 'Folga Pontual'
        CURSO = 'curso', 'Curso / Workshop'
        AUSENCIA = 'ausencia', 'Ausência Imprevista'
        MANUAL = 'manual', 'Bloqueio Manual'

    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.CASCADE, related_name='bloqueios', null=True, blank=True, help_text="Vazio = Todas as estações")
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.MANUAL)
    data_inicio = models.DateField(default=timezone.now)
    data_fim = models.DateField(default=timezone.now)
    horario_inicio = models.TimeField(null=True, blank=True)
    horario_fim = models.TimeField(null=True, blank=True)
    motivo = models.CharField(max_length=255, blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Bloqueio de Agenda / Pausa'
        verbose_name_plural = 'Bloqueios de Agenda e Pausas'
        ordering = ['-data_inicio', '-horario_inicio']

    def __str__(self):
        barb = self.barbeiro.nome if self.barbeiro else "Todos"
        return f"Bloqueio {self.get_tipo_display()} ({barb}) {self.data_inicio.strftime('%d/%m/%Y')}"


# ==============================================================================
# 2. CLIENTES, DEPENDENTES E CONTA CORRENTE
# ==============================================================================

class Cliente(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    nome = models.CharField(max_length=200)
    telefone = models.CharField(max_length=20)
    email = models.EmailField()
    data_nascimento = models.DateField(null=True, blank=True)
    canal_origem = models.CharField(max_length=50, default='Outro', help_text="Instagram, Google, Indicação, TikTok, Passou em frente, etc.")
    codigo_indicacao = models.CharField(max_length=30, unique=True, null=True, blank=True, db_index=True)
    indicado_por = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='indicados')
    barbeiro_preferido = models.ForeignKey(Barbeiro, on_delete=models.SET_NULL, null=True, blank=True, related_name='clientes_favoritos')
    servico_preferido = models.ForeignKey(Servico, on_delete=models.SET_NULL, null=True, blank=True, related_name='clientes_favoritos')
    corte_habitual = models.CharField(max_length=200, blank=True)
    preferencia_acabamento = models.CharField(max_length=100, blank=True)
    preferencia_produto = models.CharField(max_length=100, blank=True)
    observacoes = models.TextField(blank=True)
    observacoes_internas = models.TextField(blank=True, help_text="Notas privadas visíveis apenas à equipe")
    cadastrado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} - {self.telefone}'

    def save(self, *args, **kwargs):
        if not self.codigo_indicacao:
            prefix = ''.join(e for e in self.nome if e.isalnum())[:4].upper() or 'DELA'
            self.codigo_indicacao = f"{prefix}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)


class PerfilDependente(models.Model):
    cliente_titular = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='dependentes')
    nome = models.CharField(max_length=200)
    parentesco = models.CharField(max_length=50, default='Filho(a)')
    data_nascimento = models.DateField(null=True, blank=True)
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Perfil Dependente'
        verbose_name_plural = 'Perfis Dependentes'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} (Titular: {self.cliente_titular.nome})"


class ContaCorrenteCliente(models.Model):
    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE, related_name='conta_corrente')
    saldo = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Saldo interno (cortesias, ajustes, estornos)")
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Conta Corrente do Cliente'
        verbose_name_plural = 'Contas Correntes dos Clientes'

    def __str__(self):
        return f"Conta {self.cliente.nome} - Saldo: R$ {self.saldo}"


class MovimentacaoContaCorrente(models.Model):
    class Tipo(models.TextChoices):
        CREDITO = 'credito', 'Crédito Adicionado'
        DEBITO = 'debito', 'Débito / Consumo'
        AJUSTE = 'ajuste', 'Ajuste Manual'
        ESTORNO = 'estorno', 'Estorno de Pagamento'
        RECOMPENSA_INDICACAO = 'recompensa_indicacao', 'Recompensa por Indicação'

    conta_corrente = models.ForeignKey(ContaCorrenteCliente, on_delete=models.CASCADE, related_name='movimentacoes')
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    valor = models.DecimalField(max_digits=8, decimal_places=2)
    saldo_anterior = models.DecimalField(max_digits=10, decimal_places=2)
    saldo_posterior = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.CharField(max_length=255)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Movimentação de Conta Corrente'
        verbose_name_plural = 'Movimentações de Conta Corrente'
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.conta_corrente.cliente.nome}: {self.tipo} R$ {self.valor} (Saldo: {self.saldo_posterior})"


# ==============================================================================
# 3. HORÁRIOS, AGENDAMENTOS E OPERAÇÃO
# ==============================================================================

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
        AGUARDANDO = 'Aguardando', 'Cliente Chegou / Aguardando'
        EM_ATENDIMENTO = 'Em Atendimento', 'Em Atendimento'
        CONCLUIDO = 'Concluído', 'Concluído'
        CANCELADO = 'Cancelado', 'Cancelado'
        NAO_COMPARECEU = 'Não Compareceu', 'Não Compareceu'

    usuario = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='agendamentos')
    dependente = models.ForeignKey(PerfilDependente, on_delete=models.SET_NULL, null=True, blank=True, related_name='agendamentos')
    servico = models.ForeignKey(Servico, on_delete=models.PROTECT, related_name='agendamentos')
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.PROTECT, related_name='agendamentos')
    data = models.DateField(db_index=True)
    horario = models.TimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE, db_index=True)
    observacoes = models.TextField(blank=True)
    inicio_real = models.DateTimeField(null=True, blank=True)
    fim_real = models.DateTimeField(null=True, blank=True)
    duracao_real_minutos = models.PositiveIntegerField(null=True, blank=True)
    checkin_em = models.DateTimeField(null=True, blank=True)
    checkin_token = models.CharField(max_length=64, default=uuid.uuid4, null=True, blank=True, db_index=True)
    atraso_estimado_minutos = models.PositiveIntegerField(default=0)
    is_walkin = models.BooleanField(default=False)
    prioritario = models.BooleanField(default=False)
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
        nome_atendido = self.dependente.nome if self.dependente else self.cliente.nome
        return (
            f'{nome_atendido} - {self.servico.nome} com {self.barbeiro.nome} '
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
        ('gerente', 'Gerente'),
        ('recepcionista', 'Recepcionista'),
        ('financeiro', 'Financeiro'),
    ]
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_CHOICES, default='cliente')
    telefone = models.CharField(max_length=20)
    foto_perfil = models.ImageField(upload_to='perfis/', blank=True, null=True)
    pode_aplicar_desconto = models.BooleanField(default=False)
    pode_estornar = models.BooleanField(default=False)
    pode_ver_financeiro = models.BooleanField(default=False)
    pode_ajustar_estoque = models.BooleanField(default=False)
    limite_desconto_percentual = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
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


class AvaliacaoDetalhada(models.Model):
    feedback = models.OneToOneField(Feedback, on_delete=models.CASCADE, related_name='avaliacao_detalhada')
    nota_atendimento = models.PositiveSmallIntegerField(default=5)
    nota_pontualidade = models.PositiveSmallIntegerField(default=5)
    nota_resultado = models.PositiveSmallIntegerField(default=5)
    nota_ambiente = models.PositiveSmallIntegerField(default=5)

    class Meta:
        verbose_name = 'Avaliação Detalhada'
        verbose_name_plural = 'Avaliações Detalhadas'

    def __str__(self):
        return f"Detalhes Feedback #{self.feedback.id} (Média: {self.media_geral():.1f})"

    def media_geral(self):
        return (self.nota_atendimento + self.nota_pontualidade + self.nota_resultado + self.nota_ambiente) / 4.0


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
# 4. BARBER CLUB, PACOTES E FIDELIDADE DIGITAL
# ==============================================================================

class PlanoAssinatura(models.Model):
    nome = models.CharField(max_length=200)
    descricao = models.TextField()
    preco_mensal = models.DecimalField(max_digits=8, decimal_places=2)
    quantidade_creditos = models.PositiveIntegerField(default=4, help_text="Cortes/serviços inclusos por mês")
    servicos = models.ManyToManyField(Servico, related_name='planos_assinatura', blank=True)
    desconto_produtos = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('10.00'), help_text="% de desconto em produtos")
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


class PacoteServico(models.Model):
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    servicos = models.ManyToManyField(Servico, related_name='pacotes')
    preco_original = models.DecimalField(max_digits=8, decimal_places=2)
    preco_promocional = models.DecimalField(max_digits=8, decimal_places=2)
    ativo = models.BooleanField(default=True)
    destaque = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pacote de Serviços'
        verbose_name_plural = 'Pacotes de Serviços'
        ordering = ['nome']

    def __str__(self):
        return f"Pacote: {self.nome} - R$ {self.preco_promocional}"


class ProgramaFidelidade(models.Model):
    class TipoRecompensa(models.TextChoices):
        CORTE_GRATIS = 'corte_gratis', 'Corte Gratuito'
        DESCONTO_PERCENTUAL = 'desconto_percentual', 'Desconto Percentual'
        DESCONTO_FIXO = 'desconto_fixo', 'Desconto Fixo (R$)'

    nome = models.CharField(max_length=100, default='Fidelidade Delacruz')
    servicos_necessarios = models.PositiveIntegerField(default=10, help_text="Cortes concluídos para gerar recompensa")
    tipo_recompensa = models.CharField(max_length=30, choices=TipoRecompensa.choices, default=TipoRecompensa.CORTE_GRATIS)
    valor_desconto = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'), help_text="Valor em % ou R$, se aplicável")
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
# 5. ESTOQUE, FORNECEDORES, CONSUMO INTERNO E PDV
# ==============================================================================

class LocalEstoque(models.Model):
    class Tipo(models.TextChoices):
        DEPOSITO = 'deposito', 'Depósito Central'
        RECEPCAO = 'recepcao', 'Recepção / Vitrine'
        ESTACAO = 'estacao', 'Bancada / Estação do Barbeiro'

    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.DEPOSITO)
    barbeiro_responsavel = models.ForeignKey(Barbeiro, on_delete=models.SET_NULL, null=True, blank=True, related_name='locais_estoque')
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Local de Estoque'
        verbose_name_plural = 'Locais de Estoque'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"


class Produto(models.Model):
    nome = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True, null=True, blank=True)
    descricao = models.TextField(blank=True)
    categoria = models.CharField(max_length=100, default='Cabelo & Barba')
    custo = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    estoque_atual = models.IntegerField(default=0)
    estoque_minimo = models.IntegerField(default=5)
    unidade = models.CharField(max_length=20, default='un')
    imagem = models.ImageField(upload_to='produtos/', null=True, blank=True)
    is_insumo_interno = models.BooleanField(default=False, help_text="Item para consumo no atendimento (lâminas, shampoos)")
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


class SaldoEstoqueLocal(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='saldos_locais')
    local = models.ForeignKey(LocalEstoque, on_delete=models.CASCADE, related_name='produtos')
    quantidade = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Saldo de Estoque por Local'
        verbose_name_plural = 'Saldos de Estoque por Local'
        unique_together = ['produto', 'local']

    def __str__(self):
        return f"{self.produto.nome} em {self.local.nome}: {self.quantidade}"


class TransferenciaEstoque(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='transferencias')
    origem = models.ForeignKey(LocalEstoque, on_delete=models.CASCADE, related_name='transferencias_saida')
    destino = models.ForeignKey(LocalEstoque, on_delete=models.CASCADE, related_name='transferencias_entrada')
    quantidade = models.PositiveIntegerField()
    motivo = models.CharField(max_length=255, blank=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Transferência de Estoque'
        verbose_name_plural = 'Transferências de Estoque'
        ordering = ['-criada_em']

    def __str__(self):
        return f"{self.produto.nome}: {self.origem.nome} -> {self.destino.nome} ({self.quantidade} un)"


class PerdaEstoque(models.Model):
    class Motivo(models.TextChoices):
        QUEBRA = 'quebra', 'Quebra / Avaria'
        VENCIMENTO = 'vencimento', 'Validade Expirada'
        CONSUMO_INDEVIDO = 'consumo_indevido', 'Consumo Indevido'
        DIVERGENCIA = 'divergencia', 'Divergência de Inventário'
        PERDA = 'perda', 'Perda / Extravio'

    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='perdas')
    local = models.ForeignKey(LocalEstoque, on_delete=models.SET_NULL, null=True, blank=True)
    quantidade = models.PositiveIntegerField()
    motivo = models.CharField(max_length=20, choices=Motivo.choices)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    observacoes = models.TextField(blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Perda de Estoque'
        verbose_name_plural = 'Perdas de Estoque'
        ordering = ['-criada_em']

    def __str__(self):
        return f"Perda {self.produto.nome} ({self.quantidade} un - {self.get_motivo_display()})"


class KitConsumoServico(models.Model):
    servico = models.OneToOneField(Servico, on_delete=models.CASCADE, related_name='kit_consumo')
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Kit de Consumo de Serviço'
        verbose_name_plural = 'Kits de Consumo de Serviços'

    def __str__(self):
        return f"Kit de Insumos: {self.servico.nome}"


class ItemKitConsumo(models.Model):
    kit = models.ForeignKey(KitConsumoServico, on_delete=models.CASCADE, related_name='itens')
    produto_insumo = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade_unitaria = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('1.00'))
    unidade_medida = models.CharField(max_length=20, default='un')

    class Meta:
        verbose_name = 'Item do Kit de Consumo'
        verbose_name_plural = 'Itens do Kit de Consumo'

    def __str__(self):
        return f"{self.produto_insumo.nome} ({self.quantidade_unitaria} {self.unidade_medida})"


class Fornecedor(models.Model):
    nome_empresa = models.CharField(max_length=200)
    contato_nome = models.CharField(max_length=150, blank=True)
    telefone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    cnpj = models.CharField(max_length=20, blank=True)
    prazo_entrega_dias = models.PositiveIntegerField(default=3)
    observacoes = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Fornecedor'
        verbose_name_plural = 'Fornecedores'
        ordering = ['nome_empresa']

    def __str__(self):
        return self.nome_empresa


class PedidoCompra(models.Model):
    class Status(models.TextChoices):
        RASCUNHO = 'rascunho', 'Rascunho'
        ENVIADO = 'enviado', 'Enviado ao Fornecedor'
        RECEBIDO = 'recebido', 'Recebido / Estoque Atualizado'
        CANCELADO = 'cancelado', 'Cancelado'

    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.PROTECT, related_name='pedidos')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RASCUNHO)
    data_pedido = models.DateField(default=timezone.now)
    data_entrega_prevista = models.DateField(null=True, blank=True)
    data_recebimento = models.DateField(null=True, blank=True)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pedido de Compra'
        verbose_name_plural = 'Pedidos de Compra'
        ordering = ['-data_pedido']

    def __str__(self):
        return f"Pedido #{self.id} - {self.fornecedor.nome_empresa} [{self.get_status_display()}]"


class ItemPedidoCompra(models.Model):
    pedido = models.ForeignKey(PedidoCompra, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    quantidade = models.PositiveIntegerField()
    custo_unitario = models.DecimalField(max_digits=8, decimal_places=2)
    total = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        verbose_name = 'Item do Pedido de Compra'
        verbose_name_plural = 'Itens do Pedido de Compra'

    def save(self, *args, **kwargs):
        self.total = Decimal(str(self.quantidade)) * Decimal(str(self.custo_unitario))
        super().save(*args, **kwargs)


class InventarioEstoque(models.Model):
    class Status(models.TextChoices):
        EM_ANDAMENTO = 'em_andamento', 'Em Andamento'
        CONCLUIDO = 'concluido', 'Concluído'

    local = models.ForeignKey(LocalEstoque, on_delete=models.CASCADE, related_name='inventarios')
    usuario_responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    data_inventario = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.EM_ANDAMENTO)
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Inventário Físico'
        verbose_name_plural = 'Inventários Físicos'
        ordering = ['-data_inventario']

    def __str__(self):
        return f"Inventário em {self.local.nome} ({self.data_inventario.strftime('%d/%m/%Y')}) [{self.get_status_display()}]"


class ItemInventarioEstoque(models.Model):
    inventario = models.ForeignKey(InventarioEstoque, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade_esperada = models.IntegerField()
    quantidade_contada = models.IntegerField()
    divergencia = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Item do Inventário'
        verbose_name_plural = 'Itens do Inventário'

    def save(self, *args, **kwargs):
        self.divergencia = self.quantidade_contada - self.quantidade_esperada
        super().save(*args, **kwargs)


class LoteValidade(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='lotes')
    numero_lote = models.CharField(max_length=50)
    data_validade = models.DateField()
    quantidade = models.PositiveIntegerField()
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Lote e Validade'
        verbose_name_plural = 'Lotes e Validades'
        ordering = ['data_validade']

    def __str__(self):
        return f"{self.produto.nome} (Lote: {self.numero_lote} - Vence: {self.data_validade.strftime('%d/%m/%Y')})"


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
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ABERTA, db_index=True)
    subtotal = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    desconto = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    sinal_pago = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    creditos_abatidos = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    valor_total = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    metodo_pagamento = models.CharField(max_length=50, blank=True, default='Pix')
    motivo_desconto = models.CharField(max_length=255, blank=True)
    observacoes = models.TextField(blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)
    fechada_em = models.DateTimeField(null=True, blank=True, db_index=True)

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


class PagamentoDividido(models.Model):
    class Metodo(models.TextChoices):
        PIX = 'pix', 'PIX Dinâmico / Estático'
        DINHEIRO = 'dinheiro', 'Dinheiro'
        CARTAO_CREDITO = 'cartao_credito', 'Cartão de Crédito'
        CARTAO_DEBITO = 'cartao_debito', 'Cartão de Débito'
        SALDO_INTERNO = 'saldo_interno', 'Saldo em Conta Corrente'

    comanda = models.ForeignKey(Comanda, on_delete=models.CASCADE, related_name='pagamentos_divididos')
    metodo = models.CharField(max_length=30, choices=Metodo.choices)
    valor = models.DecimalField(max_digits=8, decimal_places=2)
    taxa_percentual = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    valor_liquido = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pagamento Dividido'
        verbose_name_plural = 'Pagamentos Divididos'
        ordering = ['-criado_em']

    def __str__(self):
        return f"Pagamento #{self.comanda.id}: {self.get_metodo_display()} R$ {self.valor}"


class Gorjeta(models.Model):
    comanda = models.ForeignKey(Comanda, on_delete=models.SET_NULL, null=True, blank=True, related_name='gorjetas')
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.PROTECT, related_name='gorjetas')
    valor = models.DecimalField(max_digits=8, decimal_places=2)
    metodo_pagamento = models.CharField(max_length=50, default='Pix')
    repassada = models.BooleanField(default=False)
    data_repasse = models.DateTimeField(null=True, blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Gorjeta'
        verbose_name_plural = 'Gorjetas'
        ordering = ['-criada_em']

    def __str__(self):
        return f"Gorjeta para {self.barbeiro.nome} - R$ {self.valor} [{ 'Repassada' if self.repassada else 'Pendente' }]"


# ==============================================================================
# 6. COMISSÕES E METAS FINANCEIRAS
# ==============================================================================

class RegraComissao(models.Model):
    barbeiro = models.OneToOneField(Barbeiro, on_delete=models.CASCADE, related_name='regra_comissao')
    percentual_servico = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('50.00'), help_text="% de comissão em serviços")
    percentual_produto = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('15.00'), help_text="% de comissão em produtos")
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
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE, db_index=True)
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
    meta_faturamento = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('5000.00'))
    meta_atendimentos = models.PositiveIntegerField(default=100)
    meta_produtos = models.PositiveIntegerField(default=20)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Meta do Barbeiro'
        verbose_name_plural = 'Metas dos Barbeiros'
        unique_together = ['barbeiro', 'mes', 'ano']

    def __str__(self):
        return f"Meta {self.barbeiro.nome} - {self.mes}/{self.ano} (R$ {self.meta_faturamento})"


class MetaGlobal(models.Model):
    mes = models.PositiveIntegerField()
    ano = models.PositiveIntegerField()
    meta_faturamento = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('40000.00'))
    meta_atendimentos = models.PositiveIntegerField(default=800)
    meta_produtos = models.PositiveIntegerField(default=150)
    meta_ocupacao_percentual = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('85.00'))
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Meta Global da Barbearia'
        verbose_name_plural = 'Metas Globais da Barbearia'
        unique_together = ['mes', 'ano']

    def __str__(self):
        return f"Meta Global - {self.mes}/{self.ano} (R$ {self.meta_faturamento})"


class RegistroPontoBarbeiro(models.Model):
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.CASCADE, related_name='pontos')
    data = models.DateField(default=timezone.now)
    hora_entrada = models.TimeField()
    hora_saida_pausa = models.TimeField(null=True, blank=True)
    hora_retorno_pausa = models.TimeField(null=True, blank=True)
    hora_saida = models.TimeField(null=True, blank=True)
    total_horas = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    observacoes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Registro de Ponto / Turno'
        verbose_name_plural = 'Registros de Pontos e Turnos'
        unique_together = ['barbeiro', 'data']
        ordering = ['-data']

    def __str__(self):
        return f"Ponto {self.barbeiro.nome} em {self.data.strftime('%d/%m/%Y')}"


# ==============================================================================
# 7. FINANCEIRO, CAIXA, DESPESAS E CONFIGURAÇÃO
# ==============================================================================

class CaixaDiario(models.Model):
    class Status(models.TextChoices):
        ABERTO = 'aberto', 'Aberto'
        FECHADO = 'fechado', 'Fechado'

    operador = models.ForeignKey(User, on_delete=models.PROTECT, related_name='caixas_operados')
    data_abertura = models.DateTimeField(auto_now_add=True)
    saldo_inicial = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('100.00'), help_text="Fundo de troco")
    data_fechamento = models.DateTimeField(null=True, blank=True)
    saldo_dinheiro_informado = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    saldo_esperado = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    diferenca_quebra = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ABERTO)
    observacoes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Caixa Diário'
        verbose_name_plural = 'Caixas Diários'
        ordering = ['-data_abertura']

    def __str__(self):
        return f"Caixa #{self.id} ({self.data_abertura.strftime('%d/%m/%Y %H:%M')}) - Operador: {self.operador.username} [{self.get_status_display()}]"


class MovimentacaoCaixa(models.Model):
    class Tipo(models.TextChoices):
        SUPRIMENTO = 'suprimento', 'Reforço / Suprimento de Troco'
        SANGRIA = 'sangria', 'Sangria / Retirada'
        VENDA = 'venda', 'Entrada em Dinheiro (Comanda)'
        DESPESA = 'despesa', 'Pagamento de Despesa Local'

    caixa = models.ForeignKey(CaixaDiario, on_delete=models.CASCADE, related_name='movimentacoes')
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    valor = models.DecimalField(max_digits=8, decimal_places=2)
    motivo = models.CharField(max_length=255)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Movimentação de Caixa'
        verbose_name_plural = 'Movimentações de Caixa'
        ordering = ['-criada_em']

    def __str__(self):
        return f"{self.tipo}: R$ {self.valor} ({self.motivo})"


class CategoriaDespesa(models.Model):
    class Tipo(models.TextChoices):
        FIXA = 'fixa', 'Despesa Fixa'
        VARIAVEL = 'variavel', 'Despesa Variável'

    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.FIXA)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Categoria de Despesa'
        verbose_name_plural = 'Categorias de Despesas'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"


class Despesa(models.Model):
    class Status(models.TextChoices):
        PENDENTE = 'pendente', 'Pendente'
        PAGO = 'pago', 'Pago'
        CANCELADO = 'cancelado', 'Cancelado'

    categoria = models.ForeignKey(CategoriaDespesa, on_delete=models.PROTECT, related_name='despesas')
    descricao = models.CharField(max_length=200)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data_vencimento = models.DateField(db_index=True)
    data_pagamento = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE, db_index=True)
    comprovante = models.FileField(upload_to='despesas/', null=True, blank=True)
    observacoes = models.TextField(blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Despesa'
        verbose_name_plural = 'Despesas'
        ordering = ['-data_vencimento']

    def __str__(self):
        return f"{self.descricao} - R$ {self.valor} ({self.data_vencimento.strftime('%d/%m/%Y')}) [{self.get_status_display()}]"


class TaxaMetodoPagamento(models.Model):
    metodo = models.CharField(max_length=30, unique=True, choices=PagamentoDividido.Metodo.choices)
    taxa_percentual = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), help_text="% de taxa cobrada pelo gateway")
    taxa_fixa_reais = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'), help_text="Custo fixo por transação em R$")
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Taxa de Método de Pagamento'
        verbose_name_plural = 'Taxas de Métodos de Pagamento'

    def __str__(self):
        return f"{self.get_metodo_display()}: {self.taxa_percentual}% + R$ {self.taxa_fixa_reais}"


class ConfiguracaoEstabelecimento(models.Model):
    class TipoSinal(models.TextChoices):
        NENHUM = 'nenhum', 'Sem Sinal Obrigatório'
        PERCENTUAL = 'percentual', 'Percentual do Serviço (%)'
        FIXO = 'fixo', 'Valor Fixo (R$)'
        INTEGRAL = 'integral', 'Pagamento Integral (100%)'

    tipo_sinal = models.CharField(max_length=20, choices=TipoSinal.choices, default=TipoSinal.NENHUM)
    valor_sinal = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'), help_text="% ou R$ fixo")
    minutos_expiracao_pix = models.PositiveIntegerField(default=15)
    chave_pix = models.CharField(max_length=100, default='delacruzbarber@email.com')
    titular_pix = models.CharField(max_length=150, default='Delacruz Barber')
    cidade_pix = models.CharField(max_length=100, default='Paranavai')
    lembrete_horas_antes = models.PositiveIntegerField(default=24)
    cancelamento_antecedencia_horas = models.PositiveIntegerField(default=2)
    antecedencia_minima_minutos = models.PositiveIntegerField(default=30, help_text="Antecedência mínima para agendar")
    janela_maxima_dias = models.PositiveIntegerField(default=30, help_text="Máximo de dias à frente permitidos na agenda")
    limite_agendamentos_ativos_cliente = models.PositiveIntegerField(default=3, help_text="Máximo de reservas ativas por cliente")
    tempo_maximo_espera_minutos = models.PositiveIntegerField(default=20, help_text="Tempo máximo desejado de espera em fila")
    meta_ocupacao_percentual = models.PositiveIntegerField(default=85, help_text="Meta alvo de ocupação diária da equipe")
    buffer_padrao_minutos = models.PositiveIntegerField(default=5, help_text="Buffer padrão entre cortes")

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
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AGUARDANDO, db_index=True)
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
# 8. WAITLIST, COMUNICAÇÃO E AUTOMAÇÕES
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
        ATRASO = 'atraso', 'Aviso de Atraso Operacional'
        ANIVERSARIO = 'aniversario', 'Aviso de Aniversário'
        REATIVACAO = 'reativacao', 'Campanha de Retorno'

    class Status(models.TextChoices):
        PENDENTE = 'Pendente', 'Pendente'
        ENVIADA = 'Enviada', 'Enviada'
        ERRO = 'Erro', 'Erro no Envio'

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='notificacoes')
    agendamento = models.ForeignKey(Agendamento, on_delete=models.SET_NULL, null=True, blank=True, related_name='notificacoes')
    canal = models.CharField(max_length=20, choices=Canal.choices, default=Canal.WHATSAPP)
    tipo = models.CharField(max_length=30, choices=Tipo.choices, default=Tipo.LEMBRETE_24H)
    mensagem = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE, db_index=True)
    data_prevista = models.DateTimeField(db_index=True)
    enviada_em = models.DateTimeField(null=True, blank=True)
    erro = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Notificação / Lembrete'
        verbose_name_plural = 'Notificações e Lembretes'
        ordering = ['-data_prevista']

    def __str__(self):
        return f"Notificação {self.canal} para {self.cliente.nome} [{self.status}]"


class RegraAutomacao(models.Model):
    class Tipo(models.TextChoices):
        LEMBRETE_24H = 'lembrete_24h', 'Lembrete 24 Horas Antes'
        LEMBRETE_2H = 'lembrete_2h', 'Lembrete 2 Horas Antes'
        REATIVACAO_30D = 'reativacao_30d', 'Reativação 30 Dias Sem Visita'
        REATIVACAO_45D = 'reativacao_45d', 'Reativação 45 Dias Sem Visita'
        REATIVACAO_60D = 'reativacao_60d', 'Reativação 60 Dias Sem Visita'
        FEEDBACK_POS_CORTE = 'feedback_pos_corte', 'Solicitação de Feedback Pós-Atendimento'
        ANIVERSARIO = 'aniversario', 'Aviso de Aniversário com Cortesia/Desconto'
        WAITLIST_VAGA = 'waitlist_vaga', 'Aviso Instantâneo de Vaga Liberada'
        ESTOQUE_BAIXO = 'estoque_baixo', 'Alerta Administrativo de Estoque Baixo'
        HORARIO_OCIOSO = 'horario_ocioso', 'Promoção para Horários Ociosos'

    tipo = models.CharField(max_length=30, unique=True, choices=Tipo.choices)
    titulo = models.CharField(max_length=150)
    mensagem_template = models.TextField()
    ativo = models.BooleanField(default=True)
    dias_disparo = models.PositiveIntegerField(default=0)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Regra de Automação'
        verbose_name_plural = 'Regras de Automações'
        ordering = ['titulo']

    def __str__(self):
        return f"{self.titulo} [{ 'Ativa' if self.ativo else 'Inativa' }]"


# ==============================================================================
# 9. IA, FICHA TÉCNICA E HISTÓRICO VISUAL
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
    confianca = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.85'))
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


class FichaTecnicaCorte(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='fichas_tecnicas')
    agendamento = models.ForeignKey(Agendamento, on_delete=models.SET_NULL, null=True, blank=True, related_name='ficha_tecnica')
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.PROTECT, related_name='fichas_tecnicas')
    maquina_lateral = models.CharField(max_length=100, blank=True, help_text="Ex: 0.5 baixa na nuca, 1.5 nas laterais")
    comprimento_topo = models.CharField(max_length=100, blank=True, help_text="Ex: 2 dedos na tesoura, texturizado com navalha")
    tipo_fade = models.CharField(max_length=100, blank=True, help_text="Ex: Low Fade, Mid Fade, High Taper")
    acabamento = models.CharField(max_length=100, blank=True, help_text="Ex: Pezinho quadrado navalhado")
    configuracao_barba = models.CharField(max_length=200, blank=True, help_text="Ex: Alinhamento natural com degradê")
    observacoes_tecnicas = models.TextField(blank=True, help_text="Detalhes para repetir na próxima visita")
    notas_internas = models.TextField(blank=True, help_text="Notas privadas visíveis apenas à equipe")
    data = models.DateField(default=timezone.now)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ficha Técnica do Corte'
        verbose_name_plural = 'Fichas Técnicas dos Cortes'
        ordering = ['-data']

    def __str__(self):
        return f"Ficha {self.cliente.nome} ({self.data.strftime('%d/%m/%Y')}) - {self.barbeiro.nome}"


# ==============================================================================
# 10. OPERAÇÃO, RECEPÇÃO, CHECKLISTS E EQUIPAMENTOS
# ==============================================================================

class TarefaRecepcao(models.Model):
    class Tipo(models.TextChoices):
        CONFIRMAR_CLIENTE = 'confirmar_cliente', 'Confirmar Agendamento'
        VERIFICAR_PAGAMENTO = 'verificar_pagamento', 'Verificar Pagamento Pendente'
        PREPARAR_PRODUTO = 'preparar_produto', 'Preparar / Separar Produto'
        ENTRAR_CONTATO = 'entrar_contato', 'Entrar em Contato com Cliente'
        GERAL = 'geral', 'Tarefa Operacional Geral'

    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    tipo = models.CharField(max_length=30, choices=Tipo.choices, default=Tipo.GERAL)
    data_limite = models.DateField(default=timezone.now)
    concluida = models.BooleanField(default=False)
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Tarefa da Recepção'
        verbose_name_plural = 'Tarefas da Recepção'
        ordering = ['concluida', 'data_limite']

    def __str__(self):
        return f"{self.titulo} [{ 'Feita' if self.concluida else 'Pendente' }]"


class HandoffTurno(models.Model):
    turno_origem = models.CharField(max_length=50, default='Manhã')
    turno_destino = models.CharField(max_length=50, default='Tarde / Noite')
    usuario_emissor = models.ForeignKey(User, on_delete=models.CASCADE)
    mensagem = models.TextField()
    pendencias = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Handoff de Turno'
        verbose_name_plural = 'Handoffs de Turnos'
        ordering = ['-criado_em']

    def __str__(self):
        return f"Passagem {self.turno_origem} -> {self.turno_destino} em {self.criado_em.strftime('%d/%m/%Y %H:%M')}"


class OcorrenciaOperacional(models.Model):
    class Tipo(models.TextChoices):
        ATRASO = 'atraso', 'Atraso Operacional'
        EQUIPAMENTO = 'equipamento', 'Equipamento Quebrado / Avaria'
        RECLAMACAO = 'reclamacao', 'Reclamação de Cliente'
        CAIXA = 'caixa', 'Divergência de Caixa'
        OUTRO = 'outro', 'Outro Incidente'

    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.OUTRO)
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    resolvida = models.BooleanField(default=False)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ocorrência Operacional'
        verbose_name_plural = 'Central de Ocorrências'
        ordering = ['-criada_em']

    def __str__(self):
        return f"{self.titulo} [{self.get_tipo_display()}] - { 'Resolvida' if self.resolvida else 'Aberta' }"


class ChecklistOperacional(models.Model):
    class Tipo(models.TextChoices):
        ABERTURA = 'abertura', 'Checklist de Abertura'
        FECHAMENTO = 'fechamento', 'Checklist de Fechamento'

    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    data = models.DateField(default=timezone.now)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    concluido = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Checklist Operacional'
        verbose_name_plural = 'Checklists Operacionais'
        unique_together = ['tipo', 'data']
        ordering = ['-data']

    def __str__(self):
        return f"{self.get_tipo_display()} ({self.data.strftime('%d/%m/%Y')}) [{ 'Concluído' if self.concluido else 'Pendente' }]"


class ItemChecklistOperacional(models.Model):
    checklist = models.ForeignKey(ChecklistOperacional, on_delete=models.CASCADE, related_name='itens')
    titulo = models.CharField(max_length=200)
    marcado = models.BooleanField(default=False)
    observacao = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = 'Item de Checklist'
        verbose_name_plural = 'Itens de Checklists'

    def __str__(self):
        return f"{self.titulo} - { 'OK' if self.marcado else 'Pendente' }"


class RegistroHigienizacao(models.Model):
    class Tipo(models.TextChoices):
        ESTERILIZACAO_AUTOCLAVE = 'autoclave', 'Esterilização em Autoclave / Cuba'
        HIGIENIZACAO_BANCADA = 'bancada', 'Higienização de Bancadas e Cadeiras'
        TROCA_LAMINAS = 'laminas', 'Descarte e Troca de Lâminas'
        LIMPEZA_GERAL = 'limpeza_geral', 'Limpeza Geral do Espaço'

    tipo_procedimento = models.CharField(max_length=30, choices=Tipo.choices)
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    data_hora = models.DateTimeField(default=timezone.now)
    observacoes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Registro de Higienização e Esterilização'
        verbose_name_plural = 'Registros de Higienização e Esterilização'
        ordering = ['-data_hora']

    def __str__(self):
        return f"{self.get_tipo_procedimento_display()} em {self.data_hora.strftime('%d/%m/%Y %H:%M')}"


class Equipamento(models.Model):
    class Tipo(models.TextChoices):
        MAQUINA = 'maquina', 'Máquina de Corte / Acabamento'
        SECADOR = 'secador', 'Secador de Cabelo'
        CADEIRA = 'cadeira', 'Cadeira / Lavatório Hidráulico'
        ESTERILIZADOR = 'esterilizador', 'Esterilizador / Autoclave'
        AR_CONDICIONADO = 'ar_condicionado', 'Ar-Condicionado'
        OUTRO = 'outro', 'Outro Equipamento'

    nome = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.MAQUINA)
    numero_serie = models.CharField(max_length=100, blank=True)
    barbeiro_responsavel = models.ForeignKey(Barbeiro, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipamentos')
    data_aquisicao = models.DateField(null=True, blank=True)
    data_ultima_manutencao = models.DateField(null=True, blank=True)
    proxima_manutencao = models.DateField(null=True, blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Equipamento'
        verbose_name_plural = 'Equipamentos'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"


class ManutencaoEquipamento(models.Model):
    class Tipo(models.TextChoices):
        PREVENTIVA = 'preventiva', 'Manutenção Preventiva'
        CORRETIVA = 'corretiva', 'Manutenção Corretiva / Reparo'

    equipamento = models.ForeignKey(Equipamento, on_delete=models.CASCADE, related_name='manutencoes')
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.PREVENTIVA)
    data_realizada = models.DateField(default=timezone.now)
    custo = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    prestador_servico = models.CharField(max_length=150, blank=True)
    descricao = models.TextField()

    class Meta:
        verbose_name = 'Manutenção de Equipamento'
        verbose_name_plural = 'Manutenções de Equipamentos'
        ordering = ['-data_realizada']

    def __str__(self):
        return f"Manutenção {self.equipamento.nome} ({self.data_realizada.strftime('%d/%m/%Y')}) - R$ {self.custo}"


# ==============================================================================
# 11. AUDITORIA, APROVAÇÕES E LGPD
# ==============================================================================

class RegistroAuditoria(models.Model):
    class Acao(models.TextChoices):
        ALTERACAO_PRECO = 'alteracao_preco', 'Alteração de Preço'
        ALTERACAO_COMISSAO = 'alteracao_comissao', 'Alteração de Comissão'
        AJUSTE_ESTOQUE = 'ajuste_estoque', 'Ajuste Manual de Estoque'
        DESCONTO_CONCEDIDO = 'desconto_concedido', 'Desconto Concedido'
        ESTORNO_REALIZADO = 'estorno_realizado', 'Estorno Realizado'
        LOGIN_ADMIN = 'login_admin', 'Login Administrativo'
        OUTRA = 'outra', 'Operação Auditada'

    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    acao = models.CharField(max_length=30, choices=Acao.choices)
    tabela_afetada = models.CharField(max_length=100)
    registro_id = models.CharField(max_length=100, blank=True)
    valor_anterior = models.TextField(blank=True)
    valor_novo = models.TextField(blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    data_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Registro de Auditoria'
        verbose_name_plural = 'Registros de Auditoria'
        ordering = ['-data_hora']

    def __str__(self):
        usr = self.usuario.username if self.usuario else "Sistema"
        return f"[{self.data_hora.strftime('%d/%m/%Y %H:%M')}] {usr}: {self.get_acao_display()} ({self.tabela_afetada})"


class AprovacaoAcaoSensivel(models.Model):
    class Tipo(models.TextChoices):
        DESCONTO_ELEVADO = 'desconto_elevado', 'Desconto Elevado'
        ESTORNO = 'estorno', 'Estorno de Pagamento'
        AJUSTE_ESTOQUE_GRANDE = 'ajuste_estoque_grande', 'Ajuste de Estoque de Grande Porte'

    class Status(models.TextChoices):
        PENDENTE = 'pendente', 'Pendente de Aprovação'
        APROVADO = 'aprovado', 'Aprovado'
        REJEITADO = 'rejeitado', 'Rejeitado'

    solicitante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solicitacoes_aprovacao')
    aprovador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='aprovacoes_concedidas')
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE)
    detalhes = models.TextField()
    motivo_rejeicao = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    decidido_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Aprovação de Ação Sensível'
        verbose_name_plural = 'Aprovações de Ações Sensíveis'
        ordering = ['-criado_em']

    def __str__(self):
        return f"Aprovação #{self.id} ({self.get_tipo_display()}) - [{self.get_status_display()}]"


class ConsentimentoCliente(models.Model):
    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE, related_name='consentimentos')
    fotos_privadas = models.BooleanField(default=True, help_text="Permite histórico visual de evolução privado")
    fotos_portfolio = models.BooleanField(default=False, help_text="Permite fotos no portfólio público")
    ia_visagismo = models.BooleanField(default=True, help_text="Permite análise de visagismo facial por IA")
    whatsapp_notificacoes = models.BooleanField(default=True, help_text="Permite lembretes transacionais no WhatsApp")
    whatsapp_marketing = models.BooleanField(default=False, help_text="Permite promoções e cupons no WhatsApp")
    email_marketing = models.BooleanField(default=False, help_text="Permite newsletters e campanhas de email")
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Consentimento LGPD do Cliente'
        verbose_name_plural = 'Consentimentos LGPD dos Clientes'

    def __str__(self):
        return f"LGPD {self.cliente.nome} (Atualizado: {self.atualizado_em.strftime('%d/%m/%Y')})"


class DadosFiscaisEmpresa(models.Model):
    razao_social = models.CharField(max_length=200, default='Delacruz Barber Serviços de Beleza LTDA')
    cnpj = models.CharField(max_length=20, default='00.000.000/0001-00')
    inscricao_municipal = models.CharField(max_length=50, blank=True)
    cnae_principal = models.CharField(max_length=20, default='9602-5/01', help_text="Cabeleireiros, manicure e pedicure")
    regime_tributario = models.CharField(max_length=50, default='Simples Nacional')
    aliquota_iss = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('2.00'))

    class Meta:
        verbose_name = 'Dados Fiscais (Preparação NFS-e)'
        verbose_name_plural = 'Dados Fiscais (Preparação NFS-e)'

    def __str__(self):
        return f"{self.razao_social} ({self.cnpj})"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj


# ==============================================================================
# 12. PWA, PUSH & CUPONS
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
