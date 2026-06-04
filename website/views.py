import os
from django.conf import settings
from django.views.generic import TemplateView, ListView, DetailView, FormView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q, Avg
from datetime import date, datetime, timedelta
from django.contrib.auth.models import User
from django.contrib.auth import login

from .models import (
    Servico, Barbeiro, Cliente, HorarioDisponivel, Agendamento,
    MensagemContato, PerfilUsuario, Feedback, FotoTrabalho
)
from .forms import (
    ServicoForm, BarbeiroForm, ClienteForm, HorarioDisponivelForm,
    AgendamentoForm, MensagemContatoForm, AgendamentoPublicoForm,
    CadastroForm, PerfilUpdateForm, FeedbackForm, FotoTrabalhoForm
)


# ==============================================================================
# PUBLIC VIEWS
# ==============================================================================

class IndexView(TemplateView):
    template_name = 'website/inicio.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['servicos'] = Servico.objects.filter(ativo=True, destaque=True).order_by('ordem')
        context['barbeiros'] = Barbeiro.objects.filter(ativo=True)
        context['all_servicos'] = Servico.objects.filter(ativo=True)
        context['fotos_trabalho'] = FotoTrabalho.objects.filter(publicado=True).order_by('-criado_em')
        return context


class SobreView(TemplateView):
    template_name = 'website/sobre.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['barbeiros'] = Barbeiro.objects.filter(ativo=True)
        static_dir = os.path.join(settings.BASE_DIR, 'website', 'static', 'website', 'img')
        context['has_diagrama_caso_uso'] = os.path.exists(os.path.join(static_dir, 'diagrama-caso-uso.png'))
        context['has_diagrama_classes'] = os.path.exists(os.path.join(static_dir, 'diagrama-classes.png'))
        return context


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

    def get_initial(self):
        initial = super().get_initial()
        if self.request.user.is_authenticated:
            user = self.request.user
            initial['nome'] = f"{user.first_name} {user.last_name}" or user.username
            initial['email'] = user.email
            perfil = getattr(user, 'perfil', None)
            if perfil:
                initial['telefone'] = perfil.telefone
            else:
                cliente = Cliente.objects.filter(usuario=user).first()
                if cliente:
                    initial['telefone'] = cliente.telefone
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['servicos'] = Servico.objects.filter(ativo=True)
        context['barbeiros'] = Barbeiro.objects.filter(ativo=True)
        context['horarios'] = [
            '08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '11:00', '11:30',
            '12:00', '12:30', '13:00', '13:30', '14:00', '14:30', '15:00', '15:30',
            '16:00', '16:30', '17:00', '17:30', '18:00', '18:30', '19:00', '19:30',
            '20:00', '20:30', '21:00',
        ]
        return context

    def form_valid(self, form):
        email = form.cleaned_data['email']
        nome = form.cleaned_data['nome']
        telefone = form.cleaned_data['telefone']

        if self.request.user.is_authenticated:
            cliente, created = Cliente.objects.get_or_create(
                usuario=self.request.user,
                defaults={'nome': nome, 'email': email, 'telefone': telefone},
            )
            if not created:
                cliente.nome = nome
                cliente.email = email
                cliente.telefone = telefone
                cliente.save()
        else:
            cliente, created = Cliente.objects.get_or_create(
                email=email,
                defaults={'nome': nome, 'telefone': telefone},
            )
            if not created:
                cliente.nome = nome
                cliente.telefone = telefone
                cliente.save()

        Agendamento.objects.create(
            usuario=self.request.user if self.request.user.is_authenticated else None,
            cliente=cliente,
            servico=form.cleaned_data['servico'],
            barbeiro=form.cleaned_data['barbeiro'],
            data=form.cleaned_data['data'],
            horario=form.cleaned_data['horario'],
            observacoes=form.cleaned_data.get('observacoes', ''),
            status='Pendente',
        )

        messages.success(self.request, 'Agendamento realizado com sucesso! A Delacruz Barber aguarda você.')
        if self.request.user.is_authenticated:
            perfil = getattr(self.request.user, 'perfil', None)
            if perfil and perfil.tipo_usuario == 'Cliente':
                return redirect('area_cliente')
        return redirect(self.success_url)



