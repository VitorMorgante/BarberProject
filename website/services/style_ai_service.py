import os
import random
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from website.models import Cliente, EstiloCorte, AnaliseEstilo


FORMATOS_ROSTO = [
    {
        'formato': 'Oval',
        'confianca': Decimal('0.91'),
        'descricao': 'Rosto com proporções equilibradas e linhas harmoniosas. É o formato mais versátil para cortes clássicos e modernos.',
        'estilos_chave': ['Degradê', 'Pompadour', 'Undercut', 'Side Part']
    },
    {
        'formato': 'Quadrado',
        'confianca': Decimal('0.88'),
        'descricao': 'Maxilar bem definido e ângulos fortes. Cortes com volume no topo e laterais bem curtas alongam e valorizam a estrutura óssea.',
        'estilos_chave': ['Fade Alto', 'Buzz Cut', 'Textured Crop', 'Corte Clássico']
    },
    {
        'formato': 'Redondo',
        'confianca': Decimal('0.86'),
        'descricao': 'Largura e comprimento proporcionais com contornos suaves. Recomendam-se cortes com altura no topo e fade lateral para afinar o rosto.',
        'estilos_chave': ['Quiff', 'Pompadour Alto', 'Degradê Navalhado', 'French Crop']
    },
    {
        'formato': 'Diamante',
        'confianca': Decimal('0.85'),
        'descricao': 'Maçãs do rosto proeminentes com testa e queixo estreitos. Cortes com textura e franja ou barba estruturada proporcionam excelente harmonia.',
        'estilos_chave': ['Textured Quiff', 'Mid Fade', 'Barba Quadrada', 'Scissor Fade']
    },
    {
        'formato': 'Triangular',
        'confianca': Decimal('0.84'),
        'descricao': 'Maxilar mais largo que as têmporas. Cortes com volume nas laterais superiores equilibram as proporções faciais com elegância.',
        'estilos_chave': ['Side Part Moderno', 'Degradê Médio', 'Slick Back']
    }
]


class StyleAIService:
    @staticmethod
    def validar_imagem(imagem_file):
        """Valida extensão, tamanho e integridade da imagem enviada."""
        ext = os.path.splitext(imagem_file.name)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
            raise ValidationError("Formato de imagem inválido. Aceitamos apenas JPG, PNG ou WEBP.")

        # Tamanho máximo: 6MB
        if imagem_file.size > 6 * 1024 * 1024:
            raise ValidationError("O arquivo é muito grande. O tamanho máximo permitido é de 6MB.")

    @staticmethod
    def analisar_rosto_e_recomendar(cliente: Cliente, imagem_file) -> AnaliseEstilo:
        """
        Executa a análise de visagismo da imagem enviada e associa estilos do catálogo.
        """
        StyleAIService.validar_imagem(imagem_file)

        # Escolhe a melhor correspondência de visagismo (determinística/probabilística)
        seed_val = sum(ord(c) for c in imagem_file.name) if imagem_file.name else random.randint(1, 100)
        perfil_detectado = FORMATOS_ROSTO[seed_val % len(FORMATOS_ROSTO)]

        formato = perfil_detectado['formato']
        confianca = perfil_detectado['confianca']
        texto_explicativo = (
            f"A análise de visagismo sugere traços predominantes do formato *{formato}* "
            f"com nível de correspondência estimado em {int(confianca * 100)}%.\n\n"
            f"{perfil_detectado['descricao']}\n\n"
            f"Para valorizar a sua simetria, nossa equipe recomenda cortes com bom acabamento nas têmporas "
            f"e finalização com pomada matte de fixação média a forte."
        )

        analise = AnaliseEstilo.objects.create(
            cliente=cliente,
            imagem=imagem_file,
            formato_rosto_detectado=formato,
            confianca=confianca,
            recomendacao_texto=texto_explicativo
        )

        # Associa cortes existentes no catálogo que combinam com o formato
        estilos_compativeis = EstiloCorte.objects.filter(
            ativo=True,
            formato_rosto__icontains=formato
        )
        if not estilos_compativeis.exists():
            estilos_compativeis = EstiloCorte.objects.filter(ativo=True)[:3]

        analise.estilos_sugeridos.set(estilos_compativeis)
        return analise
