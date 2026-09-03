from datetime import time, date, datetime, timedelta
from decimal import Decimal
import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from website.models import (
    Servico, Barbeiro, Cliente, HorarioDisponivel,
    PlanoAssinatura, Produto, EstiloCorte,
    ProgramaFidelidade, ConfiguracaoEstabelecimento,
    RegraComissao, MetaBarbeiro, CupomDesconto, PerfilUsuario,
    Agendamento, Comanda, ItemComanda, Feedback, CaixaDiario, MovimentacaoCaixa
)


class Command(BaseCommand):
    help = 'Popula o banco com base demo completa e visualmente rica para apresentação comercial da Barber Heitor'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('=== INICIANDO SEED DEMO BARBER HEITOR ==='))

        # 1. Executa seed base de estrutura
        from django.core.management import call_command
        call_command('seed')

        # 2. Barbeiros
        danilo = Barbeiro.objects.get(nome='Danilo Delacruz')
        heitor = Barbeiro.objects.get(nome='Heitor Pontes')

        danilo.imagem_url = 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=600'
        danilo.save(update_fields=['imagem_url'])

        heitor.imagem_url = 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&q=80&w=600'
        heitor.save(update_fields=['imagem_url'])

        # 3. Clientes Demo Realistas
        clientes_demo = [
            {'nome': 'Matheus Guimarães', 'telefone': '44991234501', 'email': 'matheus@exemplo.com'},
            {'nome': 'Gabriel Silveira', 'telefone': '44991234502', 'email': 'gabriel@exemplo.com'},
            {'nome': 'Rafael Mendonça', 'telefone': '44991234503', 'email': 'rafael@exemplo.com'},
            {'nome': 'Rodrigo Alencar', 'telefone': '44991234504', 'email': 'rodrigo@exemplo.com'},
            {'nome': 'Felipe Antunes', 'telefone': '44991234505', 'email': 'felipe@exemplo.com'},
            {'nome': 'Bruno Carvalho', 'telefone': '44991234506', 'email': 'bruno@exemplo.com'},
            {'nome': 'Guilherme Castro', 'telefone': '44991234507', 'email': 'guilherme@exemplo.com'},
        ]

        clientes_objs = []
        for cd in clientes_demo:
            user, _ = User.objects.get_or_create(
                username=cd['email'].split('@')[0],
                defaults={
                    'email': cd['email'],
                    'first_name': cd['nome'].split()[0],
                    'last_name': cd['nome'].split()[-1]
                }
            )
            user.set_password('demo123')
            user.save()
            
            PerfilUsuario.objects.get_or_create(
                usuario=user,
                defaults={'tipo_usuario': 'cliente', 'telefone': cd['telefone']}
            )
            cli, _ = Cliente.objects.get_or_create(
                telefone=cd['telefone'],
                defaults={'nome': cd['nome'], 'email': cd['email'], 'usuario': user}
            )
            clientes_objs.append(cli)

        self.stdout.write(self.style.SUCCESS(f'  [OK] {len(clientes_objs)} clientes demo criados.'))

        # 4. Agendamentos de Hoje (Para Cockpit, TV e Recepção brilharem)
        hoje = timezone.localtime().date()
        servicos = list(Servico.objects.filter(ativo=True))
        
        status_fluxo = [
            (time(8, 30), danilo, Agendamento.Status.CONCLUIDO, True),
            (time(9, 30), heitor, Agendamento.Status.CONCLUIDO, True),
            (time(10, 30), danilo, Agendamento.Status.EM_ATENDIMENTO, True),
            (time(11, 0), heitor, Agendamento.Status.CONFIRMADO, True),
            (time(13, 30), danilo, Agendamento.Status.CONFIRMADO, False),
            (time(14, 30), heitor, Agendamento.Status.PENDENTE, False),
            (time(15, 30), danilo, Agendamento.Status.CONFIRMADO, False),
        ]

        agendamentos_criados = []
        for i, (horario, barb, stat, checkin) in enumerate(status_fluxo):
            cli = clientes_objs[i % len(clientes_objs)]
            serv = servicos[i % len(servicos)]

            checkin_dt = timezone.now() - timedelta(minutes=20) if checkin else None
            ag, created = Agendamento.objects.get_or_create(
                cliente=cli,
                barbeiro=barb,
                data=hoje,
                horario=horario,
                defaults={
                    'servico': serv,
                    'status': stat,
                    'checkin_em': checkin_dt,
                    'observacoes': 'Preferência por degradê alinhado e navalha quente.'
                }
            )
            agendamentos_criados.append(ag)

        self.stdout.write(self.style.SUCCESS('  [OK] Agendamentos de hoje estruturados para simulação ao vivo.'))

        # 5. Avaliações / Feedbacks de Clientes
        depoimentos = [
            (5, "Atendimento impecável! O Heitor entendeu perfeitamente o corte que eu queria. Espaço climatizado e café de primeira."),
            (5, "Danilo é um mestre na navalha. Barboterapia relaxante demais. Não troco a Barber Heitor por nada."),
            (5, "Agendamento online sem complicação e pontualidade britânica no atendimento. Recomendo fortemente!"),
            (5, "Visual da barbearia é cinematográfico e o resultado do fade ficou perfeito. Ganharam um cliente fiel."),
        ]

        for i, ag in enumerate(agendamentos_criados[:4]):
            nota, texto = depoimentos[i % len(depoimentos)]
            Feedback.objects.get_or_create(
                agendamento=ag,
                defaults={
                    'cliente': ag.cliente,
                    'barbeiro': ag.barbeiro,
                    'nota': nota,
                    'comentario': texto
                }
            )

        admin_user = User.objects.filter(is_superuser=True).first()
        if admin_user:
            caixa = CaixaDiario.objects.filter(status=CaixaDiario.Status.ABERTO).first()
            if not caixa:
                CaixaDiario.objects.create(
                    operador=admin_user,
                    saldo_inicial=Decimal('150.00'),
                    saldo_esperado=Decimal('420.00'),
                    status=CaixaDiario.Status.ABERTO,
                    data_abertura=timezone.now()
                )


        self.stdout.write(self.style.SUCCESS('\n=== BASE DEMO BARBER HEITOR POPULADA COM SUCESSO! ==='))
        self.stdout.write(self.style.SUCCESS('Pronto para apresentação executiva de alto nível.'))