# ==============================================================================
# DASHBOARD
# ==============================================================================

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'website/dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        user = request.user
        
        # 1. Admin/staff/superuser -> /dashboard/
        if user.is_superuser or user.is_staff:
            return super().dispatch(request, *args, **kwargs)
            
        perfil = getattr(user, 'perfil', None)
        if perfil and perfil.tipo_usuario.lower() == 'administrador':
            return super().dispatch(request, *args, **kwargs)
            
        # 2. Barbeiro -> /barbeiro/area/
        # Check whether the logged user has a related Barbeiro record or PerfilUsuario.tipo_usuario == "barbeiro"
        if (perfil and perfil.tipo_usuario.lower() == 'barbeiro') or Barbeiro.objects.filter(usuario=user).exists():
            return redirect('area_barbeiro')
            
        # 3. Cliente -> /cliente/area/
        return redirect('area_cliente')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoje = date.today()
        agendamentos_hoje = Agendamento.objects.filter(data=hoje, usuario=self.request.user)

        context['hoje'] = hoje
        context['total_hoje'] = agendamentos_hoje.count()
        context['pendentes'] = agendamentos_hoje.filter(status='Pendente').count()
        context['confirmados'] = agendamentos_hoje.filter(status='Confirmado').count()
        context['concluidos'] = agendamentos_hoje.filter(status='Concluído').count()
        context['receita_hoje'] = (
            agendamentos_hoje.filter(status='Concluído')
            .aggregate(total=Sum('servico__preco'))['total'] or 0
        )
        context['ultimos_agendamentos'] = Agendamento.objects.filter(usuario=self.request.user)[:10]
        context['total_clientes'] = Cliente.objects.filter(usuario=self.request.user).count()
        context['mensagens_nao_lidas'] = MensagemContato.objects.filter(lida=False, usuario=self.request.user).count()
        return context


class AdminStaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        if self.request.user.is_superuser or self.request.user.is_staff:
            return True
        perfil = getattr(self.request.user, 'perfil', None)
        if perfil and perfil.tipo_usuario.lower() == 'administrador':
            return True
        return False


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.is_superuser)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied





class BarbeiroRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        perfil = getattr(user, 'perfil', None)
        if perfil and perfil.tipo_usuario.lower() == 'barbeiro':
            return True
        if Barbeiro.objects.filter(usuario=user).exists():
            return True
        return False

    def handle_no_permission(self):
        messages.error(self.request, 'Acesso restrito a barbeiros autorizados.')
        return redirect('pagina_inicial')


# ==============================================================================
# SERVICO CRUD
# ==============================================================================

# ==============================================================================
# SERVICO CRUD
# ==============================================================================

class ServicoCreate(LoginRequiredMixin, AdminStaffRequiredMixin, CreateView):
    model = Servico
    form_class = ServicoForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_servicos')
    extra_context = {'titulo': 'Cadastrar Serviço', 'botao': 'Cadastrar'}

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        return super().form_valid(form)


class ServicoUpdate(LoginRequiredMixin, AdminStaffRequiredMixin, UpdateView):
    model = Servico
    form_class = ServicoForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_servicos')
    extra_context = {'titulo': 'Editar Serviço', 'botao': 'Salvar alterações'}

    def get_queryset(self):
        return self.model.objects.all()


class ServicoDelete(LoginRequiredMixin, AdminStaffRequiredMixin, DeleteView):
    model = Servico
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_servicos')
    extra_context = {'titulo': 'Excluir Serviço', 'botao': 'Excluir'}

    def get_queryset(self):
        return self.model.objects.all()


class ServicoList(LoginRequiredMixin, AdminStaffRequiredMixin, ListView):
    model = Servico
    template_name = 'website/listas/servicos.html'
    context_object_name = 'servicos'

    def get_queryset(self):
        return self.model.objects.all()


