import json
from decimal import Decimal
from datetime import time, date, timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from website.models import (
    Servico, Barbeiro, Cliente, HorarioDisponivel, Agendamento,
    PlanoAssinatura, AssinaturaCliente, MovimentacaoCredito,
    ProgramaFidelidade, ProgressoFidelidade, RecompensaFidelidade,
    Produto, MovimentacaoEstoque, Comanda, ItemComanda,
    RegraComissao, Comissao, RepasseComissao, MetaBarbeiro,
    ConfiguracaoEstabelecimento, Pagamento, EventoWebhookPagamento,
    ListaEspera, Notificacao, CupomDesconto
)
from website.services.agendamento_service import AgendamentoService
from website.services.subscription_service import SubscriptionService
from website.services.loyalty_service import LoyaltyService
from website.services.inventory_service import InventoryService
from website.services.comissao_service import ComissaoService
from website.services.payment_service import PaymentService, gerar_pix_copia_e_cola


class TestPublicPages(TestCase):
    """Testa se todas as páginas públicas e PWA retornam HTTP 200."""

    def setUp(self):
        self.barbeiro = Barbeiro.objects.create(
            nome='Danilo Delacruz',
            cargo='Barbeiro',
            especialidade='Cortes clássicos, degradê e acabamento preciso',
            ativo=True,
        )
        self.servico = Servico.objects.create(
            nome='Corte Degradê',
            descricao='Corte masculino com técnica de degradê.',
            preco=Decimal('45.00'),
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

    def test_pwa_manifest(self):
        response = self.client.get(reverse('pwa_manifest'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Delacruz Barber', response.json()['name'])

    def test_pwa_sw(self):
        response = self.client.get(reverse('pwa_sw'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/javascript')


class TestAgendamentoValidation(TestCase):
    """Testa a regra fundamental de unicidade de horário ativo por barbeiro."""

    def setUp(self):
        self.barbeiro = Barbeiro.objects.create(
            nome='Danilo Delacruz',
            cargo='Barbeiro',
            especialidade='Cortes clássicos',
        )
        self.servico = Servico.objects.create(
            nome='Corte Degradê',
            descricao='Corte degradê.',
            preco=Decimal('45.00'),
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
        Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            barbeiro=self.barbeiro,
            data=self.data_futura,
            horario=time(9, 0),
            status=Agendamento.Status.PENDENTE,
        )
        with self.assertRaises(Exception):
            Agendamento.objects.create(
                cliente=self.cliente,
                servico=self.servico,
                barbeiro=self.barbeiro,
                data=self.data_futura,
                horario=time(9, 0),
                status=Agendamento.Status.CONFIRMADO,
            )

    def test_cancelled_then_rebook_allowed(self):
        Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            barbeiro=self.barbeiro,
            data=self.data_futura,
            horario=time(9, 0),
            status=Agendamento.Status.CANCELADO,
        )
        agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            barbeiro=self.barbeiro,
            data=self.data_futura,
            horario=time(9, 0),
            status=Agendamento.Status.PENDENTE,
        )
        self.assertEqual(agendamento.status, Agendamento.Status.PENDENTE)


class TestBarberClubSubscription(TestCase):
    """Testa assinaturas, créditos atômicos e estorno no Barber Club."""

    def setUp(self):
        self.cliente = Cliente.objects.create(nome='Lucas Assinante', telefone='44999991111', email='lucas@email.com')
        self.servico = Servico.objects.create(nome='Corte Classic', preco=Decimal('40.00'), duracao_minutos=30)
        self.plano = PlanoAssinatura.objects.create(
            nome='Delacruz Prime',
            descricao='4 cortes por mês',
            preco_mensal=Decimal('135.00'),
            quantidade_creditos=4,
            ativo=True,
        )
        self.barbeiro = Barbeiro.objects.create(nome='Danilo Delacruz', cargo='Barbeiro')

    def test_ativacao_e_consumo_creditos(self):
        assinatura = SubscriptionService.ativar_ou_renovar_assinatura(self.cliente, self.plano)
        self.assertEqual(assinatura.creditos_disponiveis, 4)
        self.assertEqual(assinatura.status, AssinaturaCliente.Status.ATIVA)

        # Consome 1 crédito
        consumiu = SubscriptionService.consumir_credito(self.cliente, self.servico)
        self.assertTrue(consumiu)

        assinatura.refresh_from_db()
        self.assertEqual(assinatura.creditos_disponiveis, 3)
        self.assertEqual(assinatura.creditos_utilizados, 1)

    def test_saldo_zero_impede_consumo(self):
        assinatura = SubscriptionService.ativar_ou_renovar_assinatura(self.cliente, self.plano)
        assinatura.creditos_disponiveis = 0
        assinatura.save()

        consumiu = SubscriptionService.consumir_credito(self.cliente, self.servico)
        self.assertFalse(consumiu)

    def test_estorno_credito_cancelamento(self):
        assinatura = SubscriptionService.ativar_ou_renovar_assinatura(self.cliente, self.plano)
        agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            barbeiro=self.barbeiro,
            data=date.today() + timedelta(days=2),
            horario=time(10, 0),
            status=Agendamento.Status.CONFIRMADO
        )
        SubscriptionService.consumir_credito(self.cliente, self.servico, agendamento=agendamento)
        assinatura.refresh_from_db()
        self.assertEqual(assinatura.creditos_disponiveis, 3)

        # Cancela e estorna
        AgendamentoService.cancelar_atendimento(agendamento, motivo="Cliente desmarcou")
        assinatura.refresh_from_db()
        self.assertEqual(assinatura.creditos_disponiveis, 4)


class TestFidelidadeDigital(TestCase):
    """Testa fidelidade, acúmulo de pontos e geração de recompensa."""

    def setUp(self):
        self.cliente = Cliente.objects.create(nome='Fiel da Barbearia', telefone='44999992222', email='fiel@email.com')
        self.servico = Servico.objects.create(nome='Corte Degradê', preco=Decimal('45.00'), duracao_minutos=40)
        self.barbeiro = Barbeiro.objects.create(nome='Heitor Pontes', cargo='Barbeiro')
        self.programa = ProgramaFidelidade.objects.create(
            nome='Fidelidade Delacruz',
            servicos_necessarios=10,
            tipo_recompensa='corte_gratis',
            ativo=True
        )

    def test_contagem_e_geracao_recompensa(self):
        progresso = None
        for i in range(10):
            agendamento = Agendamento.objects.create(
                cliente=self.cliente,
                servico=self.servico,
                barbeiro=self.barbeiro,
                data=date.today(),
                horario=time(8 + (i % 10), 0),
                status=Agendamento.Status.CONFIRMADO
            )
            AgendamentoService.concluir_atendimento(agendamento)

        progresso = ProgressoFidelidade.objects.get(cliente=self.cliente)
        self.assertEqual(progresso.total_historico, 10)
        self.assertEqual(progresso.recompensas_acumuladas, 1)

        recompensas = RecompensaFidelidade.objects.filter(cliente=self.cliente, status=RecompensaFidelidade.Status.DISPONIVEL)
        self.assertEqual(recompensas.count(), 1)


class TestInventoryService(TestCase):
    """Testa controle atômico de estoque e impedimento de saldo negativo."""

    def setUp(self):
        self.produto = Produto.objects.create(
            nome='Pomada Matte',
            sku='POM-01',
            preco=Decimal('35.00'),
            custo=Decimal('15.00'),
            estoque_atual=10,
            estoque_minimo=3
        )

    def test_venda_estoque(self):
        mov = InventoryService.movimentar_estoque(self.produto, tipo='venda', quantidade=3)
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.estoque_atual, 7)
        self.assertEqual(mov.saldo_anterior, 10)
        self.assertEqual(mov.saldo_posterior, 7)

    def test_estoque_insuficiente_lanca_erro(self):
        with self.assertRaises(ValidationError):
            InventoryService.movimentar_estoque(self.produto, tipo='venda', quantidade=20)


class TestComissaoService(TestCase):
    """Testa snapshots de comissão e repasses."""

    def setUp(self):
        self.barbeiro = Barbeiro.objects.create(nome='Danilo Delacruz', cargo='Barbeiro')
        RegraComissao.objects.create(
            barbeiro=self.barbeiro,
            percentual_servico=Decimal('50.00'),
            percentual_produto=Decimal('15.00')
        )
        self.cliente = Cliente.objects.create(nome='Cliente Pagante', telefone='44999993333', email='pagante@email.com')
        self.servico = Servico.objects.create(nome='Corte + Barba', preco=Decimal('70.00'), duracao_minutos=60)
        self.produto = Produto.objects.create(nome='Pomada', preco=Decimal('40.00'), estoque_atual=5)

    def test_comissao_servico_e_produto(self):
        agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            barbeiro=self.barbeiro,
            data=date.today(),
            horario=time(14, 0),
            status=Agendamento.Status.CONFIRMADO
        )
        comanda = Comanda.objects.create(
            agendamento=agendamento,
            cliente=self.cliente,
            barbeiro=self.barbeiro,
            subtotal=Decimal('110.00'),
            valor_total=Decimal('110.00')
        )
        ItemComanda.objects.create(
            comanda=comanda,
            tipo=ItemComanda.Tipo.PRODUTO,
            produto=self.produto,
            descricao='Pomada',
            quantidade=1,
            preco_unitario=Decimal('40.00'),
            total=Decimal('40.00')
        )

        AgendamentoService.concluir_atendimento(agendamento, comanda=comanda)

        # Comissão serviço: 50% de 70 = 35.00
        com_serv = Comissao.objects.get(agendamento=agendamento, tipo='servico')
        self.assertEqual(com_serv.valor_comissao, Decimal('35.00'))

        # Comissão produto: 15% de 40 = 6.00
        com_prod = Comissao.objects.get(comanda=comanda, tipo='produto')
        self.assertEqual(com_prod.valor_comissao, Decimal('6.00'))


