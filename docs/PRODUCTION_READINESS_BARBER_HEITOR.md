# BARBER HEITOR — Checklist de Prontidão para Produção (Production Readiness)

Este documento atesta os requisitos de segurança, estabilidade, infraestrutura e conformidade técnica implementados para a entrada em produção da plataforma **Barber Heitor**.

---

## 1. Variáveis de Ambiente & Segurança do Core

| Variável | Obrigatoriedade | Descrição | Status / Comportamento |
| :--- | :--- | :--- | :--- |
| `DJANGO_SECRET_KEY` | **Crítica (Obrigatória em Prod)** | Chave criptográfica do Django | O sistema lança `ImproperlyConfigured` imediatamente no boot se `DEBUG=False` e a chave não estiver definida. |
| `DJANGO_DEBUG` | **Crítica** | Ativa/desativa modo debug | Deve ser estritamente `False` em produção. Bloqueia endpoints de simulação e mensagens de erro verbosas. |
| `DJANGO_ALLOWED_HOSTS` | **Crítica** | Domínios autorizados para servir o tráfego | Suporta lista separada por vírgulas (ex: `barberheitor.com.br,www.barberheitor.com.br`). |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | **Crítica** | Origens seguras para requisições POST/AJAX | Suporta lista separada por vírgulas com protocolo HTTPS. |

---

## 2. Banco de Dados & Persistência

- **Configuração Flexível**: Através da variável `DATABASE_URL`, o sistema conecta-se nativamente a instâncias **PostgreSQL** de produção com suporte a pooling de conexões (`conn_max_age=600`).
- **Fallback de Desenvolvimento**: Em ambientes locais/testes sem `DATABASE_URL`, o sistema opera normalmente com SQLite3 (`db.sqlite3`).
- **Transações Atômicas**: Todas as operações financeiras críticas (`criar_pagamento_sinal`, `confirmar_pagamento`, `processar_webhook`, `comanda.recalcular`) utilizam `@transaction.atomic` e bloqueio seletivo com `select_for_update()`, prevenindo condições de corrida e inconsistências de saldo.

---

## 3. Assets Estáticos & PWA (WhiteNoise)

- **WhiteNoise Middleware**: Configurado no `MIDDLEWARE` para entrega eficiente de arquivos estáticos compactados (`CompressedManifestStaticFilesStorage`).
- **Diretório de Coleta**: Definido em `STATIC_ROOT = BASE_DIR / 'staticfiles'`.
- **Ícones PWA**: Ícones em alta definição (`icon-192.png`, `icon-512.png`, `favicon.png`, `favicon.svg`) gerados e validados em `website/static/website/img/`, eliminando respostas HTTP 404.
- **Service Worker**: Cache versionado (`barber-heitor-cache-v2`) com whitelist para navegação offline de assets estáticos públicos e bloqueio explícito de rotas autenticadas e APIs.

---

## 4. Gateway de Pagamento & PIX Hardening

- **Bloqueio de Fallback Silencioso**: Se `PAYMENT_GATEWAY='mercadopago'` for especificado e `PAYMENT_ACCESS_TOKEN` estiver ausente, o sistema rejeita a operação com erro explícito em produção (`ImproperlyConfigured`), impedindo a criação de pagamentos fictícios.
- **Proteção do Endpoint de Simulação**: O método `POST` de `PagamentoPixView` é restrito estritamente a `DEBUG=True and PAYMENT_GATEWAY=='mock'`. Em produção, requisições recebem `HTTP 403 Forbidden`. O botão de simulação é condicionalmente omitido no template.
- **QR Code Seguro & Local**: A geração de QR Codes PIX é realizada localmente em Python via biblioteca `qrcode`, convertida em Base64 diretamente no servidor. Não há dependência nem vazamento de dados financeiros para APIs públicas (como `api.qrserver.com`).
- **Dados do Pagador Dinâmicos**: O payload enviado ao Mercado Pago utiliza o nome e e-mail reais do cliente agendado, com sanitização de campos.
- **Idempotência & Verificação de Webhook**:
  - A tabela `EventoWebhookPagamento` audita e impede reprocessamentos duplicados.
  - Suporte a verificação de assinatura HMAC-SHA256 (`x-signature` com `PAYMENT_WEBHOOK_SECRET`).
  - Consulta ativa via API (`/v1/payments/{id}`) para validar status `approved` e consistência do valor pago antes de atualizar agendamentos.

---

## 5. Health Check & Monitoramento

- **Endpoint**: `GET /health/`
- **Validação de Conectividade**: Executa probe ativo no banco de dados (`SELECT 1`).
- **Payload Padronizado**: Retorna JSON contendo `{"status": "healthy", "app": "Barber Heitor", "version": "2.0.0", "database": "connected"}` com status code HTTP 200 (ou HTTP 503 em caso de indisponibilidade).

---

## 6. Procedimento de Deploy Recomendado

1. Clonar repositório e ativar ambiente virtual.
2. Definir variáveis no arquivo `.env` de produção.
3. Executar migrações: `python manage.py migrate`.
4. Coletar arquivos estáticos: `python manage.py collectstatic --noinput`.
5. Se for ambiente inicial demonstrativo: `python manage.py seed_demo`.
6. Subir aplicação via servidor WSGI/ASGI de produção (ex: Gunicorn/Uvicorn).
