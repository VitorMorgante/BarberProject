from datetime import date, time, timedelta
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.conf import settings

from website.models import (
    Servico, Produto, PlanoAssinatura, Barbeiro, Cliente,
    EscalaBarbeiro, Agendamento, ItemAgendamento, AssinaturaCliente,
    Comanda, ItemComanda, MovimentacaoCredito, ConfiguracaoEstabelecimento
)
from website.services.agenda_inteligente_service import AgendaInteligenteService
from website.services.subscription_service import SubscriptionService
from website.services.agendamento_service import AgendamentoService


class BarberHeitorRealCatalogTestCase(TestCase):
    """Valida o catálogo canônico confirmado do Barber Heitor."""

    def test_catalogo_servicos_canonicos(self):
        from django.core.management import call_command
        call_command('seed_heitor_real')

        cabelo = Servico.objects.get(codigo='cabelo', ativo=True)
        self.assertEqual(cabelo.nome, 'Cabelo')
        self.assertEqual(cabelo.preco, Decimal('30.00'))
        self.assertEqual(cabelo.duracao_minutos, 30)

        barba = Servico.objects.get(codigo='barba', ativo=True)
        self.assertEqual(barba.nome, 'Barba')
        self.assertEqual(barba.preco, Decimal('20.00'))
        self.assertEqual(barba.duracao_minutos, 20)

        cavanhaque = Servico.objects.get(codigo='cavanhaque', ativo=True)
        self.assertEqual(cavanhaque.nome, 'Cavanhaque')
        self.assertEqual(cavanhaque.preco, Decimal('15.00'))
        self.assertEqual(cavanhaque.duracao_minutos, 15)

        sobrancelha = Servico.objects.get(codigo='sobrancelha', ativo=True)
        self.assertEqual(sobrancelha.nome, 'Sobrancelha')
        self.assertEqual(sobrancelha.preco, Decimal('5.00'))
        self.assertEqual(sobrancelha.duracao_minutos, 10)

        # Apenas os 4 canônicos ativos
        self.assertEqual(Servico.objects.filter(ativo=True).count(), 4)

    def test_catalogo_produtos_confirmados(self):
        from django.core.management import call_command
        call_command('seed_heitor_real')

        p1 = Produto.objects.get(sku='HEITOR-POMADA-FOX', ativo=True)
        self.assertEqual(p1.nome, 'Pomada Fox')
        self.assertEqual(p1.preco, Decimal('20.00'))
        self.assertEqual(p1.estoque_atual, 0)
        self.assertEqual(p1.custo, Decimal('0.00'))

        p2 = Produto.objects.get(sku='HEITOR-POMADA-PO', ativo=True)
        self.assertEqual(p2.nome, 'Pomada em pó')
        self.assertEqual(p2.preco, Decimal('30.00'))

        p3 = Produto.objects.get(sku='HEITOR-SHAMPOO-ANTICASPA', ativo=True)
        self.assertEqual(p3.nome, 'Shampoo anticaspa')
        self.assertEqual(p3.preco, Decimal('30.00'))

        self.assertEqual(Produto.objects.filter(ativo=True).count(), 3)

    def test_planos_confirmados(self):
        from django.core.management import call_command
        call_command('seed_heitor_real')

        p_normal = PlanoAssinatura.objects.get(codigo='plano-normal', ativo=True)
        self.assertEqual(p_normal.preco_mensal, Decimal('80.00'))
        self.assertEqual(p_normal.modalidade, PlanoAssinatura.Modalidade.LIMITADO)
        self.assertEqual(p_normal.limite_mensal, 4)
        self.assertEqual(p_normal.desconto_produtos, Decimal('0.00'))
        nomes_normal = set(p_normal.servicos_inclusos.values_list('codigo', flat=True))
        self.assertEqual(nomes_normal, {'cabelo', 'sobrancelha'})

        p_barba = PlanoAssinatura.objects.get(codigo='plano-com-barba', ativo=True)
        self.assertEqual(p_barba.preco_mensal, Decimal('120.00'))
        self.assertEqual(p_barba.modalidade, PlanoAssinatura.Modalidade.LIMITADO)
        self.assertEqual(p_barba.limite_mensal, 4)
        self.assertEqual(p_barba.desconto_produtos, Decimal('0.00'))
        nomes_barba = set(p_barba.servicos_inclusos.values_list('codigo', flat=True))
        self.assertEqual(nomes_barba, {'cabelo', 'sobrancelha', 'barba'})

        p_inf = PlanoAssinatura.objects.get(codigo='plano-cortes-infinitos', ativo=True)
        self.assertEqual(p_inf.preco_mensal, Decimal('100.00'))
        self.assertEqual(p_inf.modalidade, PlanoAssinatura.Modalidade.ILIMITADO)
        self.assertIsNone(p_inf.limite_mensal)
        nomes_inf = set(p_inf.servicos_inclusos.values_list('codigo', flat=True))
        self.assertEqual(nomes_inf, {'cabelo', 'sobrancelha'})

        self.assertEqual(PlanoAssinatura.objects.filter(ativo=True).count(), 3)