class ServicoDetail(LoginRequiredMixin, AdminStaffRequiredMixin, DetailView):
    model = Servico
    template_name = 'website/ver/servico.html'
    context_object_name = 'servico'

    def get_queryset(self):
        return self.model.objects.all()


# ==============================================================================
# BARBEIRO CRUD
# ==============================================================================

class BarbeiroCreate(AdminRequiredMixin, CreateView):
    model = Barbeiro
    form_class = BarbeiroForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_barbeiros')
    extra_context = {'titulo': 'Cadastrar Barbeiro', 'botao': 'Cadastrar'}

    def form_valid(self, form):
        response = super().form_valid(form)
        if form.instance.usuario:
            perfil, _ = PerfilUsuario.objects.get_or_create(usuario=form.instance.usuario)
            perfil.tipo_usuario = 'barbeiro'
            perfil.save()
        return response


class BarbeiroUpdate(AdminRequiredMixin, UpdateView):
    model = Barbeiro
    form_class = BarbeiroForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_barbeiros')
    extra_context = {'titulo': 'Editar Barbeiro', 'botao': 'Salvar alterações'}

    def get_queryset(self):
        return self.model.objects.all()

    def form_valid(self, form):
        response = super().form_valid(form)
        if form.instance.usuario:
            perfil, _ = PerfilUsuario.objects.get_or_create(usuario=form.instance.usuario)
            perfil.tipo_usuario = 'barbeiro'
            perfil.save()
        return response


class BarbeiroDelete(AdminRequiredMixin, DeleteView):
    model = Barbeiro
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_barbeiros')
    extra_context = {'titulo': 'Excluir Barbeiro', 'botao': 'Excluir'}

    def get_queryset(self):
        return self.model.objects.all()


class BarbeiroList(AdminRequiredMixin, ListView):
    model = Barbeiro
    template_name = 'website/listas/barbeiros.html'
    context_object_name = 'barbeiros'

    def get_queryset(self):
        return self.model.objects.all()


class BarbeiroDetail(AdminRequiredMixin, DetailView):
    model = Barbeiro
    template_name = 'website/ver/barbeiro.html'
    context_object_name = 'barbeiro'

    def get_queryset(self):
        return self.model.objects.all()



# ==============================================================================
# CLIENTE CRUD
# ==============================================================================

