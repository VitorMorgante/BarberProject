import os
import json
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.conf import settings
from django.db import transaction
from django.db.models import Sum, Count, Q, Avg, F
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, ListView, DetailView, FormView, View
from django.views.generic.edit import CreateView, UpdateView, DeleteView

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
from .forms import (
    ServicoForm, BarbeiroForm, ClienteForm, HorarioDisponivelForm,
    AgendamentoForm, MensagemContatoForm, AgendamentoPublicoForm,
    CadastroForm, PerfilUpdateForm, FeedbackForm, FotoTrabalhoForm,
    PlanoAssinaturaForm, ProdutoForm, MovimentacaoEstoqueForm, ItemComandaForm,
    RegraComissaoForm, MetaBarbeiroForm, RepasseComissaoForm,
    ConfiguracaoEstabelecimentoForm, ListaEsperaForm, AnaliseEstiloForm,
    HistoricoVisualClienteForm
)
from website.services.agendamento_service import AgendamentoService
from website.services.subscription_service import SubscriptionService
from website.services.loyalty_service import LoyaltyService
from website.services.inventory_service import InventoryService
from website.services.comissao_service import ComissaoService
from website.services.payment_service import PaymentService
from website.services.whatsapp_service import WhatsAppService
from website.services.style_ai_service import StyleAIService


# ==============================================================================
# PERMISSÕES / MIXINS
# ==============================================================================

class AdminStaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        perfil = getattr(user, 'perfil', None)
        return bool(perfil and perfil.tipo_usuario.lower() == 'administrador')

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('login')
        messages.error(self.request, 'Acesso restrito à administração da Delacruz Barber.')
        return redirect('pagina_inicial')


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.is_staff or user.is_superuser)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('login')
        messages.error(self.request, 'Acesso restrito ao Administrador.')
        return redirect('pagina_inicial')


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
        return Barbeiro.objects.filter(usuario=user).exists()

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('login')
        messages.error(self.request, 'Acesso restrito aos barbeiros autorizados.')
        return redirect('pagina_inicial')


# ==============================================================================
# 1. PÚBLICO & PWA
# ==============================================================================

class IndexView(TemplateView):
    template_name = 'website/inicio.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['servicos'] = Servico.objects.filter(ativo=True, destaque=True).order_by('ordem')
        context['barbeiros'] = Barbeiro.objects.filter(ativo=True)
        context['all_servicos'] = Servico.objects.filter(ativo=True)
        context['fotos_trabalho'] = FotoTrabalho.objects.filter(publicado=True).order_by('-criado_em')[:8]
        context['planos_club'] = PlanoAssinatura.objects.filter(ativo=True).order_by('preco_mensal')[:3]
        context['estilos_catalogo'] = EstiloCorte.objects.filter(ativo=True)[:6]
        return context


class SobreView(TemplateView):
    template_name = 'website/sobre.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['barbeiros'] = Barbeiro.objects.filter(ativo=True)
        return context


class ServicosPublicView(ListView):
    model = Servico
    template_name = 'website/servicos.html'
    context_object_name = 'servicos'

    def get_queryset(self):
        return Servico.objects.filter(ativo=True).order_by('ordem', 'nome')


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
        messages.success(self.request, 'Mensagem enviada com sucesso! A equipe Delacruz Barber entrará em contato.')
        return super().form_valid(form)


class AgendamentoPublicoView(FormView):
    template_name = 'website/agendamento.html'
    form_class = AgendamentoPublicoForm
    success_url = reverse_lazy('agendamento')

    def get_initial(self):
        initial = super().get_initial()
        if self.request.user.is_authenticated:
            user = self.request.user
            nome_completo = f"{user.first_name} {user.last_name}".strip() or user.username
            initial['nome'] = nome_completo
            initial['email'] = user.email
            perfil = getattr(user, 'perfil', None)
            if perfil and perfil.telefone:
                initial['telefone'] = perfil.telefone
            else:
                cliente = Cliente.objects.filter(usuario=user).first()
                if cliente:
                    initial['telefone'] = cliente.telefone
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['servicos'] = Servico.objects.filter(ativo=True).order_by('ordem', 'nome')
        context['barbeiros'] = Barbeiro.objects.filter(ativo=True)
        context['produtos_adicionais'] = Produto.objects.filter(ativo=True, estoque_atual__gt=0)[:4]
        context['config'] = ConfiguracaoEstabelecimento.get_solo()
        return context

    @transaction.atomic
    def form_valid(self, form):
        email = form.cleaned_data['email']
        nome = form.cleaned_data['nome']
        telefone = form.cleaned_data['telefone']
        servico = form.cleaned_data['servico']
        barbeiro = form.cleaned_data['barbeiro']
        data_agendamento = form.cleaned_data['data']
        horario_agendamento = form.cleaned_data['horario']
        observacoes = form.cleaned_data.get('observacoes', '')

        # Localiza ou cria o Cliente correspondente
        if self.request.user.is_authenticated:
            cliente, _ = Cliente.objects.get_or_create(
                usuario=self.request.user,
                defaults={'nome': nome, 'email': email, 'telefone': telefone}
            )
            cliente.nome = nome
            cliente.email = email
            cliente.telefone = telefone
            cliente.save()
        else:
            cliente, _ = Cliente.objects.get_or_create(
                email=email,
                defaults={'nome': nome, 'telefone': telefone}
            )
            cliente.nome = nome
            cliente.telefone = telefone
            cliente.save()

        # Verifica concorrência de horário antes de gravar
        conflito = Agendamento.objects.filter(
            barbeiro=barbeiro,
            data=data_agendamento,
            horario=horario_agendamento
        ).exclude(status=Agendamento.Status.CANCELADO).exists()

        if conflito:
            messages.error(self.request, 'Este horário acabou de ser reservado por outro cliente. Por favor, escolha outro.')
            return redirect('agendamento')

        # Cria o agendamento
        agendamento = Agendamento.objects.create(
            usuario=self.request.user if self.request.user.is_authenticated else None,
            cliente=cliente,
            servico=servico,
            barbeiro=barbeiro,
            data=data_agendamento,
            horario=horario_agendamento,
            observacoes=observacoes,
            status=Agendamento.Status.PENDENTE
        )

        # Cria Comanda inicial
        comanda = Comanda.objects.create(
            agendamento=agendamento,
            cliente=cliente,
            barbeiro=barbeiro,
            subtotal=servico.preco,
            valor_total=servico.preco,
            status=Comanda.Status.ABERTA
        )
        ItemComanda.objects.create(
            comanda=comanda,
            tipo=ItemComanda.Tipo.SERVICO,
            servico=servico,
            descricao=servico.nome,
            quantidade=1,
            preco_unitario=servico.preco,
            total=servico.preco
        )

        # Verifica cobrança de Sinal PIX
        config = ConfiguracaoEstabelecimento.get_solo()
        valor_sinal = PaymentService.calcular_sinal_agendamento(servico, config)

        if valor_sinal > Decimal('0.00'):
            pagamento = PaymentService.criar_pagamento_sinal(agendamento)
            messages.info(self.request, f'Agendamento iniciado! Realize o pagamento do sinal de R$ {valor_sinal} via PIX para garantir sua vaga.')
            return redirect('pagamento_pix', identificador=pagamento.identificador_interno)

        # Se não exige sinal, confirma e redireciona
        agendamento.status = Agendamento.Status.CONFIRMADO
        agendamento.save(update_fields=['status'])
        messages.success(self.request, 'Agendamento confirmado com sucesso! A Delacruz Barber aguarda você.')

        if self.request.user.is_authenticated:
            return redirect('area_cliente')
        return redirect('agendamento')


