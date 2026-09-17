from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from website.models import Cliente, PlanoAssinatura, AssinaturaCliente
from website.portfolio_data import PORTFOLIO_ITEMS


class UserFeedbackEnhancementsTestCase(TestCase):
    """
    Testes de validação dos ajustes solicitados pelo usuário:
    1. Bootbox.js carregado em modelo.html
    2. Ausência de 'Nossa Filosofia' e presença do carrossel contínuo no lounge em inicio.html
    3. Expurgamento de vocabulário cirúrgico / visagismo / acabamento preciso
    4. Nomes reais da cultura de barbearia no catálogo de portfólio (Americano, Corte do Jaca, Moica)
    5. Botão de cancelamento visível para assinaturas ativas e pendentes com atributos Bootbox
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='cliente_feedback', password='123')
        self.cliente = Cliente.objects.create(
            usuario=self.user,
            nome='Cliente Feedback',
            email='feedback@teste.com',
            telefone='44999998888'
        )
        self.plano = PlanoAssinatura.objects.create(
            nome='Plano com barba',
            preco_mensal=Decimal('120.00'),
            modalidade=PlanoAssinatura.Modalidade.LIMITADO,
            limite_mensal=4,
            quantidade_creditos=4,
            validade_dias=30,
            ativo=True
        )

    def test_01_bootbox_carregado_em_modelo(self):
        """Garante que a biblioteca bootbox.all.min.js é carregada nas páginas que herdam de modelo.html."""
        resp = self.client.get(reverse('pagina_inicial'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('bootbox.all.min.js', resp.content.decode('utf-8'))

    def test_02_inicio_sem_nossa_filosofia_e_com_carrossel_continuo(self):
        """Página inicial não deve conter 'Nossa Filosofia' e deve ter carrossel contínuo no Lounge."""
        resp = self.client.get(reverse('pagina_inicial'))
        conteudo = resp.content.decode('utf-8')

        # 'Nossa Filosofia' e seção experiencia devem estar removidas
        self.assertNotIn('Nossa Filosofia', conteudo)
        self.assertNotIn('id="experiencia"', conteudo)

        # Carrossel contínuo no Lounge
        self.assertIn('id="loungePortfolioCarousel"', conteudo)
        self.assertIn('data-bs-ride="carousel"', conteudo)
        self.assertIn('data-bs-interval="1500"', conteudo)
        self.assertIn('data-bs-pause="false"', conteudo)
        self.assertIn('corte-01.jpg', conteudo)

    def test_03_portfolio_termos_autenticos_barbearia(self):
        """Verifica a presença dos termos e cortes autênticos (Americano, Corte do Jaca, Moica)."""
        titulos = [item['titulo'] for item in PORTFOLIO_ITEMS]
        self.assertIn('Corte Americano', titulos)
        self.assertIn('Corte do Jaca', titulos)
        self.assertIn('Moica Disfarçado', titulos)
        self.assertIn('Taper Fade Alinhado', titulos)

    def test_04_expurgamento_termos_cirurgicos_e_visagismo(self):
        """Verifica ausência de termos clínicos nas páginas públicas principais."""
        for rota in ['pagina_inicial', 'sobre', 'galeria']:
            resp = self.client.get(reverse(rota))
            conteudo = resp.content.decode('utf-8').lower()
            self.assertNotIn('cirúrgico', conteudo)
            self.assertNotIn('cirurgico', conteudo)
            self.assertNotIn('visagismo', conteudo)
            self.assertNotIn('acabamento preciso', conteudo)

    def test_05_club_card_simetrico_e_cancelar_disponivel_para_pendente(self):
        """
        Para assinaturas pendentes, o botão de cancelamento deve estar disponível no topo do card,
        e os botões devem acionar o diálogo Bootbox.
        """
        from website.services import SubscriptionService
        SubscriptionService.solicitar_assinatura(self.cliente, self.plano)
        self.client.login(username='cliente_feedback', password='123')
        resp = self.client.get(reverse('cliente_club'))
        self.assertEqual(resp.status_code, 200)
        conteudo = resp.content.decode('utf-8')

        # Botão de cancelar assinatura deve estar presente mesmo no status Pendente
        self.assertIn('btn-cancelar-assinatura', conteudo)
        self.assertIn('Cancelar Assinatura', conteudo)

        # Botão de ativação PIX deve estar presente para o plano pendente
        self.assertIn('Pagar / Ativar via PIX', conteudo)

        # Script de confirmação com Bootbox presente na página
        self.assertIn('bootbox.confirm', conteudo)
        self.assertIn('data-plano-nome', conteudo)

    def test_06_login_page_luxury_design_and_buttons(self):
        """Verifica a tela de login sofisticada com botão dourado e link de cadastro esmeralda."""
        resp = self.client.get(reverse('login'))
        self.assertEqual(resp.status_code, 200)
        conteudo = resp.content.decode('utf-8')

        # Card luxury e elementos visuais
        self.assertIn('auth-luxury-card', conteudo)
        self.assertIn('Acesso Exclusivo', conteudo)
        self.assertIn('id="id_username"', conteudo)
        self.assertIn('id="id_password"', conteudo)

        # Botão de Login Dourado (btn-brand)
        self.assertIn('btn-brand', conteudo)
        self.assertIn('Entrar na Minha Conta', conteudo)

        # Botão de Cadastro Diferenciado (btn-cadastro-luxury)
        self.assertIn('btn-cadastro-luxury', conteudo)
        self.assertIn('Criar Conta', conteudo)

    def test_07_cadastro_page_luxury_design_and_buttons(self):
        """Verifica a tela de cadastro com botão esmeralda e link de login dourado."""
        resp = self.client.get(reverse('cadastro'))
        self.assertEqual(resp.status_code, 200)
        conteudo = resp.content.decode('utf-8')

        # Card luxury e formulário completo
        self.assertIn('auth-luxury-card', conteudo)
        self.assertIn('Criar Conta', conteudo)
        self.assertIn('name="nome"', conteudo)
        self.assertIn('name="sobrenome"', conteudo)
        self.assertIn('name="usuario"', conteudo)
        self.assertIn('name="telefone"', conteudo)

        # Botão de Cadastro Diferenciado (btn-cadastro-luxury)
        self.assertIn('btn-cadastro-luxury', conteudo)
        self.assertIn('Criar Conta', conteudo)

        # Botão de Login Dourado (btn-outline-brand)
        self.assertIn('btn-outline-brand', conteudo)
        self.assertIn('Já possuo conta', conteudo)

    def test_08_perfil_photo_custom_luxury_styling_and_preview(self):
        """Verifica se o seletor de foto de perfil possui badge de câmera, campo id_foto_perfil e script de preview."""
        self.client.login(username='cliente_feedback', password='123')
        resp = self.client.get(reverse('area_cliente'))
        self.assertEqual(resp.status_code, 200)
        conteudo = resp.content.decode('utf-8')

        # Presença do campo foto de perfil e do container/avatar com live preview
        self.assertIn('id_foto_perfil', conteudo)
        self.assertIn('client-avatar-preview', conteudo)
        self.assertIn('Alterar Foto de Perfil', conteudo)
        self.assertIn('FileReader', conteudo)