class ClienteCreate(LoginRequiredMixin, AdminStaffRequiredMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_clientes')
    extra_context = {'titulo': 'Cadastrar Cliente', 'botao': 'Cadastrar'}

    def form_valid(self, form):
        return super().form_valid(form)


class ClienteUpdate(LoginRequiredMixin, AdminStaffRequiredMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_clientes')
    extra_context = {'titulo': 'Editar Cliente', 'botao': 'Salvar alterações'}

    def get_queryset(self):
        return self.model.objects.all()


class ClienteDelete(LoginRequiredMixin, AdminStaffRequiredMixin, DeleteView):
    model = Cliente
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_clientes')
    extra_context = {'titulo': 'Excluir Cliente', 'botao': 'Excluir'}

    def get_queryset(self):
        return self.model.objects.all()


class ClienteList(LoginRequiredMixin, AdminStaffRequiredMixin, ListView):
    model = Cliente
    template_name = 'website/listas/clientes.html'
    context_object_name = 'clientes'

    def get_queryset(self):
        return self.model.objects.all()


class ClienteDetail(LoginRequiredMixin, AdminStaffRequiredMixin, DetailView):
    model = Cliente
    template_name = 'website/ver/cliente.html'
    context_object_name = 'cliente'

    def get_queryset(self):
        return self.model.objects.all()


# ==============================================================================
# HORARIO DISPONIVEL CRUD
# ==============================================================================

class HorarioDisponivelCreate(LoginRequiredMixin, AdminStaffRequiredMixin, CreateView):
    model = HorarioDisponivel
    form_class = HorarioDisponivelForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_horarios')
    extra_context = {'titulo': 'Cadastrar Horário', 'botao': 'Cadastrar'}

    def form_valid(self, form):
        return super().form_valid(form)


class HorarioDisponivelUpdate(LoginRequiredMixin, AdminStaffRequiredMixin, UpdateView):
    model = HorarioDisponivel
    form_class = HorarioDisponivelForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_horarios')
    extra_context = {'titulo': 'Editar Horário', 'botao': 'Salvar alterações'}

    def get_queryset(self):
        return self.model.objects.all()


class HorarioDisponivelDelete(LoginRequiredMixin, AdminStaffRequiredMixin, DeleteView):
    model = HorarioDisponivel
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_horarios')
    extra_context = {'titulo': 'Excluir Horário', 'botao': 'Excluir'}

    def get_queryset(self):
        return self.model.objects.all()


class HorarioDisponivelList(LoginRequiredMixin, AdminStaffRequiredMixin, ListView):
    model = HorarioDisponivel
    template_name = 'website/listas/horarios.html'
    context_object_name = 'horarios'

    def get_queryset(self):
        return self.model.objects.all()


class HorarioDisponivelDetail(LoginRequiredMixin, AdminStaffRequiredMixin, DetailView):
    model = HorarioDisponivel
    template_name = 'website/ver/horario.html'
    context_object_name = 'horario'

    def get_queryset(self):
        return self.model.objects.all()


# ==============================================================================
# AGENDAMENTO CRUD
# ==============================================================================

class AgendamentoCreate(LoginRequiredMixin, AdminStaffRequiredMixin, CreateView):
    model = Agendamento
    form_class = AgendamentoForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_agendamentos')
    extra_context = {'titulo': 'Cadastrar Agendamento', 'botao': 'Cadastrar'}

    def form_valid(self, form):
        return super().form_valid(form)


class AgendamentoUpdate(LoginRequiredMixin, AdminStaffRequiredMixin, UpdateView):
    model = Agendamento
    form_class = AgendamentoForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_agendamentos')
    extra_context = {'titulo': 'Editar Agendamento', 'botao': 'Salvar alterações'}

    def get_queryset(self):
        return self.model.objects.all()


class AgendamentoDelete(LoginRequiredMixin, AdminStaffRequiredMixin, DeleteView):
    model = Agendamento
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_agendamentos')
    extra_context = {'titulo': 'Excluir Agendamento', 'botao': 'Excluir'}

    def get_queryset(self):
        return self.model.objects.all()


class AgendamentoList(LoginRequiredMixin, AdminStaffRequiredMixin, ListView):
    model = Agendamento
    template_name = 'website/listas/agendamentos.html'
    context_object_name = 'agendamentos'

    def get_queryset(self):
        return self.model.objects.all()


class AgendamentoDetail(LoginRequiredMixin, AdminStaffRequiredMixin, DetailView):
    model = Agendamento
    template_name = 'website/ver/agendamento.html'
    context_object_name = 'agendamento'

    def get_queryset(self):
        return self.model.objects.all()


# ==============================================================================
# MENSAGEM CONTATO
# ==============================================================================

class MensagemContatoList(LoginRequiredMixin, AdminStaffRequiredMixin, ListView):
    model = MensagemContato
    template_name = 'website/listas/mensagens.html'
    context_object_name = 'mensagens'

    def get_queryset(self):
        return self.model.objects.all()


class MensagemContatoDetail(LoginRequiredMixin, AdminStaffRequiredMixin, DetailView):
    model = MensagemContato
    template_name = 'website/ver/mensagem.html'
    context_object_name = 'mensagem'

    def get_queryset(self):
        return self.model.objects.all()

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.lida:
            obj.lida = True
            obj.save()
        return obj


class MensagemContatoDelete(LoginRequiredMixin, AdminStaffRequiredMixin, DeleteView):
    model = MensagemContato
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_mensagens')
    extra_context = {'titulo': 'Excluir Mensagem', 'botao': 'Excluir'}

    def get_queryset(self):
        return self.model.objects.all()


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
    ).exclude(status='Cancelado').values_list('horario', flat=True)

    ocupados = set(agendamentos)

    resultado = []
    for h in sorted(horarios_ativos):
        resultado.append({
            'horario': h.strftime('%H:%M'),
            'disponivel': h not in ocupados,
        })

    return JsonResponse({'horarios': resultado})


# ==============================================================================
# AUTH & REGISTRATION
# ==============================================================================

class CadastroUsuarioView(FormView):
    template_name = 'website/cadastro.html'
    form_class = CadastroForm

    def form_valid(self, form):
        nome = form.cleaned_data['nome']
        sobrenome = form.cleaned_data['sobrenome']
        username = form.cleaned_data['usuario']
        email = form.cleaned_data['email']
        telefone = form.cleaned_data['telefone']
        senha = form.cleaned_data['senha']

        # Create User
        user = User.objects.create_user(
            username=username,
            email=email,
            password=senha,
            first_name=nome,
            last_name=sobrenome
        )

        # Create Profile
        PerfilUsuario.objects.create(
            usuario=user,
            tipo_usuario='cliente',
            telefone=telefone
        )

        # Create or link a Cliente record
        cliente = Cliente.objects.filter(email=email).first()
        if cliente:
            cliente.usuario = user
            cliente.nome = f"{nome} {sobrenome}"
            cliente.telefone = telefone
            cliente.save()
        else:
            Cliente.objects.create(
                usuario=user,
                nome=f"{nome} {sobrenome}",
                email=email,
                telefone=telefone
            )

        login(self.request, user)
        messages.success(self.request, 'Cadastro realizado com sucesso!')
        return redirect('area_cliente')


# ==============================================================================
# CLIENT AREA
# ==============================================================================

class AreaClienteView(LoginRequiredMixin, TemplateView):
    template_name = 'website/cliente/area_cliente.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        cliente, _ = Cliente.objects.get_or_create(
            usuario=user,
            defaults={
                'nome': f"{user.first_name} {user.last_name}" or user.username,
                'email': user.email,
                'telefone': getattr(getattr(user, 'perfil', None), 'telefone', '')
            }
        )
        
        initial_data = {
            'nome': user.first_name,
            'sobrenome': user.last_name,
            'email': user.email,
            'telefone': getattr(user.perfil, 'telefone', '') if hasattr(user, 'perfil') else ''
        }
        context['profile_form'] = PerfilUpdateForm(initial=initial_data)
        
        agendamentos = Agendamento.objects.filter(cliente=cliente)
        context['proximos'] = agendamentos.filter(
            status__in=['Pendente', 'Confirmado'],
            data__gte=date.today()
        ).order_by('data', 'horario')
        
        concluidos = agendamentos.filter(status='Concluído').order_by('-data', '-horario')
        context['historico'] = concluidos
        context['ultimo_servico'] = concluidos.first() if concluidos.exists() else None
        
        return context

    def post(self, request, *args, **kwargs):
        user = request.user
        form = PerfilUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            user.first_name = form.cleaned_data['nome']
            user.last_name = form.cleaned_data['sobrenome']
            user.email = form.cleaned_data['email']
            user.save()
            
            perfil, _ = PerfilUsuario.objects.get_or_create(usuario=user)
            perfil.telefone = form.cleaned_data['telefone']
            if 'foto_perfil' in request.FILES:
                perfil.foto_perfil = request.FILES['foto_perfil']
            perfil.save()
            
            cliente = Cliente.objects.filter(usuario=user).first()
            if cliente:
                cliente.nome = f"{user.first_name} {user.last_name}"
                cliente.email = user.email
                cliente.telefone = form.cleaned_data['telefone']
                cliente.save()
                
            messages.success(request, 'Perfil atualizado com sucesso!')
        else:
            messages.error(request, 'Erro ao atualizar perfil. Verifique os dados.')
            
        return redirect('area_cliente')


