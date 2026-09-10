# BARBER HEITOR — Plataforma Comercial & Gestão de Barbearia Premium

> **"Seu estilo. Sua assinatura."**  
> Plataforma web e PWA de alto padrão para agendamento inteligente, pagamentos instantâneos via PIX dinâmico, clube de assinaturas (Barber Club), frente de caixa (PDV), controle de comissões e gestão executiva de barbearias contemporâneas.

---

## ✂️ Sobre o Projeto

A **BARBER HEITOR** é um ecossistema digital desenvolvido em Python/Django focado em proporcionar uma experiência de luxo editorial, agilidade operacional e máxima conversão comercial.

O sistema atende a todos os pilares da operação:
1. **Experiência do Cliente**: Agendamento visual em poucos cliques, pagamento de sinal via PIX dinâmico com QR Code seguro gerado localmente, clube de assinaturas recorrente (*Barber Club*), cartão fidelidade digital com resgate automático e histórico privado de evolução visual.
2. **Cockpit do Barbeiro**: Interface mobile-first desenvolvida para o dia a dia na bancada. Responde de imediato ao próximo cliente da fila, check-in, lançamento de comandas/produtos e extrato transparente de comissões.
3. **Painel Executivo & Recepção**: Painel de atendimento em tempo real (Recepção), Modo TV para sala de espera com atualização automática, controle financeiro (DRE/Caixa), gestão de estoque com alerta de reposição e automações operacionais.

---

## 💈 Equipe de Especialistas

