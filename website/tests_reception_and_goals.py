from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from website.models import Barbeiro, PerfilUsuario, MetaBarbeiro


class BarbeiroMetasEditaveisTests(TestCase):
    """Testes para a funcionalidade de metas editáveis por barbeiro e pelo admin (Heitor)."""

    def setUp(self):
        # Barbeiro 1 (Profissional Carlos)
        self.user_carlos = User.objects.create_user(username='barbeiro_carlos', password='pwd')
        PerfilUsuario.objects.create(usuario=self.user_carlos, tipo_usuario='barbeiro', telefone='44999990001')
        self.barbeiro_carlos = Barbeiro.objects.create(usuario=self.user_carlos, nome='Carlos Silva', ativo=True)

        # Barbeiro 2 (Profissional Marcos)
        self.user_marcos = User.objects.create_user(username='barbeiro_marcos', password='pwd')
        PerfilUsuario.objects.create(usuario=self.user_marcos, tipo_usuario='barbeiro', telefone='44999990002')
        self.barbeiro_marcos = Barbeiro.objects.create(usuario=self.user_marcos, nome='Marcos Souza', ativo=True)

        # Heitor: Dono, Administrador e Barbeiro
        self.user_heitor = User.objects.create_user(
            username='heitor_dono', password='pwd',
            is_staff=True, is_superuser=True
        )
        PerfilUsuario.objects.create(usuario=self.user_heitor, tipo_usuario='administrador', telefone='44999990000')
        self.barbeiro_heitor = Barbeiro.objects.create(usuario=self.user_heitor, nome='Heitor Pontes', ativo=True)

    def test_barbeiro_consegue_editar_sua_propria_meta(self):
        """Um barbeiro comum pode definir e alterar a meta que deseja atingir no mês."""
        self.client.login(username='barbeiro_carlos', password='pwd')
        hoje = date.today()

        resp = self.client.post(reverse('barbeiro_metas'), {
            'meta_faturamento': '7500.00',
            'meta_atendimentos': '160',
            'meta_produtos': '35',
            'mes': str(hoje.month),
            'ano': str(hoje.year),
        })

        self.assertRedirects(resp, f"{reverse('barbeiro_metas')}?barbeiro_id={self.barbeiro_carlos.pk}&mes={hoje.month}&ano={hoje.year}")

        meta = MetaBarbeiro.objects.get(barbeiro=self.barbeiro_carlos, mes=hoje.month, ano=hoje.year)
        self.assertEqual(meta.meta_faturamento, Decimal('7500.00'))
        self.assertEqual(meta.meta_atendimentos, 160)
        self.assertEqual(meta.meta_produtos, 35)

    def test_barbeiro_nao_consegue_editar_meta_de_outro_barbeiro(self):
        """Um barbeiro comum não tem permissão para alterar a meta de outro profissional."""
        self.client.login(username='barbeiro_carlos', password='pwd')
        hoje = date.today()

        # Carlos tenta enviar barbeiro_id do Marcos
        self.client.post(reverse('barbeiro_metas'), {
            'barbeiro_id': str(self.barbeiro_marcos.pk),
            'meta_faturamento': '1000.00',
            'meta_atendimentos': '10',
            'meta_produtos': '0',
            'mes': str(hoje.month),
            'ano': str(hoje.year),
        })

        # A alteração é salva no perfil do próprio Carlos, mantendo o Marcos intacto
        self.assertFalse(MetaBarbeiro.objects.filter(barbeiro=self.barbeiro_marcos, mes=hoje.month, ano=hoje.year).exists())
        self.assertTrue(MetaBarbeiro.objects.filter(barbeiro=self.barbeiro_carlos, mes=hoje.month, ano=hoje.year).exists())

    def test_heitor_como_dono_e_admin_consegue_editar_meta_de_qualquer_barbeiro(self):
        """Heitor, com privilégios de administrador, pode editar a meta de qualquer barbeiro da barbearia."""
        self.client.login(username='heitor_dono', password='pwd')
        hoje = date.today()

        resp = self.client.post(reverse('barbeiro_metas'), {
            'barbeiro_id': str(self.barbeiro_marcos.pk),
            'meta_faturamento': '12000.00',
            'meta_atendimentos': '220',
            'meta_produtos': '50',
            'mes': str(hoje.month),
            'ano': str(hoje.year),
        })

        self.assertRedirects(resp, f"{reverse('barbeiro_metas')}?barbeiro_id={self.barbeiro_marcos.pk}&mes={hoje.month}&ano={hoje.year}")

        meta = MetaBarbeiro.objects.get(barbeiro=self.barbeiro_marcos, mes=hoje.month, ano=hoje.year)
        self.assertEqual(meta.meta_faturamento, Decimal('12000.00'))
        self.assertEqual(meta.meta_atendimentos, 220)


