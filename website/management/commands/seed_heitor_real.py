from datetime import time, date
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User
from website.models import (
    Servico, Barbeiro, BarbeiroServico, EscalaBarbeiro,
    PlanoAssinatura, Produto, ConfiguracaoEstabelecimento,
    PerfilUsuario
)


SERVICOS_CANONICOS = [
    {
        'codigo': 'cabelo',
        'nome': 'Cabelo',
        'preco': Decimal('30.00'),
        'duracao_minutos': 30,
        'descricao': 'Corte de cabelo',
        'categoria': 'Cabelo',
        'icone': 'bi bi-scissors',
        'destaque': True,
        'ordem': 1,
    },
    {
        'codigo': 'barba',
        'nome': 'Barba',
        'preco': Decimal('20.00'),
        'duracao_minutos': 20,
        'descricao': 'Serviço de barba',
        'categoria': 'Barba',
        'icone': 'bi bi-brush',
        'destaque': True,
        'ordem': 2,
    },
    {
        'codigo': 'cavanhaque',
        'nome': 'Cavanhaque',
        'preco': Decimal('15.00'),
        'duracao_minutos': 15,
        'descricao': 'Serviço de cavanhaque',
        'categoria': 'Barba',
        'icone': 'bi bi-slash-circle',
        'destaque': False,
        'ordem': 3,
    },
    {
        'codigo': 'sobrancelha',
        'nome': 'Sobrancelha',
        'preco': Decimal('5.00'),
        'duracao_minutos': 10,
        'descricao': 'Serviço de sobrancelha',
        'categoria': 'Acabamento',
        'icone': 'bi bi-eye',
        'destaque': False,
        'ordem': 4,
    },
]

PRODUTOS_CONFIRMADOS = [
    {
        'sku': 'HEITOR-POMADA-FOX',
        'nome': 'Pomada Fox',
        'preco': Decimal('20.00'),
        'categoria': 'Finalizadores',
        'descricao': 'Pomada modeladora Fox',
    },
    {
        'sku': 'HEITOR-POMADA-PO',
        'nome': 'Pomada em pó',
        'preco': Decimal('30.00'),
        'categoria': 'Finalizadores',
        'descricao': 'Pomada em pó para volume e textura',
    },
    {
        'sku': 'HEITOR-SHAMPOO-ANTICASPA',
        'nome': 'Shampoo anticaspa',
        'preco': Decimal('30.00'),
        'categoria': 'Cuidados',
        'descricao': 'Shampoo de tratamento anticaspa',
    },
]

PLANOS_CONFIRMADOS = [
    {
        'codigo': 'plano-normal',
        'nome': 'Plano normal',
        'preco_mensal': Decimal('80.00'),
        'modalidade': PlanoAssinatura.Modalidade.LIMITADO,
        'limite_mensal': 4,
        'quantidade_creditos': 4,
        'servicos_codigos': ['cabelo', 'sobrancelha'],
        'descricao': 'Cabelo + Sobrancelha (4 atendimentos no mês)',
        'destaque': False,
    },
    {
        'codigo': 'plano-com-barba',
        'nome': 'Plano com barba',
        'preco_mensal': Decimal('120.00'),
        'modalidade': PlanoAssinatura.Modalidade.LIMITADO,
        'limite_mensal': 4,
        'quantidade_creditos': 4,
        'servicos_codigos': ['cabelo', 'sobrancelha', 'barba'],
        'descricao': 'Cabelo + Sobrancelha + Barba (4 atendimentos no mês)',
        'destaque': True,
    },
    {
        'codigo': 'plano-cortes-infinitos',
        'nome': 'Plano cortes infinitos',
        'preco_mensal': Decimal('100.00'),
        'modalidade': PlanoAssinatura.Modalidade.ILIMITADO,
        'limite_mensal': None,
        'quantidade_creditos': 999,
        'servicos_codigos': ['cabelo', 'sobrancelha'],
        'descricao': 'Cabelo + Sobrancelha ilimitados no ciclo mensal',
        'destaque': False,
    },
]