class TestPaymentAndPix(TestCase):
    """Testa geração de PIX, expiração e webhooks idempotentes."""

    def setUp(self):
        self.cliente = Cliente.objects.create(nome='Cliente PIX', telefone='44999994444', email='pix@email.com')
        self.servico = Servico.objects.create(nome='Corte Classic', preco=Decimal('50.00'), duracao_minutos=30)
        self.barbeiro = Barbeiro.objects.create(nome='Heitor', cargo='Barbeiro')
        self.config = ConfiguracaoEstabelecimento.objects.create(
            id=1,
            tipo_sinal='percentual',
            valor_sinal=Decimal('40.00'), # 40% de 50 = R$ 20,00
            chave_pix='pix@delacruz.com',
            titular_pix='Delacruz',
            cidade_pix='Paranavai'
        )

    def test_calculo_e_geracao_sinal_pix(self):
        sinal = PaymentService.calcular_sinal_agendamento(self.servico, self.config)
        self.assertEqual(sinal, Decimal('20.00'))

        agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            barbeiro=self.barbeiro,
            data=date.today() + timedelta(days=1),
            horario=time(15, 0),
            status=Agendamento.Status.PENDENTE
        )
        pag = PaymentService.criar_pagamento_sinal(agendamento)
        self.assertIsNotNone(pag)
        self.assertEqual(pag.valor, Decimal('20.00'))
        self.assertTrue(len(pag.pix_copia_cola) > 20)

    def test_webhook_idempotente(self):
        agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            barbeiro=self.barbeiro,
            data=date.today() + timedelta(days=1),
            horario=time(16, 0),
            status=Agendamento.Status.PENDENTE
        )
        pag = PaymentService.criar_pagamento_sinal(agendamento)

        payload = {'id': 'EVT-12345', 'external_reference': pag.identificador_interno}
        sucesso1 = PaymentService.processar_webhook(gateway='mercadopago', evento_id='EVT-12345', payload_dict=payload)
        self.assertTrue(sucesso1)

        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, Agendamento.Status.CONFIRMADO)

        # Reprocessamento idempotente
        sucesso2 = PaymentService.processar_webhook(gateway='mercadopago', evento_id='EVT-12345', payload_dict=payload)
        self.assertTrue(sucesso2)


