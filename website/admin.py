from django.contrib import admin
from .models import Servico, Barbeiro, Cliente, HorarioDisponivel, Agendamento, MensagemContato


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