class Command(BaseCommand):
    help = 'Adequação à operação comercial real do Barber Heitor (catálogo canônico, planos reais, Heitor e desativação de legado)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula as alterações e exibe o relatório sem persistir no banco de dados.',
        )
        parser.add_argument(
            '--force-sync',
            action='store_true',
            help='Força a atualização de preços e tempos mesmo se já existirem no banco.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force_sync = options['force_sync']

        self.stdout.write(self.style.MIGRATE_HEADING("=== CONFIGURAÇÃO REAL BARBER HEITOR ==="))
        if dry_run:
            self.stdout.write(self.style.WARNING("MODO DRY-RUN: Simulação transacional. Nenhuma alteração será gravada permanentemente no banco.\n"))

        relatorio = {
            'servicos_criados': 0,
            'servicos_atualizados': 0,
            'servicos_desativados': 0,
            'produtos_criados': 0,
            'produtos_atualizados': 0,
            'produtos_desativados': 0,
            'planos_criados': 0,
            'planos_atualizados': 0,
            'planos_desativados': 0,
            'escalas_configuradas': 0,
        }

        with transaction.atomic():
            # 1. SERVIÇOS CANÔNICOS
            self.stdout.write("\n[1/5] Processando Catálogo Canônico de Serviços...")
            codigos_reais = [s['codigo'] for s in SERVICOS_CANONICOS]
            servicos_objs = {}

            for s_data in SERVICOS_CANONICOS:
                servico = Servico.objects.filter(codigo=s_data['codigo']).first()
                if not servico:
                    servico = Servico.objects.filter(nome__iexact=s_data['nome']).first()

                if not servico:
                    servico = Servico.objects.create(
                        codigo=s_data['codigo'],
                        nome=s_data['nome'],
                        preco=s_data['preco'],
                        duracao_minutos=s_data['duracao_minutos'],
                        descricao=s_data['descricao'],
                        categoria=s_data['categoria'],
                        icone=s_data['icone'],
                        destaque=s_data['destaque'],
                        ordem=s_data['ordem'],
                        ativo=True,
                    )
                    relatorio['servicos_criados'] += 1
                    self.stdout.write(f"  + Criado: {s_data['nome']} (R$ {s_data['preco']}, {s_data['duracao_minutos']}min)")
                else:
                    modificado = False
                    if servico.codigo != s_data['codigo']:
                        servico.codigo = s_data['codigo']
                        modificado = True
                    if not servico.ativo:
                        servico.ativo = True
                        modificado = True
                    if force_sync or servico.preco != s_data['preco'] or servico.duracao_minutos != s_data['duracao_minutos']:
                        servico.preco = s_data['preco']
                        servico.duracao_minutos = s_data['duracao_minutos']
                        servico.descricao = s_data['descricao']
                        servico.categoria = s_data['categoria']
                        servico.destaque = s_data['destaque']
                        servico.ordem = s_data['ordem']
                        modificado = True
                    if modificado:
                        servico.save()
                        relatorio['servicos_atualizados'] += 1
                        self.stdout.write(f"  ~ Atualizado: {servico.nome} (R$ {servico.preco}, {servico.duracao_minutos}min)")
                    else:
                        self.stdout.write(f"  = Preservado: {servico.nome}")
                servicos_objs[s_data['codigo']] = servico

            # Desativa serviços fora da lista confirmada (sem excluir para preservar histórico)
            legados_servicos = Servico.objects.exclude(codigo__in=codigos_reais).filter(ativo=True)
            for s_leg in legados_servicos:
                relatorio['servicos_desativados'] += 1
                self.stdout.write(f"  - Desativando serviço legado: {s_leg.nome} (ID {s_leg.id})")
                s_leg.ativo = False
                s_leg.save(update_fields=['ativo'])

            # 2. PRODUTOS CONFIRMADOS
            self.stdout.write("\n[2/5] Processando Catálogo de Produtos...")
            skus_reais = [p['sku'] for p in PRODUTOS_CONFIRMADOS]

            for p_data in PRODUTOS_CONFIRMADOS:
                prod = Produto.objects.filter(sku=p_data['sku']).first()
                if not prod:
                    prod = Produto.objects.filter(nome__iexact=p_data['nome']).first()

                if not prod:
                    prod = Produto.objects.create(
                        sku=p_data['sku'],
                        nome=p_data['nome'],
                        preco=p_data['preco'],
                        custo=Decimal('0.00'),
                        estoque_atual=0,
                        estoque_minimo=0,
                        categoria=p_data['categoria'],
                        descricao=p_data['descricao'],
                        ativo=True,
                    )
                    relatorio['produtos_criados'] += 1
                    self.stdout.write(f"  + Criado produto: {p_data['nome']} (SKU: {p_data['sku']}, R$ {p_data['preco']}, Estoque: 0)")
                else:
                    modificado = False
                    if prod.sku != p_data['sku']:
                        prod.sku = p_data['sku']
                        modificado = True
                    if not prod.ativo:
                        prod.ativo = True
                        modificado = True
                    if force_sync or prod.preco != p_data['preco']:
                        prod.preco = p_data['preco']
                        modificado = True
                    if modificado:
                        prod.save()
                        relatorio['produtos_atualizados'] += 1
                        self.stdout.write(f"  ~ Atualizado produto: {prod.nome} (R$ {prod.preco})")
                    else:
                        self.stdout.write(f"  = Preservado produto: {prod.nome}")

            # Desativa produtos fora dos SKUs confirmados
            legados_prods = Produto.objects.exclude(sku__in=skus_reais).filter(ativo=True)
            for p_leg in legados_prods:
                relatorio['produtos_desativados'] += 1
                self.stdout.write(f"  - Desativando produto legado: {p_leg.nome} (SKU {p_leg.sku})")
                p_leg.ativo = False
                p_leg.save(update_fields=['ativo'])

            # 3. PLANOS CONFIRMADOS (Barber Club)
            self.stdout.write("\n[3/5] Processando Planos Mensais Confirmados...")
            codigos_planos = [p['codigo'] for p in PLANOS_CONFIRMADOS]

            for pl_data in PLANOS_CONFIRMADOS:
                plano = PlanoAssinatura.objects.filter(codigo=pl_data['codigo']).first()
                if not plano:
                    plano = PlanoAssinatura.objects.filter(nome__iexact=pl_data['nome']).first()

                if not plano:
                    plano = PlanoAssinatura.objects.create(
                        codigo=pl_data['codigo'],
                        nome=pl_data['nome'],
                        descricao=pl_data['descricao'],
                        preco_mensal=pl_data['preco_mensal'],
                        modalidade=pl_data['modalidade'],
                        limite_mensal=pl_data['limite_mensal'],
                        quantidade_creditos=pl_data['quantidade_creditos'],
                        desconto_produtos=Decimal('0.00'),
                        permite_acumular=False,
                        validade_dias=30,
                        ativo=True,
                        destaque=pl_data['destaque'],
                    )
                    # Vincula serviços cobertos
                    for c in pl_data['servicos_codigos']:
                        s_obj = servicos_objs.get(c)
                        if s_obj:
                            plano.servicos_inclusos.add(s_obj)
                            plano.servicos.add(s_obj)
                    relatorio['planos_criados'] += 1
                    self.stdout.write(f"  + Criado plano: {pl_data['nome']} (R$ {pl_data['preco_mensal']}, {pl_data['modalidade']})")
                else:
                    modificado = False
                    if plano.codigo != pl_data['codigo']:
                        plano.codigo = pl_data['codigo']
                        modificado = True
                    if not plano.ativo:
                        plano.ativo = True
                        modificado = True
                    if force_sync or plano.preco_mensal != pl_data['preco_mensal'] or plano.modalidade != pl_data['modalidade']:
                        plano.preco_mensal = pl_data['preco_mensal']
                        plano.modalidade = pl_data['modalidade']
                        plano.limite_mensal = pl_data['limite_mensal']
                        plano.quantidade_creditos = pl_data['quantidade_creditos']
                        plano.descricao = pl_data['descricao']
                        plano.desconto_produtos = Decimal('0.00')
                        plano.destaque = pl_data['destaque']
                        modificado = True
                    if modificado:
                        plano.save()
                        relatorio['planos_atualizados'] += 1
                        self.stdout.write(f"  ~ Atualizado plano: {plano.nome} (R$ {plano.preco_mensal})")
                    else:
                        self.stdout.write(f"  = Preservado plano: {plano.nome}")

                    # Garante vínculos dos serviços cobertos
                    plano.servicos_inclusos.clear()
                    plano.servicos.clear()
                    for c in pl_data['servicos_codigos']:
                        s_obj = servicos_objs.get(c)
                        if s_obj:
                            plano.servicos_inclusos.add(s_obj)
                            plano.servicos.add(s_obj)

            # Desativa planos legados (Classic, Prime VIP, Black)
            legados_planos = PlanoAssinatura.objects.exclude(codigo__in=codigos_planos).filter(ativo=True)
            for pl_leg in legados_planos:
                relatorio['planos_desativados'] += 1
                self.stdout.write(f"  - Desativando plano legado: {pl_leg.nome} (ID {pl_leg.id})")
                pl_leg.ativo = False
                pl_leg.save(update_fields=['ativo'])

            # 4. PROFISSIONAL HEITOR & ESCALAS
            self.stdout.write("\n[4/5] Configurando Profissional Heitor & Escala de Atendimento...")
            heitor = Barbeiro.objects.filter(nome__icontains='Heitor').first()
            user_heitor, _ = User.objects.get_or_create(
                username='heitor.pontes',
                defaults={
                    'email': 'heitor.pontes@barberheitor.com.br',
                    'first_name': 'Heitor',
                    'last_name': 'Pontes',
                    'is_staff': False,
                    'is_superuser': False,
                    'is_active': True,
                }
            )
            if not user_heitor.has_usable_password():
                user_heitor.set_password('barbeiro123')
                user_heitor.save()
            PerfilUsuario.objects.get_or_create(
                usuario=user_heitor,
                defaults={'tipo_usuario': 'barbeiro', 'telefone': '(44) 99190-0997'}
            )

            if not heitor:
                heitor = Barbeiro.objects.create(
                    nome='Heitor Pontes',
                    cargo='Barbeiro Master & Visagista',
                    especialidade='Cortes masculinos, degradê, barba e sobrancelha',
                    descricao_curta='Especialista em cortes modernos e alinhamento de barba.',
                    imagem_url='/static/website/img/barbeiros/heitor_pontes.jpg',
                    usuario=user_heitor,
                    tempo_buffer_depois=5,
                    ativo=True,
                )
                self.stdout.write(f"  + Criado barbeiro: {heitor.nome}")
            else:
                heitor.nome = 'Heitor Pontes'
                heitor.tempo_buffer_depois = 5
                heitor.imagem_url = '/static/website/img/barbeiros/heitor_pontes.jpg'
                if not heitor.usuario:
                    heitor.usuario = user_heitor
                heitor.ativo = True
                heitor.save()
                self.stdout.write(f"  ~ Atualizado barbeiro: {heitor.nome} (buffer={heitor.tempo_buffer_depois}min)")

            # Vincula os serviços canônicos ao Heitor
            for s_obj in servicos_objs.values():
                BarbeiroServico.objects.get_or_create(
                    barbeiro=heitor,
                    servico=s_obj,
                    defaults={
                        'duracao_minutos': s_obj.duracao_minutos,
                        'ativo': True
                    }
                )

            # Configuração da Escala: Segunda a Sábado das 08:00 às 22:40 (para acomodar 21:30 + 60min + 5min buffer)
            # Dias da semana: 0=Segunda, 1=Terça, ..., 5=Sábado, 6=Domingo (folga)
            for dia in range(7):
                is_folga = (dia == 6) # Domingo folga
                escala, created_esc = EscalaBarbeiro.objects.get_or_create(
                    barbeiro=heitor,
                    dia_semana=dia,
                    defaults={
                        'horario_inicio_1': time(8, 0),
                        'horario_fim_1': time(22, 40),
                        'folga': is_folga,
                        'ativo': True,
                    }
                )
                if not created_esc and (escala.horario_fim_1 < time(22, 35) or escala.folga != is_folga):
                    escala.horario_inicio_1 = time(8, 0)
                    escala.horario_fim_1 = time(22, 40)
                    escala.folga = is_folga
                    escala.ativo = True
                    escala.save()
                relatorio['escalas_configuradas'] += 1
            self.stdout.write("  [OK] Escala configurada: Seg a Sáb 08:00 às 22:40 | Dom: Folga")

            # 5. CONFIGURAÇÃO GERAL DO ESTABELECIMENTO
            self.stdout.write("\n[5/5] Sincronizando Configuração do Estabelecimento...")
            config = ConfiguracaoEstabelecimento.get_solo()
            config.nome_estabelecimento = 'Barber Heitor'
            config.instagram = 'barber.heitorr'
            config.telefone = '(44) 9102-2176'
            config.tempo_padrao_buffer = 5
            config.horario_abertura = time(8, 0)
            config.horario_fechamento = time(22, 40)
            config.intervalo_grade_minutos = 5
            config.save()
            self.stdout.write("  [OK] ConfiguracaoEstabelecimento atualizada com @barber.heitorr e grade de 5min.")

            if dry_run:
                # Faz rollback forçado no modo dry-run para nada persistir
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING("\n[DRY-RUN] Rollback executado com sucesso. Banco intacto."))

        self.stdout.write(self.style.SUCCESS("\n=== RELATÓRIO DE EXECUÇÃO ==="))
        self.stdout.write(f"  Serviços: {relatorio['servicos_criados']} criados, {relatorio['servicos_atualizados']} atualizados, {relatorio['servicos_desativados']} desativados.")
        self.stdout.write(f"  Produtos: {relatorio['produtos_criados']} criados, {relatorio['produtos_atualizados']} atualizados, {relatorio['produtos_desativados']} desativados.")
        self.stdout.write(f"  Planos:   {relatorio['planos_criados']} criados, {relatorio['planos_atualizados']} atualizados, {relatorio['planos_desativados']} desativados.")
        self.stdout.write(f"  Escalas:  {relatorio['escalas_configuradas']} faixas de dia/semana configuradas.")
        self.stdout.write(self.style.SUCCESS("Operação concluída com sucesso.\n"))