class PerfilClienteView(LoginRequiredMixin, FormView):
    template_name = 'website/cliente/perfil_cliente.html'
    form_class = PerfilUpdateForm
    success_url = reverse_lazy('area_cliente')

    def get_initial(self):
        user = self.request.user
        telefone = getattr(user.perfil, 'telefone', '') if hasattr(user, 'perfil') else ''
        return {
            'nome': user.first_name,
            'sobrenome': user.last_name,
            'email': user.email,
            'telefone': telefone
        }

    def form_valid(self, form):
        user = self.request.user
        user.first_name = form.cleaned_data['nome']
        user.last_name = form.cleaned_data['sobrenome']
        user.email = form.cleaned_data['email']
        user.save()
        
        perfil, _ = PerfilUsuario.objects.get_or_create(usuario=user)
        perfil.telefone = form.cleaned_data['telefone']
        if 'foto_perfil' in self.request.FILES:
            perfil.foto_perfil = self.request.FILES['foto_perfil']
        perfil.save()

        cliente = Cliente.objects.filter(usuario=user).first()
        if cliente:
            cliente.nome = f"{user.first_name} {user.last_name}"
            cliente.email = user.email
            cliente.telefone = form.cleaned_data['telefone']
            cliente.save()

        messages.success(self.request, 'Perfil atualizado com sucesso!')
        return super().form_valid(form)