class AgendaInteligenteEngineTestCase(TestCase):
    """Valida grade de 08:00 a 21:30, buffer de 5 min, colisões e folga."""

    def setUp(self):
        self.barbeiro = Barbeiro.objects.create(
            nome='Heitor Pontes',
            ativo=True
        )
        # Escala: 08:00 às 22:40 para todos os dias úteis (segunda = 0)
        self.data_teste = date(2026, 9, 14) # Segunda-feira
        self.escala = EscalaBarbeiro.objects.create(
            barbeiro=self.barbeiro,
            dia_semana=0,
            horario_inicio_1=time(8, 0),
            horario_fim_1=time(22, 40),
            folga=False,
            ativo=True
        )
        self.servico_cabelo = Servico.objects.create(
            codigo='cabelo',
            nome='Cabelo',
            preco=Decimal('30.00'),
            duracao_minutos=30,
            ativo=True
        )
        self.servico_barba = Servico.objects.create(
            codigo='barba',
            nome='Barba',
            preco=Decimal('20.00'),
            duracao_minutos=20,
            ativo=True
        )
        self.servico_sobrancelha = Servico.objects.create(
            codigo='sobrancelha',
            nome='Sobrancelha',
            preco=Decimal('5.00'),
            duracao_minutos=10,
            ativo=True
        )
        self.cliente = Cliente.objects.create(
            nome='Cliente Teste',
            telefone='44999999999'
        )

    def test_faixa_candidatos_0800_a_2130(self):
        slots = AgendaInteligenteService.obter_horarios_com_score(
            data_agendamento=self.data_teste,
            servico=self.servico_cabelo,
            barbeiro=self.barbeiro
        )
        horarios = [s['horario'] for s in slots]

        # Início permitido mínimo é 08:00 e máximo é 21:30
        self.assertIn('08:00', horarios)
        self.assertIn('08:05', horarios)
        self.assertIn('21:30', horarios)

        # Não pode ter candidatos fora da faixa
        self.assertNotIn('07:55', horarios)
        self.assertNotIn('21:35', horarios)
        self.assertNotIn('22:00', horarios)

    def test_agendamento_cabelo_2130_valido(self):
        # Cabelo 30m às 21:30 ocupa até 22:05. Termina antes de 22:40.
        valido = AgendaInteligenteService.validar_e_bloquear_horario(
            barbeiro=self.barbeiro,
            data_agendamento=self.data_teste,
            horario=time(21, 30),
            duracao_minutos=30
        )
        self.assertTrue(valido)

    def test_agendamento_plano_com_barba_2130_valido(self):
        # Plano com barba: 60m às 21:30 ocupa até 22:35. Termina antes de 22:40.
        valido = AgendaInteligenteService.validar_e_bloquear_horario(
            barbeiro=self.barbeiro,
            data_agendamento=self.data_teste,
            horario=time(21, 30),
            duracao_minutos=60
        )
        self.assertTrue(valido)

    def test_colisao_simetrica_com_buffer_5min(self):
        # Agendamento existente das 09:00 (Cabelo 30m). Ocupa 09:00 até 09:35.
        ag = Agendamento.objects.create(
            cliente=self.cliente,
            barbeiro=self.barbeiro,
            servico=self.servico_cabelo,
            data=self.data_teste,
            horario=time(9, 0),
            status=Agendamento.Status.CONFIRMADO
        )
        ItemAgendamento.objects.create(
            agendamento=ag,
            servico=self.servico_cabelo,
            preco_snapshot=self.servico_cabelo.preco,
            duracao_snapshot=self.servico_cabelo.duracao_minutos,
            coberto_por_assinatura=False
        )

        # Candidato 08:30 (Cabelo 30m): ocupa 08:30 até 09:05.
        # Conflita com 09:00 porque 08:30 < 09:35 e 09:05 > 09:00.
        valido_0830 = AgendaInteligenteService.validar_e_bloquear_horario(
            barbeiro=self.barbeiro,
            data_agendamento=self.data_teste,
            horario=time(8, 30),
            duracao_minutos=30
        )
        self.assertFalse(valido_0830)

        # Candidato 08:25 (Cabelo 30m): ocupa 08:25 até 09:00. Não conflita.
        valido_0825 = AgendaInteligenteService.validar_e_bloquear_horario(
            barbeiro=self.barbeiro,
            data_agendamento=self.data_teste,
            horario=time(8, 25),
            duracao_minutos=30
        )
        self.assertTrue(valido_0825)

        # Candidato 09:30 (Cabelo 30m): ocupa 09:30 até 10:05. Conflita com o término do buffer (09:35).
        valido_0930 = AgendaInteligenteService.validar_e_bloquear_horario(
            barbeiro=self.barbeiro,
            data_agendamento=self.data_teste,
            horario=time(9, 30),
            duracao_minutos=30
        )
        self.assertFalse(valido_0930)

        # Candidato 09:35 (Cabelo 30m): ocupa 09:35 até 10:10. Não conflita.
        valido_0935 = AgendaInteligenteService.validar_e_bloquear_horario(
            barbeiro=self.barbeiro,
            data_agendamento=self.data_teste,
            horario=time(9, 35),
            duracao_minutos=30
        )
        self.assertTrue(valido_0935)

    def test_folga_retorna_estritamente_zero_slots(self):
        self.escala.folga = True
        self.escala.save()

        slots = AgendaInteligenteService.obter_horarios_com_score(
            data_agendamento=self.data_teste,
            servico=self.servico_cabelo,
            barbeiro=self.barbeiro
        )
        self.assertEqual(slots, [])

        valido = AgendaInteligenteService.validar_e_bloquear_horario(
            barbeiro=self.barbeiro,
            data_agendamento=self.data_teste,
            horario=time(10, 0),
            duracao_minutos=30
        )
        self.assertFalse(valido)


