# DELACRUZ BARBER — ARCHITECTURAL DECISIONS (ADRs)

Este documento registra as decisões arquiteturais fundamentais adotadas no projeto **Delacruz Barber**.

---

## ADR-001 — Manutenção da Stack Django Monolítica com JavaScript Progressivo
* **Contexto**: O projeto é uma plataforma completa de gestão de barbearia (agenda, CRM, PDV, estoque, financeiro, IA).
* **Decisão**: Manter a arquitetura Django + Templates + Bootstrap 5 + JavaScript progressivo sem migração para SPA/Next.js/React.
* **Justificativa**: Garante velocidade de entrega, simplicidade operacional, robustez transacional com Django ORM e baixo custo de manutenção.

---

## ADR-002 — Proibição Estrita de Gift Card
* **Contexto**: O roadmap de negócio definiu que a barbearia utiliza Barber Club (assinatura), Fidelidade Digital e Conta Corrente do Cliente (saldos/créditos internos).
* **Decisão**: Nenhuma funcionalidade de Gift Card, vale-presente ou voucher de presente deve ser implementada no sistema.

---

## ADR-003 — Isolamento de Regras de Negócio em Services
* **Contexto**: Views e models não devem conter toda a lógica de negócio orquestrada.
* **Decisão**: Centralizar fluxos complexos em `website/services/`:
  - `AgendamentoService`
  - `AgendaInteligenteService`
  - `SubscriptionService`
  - `LoyaltyService`
  - `PaymentService`
  - `InventoryService`
  - `ComissaoService`
  - `FinanceService`
  - `CRMService`
  - `AutomationService`
  - `WhatsAppService`
  - `StyleAIService`
  - `AuditService`

---

## ADR-004 — Transacionalidade e Idempotência
* **Contexto**: Operações de conclusão de agendamento afetam múltiplos subsistemas (agenda, comanda, estoque, crédito, fidelidade, comissão, financeiro).
* **Decisão**: Utilizar `transaction.atomic()` com `select_for_update()` em operações críticas, e garantir idempotência em webhooks, repasses e processamentos recorrentes.

---

## ADR-005 — Precisão Monetária e Snapshots Históricos
* **Contexto**: Mudanças futuras em preços de serviços, comissões de profissionais ou custos de produtos não podem alterar transações passadas.
* **Decisão**: Valores monetários utilizam estritamente `DecimalField` (nunca `float`), e cada comanda/comissão registra snapshot com os valores e percentuais vigentes no instante exato da operação.
