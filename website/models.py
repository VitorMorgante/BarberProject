from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q


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
        return self.nome


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
    STATUS_CHOICES = [
        ('Pendente', 'Pendente'),
        ('Confirmado', 'Confirmado'),
        ('Concluído', 'Concluído'),
        ('Cancelado', 'Cancelado'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='agendamentos')
    servico = models.ForeignKey(Servico, on_delete=models.PROTECT, related_name='agendamentos')
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.PROTECT, related_name='agendamentos')
    data = models.DateField()
    horario = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pendente')
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
            f'em {self.data.strftime("%d/%m/%Y")} às {self.horario.strftime("%H:%M")}'
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
        verbose_name = 'Foto de Trabalho'
        verbose_name_plural = 'Fotos de Trabalho'

    def __str__(self):
        return self.titulo