# ==============================================================================
# 2. PAGAMENTOS, SINAL E PIX VIEW & WEBHOOK
# ==============================================================================

class PagamentoPixView(TemplateView):
    template_name = 'website/pagamento_pix.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        identificador = self.kwargs.get('identificador')
        pagamento = get_object_or_404(Pagamento, identificador_interno=identificador)
        context['pagamento'] = pagamento
        context['agendamento'] = pagamento.agendamento
        context['config'] = ConfiguracaoEstabelecimento.get_solo()
        return context

    def post(self, request, *args, **kwargs):
        """Simulador de pagamento para desenvolvimento e testes rápidos."""
        identificador = self.kwargs.get('identificador')
        pagamento = get_object_or_404(Pagamento, identificador_interno=identificador)
        PaymentService.confirmar_pagamento(pagamento, payload="Confirmação Manual / Mock")
        messages.success(request, 'Pagamento PIX confirmado com sucesso! Seu horário está garantido.')
        if request.user.is_authenticated:
            return redirect('area_cliente')
        return redirect('pagina_inicial')


def pagamento_status_api(request, identificador):
    """Endpoint AJAX para polling do status de pagamento."""
    pagamento = Pagamento.objects.filter(identificador_interno=identificador).first()
    if not pagamento:
        return JsonResponse({'status': 'not_found'}, status=404)

    # Verifica expiração
    if pagamento.status == Pagamento.Status.AGUARDANDO and pagamento.expiracao_em and timezone.now() > pagamento.expiracao_em:
        pagamento.status = Pagamento.Status.EXPIRADO
        pagamento.save(update_fields=['status'])
        if pagamento.agendamento:
            pagamento.agendamento.status = Agendamento.Status.CANCELADO
            pagamento.agendamento.save(update_fields=['status'])

    return JsonResponse({
        'status': pagamento.status,
        'pago': pagamento.status == Pagamento.Status.PAGO,
        'expirado': pagamento.status == Pagamento.Status.EXPIRADO,
        'valor': str(pagamento.valor),
    })


@csrf_exempt
def webhook_pagamento(request, gateway):
    """Endpoint receptor de webhooks idempotentes dos gateways (Mercado Pago, Asaas, etc)."""
    if request.method != 'POST':
        return HttpResponse("Method not allowed", status=405)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        payload = request.POST.dict()

    evento_id = request.headers.get('X-Event-Id') or payload.get('id') or payload.get('data', {}).get('id') or str(timezone.now().timestamp())
    sucesso = PaymentService.processar_webhook(gateway=gateway, evento_id=str(evento_id), payload_dict=payload)

    if sucesso:
        return JsonResponse({'status': 'processed'})
    return JsonResponse({'status': 'ignored_or_error'}, status=200)


# ==============================================================================
# 3. PWA & WEB PUSH ENDPOINTS
# ==============================================================================

