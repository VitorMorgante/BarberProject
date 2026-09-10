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
            username='heitor.pontes',
            defaults={
                'email': 'heitor.pontes@barberheitor.com.br',
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
        self.stdout.write(self.style.SUCCESS('  [OK] Barbeiro Login: heitor.pontes / barbeiro123'))

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
                'imagem_url': '/static/website/img/barbeiros/heitor_pontes.jpg',
                'ativo': True,
                'usuario': heitor_user,
            },
        )
        if not heitor.usuario or heitor.cargo != 'Barbeiro Master & Visagista' or not heitor.imagem_url:
            heitor.usuario = heitor_user
            heitor.cargo = 'Barbeiro Master & Visagista'
            heitor.imagem_url = '/static/website/img/barbeiros/heitor_pontes.jpg'
            heitor.save(update_fields=['usuario', 'cargo', 'imagem_url'])
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

        from django.core.management import call_command
        self.stdout.write(self.style.NOTICE('--- Sincronizando Catálogo Oficial Barber Heitor ---'))
        call_command('seed_heitor_real', stdout=self.stdout)

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
        ]

        for c_data in cupons_data:
            c_obj, _ = CupomDesconto.objects.get_or_create(
                codigo=c_data['codigo'],
                defaults=c_data
            )
            self.stdout.write(self.style.SUCCESS(f'  [OK] Cupom: {c_obj.codigo}'))

        self.stdout.write(self.style.SUCCESS('\nSeed Barber Heitor executado com sucesso e sincronizado com o catálogo oficial!'))

