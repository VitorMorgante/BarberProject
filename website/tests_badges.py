import os
from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from website.models import User, Servico, Barbeiro, HorarioDisponivel


class TestBadgesCompatibility(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='barbeiro_badge_user',
            password='password123',
            is_staff=True
        )
        self.barbeiro = Barbeiro.objects.create(nome='Heitor Pontes', cargo='Master Barber', ativo=True)
        self.servico = Servico.objects.create(
            usuario=self.user,
            nome='Corte Degradê',
            categoria='Cabelo',
            preco=45.0,
            duracao_minutos=30,
            ativo=True
        )
        self.horario = HorarioDisponivel.objects.create(
            usuario=self.user,
            barbeiro=self.barbeiro,
            horario='14:00',
            ativo=True
        )
        self.client = Client()

    def test_css_tokens_and_adaptive_classes_exist(self):
        """Verifica se o arquivo style.css possui o sistema adaptativo de badges (claro no escuro, escuro no claro)."""
        css_path = os.path.join(settings.BASE_DIR, 'website', 'static', 'website', 'css', 'style.css')
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()

        # Variáveis de badges no escuro (badges claras)
        self.assertIn('--badge-bg-neutral: #f8fafc', css_content)
        self.assertIn('--badge-text-neutral: #090d16', css_content)

        # Variáveis de badges no claro (badges escuras)
        self.assertIn('--badge-bg-neutral: #090d16', css_content)
        self.assertIn('--badge-text-neutral: #f8fafc', css_content)

        # Classes universais
        self.assertIn('.badge-count', css_content)
        self.assertIn('.badge.bg-brand', css_content)
        self.assertIn('.badge.bg-dark', css_content)
        self.assertIn('.badge.bg-success', css_content)
        self.assertIn('.badge-status-Pendente', css_content)
        self.assertIn('.badge-status-Confirmado', css_content)

    def test_listas_render_badges_correctly(self):
        """Testa se as telas de listagem renderizam badge-count e badges de status adequadamente."""
        self.client.login(username='barbeiro_badge_user', password='password123')

        # 1. Horários
        res_horarios = self.client.get(reverse('listar_horarios'))
        self.assertEqual(res_horarios.status_code, 200)
        self.assertIn('badge-count', res_horarios.content.decode('utf-8'))
        self.assertIn('badge bg-success', res_horarios.content.decode('utf-8'))

        # 2. Serviços
        res_servicos = self.client.get(reverse('listar_servicos'))
        self.assertEqual(res_servicos.status_code, 200)
        self.assertIn('badge-count', res_servicos.content.decode('utf-8'))
        self.assertIn('badge bg-secondary', res_servicos.content.decode('utf-8'))
        self.assertIn('badge bg-success', res_servicos.content.decode('utf-8'))
