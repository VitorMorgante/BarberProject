from django.views.generic import TemplateView, ListView, DetailView, FormView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import date, datetime

from .models import Servico, Barbeiro, Cliente, HorarioDisponivel, Agendamento, MensagemContato
from .forms import (
    ServicoForm, BarbeiroForm, ClienteForm, HorarioDisponivelForm,
    AgendamentoForm, MensagemContatoForm, AgendamentoPublicoForm,
)


# ==============================================================================
# PUBLIC VIEWS
# ==============================================================================

class IndexView(TemplateView):
    template_name = 'website/inicio.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['servicos'] = Servico.objects.filter(ativo=True, destaque=True)
        context['barbeiros'] = Barbeiro.objects.filter(ativo=True)
        context['all_servicos'] = Servico.objects.filter(ativo=True)
        return context


class SobreView(TemplateView):
    template_name = 'website/sobre.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['barbeiros'] = Barbeiro.objects.filter(ativo=True)
        return context


class ContatoView(CreateView):
    model = MensagemContato
    form_class = MensagemContatoForm
    template_name = 'website/contato.html'
    success_url = reverse_lazy('contato')
    extra_context = {'titulo': 'Fale Conosco', 'botao': 'Enviar Mensagem'}

    def form_valid(self, form):
        messages.success(self.request, 'Mensagem enviada com sucesso! A Delacruz Barber entrará em contato em breve.')
        return super().form_valid(form)


class AgendamentoPublicoView(FormView):
    template_name = 'website/agendamento.html'
    form_class = AgendamentoPublicoForm
    success_url = reverse_lazy('agendamento')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['servicos'] = Servico.objects.filter(ativo=True)
        context['barbeiros'] = Barbeiro.objects.filter(ativo=True)
        context['horarios'] = [
            '08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '11:00',
            '13:30', '14:00', '14:30', '15:00', '15:30', '16:00', '16:30',
            '17:00', '17:30',
        ]
        return context

    def form_valid(self, form):
        # Get or create cliente
        email = form.cleaned_data['email']
        nome = form.cleaned_data['nome']
        telefone = form.cleaned_data['telefone']

        cliente, created = Cliente.objects.get_or_create(
            email=email,
            defaults={'nome': nome, 'telefone': telefone},
        )
        if not created:
            cliente.nome = nome
            cliente.telefone = telefone
            cliente.save()

        # Create agendamento
        Agendamento.objects.create(
            cliente=cliente,
            servico=form.cleaned_data['servico'],
            barbeiro=form.cleaned_data['barbeiro'],
            data=form.cleaned_data['data'],
            horario=form.cleaned_data['horario'],
            observacoes=form.cleaned_data.get('observacoes', ''),
            status='pendente',
        )

        messages.success(self.request, 'Agendamento realizado com sucesso! A Delacruz Barber aguarda você.')
        return redirect(self.success_url)


class ServicosPublicView(ListView):
    model = Servico
    template_name = 'website/servicos.html'
    context_object_name = 'servicos'

    def get_queryset(self):
        return Servico.objects.filter(ativo=True)


class BarbeirosPublicView(ListView):
    model = Barbeiro
    template_name = 'website/barbeiros.html'
    context_object_name = 'barbeiros'

    def get_queryset(self):
        return Barbeiro.objects.filter(ativo=True)


class AgendamentoSucessoView(TemplateView):
    template_name = 'website/agendamento_sucesso.html'


# ==============================================================================
# DASHBOARD
# ==============================================================================

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'website/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoje = date.today()
        agendamentos_hoje = Agendamento.objects.filter(data=hoje)

        context['hoje'] = hoje
        context['total_hoje'] = agendamentos_hoje.count()
        context['pendentes'] = agendamentos_hoje.filter(status='pendente').count()
        context['confirmados'] = agendamentos_hoje.filter(status='confirmado').count()
        context['concluidos'] = agendamentos_hoje.filter(status='concluido').count()
        context['receita_hoje'] = (
            agendamentos_hoje.filter(status='concluido')
            .aggregate(total=Sum('servico__preco'))['total'] or 0
        )
        context['ultimos_agendamentos'] = Agendamento.objects.all()[:10]
        context['total_clientes'] = Cliente.objects.count()
        context['mensagens_nao_lidas'] = MensagemContato.objects.filter(lida=False).count()
        return context


# ==============================================================================
# SERVICO CRUD
# ==============================================================================

class ServicoCreate(LoginRequiredMixin, CreateView):
    model = Servico
    form_class = ServicoForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_servicos')
    extra_context = {'titulo': 'Cadastrar Serviço', 'botao': 'Cadastrar'}


class ServicoUpdate(LoginRequiredMixin, UpdateView):
    model = Servico
    form_class = ServicoForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_servicos')
    extra_context = {'titulo': 'Editar Serviço', 'botao': 'Salvar'}


class ServicoDelete(LoginRequiredMixin, DeleteView):
    model = Servico
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_servicos')
    extra_context = {'titulo': 'Excluir Serviço', 'botao': 'Excluir'}


class ServicoList(LoginRequiredMixin, ListView):
    model = Servico
    template_name = 'website/listas/servicos.html'
    context_object_name = 'servicos'


class ServicoDetail(LoginRequiredMixin, DetailView):
    model = Servico
    template_name = 'website/ver/servico.html'
    context_object_name = 'servico'


# ==============================================================================
# BARBEIRO CRUD
# ==============================================================================

class BarbeiroCreate(LoginRequiredMixin, CreateView):
    model = Barbeiro
    form_class = BarbeiroForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_barbeiros')
    extra_context = {'titulo': 'Cadastrar Barbeiro', 'botao': 'Cadastrar'}