class ItemAgendamentoAndMultiServiceTestCase(TestCase):
    """Valida criação de ItemAgendamento, snapshots e métodos de duração total."""

    def setUp(self):
        self.barbeiro = Barbeiro.objects.create(nome='Heitor Pontes', ativo=True)
        self.cliente = Cliente.objects.create(nome='Cliente Teste', telefone='44999999999')
        self.cabelo = Servico.objects.create(codigo='cabelo', nome='Cabelo', preco=Decimal('30.00'), duracao_minutos=30, ativo=True)
        self.barba = Servico.objects.create(codigo='barba', nome='Barba', preco=Decimal('20.00'), duracao_minutos=20, ativo=True)

    def test_multi_servico_snapshot(self):
        ag = Agendamento.objects.create(
            cliente=self.cliente,
            barbeiro=self.barbeiro,
            servico=self.cabelo,
            data=date(2026, 9, 15),
            horario=time(10, 0),
            status=Agendamento.Status.CONFIRMADO
        )
        ItemAgendamento.objects.create(
            agendamento=ag,
            servico=self.cabelo,
            preco_snapshot=self.cabelo.preco,
            duracao_snapshot=self.cabelo.duracao_minutos,
            coberto_por_assinatura=False
        )
        ItemAgendamento.objects.create(
            agendamento=ag,
            servico=self.barba,
            preco_snapshot=self.barba.preco,
            duracao_snapshot=self.barba.duracao_minutos,
            coberto_por_assinatura=False
        )

        self.assertEqual(ag.get_duracao_total(), 50)
        self.assertEqual(ag.get_preco_total(), Decimal('50.00'))
        self.assertIn('Cabelo', ag.get_servicos_nomes())
        self.assertIn('Barba', ag.get_servicos_nomes())


