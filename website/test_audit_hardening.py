import json
from datetime import date, time, datetime, timedelta
from decimal import Decimal
from django.test import TestCase, Client as TestClient
from django.urls import reverse
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.utils import timezone

from website.models import (
    Servico, Barbeiro, Cliente, Agendamento, Comanda, ItemComanda,
    PlanoAssinatura, AssinaturaCliente, MovimentacaoCredito,
    ProgramaFidelidade, ProgressoFidelidade, RecompensaFidelidade,
    Produto, SaldoEstoqueLocal, LocalEstoque, MovimentacaoEstoque,
    KitConsumoServico, ItemKitConsumo, PerfilUsuario, Feedback,
    HistoricoVisualCliente, FichaTecnicaCorte, CaixaDiario,
    MovimentacaoCaixa, CupomDesconto, Pagamento, PagamentoDividido,
    ConfiguracaoEstabelecimento, ConsentimentoCliente, ListaEspera,
    RegraAutomacao, TaxaMetodoPagamento
)
from website.services.agendamento_service import AgendamentoService
from website.services.subscription_service import SubscriptionService
from website.services.loyalty_service import LoyaltyService
from website.services.inventory_service import InventoryService
from website.services.payment_service import PaymentService
from website.services.crm_service import CRMService
from website.services.finance_service import FinanceService
from website.services.agenda_inteligente_service import AgendaInteligenteService
from website.services.automation_service import AutomationService
from website.services.comissao_service import ComissaoService


from django.core.exceptions import ValidationError