- **Heitor Pontes**: Sócio-fundador e barbeiro master ([@barber.heitorr](https://www.instagram.com/barber.heitorr/)), especialista em cortes masculinos contemporâneos, barba e finalizações de alto padrão.
- **Danilo Delacruz**: Barbeiro especialista em cortes masculinos clássicos, alinhamento de barba e acabamentos cirúrgicos na navalha.

---

## ✂️ Catálogo Oficial & Planos de Assinatura (Barber Heitor)

### Serviços Confirmados
- **Cabelo**: R$ 30,00 (30 min) — Código: `cabelo`
- **Barba**: R$ 20,00 (20 min) — Código: `barba`
- **Cavanhaque**: R$ 15,00 (15 min) — Código: `cavanhaque`
- **Sobrancelha**: R$ 5,00 (10 min) — Código: `sobrancelha`

### Produtos de Venda Balcão
- **Pomada Fox**: R$ 20,00 (Código: `POM-FOX` / SKU: `HEITOR-POMADA-FOX`)
- **Pomada em Pó**: R$ 30,00 (Código: `POM-PO` / SKU: `HEITOR-POMADA-PO`)
- **Shampoo Anticaspa**: R$ 30,00 (Código: `SHAMP-ANTICASPA` / SKU: `HEITOR-SHAMPOO-ANTICASPA`)

### Clube de Assinaturas (Barber Club)
- **Plano Normal**: R$ 80,00 / mês (Modalidade Limitada: 4 cortes/mês — Cabelo + Sobrancelha)
- **Plano com Barba**: R$ 120,00 / mês (Modalidade Limitada: 4 cortes/mês — Cabelo + Sobrancelha + Barba)
- **Plano Cortes Infinitos**: R$ 100,00 / mês (Modalidade Ilimitada — Cabelo + Sobrancelha)

---

## 🎨 Design System & Identidade Visual

O projeto foi construído sobre uma arquitetura de tokens semânticos (`website/static/website/css/tokens.css` e `style.css`):
- **Superfícies**: Paleta Obsidian Noir (`#06080d`, `#0d121c`, `#141b29`) com alta densidade e profundidade visual.
- **Acentos**: Champanhe & Ouro Envelhecido (`#d4af37`, `#f5e2ad`).
- **Tipografia**: Serif clássica editorial (*Playfair Display*) para títulos de impacto e sem serifa técnica (*Montserrat*) para interfaces de alta legibilidade.
- **Acessibilidade & Mobile**: Todos os controles de formulário, botões e selects possuem altura mínima de toque de 44px (`--touch-target-min`), contraste rigoroso (evitando texto branco sobre fundo claro em selects nativos) e total ausência de rolagem horizontal indesejada.

---

## 🛡️ Segurança Financeira & PIX Hardening

- **Geração Local de QR Code**: Eliminação do vazamento de payloads financeiros para serviços públicos terceiros. Todos os QR Codes PIX são gerados internamente em Python com biblioteca `qrcode` em formato Base64.
- **Proteção do Ambiente de Produção**: A simulação manual de confirmação de pagamento foi estritamente bloqueada em produção. Em `DEBUG=False` ou `PAYMENT_GATEWAY=mercadopago`, qualquer tentativa de POST arbitrário retorna `403 Forbidden`.
- **Validação de Webhooks & Idempotência**: Suporte a verificação de assinatura criptográfica HMAC-SHA256 e consulta ativa à API do gateway antes de confirmar agendamentos.
- **Dados do Pagador Dinâmicos**: O payload do PIX utiliza os dados reais do cliente agendado, com sanitização de nomes e e-mails.

---

## 🚀 Como Executar o Projeto Localmente

### 1. Pré-requisitos
- Python 3.10+ (recomendado 3.12 ou superior)
- Git

### 2. Clonar e Instalar Dependências
```bash
git clone https://github.com/VitorMorgante/BarberProject.git
cd BarberProject

# Criar ambiente virtual
python -m venv venv

# Ativar no Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Instalar requisitos
pip install -r requirements.txt
```

### 3. Configuração de Variáveis de Ambiente
Copie o arquivo de exemplo e ajuste suas credenciais conforme necessário:
```bash
copy .env.example .env
```

### 4. Migrações do Banco de Dados
```bash
python manage.py migrate
```

### 5. Popular Base Comercial Real (Barber Heitor) ou Demo
Para aplicar o catálogo canônico de serviços, produtos, planos de assinatura e a escala oficial de Heitor e Danilo:
```bash
# Sincronização canônica oficial (idempotente):
python manage.py seed_heitor_real

# Para simular alterações antes de persistir:
python manage.py seed_heitor_real --dry-run

# Ou carregar base demonstrativa ampliada para hoje:
python manage.py seed_demo
```

### 6. Iniciar o Servidor de Desenvolvimento
```bash
python manage.py runserver
```
Acesse a aplicação em `http://127.0.0.1:8000/`.

---

## 🔑 Credenciais de Acesso (Ambiente Demo)

| Perfil | Usuário | Senha | Acesso |
| :--- | :--- | :--- | :--- |
| **Administrador / Executivo** | `admin` | `admin123` | Cockpit Executivo, Financeiro, Comissões, Estoque e Cadastros |
| **Barbeiro (Danilo)** | `danilo` | `barbeiro123` | Painel do Barbeiro, Atendimentos, Comanda PDV, Comissões |
| **Barbeiro (Heitor)** | `heitor` | `barbeiro123` | Painel do Barbeiro, Atendimentos, Comanda PDV, Comissões |
| **Cliente Demonstrativo** | `cliente` | `cliente123` | Área do Cliente, Barber Club Prime, Fidelidade Digital |

---

## 🧪 Execução de Testes Automatizados

```bash
# Executar a suíte completa de conformidade com Barber Heitor:
python manage.py test website.tests_heitor_real --keepdb

# Executar a suíte de regressão geral do sistema:
python manage.py test website.tests --keepdb

# Executar todos os testes:
python manage.py test --keepdb
```

---

## 📦 Produção & Deploy

- **Coleta de Arquivos Estáticos**:
  ```bash
  python manage.py collectstatic --noinput
  ```
- **WhiteNoise**: Integrado nativamente para entrega compactada de assets estáticos com cache agressivo.
- **Health Check Endpoint**: Disponível em `/health/` para monitoramento automatizado por balanceadores de carga e orquestradores de containers.
- **Banco de Dados**: Suporta PostgreSQL via variável de ambiente `DATABASE_URL` com fallback transparente para SQLite em ambiente local.