class HistoricoClienteView(LoginRequiredMixin, ListView):
    model = Agendamento
    template_name = 'website/cliente/historico_cliente.html'
    context_object_name = 'agendamentos'

    def get_queryset(self):
        cliente = Cliente.objects.filter(usuario=self.request.user).first()
        if not cliente:
            return Agendamento.objects.none()
        return Agendamento.objects.filter(cliente=cliente).order_by('-data', '-horario')


class FeedbackCreateView(LoginRequiredMixin, CreateView):
    model = Feedback
    form_class = FeedbackForm
    template_name = 'website/cliente/feedback.html'
    success_url = reverse_lazy('area_cliente')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agendamento'] = Agendamento.objects.get(pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        agendamento = Agendamento.objects.get(pk=self.kwargs['pk'])
        cliente = Cliente.objects.filter(usuario=self.request.user).first()

        if agendamento.cliente != cliente:
            messages.error(self.request, 'Você não tem permissão para avaliar este agendamento.')
            return redirect('area_cliente')
        
        if agendamento.status != 'Concluído':
            messages.error(self.request, 'Você só pode avaliar agendamentos concluídos.')
            return redirect('area_cliente')

        if Feedback.objects.filter(agendamento=agendamento).exists():
            messages.error(self.request, 'Você já enviou avaliação para este agendamento.')
            return redirect('area_cliente')

        form.instance.usuario = self.request.user
        form.instance.cliente = cliente
        form.instance.barbeiro = agendamento.barbeiro
        form.instance.agendamento = agendamento
        form.instance.aprovado = True

        messages.success(self.request, 'Feedback enviado com sucesso!')
        return super().form_valid(form)


class CancelarAgendamentoClienteView(LoginRequiredMixin, TemplateView):
    def post(self, request, pk, *args, **kwargs):
        agendamento = Agendamento.objects.filter(pk=pk).first()
        cliente = Cliente.objects.filter(usuario=request.user).first()
        if agendamento and agendamento.cliente == cliente and agendamento.status in ['Pendente', 'Confirmado']:
            agendamento.status = 'Cancelado'
            agendamento.save()
            messages.success(request, 'Agendamento cancelado com sucesso!')
        else:
            messages.error(request, 'Não foi possível cancelar este agendamento.')
        return redirect('area_cliente')


# ==============================================================================
# BARBER AREA
# ==============================================================================