class SecurityAuthorizationIDORTests(TestCase):
    """Testes de segurança contra IDOR, CSRF e controle de acesso baseado em funções (RBAC)."""

    def setUp(self):
        self.user_client1 = User.objects.create_user(username='cliente1', password='password123')
        self.cliente1 = Cliente.objects.create(usuario=self.user_client1, nome='Cliente Um', email='c1@test.com', telefone='44999990001')

        self.user_client2 = User.objects.create_user(username='cliente2', password='password123')
        self.cliente2 = Cliente.objects.create(usuario=self.user_client2, nome='Cliente Dois', email='c2@test.com', telefone='44999990002')

        self.user_barber1 = User.objects.create_user(username='barbeiro1', password='password123')
        PerfilUsuario.objects.create(usuario=self.user_barber1, tipo_usuario='barbeiro', telefone='44999990003')
        self.barbeiro1 = Barbeiro.objects.create(usuario=self.user_barber1, nome='Barbeiro Um', especialidade='Cortes Clássicos', ativo=True)

        self.user_barber2 = User.objects.create_user(username='barbeiro2', password='password123')
        PerfilUsuario.objects.create(usuario=self.user_barber2, tipo_usuario='barbeiro', telefone='44999990004')
        self.barbeiro2 = Barbeiro.objects.create(usuario=self.user_barber2, nome='Barbeiro Dois', especialidade='Degradê', ativo=True)

        self.admin_user = User.objects.create_superuser(username='admin', password='password123', email='admin@test.com')
        PerfilUsuario.objects.create(usuario=self.admin_user, tipo_usuario='administrador', telefone='44999990000')

        self.servico = Servico.objects.create(nome='Corte Executivo', preco=Decimal('50.00'), duracao_minutos=40, ativo=True)

        self.agendamento_barber2 = Agendamento.objects.create(
            cliente=self.cliente2,
            servico=self.servico,
            barbeiro=self.barbeiro2,
            data=date.today() + timedelta(days=1),
            horario=time(14, 0),
            status=Agendamento.Status.CONFIRMADO
        )

        self.comanda_barber2 = Comanda.objects.create(
            agendamento=self.agendamento_barber2,
            cliente=self.cliente2,
            barbeiro=self.barbeiro2,
            subtotal=self.servico.preco,
            valor_total=self.servico.preco,
            status=Comanda.Status.ABERTA
        )

    def test_reagendar_drag_drop_api_rejects_unauthenticated(self):
        """API de drag and drop deve recusar chamadas não autenticadas (HTTP 401)."""
        response = self.client.post(
            reverse('api_reagendar_dragdrop'),
            data=json.dumps({
                'agendamento_id': self.agendamento_barber2.id,
                'nova_data': str(date.today() + timedelta(days=2)),
                'novo_horario': '15:00',
                'novo_barbeiro_id': self.barbeiro1.id
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)

    def test_reagendar_drag_drop_api_rejects_unauthorized_client_or_other_barber(self):
        """Cliente comum ou barbeiro não atribuído não pode remarcar agendamento alheio."""
        self.client.login(username='cliente1', password='password123')
        response = self.client.post(
            reverse('api_reagendar_dragdrop'),
            data=json.dumps({
                'agendamento_id': self.agendamento_barber2.id,
                'nova_data': str(date.today() + timedelta(days=2)),
                'novo_horario': '15:00',
                'novo_barbeiro_id': self.barbeiro1.id
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_barbeiro_comanda_idor_protection(self):
        """Barbeiro 1 não pode acessar ou manipular comanda do Barbeiro 2."""
        self.client.login(username='barbeiro1', password='password123')
        response = self.client.get(reverse('barbeiro_comanda', kwargs={'pk': self.agendamento_barber2.id}))
        # Deve redirecionar para a área do barbeiro com mensagem de acesso negado
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('area_barbeiro'), response.url)

    def test_barbeiro_foto_resultado_idor_protection(self):
        """Barbeiro 1 não pode anexar foto ao atendimento do Barbeiro 2."""
        self.client.login(username='barbeiro1', password='password123')
        response = self.client.get(reverse('barbeiro_foto_resultado', kwargs={'pk': self.agendamento_barber2.id}))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('agendamentos_barbeiro'), response.url)

    def test_iniciar_atendimento_barbeiro_idor_protection(self):
        """Barbeiro 1 não pode iniciar o atendimento do Barbeiro 2."""
        self.client.login(username='barbeiro1', password='password123')
        response = self.client.post(reverse('barbeiro_iniciar_atendimento', kwargs={'pk': self.agendamento_barber2.id}))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('area_barbeiro'), response.url)
        # O status não deve ter sido alterado para 'Em Atendimento'
        self.agendamento_barber2.refresh_from_db()
        self.assertEqual(self.agendamento_barber2.status, Agendamento.Status.CONFIRMADO)

    def test_fechar_comanda_dividida_access_control(self):
        """Cliente comum não tem autorização para fechar comandas."""
        self.client.login(username='cliente1', password='password123')
        response = self.client.post(
            reverse('fechar_comanda_dividida', kwargs={'pk': self.comanda_barber2.id}),
            data={'metodo[]': ['pix'], 'valor[]': ['50.00'], 'gorjeta': '0.00'}
        )
        self.assertEqual(response.status_code, 302)
        self.comanda_barber2.refresh_from_db()
        self.assertEqual(self.comanda_barber2.status, Comanda.Status.ABERTA)

    def test_ficha_tecnica_access_control(self):
        """Cliente comum não pode criar fichas técnicas arbitrárias."""
        self.client.login(username='cliente1', password='password123')
        response = self.client.post(
            reverse('salvar_ficha_tecnica', kwargs={'cliente_id': self.cliente2.id}),
            data={'maquina_lateral': '1.0', 'comprimento_topo': 'Tesoura'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(FichaTecnicaCorte.objects.filter(cliente=self.cliente2).count(), 0)

    def test_caixa_diario_access_control(self):
        """Cliente comum não pode abrir ou fechar caixas da barbearia."""
        self.client.login(username='cliente1', password='password123')
        response = self.client.post(reverse('admin_caixa'), data={'acao': 'abrir', 'saldo_inicial': '200.00'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CaixaDiario.objects.count(), 0)

    def test_feedback_idor_protection(self):
        """Cliente 1 não pode enviar avaliação de agendamento pertencente ao Cliente 2."""
        self.agendamento_barber2.status = Agendamento.Status.CONCLUIDO
        self.agendamento_barber2.save()

        self.client.login(username='cliente1', password='password123')
        response = self.client.get(reverse('criar_feedback', kwargs={'pk': self.agendamento_barber2.id}))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('area_cliente'), response.url)

        post_response = self.client.post(
            reverse('criar_feedback', kwargs={'pk': self.agendamento_barber2.id}),
            data={'nota': 5, 'comentario': 'Tentativa IDOR'}
        )
        self.assertEqual(post_response.status_code, 302)
        self.assertEqual(Feedback.objects.filter(agendamento=self.agendamento_barber2).count(), 0)

    def test_download_ics_access_control(self):
        """Usuário não autorizado não pode fazer download do arquivo ICS de outro cliente."""
        self.client.login(username='cliente1', password='password123')
        response = self.client.get(reverse('agendamento_ics', kwargs={'pk': self.agendamento_barber2.id}))
        self.assertEqual(response.status_code, 403)


class IdempotencyAndConcurrencyHardeningTests(TestCase):
    """Testes de idempotência em estornos, conclusão de atendimentos e concorrência de reservas."""

    def setUp(self):
        self.user = User.objects.create_user(username='clube_user', password='password123')
        self.cliente = Cliente.objects.create(usuario=self.user, nome='Assinante Teste', email='sub@test.com', telefone='44999998888')

        self.barbeiro = Barbeiro.objects.create(nome='Barbeiro Chefe', especialidade='Todos', ativo=True)
        self.servico = Servico.objects.create(nome='Corte + Barba', preco=Decimal('70.00'), duracao_minutos=50, ativo=True)

        self.plano = PlanoAssinatura.objects.create(
            nome='Plano Ouro VIP',
            descricao='Plano Ouro com 4 cortes mensais',
            preco_mensal=Decimal('120.00'),
            quantidade_creditos=4,
            ativo=True
        )
        self.plano.servicos.add(self.servico)

        self.assinatura = AssinaturaCliente.objects.create(
            cliente=self.cliente,
            plano=self.plano,
            data_inicio=date.today(),
            data_renovacao=date.today() + timedelta(days=30),
            creditos_disponiveis=4,
            creditos_utilizados=0,
            status=AssinaturaCliente.Status.ATIVA
        )

        self.agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            barbeiro=self.barbeiro,
            data=date.today() + timedelta(days=3),
            horario=time(10, 0),
            status=Agendamento.Status.CONFIRMADO
        )

    def test_subscription_estorno_idempotency(self):
        """Chamadas repetidas de estorno de crédito não podem conceder créditos infinitos."""
        # 1. Consome crédito para o agendamento
        sucesso_consumo = SubscriptionService.consumir_credito(self.cliente, self.servico, self.agendamento)
        self.assertTrue(sucesso_consumo)
        self.assinatura.refresh_from_db()
        self.assertEqual(self.assinatura.creditos_disponiveis, 3)
        self.assertEqual(self.assinatura.creditos_utilizados, 1)

        # 2. Primeiro estorno (válido)
        primeiro_estorno = SubscriptionService.estornar_credito(self.agendamento)
        self.assertTrue(primeiro_estorno)
        self.assinatura.refresh_from_db()
        self.assertEqual(self.assinatura.creditos_disponiveis, 4)
        self.assertEqual(self.assinatura.creditos_utilizados, 0)

        # 3. Segundo estorno para o mesmo agendamento (deve falhar por idempotência)
        segundo_estorno = SubscriptionService.estornar_credito(self.agendamento)
        self.assertFalse(segundo_estorno)
        self.assinatura.refresh_from_db()
        self.assertEqual(self.assinatura.creditos_disponiveis, 4)  # Permanece 4, não 5!
        self.assertEqual(self.assinatura.creditos_utilizados, 0)

        # 4. Terceiro estorno (deve falhar também)
        terceiro_estorno = SubscriptionService.estornar_credito(self.agendamento)
        self.assertFalse(terceiro_estorno)
        self.assinatura.refresh_from_db()
        self.assertEqual(self.assinatura.creditos_disponiveis, 4)

    def test_concluir_atendimento_idempotency(self):
        """Conclusão repetida do mesmo agendamento não duplica comissões, pontos de fidelidade nem baixa de estoque."""
        produto = Produto.objects.create(
            nome='Pomada Efeito Seco',
            preco=Decimal('40.00'),
            custo=Decimal('15.00'),
            estoque_atual=10,
            estoque_minimo=2,
            ativo=True
        )

        comanda = Comanda.objects.create(
            agendamento=self.agendamento,
            cliente=self.cliente,
            barbeiro=self.barbeiro,
            subtotal=Decimal('110.00'),
            valor_total=Decimal('110.00'),
            status=Comanda.Status.ABERTA
        )
        ItemComanda.objects.create(
            comanda=comanda,
            tipo=ItemComanda.Tipo.SERVICO,
            servico=self.servico,
            descricao=self.servico.nome,
            quantidade=1,
            preco_unitario=self.servico.preco,
            total=self.servico.preco
        )
        ItemComanda.objects.create(
            comanda=comanda,
            tipo=ItemComanda.Tipo.PRODUTO,
            produto=produto,
            descricao=produto.nome,
            quantidade=1,
            preco_unitario=produto.preco,
            total=produto.preco
        )

        # 1. Primeira conclusão
        AgendamentoService.concluir_atendimento(self.agendamento, comanda=comanda)
        self.agendamento.refresh_from_db()
        produto.refresh_from_db()
        self.assertEqual(self.agendamento.status, Agendamento.Status.CONCLUIDO)
        self.assertEqual(produto.estoque_atual, 9)

        total_comissoes_inicial = self.agendamento.comissoes.count()
        self.assertGreater(total_comissoes_inicial, 0)

        # 2. Segunda conclusão acidental (e.g. duplo clique ou replay de webhook)
        AgendamentoService.concluir_atendimento(self.agendamento, comanda=comanda)
        produto.refresh_from_db()
        self.assertEqual(produto.estoque_atual, 9)  # Não pode decrementar para 8!
        self.assertEqual(self.agendamento.comissoes.count(), total_comissoes_inicial)  # Não pode duplicar comissão!

    def test_concorrencia_horario_duplo_agendamento(self):
        """O banco de dados deve rejeitar com UniqueConstraint reservas simultâneas no mesmo barbeiro/data/horário."""
        with self.assertRaises(IntegrityError):
            Agendamento.objects.create(
                cliente=self.cliente,
                servico=self.servico,
                barbeiro=self.barbeiro,
                data=self.agendamento.data,
                horario=self.agendamento.horario,
                status=Agendamento.Status.CONFIRMADO
            )


class PerformanceAndQueryOptimizationTests(TestCase):
    """Testes de perfilamento de queries SQL e eliminação de N+1 no CRM e relatórios."""

    def setUp(self):
        self.barbeiro = Barbeiro.objects.create(nome='Barbeiro Senior', especialidade='Cortes', ativo=True)
        self.servico = Servico.objects.create(nome='Corte Regular', preco=Decimal('45.00'), duracao_minutos=30, ativo=True)

        # Cria 15 clientes com agendamentos concluídos
        self.clientes = []
        for i in range(15):
            c = Cliente.objects.create(
                nome=f'Cliente {i}',
                email=f'c{i}@perf.test',
                telefone=f'449999910{i:02d}',
                data_nascimento=date(1990, date.today().month, 15)
            )
            self.clientes.append(c)

            # Agendamento concluído
            ag = Agendamento.objects.create(
                cliente=c,
                servico=self.servico,
                barbeiro=self.barbeiro,
                data=date.today() - timedelta(days=i * 2 + 1),
                horario=time(9 + (i % 8), 0),
                status=Agendamento.Status.CONCLUIDO
            )
            # Comanda fechada
            Comanda.objects.create(
                agendamento=ag,
                cliente=c,
                barbeiro=self.barbeiro,
                subtotal=self.servico.preco,
                valor_total=self.servico.preco,
                status=Comanda.Status.FECHADA
            )

    def test_crm_obter_segmentos_is_bounded_and_fast(self):
        """CRMService.obter_segmentos_clientes deve rodar em no máximo 4 queries constantes (sem N+1)."""
        with self.assertNumQueries(4):
            resultado = CRMService.obter_segmentos_clientes()

        self.assertEqual(resultado['total_clientes'], 15)
        self.assertEqual(len(resultado['aniversariantes']), 15)

    def test_automation_resumo_executivo_dia_queries(self):
        """AutomationService.obter_resumo_executivo_dia deve usar agregações otimizadas do DB (3 queries)."""
        # Cria alguns agendamentos para hoje
        for i in range(3):
            Agendamento.objects.create(
                cliente=self.clientes[i],
                servico=self.servico,
                barbeiro=self.barbeiro,
                data=date.today(),
                horario=time(14 + i, 0),
                status=Agendamento.Status.CONFIRMADO
            )

        with self.assertNumQueries(3):
            resumo = AutomationService.obter_resumo_executivo_dia()

        self.assertEqual(resumo['total_agendamentos'], 3)
        self.assertEqual(resumo['faturamento_previsto'], Decimal('135.00'))


class BusinessRulesAndBoundaryValuesTests(TestCase):
    """Testes de regras de negócio, limites de cupom, precisão decimal e estoque negativo."""

    def setUp(self):
        self.cliente = Cliente.objects.create(nome='Cliente Regras', email='regras@test.com', telefone='44998877665')
        self.produto = Produto.objects.create(
            nome='Shampoo Antiqueda',
            preco=Decimal('60.00'),
            custo=Decimal('25.00'),
            estoque_atual=2,
            estoque_minimo=1,
            ativo=True
        )

    def test_negative_stock_prevention(self):
        """Tentativa de vender mais do que o estoque disponível deve lançar ValidationError de saldo insuficiente."""
        with self.assertRaises(ValidationError):
            InventoryService.movimentar_estoque(
                produto=self.produto,
                tipo='venda',
                quantidade=5,  # Tem apenas 2
                motivo="Tentativa de estoque negativo"
            )

        self.produto.refresh_from_db()
        self.assertEqual(self.produto.estoque_atual, 2)

    def test_cupom_desconto_boundary_and_usage_limits(self):
        """Validação de cupom respeita data de validade, valor mínimo e limite de usos."""
        cupom = CupomDesconto.objects.create(
            codigo='PROMO50',
            tipo=CupomDesconto.Tipo.FIXO,
            valor=Decimal('50.00'),
            valor_minimo_pedido=Decimal('100.00'),
            limite_usos=1,
            usos_atuais=0,
            valido_ate=date.today() + timedelta(days=1),
            ativo=True
        )

        # Abaixo do valor mínimo
        valido, msg = cupom.is_valido(Decimal('80.00'))
        self.assertFalse(valido)

        # Valor atingido
        valido, msg = cupom.is_valido(Decimal('120.00'))
        self.assertTrue(valido)

        # Consome o único uso
        cupom.usos_atuais = 1
        cupom.save()

        # Agora deve ser rejeitado por limite atingido
        valido, msg = cupom.is_valido(Decimal('120.00'))
        self.assertFalse(valido)
        self.assertIn('Limite de usos', msg)

    def test_financial_split_payment_sum(self):
        """Pagamento dividido com múltiplos métodos e gorjeta calcula taxas e total com precisão exata."""
        barbeiro = Barbeiro.objects.create(nome='Barbeiro Financeiro', ativo=True)
        comanda = Comanda.objects.create(
            cliente=self.cliente,
            barbeiro=barbeiro,
            subtotal=Decimal('100.00'),
            valor_total=Decimal('100.00'),
            status=Comanda.Status.ABERTA
        )

        pagamentos_info = [
            {'metodo': 'pix', 'valor': Decimal('60.00')},
            {'metodo': 'dinheiro', 'valor': Decimal('40.00')}
        ]

        comanda_result = PaymentService.registrar_pagamento_dividido(
            comanda=comanda,
            pagamentos_info=pagamentos_info,
            gorjeta_valor=Decimal('15.00')
        )

        comanda.refresh_from_db()
        self.assertEqual(comanda.status, Comanda.Status.FECHADA)
        pagamentos_divididos = comanda.pagamentos_divididos.all()
        self.assertEqual(pagamentos_divididos.count(), 2)
        total_pago = sum(p.valor for p in pagamentos_divididos)
        self.assertEqual(total_pago, Decimal('100.00'))
        self.assertEqual(comanda.gorjetas.first().valor, Decimal('15.00'))

    def test_health_check_endpoint(self):
        """Endpoint de health check responde HTTP 200 com status do banco de dados operacional."""
        response = self.client.get(reverse('health_check'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['database'], 'ok')
        self.assertEqual(data['version'], '2.0.0')