class BarbeiroUpdate(LoginRequiredMixin, UpdateView):
    model = Barbeiro
    form_class = BarbeiroForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_barbeiros')
    extra_context = {'titulo': 'Editar Barbeiro', 'botao': 'Salvar'}


class BarbeiroDelete(LoginRequiredMixin, DeleteView):
    model = Barbeiro
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_barbeiros')
    extra_context = {'titulo': 'Excluir Barbeiro', 'botao': 'Excluir'}


class BarbeiroList(LoginRequiredMixin, ListView):
    model = Barbeiro
    template_name = 'website/listas/barbeiros.html'
    context_object_name = 'barbeiros'


class BarbeiroDetail(LoginRequiredMixin, DetailView):
    model = Barbeiro
    template_name = 'website/ver/barbeiro.html'
    context_object_name = 'barbeiro'


# ==============================================================================
# CLIENTE CRUD
# ==============================================================================

class ClienteCreate(LoginRequiredMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_clientes')
    extra_context = {'titulo': 'Cadastrar Cliente', 'botao': 'Cadastrar'}


class ClienteUpdate(LoginRequiredMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_clientes')
    extra_context = {'titulo': 'Editar Cliente', 'botao': 'Salvar'}


class ClienteDelete(LoginRequiredMixin, DeleteView):
    model = Cliente
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_clientes')
    extra_context = {'titulo': 'Excluir Cliente', 'botao': 'Excluir'}


class ClienteList(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = 'website/listas/clientes.html'
    context_object_name = 'clientes'


class ClienteDetail(LoginRequiredMixin, DetailView):
    model = Cliente
    template_name = 'website/ver/cliente.html'
    context_object_name = 'cliente'


# ==============================================================================
# HORARIO DISPONIVEL CRUD
# ==============================================================================

class HorarioDisponivelCreate(LoginRequiredMixin, CreateView):
    model = HorarioDisponivel
    form_class = HorarioDisponivelForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_horarios')
    extra_context = {'titulo': 'Cadastrar Horário', 'botao': 'Cadastrar'}


class HorarioDisponivelUpdate(LoginRequiredMixin, UpdateView):
    model = HorarioDisponivel
    form_class = HorarioDisponivelForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_horarios')
    extra_context = {'titulo': 'Editar Horário', 'botao': 'Salvar'}


class HorarioDisponivelDelete(LoginRequiredMixin, DeleteView):
    model = HorarioDisponivel
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_horarios')
    extra_context = {'titulo': 'Excluir Horário', 'botao': 'Excluir'}


class HorarioDisponivelList(LoginRequiredMixin, ListView):
    model = HorarioDisponivel
    template_name = 'website/listas/horarios.html'
    context_object_name = 'horarios'


class HorarioDisponivelDetail(LoginRequiredMixin, DetailView):
    model = HorarioDisponivel
    template_name = 'website/ver/horario.html'
    context_object_name = 'horario'


# ==============================================================================
# AGENDAMENTO CRUD
# ==============================================================================

class AgendamentoCreate(LoginRequiredMixin, CreateView):
    model = Agendamento
    form_class = AgendamentoForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_agendamentos')
    extra_context = {'titulo': 'Cadastrar Agendamento', 'botao': 'Cadastrar'}


class AgendamentoUpdate(LoginRequiredMixin, UpdateView):
    model = Agendamento
    form_class = AgendamentoForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_agendamentos')
    extra_context = {'titulo': 'Editar Agendamento', 'botao': 'Salvar'}


class AgendamentoDelete(LoginRequiredMixin, DeleteView):
    model = Agendamento
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_agendamentos')
    extra_context = {'titulo': 'Excluir Agendamento', 'botao': 'Excluir'}


class AgendamentoList(LoginRequiredMixin, ListView):
    model = Agendamento
    template_name = 'website/listas/agendamentos.html'
    context_object_name = 'agendamentos'


class AgendamentoDetail(LoginRequiredMixin, DetailView):
    model = Agendamento
    template_name = 'website/ver/agendamento.html'
    context_object_name = 'agendamento'


# ==============================================================================
# MENSAGEM CONTATO
# ==============================================================================

class MensagemContatoList(LoginRequiredMixin, ListView):
    model = MensagemContato
    template_name = 'website/listas/mensagens.html'
    context_object_name = 'mensagens'


class MensagemContatoDetail(LoginRequiredMixin, DetailView):
    model = MensagemContato
    template_name = 'website/ver/mensagem.html'
    context_object_name = 'mensagem'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.lida:
            obj.lida = True
            obj.save()
        return obj


class MensagemContatoDelete(LoginRequiredMixin, DeleteView):
    model = MensagemContato
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_mensagens')
    extra_context = {'titulo': 'Excluir Mensagem', 'botao': 'Excluir'}


# ==============================================================================
# API
# ==============================================================================

def horarios_disponiveis_api(request):
    barbeiro_id = request.GET.get('barbeiro_id')
    data_str = request.GET.get('data')

    if not barbeiro_id or not data_str:
        return JsonResponse({'horarios': []})

    try:
        data_agendamento = datetime.strptime(data_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return JsonResponse({'horarios': []})

    # All active timeslots for this barber
    horarios_ativos = HorarioDisponivel.objects.filter(
        barbeiro_id=barbeiro_id,
        ativo=True,
    ).values_list('horario', flat=True)

    # Already booked slots for this barber on this date
    agendamentos = Agendamento.objects.filter(
        barbeiro_id=barbeiro_id,
        data=data_agendamento,
    ).exclude(status='cancelado').values_list('horario', flat=True)

    ocupados = set(agendamentos)

    resultado = []
    for h in sorted(horarios_ativos):
        resultado.append({
            'horario': h.strftime('%H:%M'),
            'disponivel': h not in ocupados,
        })

    return JsonResponse({'horarios': resultado})
