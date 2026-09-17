from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from website.models import (
    Cliente, PlanoAssinatura, AssinaturaCliente, Pagamento, ConfiguracaoEstabelecimento
)
from website.services import PaymentService, SubscriptionService


class TestSubscriptionPaymentFlow(TestCase):
    def setUp(self):
        self.config, _ = ConfiguracaoEstabelecimento.objects.get_or_create(
            id=1,
            defaults={
                'minutos_expiracao_pix': 30,
                'chave_pix': 'pix@heitor.com',
                'titular_pix': 'Heitor Pontes',
                'cidade_pix': 'Paranavai'
            }
        )
        self.user = User.objects.create_user(
            username='clienteteste',
            password='password123',
            first_name='João',
            last_name='Silva',
            email='joao@teste.com'
        )
        self.cliente = Cliente.objects.create(
            usuario=self.user,
            nome='João Silva',
            email='joao@teste.com',
            telefone='41999999999'
        )
        self.plano = PlanoAssinatura.objects.create(
            nome='Plano Vip Prime',
            preco_mensal=Decimal('99.90'),
            modalidade=PlanoAssinatura.Modalidade.LIMITADO,
            limite_mensal=4,
            quantidade_creditos=4,
            validade_dias=30,
            ativo=True
        )
        self.client = Client()

    def test_inicio_page_has_direct_subscription_link(self):
        """Verifica se o botão de assinar na home direciona para o checkout do clube com o id do plano."""
        response = self.client.get(reverse('pagina_inicial'))
        self.assertEqual(response.status_code, 200)
        expected_url = f"{reverse('cliente_club')}?assinar={self.plano.id}"
        self.assertIn(expected_url, response.content.decode())

    def test_get_cliente_club_with_assinar_redirects_to_pix_payment(self):
        """Ao acessar /cliente/club/?assinar=ID, deve gerar a cobrança PIX e redirecionar para tela de pagamento."""
        self.client.login(username='clienteteste', password='password123')
        response = self.client.get(reverse('cliente_club'), {'assinar': self.plano.id})
        
        # Deve redirecionar para a tela de pagamento PIX
        self.assertEqual(response.status_code, 302)
        pagamento = Pagamento.objects.filter(tipo=Pagamento.Tipo.ASSINATURA, assinatura__cliente=self.cliente).first()
        self.assertIsNotNone(pagamento)
        self.assertEqual(pagamento.valor, Decimal('99.90'))
        self.assertEqual(pagamento.status, Pagamento.Status.AGUARDANDO)
        self.assertIn(reverse('pagamento_pix', kwargs={'identificador': pagamento.identificador_interno}), response.url)

    def test_post_cliente_club_redirects_to_pix_payment(self):
        """Ao enviar o formulário do plano via POST, gera cobrança e redireciona para tela de pagamento."""
        self.client.login(username='clienteteste', password='password123')
        response = self.client.post(reverse('cliente_club'), {'plano_id': self.plano.id})
        
        self.assertEqual(response.status_code, 302)
        pagamento = Pagamento.objects.filter(tipo=Pagamento.Tipo.ASSINATURA, assinatura__cliente=self.cliente).first()
        self.assertIsNotNone(pagamento)
        self.assertIn(pagamento.identificador_interno, response.url)

    def test_pagamento_pix_screen_and_confirmation_activates_subscription(self):
        """Testa visualização da tela de pagamento da assinatura e confirmação via simulação."""
        self.client.login(username='clienteteste', password='password123')
        assinatura = SubscriptionService.solicitar_assinatura(self.cliente, self.plano)
        pagamento = PaymentService.criar_pagamento_assinatura(assinatura)

        # 1. Tela de pagamento PIX
        url_pix = reverse('pagamento_pix', kwargs={'identificador': pagamento.identificador_interno})
        response = self.client.get(url_pix)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Plano Vip Prime', response.content.decode())
        self.assertIn('Barber Club Prime', response.content.decode())

        # 2. Confirmação do pagamento
        with self.settings(DEBUG=True, PAYMENT_GATEWAY='mock'):
            post_response = self.client.post(url_pix)
            self.assertEqual(post_response.status_code, 302)
            self.assertIn(reverse('cliente_club'), post_response.url)

        # Verifica ativação da assinatura e créditos
        assinatura.refresh_from_db()
        self.assertEqual(assinatura.status, AssinaturaCliente.Status.ATIVA)
        self.assertEqual(assinatura.creditos_disponiveis, 4)

        # 3. Na tela do clube deve aparecer o botão de agendar com créditos
        club_response = self.client.get(reverse('cliente_club'))
        self.assertEqual(club_response.status_code, 200)
        self.assertIn('Agendar com meus Créditos', club_response.content.decode('utf-8'))

    def test_pagamento_status_api_for_subscription(self):
        """API de status deve indicar que é assinatura e fornecer a rota de redirecionamento para o clube."""
        self.client.login(username='clienteteste', password='password123')
        assinatura = SubscriptionService.solicitar_assinatura(self.cliente, self.plano)
        pagamento = PaymentService.criar_pagamento_assinatura(assinatura)

        api_url = reverse('api_pagamento_status', kwargs={'identificador': pagamento.identificador_interno})
        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['is_assinatura'])
        self.assertEqual(data['redirect_url'], reverse('cliente_club'))

    def test_cancelar_assinatura_cliente(self):
        """Testa o cancelamento transparente da assinatura pelo cliente no Barber Club."""
        self.client.login(username='clienteteste', password='password123')
        assinatura = SubscriptionService.ativar_ou_renovar_assinatura(self.cliente, self.plano)
        self.assertEqual(assinatura.status, AssinaturaCliente.Status.ATIVA)

        # Tela do clube antes de cancelar deve ter o botão de Cancelar Assinatura
        response_before = self.client.get(reverse('cliente_club'))
        self.assertEqual(response_before.status_code, 200)
        self.assertIn('Cancelar Assinatura', response_before.content.decode('utf-8'))

        # Executa cancelamento via POST
        post_response = self.client.post(
            reverse('cancelar_assinatura_cliente'),
            {'motivo': 'Quero pausar por um tempo'}
        )
        self.assertEqual(post_response.status_code, 302)
        self.assertIn(reverse('cliente_club'), post_response.url)

        # Verifica banco de dados
        assinatura.refresh_from_db()
        self.assertEqual(assinatura.status, AssinaturaCliente.Status.CANCELADA)
        self.assertIsNotNone(assinatura.data_termino)

        # Tela do clube após cancelamento deve exibir status Cancelada
        response_after = self.client.get(reverse('cliente_club'))
        self.assertEqual(response_after.status_code, 200)
        self.assertIn('Assinatura Cancelada', response_after.content.decode('utf-8'))
        self.assertNotIn('title="Cancelar renovações desta assinatura"', response_after.content.decode('utf-8'))
