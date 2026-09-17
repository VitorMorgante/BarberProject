from decimal import Decimal
from datetime import time, date
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from website.models import Servico, Cliente, Barbeiro, HorarioDisponivel, PerfilUsuario


class TerceiroTrimestreRequisitosTests(TestCase):
    """
    Suíte de testes para os 4 requisitos do Conceito do 3º Trimestre:
    1. Separação de objetos por usuário (Vídeos #21 e #22)
    2. Filtro de busca na ListView (Vídeo #36)
    3. Dois plugins jQuery (Máscara e DataTables) (Vídeos #33 e #34)
    4. Fluxo e integridade das rotas
    """

    def setUp(self):
        # Usuário 1 (Professor / Aluno A)
        self.user1 = User.objects.create_user(
            username='user_aluno1',
            password='senha123',
            email='aluno1@test.com',
            first_name='Aluno',
            last_name='Um',
            is_staff=True
        )
        PerfilUsuario.objects.create(usuario=self.user1, tipo_usuario='administrador', telefone='44999991111')

        # Usuário 2 (Professor / Aluno B)
        self.user2 = User.objects.create_user(
            username='user_aluno2',
            password='senha123',
            email='aluno2@test.com',
            first_name='Aluno',
            last_name='Dois',
            is_staff=True
        )
        PerfilUsuario.objects.create(usuario=self.user2, tipo_usuario='administrador', telefone='44999992222')

        # Barbeiro base para testes de horários
        self.barbeiro = Barbeiro.objects.create(
            nome='Heitor Master',
            cargo='Barbeiro',
            especialidade='Geral',
            ativo=True
        )

    # --------------------------------------------------------------------------
    # REQUISITO 1: Separação de objetos por usuário (Vídeos #21 e #22)
    # --------------------------------------------------------------------------

    def test_servico_create_atribui_usuario_logado(self):
        """No CreateView de Serviço, o usuário autenticado deve ser gravado automaticamente."""
        self.client.login(username='user_aluno1', password='senha123')
        resp = self.client.post(reverse('cadastrar_servico'), {
            'nome': 'Corte Navalhado VIP',
            'descricao': 'Corte com navalha e toalha quente',
            'preco': '45.00',
            'duracao_minutos': 35,
            'categoria': 'Cabelo',
            'icone': 'bi bi-scissors',
            'ativo': True,
            'ordem': 1
        })
        self.assertEqual(resp.status_code, 302)
        servico = Servico.objects.filter(nome='Corte Navalhado VIP').first()
        self.assertIsNotNone(servico)
        self.assertEqual(servico.usuario, self.user1)

    def test_servico_list_filtra_apenas_objetos_do_usuario(self):
        """User 1 deve visualizar apenas seus serviços; User 2 apenas os seus."""
        servico1 = Servico.objects.create(
            usuario=self.user1,
            nome='Serviço do User 1',
            descricao='Exclusivo User 1',
            preco=Decimal('50.00'),
            duracao_minutos=30,
            ativo=True
        )
        servico2 = Servico.objects.create(
            usuario=self.user2,
            nome='Serviço do User 2',
            descricao='Exclusivo User 2',
            preco=Decimal('60.00'),
            duracao_minutos=40,
            ativo=True
        )

        # Login com User 1
        self.client.login(username='user_aluno1', password='senha123')
        resp1 = self.client.get(reverse('listar_servicos'))
        self.assertEqual(resp1.status_code, 200)
        self.assertContains(resp1, 'Serviço do User 1')
        self.assertNotContains(resp1, 'Serviço do User 2')

        # Login com User 2
        self.client.login(username='user_aluno2', password='senha123')
        resp2 = self.client.get(reverse('listar_servicos'))
        self.assertEqual(resp2.status_code, 200)
        self.assertContains(resp2, 'Serviço do User 2')
        self.assertNotContains(resp2, 'Serviço do User 1')

    def test_servico_update_e_delete_bloqueia_outro_usuario(self):
        """User 2 não pode editar nem excluir serviço do User 1 (retorna 404)."""
        servico1 = Servico.objects.create(
            usuario=self.user1,
            nome='Corte Protegido User 1',
            descricao='Teste IDOR',
            preco=Decimal('50.00'),
            duracao_minutos=30,
            ativo=True
        )

        self.client.login(username='user_aluno2', password='senha123')

        # Tentativa de editar serviço alheio
        resp_edit = self.client.get(reverse('editar_servico', kwargs={'pk': servico1.pk}))
        self.assertEqual(resp_edit.status_code, 404)

        # Tentativa de excluir serviço alheio
        resp_del = self.client.get(reverse('excluir_servico', kwargs={'pk': servico1.pk}))
        self.assertEqual(resp_del.status_code, 404)

        resp_del_post = self.client.post(reverse('excluir_servico', kwargs={'pk': servico1.pk}))
        self.assertEqual(resp_del_post.status_code, 404)
        self.assertTrue(Servico.objects.filter(pk=servico1.pk).exists())

    def test_cliente_separacao_por_usuario(self):
        """Cliente CreateView grava usuário logado, ListView filtra por usuário e Update/Delete bloqueia terceiros."""
        # Criação direta associando aos usuários
        c1 = Cliente.objects.create(usuario=self.user1, nome='Cliente Exclusivo 1', telefone='44999990001', email='c1@test.com')
        c2 = Cliente.objects.create(usuario=self.user2, nome='Cliente Exclusivo 2', telefone='44999990002', email='c2@test.com')

        # User 1 visualiza apenas Cliente 1
        self.client.login(username='user_aluno1', password='senha123')
        resp1 = self.client.get(reverse('listar_clientes'))
        self.assertContains(resp1, 'Cliente Exclusivo 1')
        self.assertNotContains(resp1, 'Cliente Exclusivo 2')

        # User 2 não pode editar nem excluir Cliente 1
        self.client.login(username='user_aluno2', password='senha123')
        self.assertEqual(self.client.get(reverse('editar_cliente', kwargs={'pk': c1.pk})).status_code, 404)
        self.assertEqual(self.client.get(reverse('excluir_cliente', kwargs={'pk': c1.pk})).status_code, 404)

    def test_horario_separacao_por_usuario(self):
        """HorarioDisponivel também respeita isolamento por usuário (3ª classe de garantia)."""
        h1 = HorarioDisponivel.objects.create(usuario=self.user1, barbeiro=self.barbeiro, horario=time(8, 0), ativo=True)
        h2 = HorarioDisponivel.objects.create(usuario=self.user2, barbeiro=self.barbeiro, horario=time(9, 0), ativo=True)

        self.client.login(username='user_aluno1', password='senha123')
        resp = self.client.get(reverse('listar_horarios'))
        self.assertContains(resp, '08:00')
        self.assertNotContains(resp, '09:00')

        self.client.login(username='user_aluno2', password='senha123')
        self.assertEqual(self.client.get(reverse('editar_horario', kwargs={'pk': h1.pk})).status_code, 404)
        self.assertEqual(self.client.get(reverse('excluir_horario', kwargs={'pk': h1.pk})).status_code, 404)

    # --------------------------------------------------------------------------
    # REQUISITO 2: Filtro de pesquisa na ListView (Vídeo #36)
    # --------------------------------------------------------------------------

    def test_filtro_pesquisa_servicos_listview(self):
        """A busca GET ?nome=... deve filtrar serviços pelo nome no get_queryset."""
        Servico.objects.create(usuario=self.user1, nome='Barboterapia Real', preco=Decimal('35.00'), duracao_minutos=20, ativo=True)
        Servico.objects.create(usuario=self.user1, nome='Degradê Americano', preco=Decimal('45.00'), duracao_minutos=30, ativo=True)
        Servico.objects.create(usuario=self.user1, nome='Hidratação Capilar', preco=Decimal('25.00'), duracao_minutos=15, ativo=True)

        self.client.login(username='user_aluno1', password='senha123')

        # Busca por 'Barbo'
        resp_busca = self.client.get(reverse('listar_servicos'), {'nome': 'Barbo'})
        self.assertEqual(resp_busca.status_code, 200)
        self.assertContains(resp_busca, 'Barboterapia Real')
        self.assertNotContains(resp_busca, 'Degradê Americano')
        self.assertNotContains(resp_busca, 'Hidratação Capilar')

        # Busca por 'Americano'
        resp_busca2 = self.client.get(reverse('listar_servicos'), {'nome': 'Americano'})
        self.assertEqual(resp_busca2.status_code, 200)
        self.assertContains(resp_busca2, 'Degradê Americano')
        self.assertNotContains(resp_busca2, 'Barboterapia Real')

    def test_filtro_pesquisa_clientes_listview(self):
        """A busca GET ?nome=... deve filtrar clientes pelo nome no get_queryset."""
        Cliente.objects.create(usuario=self.user1, nome='Guilherme Santos', telefone='44999990010', email='g@test.com')
        Cliente.objects.create(usuario=self.user1, nome='Rodrigo Ferreira', telefone='44999990020', email='r@test.com')

        self.client.login(username='user_aluno1', password='senha123')

        resp_busca = self.client.get(reverse('listar_clientes'), {'nome': 'Guilherme'})
        self.assertEqual(resp_busca.status_code, 200)
        self.assertContains(resp_busca, 'Guilherme Santos')
        self.assertNotContains(resp_busca, 'Rodrigo Ferreira')

    # --------------------------------------------------------------------------
    # REQUISITO 3: Plugins jQuery (Vídeos #33 e #34)
    # --------------------------------------------------------------------------

    def test_plugins_jquery_carregados_no_template_base(self):
        """jQuery, jQuery Mask e DataTables devem estar referenciados no template."""
        self.client.login(username='user_aluno1', password='senha123')
        resp = self.client.get(reverse('listar_servicos'))

        self.assertEqual(resp.status_code, 200)
        # Verifica jQuery Core
        self.assertContains(resp, 'jquery.min.js')
        # Verifica Plugin 1: jQuery Mask (Vídeo #33)
        self.assertContains(resp, 'jquery.mask.min.js')
        # Verifica Plugin 2: DataTables (Vídeo #34)
        self.assertContains(resp, 'jquery.dataTables.min.js')
        self.assertContains(resp, 'dataTables.bootstrap5.min.js')
        self.assertContains(resp, 'dataTables.bootstrap5.min.css')
        # Verifica se tabela possui classe do datatable
        self.assertContains(resp, 'datatable-custom')
        # Verifica se o formulário de busca por nome está presente
        self.assertContains(resp, 'name="nome"')
