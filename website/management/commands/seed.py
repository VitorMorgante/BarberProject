from datetime import time
from django.core.management.base import BaseCommand
from website.models import Servico, Barbeiro, HorarioDisponivel


class Command(BaseCommand):
    help = 'Popula o banco de dados com dados iniciais da Delacruz Barber'

    def handle(self, *args, **options):
        self.stdout.write('Criando barbeiros...')

        danilo, _ = Barbeiro.objects.get_or_create(
            nome='Danilo Delacruz',
            defaults={
                'cargo': 'Barbeiro Chefe',
                'especialidade': 'Cortes clássicos, degradê e acabamento preciso',
                'descricao_curta': 'Fundador da Delacruz Barber, especialista em cortes masculinos clássicos e modernos.',
                'ativo': True,
            },
        )
        self.stdout.write(self.style.SUCCESS(f'  [OK] {danilo.nome}'))

        heitor, _ = Barbeiro.objects.get_or_create(
            nome='Heitor Pontes',
            defaults={
                'cargo': 'Barbeiro',
                'especialidade': 'Cortes modernos, barba e finalização',
                'descricao_curta': 'Especialista em cortes modernos, design de barba e técnicas de finalização.',
                'ativo': True,
            },
        )
        self.stdout.write(self.style.SUCCESS(f'  [OK] {heitor.nome}'))

        self.stdout.write('Criando serviços...')

        servicos_data = [
            {
                'nome': 'Corte Masculino Clássico',
                'descricao': 'Corte tradicional masculino com acabamento alinhado e finalização profissional.',
                'preco': 40.00,
                'duracao_minutos': 30,
                'categoria': 'Cortes',
                'icone': 'bi bi-scissors',
                'destaque': True,
                'ordem': 1,
            },
            {
                'nome': 'Corte Degradê',
                'descricao': 'Corte masculino com técnica de degradê suave ou marcado, finalizado com produtos premium.',
                'preco': 45.00,
                'duracao_minutos': 40,
                'categoria': 'Cortes',
                'icone': 'bi bi-scissors',
                'destaque': True,
                'ordem': 2,
            },
            {
                'nome': 'Barba Completa',
                'descricao': 'Aparação e modelagem de barba com navalha, toalha quente e hidratação.',
                'preco': 35.00,
                'duracao_minutos': 30,
                'categoria': 'Barba',
                'icone': 'bi bi-brush',
                'destaque': True,
                'ordem': 3,
            },
            {
                'nome': 'Corte + Barba',
                'descricao': 'Combo completo de corte degradê com barba modelada. O pacote mais pedido.',
                'preco': 70.00,
                'duracao_minutos': 60,
                'categoria': 'Combos',
                'icone': 'bi bi-star',
                'destaque': True,
                'ordem': 4,
            },
            {
                'nome': 'Sobrancelha',
                'descricao': 'Design e aparação de sobrancelha masculina com navalha.',
                'preco': 20.00,
                'duracao_minutos': 15,
                'categoria': 'Estética',
                'icone': 'bi bi-eye',
                'destaque': False,
                'ordem': 5,
            },
            {
                'nome': 'Corte Infantil',
                'descricao': 'Corte especial para crianças até 12 anos, com paciência e cuidado.',
                'preco': 35.00,
                'duracao_minutos': 30,
                'categoria': 'Cortes',
                'icone': 'bi bi-emoji-smile',
                'destaque': False,
                'ordem': 6,
            },
            {
                'nome': 'Pacote Premium Delacruz',
                'descricao': 'Experiência completa com corte, barba, sobrancelha e finalização premium.',
                'preco': 100.00,
                'duracao_minutos': 90,
                'categoria': 'Premium',
                'icone': 'bi bi-gem',
                'destaque': True,
                'ordem': 7,
            },
        ]

        for data in servicos_data:
            servico, _ = Servico.objects.get_or_create(
                nome=data['nome'],
                defaults=data,
            )
            self.stdout.write(self.style.SUCCESS(f'  [OK] {servico.nome}'))

        self.stdout.write('Criando horários disponíveis...')

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
                obj, _ = HorarioDisponivel.objects.get_or_create(
                    barbeiro=barbeiro,
                    horario=h,
                    defaults={'ativo': True},
                )
            self.stdout.write(self.style.SUCCESS(f'  [OK] {barbeiro.nome}: {len(horarios)} horários'))

        self.stdout.write(self.style.SUCCESS('\nSeed concluído com sucesso!'))