class SubscriptionsAndComandaTestCase(TestCase):
    """Valida assinaturas pendentes, planos limitados vs ilimitados e fechamento de comanda."""

    def setUp(self):
        self.barbeiro = Barbeiro.objects.create(nome='Heitor Pontes', ativo=True)
        self.user = User.objects.create_user(username='clitest', password='123')
        self.cliente = Cliente.objects.create(usuario=self.user, nome='Cliente Teste', telefone='44999999999')

        self.cabelo = Servico.objects.create(codigo='cabelo', nome='Cabelo', preco=Decimal('30.00'), duracao_minutos=30, ativo=True)
        self.sobrancelha = Servico.objects.create(codigo='sobrancelha', nome='Sobrancelha', preco=Decimal('5.00'), duracao_minutos=10, ativo=True)
        self.pomada = Produto.objects.create(sku='HEITOR-POMADA-FOX', nome='Pomada Fox', preco=Decimal('20.00'), estoque_atual=10, ativo=True)

        self.plano_normal = PlanoAssinatura.objects.create(
            codigo='plano-normal',
            nome='Plano normal',
            preco_mensal=Decimal('80.00'),
            modalidade=PlanoAssinatura.Modalidade.LIMITADO,
            limite_mensal=4,
            ativo=True
        )
        self.plano_normal.servicos_inclusos.add(self.cabelo, self.sobrancelha)

        self.plano_infinito = PlanoAssinatura.objects.create(
            codigo='plano-cortes-infinitos',
            nome='Plano cortes infinitos',
            preco_mensal=Decimal('100.00'),
            modalidade=PlanoAssinatura.Modalidade.ILIMITADO,
            limite_mensal=None,
            ativo=True
        )
        self.plano_infinito.servicos_inclusos.add(self.cabelo, self.sobrancelha)

    def test_adesao_fica_com_status_pendente(self):
        assinatura = SubscriptionService.solicitar_assinatura(self.cliente, self.plano_normal)
        self.assertEqual(assinatura.status, AssinaturaCliente.Status.PENDENTE)
        self.assertEqual(assinatura.creditos_disponiveis, 0)
        pode, msg = assinatura.pode_utilizar()
        self.assertFalse(pode)

    def test_plano_limitado_bloqueia_apos_limite(self):
        assinatura = SubscriptionService.ativar_ou_renovar_assinatura(self.cliente, self.plano_normal)
        self.assertEqual(assinatura.status, AssinaturaCliente.Status.ATIVA)
        self.assertEqual(assinatura.creditos_disponiveis, 4)

        for _ in range(4):
            pode, _ = assinatura.pode_utilizar()
            self.assertTrue(pode)
            consumido, _ = SubscriptionService.consumir_credito(self.cliente, self.cabelo)
            self.assertTrue(consumido)
            assinatura.refresh_from_db()

        self.assertEqual(assinatura.creditos_disponiveis, 0)
        pode, _ = assinatura.pode_utilizar()
        self.assertFalse(pode)

    def test_plano_ilimitado_nao_bloqueia_apos_quatro_cortes(self):
        assinatura = SubscriptionService.ativar_ou_renovar_assinatura(self.cliente, self.plano_infinito)
        self.assertEqual(assinatura.status, AssinaturaCliente.Status.ATIVA)

        for _ in range(6):
            pode, _ = assinatura.pode_utilizar()
            self.assertTrue(pode)
            consumido, _ = SubscriptionService.consumir_credito(self.cliente, self.cabelo)
            self.assertTrue(consumido)

        assinatura.refresh_from_db()
        pode, _ = assinatura.pode_utilizar()
        self.assertTrue(pode)

    def test_fechamento_comanda_abate_pacote_e_cobra_apenas_excedente(self):
        assinatura = SubscriptionService.ativar_ou_renovar_assinatura(self.cliente, self.plano_normal)

        ag = Agendamento.objects.create(
            cliente=self.cliente,
            barbeiro=self.barbeiro,
            servico=self.cabelo,
            data=date.today(),
            horario=time(14, 0),
            status=Agendamento.Status.EM_ATENDIMENTO
        )
        ItemAgendamento.objects.create(
            agendamento=ag,
            servico=self.cabelo,
            preco_snapshot=self.cabelo.preco,
            duracao_snapshot=self.cabelo.duracao_minutos
        )
        ItemAgendamento.objects.create(
            agendamento=ag,
            servico=self.sobrancelha,
            preco_snapshot=self.sobrancelha.preco,
            duracao_snapshot=self.sobrancelha.duracao_minutos
        )

        comanda = Comanda.objects.create(
            agendamento=ag,
            cliente=self.cliente,
            barbeiro=self.barbeiro,
            status=Comanda.Status.ABERTA
        )
        ItemComanda.objects.create(
            comanda=comanda,
            tipo=ItemComanda.Tipo.SERVICO,
            servico=self.cabelo,
            descricao=self.cabelo.nome,
            quantidade=1,
            preco_unitario=self.cabelo.preco,
            total=self.cabelo.preco
        )
        ItemComanda.objects.create(
            comanda=comanda,
            tipo=ItemComanda.Tipo.SERVICO,
            servico=self.sobrancelha,
            descricao=self.sobrancelha.nome,
            quantidade=1,
            preco_unitario=self.sobrancelha.preco,
            total=self.sobrancelha.preco
        )
        # Produto excedente não coberto (Pomada Fox R$ 20.00)
        ItemComanda.objects.create(
            comanda=comanda,
            tipo=ItemComanda.Tipo.PRODUTO,
            produto=self.pomada,
            descricao=self.pomada.nome,
            quantidade=1,
            preco_unitario=self.pomada.preco,
            total=self.pomada.preco
        )
        comanda.recalcular()
        # Subtotal: 30 + 5 + 20 = 55.00
        self.assertEqual(comanda.subtotal, Decimal('55.00'))

        # Conclusão do atendimento
        AgendamentoService.concluir_atendimento(ag, comanda=comanda)
        comanda.refresh_from_db()

        # Cabelo (30) + Sobrancelha (5) abatidos pelo plano = 35.00
        self.assertEqual(comanda.creditos_abatidos, Decimal('35.00'))
        # Valor a pagar deve ser estritamente o excedente não coberto: R$ 20.00
        self.assertEqual(comanda.valor_total, Decimal('20.00'))


class VisagismoAndBrandAlignmentTestCase(TestCase):
    """Valida redirecionamento de visagismo e canais da marca."""

    def test_redirecionamento_rota_estilo(self):
        client = Client()
        user = User.objects.create_user(username='user_visagismo', password='123')
        client.login(username='user_visagismo', password='123')

        response = client.get(reverse('cliente_estilo'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('servicos'), response['Location'])

    def test_instagram_oficial_configurado(self):
        self.assertEqual(settings.BARBER_INSTAGRAM, 'barber.heitorr')
