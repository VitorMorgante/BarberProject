from django.test import TestCase
from django.urls import reverse
from website.models import Servico, Barbeiro, HorarioDisponivel
from datetime import time, date

class PublicViewsTests(TestCase):
    def setUp(self):
        # Create initial test data
        self.barbeiro = Barbeiro.objects.create(
            nome='Daniel Delacruz',
            cargo='Barbeiro Chefe',
            especialidade='Cortes clássicos',
            ativo=True
        )
        self.servico = Servico.objects.create(
            nome='Corte Degradê',
            descricao='Corte masculino degradê',
            preco=45.00,
            duracao_minutos=40,
            ativo=True,
            destaque=True
        )
        self.horario = HorarioDisponivel.objects.create(
            barbeiro=self.barbeiro,
            horario=time(9, 0),
            ativo=True
        )

    def test_pagina_inicial_view(self):
        response = self.client.get(reverse('pagina_inicial'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'website/inicio.html')
        self.assertContains(response, 'Corte Degradê')

    def test_sobre_view(self):
        response = self.client.get(reverse('sobre'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'website/sobre.html')
        self.assertContains(response, 'Daniel Delacruz')

    def test_contato_view_get(self):
        response = self.client.get(reverse('contato'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'website/contato.html')

    def test_agendamento_view_get(self):
        response = self.client.get(reverse('agendamento'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'website/agendamento.html')

    def test_agendamento_sucesso_view(self):
        response = self.client.get(reverse('agendamento_sucesso'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'website/agendamento_sucesso.html')

    def test_api_horarios_disponiveis(self):
        url = reverse('api_horarios_disponiveis') + f'?barbeiro_id={self.barbeiro.pk}&data={date.today().strftime("%Y-%m-%d")}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {"horarios": [{"horario": "09:00", "disponivel": True}]}
        )

class AuthenticatedViewsTests(TestCase):
    def test_dashboard_redirects_to_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/dashboard/')