class TestCupomDescontoAndCalendarSync(TestCase):
    """Testa cupons de desconto, validação AJAX e exportação iCalendar (.ics)."""

    def setUp(self):
        self.cupom_perc = CupomDesconto.objects.create(
            codigo='PROMO15',
            tipo=CupomDesconto.Tipo.PERCENTUAL,
            valor=Decimal('15.00'),
            valor_minimo_pedido=Decimal('40.00'),
            ativo=True
        )
        self.cupom_fixo = CupomDesconto.objects.create(
            codigo='MENOS10',
            tipo=CupomDesconto.Tipo.FIXO,
            valor=Decimal('10.00'),
            valor_minimo_pedido=Decimal('30.00'),
            ativo=True
        )
        self.barbeiro = Barbeiro.objects.create(nome='Danilo Delacruz', cargo='Barbeiro')
        self.servico = Servico.objects.create(nome='Corte Degradê', preco=Decimal('50.00'), duracao_minutos=40)
        self.cliente = Cliente.objects.create(nome='Cliente Cupom', telefone='44999995555', email='cupom@email.com')
        self.agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            barbeiro=self.barbeiro,
            data=date.today() + timedelta(days=2),
            horario=time(10, 0),
            status=Agendamento.Status.CONFIRMADO
        )

    def test_calculo_cupom_percentual(self):
        desconto, msg = self.cupom_perc.calcular_desconto(Decimal('100.00'))
        self.assertEqual(desconto, Decimal('15.00'))

    def test_calculo_cupom_fixo(self):
        desconto, msg = self.cupom_fixo.calcular_desconto(Decimal('50.00'))
        self.assertEqual(desconto, Decimal('10.00'))

    def test_cupom_api_endpoint(self):
        response = self.client.get(reverse('api_validar_cupom'), {'codigo': 'PROMO15', 'valor': '50.00'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['valido'])
        self.assertEqual(data['desconto_aplicado'], 7.50)
        self.assertEqual(data['valor_final'], 42.50)

    def test_download_ics_calendar(self):
        response = self.client.get(reverse('agendamento_ics', args=[self.agendamento.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/calendar; charset=utf-8')
        self.assertIn(b'BEGIN:VCALENDAR', response.content)
        self.assertIn(b'Delacruz Barber', response.content)


class TestAreaBarbeiroView(TestCase):
    """Valida que /barbeiro/area/ não gera o erro Cannot filter a query once a slice has been taken."""

    def setUp(self):
        self.user_barbeiro = User.objects.create_user(username='barbeiro_danilo', password='password123')
        self.barbeiro = Barbeiro.objects.create(
            nome='Danilo Delacruz',
            cargo='Barbeiro',
            usuario=self.user_barbeiro
        )
        self.cliente = Cliente.objects.create(nome='Cliente Teste', telefone='44999991234')
        self.servico = Servico.objects.create(nome='Corte', preco=Decimal('40.00'), duracao_minutos=30)
        self.client.login(username='barbeiro_danilo', password='password123')

    def test_area_barbeiro_sem_agendamentos(self):
        response = self.client.get(reverse('area_barbeiro'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['atendimento_atual'])
        self.assertEqual(len(response.context['proximos']), 0)

    def test_area_barbeiro_com_atendimento_em_andamento_e_multiplos(self):
        hoje = date.today()
        # Cria 15 agendamentos com horários distintos para testar o slice de 10
        for i in range(15):
            status = Agendamento.Status.EM_ATENDIMENTO if i == 0 else Agendamento.Status.CONFIRMADO
            Agendamento.objects.create(
                cliente=self.cliente,
                barbeiro=self.barbeiro,
                servico=self.servico,
                data=hoje,
                horario=time(8 + (i // 2), (i % 2) * 30),
                status=status
            )

        response = self.client.get(reverse('area_barbeiro'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['atendimento_atual'])
        self.assertEqual(response.context['atendimento_atual'].status, Agendamento.Status.EM_ATENDIMENTO)
        self.assertEqual(len(response.context['proximos']), 10)


class TestAgendaInteligenteService(TestCase):
    """Testes do motor de agendamento inteligente, scoring de slots, check-in e fila."""

    def setUp(self):
        self.barbeiro = Barbeiro.objects.create(nome='Danilo Delacruz', cargo='Master', ativo=True)
        self.servico = Servico.objects.create(nome='Corte Premium', preco=Decimal('50.00'), duracao_minutos=30, ativo=True)
        self.cliente = Cliente.objects.create(nome='Lucas Silva', telefone='4499887766')

    def test_calcular_score_no_show_novo_cliente(self):
        from website.services.agenda_inteligente_service import AgendaInteligenteService
        score = AgendaInteligenteService.calcular_score_no_show(self.cliente)
        self.assertEqual(score, 30)  # Risco moderado padrão para novos clientes

    def test_calcular_score_no_show_cliente_com_falta(self):
        from website.services.agenda_inteligente_service import AgendaInteligenteService
        Agendamento.objects.create(
            cliente=self.cliente, barbeiro=self.barbeiro, servico=self.servico,
            data=date.today() - timedelta(days=5), horario=time(10, 0),
            status=Agendamento.Status.NAO_COMPARECEU
        )
        score = AgendaInteligenteService.calcular_score_no_show(self.cliente)
        self.assertEqual(score, 95)

    def test_obter_horarios_com_score_e_checkin(self):
        from website.services.agenda_inteligente_service import AgendaInteligenteService
        amanha = date.today() + timedelta(days=1)
        slots = AgendaInteligenteService.obter_horarios_com_score(amanha, self.servico, self.barbeiro, self.cliente)
        self.assertTrue(len(slots) > 0)
        self.assertIn('score', slots[0])
        self.assertIn('horario', slots[0])

        # Teste de Check-in
        ag = Agendamento.objects.create(
            cliente=self.cliente, barbeiro=self.barbeiro, servico=self.servico,
            data=date.today(), horario=time(14, 0), status=Agendamento.Status.CONFIRMADO
        )
        sucesso = AgendaInteligenteService.registrar_checkin(ag)
        self.assertTrue(sucesso)
        ag.refresh_from_db()
        self.assertEqual(ag.status, Agendamento.Status.AGUARDANDO)
        self.assertIsNotNone(ag.checkin_em)

    def test_obter_fila_tempo_real(self):
        from website.services.agenda_inteligente_service import AgendaInteligenteService
        hoje = date.today()
        ag1 = Agendamento.objects.create(
            cliente=self.cliente, barbeiro=self.barbeiro, servico=self.servico,
            data=hoje, horario=time(14, 0), status=Agendamento.Status.EM_ATENDIMENTO
        )
        cliente2 = Cliente.objects.create(nome='Marcos Paulo', telefone='449112233')
        ag2 = Agendamento.objects.create(
            cliente=cliente2, barbeiro=self.barbeiro, servico=self.servico,
            data=hoje, horario=time(14, 30), status=Agendamento.Status.AGUARDANDO,
            checkin_em=timezone.now()
        )
        fila = AgendaInteligenteService.obter_fila_tempo_real()
        self.assertEqual(len(fila['em_atendimento']), 1)
        self.assertEqual(fila['total_fila'], 1)


class TestCRMService(TestCase):
    """Testes do CRM 360, cálculo de LTV, previsão de retorno e bônus de indicação."""

    def setUp(self):
        self.barbeiro = Barbeiro.objects.create(nome='Danilo Delacruz', cargo='Master', ativo=True)
        self.servico = Servico.objects.create(nome='Corte Tradicional', preco=Decimal('45.00'), duracao_minutos=30, ativo=True)
        self.indicador = Cliente.objects.create(nome='Pedro Indicador', telefone='44988112233')
        self.cliente = Cliente.objects.create(nome='Thiago Novo', telefone='44988445566', indicado_por=self.indicador)

    def test_metricas_cliente_e_ltv(self):
        from website.services.crm_service import CRMService
        # Conclui 2 cortes para o cliente
        ag1 = Agendamento.objects.create(
            cliente=self.cliente, barbeiro=self.barbeiro, servico=self.servico,
            data=date.today() - timedelta(days=20), horario=time(10, 0),
            status=Agendamento.Status.CONCLUIDO
        )
        ag2 = Agendamento.objects.create(
            cliente=self.cliente, barbeiro=self.barbeiro, servico=self.servico,
            data=date.today(), horario=time(10, 0),
            status=Agendamento.Status.CONCLUIDO
        )
        Comanda.objects.create(
            cliente=self.cliente, barbeiro=self.barbeiro, agendamento=ag1,
            subtotal=Decimal('45.00'), valor_total=Decimal('45.00'), status=Comanda.Status.FECHADA
        )
        Comanda.objects.create(
            cliente=self.cliente, barbeiro=self.barbeiro, agendamento=ag2,
            subtotal=Decimal('45.00'), valor_total=Decimal('45.00'), status=Comanda.Status.FECHADA
        )

        metricas = CRMService.calcular_metricas_cliente(self.cliente)
        self.assertEqual(metricas['total_cortes'], 2)
        self.assertEqual(metricas['ltv_realizado'], Decimal('90.00'))
        self.assertEqual(metricas['freq_media_dias'], 20)
        self.assertFalse(metricas['is_em_risco'])

    def test_recompensa_indicacao_idempotente(self):
        from website.services.crm_service import CRMService
        from website.models import ContaCorrenteCliente
        ag = Agendamento.objects.create(
            cliente=self.cliente, barbeiro=self.barbeiro, servico=self.servico,
            data=date.today(), horario=time(11, 0),
            status=Agendamento.Status.CONCLUIDO
        )
        # Primeiro disparo: concede R$ 15,00 ao indicador
        concedido = CRMService.processar_recompensa_indicacao(ag)
        self.assertTrue(concedido)
        conta = ContaCorrenteCliente.objects.get(cliente=self.indicador)
        self.assertEqual(conta.saldo, Decimal('15.00'))

        # Segundo disparo idêntico: garante idempotência sem duplicar saldo
        concedido_segundo = CRMService.processar_recompensa_indicacao(ag)
        self.assertFalse(concedido_segundo)
        conta.refresh_from_db()
        self.assertEqual(conta.saldo, Decimal('15.00'))


class TestFinanceService(TestCase):
    """Testes do Caixa Diário, DRE e Simuladores Financeiros."""

    def setUp(self):
        self.user = User.objects.create_user(username='gerente', password='123')
        self.barbeiro = Barbeiro.objects.create(nome='Danilo Delacruz', cargo='Master', ativo=True)
        self.servico = Servico.objects.create(nome='Corte', preco=Decimal('50.00'), duracao_minutos=30, ativo=True)

    def test_ciclo_caixa_diario(self):
        from website.services.finance_service import FinanceService
        from website.models import CaixaDiario, MovimentacaoCaixa
        caixa = FinanceService.abrir_caixa(operador=self.user, saldo_inicial=Decimal('150.00'))
        self.assertEqual(caixa.status, CaixaDiario.Status.ABERTO)
        self.assertEqual(caixa.saldo_esperado, Decimal('150.00'))

        # Sangria de R$ 30,00
        FinanceService.registrar_movimentacao_caixa(caixa, tipo=MovimentacaoCaixa.Tipo.SANGRIA, valor=Decimal('30.00'), motivo='Água mineral')
        caixa.refresh_from_db()
        self.assertEqual(caixa.saldo_esperado, Decimal('120.00'))

        # Fechamento com R$ 120,00 (diferença zero)
        caixa_fechado = FinanceService.fechar_caixa(caixa, saldo_informado=Decimal('120.00'))
        self.assertEqual(caixa_fechado.status, CaixaDiario.Status.FECHADO)
        self.assertEqual(caixa_fechado.diferenca_quebra, Decimal('0.00'))

    def test_simulador_preco(self):
        from website.services.finance_service import FinanceService
        sim = FinanceService.simular_reajuste_preco(self.servico.id, novo_preco=Decimal('60.00'))
        self.assertEqual(sim['novo_preco'], Decimal('60.00'))
        self.assertTrue(sim['impacto_faturamento'] > 0)


class TestAIAssistantService(TestCase):
    """Testes do assistente virtual de agendamento em linguagem natural conectado ao banco real."""

    def setUp(self):
        self.barbeiro = Barbeiro.objects.create(nome='Danilo Delacruz', cargo='Master', ativo=True)
        self.servico = Servico.objects.create(nome='Corte Degradê', preco=Decimal('45.00'), duracao_minutos=30, ativo=True)

    def test_interpretador_mensagem_agendamento(self):
        from website.services.ai_assistant_service import AIAssistantService
        res = AIAssistantService.processar_mensagem_agendamento("Quero cortar amanhã depois das 14h com o Danilo")
        self.assertIn('resposta', res)
        self.assertEqual(res['servico_nome'], 'Corte Degradê')
        self.assertEqual(res['barbeiro_nome'], 'Danilo Delacruz')
        self.assertTrue(len(res['horarios_disponiveis']) > 0)

    def test_consulta_gestao_real(self):
        from website.services.ai_assistant_service import AIAssistantService
        resposta = AIAssistantService.responder_consulta_gestao("Quanto faturamos esta semana?")
        self.assertIn("Faturamento desta semana", resposta)


class TestSplitPaymentsAndConsumableKits(TestCase):
    """Testes de pagamento dividido (PIX + Dinheiro) e baixa de insumos (Kit de Consumo)."""

    def setUp(self):
        self.barbeiro = Barbeiro.objects.create(nome='Danilo Delacruz', cargo='Master', ativo=True)
        self.servico = Servico.objects.create(nome='Barba Completa', preco=Decimal('40.00'), duracao_minutos=30, ativo=True)
        self.cliente = Cliente.objects.create(nome='Renato Souza', telefone='449776655')
        self.insumo = Produto.objects.create(
            nome='Lâmina Descartável', preco=Decimal('0.00'), custo=Decimal('0.80'),
            estoque_atual=20, estoque_minimo=5, is_insumo_interno=True, ativo=True
        )
        from website.models import KitConsumoServico, ItemKitConsumo
        kit = KitConsumoServico.objects.create(servico=self.servico, ativo=True)
        ItemKitConsumo.objects.create(kit=kit, produto_insumo=self.insumo, quantidade_unitaria=Decimal('1.00'))

    def test_conclusao_atendimento_baixa_insumo(self):
        ag = Agendamento.objects.create(
            cliente=self.cliente, barbeiro=self.barbeiro, servico=self.servico,
            data=date.today(), horario=time(15, 0), status=Agendamento.Status.CONFIRMADO
        )
        AgendamentoService.iniciar_atendimento(ag)
        ag.refresh_from_db()
        self.assertEqual(ag.status, Agendamento.Status.EM_ATENDIMENTO)
        self.assertIsNotNone(ag.inicio_real)

        AgendamentoService.concluir_atendimento(ag)
        ag.refresh_from_db()
        self.assertEqual(ag.status, Agendamento.Status.CONCLUIDO)
        self.assertIsNotNone(ag.fim_real)

        self.insumo.refresh_from_db()
        self.assertEqual(self.insumo.estoque_atual, 19)  # 20 - 1 lâmina consumida

    def test_pagamento_dividido_comanda(self):
        from website.models import PagamentoDividido
        comanda = Comanda.objects.create(
            cliente=self.cliente, barbeiro=self.barbeiro,
            subtotal=Decimal('60.00'), valor_total=Decimal('60.00'), status=Comanda.Status.ABERTA
        )
        pagamentos_info = [
            {'metodo': 'pix', 'valor': Decimal('30.00')},
            {'metodo': 'dinheiro', 'valor': Decimal('30.00')}
        ]
        PaymentService.registrar_pagamento_dividido(comanda, pagamentos_info, gorjeta_valor=Decimal('5.00'))
        comanda.refresh_from_db()
        self.assertEqual(comanda.status, Comanda.Status.FECHADA)
        self.assertEqual(comanda.pagamentos_divididos.count(), 2)
        self.assertEqual(comanda.gorjetas.count(), 1)
        self.assertEqual(comanda.gorjetas.first().valor, Decimal('5.00'))


class TestLGPDAndViews(TestCase):
    """Testes de endpoints LGPD, Modo Recepção, Modo TV e Cardápio Digital."""

    def setUp(self):
        self.user = User.objects.create_user(username='cliente_teste', password='password123')
        self.cliente = Cliente.objects.create(usuario=self.user, nome='Cliente LGPD', telefone='4491234567')

    def test_cardapio_digital_view(self):
        response = self.client.get(reverse('cardapio_digital'))
        self.assertEqual(response.status_code, 200)

    def test_modo_tv_view(self):
        response = self.client.get(reverse('modo_tv'))
        self.assertEqual(response.status_code, 200)

    def test_central_lgpd_export_json(self):
        self.client.login(username='cliente_teste', password='password123')
        response = self.client.get(reverse('exportar_lgpd'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')
        data = response.json()
        self.assertEqual(data['titular']['nome'], 'Cliente LGPD')

