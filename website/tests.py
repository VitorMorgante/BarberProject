from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from website.models import Servico, Barbeiro, Cliente, HorarioDisponivel, Agendamento
from datetime import time, date, timedelta



class TestPublicPages(TestCase):
    """Test that all public pages return HTTP 200."""

    def setUp(self):
        self.barbeiro = Barbeiro.objects.create(
            nome='Danilo Delacruz',
            cargo='Barbeiro Chefe',
            especialidade='Cortes clássicos, degradê e acabamento preciso',
            ativo=True,
        )
        self.servico = Servico.objects.create(
            nome='Corte Degradê',
            descricao='Corte masculino com técnica de degradê.',
            preco=45.00,
            duracao_minutos=40,
            ativo=True,
            destaque=True,
        )
        HorarioDisponivel.objects.create(
            barbeiro=self.barbeiro,
            horario=time(9, 0),
            ativo=True,
        )

    def test_home_page(self):
        response = self.client.get(reverse('pagina_inicial'))
        self.assertEqual(response.status_code, 200)

    def test_about_page(self):
        response = self.client.get(reverse('sobre'))
        self.assertEqual(response.status_code, 200)

    def test_contact_page(self):
        response = self.client.get(reverse('contato'))
        self.assertEqual(response.status_code, 200)

    def test_appointment_page(self):
        response = self.client.get(reverse('agendamento'))
        self.assertEqual(response.status_code, 200)

    def test_services_page(self):
        response = self.client.get(reverse('servicos'))
        self.assertEqual(response.status_code, 200)

    def test_barbers_page(self):
        response = self.client.get(reverse('barbeiros'))
        self.assertEqual(response.status_code, 200)


class TestModels(TestCase):
    """Test model creation."""

    def test_servico_creation(self):
        servico = Servico.objects.create(
            nome='Corte Teste',
            descricao='Descrição de teste.',
            preco=50.00,
            duracao_minutos=30,
        )
        self.assertEqual(str(servico), 'Corte Teste')
        self.assertTrue(servico.ativo)

    def test_barbeiro_creation(self):
        barbeiro = Barbeiro.objects.create(
            nome='Barbeiro Teste',
            cargo='Barbeiro',
            especialidade='Cortes modernos',
        )
        self.assertEqual(str(barbeiro), 'Barbeiro Teste')
        self.assertTrue(barbeiro.ativo)


class TestAgendamentoValidation(TestCase):
    """Test that duplicate active appointments are rejected."""

    def setUp(self):
        self.barbeiro = Barbeiro.objects.create(
            nome='Danilo Delacruz',
            cargo='Barbeiro Chefe',
            especialidade='Cortes clássicos',
        )
        self.servico = Servico.objects.create(
            nome='Corte Degradê',
            descricao='Corte degradê.',
            preco=45.00,
            duracao_minutos=40,
        )
        self.cliente = Cliente.objects.create(
            nome='Cliente Teste',
            telefone='11999999999',
            email='teste@email.com',
        )
        self.horario_disp = HorarioDisponivel.objects.create(
            barbeiro=self.barbeiro,
            horario=time(9, 0),
            ativo=True,
        )
        self.data_futura = date.today() + timedelta(days=7)

    def test_duplicate_active_appointment_rejected(self):
        """Creating two active appointments for the same barber/date/time should fail."""
        Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            barbeiro=self.barbeiro,
            data=self.data_futura,
            horario=time(9, 0),
            status='Pendente',
        )
        with self.assertRaises(Exception):
            Agendamento.objects.create(
                cliente=self.cliente,
                servico=self.servico,
                barbeiro=self.barbeiro,
                data=self.data_futura,
                horario=time(9, 0),
                status='Confirmado',
            )

    def test_cancelled_then_rebook_allowed(self):
        """A cancelled appointment should allow rebooking the same slot."""
        Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            barbeiro=self.barbeiro,
            data=self.data_futura,
            horario=time(9, 0),
            status='Cancelado',
        )
        # This should NOT raise
        agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            barbeiro=self.barbeiro,
            data=self.data_futura,
            horario=time(9, 0),
            status='Pendente',
        )
        self.assertEqual(agendamento.status, 'Pendente')


class TestBarbeiroPermissions(TestCase):
    """Test permissions for Barbeiro CRUD views."""

    def setUp(self):
        self.client_user = User.objects.create_user(username='client', password='password123')
        self.staff_user = User.objects.create_user(username='staff', password='password123', is_staff=True)
        self.superuser = User.objects.create_user(username='admin', password='password123', is_superuser=True)
        self.barbeiro = Barbeiro.objects.create(
            nome='Test Barber',
            cargo='Barbeiro',
            especialidade='Modern cut',
            ativo=True
        )

    def test_anonymous_user_redirected_to_login(self):
        urls = [
            reverse('cadastrar_barbeiro'),
            reverse('listar_barbeiros'),
            reverse('editar_barbeiro', args=[self.barbeiro.pk]),
            reverse('excluir_barbeiro', args=[self.barbeiro.pk]),
            reverse('ver_barbeiro', args=[self.barbeiro.pk]),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)

    def test_client_user_forbidden(self):
        self.client.login(username='client', password='password123')
        urls = [
            reverse('cadastrar_barbeiro'),
            reverse('listar_barbeiros'),
            reverse('editar_barbeiro', args=[self.barbeiro.pk]),
            reverse('excluir_barbeiro', args=[self.barbeiro.pk]),
            reverse('ver_barbeiro', args=[self.barbeiro.pk]),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403)

    def test_staff_user_allowed(self):
        self.client.login(username='staff', password='password123')
        urls = [
            reverse('cadastrar_barbeiro'),
            reverse('listar_barbeiros'),
            reverse('editar_barbeiro', args=[self.barbeiro.pk]),
            reverse('ver_barbeiro', args=[self.barbeiro.pk]),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_superuser_allowed(self):
        self.client.login(username='admin', password='password123')
        urls = [
            reverse('cadastrar_barbeiro'),
            reverse('listar_barbeiros'),
            reverse('editar_barbeiro', args=[self.barbeiro.pk]),
            reverse('ver_barbeiro', args=[self.barbeiro.pk]),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

