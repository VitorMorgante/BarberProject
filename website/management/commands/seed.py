from datetime import time, date
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from website.models import (
    Servico, Barbeiro, Cliente, HorarioDisponivel,
    PlanoAssinatura, Produto, EstiloCorte,
    ProgramaFidelidade, ConfiguracaoEstabelecimento,
    RegraComissao, MetaBarbeiro, CupomDesconto, PerfilUsuario
)


class Command(BaseCommand):
    help = 'Popula o banco de dados com dados iniciais completos da Barber Heitor'

    def handle(self, *args, **options):
        self.stdout.write('--- Criando Usuários de Acesso (Superuser, Barbeiro, Cliente) ---')

        # 1. Superuser / Administrador
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser('admin', 'admin@barberheitor.com.br', 'admin123')
            admin_user.first_name = 'Administrador'
            admin_user.last_name = 'Heitor'
            admin_user.save()
            PerfilUsuario.objects.get_or_create(
                usuario=admin_user,
                defaults={'tipo_usuario': 'administrador', 'telefone': '4491022176'}
            )
            self.stdout.write(self.style.SUCCESS('  [OK] Superuser/Admin: admin / admin123'))
        else:
            self.stdout.write('  [SKIP] Superuser admin já existe.')

        # 2. Usuário Barbeiro (Danilo Delacruz)
        barbeiro_user, created_b = User.objects.get_or_create(
            username='danilo',
            defaults={
                'email': 'danilo@barberheitor.com.br',
                'first_name': 'Danilo',
                'last_name': 'Delacruz'
            }
        )
        if created_b:
            barbeiro_user.set_password('barbeiro123')
            barbeiro_user.save()
        PerfilUsuario.objects.get_or_create(
            usuario=barbeiro_user,
            defaults={'tipo_usuario': 'barbeiro', 'telefone': '4499190997'}
        )
        self.stdout.write(self.style.SUCCESS('  [OK] Barbeiro Login: danilo / barbeiro123'))

        # 3. Usuário Barbeiro (Heitor Pontes)
        heitor_user, created_h = User.objects.get_or_create(
            username='heitor',
            defaults={
                'email': 'heitor@barberheitor.com.br',
                'first_name': 'Heitor',
                'last_name': 'Pontes'
            }
        )
        if created_h:
            heitor_user.set_password('barbeiro123')
            heitor_user.save()
        PerfilUsuario.objects.get_or_create(
            usuario=heitor_user,
            defaults={'tipo_usuario': 'barbeiro', 'telefone': '4491022176'}
        )
        self.stdout.write(self.style.SUCCESS('  [OK] Barbeiro Login: heitor / barbeiro123'))

        # 4. Usuário Cliente Demonstrativo
        cliente_user, created_c = User.objects.get_or_create(
            username='cliente',
            defaults={
                'email': 'cliente@email.com',
                'first_name': 'Lucas',
                'last_name': 'Silva'
            }
        )
        if created_c:
            cliente_user.set_password('cliente123')
            cliente_user.save()
        PerfilUsuario.objects.get_or_create(
            usuario=cliente_user,
            defaults={'tipo_usuario': 'cliente', 'telefone': '44998887766'}
        )
        Cliente.objects.get_or_create(
            usuario=cliente_user,
            defaults={'nome': 'Lucas Silva', 'telefone': '44998887766', 'email': 'cliente@email.com'}
        )
        self.stdout.write(self.style.SUCCESS('  [OK] Cliente Login: cliente / cliente123'))

        self.stdout.write('\n--- Criando Barbeiros e Regras de Comissão ---')

        danilo, _ = Barbeiro.objects.get_or_create(
            nome='Danilo Delacruz',
            defaults={
                'cargo': 'Barbeiro Especialista',
                'especialidade': 'Cortes clássicos, degradê navalhado e acabamento preciso',
                'descricao_curta': 'Mestre barbeiro com vasta experiência em cortes masculinos clássicos e modernos.',
                'ativo': True,
                'usuario': barbeiro_user,
            },
        )
        if not danilo.usuario or danilo.cargo != 'Barbeiro Especialista':
            danilo.usuario = barbeiro_user
            danilo.cargo = 'Barbeiro Especialista'
            danilo.save(update_fields=['usuario', 'cargo'])
        RegraComissao.objects.get_or_create(
            barbeiro=danilo,
            defaults={'percentual_servico': Decimal('50.00'), 'percentual_produto': Decimal('15.00')}
        )
        MetaBarbeiro.objects.get_or_create(
            barbeiro=danilo,
            mes=date.today().month,
            ano=date.today().year,
            defaults={'meta_faturamento': Decimal('6000.00'), 'meta_atendimentos': 120, 'meta_produtos': 25}
        )
        self.stdout.write(self.style.SUCCESS(f'  [OK] {danilo.nome}'))

        heitor, _ = Barbeiro.objects.get_or_create(
            nome='Heitor Pontes',
            defaults={
                'cargo': 'Barbeiro Master & Visagista',
                'especialidade': 'Cortes modernos, barboterapia e consultoria visagista',
                'descricao_curta': 'Sócio-fundador da Barber Heitor, especialista em design de barba e visagismo.',
                'ativo': True,
                'usuario': heitor_user,
            },
        )
        if not heitor.usuario or heitor.cargo != 'Barbeiro Master & Visagista':
            heitor.usuario = heitor_user
            heitor.cargo = 'Barbeiro Master & Visagista'
            heitor.save(update_fields=['usuario', 'cargo'])
        RegraComissao.objects.get_or_create(
            barbeiro=heitor,
            defaults={'percentual_servico': Decimal('50.00'), 'percentual_produto': Decimal('15.00')}
        )
        MetaBarbeiro.objects.get_or_create(
            barbeiro=heitor,
            mes=date.today().month,
            ano=date.today().year,
            defaults={'meta_faturamento': Decimal('6500.00'), 'meta_atendimentos': 130, 'meta_produtos': 30}
        )
        self.stdout.write(self.style.SUCCESS(f'  [OK] {heitor.nome}'))

        self.stdout.write('--- Criando Serviços Barber Heitor ---')

        servicos_data = [
            {
                'nome': 'Corte Masculino Clássico',
                'descricao': 'Corte tradicional masculino com acabamento alinhado e finalização profissional.',
                'preco': Decimal('40.00'),
                'duracao_minutos': 30,
                'categoria': 'Cortes',
                'icone': 'scissors',
                'destaque': True,
                'ordem': 1,
            },
            {
                'nome': 'Corte Degradê (Fade)',
                'descricao': 'Corte com técnica de degradê suave ou navalhado, finalizado com produtos premium.',
                'preco': Decimal('45.00'),
                'duracao_minutos': 40,
                'categoria': 'Cortes',
                'icone': 'scissors',
                'destaque': True,
                'ordem': 2,
            },
            {
                'nome': 'Barboterapia & Navalha',
                'descricao': 'Aparação e modelagem de barba com toalha quente aromática, óleos e navalha descartável.',
                'preco': Decimal('35.00'),
                'duracao_minutos': 30,
                'categoria': 'Barba',
                'icone': 'brush',
                'destaque': True,
                'ordem': 3,
            },
            {
                'nome': 'Combo Signature (Corte + Barba)',
                'descricao': 'Experiência completa combinando corte degradê e barboterapia. Nosso carro-chefe.',
                'preco': Decimal('70.00'),
                'duracao_minutos': 60,
                'categoria': 'Combos',
                'icone': 'star',
                'destaque': True,
                'ordem': 4,
            },
            {
                'nome': 'Design de Sobrancelha',
                'descricao': 'Alinhamento e limpeza facial masculina com navalha de precisão.',
                'preco': Decimal('20.00'),
                'duracao_minutos': 15,
                'categoria': 'Estética',
                'icone': 'eye',
                'destaque': False,
                'ordem': 5,
            },
            {
                'nome': 'Corte Kids VIP',
                'descricao': 'Corte infantil especial até 12 anos com paciência, atenção e acolhimento.',
                'preco': Decimal('35.00'),
                'duracao_minutos': 30,
                'categoria': 'Cortes',
                'icone': 'emoji-smile',
                'destaque': False,
                'ordem': 6,
            },
            {
                'nome': 'Experiência Barber Heitor Prime',
                'descricao': 'Cuidado total com corte, barba, sobrancelha, massagem facial e finalização premium.',
                'preco': Decimal('100.00'),
                'duracao_minutos': 90,
                'categoria': 'Premium',
                'icone': 'gem',
                'destaque': True,
                'ordem': 7,
            },
        ]

        servicos_objs = []
        for data in servicos_data:
            servico, _ = Servico.objects.get_or_create(
                nome=data['nome'],
                defaults=data,
            )
            servicos_objs.append(servico)
            self.stdout.write(self.style.SUCCESS(f'  [OK] {servico.nome}'))

        self.stdout.write('--- Criando Planos Barber Club Prime ---')

        planos_data = [
            {
                'nome': 'Barber Heitor Classic',
                'descricao': 'Ideal para manter o corte em dia quinzenalmente.',
                'preco_mensal': Decimal('75.00'),
                'quantidade_creditos': 2,
                'desconto_produtos': Decimal('10.00'),
                'validade_dias': 30,
                'ativo': True,
                'destaque': False,
            },
            {
                'nome': 'Barber Heitor Prime VIP',
                'descricao': 'Nosso plano mais completo: 4 cortes mensais, prioridade de atendimento e lounge exclusivo.',
                'preco_mensal': Decimal('135.00'),
                'quantidade_creditos': 4,
                'desconto_produtos': Decimal('15.00'),
                'validade_dias': 30,
                'ativo': True,
                'destaque': True,
            },
            {
                'nome': 'Barber Heitor Black (Corte + Barba)',
                'descricao': 'Para quem exige barba e cabelo impecáveis toda semana com máxima comodidade.',
                'preco_mensal': Decimal('220.00'),
                'quantidade_creditos': 4,
                'desconto_produtos': Decimal('20.00'),
                'validade_dias': 30,
                'ativo': True,
                'destaque': False,
            }
        ]

        for p_data in planos_data:
            plano, _ = PlanoAssinatura.objects.get_or_create(
                nome=p_data['nome'],
                defaults=p_data
            )
            self.stdout.write(self.style.SUCCESS(f'  [OK] {plano.nome}'))

        self.stdout.write('--- Criando Catálogo de Produtos & PDV ---')

        produtos_data = [
            {
                'nome': 'Pomada Modeladora Efeito Matte Barber Heitor',
                'sku': 'POM-MATTE-BH',
                'descricao': 'Fixação forte e acabamento natural sem brilho, fragrância amadeirada nobre.',
                'categoria': 'Cabelo',
                'custo': Decimal('14.00'),
                'preco': Decimal('35.00'),
                'estoque_atual': 25,
                'estoque_minimo': 5,
                'unidade': 'un',
                'ativo': True,
            },
            {
                'nome': 'Óleo Hidratante para Barba Premium BH',
                'sku': 'OLEO-BARBA-BH',
                'descricao': 'Hidratação profunda com óleos essenciais e toque seco.',
                'categoria': 'Barba',
                'custo': Decimal('18.00'),
                'preco': Decimal('42.00'),
                'estoque_atual': 18,
                'estoque_minimo': 4,
                'unidade': 'un',
                'ativo': True,
            },
            {
                'nome': 'Balm Alinhador de Barba Barber Heitor',
                'sku': 'BALM-BARBA-BH',
                'descricao': 'Modela e reduz o frizz dos fios da barba ao longo do dia.',
                'categoria': 'Barba',
                'custo': Decimal('16.00'),
                'preco': Decimal('38.00'),
                'estoque_atual': 12,
                'estoque_minimo': 4,
                'unidade': 'un',
                'ativo': True,
            },
            {
                'nome': 'Café Especial Barber Heitor Grãos Selecionados',
                'sku': 'CAFE-ESP-BH',
                'descricao': 'Dose de café espresso artesanal com notas de chocolate e caramelo.',
                'categoria': 'Bebidas',
                'custo': Decimal('2.50'),
                'preco': Decimal('8.00'),
                'estoque_atual': 50,
                'estoque_minimo': 10,
                'unidade': 'un',
                'ativo': True,
            },
            {
                'nome': 'Cerveja Artesanal IPA Barber Heitor 500ml',
                'sku': 'CERV-IPA-BH',
                'descricao': 'Cerveja artesanal bem lupulada servida estalando de gelada no lounge.',
                'categoria': 'Bebidas',
                'custo': Decimal('7.00'),
                'preco': Decimal('16.00'),
                'estoque_atual': 24,
                'estoque_minimo': 6,
                'unidade': 'un',
                'ativo': True,
            }
        ]

        for p in produtos_data:
            prod, _ = Produto.objects.get_or_create(
                sku=p['sku'],
                defaults=p
            )
            self.stdout.write(self.style.SUCCESS(f'  [OK] {prod.nome}'))

        self.stdout.write('--- Criando Catálogo de Estilos para Visagismo IA ---')

        estilos_data = [
            {
                'nome': 'Degradê High Fade',
                'descricao': 'Laterais raspadas bem alto com transição suave e topo texturizado.',
                'tipo_cabelo': 'Liso, Ondulado, Crespo',
                'formato_rosto': 'Oval, Quadrado, Redondo',
                'manutencao': '15 dias',
                'ativo': True,
            },
            {
                'nome': 'Textured Crop Moderno',
                'descricao': 'Franja reta ou desfiada com textura no topo e fade médio.',
                'tipo_cabelo': 'Liso, Ondulado',
                'formato_rosto': 'Oval, Quadrado, Diamante',
                'manutencao': '15 a 20 dias',
                'ativo': True,
            },
            {
                'nome': 'Pompadour Clássico',
                'descricao': 'Volume expressivo no topete penteado para trás com acabamento brilhoso ou matte.',
                'tipo_cabelo': 'Liso, Levemente Ondulado',
                'formato_rosto': 'Oval, Redondo',
                'manutencao': '20 dias',
                'ativo': True,
            },
            {
                'nome': 'Side Part Executivo',
                'descricao': 'Divisão lateral clássica e alinhada com acabamento na tesoura ou máquina baixa.',
                'tipo_cabelo': 'Todos',
                'formato_rosto': 'Oval, Quadrado, Triangular',
                'manutencao': '20 a 30 dias',
                'ativo': True,
            },
            {
                'nome': 'Barba Espartana Alinhada',
                'descricao': 'Design de barba com ponta proeminente e bochechas limpas na navalha.',
                'tipo_cabelo': 'Barba densa',
                'formato_rosto': 'Redondo, Oval, Quadrado',
                'manutencao': '15 dias',
                'ativo': True,
            }
        ]

        for est in estilos_data:
            obj, _ = EstiloCorte.objects.get_or_create(
                nome=est['nome'],
                defaults=est
            )
            self.stdout.write(self.style.SUCCESS(f'  [OK] {obj.nome}'))

        self.stdout.write('--- Configurando Programa de Fidelidade & Regras de Estabelecimento ---')

        ProgramaFidelidade.objects.get_or_create(
            nome='Fidelidade Barber Heitor',
            defaults={
                'servicos_necessarios': 10,
                'tipo_recompensa': 'corte_gratis',
                'valor_desconto': Decimal('0.00'),
                'ativo': True
            }
        )

        ConfiguracaoEstabelecimento.objects.get_or_create(
            id=1,
            defaults={
                'tipo_sinal': 'nenhum',
                'valor_sinal': Decimal('0.00'),
                'minutos_expiracao_pix': 15,
                'chave_pix': 'contato@barberheitor.com.br',
                'titular_pix': 'Barber Heitor',
                'cidade_pix': 'Paranavai',
                'lembrete_horas_antes': 24,
            }
        )

        self.stdout.write('--- Criando Cupons Promocionais ---')

        cupons_data = [
            {
                'codigo': 'HEITOR10',
                'descricao': 'R$ 10 de desconto no corte ou combo',
                'tipo': 'fixo',
                'valor': Decimal('10.00'),
                'valor_minimo_pedido': Decimal('35.00'),
                'ativo': True,
            },
            {
                'codigo': 'PRIMEIRAVEZ15',
                'descricao': '15% de desconto no primeiro atendimento',
                'tipo': 'percentual',
                'valor': Decimal('15.00'),
                'valor_minimo_pedido': Decimal('0.00'),
                'ativo': True,
            },
            {
                'codigo': 'PRIME20',
                'descricao': '20% de desconto especial Barber Club',
                'tipo': 'percentual',
                'valor': Decimal('20.00'),
                'valor_minimo_pedido': Decimal('50.00'),
                'ativo': True,
            }
        ]

        for c_data in cupons_data:
            c_obj, _ = CupomDesconto.objects.get_or_create(
                codigo=c_data['codigo'],
                defaults=c_data
            )
            self.stdout.write(self.style.SUCCESS(f'  [OK] Cupom: {c_obj.codigo}'))

        self.stdout.write('--- Criando Horários Disponíveis ---')

        horarios = [
            time(8, 0), time(8, 30), time(9, 0), time(9, 30),
            time(10, 0), time(10, 30), time(11, 0), time(11, 30),
            time(12, 0), time(12, 30), time(13, 0), time(13, 30),
            time(14, 0), time(14, 30), time(15, 0), time(15, 30),
            time(16, 0), time(16, 30), time(17, 0), time(17, 30),
            time(18, 0), time(18, 30), time(19, 0), time(19, 30),
            time(20, 0), time(20, 30), time(21, 0),
        ]

        for barbeiro in [danilo, heitor]:
            for h in horarios:
                HorarioDisponivel.objects.get_or_create(
                    barbeiro=barbeiro,
                    horario=h,
                    defaults={'ativo': True},
                )
            self.stdout.write(self.style.SUCCESS(f'  [OK] {barbeiro.nome}: {len(horarios)} horários'))

        self.stdout.write(self.style.SUCCESS('\nSeed Barber Heitor executado com sucesso total!'))
