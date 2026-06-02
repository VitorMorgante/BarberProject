from django.db import models


class Servico(models.Model):
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
        ('pendente', 'Pendente'),
        ('confirmado', 'Confirmado'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='agendamentos')
    servico = models.ForeignKey(Servico, on_delete=models.PROTECT, related_name='agendamentos')
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.PROTECT, related_name='agendamentos')
    data = models.DateField()
    horario = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Agendamento'
        verbose_name_plural = 'Agendamentos'
        unique_together = ['barbeiro', 'data', 'horario']
        ordering = ['-data', '-horario']

    def __str__(self):
        return (
            f'{self.cliente.nome} - {self.servico.nome} com {self.barbeiro.nome} '
            f'em {self.data.strftime("%d/%m/%Y")} às {self.horario.strftime("%H:%M")}'
        )


class MensagemContato(models.Model):
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
