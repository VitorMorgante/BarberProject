import hashlib
import os
import json
from django.test import TestCase, Client
from django.urls import reverse
from website.portfolio_data import PORTFOLIO_ITEMS, get_portfolio_items


class PortfolioHeitorRealTests(TestCase):
    """
    Testes de validação da integração do Portfólio Real Barber Heitor
    (6 fotografias e 3 vídeos MP4 com capas).
    """

    def setUp(self):
        self.client = Client()
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.static_heitor_dir = os.path.join(
            self.base_dir, 'website', 'static', 'website', 'portfolio', 'heitor'
        )

    def test_01_total_itens_portfolio(self):
        """Garante a contagem canônica: 6 imagens e 3 vídeos (9 itens)."""
        itens = get_portfolio_items()
        self.assertEqual(len(itens), 9)

        fotos = get_portfolio_items(tipo='imagem')
        self.assertEqual(len(fotos), 6)

        videos = get_portfolio_items(tipo='video')
        self.assertEqual(len(videos), 3)

    def test_02_arquivos_estaticos_existem_e_hashes_conferem(self):
        """Verifica a integridade de bytes (SHA-256) de todos os arquivos estáticos copiados."""
        manifest_path = os.path.join(self.static_heitor_dir, 'manifesto.json')
        self.assertTrue(os.path.exists(manifest_path), "manifesto.json deve existir na pasta estática")

        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        for item in manifest['arquivos']:
            caminho_relativo = item['arquivo']  # ex: fotos/corte-01.jpg
            arquivo_fisico = os.path.join(self.static_heitor_dir, caminho_relativo)
            self.assertTrue(
                os.path.exists(arquivo_fisico),
                f"Arquivo físico não encontrado: {arquivo_fisico}"
            )

            # Validação estrita de SHA-256
            sha = hashlib.sha256(open(arquivo_fisico, 'rb').read()).hexdigest()
            self.assertEqual(sha, item['sha256'], f"SHA-256 divergente em {caminho_relativo}")

            # Se for vídeo, checa poster/capa
            if 'capa' in item:
                capa_fisica = os.path.join(self.static_heitor_dir, item['capa'])
                self.assertTrue(os.path.exists(capa_fisica), f"Capa não encontrada: {capa_fisica}")
                capa_sha = hashlib.sha256(open(capa_fisica, 'rb').read()).hexdigest()
                self.assertEqual(capa_sha, item['capa_sha256'], f"SHA-256 da capa divergente em {item['capa']}")

    def test_03_pagina_galeria_retorna_200_e_contem_itens(self):
        """A rota /galeria/ deve renderizar os 9 itens com capas e fontes corretas."""
        resp = self.client.get(reverse('galeria'))
        self.assertEqual(resp.status_code, 200)

        conteudo = resp.content.decode('utf-8')

        # Verifica presença de todas as 6 imagens e 3 vídeos no HTML
        for item in PORTFOLIO_ITEMS:
            self.assertIn(item['arquivo_static'], conteudo)
            self.assertIn(item['titulo'], conteudo)
            if item['is_video']:
                self.assertIn(item['capa_static'], conteudo)

        # Verifica que os atributos acessíveis e de performance estão presentes
        self.assertIn('controls', conteudo)
        self.assertIn('playsinline', conteudo)
        self.assertIn('preload="none"', conteudo)
        self.assertIn('loading="lazy"', conteudo)
        self.assertIn('decoding="async"', conteudo)

    def test_04_pagina_inicial_contem_secao_portfolio_e_link(self):
        """A página inicial deve exibir o portfólio e link para /galeria/."""
        resp = self.client.get(reverse('pagina_inicial'))
        self.assertEqual(resp.status_code, 200)

        conteudo = resp.content.decode('utf-8')
        self.assertIn('id="galeria"', conteudo)
        self.assertIn(reverse('galeria'), conteudo)
        self.assertIn('corte-01.jpg', conteudo)
        self.assertIn('corte-01.mp4', conteudo)

    def test_05_filtros_apenas_categorias_com_conteudo(self):
        """Filtros não podem conter categorias vazias (ex: Infantil, Barba avulsa)."""
        resp = self.client.get(reverse('galeria'))
        conteudo = resp.content.decode('utf-8')

        # Filtros válidos presentes
        self.assertIn('data-filter="all"', conteudo)
        self.assertIn('data-filter="fotos"', conteudo)
        self.assertIn('data-filter="videos"', conteudo)

        # Filtros antigos/vazios ausentes
        self.assertNotIn('data-filter="Infantil"', conteudo)
        self.assertNotIn('data-filter="degrades"', conteudo)