class AreaBarbeiroView(BarbeiroRequiredMixin, TemplateView):
    template_name = 'website/barbeiro/area_barbeiro.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        barbeiro = Barbeiro.objects.filter(usuario=user).first()
        if not barbeiro and (user.is_superuser or user.is_staff):
            barbeiro = Barbeiro.objects.first()
        
        context['barbeiro'] = barbeiro
        
        initial_data = {
            'nome': user.first_name,
            'sobrenome': user.last_name,
            'email': user.email,
            'telefone': getattr(user.perfil, 'telefone', '') if hasattr(user, 'perfil') else ''
        }
        context['profile_form'] = PerfilUpdateForm(initial=initial_data)

        if barbeiro:
            agendamentos = Agendamento.objects.filter(barbeiro=barbeiro)
            context['proximos'] = agendamentos.filter(
                status__in=['Pendente', 'Confirmado'],
                data__gte=date.today()
            ).order_by('data', 'horario')[:10]
            
            context['concluidos'] = agendamentos.filter(status='Concluído').order_by('-data', '-horario')[:10]
            
            hoje = date.today()
            context['receita_hoje'] = agendamentos.filter(
                status='Concluído',
                data=hoje
            ).aggregate(total=Sum('servico__preco'))['total'] or 0
            
            trinta_dias_atras = hoje - timedelta(days=30)
            context['receita_30_dias'] = agendamentos.filter(
                status='Concluído',
                data__gte=trinta_dias_atras
            ).aggregate(total=Sum('servico__preco'))['total'] or 0
            
            context['feedbacks'] = Feedback.objects.filter(barbeiro=barbeiro).order_by('-criado_em')
            context['fotos'] = FotoTrabalho.objects.filter(barbeiro=barbeiro).order_by('-criado_em')[:6]
        else:
            context['proximos'] = []
            context['concluidos'] = []
            context['receita_hoje'] = 0
            context['receita_30_dias'] = 0
            context['feedbacks'] = []
            context['fotos'] = []
            
        return context

    def post(self, request, *args, **kwargs):
        user = request.user
        form = PerfilUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            user.first_name = form.cleaned_data['nome']
            user.last_name = form.cleaned_data['sobrenome']
            user.email = form.cleaned_data['email']
            user.save()
            
            perfil, _ = PerfilUsuario.objects.get_or_create(usuario=user)
            perfil.telefone = form.cleaned_data['telefone']
            if 'foto_perfil' in request.FILES:
                perfil.foto_perfil = request.FILES['foto_perfil']
            perfil.save()
            
            barbeiro = Barbeiro.objects.filter(usuario=user).first()
            if barbeiro:
                barbeiro.nome = f"{user.first_name} {user.last_name}"
                barbeiro.save()
                
            messages.success(request, 'Perfil atualizado com sucesso!')
        else:
            messages.error(request, 'Erro ao atualizar perfil. Verifique os dados.')
            
        return redirect('area_barbeiro')


class AgendamentosBarbeiroView(BarbeiroRequiredMixin, ListView):
    model = Agendamento
    template_name = 'website/barbeiro/agendamentos_barbeiro.html'
    context_object_name = 'agendamentos'

    def get_queryset(self):
        barbeiro = Barbeiro.objects.filter(usuario=self.request.user).first()
        if not barbeiro:
            return Agendamento.objects.none()
        return Agendamento.objects.filter(barbeiro=barbeiro).order_by('-data', '-horario')

    def post(self, request, *args, **kwargs):
        agendamento_id = request.POST.get('agendamento_id')
        novo_status = request.POST.get('status')
        
        if not agendamento_id or not novo_status:
            messages.error(request, 'Dados inválidos.')
            return redirect('agendamentos_barbeiro')
            
        agendamento = Agendamento.objects.filter(pk=agendamento_id).first()
        barbeiro = Barbeiro.objects.filter(usuario=request.user).first()
        
        if not agendamento or agendamento.barbeiro != barbeiro:
            messages.error(request, 'Você não tem permissão para alterar este agendamento.')
            return redirect('agendamentos_barbeiro')
            
        if novo_status in ['Confirmado', 'Concluído', 'Cancelado']:
            agendamento.status = novo_status
            agendamento.save()
            messages.success(request, f'Status do agendamento atualizado para {novo_status}!')
        else:
            messages.error(request, 'Status inválido.')
            
        return redirect('agendamentos_barbeiro')


