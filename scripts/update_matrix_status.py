import re
from pathlib import Path

# Mapping of implemented REQs with implementation details and test references
IMPLEMENTED_REQS = {
    1: ("IMPLEMENTED", "AgendaInteligenteService (score de horários e minimização de ociosidade)", "website/services/agenda_inteligente_service.py", "TestAgendaInteligenteService"),
    2: ("IMPLEMENTED", "Score preditivo de no-show (0 a 100)", "website/services/agenda_inteligente_service.py", "TestAgendaInteligenteService"),
    3: ("IMPLEMENTED", "Sinal adaptativo (50% para alto risco de no-show)", "website/services/payment_service.py", "TestSinalAdaptativo"),
    4: ("IMPLEMENTED", "Previsão do ciclo e frequência média de retorno", "website/services/crm_service.py", "TestCRMService"),
    5: ("IMPLEMENTED", "Recomendação automática de retorno e campanhas", "website/services/automation_service.py", "TestAutomationService"),
    7: ("IMPLEMENTED", "Check-in por QR Code e token único", "website/views.py, website/models.py", "TestAgendaInteligenteService"),
    8: ("IMPLEMENTED", "Fila operacional em tempo real (Aguardando, Na Cadeira)", "website/services/agenda_inteligente_service.py", "TestAgendaInteligenteService"),
    9: ("IMPLEMENTED", "Painel operacional ao vivo da recepção", "website/views.py, website/templates/website/recepcao.html", "TestLGPDAndViews"),
    10: ("IMPLEMENTED", "Registro de atraso operacional e impacto", "website/services/agenda_inteligente_service.py", "TestAgendaInteligenteService"),
    11: ("IMPLEMENTED", "Aviso automático de atraso via WhatsApp/Notificação", "website/services/agenda_inteligente_service.py", "TestAgendaInteligenteService"),
    12: ("IMPLEMENTED", "Escala semanal completa por barbeiro (turnos e intervalos)", "website/models.py", "TestEscalaBarbeiro"),
    13: ("IMPLEMENTED", "Controle de folgas na escala semanal", "website/models.py", "TestEscalaBarbeiro"),
    14: ("IMPLEMENTED", "Bloqueio de período de férias", "website/models.py", "TestBloqueioAgenda"),
    15: ("IMPLEMENTED", "Bloqueios manuais de agenda com motivo", "website/models.py", "TestBloqueioAgenda"),
    16: ("IMPLEMENTED", "Intervalo de almoço e pausas estruturadas", "website/models.py", "TestEscalaBarbeiro"),
    17: ("IMPLEMENTED", "Duração personalizada por BarbeiroServico", "website/models.py", "TestBarbeiroServico"),
    18: ("IMPLEMENTED", "Preço customizado em BarbeiroServico", "website/models.py", "TestBarbeiroServico"),
    19: ("IMPLEMENTED", "Especialidades e tags por barbeiro", "website/models.py", "TestEspecialidades"),
    20: ("IMPLEMENTED", "Reserva prioritária para membros do Barber Club", "website/services/agendamento_service.py", "TestSubscription"),
    21: ("IMPLEMENTED", "Lista de restrição com sinal reforçado", "website/services/payment_service.py", "TestSinalAdaptativo"),
    22: ("IMPLEMENTED", "Controle de capacidade por bancada/estação", "website/models.py", "TestCapacidade"),
    23: ("IMPLEMENTED", "Agenda visual com grade horária", "website/views.py, website/templates/website/admin/agenda_visual.html", "TestLGPDAndViews"),
    24: ("IMPLEMENTED", "Drag-and-drop de reagendamento com validação de conflito", "website/views.py", "TestLGPDAndViews"),
    25: ("IMPLEMENTED", "Mapa de ocupação e carga horária", "website/views.py", "TestLGPDAndViews"),
    26: ("IMPLEMENTED", "Registro de início real, término real e duração observada", "website/models.py, website/services/agendamento_service.py", "TestSplitPaymentsAndConsumableKits"),
    27: ("IMPLEMENTED", "Comparativo previsto vs real e desvio de duração", "website/services/agenda_inteligente_service.py", "TestAgendaInteligenteService"),
    28: ("IMPLEMENTED", "Cálculo de atraso acumulado e cascata na agenda", "website/services/agenda_inteligente_service.py", "TestAgendaInteligenteService"),
    29: ("IMPLEMENTED", "Atualização dinâmica da previsão de atendimento", "website/services/agenda_inteligente_service.py", "TestAgendaInteligenteService"),
    30: ("IMPLEMENTED", "Pausa rápida do barbeiro (5, 10, 15, 30 min)", "website/views.py, website/services/agenda_inteligente_service.py", "TestAgendaInteligenteService"),
    31: ("IMPLEMENTED", "Troca assistida de barbeiro com validação", "website/services/agenda_inteligente_service.py", "TestAgendaInteligenteService"),
    32: ("IMPLEMENTED", "Workflow de cobertura de ausência de barbeiro", "website/services/agenda_inteligente_service.py", "TestAgendaInteligenteService"),
    33: ("IMPLEMENTED", "Query de detecção de agendamentos afetados por ausência", "website/services/agenda_inteligente_service.py", "TestAgendaInteligenteService"),
    34: ("IMPLEMENTED", "Sugestão de profissionais compatíveis e disponíveis", "website/services/agenda_inteligente_service.py", "TestAgendaInteligenteService"),
    35: ("IMPLEMENTED", "Barbeiro preferido registrado no cliente", "website/models.py", "TestPreferencias"),
    36: ("IMPLEMENTED", "Preferência de horário e acabamento", "website/models.py", "TestPreferencias"),
    37: ("IMPLEMENTED", "Favoritos do cliente e atalho 1-Click Repeat Cut", "website/views.py", "Test1ClickBooking"),
    48: ("IMPLEMENTED", "Fila híbrida (agendados + walk-ins)", "website/services/agenda_inteligente_service.py", "TestAgendaInteligenteService"),
    49: ("IMPLEMENTED", "Previsão de tempo de espera e clientes à frente", "website/services/agenda_inteligente_service.py", "TestAgendaInteligenteService"),
    50: ("IMPLEMENTED", "Cadastro rápido de cliente sem agendamento (Walk-in)", "website/views.py", "TestLGPDAndViews"),
    51: ("IMPLEMENTED", "Atribuição inteligente de barbeiro para walk-in", "website/views.py", "TestLGPDAndViews"),
    68: ("IMPLEMENTED", "Cálculo de LTV realizado e LTV futuro estimado", "website/services/crm_service.py", "TestCRMService"),
    69: ("IMPLEMENTED", "Score de churn e detecção de risco de perda", "website/services/crm_service.py", "TestCRMService"),
    70: ("IMPLEMENTED", "Ciclo médio de corte individual", "website/services/crm_service.py", "TestCRMService"),
    71: ("IMPLEMENTED", "Previsão da data do próximo corte", "website/services/crm_service.py", "TestCRMService"),
    72: ("IMPLEMENTED", "Segmentação VIP (ticket alto ou alta frequência)", "website/services/crm_service.py", "TestCRMService"),
    73: ("IMPLEMENTED", "Segmentação de Clientes Novos (0 ou 1 corte)", "website/services/crm_service.py", "TestCRMService"),
    74: ("IMPLEMENTED", "Segmentação de Clientes em Risco de Churn", "website/services/crm_service.py", "TestCRMService"),
    75: ("IMPLEMENTED", "Segmentação de Clientes Inativos (45d+ sem retorno)", "website/services/crm_service.py", "TestCRMService"),
    76: ("IMPLEMENTED", "Segmentação de Aniversariantes do Mês", "website/services/crm_service.py", "TestCRMService"),
    77: ("IMPLEMENTED", "Segmentação de Clientes Recorrentes", "website/services/crm_service.py", "TestCRMService"),
    81: ("IMPLEMENTED", "Perfil 360 consolidado com timeline unificada", "website/views.py, website/templates/website/admin/perfil_360.html", "TestCRMService"),
    82: ("IMPLEMENTED", "Linha do tempo interativa de eventos do cliente", "website/services/crm_service.py", "TestCRMService"),
    95: ("IMPLEMENTED", "Código único de indicação por cliente", "website/models.py", "TestCRMService"),
    96: ("IMPLEMENTED", "Recompensa de indicação creditada na conta interna", "website/services/crm_service.py", "TestCRMService"),
    97: ("IMPLEMENTED", "Validação de primeiro corte do indicado com idempotência", "website/services/crm_service.py", "TestCRMService"),
    114: ("IMPLEMENTED", "Régua automática de lembrete 24h antes", "website/services/automation_service.py", "TestAutomationService"),
    115: ("IMPLEMENTED", "Régua automática pós-corte e solicitação de feedback", "website/services/automation_service.py", "TestAutomationService"),
    116: ("IMPLEMENTED", "Régua automática de reativação de inativos (45d)", "website/services/automation_service.py", "TestAutomationService"),
    118: ("IMPLEMENTED", "Central de Réguas de Automação com toggle ativo/inativo", "website/views.py, website/templates/website/admin/automacoes.html", "TestAutomationService"),
    125: ("IMPLEMENTED", "Resumo Executivo Diário com faturamento e pendências", "website/services/automation_service.py", "TestAutomationService"),
    145: ("IMPLEMENTED", "Ficha técnica de corte (máquinas, topo, fade, barba)", "website/models.py, website/views.py", "TestLGPDAndViews"),
    146: ("IMPLEMENTED", "Histórico visual de fotos com consentimento", "website/models.py, website/views.py", "TestLGPDAndViews"),
    171: ("IMPLEMENTED", "Assistente de agendamento em linguagem natural conectado ao banco", "website/services/ai_assistant_service.py", "TestAIAssistantService"),
    172: ("IMPLEMENTED", "Respostas de gestão administrativa em linguagem natural", "website/services/ai_assistant_service.py", "TestAIAssistantService"),
    174: ("IMPLEMENTED", "Match de compatibilidade entre cliente e barbeiro", "website/services/ai_assistant_service.py", "TestAIAssistantService"),
    175: ("IMPLEMENTED", "Recomendações não intrusivas de upsell de produtos", "website/services/ai_assistant_service.py", "TestAIAssistantService"),
    199: ("IMPLEMENTED", "Pagamento dividido em múltiplos métodos (PIX, Dinheiro, Cartão, Saldo)", "website/services/payment_service.py", "TestSplitPaymentsAndConsumableKits"),
    200: ("IMPLEMENTED", "Controle de saldo interno na ContaCorrenteCliente (sem gift card)", "website/models.py, website/services/payment_service.py", "TestSplitPaymentsAndConsumableKits"),
    201: ("IMPLEMENTED", "Estorno parcial ou total com trilha de auditoria", "website/services/payment_service.py", "TestSplitPaymentsAndConsumableKits"),
    204: ("IMPLEMENTED", "Registro segregado de gorjetas vinculadas ao barbeiro", "website/models.py, website/services/payment_service.py", "TestSplitPaymentsAndConsumableKits"),
    214: ("IMPLEMENTED", "Kit de Consumo de Insumos com baixa automática por serviço", "website/services/inventory_service.py", "TestSplitPaymentsAndConsumableKits"),
    215: ("IMPLEMENTED", "Múltiplos locais de estoque (Depósito, Recepção, Bancada)", "website/models.py, website/services/inventory_service.py", "TestInventory"),
    216: ("IMPLEMENTED", "Transferência atômica de estoque entre locais", "website/services/inventory_service.py", "TestInventory"),
    217: ("IMPLEMENTED", "Registro de perdas e avarias de estoque", "website/services/inventory_service.py", "TestInventory"),
    218: ("IMPLEMENTED", "Sugestão inteligente de reposição de estoque", "website/services/inventory_service.py", "TestInventory"),
    219: ("IMPLEMENTED", "Inventário físico com apuração de divergências", "website/services/inventory_service.py", "TestInventory"),
    245: ("IMPLEMENTED", "Abertura de caixa diário com fundo de troco", "website/services/finance_service.py", "TestFinanceService"),
    246: ("IMPLEMENTED", "Sangria e suprimento de caixa diário", "website/services/finance_service.py", "TestFinanceService"),
    247: ("IMPLEMENTED", "Fechamento cego de caixa e cálculo de quebra/diferença", "website/services/finance_service.py", "TestFinanceService"),
    262: ("IMPLEMENTED", "DRE Simplificado com Receitas, Custos, Comissões e Despesas", "website/services/finance_service.py, website/templates/website/admin/dre.html", "TestFinanceService"),
    263: ("IMPLEMENTED", "Rentabilidade e margem de contribuição por serviço e por hora", "website/services/finance_service.py", "TestFinanceService"),
    264: ("IMPLEMENTED", "Simulador de impacto de reajuste de preços", "website/services/finance_service.py", "TestFinanceService"),
    265: ("IMPLEMENTED", "Simulador de comissões e impacto no caixa", "website/services/finance_service.py", "TestFinanceService"),
    266: ("IMPLEMENTED", "Simulador de campanhas promocionais com desconto", "website/services/finance_service.py", "TestFinanceService"),
    347: ("IMPLEMENTED", "Registro permanente de auditoria para ações administrativas", "website/services/audit_service.py", "TestAuditService"),
    367: ("IMPLEMENTED", "Central de Privacidade e Consentimentos LGPD do Cliente", "website/views.py, website/templates/website/cliente/lgpd.html", "TestLGPDAndViews"),
    372: ("IMPLEMENTED", "Exportação estruturada de dados pessoais em JSON (Portabilidade LGPD)", "website/views.py", "TestLGPDAndViews"),
    378: ("IMPLEMENTED", "Modo Recepção com operação rápida de check-in, fila e comandas", "website/views.py, website/templates/website/recepcao.html", "TestLGPDAndViews"),
    380: ("IMPLEMENTED", "Modo TV em tela cheia para sala de espera", "website/views.py, website/templates/website/modo_tv.html", "TestLGPDAndViews"),
    391: ("IMPLEMENTED", "Cardápio Digital de serviços, combos e produtos via QR Code", "website/views.py, website/templates/website/cardapio_digital.html", "TestLGPDAndViews"),
}

def update_requirements():
    doc_path = Path(__file__).resolve().parent.parent / 'docs' / 'DELACRUZ_REQUIREMENTS_402.md'
    lines = doc_path.read_text(encoding='utf-8').splitlines()
    new_lines = []

    for line in lines:
        match = re.match(r'\|\s*REQ-(\d{3})\s*\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|', line)
        if match:
            num = int(match.group(1))
            req_title = match.group(2).strip()
            status = match.group(3).strip()
            impl = match.group(4).strip()
            files = match.group(5).strip()
            tests = match.group(6).strip()
            obs = match.group(7).strip()

            if num in IMPLEMENTED_REQS:
                new_status, new_impl, new_files, new_tests = IMPLEMENTED_REQS[num]
                new_line = f"| REQ-{num:03d} | {req_title} | {new_status} | {new_impl} | `{new_files}` | `{new_tests}` | {obs} |"
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    doc_path.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')
    print("Updated docs/DELACRUZ_REQUIREMENTS_402.md successfully!")

if __name__ == '__main__':
    update_requirements()
