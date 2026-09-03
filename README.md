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

- **Danilo Delacruz**: Barbeiro especialista em cortes masculinos clássicos, visagismo e acabamentos cirúrgicos na navalha.
- **Heitor Pontes**: Sócio-fundador e barbeiro master, especialista em tendências contemporâneas, barboterapia relaxante e visagismo personalizado.

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

### 5. Popular Base Comercial Demo (Apresentação Imediata)
Para carregar dados completos com barbeiros, catálogo de serviços, produtos, comandas, clientes e agendamentos ao vivo para a data de hoje:
```bash
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
python manage.py test
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