class HistoricoBarbeiroView(BarbeiroRequiredMixin, ListView):
    model = Agendamento
    template_name = 'website/barbeiro/historico_barbeiro.html'
    context_object_name = 'agendamentos'

    def get_queryset(self):
        barbeiro = Barbeiro.objects.filter(usuario=self.request.user).first()
        if not barbeiro:
            return Agendamento.objects.none()
        return Agendamento.objects.filter(barbeiro=barbeiro, status='Concluído').order_by('-data', '-horario')


class RelatoriosBarbeiroView(BarbeiroRequiredMixin, TemplateView):
    template_name = 'website/barbeiro/relatorios_barbeiro.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        barbeiro = Barbeiro.objects.filter(usuario=self.request.user).first()
        if not barbeiro:
            return context
            
        hoje = date.today()
        ontem = hoje - timedelta(days=1)
        trinta_dias_atras = hoje - timedelta(days=30)
        
        agendamentos = Agendamento.objects.filter(barbeiro=barbeiro, status='Concluído')
        
        context['receita_hoje'] = agendamentos.filter(data=hoje).aggregate(total=Sum('servico__preco'))['total'] or 0
        context['receita_ontem'] = agendamentos.filter(data=ontem).aggregate(total=Sum('servico__preco'))['total'] or 0
        context['receita_30_dias'] = agendamentos.filter(data__gte=trinta_dias_atras).aggregate(total=Sum('servico__preco'))['total'] or 0
        
        context['qtd_hoje'] = agendamentos.filter(data=hoje).count()
        context['qtd_30_dias'] = agendamentos.filter(data__gte=trinta_dias_atras).count()
        
        context['servicos_mais_pedidos'] = (
            agendamentos.values('servico__nome')
            .annotate(quantidade=Count('servico'))
            .order_by('-quantidade')[:5]
        )
        
        feedbacks = Feedback.objects.filter(barbeiro=barbeiro)
        avg_nota = feedbacks.aggregate(media=Avg('nota'))['media']
        context['nota_media'] = round(avg_nota, 1) if avg_nota else 0
        
        return context


class FotoTrabalhoListView(BarbeiroRequiredMixin, ListView):
    model = FotoTrabalho
    template_name = 'website/barbeiro/fotos_barbeiro.html'
    context_object_name = 'fotos'

    def get_queryset(self):
        barbeiro = Barbeiro.objects.filter(usuario=self.request.user).first()
        if not barbeiro:
            return FotoTrabalho.objects.none()
        return FotoTrabalho.objects.filter(barbeiro=barbeiro).order_by('-criado_em')


class FotoTrabalhoCreateView(BarbeiroRequiredMixin, CreateView):
    model = FotoTrabalho
    form_class = FotoTrabalhoForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('fotos_barbeiro')
    extra_context = {'titulo': 'Cadastrar Foto de Trabalho', 'botao': 'Cadastrar'}

    def form_valid(self, form):
        barbeiro = Barbeiro.objects.filter(usuario=self.request.user).first()
        if not barbeiro:
            messages.error(self.request, 'Você precisa ter um perfil de barbeiro cadastrado.')
            return redirect('pagina_inicial')
        form.instance.usuario = self.request.user
        form.instance.barbeiro = barbeiro
        messages.success(self.request, 'Foto cadastrada com sucesso!')
        return super().form_valid(form)


class FotoTrabalhoUpdateView(BarbeiroRequiredMixin, UpdateView):
    model = FotoTrabalho
    form_class = FotoTrabalhoForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('fotos_barbeiro')
    extra_context = {'titulo': 'Editar Foto de Trabalho', 'botao': 'Salvar'}

    def get_queryset(self):
        return FotoTrabalho.objects.filter(usuario=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Foto atualizada com sucesso!')
        return super().form_valid(form)


class FotoTrabalhoDeleteView(BarbeiroRequiredMixin, DeleteView):
    model = FotoTrabalho
    template_name = 'website/form.html'
    success_url = reverse_lazy('fotos_barbeiro')
    extra_context = {'titulo': 'Excluir Foto de Trabalho', 'botao': 'Excluir'}

    def get_queryset(self):
        return FotoTrabalho.objects.filter(usuario=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Foto excluída com sucesso!')
        return super().delete(request, *args, **kwargs)

