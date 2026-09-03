# Auditoria Baseline Antes das Alterações — Barber Heitor
**Data da Auditoria:** 03/09/2026  
**Repositório:** BarberProject  
**Marca Anterior:** Delacruz Barber / DelaCruz Barber  
**Nova Marca Oficial:** BARBER HEITOR  

---

## 1. Comandos de Verificação do Sistema

### 1.1 `python manage.py check`
- **Resultado:** Código 0 (Sucesso)
- **Saída:** `System check identified no issues (0 silenced).`
- **Observações:** O sistema Django estruturalmente não apresentava erros fatais de sintaxe ou configuração básica.

### 1.2 `python manage.py makemigrations --check`
- **Resultado:** Código 0 (Sucesso)
- **Saída:** `No changes detected`
- **Observações:** Nenhum modelo pendente de migração.

### 1.3 `python manage.py showmigrations`
- **Resultado:** Todas as migrações aplicadas até a `website 0008_alter_agendamento_data_alter_agendamento_status_and_more`.

### 1.4 `python manage.py test`
- **Resultado:** 59 testes executados em 84.323s.
- **Saída:** `Ran 59 tests in 84.323s - OK`
- **Observações:** A suíte de testes existente (em `tests.py` e `test_audit_hardening.py`) passa integralmente antes das modificações.

---

## 2. Diagnóstico de Problemas Encontrados no Baseline

### 2.1 Marca Hardcoded e Acoplamento Global
- Mais de 60 arquivos contêm referências fixas a "Delacruz Barber", "delacruz-card", "btn-delacruz", "delacruz-cache-v1", etc.
- Inexistência de centralização dos dados do estabelecimento (nome, telefone, endereço, redes sociais), forçando repetição constante em templates.
- **Atenção Contextual:** "Danilo Delacruz" é o nome pessoal de um dos barbeiros e deve ser mantido como nome de pessoa, enquanto o estabelecimento como um todo passa a se chamar **Barber Heitor**.

### 2.2 Fragmentação e Conflito de CSS / Design
- Inconsistência crítica de paleta:
  - `website/static/website/css/style.css` definiu `--primary-gold: #22c55e` (verde!), embora a variável se chamasse "gold".
  - `website/templates/website/modelo.html` definiu regras inline com `#c5a880` (dourado) e `.btn-delacruz`, sobrescrevendo arbitrariamente o arquivo CSS.
- Falta de estilização de formulários:
  - Nenhuma regra para `.form-control`, `.form-select`, `select` ou `<option>` no `style.css`.
  - No modo escuro, `<option>` nativo em navegadores como Chrome, Edge e Firefox no Windows exibe texto ilegível ou fundo branco com texto claro.
- Classes CSS inexistentes usadas em templates:
  - `form.html` referencia `class="card delacruz-card"`, mas a classe definida no CSS/modelo era `.card-delacruz`, quebrando o isolamento do card e caindo no estilo padrão do Bootstrap 5.

### 2.3 JavaScript e Interatividade
- Incompatibilidade de seletor na Navbar:
  - `main.js` busca `.navbar-custom` para adicionar a classe `.scrolled`, porém `modelo.html` usa `.custom-navbar`, impedindo a ativação do efeito de scroll.
- O botão de confirmação manual em `pagamento_pix.html` realiza submit via POST que chama `PaymentService.confirmar_pagamento` sem qualquer checagem de ambiente.

### 2.4 PWA & Assets Faltantes (404)
- O manifesto PWA em `views.py` (`manifest_view`) referencia `/static/website/img/icon-192.png` e `/static/website/img/icon-512.png`.
- O diretório `website/static/website/img/` continha apenas um arquivo `.gitkeep`, gerando requisições com status 404 para os ícones do app.
- O cache do Service Worker utilizava o nome obsoleto `'delacruz-cache-v1'`.

### 2.5 Segurança & Endurecimento do PIX / Mercado Pago
- **Falha de Simulação Manual:** `PagamentoPixView.post` confirmava pagamentos no banco de dados independentemente de `DEBUG` estar ativo ou de o gateway ser mock, permitindo que qualquer visitante fizesse POST para aprovar agendamentos.
- **Fallback Silencioso em Produção:** Em `MercadoPagoProvider`, a ausência de `PAYMENT_ACCESS_TOKEN` ou qualquer exceção de rede caía silenciosamente para `MockPixProvider`, gerando aprovações falsas em ambiente real.
- **Dados Hardcoded do Pagador:** Na requisição do Mercado Pago, os dados do cliente estavam fixados como `cliente@delacruzbarber.com.br` e nome `Cliente Delacruz`.
- **Vazamento de Dados em QR Code:** O template de pagamento utilizava `https://api.qrserver.com` para gerar imagens de QR Code, expondo o código EMVCo com chaves e identificadores a um serviço público de terceiros.
- **Validação de Webhook:** Ausência de verificação criptográfica estrita de assinatura de webhook (`x-signature`) e consulta ativa à API do Mercado Pago para conferência de status, valor e referência antes da confirmação.

### 2.6 Prontidão para Produção (Settings & Infraestrutura)
- `STATIC_ROOT` não estava configurado em `settings.py`.
- Ausência de WhiteNoise para servir arquivos estáticos em ambientes conteinerizados ou de produção.
- Ausência de trava para `SECRET_KEY` insegura quando `DEBUG=False`.
- Ausência de suporte para string de conexão PostgreSQL via `DATABASE_URL`.

---

## 3. Conclusão do Baseline
O projeto possui uma base sólida de regras de negócio em Django e ampla cobertura de modelos, mas sofria de acoplamento com a marca anterior, severas inconsistências de CSS/tema, bugs de contraste em inputs/selects, 404 em assets e fragilidades de segurança nos fluxos de pagamento que impossibilitavam o uso seguro em produção.