class RecepcionistaWorkflowAndSecurityTests(TestCase):
    """Testes para o fluxo, telas permitidas e bloqueios de segurança da Recepcionista."""

    def setUp(self):
        # Criação de Recepcionista
        self.user_recepcao = User.objects.create_user(username='recepcionista_ana', password='pwd')
        self.perfil_recepcao = PerfilUsuario.objects.create(
            usuario=self.user_recepcao,
            tipo_usuario='recepcionista',
            telefone='44999998888'
        )

        # Heitor: Dono, Administrador e Barbeiro
        self.user_heitor = User.objects.create_user(
            username='heitor_master', password='pwd',
            is_staff=True, is_superuser=True
        )
        PerfilUsuario.objects.create(usuario=self.user_heitor, tipo_usuario='administrador', telefone='44999990000')
        self.barbeiro_heitor = Barbeiro.objects.create(usuario=self.user_heitor, nome='Heitor Pontes', ativo=True)

    def test_login_recepcionista_redireciona_direto_para_recepcao(self):
        """Ao fazer login, o perfil de recepcionista deve ir direto para o painel de recepção."""
        self.client.login(username='recepcionista_ana', password='pwd')
        resp = self.client.get(reverse('dashboard'))
        self.assertRedirects(resp, reverse('modo_recepcao'))

    def test_recepcionista_acessa_telas_operacionais_permitidas(self):
        """A recepcionista tem acesso liberado às telas de recepção, clientes, espera e caixa."""
        self.client.login(username='recepcionista_ana', password='pwd')

        # Recepção e fila ao vivo
        resp_recepcao = self.client.get(reverse('modo_recepcao'))
        self.assertEqual(resp_recepcao.status_code, 200)

        # Lista de espera
        resp_waitlist = self.client.get(reverse('admin_waitlist'))
        self.assertEqual(resp_waitlist.status_code, 200)

        # Base de clientes
        resp_clientes = self.client.get(reverse('listar_clientes'))
        self.assertEqual(resp_clientes.status_code, 200)

        # Caixa diário
        resp_caixa = self.client.get(reverse('admin_caixa'))
        self.assertEqual(resp_caixa.status_code, 200)

    def test_recepcionista_bloqueada_em_telas_financeiras_estrategicas(self):
        """A recepcionista NÃO pode visualizar financeiro geral, comissões ou gestão de usuários."""
        self.client.login(username='recepcionista_ana', password='pwd')

        # Financeiro executivo bloqueado
        resp_fin = self.client.get(reverse('admin_financeiro'))
        self.assertRedirects(resp_fin, reverse('pagina_inicial'))

        # Comissões de barbeiros bloqueadas
        resp_com = self.client.get(reverse('admin_comissoes'))
        self.assertRedirects(resp_com, reverse('pagina_inicial'))

        # Cadastro de recepcionistas bloqueado
        resp_rec = self.client.get(reverse('listar_recepcionistas'))
        self.assertRedirects(resp_rec, reverse('pagina_inicial'))

    def test_heitor_tem_acesso_universal_a_tudo(self):
        """Heitor, sendo dono, administrador e barbeiro, pode acessar tanto as telas de gestão quanto a recepção e a cadeira."""
        self.client.login(username='heitor_master', password='pwd')

        telas = [
            'dashboard',
            'admin_financeiro',
            'admin_comissoes',
            'listar_recepcionistas',
            'modo_recepcao',
            'area_barbeiro',
            'barbeiro_metas',
            'listar_clientes',
            'admin_waitlist',
            'admin_caixa'
        ]

        for rota in telas:
            resp = self.client.get(reverse(rota))
            self.assertEqual(resp.status_code, 200, f"Heitor deve ter acesso 200 OK à rota {rota}")
