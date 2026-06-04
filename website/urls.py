from django.urls import path
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Auth
    path('login/', auth_views.LoginView.as_view(
        template_name='website/form.html',
        extra_context={'titulo': 'Login', 'botao': 'Entrar'},
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('cadastro/', views.CadastroUsuarioView.as_view(), name='cadastro'),
    path('alterar-senha/', auth_views.PasswordChangeView.as_view(
        template_name='website/form.html',
        success_url=reverse_lazy('dashboard'),
        extra_context={'titulo': 'Alterar Senha', 'botao': 'Alterar'},
    ), name='alterar_senha'),


    # Public
    path('', views.IndexView.as_view(), name='pagina_inicial'),
    path('sobre/', views.SobreView.as_view(), name='sobre'),
    path('contato/', views.ContatoView.as_view(), name='contato'),
    path('agendamento/', views.AgendamentoPublicoView.as_view(), name='agendamento'),
    path('servicos/', views.ServicosPublicView.as_view(), name='servicos'),
    path('barbeiros/', views.BarbeirosPublicView.as_view(), name='barbeiros'),

    # API
    path('api/horarios-disponiveis/', views.horarios_disponiveis_api, name='api_horarios_disponiveis'),

    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    # Servico CRUD
    path('cadastrar/servico/', views.ServicoCreate.as_view(), name='cadastrar_servico'),
    path('listar/servicos/', views.ServicoList.as_view(), name='listar_servicos'),
    path('editar/servico/<int:pk>/', views.ServicoUpdate.as_view(), name='editar_servico'),
    path('excluir/servico/<int:pk>/', views.ServicoDelete.as_view(), name='excluir_servico'),
    path('ver/servico/<int:pk>/', views.ServicoDetail.as_view(), name='ver_servico'),

    # Barbeiro CRUD
    path('cadastrar/barbeiro/', views.BarbeiroCreate.as_view(), name='cadastrar_barbeiro'),
    path('listar/barbeiros/', views.BarbeiroList.as_view(), name='listar_barbeiros'),
    path('editar/barbeiro/<int:pk>/', views.BarbeiroUpdate.as_view(), name='editar_barbeiro'),
    path('excluir/barbeiro/<int:pk>/', views.BarbeiroDelete.as_view(), name='excluir_barbeiro'),
    path('ver/barbeiro/<int:pk>/', views.BarbeiroDetail.as_view(), name='ver_barbeiro'),

    # Cliente CRUD
    path('cadastrar/cliente/', views.ClienteCreate.as_view(), name='cadastrar_cliente'),
    path('listar/clientes/', views.ClienteList.as_view(), name='listar_clientes'),
    path('editar/cliente/<int:pk>/', views.ClienteUpdate.as_view(), name='editar_cliente'),
    path('excluir/cliente/<int:pk>/', views.ClienteDelete.as_view(), name='excluir_cliente'),
    path('ver/cliente/<int:pk>/', views.ClienteDetail.as_view(), name='ver_cliente'),

    # HorarioDisponivel CRUD
    path('cadastrar/horario/', views.HorarioDisponivelCreate.as_view(), name='cadastrar_horario'),
    path('listar/horarios/', views.HorarioDisponivelList.as_view(), name='listar_horarios'),
    path('editar/horario/<int:pk>/', views.HorarioDisponivelUpdate.as_view(), name='editar_horario'),
    path('excluir/horario/<int:pk>/', views.HorarioDisponivelDelete.as_view(), name='excluir_horario'),
    path('ver/horario/<int:pk>/', views.HorarioDisponivelDetail.as_view(), name='ver_horario'),

    # Agendamento CRUD
    path('cadastrar/agendamento/', views.AgendamentoCreate.as_view(), name='cadastrar_agendamento'),
    path('listar/agendamentos/', views.AgendamentoList.as_view(), name='listar_agendamentos'),
    path('editar/agendamento/<int:pk>/', views.AgendamentoUpdate.as_view(), name='editar_agendamento'),
    path('excluir/agendamento/<int:pk>/', views.AgendamentoDelete.as_view(), name='excluir_agendamento'),
    path('ver/agendamento/<int:pk>/', views.AgendamentoDetail.as_view(), name='ver_agendamento'),

    # MensagemContato
    path('listar/mensagens/', views.MensagemContatoList.as_view(), name='listar_mensagens'),
    path('ver/mensagem/<int:pk>/', views.MensagemContatoDetail.as_view(), name='ver_mensagem'),
    path('excluir/mensagem/<int:pk>/', views.MensagemContatoDelete.as_view(), name='excluir_mensagem'),

    # Client Area
    path('cliente/area/', views.AreaClienteView.as_view(), name='area_cliente'),
    path('cliente/historico/', views.HistoricoClienteView.as_view(), name='historico_cliente'),
    path('cliente/feedback/<int:pk>/', views.FeedbackCreateView.as_view(), name='criar_feedback'),
    path('cliente/perfil/', views.PerfilClienteView.as_view(), name='perfil_cliente'),
    path('cliente/cancelar/<int:pk>/', views.CancelarAgendamentoClienteView.as_view(), name='cancelar_agendamento_cliente'),

    # Barber Area
    path('barbeiro/area/', views.AreaBarbeiroView.as_view(), name='area_barbeiro'),
    path('barbeiro/agendamentos/', views.AgendamentosBarbeiroView.as_view(), name='agendamentos_barbeiro'),
    path('barbeiro/historico/', views.HistoricoBarbeiroView.as_view(), name='historico_barbeiro'),
    path('barbeiro/relatorios/', views.RelatoriosBarbeiroView.as_view(), name='relatorios_barbeiro'),
    path('barbeiro/fotos/', views.FotoTrabalhoListView.as_view(), name='fotos_barbeiro'),
    path('barbeiro/fotos/cadastrar/', views.FotoTrabalhoCreateView.as_view(), name='cadastrar_foto_barbeiro'),
    path('barbeiro/fotos/editar/<int:pk>/', views.FotoTrabalhoUpdateView.as_view(), name='editar_foto_barbeiro'),
    path('barbeiro/fotos/excluir/<int:pk>/', views.FotoTrabalhoDeleteView.as_view(), name='excluir_foto_barbeiro'),

    # Available Times Helper View (alias)
    path('horarios-disponiveis/', views.horarios_disponiveis_api, name='horarios_disponiveis'),
]