def manifest_view(request):
    """Retorna o manifesto PWA da Delacruz Barber."""
    manifest = {
        "name": "Delacruz Barber - Barbearia Premium",
        "short_name": "Delacruz Barber",
        "description": "Agendamentos, Barber Club e gestão para a barbearia Delacruz Barber.",
        "start_url": "/",
        "display": "standalone",
        "theme_color": "#020617",
        "background_color": "#020617",
        "icons": [
            {
                "src": "/static/website/img/icon-192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/website/img/icon-512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }
    return JsonResponse(manifest, content_type="application/manifest+json")


def service_worker_view(request):
    """Retorna o script Service Worker para cache seguro de assets públicos."""
    sw_code = """
    const CACHE_NAME = 'delacruz-cache-v1';
    const STATIC_ASSETS = [
      '/',
      '/servicos/',
      '/barbeiros/',
      '/sobre/',
      '/static/website/css/style.css',
      '/static/website/js/main.js',
      'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
      'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css'
    ];

    self.addEventListener('install', (e) => {
      e.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
      );
      self.skipWaiting();
    });

    self.addEventListener('activate', (e) => {
      e.waitUntil(
        caches.keys().then((keys) => {
          return Promise.all(
            keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
          );
        })
      );
      self.clients.claim();
    });

    self.addEventListener('fetch', (e) => {
      // Ignora requisições de pagamento, autenticação e POST
      if (e.request.method !== 'GET' || e.request.url.includes('/login/') || e.request.url.includes('/api/')) {
        return;
      }
      e.respondWith(
        fetch(e.request).catch(() => caches.match(e.request))
      );
    });
    """
    return HttpResponse(sw_code, content_type="application/javascript")


@csrf_exempt
def push_subscription_api(request):
    """Registra subscrição de Web Push para o usuário logado."""
    if not request.user.is_authenticated or request.method != 'POST':
        return JsonResponse({'status': 'unauthorized'}, status=401)

    try:
        data = json.loads(request.body.decode('utf-8'))
        PushSubscription.objects.update_or_create(
            usuario=request.user,
            endpoint=data.get('endpoint'),
            defaults={
                'p256dh': data.get('keys', {}).get('p256dh', ''),
                'auth': data.get('keys', {}).get('auth', ''),
            }
        )
        return JsonResponse({'status': 'subscribed'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# ==============================================================================
# 4. AUTH & REGISTRO
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

        user = User.objects.create_user(
            username=username,
            email=email,
            password=senha,
            first_name=nome,
            last_name=sobrenome
        )
        PerfilUsuario.objects.create(
            usuario=user,
            tipo_usuario='cliente',
            telefone=telefone
        )

        cliente = Cliente.objects.filter(email=email).first()
        if cliente:
            cliente.usuario = user
            cliente.nome = f"{nome} {sobrenome}".strip()
            cliente.telefone = telefone
            cliente.save()
        else:
            Cliente.objects.create(
                usuario=user,
                nome=f"{nome} {sobrenome}".strip(),
                email=email,
                telefone=telefone
            )

        login(self.request, user)
        messages.success(self.request, f'Bem-vindo à Delacruz Barber, {nome}! Sua conta foi criada com sucesso.')
        return redirect('area_cliente')


# ==============================================================================
# 5. ÁREA DO CLIENTE (PORTAL COMPLETO)
# ==============================================================================

class AreaClienteView(LoginRequiredMixin, TemplateView):
    template_name = 'website/cliente/area_cliente.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        cliente, _ = Cliente.objects.get_or_create(
            usuario=user,
            defaults={
                'nome': f"{user.first_name} {user.last_name}".strip() or user.username,
                'email': user.email,
                'telefone': getattr(getattr(user, 'perfil', None), 'telefone', '')
            }
        )
        context['cliente'] = cliente
        
        # Formulário de perfil
        initial_data = {
            'nome': user.first_name,
            'sobrenome': user.last_name,
            'email': user.email,
            'telefone': getattr(user.perfil, 'telefone', '') if hasattr(user, 'perfil') else ''
        }
        context['profile_form'] = PerfilUpdateForm(initial=initial_data)
        
        # Agendamentos
        agendamentos = Agendamento.objects.filter(cliente=cliente)
        context['proximos'] = agendamentos.filter(
            status__in=[Agendamento.Status.PENDENTE, Agendamento.Status.CONFIRMADO, Agendamento.Status.EM_ATENDIMENTO],
            data__gte=date.today()
        ).order_by('data', 'horario')
        
        concluidos = agendamentos.filter(status=Agendamento.Status.CONCLUIDO).order_by('-data', '-horario')
        context['historico'] = concluidos[:5]
        context['ultimo_servico'] = concluidos.first()

        # Barber Club
        context['club'] = SubscriptionService.get_resumo_cliente(cliente)
        
        # Fidelidade Digital
        context['fidelidade'] = LoyaltyService.get_resumo_cliente(cliente)

        # Última Análise de Estilo
        context['ultima_analise'] = AnaliseEstilo.objects.filter(cliente=cliente).first()

        # Fotos de Evolução Privadas
        context['fotos_evolucao'] = HistoricoVisualCliente.objects.filter(cliente=cliente).order_by('-data')[:4]

        # Lista de Espera ativa
        context['waitlist_ativas'] = ListaEspera.objects.filter(
            cliente=cliente,
            status__in=[ListaEspera.Status.AGUARDANDO, ListaEspera.Status.NOTIFICADO]
        )

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
                cliente.nome = f"{user.first_name} {user.last_name}".strip()
                cliente.email = user.email
                cliente.telefone = form.cleaned_data['telefone']
                cliente.save()
                
            messages.success(request, 'Perfil atualizado com sucesso!')
        else:
            messages.error(request, 'Erro ao atualizar perfil. Verifique os campos.')
            
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
            cliente.nome = f"{user.first_name} {user.last_name}".strip()
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
        context['agendamento'] = get_object_or_404(Agendamento, pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        agendamento = get_object_or_404(Agendamento, pk=self.kwargs['pk'])
        cliente = Cliente.objects.filter(usuario=self.request.user).first()

        if agendamento.cliente != cliente:
            messages.error(self.request, 'Você não tem permissão para avaliar este agendamento.')
            return redirect('area_cliente')
        
        if agendamento.status != Agendamento.Status.CONCLUIDO:
            messages.error(self.request, 'Apenas agendamentos concluídos podem ser avaliados.')
            return redirect('area_cliente')

        if Feedback.objects.filter(agendamento=agendamento).exists():
            messages.error(self.request, 'Você já enviou avaliação para este atendimento.')
            return redirect('area_cliente')

        form.instance.usuario = self.request.user
        form.instance.cliente = cliente
        form.instance.barbeiro = agendamento.barbeiro
        form.instance.agendamento = agendamento
        form.instance.aprovado = True

        messages.success(self.request, 'Agradecemos pelo seu feedback! Ele nos ajuda a manter a excelência.')
        return super().form_valid(form)


class CancelarAgendamentoClienteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        cliente = Cliente.objects.filter(usuario=request.user).first()
        agendamento = get_object_or_404(Agendamento, pk=pk)

        if agendamento.cliente != cliente:
            messages.error(request, 'Acesso negado para cancelar este agendamento.')
            return redirect('area_cliente')

        if agendamento.status in [Agendamento.Status.PENDENTE, Agendamento.Status.CONFIRMADO]:
            AgendamentoService.cancelar_atendimento(agendamento, motivo="Cancelado pelo próprio cliente na Área do Cliente")
            messages.success(request, 'Agendamento cancelado com sucesso. Se havia créditos, eles foram estornados.')
        else:
            messages.error(request, 'Não é possível cancelar agendamentos já em atendimento ou concluídos.')

        return redirect('area_cliente')


class ClienteClubView(LoginRequiredMixin, TemplateView):
    """Painel do Barber Club / Delacruz Prime para o cliente."""
    template_name = 'website/cliente/club.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente = Cliente.objects.filter(usuario=self.request.user).first()
        context['planos'] = PlanoAssinatura.objects.filter(ativo=True).order_by('preco_mensal')
        context['club'] = SubscriptionService.get_resumo_cliente(cliente) if cliente else None
        
        if cliente and context['club']:
            context['movimentacoes'] = MovimentacaoCredito.objects.filter(
                assinatura=context['club']['assinatura']
            ).order_by('-criado_em')[:15]
        return context

    def post(self, request, *args, **kwargs):
        """Assinar ou trocar de plano."""
        plano_id = request.POST.get('plano_id')
        plano = get_object_or_404(PlanoAssinatura, pk=plano_id, ativo=True)
        cliente = get_object_or_404(Cliente, usuario=request.user)

        SubscriptionService.ativar_ou_renovar_assinatura(cliente, plano)
        messages.success(request, f'Parabéns! Sua assinatura do {plano.nome} foi ativada com sucesso (+{plano.quantidade_creditos} créditos liberados).')
        return redirect('cliente_club')


class ClienteFidelidadeView(LoginRequiredMixin, TemplateView):
    """Painel de Fidelidade Digital para o cliente."""
    template_name = 'website/cliente/fidelidade.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente = Cliente.objects.filter(usuario=self.request.user).first()
        context['fidelidade'] = LoyaltyService.get_resumo_cliente(cliente) if cliente else None
        context['recompensas_historico'] = RecompensaFidelidade.objects.filter(cliente=cliente).order_by('-data_gerada') if cliente else []
        return context


class ClienteEstiloView(LoginRequiredMixin, FormView):
    """Consultor de Estilo & Visagismo com IA."""
    template_name = 'website/cliente/estilo.html'
    form_class = AnaliseEstiloForm
    success_url = reverse_lazy('cliente_estilo')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente = Cliente.objects.filter(usuario=self.request.user).first()
        context['analises'] = AnaliseEstilo.objects.filter(cliente=cliente).order_by('-criado_em') if cliente else []
        context['catalogo_cortes'] = EstiloCorte.objects.filter(ativo=True)
        return context

    def form_valid(self, form):
        cliente = get_object_or_404(Cliente, usuario=self.request.user)
        imagem_file = form.cleaned_data['imagem']
        try:
            analise = StyleAIService.analisar_rosto_e_recomendar(cliente, imagem_file)
            messages.success(self.request, f'Análise de visagismo concluída! Seu formato facial identificado é {analise.formato_rosto_detectado}. Veja as recomendações abaixo.')
        except Exception as e:
            messages.error(self.request, f'Erro na análise: {str(e)}')
        return redirect('cliente_estilo')


class ClienteEvolucaoView(LoginRequiredMixin, ListView):
    """Galeria privada com o histórico cronológico de evolução visual do cliente."""
    model = HistoricoVisualCliente
    template_name = 'website/cliente/evolucao.html'
    context_object_name = 'fotos_evolucao'

    def get_queryset(self):
        cliente = Cliente.objects.filter(usuario=self.request.user).first()
        if not cliente:
            return HistoricoVisualCliente.objects.none()
        return HistoricoVisualCliente.objects.filter(cliente=cliente).order_by('-data')


class ClienteWaitlistView(LoginRequiredMixin, FormView):
    """Inscrição em lista de espera para datas ou horários cheios."""
    template_name = 'website/cliente/waitlist.html'
    form_class = ListaEsperaForm
    success_url = reverse_lazy('cliente_waitlist')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente = Cliente.objects.filter(usuario=self.request.user).first()
        context['entradas_waitlist'] = ListaEspera.objects.filter(cliente=cliente).order_by('-criado_em') if cliente else []
        return context

    def form_valid(self, form):
        cliente = get_object_or_404(Cliente, usuario=self.request.user)
        lista = form.save(commit=False)
        lista.cliente = cliente
        lista.status = ListaEspera.Status.AGUARDANDO
        lista.save()
        messages.success(self.request, 'Você está na Lista de Espera! Se houver desistência ou vaga livre nessa faixa de horário, você será notificado.')
        return redirect('cliente_waitlist')


class CancelarWaitlistView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        cliente = Cliente.objects.filter(usuario=request.user).first()
        item = get_object_or_404(ListaEspera, pk=pk, cliente=cliente)
        item.status = ListaEspera.Status.CANCELADO
        item.save(update_fields=['status'])
        messages.success(request, 'Entrada na lista de espera cancelada.')
        return redirect('cliente_waitlist')


# ==============================================================================
# 6. ÁREA DO BARBEIRO (PAINEL PROFISSIONAL COMPLETO)
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
        
        # Perfil
        initial_data = {
            'nome': user.first_name,
            'sobrenome': user.last_name,
            'email': user.email,
            'telefone': getattr(user.perfil, 'telefone', '') if hasattr(user, 'perfil') else ''
        }
        context['profile_form'] = PerfilUpdateForm(initial=initial_data)

        if barbeiro:
            hoje = date.today()
            agendamentos = Agendamento.objects.filter(barbeiro=barbeiro).select_related('cliente', 'servico', 'barbeiro')
            
            # QuerySet base sem slice
            proximos_base_qs = agendamentos.filter(
                status__in=[Agendamento.Status.PENDENTE, Agendamento.Status.CONFIRMADO, Agendamento.Status.EM_ATENDIMENTO],
                data__gte=hoje
            ).order_by('data', 'horario')

            # Atendimento atual (em andamento)
            context['atendimento_atual'] = proximos_base_qs.filter(status=Agendamento.Status.EM_ATENDIMENTO).first()

            # Slice aplicado somente no final para a listagem
            proximos_lista = list(proximos_base_qs[:10])
            for item in proximos_lista:
                msg = WhatsAppService.gerar_mensagem_barbeiro_chamar(item)
                item.whatsapp_link = WhatsAppService.gerar_link_click_to_chat(item.cliente.telefone, msg)

            context['proximos'] = proximos_lista
            context['proximos_agendamentos'] = proximos_lista

            # Extrato e Comissões
            extrato = ComissaoService.get_extrato_barbeiro(barbeiro, data_inicio=hoje - timedelta(days=30), data_fim=hoje)
            context['extrato'] = extrato
            context['comissao_hoje'] = Comissao.objects.filter(barbeiro=barbeiro, criado_em__date=hoje).aggregate(total=Sum('valor_comissao'))['total'] or Decimal('0.00')

            # Meta Mensal
            context['meta_info'] = ComissaoService.get_progresso_meta(barbeiro)
            
            # Feedbacks & Fotos
            context['feedbacks'] = Feedback.objects.filter(barbeiro=barbeiro).order_by('-criado_em')[:5]
            context['fotos'] = FotoTrabalho.objects.filter(barbeiro=barbeiro).order_by('-criado_em')[:6]
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
                barbeiro.nome = f"{user.first_name} {user.last_name}".strip()
                barbeiro.save()
                
            messages.success(request, 'Perfil atualizado com sucesso!')
        else:
            messages.error(request, 'Erro ao atualizar perfil.')
        return redirect('area_barbeiro')


class AgendamentosBarbeiroView(BarbeiroRequiredMixin, ListView):
    model = Agendamento
    template_name = 'website/barbeiro/agendamentos_barbeiro.html'
    context_object_name = 'agendamentos'

    def get_queryset(self):
        barbeiro = Barbeiro.objects.filter(usuario=self.request.user).first()
        if not barbeiro:
            if self.request.user.is_superuser or self.request.user.is_staff:
                barbeiro = Barbeiro.objects.first()
            else:
                return Agendamento.objects.none()
        return Agendamento.objects.filter(barbeiro=barbeiro).order_by('-data', '-horario')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for item in context['agendamentos']:
            msg = WhatsAppService.gerar_mensagem_barbeiro_chamar(item)
            item.whatsapp_link = WhatsAppService.gerar_link_click_to_chat(item.cliente.telefone, msg)
        return context

    def post(self, request, *args, **kwargs):
        agendamento_id = request.POST.get('agendamento_id')
        novo_status = request.POST.get('status')
        
        agendamento = get_object_or_404(Agendamento, pk=agendamento_id)
        barbeiro = Barbeiro.objects.filter(usuario=request.user).first()
        
        if not (request.user.is_superuser or request.user.is_staff) and agendamento.barbeiro != barbeiro:
            messages.error(request, 'Permissão negada para alterar este agendamento.')
            return redirect('agendamentos_barbeiro')
            
        if novo_status == Agendamento.Status.CONCLUIDO:
            AgendamentoService.concluir_atendimento(agendamento, usuario_responsavel=request.user)
            messages.success(request, f'Atendimento #{agendamento.id} finalizado! Comissões e fidelidade computadas.')
        elif novo_status == Agendamento.Status.CANCELADO:
            AgendamentoService.cancelar_atendimento(agendamento, motivo="Cancelado pelo barbeiro")
            messages.warning(request, f'Agendamento #{agendamento.id} cancelado.')
        elif novo_status in [Agendamento.Status.CONFIRMADO, Agendamento.Status.EM_ATENDIMENTO, Agendamento.Status.NAO_COMPARECEU]:
            agendamento.status = novo_status
            agendamento.save(update_fields=['status', 'atualizado_em'])
            messages.success(request, f'Status do agendamento atualizado para {novo_status}.')
        else:
            messages.error(request, 'Status inválido.')
            
        return redirect('agendamentos_barbeiro')


class BarbeiroComandaView(BarbeiroRequiredMixin, TemplateView):
    """Gerenciamento de Comanda / PDV do atendimento pelo barbeiro."""
    template_name = 'website/barbeiro/comanda_atendimento.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        agendamento = get_object_or_404(Agendamento, pk=self.kwargs['pk'])
        comanda, _ = Comanda.objects.get_or_create(
            agendamento=agendamento,
            defaults={
                'cliente': agendamento.cliente,
                'barbeiro': agendamento.barbeiro,
                'subtotal': agendamento.servico.preco,
                'valor_total': agendamento.servico.preco,
                'status': Comanda.Status.ABERTA
            }
        )
        # Garante item de serviço na comanda
        if not comanda.itens.filter(tipo=ItemComanda.Tipo.SERVICO).exists():
            ItemComanda.objects.create(
                comanda=comanda,
                tipo=ItemComanda.Tipo.SERVICO,
                servico=agendamento.servico,
                descricao=agendamento.servico.nome,
                quantidade=1,
                preco_unitario=agendamento.servico.preco,
                total=agendamento.servico.preco
            )
            comanda.recalcular()

        context['agendamento'] = agendamento
        context['comanda'] = comanda
        context['produtos_disponiveis'] = Produto.objects.filter(ativo=True, estoque_atual__gt=0)
        context['servicos_adicionais'] = Servico.objects.filter(ativo=True).exclude(pk=agendamento.servico.pk)
        return context

    def post(self, request, *args, **kwargs):
        agendamento = get_object_or_404(Agendamento, pk=self.kwargs['pk'])
        comanda = get_object_or_404(Comanda, agendamento=agendamento)
        acao = request.POST.get('acao')

        if acao == 'adicionar_produto':
            produto_id = request.POST.get('produto_id')
            qtd = int(request.POST.get('quantidade', 1))
            produto = get_object_or_404(Produto, pk=produto_id)
            ItemComanda.objects.create(
                comanda=comanda,
                tipo=ItemComanda.Tipo.PRODUTO,
                produto=produto,
                descricao=produto.nome,
                quantidade=qtd,
                preco_unitario=produto.preco,
                total=produto.preco * qtd
            )
            comanda.recalcular()
            messages.success(request, f'{produto.nome} adicionado à comanda!')

        elif acao == 'adicionar_servico':
            servico_id = request.POST.get('servico_id')
            servico = get_object_or_404(Servico, pk=servico_id)
            ItemComanda.objects.create(
                comanda=comanda,
                tipo=ItemComanda.Tipo.ADICIONAL,
                servico=servico,
                descricao=f"+ {servico.nome}",
                quantidade=1,
                preco_unitario=servico.preco,
                total=servico.preco
            )
            comanda.recalcular()
            messages.success(request, f'Serviço extra {servico.nome} adicionado!')

        elif acao == 'remover_item':
            item_id = request.POST.get('item_id')
            item = get_object_or_404(ItemComanda, pk=item_id, comanda=comanda)
            item.delete()
            comanda.recalcular()
            messages.info(request, 'Item removido da comanda.')

        elif acao == 'aplicar_cupom':
            codigo_cupom = request.POST.get('codigo_cupom', '').strip().upper()
            try:
                cupom = CupomDesconto.objects.get(codigo__iexact=codigo_cupom)
                valido, msg = cupom.is_valido(comanda.subtotal)
                if valido:
                    desconto, _ = cupom.calcular_desconto(comanda.subtotal)
                    comanda.desconto = Decimal(str(desconto))
                    comanda.recalcular()
                    cupom.usos_atuais += 1
                    cupom.save(update_fields=['usos_atuais'])
                    messages.success(request, f"Cupom {cupom.codigo} aplicado! Desconto de R$ {desconto:.2f}.")
                else:
                    messages.error(request, msg)
            except CupomDesconto.DoesNotExist:
                messages.error(request, "Cupom promocional não encontrado.")

        elif acao == 'finalizar_comanda':
            AgendamentoService.concluir_atendimento(agendamento, comanda=comanda, usuario_responsavel=request.user)
            messages.success(request, f'Atendimento e Comanda #{comanda.id} concluídos com sucesso!')
            return redirect('agendamentos_barbeiro')

        return redirect('barbeiro_comanda', pk=agendamento.pk)


class BarbeiroFotoResultadoView(BarbeiroRequiredMixin, CreateView):
    """Anexa foto do resultado ao histórico visual privado do cliente."""
    model = HistoricoVisualCliente
    form_class = HistoricoVisualClienteForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('agendamentos_barbeiro')
    extra_context = {'titulo': 'Registrar Foto do Resultado (Privado)', 'botao': 'Salvar Foto de Evolução'}

    def get_initial(self):
        agendamento = get_object_or_404(Agendamento, pk=self.kwargs['pk'])
        barbeiro = Barbeiro.objects.filter(usuario=self.request.user).first() or agendamento.barbeiro
        return {
            'agendamento': agendamento,
            'cliente': agendamento.cliente,
            'barbeiro': barbeiro,
            'consentimento': True,
        }

    def form_valid(self, form):
        form.instance.data = date.today()
        messages.success(self.request, 'Foto do resultado salva no histórico privado do cliente!')
        return super().form_valid(form)


class HistoricoBarbeiroView(BarbeiroRequiredMixin, ListView):
    model = Agendamento
    template_name = 'website/barbeiro/historico_barbeiro.html'
    context_object_name = 'agendamentos'

    def get_queryset(self):
        barbeiro = Barbeiro.objects.filter(usuario=self.request.user).first()
        if not barbeiro:
            return Agendamento.objects.none()
        return Agendamento.objects.filter(barbeiro=barbeiro, status=Agendamento.Status.CONCLUIDO).order_by('-data', '-horario')


class BarbeiroGanhosView(BarbeiroRequiredMixin, TemplateView):
    """Extrato detalhado de comissões e ganhos do barbeiro."""
    template_name = 'website/barbeiro/ganhos.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        barbeiro = Barbeiro.objects.filter(usuario=self.request.user).first()
        if not barbeiro and (self.request.user.is_superuser or self.request.user.is_staff):
            barbeiro = Barbeiro.objects.first()

        periodo = self.request.GET.get('periodo', '30_dias')
        hoje = date.today()

        if periodo == 'hoje':
            inicio = hoje
        elif periodo == 'semana':
            inicio = hoje - timedelta(days=7)
        elif periodo == 'mes':
            inicio = hoje.replace(day=1)
        else:
            inicio = hoje - timedelta(days=30)

        context['barbeiro'] = barbeiro
        context['periodo_selecionado'] = periodo
        context['extrato'] = ComissaoService.get_extrato_barbeiro(barbeiro, data_inicio=inicio, data_fim=hoje) if barbeiro else None
        return context


class BarbeiroMetasView(BarbeiroRequiredMixin, TemplateView):
    """Painel de metas e performance do barbeiro."""
    template_name = 'website/barbeiro/metas.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        barbeiro = Barbeiro.objects.filter(usuario=self.request.user).first()
        if not barbeiro and (self.request.user.is_superuser or self.request.user.is_staff):
            barbeiro = Barbeiro.objects.first()
        context['barbeiro'] = barbeiro
        context['meta_info'] = ComissaoService.get_progresso_meta(barbeiro) if barbeiro else None
        return context


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
        
        agendamentos = Agendamento.objects.filter(barbeiro=barbeiro, status=Agendamento.Status.CONCLUIDO)
        
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
        messages.success(self.request, 'Foto cadastrada com sucesso no portfólio!')
        return super().form_valid(form)


class FotoTrabalhoUpdateView(BarbeiroRequiredMixin, UpdateView):
    model = FotoTrabalho
    form_class = FotoTrabalhoForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('fotos_barbeiro')
    extra_context = {'titulo': 'Editar Foto de Trabalho', 'botao': 'Salvar Alterações'}

    def get_queryset(self):
        return FotoTrabalho.objects.filter(usuario=self.request.user)


class FotoTrabalhoDeleteView(BarbeiroRequiredMixin, DeleteView):
    model = FotoTrabalho
    template_name = 'website/form.html'
    success_url = reverse_lazy('fotos_barbeiro')
    extra_context = {'titulo': 'Excluir Foto de Trabalho', 'botao': 'Excluir Foto'}

    def get_queryset(self):
        return FotoTrabalho.objects.filter(usuario=self.request.user)


# ==============================================================================
# 7. DASHBOARD & GESTÃO ADMINISTRATIVA
# ==============================================================================

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'website/dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        user = request.user
        if user.is_superuser or user.is_staff:
            return super().dispatch(request, *args, **kwargs)
            
        perfil = getattr(user, 'perfil', None)
        if perfil and perfil.tipo_usuario.lower() == 'administrador':
            return super().dispatch(request, *args, **kwargs)
            
        if (perfil and perfil.tipo_usuario.lower() == 'barbeiro') or Barbeiro.objects.filter(usuario=user).exists():
            return redirect('area_barbeiro')
            
        return redirect('area_cliente')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoje = date.today()
        mes_atual = hoje.month
        ano_atual = hoje.year

        agendamentos_hoje = Agendamento.objects.filter(data=hoje)
        concluidos_hoje = agendamentos_hoje.filter(status=Agendamento.Status.CONCLUIDO)
        concluidos_mes = Agendamento.objects.filter(data__month=mes_atual, data__year=ano_atual, status=Agendamento.Status.CONCLUIDO)

        # Faturamento Real via Comandas Fechadas / Agendamentos Concluídos
        faturamento_hoje = Comanda.objects.filter(fechada_em__date=hoje, status=Comanda.Status.FECHADA).aggregate(total=Sum('valor_total'))['total']
        if faturamento_hoje is None:
            faturamento_hoje = concluidos_hoje.aggregate(total=Sum('servico__preco'))['total'] or Decimal('0.00')

        faturamento_mes = Comanda.objects.filter(fechada_em__month=mes_atual, fechada_em__year=ano_atual, status=Comanda.Status.FECHADA).aggregate(total=Sum('valor_total'))['total']
        if faturamento_mes is None:
            faturamento_mes = concluidos_mes.aggregate(total=Sum('servico__preco'))['total'] or Decimal('0.00')

        total_atendimentos_mes = concluidos_mes.count()
        ticket_medio = (faturamento_mes / total_atendimentos_mes) if total_atendimentos_mes > 0 else Decimal('0.00')

        no_shows = Agendamento.objects.filter(data__month=mes_atual, data__year=ano_atual, status=Agendamento.Status.NAO_COMPARECEU).count()
        total_geral_mes = Agendamento.objects.filter(data__month=mes_atual, data__year=ano_atual).count()
        taxa_no_show = round((no_shows / total_geral_mes * 100), 1) if total_geral_mes > 0 else 0

        context['hoje'] = hoje
        context['total_hoje'] = agendamentos_hoje.count()
        context['pendentes'] = agendamentos_hoje.filter(status=Agendamento.Status.PENDENTE).count()
        context['confirmados'] = agendamentos_hoje.filter(status=Agendamento.Status.CONFIRMADO).count()
        context['concluidos'] = concluidos_hoje.count()
        context['faturamento_hoje'] = faturamento_hoje
        context['faturamento_mes'] = faturamento_mes
        context['ticket_medio'] = round(ticket_medio, 2)
        context['taxa_no_show'] = taxa_no_show
        context['assinantes_ativos'] = AssinaturaCliente.objects.filter(status=AssinaturaCliente.Status.ATIVA).count()
        context['produtos_baixo_estoque'] = Produto.objects.filter(ativo=True, estoque_atual__lte=F('estoque_minimo'))
        context['ultimos_agendamentos'] = Agendamento.objects.all().order_by('-data', '-horario')[:8]
        context['total_clientes'] = Cliente.objects.count()
        context['mensagens_nao_lidas'] = MensagemContato.objects.filter(lida=False).count()

        # Ranking de Barbeiros no mês
        context['top_barbeiros'] = (
            concluidos_mes.values('barbeiro__nome')
            .annotate(cortes=Count('id'), total_valor=Sum('servico__preco'))
            .order_by('-cortes')[:5]
        )

        return context


class FinanceiroAdminView(AdminStaffRequiredMixin, TemplateView):
    """Visão financeira executiva da barbearia."""
    template_name = 'website/admin/financeiro.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoje = date.today()
        mes = int(self.request.GET.get('mes', hoje.month))
        ano = int(self.request.GET.get('ano', hoje.year))

        comandas = Comanda.objects.filter(fechada_em__month=mes, fechada_em__year=ano, status=Comanda.Status.FECHADA)
        comissoes = Comissao.objects.filter(criado_em__month=mes, criado_em__year=ano)

        faturamento_bruto = comandas.aggregate(total=Sum('subtotal'))['total'] or Decimal('0.00')
        faturamento_liquido = comandas.aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')
        total_comissoes = comissoes.aggregate(total=Sum('valor_comissao'))['total'] or Decimal('0.00')
        lucro_estimado = max(Decimal('0.00'), faturamento_liquido - total_comissoes)

        context['mes'] = mes
        context['ano'] = ano
        context['faturamento_bruto'] = faturamento_bruto
        context['faturamento_liquido'] = faturamento_liquido
        context['total_comissoes'] = total_comissoes
        context['lucro_estimado'] = lucro_estimado
        context['ultimas_comandas'] = comandas.order_by('-fechada_em')[:20]
        context['repasses_pendentes'] = Comissao.objects.filter(status=Comissao.Status.PENDENTE).aggregate(total=Sum('valor_comissao'))['total'] or Decimal('0.00')
        return context


class ComissoesAdminView(AdminStaffRequiredMixin, TemplateView):
    """Gestão de comissões por barbeiro e repasses."""
    template_name = 'website/admin/comissoes.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        barbeiros = Barbeiro.objects.filter(ativo=True)
        resumo_barbeiros = []
        for b in barbeiros:
            extrato = ComissaoService.get_extrato_barbeiro(b)
            resumo_barbeiros.append({
                'barbeiro': b,
                'total_comissao': extrato['total_comissao'],
                'total_repasses': extrato['total_repasses'],
                'saldo_a_receber': extrato['saldo_a_receber'],
            })
        context['barbeiros_resumo'] = resumo_barbeiros
        context['ultimos_repasses'] = RepasseComissao.objects.all().order_by('-data_repasse')[:15]
        return context


class RepasseComissaoCreateView(AdminStaffRequiredMixin, CreateView):
    model = RepasseComissao
    form_class = RepasseComissaoForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('admin_comissoes')
    extra_context = {'titulo': 'Registrar Repasse de Comissão', 'botao': 'Confirmar Repasse'}

    def form_valid(self, form):
        form.instance.usuario_responsavel = self.request.user
        messages.success(self.request, f'Repasse de R$ {form.instance.valor} para {form.instance.barbeiro.nome} registrado com sucesso!')
        return super().form_valid(form)


# --- PRODUTOS E ESTOQUE CRUD ---

class ProdutoListView(AdminStaffRequiredMixin, ListView):
    model = Produto
    template_name = 'website/listas/produtos.html'
    context_object_name = 'produtos'

    def get_queryset(self):
        return Produto.objects.all().order_by('nome')


class ProdutoCreate(AdminStaffRequiredMixin, CreateView):
    model = Produto
    form_class = ProdutoForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_produtos')
    extra_context = {'titulo': 'Cadastrar Produto', 'botao': 'Salvar Produto'}


class ProdutoUpdate(AdminStaffRequiredMixin, UpdateView):
    model = Produto
    form_class = ProdutoForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_produtos')
    extra_context = {'titulo': 'Editar Produto', 'botao': 'Salvar Alterações'}


class ProdutoDelete(AdminStaffRequiredMixin, DeleteView):
    model = Produto
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_produtos')
    extra_context = {'titulo': 'Excluir Produto', 'botao': 'Excluir Produto'}


class EstoqueMovimentacaoView(AdminStaffRequiredMixin, FormView):
    template_name = 'website/admin/estoque.html'
    form_class = MovimentacaoEstoqueForm
    success_url = reverse_lazy('admin_estoque')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['produtos'] = Produto.objects.all().order_by('nome')
        context['produtos_baixo_estoque'] = Produto.objects.filter(ativo=True, estoque_atual__lte=F('estoque_minimo'))
        context['ultimas_movimentacoes'] = MovimentacaoEstoque.objects.all().order_by('-criado_em')[:25]
        return context

    def form_valid(self, form):
        produto = form.cleaned_data['produto']
        tipo = form.cleaned_data['tipo']
        quantidade = form.cleaned_data['quantidade']
        motivo = form.cleaned_data['motivo']
        try:
            InventoryService.movimentar_estoque(
                produto=produto,
                tipo=tipo,
                quantidade=quantidade,
                motivo=motivo,
                usuario=self.request.user
            )
            messages.success(self.request, f'Movimentação de {quantidade} ({tipo}) no produto {produto.nome} realizada com sucesso!')
        except Exception as e:
            messages.error(self.request, f'Erro na movimentação: {str(e)}')
        return redirect('admin_estoque')


# --- ASSINATURAS & CONFIGURAÇÕES CRUD ---

class PlanoAssinaturaListView(AdminStaffRequiredMixin, ListView):
    model = PlanoAssinatura
    template_name = 'website/listas/planos.html'
    context_object_name = 'planos'


class PlanoAssinaturaCreate(AdminStaffRequiredMixin, CreateView):
    model = PlanoAssinatura
    form_class = PlanoAssinaturaForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_planos')
    extra_context = {'titulo': 'Cadastrar Plano Barber Club', 'botao': 'Salvar Plano'}


class PlanoAssinaturaUpdate(AdminStaffRequiredMixin, UpdateView):
    model = PlanoAssinatura
    form_class = PlanoAssinaturaForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_planos')
    extra_context = {'titulo': 'Editar Plano Barber Club', 'botao': 'Salvar Alterações'}


class PlanoAssinaturaDelete(AdminStaffRequiredMixin, DeleteView):
    model = PlanoAssinatura
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_planos')
    extra_context = {'titulo': 'Excluir Plano Barber Club', 'botao': 'Excluir'}


class ConfiguracaoEstabelecimentoView(AdminStaffRequiredMixin, UpdateView):
    model = ConfiguracaoEstabelecimento
    form_class = ConfiguracaoEstabelecimentoForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('dashboard')
    extra_context = {'titulo': 'Configurações da Barbearia & Regras de PIX / Sinal', 'botao': 'Salvar Configurações'}

    def get_object(self, queryset=None):
        return ConfiguracaoEstabelecimento.get_solo()

    def form_valid(self, form):
        messages.success(self.request, 'Configurações da Delacruz Barber salvas com sucesso!')
        return super().form_valid(form)


class WaitlistAdminView(AdminStaffRequiredMixin, ListView):
    model = ListaEspera
    template_name = 'website/admin/waitlist.html'
    context_object_name = 'waitlist'
    queryset = ListaEspera.objects.all().order_by('-data_desejada')


# --- CRUDS EXISTENTES (PRESERVADOS) ---

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


class ServicoDelete(LoginRequiredMixin, AdminStaffRequiredMixin, DeleteView):
    model = Servico
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_servicos')
    extra_context = {'titulo': 'Excluir Serviço', 'botao': 'Excluir'}


class ServicoList(LoginRequiredMixin, AdminStaffRequiredMixin, ListView):
    model = Servico
    template_name = 'website/listas/servicos.html'
    context_object_name = 'servicos'


class ServicoDetail(LoginRequiredMixin, AdminStaffRequiredMixin, DetailView):
    model = Servico
    template_name = 'website/ver/servico.html'
    context_object_name = 'servico'


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


class BarbeiroList(AdminRequiredMixin, ListView):
    model = Barbeiro
    template_name = 'website/listas/barbeiros.html'
    context_object_name = 'barbeiros'


class BarbeiroDetail(AdminRequiredMixin, DetailView):
    model = Barbeiro
    template_name = 'website/ver/barbeiro.html'
    context_object_name = 'barbeiro'


class ClienteCreate(LoginRequiredMixin, AdminStaffRequiredMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_clientes')
    extra_context = {'titulo': 'Cadastrar Cliente', 'botao': 'Cadastrar'}


class ClienteUpdate(LoginRequiredMixin, AdminStaffRequiredMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_clientes')
    extra_context = {'titulo': 'Editar Cliente', 'botao': 'Salvar alterações'}


class ClienteDelete(LoginRequiredMixin, AdminStaffRequiredMixin, DeleteView):
    model = Cliente
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_clientes')
    extra_context = {'titulo': 'Excluir Cliente', 'botao': 'Excluir'}


class ClienteList(LoginRequiredMixin, AdminStaffRequiredMixin, ListView):
    model = Cliente
    template_name = 'website/listas/clientes.html'
    context_object_name = 'clientes'


class ClienteDetail(LoginRequiredMixin, AdminStaffRequiredMixin, DetailView):
    model = Cliente
    template_name = 'website/ver/cliente.html'
    context_object_name = 'cliente'


class HorarioDisponivelCreate(LoginRequiredMixin, AdminStaffRequiredMixin, CreateView):
    model = HorarioDisponivel
    form_class = HorarioDisponivelForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_horarios')
    extra_context = {'titulo': 'Cadastrar Horário', 'botao': 'Cadastrar'}


class HorarioDisponivelUpdate(LoginRequiredMixin, AdminStaffRequiredMixin, UpdateView):
    model = HorarioDisponivel
    form_class = HorarioDisponivelForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_horarios')
    extra_context = {'titulo': 'Editar Horário', 'botao': 'Salvar alterações'}


class HorarioDisponivelDelete(LoginRequiredMixin, AdminStaffRequiredMixin, DeleteView):
    model = HorarioDisponivel
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_horarios')
    extra_context = {'titulo': 'Excluir Horário', 'botao': 'Excluir'}


class HorarioDisponivelList(LoginRequiredMixin, AdminStaffRequiredMixin, ListView):
    model = HorarioDisponivel
    template_name = 'website/listas/horarios.html'
    context_object_name = 'horarios'


class HorarioDisponivelDetail(LoginRequiredMixin, AdminStaffRequiredMixin, DetailView):
    model = HorarioDisponivel
    template_name = 'website/ver/horario.html'
    context_object_name = 'horario'


class AgendamentoCreate(LoginRequiredMixin, AdminStaffRequiredMixin, CreateView):
    model = Agendamento
    form_class = AgendamentoForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_agendamentos')
    extra_context = {'titulo': 'Cadastrar Agendamento', 'botao': 'Cadastrar'}


class AgendamentoUpdate(LoginRequiredMixin, AdminStaffRequiredMixin, UpdateView):
    model = Agendamento
    form_class = AgendamentoForm
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_agendamentos')
    extra_context = {'titulo': 'Editar Agendamento', 'botao': 'Salvar alterações'}


class AgendamentoDelete(LoginRequiredMixin, AdminStaffRequiredMixin, DeleteView):
    model = Agendamento
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_agendamentos')
    extra_context = {'titulo': 'Excluir Agendamento', 'botao': 'Excluir'}


class AgendamentoList(LoginRequiredMixin, AdminStaffRequiredMixin, ListView):
    model = Agendamento
    template_name = 'website/listas/agendamentos.html'
    context_object_name = 'agendamentos'


class AgendamentoDetail(LoginRequiredMixin, AdminStaffRequiredMixin, DetailView):
    model = Agendamento
    template_name = 'website/ver/agendamento.html'
    context_object_name = 'agendamento'


class MensagemContatoList(LoginRequiredMixin, AdminStaffRequiredMixin, ListView):
    model = MensagemContato
    template_name = 'website/listas/mensagens.html'
    context_object_name = 'mensagens'


class MensagemContatoDetail(LoginRequiredMixin, AdminStaffRequiredMixin, DetailView):
    model = MensagemContato
    template_name = 'website/ver/mensagem.html'
    context_object_name = 'mensagem'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.lida:
            obj.lida = True
            obj.save(update_fields=['lida'])
        return obj


class MensagemContatoDelete(LoginRequiredMixin, AdminStaffRequiredMixin, DeleteView):
    model = MensagemContato
    template_name = 'website/form.html'
    success_url = reverse_lazy('listar_mensagens')
    extra_context = {'titulo': 'Excluir Mensagem', 'botao': 'Excluir'}


# ==============================================================================
# 8. API DE HORÁRIOS DISPONÍVEIS
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

    horarios_ativos = HorarioDisponivel.objects.filter(
        barbeiro_id=barbeiro_id,
        ativo=True,
    ).values_list('horario', flat=True)

    agendamentos = Agendamento.objects.filter(
        barbeiro_id=barbeiro_id,
        data=data_agendamento,
    ).exclude(status=Agendamento.Status.CANCELADO).values_list('horario', flat=True)

    ocupados = set(agendamentos)

    resultado = []
    for h in sorted(horarios_ativos):
        resultado.append({
            'horario': h.strftime('%H:%M'),
            'disponivel': h not in ocupados,
        })

    return JsonResponse({'horarios': resultado})


# ==============================================================================
# 9. RECURSOS EXCLUSIVOS MOBILE & EXPERIÊNCIA NATIVA
# ==============================================================================

def validar_cupom_api(request):
    """Endpoint AJAX para validar cupom promocional e calcular o desconto em tempo real."""
    codigo = request.GET.get('codigo', '').strip().upper()
    valor_str = request.GET.get('valor', '0')

    try:
        valor_total = Decimal(str(valor_str))
    except Exception:
        valor_total = Decimal('0.00')

    if not codigo:
        return JsonResponse({'valido': False, 'mensagem': 'Informe o código do cupom.'}, status=400)

    try:
        cupom = CupomDesconto.objects.get(codigo__iexact=codigo)
    except CupomDesconto.DoesNotExist:
        return JsonResponse({'valido': False, 'mensagem': 'Cupom promocional não encontrado.'}, status=404)

    valido, mensagem = cupom.is_valido(valor_total)
    if not valido:
        return JsonResponse({'valido': False, 'mensagem': mensagem}, status=400)

    desconto, _ = cupom.calcular_desconto(valor_total)
    valor_final = max(Decimal('0.00'), valor_total - desconto)

    return JsonResponse({
        'valido': True,
        'codigo': cupom.codigo,
        'tipo': cupom.tipo,
        'tipo_display': cupom.get_tipo_display(),
        'valor_cupom': float(cupom.valor),
        'desconto_aplicado': float(desconto),
        'valor_final': float(valor_final),
        'mensagem': f"Cupom {cupom.codigo} aplicado com sucesso! Desconto de R$ {desconto:.2f}."
    })


def download_ics_view(request, pk):
    """Gera e retorna um arquivo .ics (iCalendar) para sincronizar o agendamento no iPhone / Android / Google Calendar."""
    agendamento = get_object_or_404(Agendamento, pk=pk)

    # Início e fim do agendamento
    data_hora_inicio = datetime.combine(agendamento.data, agendamento.horario)
    duracao = agendamento.servico.duracao_minutos or 40
    data_hora_fim = data_hora_inicio + timedelta(minutes=duracao)

    # Formatação RFC 5545
    fmt_ics = "%Y%m%dT%H%M%S"
    dtstart = data_hora_inicio.strftime(fmt_ics)
    dtend = data_hora_fim.strftime(fmt_ics)
    dtstamp = datetime.now().strftime(fmt_ics)

    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Delacruz Barber//Agendamento v2.0//PT-BR
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:delacruz-agendamento-{agendamento.id}@delacruzbarber.com.br
DTSTAMP:{dtstamp}
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:Delacruz Barber: {agendamento.servico.nome} com {agendamento.barbeiro.nome}
DESCRIPTION:Agendamento de {agendamento.servico.nome} na Delacruz Barber com o barbeiro {agendamento.barbeiro.nome}. Valor: R$ {agendamento.servico.preco}. Telefone: (44) 9919-0997.
LOCATION:Rua Terezinha Fortes Martins, 136, Jardim Progresso, Paranavaí - PR
STATUS:CONFIRMED
BEGIN:VALARM
TRIGGER:-PT2H
ACTION:DISPLAY
DESCRIPTION:Lembrete de corte na Delacruz Barber em 2 horas!
END:VALARM
END:VEVENT
END:VCALENDAR"""

    response = HttpResponse(ics_content, content_type='text/calendar; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="delacruz-agendamento-{agendamento.id}.ics"'
    return response


class RepetirUltimoCorteView(LoginRequiredMixin, View):
    """Permite ao cliente repetir seu último corte em 1 clique (1-Click Express Booking)."""
    def get(self, request):
        cliente = Cliente.objects.filter(usuario=request.user).first()
        if not cliente:
            messages.warning(request, "Perfil de cliente não encontrado.")
            return redirect('agendamento')

        ultimo_agendamento = Agendamento.objects.filter(
            cliente=cliente,
            status__in=[Agendamento.Status.CONCLUIDO, Agendamento.Status.CONFIRMADO]
        ).order_by('-data', '-horario').first()

        if ultimo_agendamento:
            url = f"{reverse('agendamento')}?servico={ultimo_agendamento.servico.id}&barbeiro={ultimo_agendamento.barbeiro.id}"
            return redirect(url)

        messages.info(request, "Nenhum histórico anterior encontrado. Selecione seu serviço e barbeiro preferido.")
        return redirect('agendamento')
