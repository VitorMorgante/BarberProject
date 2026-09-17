from decimal import Decimal
from datetime import date, time, timedelta
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from website.models import (
    Servico, Cliente, Barbeiro, Agendamento, Feedback, PerfilUsuario, Comanda
)


class PerformanceQueryCountTests(TestCase):
    """
    Testes de regressão de performance garantindo que N+1 queries não ocorram
    nas views de alta frequência (Histórico, Dashboard, Barbeiro, etc).
    """

    def setUp(self):
        # Cria barbeiro com usuário
        self.barbeiro_user = User.objects.create_user(
            username='barbeiro_perf', password='password123',
            first_name='Carlos', last_name='Barbeiro'
        )
        PerfilUsuario.objects.create(
            usuario=self.barbeiro_user,
            tipo_usuario='barbeiro',
            telefone='44999990001'
        )
        self.barbeiro = Barbeiro.objects.create(
            usuario=self.barbeiro_user,
            nome='Carlos Barbeiro',
            ativo=True
        )

        # Cria cliente com usuário
        self.cliente_user = User.objects.create_user(
            username='cliente_perf', password='password123',
            first_name='Joao', last_name='Cliente'
        )
        PerfilUsuario.objects.create(
            usuario=self.cliente_user,
            tipo_usuario='cliente',
            telefone='44999990002'
        )
        self.cliente = Cliente.objects.create(
            usuario=self.cliente_user,
            nome='Joao Cliente',
            telefone='44999990002',
            email='joao@test.com'
        )

        # Cria cliente invasor para testes de segurança/IDOR
        self.outro_user = User.objects.create_user(
            username='invasor_perf', password='password123',
            first_name='Pedro', last_name='Invasor'
        )
        PerfilUsuario.objects.create(
            usuario=self.outro_user,
            tipo_usuario='cliente',
            telefone='44999990003'
        )
        self.outro_cliente = Cliente.objects.create(
            usuario=self.outro_user,
            nome='Pedro Invasor',
            telefone='44999990003',
            email='pedro@test.com'
        )

        # Cria serviços
        self.servico_corte = Servico.objects.create(
            nome='Corte Masculino Perf',
            preco=Decimal('35.00'),
            duracao_minutos=30,
            ativo=True
        )
        self.servico_barba = Servico.objects.create(
            nome='Barba Modelada Perf',
            preco=Decimal('25.00'),
            duracao_minutos=20,
            ativo=True
        )

        # Cria 6 agendamentos com serviços e feedbacks para o cliente
        self.agendamentos = []
        hoje = date.today()
        for i in range(6):
            ag = Agendamento.objects.create(
                cliente=self.cliente,
                barbeiro=self.barbeiro,
                servico=self.servico_corte if i % 2 == 0 else self.servico_barba,
                data=hoje - timedelta(days=i + 1),
                horario=time(9 + i, 0),
                status=Agendamento.Status.CONCLUIDO
            )
            Feedback.objects.create(
                agendamento=ag,
                cliente=self.cliente,
                barbeiro=self.barbeiro,
                nota=5,
                comentario=f'Excelente corte #{i}'
            )
            self.agendamentos.append(ag)

    def test_historico_cliente_query_count_constant(self):
        """
        O histórico do cliente não deve disparar consultas N+1 por linha.
        Mesmo com 6 agendamentos + feedbacks + serviços + barbeiros, a listagem
        deve resolver tudo em 1 única query joined via select_related.
        """
        self.client.login(username='cliente_perf', password='password123')
        
        # 6 queries: session, auth_user, cliente, perfil, barbeiro exists, agendamentos join
        with self.assertNumQueries(6):
            response = self.client.get(reverse('historico_cliente'))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Corte Masculino Perf')
            self.assertContains(response, 'Carlos Barbeiro')

    def test_agendamentos_barbeiro_query_count_optimized(self):
        """
        A visão de agendamentos do barbeiro deve usar select_related('cliente', 'servico')
        garantindo que o loop com link de WhatsApp não execute N queries de cliente.
        """
        self.client.login(username='barbeiro_perf', password='password123')
        with self.assertNumQueries(6):
            response = self.client.get(reverse('agendamentos_barbeiro'))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Joao Cliente')


class SecurityAndAuthorizationHardeningTests(TestCase):
    """
    Testes de segurança contra IDOR (Insecure Direct Object Reference) e
    violações de controle de acesso entre clientes e barbeiros.
    """

    def setUp(self):
        self.user1 = User.objects.create_user(username='vitima', password='pwd')
        self.cliente1 = Cliente.objects.create(usuario=self.user1, nome='Vitima', telefone='1111')

        self.user2 = User.objects.create_user(username='atacante', password='pwd')
        self.cliente2 = Cliente.objects.create(usuario=self.user2, nome='Atacante', telefone='2222')

        self.barbeiro = Barbeiro.objects.create(nome='Barbeiro Teste', ativo=True)
        self.servico = Servico.objects.create(nome='Corte Teste', preco=Decimal('30.00'), duracao_minutos=30)

        self.agendamento = Agendamento.objects.create(
            cliente=self.cliente1,
            barbeiro=self.barbeiro,
            servico=self.servico,
            data=date.today() + timedelta(days=2),
            horario=time(10, 0),
            status=Agendamento.Status.CONFIRMADO
        )

    def test_cliente_nao_pode_cancelar_agendamento_alheio(self):
        """Um cliente não pode cancelar o agendamento de outro cliente (prevenção contra IDOR)."""
        self.client.login(username='atacante', password='pwd')
        url = reverse('cancelar_agendamento_cliente', kwargs={'pk': self.agendamento.pk})
        response = self.client.post(url)
        
        # Deve redirecionar com erro e manter o agendamento inalterado
        self.agendamento.refresh_from_db()
        self.assertEqual(self.agendamento.status, Agendamento.Status.CONFIRMADO)

    def test_cliente_nao_pode_avaliar_agendamento_alheio(self):
        """Um cliente não pode avaliar um agendamento pertencente a outro cliente."""
        self.agendamento.status = Agendamento.Status.CONCLUIDO
        self.agendamento.save()

        self.client.login(username='atacante', password='pwd')
        url = reverse('criar_feedback', kwargs={'pk': self.agendamento.pk})
        response = self.client.get(url)
        
        # Deve bloquear o acesso e redirecionar para area_cliente
        self.assertRedirects(response, reverse('area_cliente'))
