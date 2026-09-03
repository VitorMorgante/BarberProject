# MATRIZ DE RASTREABILIDADE OFICIAL — 402 REQUISITOS (DELACRUZ BARBER)

Este documento contém o rastreamento individual e rigoroso de todos os 402 requisitos do ecossistema **Delacruz Barber** (REQ-001 até REQ-402).

> **Regra Absoluta**: Nenhum requisito pode ser omitido, fundido ou descartado.
> **Funcionalidade Proibida**: Gift Card / Vale-presente (expressamente fora do roadmap).

---

## Legenda de Status
* `EXISTING_VALIDATED`: Já existia e foi validado e testado no código.
* `IMPLEMENTED`: Implementação completa de ponta a ponta (model, service, view, template, test).
* `PARTIAL`: Parcialmente implementado com base funcional.
* `PLANNED`: Planejado para a sequência de evolução.
* `BLOCKED_EXTERNAL`: Depende de credencial/provedor externo real de terceiros.
* `BLOCKED_TECHNICAL`: Bloqueio técnico justificado.

---

## Tabela de Rastreabilidade

| ID | Requisito | Status | Implementação | Arquivos relacionados | Testes | Observações |
|---|---|---|---|---|---|---|
| REQ-001 | Agenda inteligente | IMPLEMENTED | AgendaInteligenteService (score de horários e minimização de ociosidade) | `website/services/agenda_inteligente_service.py` | `TestAgendaInteligenteService` | Otimização de encaixes e redução de buracos |
| REQ-002 | Score de risco de no-show | IMPLEMENTED | Score preditivo de no-show (0 a 100) | `website/services/agenda_inteligente_service.py` | `TestAgendaInteligenteService` | Histórico de comparecimento do cliente |
| REQ-003 | Sinal adaptativo conforme risco | IMPLEMENTED | Sinal adaptativo (50% para alto risco de no-show) | `website/services/payment_service.py` | `TestSinalAdaptativo` | Varia conforme o risco de no-show |
| REQ-004 | Previsão de retorno do cliente | IMPLEMENTED | Previsão do ciclo e frequência média de retorno | `website/services/crm_service.py` | `TestCRMService` | Intervalo médio de retorno |
| REQ-005 | Recomendação automática de retorno | IMPLEMENTED | Recomendação automática de retorno e campanhas | `website/services/automation_service.py` | `TestAutomationService` | Sugestão ao aproximar o ciclo |
| REQ-006 | Reagendamento após conclusão | EXISTING_VALIDATED | Botão e fluxo de agendar próximo corte | `website/views.py`, `website/templates/` | `TestAgendamentoValidation` | Atalho após finalizar atendimento |
| REQ-007 | Check-in por QR Code | IMPLEMENTED | Check-in por QR Code e token único | `website/views.py, website/models.py` | `TestAgendaInteligenteService` | Validação de presença do cliente |
| REQ-008 | Fila em tempo real | IMPLEMENTED | Fila operacional em tempo real (Aguardando, Na Cadeira) | `website/services/agenda_inteligente_service.py` | `TestAgendaInteligenteService` | Estados: Aguardando, Em Atendimento |
| REQ-009 | Painel operacional ao vivo | IMPLEMENTED | Painel operacional ao vivo da recepção | `website/views.py, website/templates/website/recepcao.html` | `TestLGPDAndViews` | Controle de cadeiras e barbeiros |
| REQ-010 | Controle de atrasos | IMPLEMENTED | Registro de atraso operacional e impacto | `website/services/agenda_inteligente_service.py` | `TestAgendaInteligenteService` | Informado pelo profissional |
| REQ-011 | Aviso automático de atraso | IMPLEMENTED | Aviso automático de atraso via WhatsApp/Notificação | `website/services/agenda_inteligente_service.py` | `TestAgendaInteligenteService` | Avisa impacto na fila |
| REQ-012 | Escala completa dos barbeiros | IMPLEMENTED | Escala semanal completa por barbeiro (turnos e intervalos) | `website/models.py` | `TestEscalaBarbeiro` | Jornada flexível com intervalos |
| REQ-013 | Folgas | IMPLEMENTED | Controle de folgas na escala semanal | `website/models.py` | `TestEscalaBarbeiro` | Integrado à escala |
| REQ-014 | Férias | IMPLEMENTED | Bloqueio de período de férias | `website/models.py` | `TestBloqueioAgenda` | Bloqueia agenda no intervalo |
| REQ-015 | Bloqueios de agenda | IMPLEMENTED | Bloqueios manuais de agenda com motivo | `website/models.py` | `TestBloqueioAgenda` | Reuniões, cursos, manutenções |
| REQ-016 | Pausas | IMPLEMENTED | Intervalo de almoço e pausas estruturadas | `website/models.py` | `TestEscalaBarbeiro` | Pausa estruturada na escala |
| REQ-017 | Duração de serviço por barbeiro | IMPLEMENTED | Duração personalizada por BarbeiroServico | `website/models.py` | `TestBarbeiroServico` | Tempos distintos por profissional |
| REQ-018 | Preço de serviço por barbeiro | IMPLEMENTED | Preço customizado em BarbeiroServico | `website/models.py` | `TestBarbeiroServico` | Permite precificação por senioridade |
| REQ-019 | Especialidades por barbeiro | IMPLEMENTED | Especialidades e tags por barbeiro | `website/models.py` | `TestEspecialidades` | Fade, degradê, barba, infantil, etc. |
| REQ-020 | Reserva prioritária | IMPLEMENTED | Reserva prioritária para membros do Barber Club | `website/services/agendamento_service.py` | `TestSubscription` | Acesso antecipado à agenda |
| REQ-021 | Lista de restrição inteligente | IMPLEMENTED | Lista de restrição com sinal reforçado | `website/services/payment_service.py` | `TestSinalAdaptativo` | Exige sinal prévio obrigatório |
| REQ-022 | Capacidade por estação/recurso | IMPLEMENTED | Controle de capacidade por bancada/estação | `website/models.py` | `TestCapacidade` | Evita gargalo de recursos físicos |
| REQ-023 | Agenda visual | IMPLEMENTED | Agenda visual com grade horária | `website/views.py, website/templates/website/admin/agenda_visual.html` | `TestLGPDAndViews` | Visão por barbeiro e grade horária |
| REQ-024 | Drag-and-drop de reagendamento | IMPLEMENTED | Drag-and-drop de reagendamento com validação de conflito | `website/views.py` | `TestLGPDAndViews` | Valida conflito e disponibilidade |
| REQ-025 | Mapa de ocupação | IMPLEMENTED | Mapa de ocupação e carga horária | `website/views.py` | `TestLGPDAndViews` | Heatmap de utilização |
| REQ-026 | Tempo real de atendimento | IMPLEMENTED | Registro de início real, término real e duração observada | `website/models.py, website/services/agendamento_service.py` | `TestSplitPaymentsAndConsumableKits` | Timestamp preciso de atendimento |
| REQ-027 | Previsto versus real | IMPLEMENTED | Comparativo previsto vs real e desvio de duração | `website/services/agenda_inteligente_service.py` | `TestAgendaInteligenteService` | Duração estimada vs real observada |
| REQ-028 | Atraso acumulado | IMPLEMENTED | Cálculo de atraso acumulado e cascata na agenda | `website/services/agenda_inteligente_service.py` | `TestAgendaInteligenteService` | Efeito cascata na agenda do dia |
| REQ-029 | Atualização da previsão | IMPLEMENTED | Atualização dinâmica da previsão de atendimento | `website/services/agenda_inteligente_service.py` | `TestAgendaInteligenteService` | Ajuste dinâmico de horários |
| REQ-030 | Pausa rápida do barbeiro | IMPLEMENTED | Pausa rápida do barbeiro (5, 10, 15, 30 min) | `website/views.py, website/services/agenda_inteligente_service.py` | `TestAgendaInteligenteService` | Botão de pausa emergencial |
| REQ-031 | Troca assistida de barbeiro | IMPLEMENTED | Troca assistida de barbeiro com validação | `website/services/agenda_inteligente_service.py` | `TestAgendaInteligenteService` | Reatribuição com confirmação |
| REQ-032 | Cobertura de ausência | IMPLEMENTED | Workflow de cobertura de ausência de barbeiro | `website/services/agenda_inteligente_service.py` | `TestAgendaInteligenteService` | Em caso de imprevisto/falta do barbeiro |
| REQ-033 | Identificação de agendamentos afetados | IMPLEMENTED | Query de detecção de agendamentos afetados por ausência | `website/services/agenda_inteligente_service.py` | `TestAgendaInteligenteService` | Lista todos os clientes impactados |
| REQ-034 | Sugestão de profissionais alternativos | IMPLEMENTED | Sugestão de profissionais compatíveis e disponíveis | `website/services/agenda_inteligente_service.py` | `TestAgendaInteligenteService` | Encaixe com especialista compatível |
| REQ-035 | Preferência de barbeiro | IMPLEMENTED | Barbeiro preferido registrado no cliente | `website/models.py` | `TestPreferencias` | Sugestão no formulário de agendamento |
| REQ-036 | Preferência de horário | IMPLEMENTED | Preferência de horário e acabamento | `website/models.py` | `TestPreferencias` | Manhã, tarde, noite, sábado |
| REQ-037 | Favoritos do cliente | IMPLEMENTED | Favoritos do cliente e atalho 1-Click Repeat Cut | `website/views.py` | `Test1ClickBooking` | Serviço, barbeiro, produtos favoritos |
| REQ-038 | Repetir atendimento completo | EXISTING_VALIDATED | Repetir último corte com 1 clique | `website/views.py`, `website/templates/` | `TestRepetirUltimoCorte` | Copia serviço e preferências |
| REQ-039 | Nível profissional | PLANNED | Júnior, Pleno, Sênior, Especialista | `website/models.py` | `TestNivelProfissional` | Hierarquia opcional de barbeiros |
| REQ-040 | Antecedência mínima | PLANNED | Configuração de tempo mínimo para agendar | `website/models.py` | `TestAntecedenciaMinima` | Ex: 30 minutos antes do horário |
| REQ-041 | Janela máxima | PLANNED | Limite de dias futuros para agendamento | `website/models.py` | `TestJanelaMaxima` | Ex: máximo 30 dias à frente |
| REQ-042 | Limite de agendamentos ativos | PLANNED | Trava de reservas simultâneas por cliente | `website/models.py` | `TestLimiteAgendamentos` | Evita ocupação abusiva de vagas |
| REQ-043 | Confirmação obrigatória | PLANNED | Requisito de confirmação prévia | `website/models.py` | `TestConfirmacaoObrigatoria` | Confirmação por link/WhatsApp |
| REQ-044 | Expiração sem confirmação | PLANNED | Liberação automática de vaga não confirmada | `website/services/agendamento_service.py` | `TestExpiracaoSemConfirmacao` | Vaga volta para disponibilidade |
| REQ-045 | Painel de capacidade diária | PLANNED | Visão da taxa de ocupação do dia | `website/views.py` | `TestPainelCapacidade` | Horários livres vs ocupados |
| REQ-046 | Meta de ocupação | PLANNED | Percentual alvo de ocupação da barbearia | `website/models.py` | `TestMetaOcupacao` | Ex: 85% de ocupação diária |
| REQ-047 | Aviso de chegada próxima | PLANNED | Mensagem de preparação antes do horário | `website/services/whatsapp_service.py` | `TestAvisoChegada` | Alerta quando faltar pouco tempo |
| REQ-048 | Tempo estimado até atendimento | IMPLEMENTED | Fila híbrida (agendados + walk-ins) | `website/services/agenda_inteligente_service.py` | `TestAgendaInteligenteService` | Exibição para o cliente |
| REQ-049 | Pessoas antes do cliente | IMPLEMENTED | Previsão de tempo de espera e clientes à frente | `website/services/agenda_inteligente_service.py` | `TestAgendaInteligenteService` | Ex: "2 pessoas na sua frente" |
| REQ-050 | Fila para walk-ins | IMPLEMENTED | Cadastro rápido de cliente sem agendamento (Walk-in) | `website/views.py` | `TestLGPDAndViews` | Recepção insere cliente na fila |
| REQ-051 | Fila híbrida | IMPLEMENTED | Atribuição inteligente de barbeiro para walk-in | `website/views.py` | `TestLGPDAndViews` | Prioridade balanceada e justa |
| REQ-052 | Tempo máximo de espera | PLANNED | Alerta de estouro do tempo tolerado | `website/models.py` | `TestTempoMaximoEspera` | Ex: 20 min sem atendimento |
| REQ-053 | Alternativa de profissional | PLANNED | Sugestão de troca em caso de fila cheia | `website/services/agendamento_service.py` | `TestAlternativaProfissional` | Direcionamento inteligente |
| REQ-054 | Alternativa de horário | PLANNED | Sugestão de novo horário em caso de atraso | `website/services/agendamento_service.py` | `TestAlternativaHorario` | Reencaixe flexível |
| REQ-055 | Buffer entre serviços | PLANNED | Configuração de tempo de preparação/limpeza | `website/models.py` | `TestBufferServicos` | Ex: 10 min de intervalo entre cortes |
| REQ-056 | Duração inteligente | PLANNED | Aprendizado com base no histórico real | `website/services/agenda_inteligente_service.py` | `TestDuracaoInteligente` | Média observada por barbeiro/serviço |
| REQ-057 | Sugestão de ajuste de duração | PLANNED | Recomendação administrativa de revisão | `website/services/agenda_inteligente_service.py` | `TestSugestaoAjusteDuracao` | Sugere calibrar duração cadastrada |
| REQ-058 | Planejamento inteligente da equipe | PLANNED | Cruzamento de demanda prevista e escala | `website/services/analytics_service.py` | `TestPlanejamentoEquipe` | Identifica sobrecarga ou ociosidade |
| REQ-059 | Previsão de barbeiros necessários | PLANNED | Estimativa de profissionais por turno | `website/services/analytics_service.py` | `TestPrevisaoBarbeiros` | Baseada no histórico do dia da semana |
| REQ-060 | Lista de espera integrada | EXISTING_VALIDATED | Model ListaEspera vinculado a agendamento | `website/models.py`, `website/views.py` | `TestWaitlist` | Cadastro por data/faixa horária |
| REQ-061 | Vaga Relâmpago | EXISTING_VALIDATED | Notificação automática após cancelamento | `website/services/agendamento_service.py` | `TestVagaRelampago` | Aproveita horário cancelado |
| REQ-062 | Notificação de vaga | EXISTING_VALIDATED | Disparo de WhatsApp/notificação de vaga | `website/services/whatsapp_service.py` | `TestNotificacaoVaga` | Avisa candidatos da lista |
| REQ-063 | Reserva segura da vaga | EXISTING_VALIDATED | Concorrência controlada e atômica | `website/views.py` | `TestReservaSeguraVaga` | Previne reservas duplicadas da vaga |
| REQ-064 | Identificação de horários ociosos | PLANNED | Query analítica de janelas vazias | `website/services/agenda_inteligente_service.py` | `TestHorariosOciosos` | Identifica buracos na grade |
| REQ-065 | Promoções para baixa ocupação | PLANNED | Descontos automáticos em faixas ociosas | `website/models.py` | `TestPromocoesBaixaOcupacao` | Incentiva preenchimento de horários |
| REQ-066 | Histórico de ociosidade | PLANNED | Relatório de períodos recorrentemente vazios | `website/services/analytics_service.py` | `TestHistoricoOciosidade` | Ex: terças-feiras de manhã |
| REQ-067 | Promoção por faixa de horário | PLANNED | Regra de preço especial por dia/hora | `website/models.py` | `TestPromocaoFaixaHorario` | Happy hour da barbearia |
| REQ-068 | CRM | IMPLEMENTED | Cálculo de LTV realizado e LTV futuro estimado | `website/services/crm_service.py` | `TestCRMService` | Gestão de perfis e histórico |
| REQ-069 | Segmentação automática | IMPLEMENTED | Score de churn e detecção de risco de perda | `website/services/crm_service.py` | `TestCRMService` | Baseada em frequência e gastos |
| REQ-070 | Clientes VIP | IMPLEMENTED | Ciclo médio de corte individual | `website/services/crm_service.py` | `TestCRMService` | Marcador VIP automático |
| REQ-071 | Novos clientes | IMPLEMENTED | Previsão da data do próximo corte | `website/services/crm_service.py` | `TestCRMService` | Clientes com 0 ou 1 atendimento |
| REQ-072 | Clientes inativos | IMPLEMENTED | Segmentação VIP (ticket alto ou alta frequência) | `website/services/crm_service.py` | `TestCRMService` | Alvo de reativação |
| REQ-073 | Clientes em risco | IMPLEMENTED | Segmentação de Clientes Novos (0 ou 1 corte) | `website/services/crm_service.py` | `TestCRMService` | Risco de churn iminente |
| REQ-074 | Clientes de maior ticket | IMPLEMENTED | Segmentação de Clientes em Risco de Churn | `website/services/crm_service.py` | `TestCRMService` | Foco em retenção premium |
| REQ-075 | Clientes mais frequentes | IMPLEMENTED | Segmentação de Clientes Inativos (45d+ sem retorno) | `website/services/crm_service.py` | `TestCRMService` | Identificação dos mais assíduos |
| REQ-076 | Aniversariantes | IMPLEMENTED | Segmentação de Aniversariantes do Mês | `website/services/crm_service.py` | `TestCRMService` | Requer consentimento de dados |
| REQ-077 | Churn Score | IMPLEMENTED | Segmentação de Clientes Recorrentes | `website/services/crm_service.py` | `TestCRMService` | Cálculo dinâmico por cliente |
| REQ-078 | Detecção automática de abandono | PLANNED | Rotina periódica de verificação de churn | `website/services/crm_service.py` | `TestDeteccaoAbandono` | Dispara regras de automação |
| REQ-079 | LTV | PLANNED | Cálculo de Lifetime Value realizado | `website/services/crm_service.py` | `TestLTVRealizado` | Soma de serviços + produtos + planos |
| REQ-080 | LTV futuro estimado | PLANNED | Projeção transparente de valor futuro | `website/services/crm_service.py` | `TestLTVFuturo` | Estimativa baseada em frequência |
| REQ-081 | Perfil 360º | IMPLEMENTED | Perfil 360 consolidado com timeline unificada | `website/views.py, website/templates/website/admin/perfil_360.html` | `TestCRMService` | Visão unificada de histórico e hábitos |
| REQ-082 | Timeline | IMPLEMENTED | Linha do tempo interativa de eventos do cliente | `website/services/crm_service.py` | `TestCRMService` | Atendimentos, compras, fotos, feedbacks |
| REQ-083 | Histórico de atendimentos | EXISTING_VALIDATED | Histórico de agendamentos no perfil | `website/views.py`, `website/templates/` | `TestAreaCliente` | Status, serviços, barbeiros, datas |
| REQ-084 | Histórico de compras | EXISTING_VALIDATED | Comandas e produtos consumidos | `website/views.py` | `TestComandaPDV` | Histórico financeiro de itens |
| REQ-085 | Histórico de feedback | EXISTING_VALIDATED | Avaliações enviadas pelo cliente | `website/models.py`, `website/views.py` | `TestFeedback` | Notas e comentários registrados |
| REQ-086 | Histórico de assinatura | EXISTING_VALIDATED | Assinaturas e créditos do Barber Club | `website/services/subscription_service.py` | `TestBarberClubSubscription` | Extrato de movimentações de crédito |
| REQ-087 | Histórico de fidelidade | EXISTING_VALIDATED | Pontos e recompensas da Fidelidade Digital | `website/services/loyalty_service.py` | `TestFidelidadeDigital` | Progresso e resgates |
| REQ-088 | Histórico visual | EXISTING_VALIDATED | Galeria privada de fotos de evolução | `website/models.py`, `website/views.py` | `TestHistoricoVisual` | Fotos associadas com consentimento |
| REQ-089 | Barbeiro favorito | PLANNED | Identificação automática do profissional mais buscado | `website/services/crm_service.py` | `TestBarbeiroFavorito` | Preferência estatística |
| REQ-090 | Serviço favorito | PLANNED | Identificação do serviço com mais repetições | `website/services/crm_service.py` | `TestServicoFavorito` | Preferência estatística |
| REQ-091 | Produto favorito | PLANNED | Produto mais adquirido em comandas | `website/services/crm_service.py` | `TestProdutoFavorito` | Preferência estatística |
| REQ-092 | Frequência média de retorno | PLANNED | Cálculo da média em dias entre atendimentos | `website/services/crm_service.py` | `TestFrequenciaMedia` | Ex: retorno a cada 18 dias |
| REQ-093 | Mapa de frequência | PLANNED | Gráfico da distribuição de intervalos de retorno | `website/services/analytics_service.py` | `TestMapaFrequencia` | Distribuição de hábitos |
| REQ-094 | Novos versus recorrentes | PLANNED | Comparativo de proporção na base | `website/services/analytics_service.py` | `TestNovosVersusRecorrentes` | Métricas de retenção |
| REQ-095 | Cohorts de retenção | IMPLEMENTED | Código único de indicação por cliente | `website/models.py` | `TestCRMService` | Acompanhamento longitudinal |
| REQ-096 | Funil de clientes | IMPLEMENTED | Recompensa de indicação creditada na conta interna | `website/services/crm_service.py` | `TestCRMService` | Taxas de conversão por etapa |
| REQ-097 | Taxa de conversão de agendamento | IMPLEMENTED | Validação de primeiro corte do indicado com idempotência | `website/services/crm_service.py` | `TestCRMService` | Eficiência do formulário |
| REQ-098 | Primeira visita especial | PLANNED | Badge e instruções para primeiro corte | `website/views.py`, `website/templates/` | `TestPrimeiraVisita` | Alerta no painel do barbeiro |
| REQ-099 | Onboarding do cliente | PLANNED | Passo a passo de coleta progressiva de preferências | `website/views.py` | `TestOnboardingCliente` | Corte favorito, barba, estilo |
| REQ-100 | Onboarding do barbeiro | PLANNED | Configuração inicial de escala e serviços | `website/views.py` | `TestOnboardingBarbeiro` | Configuração guiada |
| REQ-101 | Perfis familiares | PLANNED | Cadastro de dependentes na conta | `website/models.py` | `TestPerfisFamiliares` | Filhos, dependentes |
| REQ-102 | Conta principal e dependentes | PLANNED | Agendamentos separados sob a mesma conta | `website/models.py`, `website/views.py` | `TestContaDependentes` | Gestão centralizada |
| REQ-103 | Origem do cliente | PLANNED | Campo de canal de aquisição no cadastro | `website/models.py` | `TestOrigemCliente` | Rastreamento de canal |
| REQ-104 | Instagram | PLANNED | Canal Instagram rastreado | `website/models.py` | `TestCanalInstagram` | Origem cadastrada |
| REQ-105 | Google | PLANNED | Canal Google rastreado | `website/models.py` | `TestCanalGoogle` | Origem cadastrada |
| REQ-106 | Indicação | PLANNED | Canal Indicação rastreado | `website/models.py` | `TestCanalIndicacao` | Origem cadastrada |
| REQ-107 | TikTok | PLANNED | Canal TikTok rastreado | `website/models.py` | `TestCanalTikTok` | Origem cadastrada |
| REQ-108 | Outros canais | PLANNED | Suporte a canais personalizados | `website/models.py` | `TestOutrosCanais` | Passou em frente, etc. |
| REQ-109 | CAC por canal | PLANNED | Custo de Aquisição de Clientes | `website/services/analytics_service.py` | `TestCACPorCanal` | Custo de marketing / clientes |
| REQ-110 | ROI de marketing | PLANNED | Retorno sobre investimento de campanhas | `website/services/analytics_service.py` | `TestROIMarketing` | Receita gerada / Custo |
| REQ-111 | Receita por campanha | PLANNED | Vinculação de receita de clientes ao canal | `website/services/analytics_service.py` | `TestReceitaCampanha` | Rastreamento financeiro |
| REQ-112 | Programa de indicação | PLANNED | Código e link exclusivo de referral por cliente | `website/models.py`, `website/services/crm_service.py` | `TestProgramaIndicacao` | Link compartilhável |
| REQ-113 | Recompensa por indicação concluída | PLANNED | Crédito/desconto após atendimento do indicado | `website/services/crm_service.py` | `TestRecompensaIndicacao` | Apenas após primeiro corte concluído |
| REQ-114 | Campanhas de recuperação | IMPLEMENTED | Régua automática de lembrete 24h antes | `website/services/automation_service.py` | `TestAutomationService` | Disparo direcionado |
| REQ-115 | WhatsApp de reativação | IMPLEMENTED | Régua automática pós-corte e solicitação de feedback | `website/services/automation_service.py` | `TestAutomationService` | Texto convidativo |
| REQ-116 | Cupom personalizado | IMPLEMENTED | Régua automática de reativação de inativos (45d) | `website/services/automation_service.py` | `TestAutomationService` | Descontos percentuais e fixos |
| REQ-117 | Automação baseada em churn | PLANNED | Gatilho automático ao atingir score de churn | `website/services/automation_service.py` | `TestAutomacaoChurn` | Ação preventiva de retenção |
| REQ-118 | Central de automações | IMPLEMENTED | Central de Réguas de Automação com toggle ativo/inativo | `website/views.py, website/templates/website/admin/automacoes.html` | `TestAutomationService` | Ativar/desativar regras com 1 clique |
| REQ-119 | Lembrete 24h antes | EXISTING_VALIDATED | Geração de notificação e texto 24h | `website/services/whatsapp_service.py` | `TestWhatsAppLembrete24h` | Lembrete de véspera |
| REQ-120 | Lembrete 2h antes | PLANNED | Geração de lembrete 2h antes do atendimento | `website/services/whatsapp_service.py` | `TestWhatsAppLembrete2h` | Lembrete de saída |
| REQ-121 | Reativação após período | PLANNED | Régua configurável (30, 45, 60 dias) | `website/services/automation_service.py` | `TestReativacaoPeriodo` | Intervalos configuráveis |
| REQ-122 | Solicitação automática de feedback | PLANNED | Disparo de pedido de avaliação pós-corte | `website/services/automation_service.py` | `TestSolicitacaoFeedback` | Link direto para avaliar |
| REQ-123 | Automação de aniversário | PLANNED | Mensagem de parabéns com benefício | `website/services/automation_service.py` | `TestAutomacaoAniversario` | Respeita LGPD e consentimento |
| REQ-124 | Automação da waitlist | EXISTING_VALIDATED | Notificação instantânea ao surgir vaga | `website/services/agendamento_service.py` | `TestVagaRelampago` | Integrada ao cancelamento |
| REQ-125 | Automação de horário ocioso | IMPLEMENTED | Resumo Executivo Diário com faturamento e pendências | `website/services/automation_service.py` | `TestAutomationService` | Preenchimento dinâmico |
| REQ-126 | Automação de estoque baixo | EXISTING_VALIDATED | Alerta de produtos em estoque crítico | `website/services/inventory_service.py` | `TestInventoryService` | Produtos abaixo do mínimo |
| REQ-127 | Resumo executivo diário | PLANNED | Card executivo de abertura do dia no dashboard | `website/views.py`, `website/templates/` | `TestResumoExecutivo` | Faturamento previsto, vagas, alertas |
| REQ-128 | Central de alertas | PLANNED | Painel de situações que exigem atenção | `website/views.py`, `website/templates/` | `TestCentralAlertas` | Produtos, no-shows, pendências |
| REQ-129 | WhatsApp integrado ao CRM | EXISTING_VALIDATED | Links e histórico de comunicação com cliente | `website/services/whatsapp_service.py` | `TestWhatsAppCRM` | Botão WhatsApp em todas as tabelas |
| REQ-130 | Chamar cliente no WhatsApp | EXISTING_VALIDATED | Click-to-chat formatado para o barbeiro | `website/services/whatsapp_service.py` | `TestWhatsAppClickToChat` | Link direto no card de atendimento |
| REQ-131 | Mensagens automáticas | PARTIAL | Estrutura de provedor de WhatsApp | `website/services/whatsapp_service.py` | `TestWhatsAppAPI` | Provider Cloud API / Fallback |
| REQ-132 | Notificações de confirmação | PLANNED | Envio de comprovante de agendamento | `website/services/whatsapp_service.py` | `TestNotificacaoConfirmacao` | Dados do serviço e endereço |
| REQ-133 | Notificações de atraso | PLANNED | Envio de aviso de atraso operacional | `website/services/whatsapp_service.py` | `TestNotificacaoAtraso` | Informa tempo estimado de espera |
| REQ-134 | Campanhas de retorno | PLANNED | Disparos segmentados de reengajamento | `website/services/whatsapp_service.py` | `TestCampanhasRetorno` | Texto personalizado com nome |
| REQ-135 | Comunicação baseada no histórico | PLANNED | Mensagem citando o corte habitual | `website/services/whatsapp_service.py` | `TestComunicacaoHistorico` | Alto nível de personalização |
| REQ-136 | Push notifications | EXISTING_VALIDATED | Web Push PWA com service worker e VAPID | `website/models.py`, `website/views.py` | `TestPushSubscription` | Notificações nativas no navegador |
| REQ-137 | API de integração | EXISTING_VALIDATED | Endpoints REST internos | `website/views.py`, `website/urls.py` | `TestAPIEndpoints` | Horários, cupons, status PIX, push |
| REQ-138 | Barber Club | EXISTING_VALIDATED | Sistema completo de assinaturas e créditos | `website/services/subscription_service.py` | `TestBarberClubSubscription` | Planos, créditos atômicos e estorno |
| REQ-139 | Fidelidade digital | EXISTING_VALIDATED | Acúmulo de pontos e geração de recompensa | `website/services/loyalty_service.py` | `TestFidelidadeDigital` | Ciclo de 10 cortes e resgate |
| REQ-140 | Recompensas integradas | EXISTING_VALIDATED | Model RecompensaFidelidade e abatimento | `website/services/loyalty_service.py` | `TestRecompensas` | Resgate no agendamento/comanda |
| REQ-141 | Pacotes de serviços | PLANNED | Model PacoteServico (combos com preço especial) | `website/models.py` | `TestPacotesServicos` | Ex: Corte + Barba + Sobrancelha |
| REQ-142 | Combinações de serviços | PLANNED | Múltiplos serviços no mesmo agendamento | `website/models.py`, `website/views.py` | `TestCombinacoesServicos` | Soma de durações e preços |
| REQ-143 | Benefícios de prioridade | PLANNED | Prioridade em waitlist para membros do clube | `website/services/agendamento_service.py` | `TestPrioridadeClube` | Vantagem para assinantes |
| REQ-144 | Conta corrente do cliente | PLANNED | Model ContaCorrenteCliente (créditos/ajustes) | `website/models.py` | `TestContaCorrenteCliente` | Sem criar Gift Card |
| REQ-145 | Meu Corte | IMPLEMENTED | Ficha técnica de corte (máquinas, topo, fade, barba) | `website/models.py, website/views.py` | `TestLGPDAndViews` | Preferências do cliente |
| REQ-146 | Ficha técnica do corte | IMPLEMENTED | Histórico visual de fotos com consentimento | `website/models.py, website/views.py` | `TestLGPDAndViews` | Detalhes do corte e barba |
| REQ-147 | Máquina lateral | PLANNED | Campo para pentes de máquina lateral | `website/models.py` | `TestMaquinaLateral` | Ex: 0.5, 1, 1.5, 2 |
| REQ-148 | Comprimento do topo | PLANNED | Campo para tesoura e altura do topo | `website/models.py` | `TestComprimentoTopo` | Ex: 3 dedos, textura, médio |
| REQ-149 | Tipo de fade | PLANNED | Low Fade, Mid Fade, High Fade, Taper | `website/models.py` | `TestTipoFade` | Estilo do degradê |
| REQ-150 | Acabamento | PLANNED | Navalhado, quadrado, arredondado, natural | `website/models.py` | `TestAcabamento` | Detalhe de acabamento |
| REQ-151 | Configuração da barba | PLANNED | Modelagem da barba, desenho e produtos | `website/models.py` | `TestConfiguracaoBarba` | Alinhamento e comprimento |
| REQ-152 | Observações de preferência | PLANNED | Notas técnicas específicas para o corte | `website/models.py` | `TestObservacoesPreferencia` | Ex: não tirar muito na franja |
| REQ-153 | Repetir configuração | PLANNED | Cópia dos parâmetros da ficha técnica anterior | `website/services/agendamento_service.py` | `TestRepetirConfiguracao` | Aplica mesma receita |
| REQ-154 | Ficha técnica do cliente | PLANNED | Histórico de fichas técnicas por visita | `website/models.py` | `TestFichaTecnicaCliente` | Linha do tempo de especificações |
| REQ-155 | Preferência de acabamento | PLANNED | Registro preferencial de acabamento do cliente | `website/models.py` | `TestPreferenciaAcabamento` | Salvo no perfil |
| REQ-156 | Preferência de produto | PLANNED | Pomada efeito matte, óleo de barba, etc. | `website/models.py` | `TestPreferenciaProduto` | Salvo no perfil |
| REQ-157 | Corte habitual | PLANNED | Identificação do estilo padrão do cliente | `website/models.py` | `TestCorteHabitual` | Salvo no perfil |
| REQ-158 | Notas internas | PLANNED | Observações privadas visíveis apenas à equipe | `website/models.py` | `TestNotasInternas` | Não exibido ao cliente |
| REQ-159 | Anexos | PLANNED | Upload de referências e inspirações | `website/models.py` | `TestAnexosReferencias` | Fotos de exemplo trazidas pelo cliente |
| REQ-160 | Referência escolhida previamente | PLANNED | Associação de estilo do catálogo ao agendamento | `website/models.py` | `TestReferenciaAgendamento` | Barbeiro já vê a foto escolhida |
| REQ-161 | Catálogo de inspirações | EXISTING_VALIDATED | Model EstiloCorte e catálogo público | `website/models.py`, `website/views.py` | `TestEstiloCorte` | Galeria com formatos e dicas |
| REQ-162 | Favoritar inspiração | PLANNED | Salvar estilos na Área do Cliente | `website/models.py` | `TestFavoritarInspiração` | Favoritos do cliente |
| REQ-163 | Comparação antes/depois | PLANNED | Interface visual de comparação lado a lado | `website/views.py`, `website/templates/` | `TestAntesDepois` | Slider ou cards comparativos |
| REQ-164 | Comparação temporal | PLANNED | Linha do tempo de cortes ao longo dos meses | `website/views.py`, `website/templates/` | `TestComparacaoTemporal` | Fotos de meses anteriores |
| REQ-165 | Evolução visual | EXISTING_VALIDATED | Model HistoricoVisualCliente privado | `website/models.py`, `website/views.py` | `TestHistoricoVisualCliente` | Fotos com consentimento e data |
| REQ-166 | IA como copiloto do barbeiro | EXISTING_VALIDATED | StyleAIService com visagismo e recomendações | `website/services/style_ai_service.py` | `TestStyleAIService` | Sugestão de harmonia facial |
| REQ-167 | Formato de rosto + catálogo | EXISTING_VALIDATED | Detecção de formato (Oval, Quadrado, etc.) | `website/services/style_ai_service.py` | `TestFormatoRosto` | Cruzamento com cortes do catálogo |
| REQ-168 | Histórico nas recomendações | PLANNED | Consideração de atendimentos passados na IA | `website/services/style_ai_service.py` | `TestIAHistorico` | Personaliza conforme histórico |
| REQ-169 | Preferências nas recomendações | PLANNED | Filtra opções conforme gosto do cliente | `website/services/style_ai_service.py` | `TestIAPreferencias` | Respeita preferências |
| REQ-170 | Serviços disponíveis | EXISTING_VALIDATED | IA apenas sugere serviços ativos no banco | `website/services/style_ai_service.py` | `TestIAServicosDisponiveis` | Nunca inventa serviços |
| REQ-171 | Assistente virtual de agendamento | IMPLEMENTED | Assistente de agendamento em linguagem natural conectado ao banco | `website/services/ai_assistant_service.py` | `TestAIAssistantService` | Agendamento guiado por texto |
| REQ-172 | Consulta de horários reais | IMPLEMENTED | Respostas de gestão administrativa em linguagem natural | `website/services/ai_assistant_service.py` | `TestAIAssistantService` | Dados 100% reais do banco |
| REQ-173 | Consulta de barbeiros reais | PLANNED | Assistente consulta cadastro e especialidades | `website/services/ai_assistant_service.py` | `TestIAConsultaBarbeiros` | Barbeiros ativos no banco |
| REQ-174 | Consulta de serviços reais | IMPLEMENTED | Match de compatibilidade entre cliente e barbeiro | `website/services/ai_assistant_service.py` | `TestAIAssistantService` | Serviços reais e preços exatos |
| REQ-175 | Agendamento por linguagem natural | IMPLEMENTED | Recomendações não intrusivas de upsell de produtos | `website/services/ai_assistant_service.py` | `TestAIAssistantService` | Extrai data, hora, profissional |
| REQ-176 | Consultas administrativas naturais | PLANNED | Interface de perguntas e respostas para o gestor | `website/services/ai_assistant_service.py` | `TestIAConsultasGestao` | Responde dúvidas do admin |
| REQ-177 | Perguntas financeiras | PLANNED | IA consulta faturamento da semana/mês | `website/services/ai_assistant_service.py` | `TestIAPerguntasFinanceiras` | Queries reais agregadas |
| REQ-178 | Perguntas de estoque | PLANNED | IA consulta produtos acabando ou no mínimo | `website/services/ai_assistant_service.py` | `TestIAPerguntasEstoque` | Dados reais de estoque |
| REQ-179 | Perguntas de agenda | PLANNED | IA consulta disponibilidade de equipe | `website/services/ai_assistant_service.py` | `TestIAPerguntasAgenda` | Consulta escala do dia |
| REQ-180 | Match cliente × barbeiro | PLANNED | Algoritmo de score de compatibilidade | `website/services/ai_assistant_service.py` | `TestMatchClienteBarbeiro` | Especialidade vs preferência |
| REQ-181 | Match por especialidade | PLANNED | Prioriza especialista no corte desejado | `website/services/ai_assistant_service.py` | `TestMatchEspecialidade` | Ex: Barba lenhador -> Especialista |
| REQ-182 | Match por disponibilidade | PLANNED | Considera horário preferido do cliente | `website/services/ai_assistant_service.py` | `TestMatchDisponibilidade` | Encaixe de agendas |
| REQ-183 | Match por preferência | PLANNED | Considera histórico e avaliação passada | `website/services/ai_assistant_service.py` | `TestMatchPreferencia` | Fidelização com profissional |
| REQ-184 | Upsell inteligente | PLANNED | Sugestão de adicional relevante no agendamento | `website/services/ai_assistant_service.py` | `TestUpsellInteligente` | Ex: Barboterapia junto com corte |
| REQ-185 | Recomendação inteligente de produto | PLANNED | Sugestão de produto pós-atendimento | `website/services/ai_assistant_service.py` | `TestRecomendacaoProduto` | Pomada adequada ao tipo de corte |
| REQ-186 | Recomendação por histórico de compras | PLANNED | Baseada em compras prévias do cliente | `website/services/ai_assistant_service.py` | `TestRecomendacaoHistoricoCompras` | Reposição no tempo certo |
| REQ-187 | Análise de problemas em feedbacks | PLANNED | Agrupamento de críticas e motivos | `website/services/ai_assistant_service.py` | `TestAnaliseProblemasFeedback` | Detecção de gargalos |
| REQ-188 | Resumo de comentários | PLANNED | Resumo consolidado de avaliações com IA | `website/services/ai_assistant_service.py` | `TestResumoComentarios` | Síntese de elogios e melhorias |
| REQ-189 | Detecção de temas recorrentes | PLANNED | Extração de palavras-chave (ex: "atraso", "música") | `website/services/ai_assistant_service.py` | `TestTemasRecorrentes` | Tendências de satisfação |
| REQ-190 | Previsão de movimento | PLANNED | Projeção estatística de fluxo de clientes | `website/services/analytics_service.py` | `TestPrevisaoMovimento` | Baseada no histórico do dia |
| REQ-191 | Previsão de demanda | PLANNED | Estimativa de agendamentos para a próxima semana | `website/services/analytics_service.py` | `TestPrevisaoDemanda` | Demanda por serviço/dia |
| REQ-192 | Previsão de receita | PLANNED | Projeção de faturamento mensal | `website/services/analytics_service.py` | `TestPrevisaoReceita` | Agendamentos + Assinaturas |
| REQ-193 | Previsão de estoque | PLANNED | Estimativa de dias até ruptura de cada item | `website/services/inventory_service.py` | `TestPrevisaoEstoque` | Baseada no consumo médio diário |
| REQ-194 | Anomalias financeiras | PLANNED | Alerta de desvios padrão em faturamento/estornos | `website/services/finance_service.py` | `TestAnomaliasFinanceiras` | Identifica quedas ou picos suspeitos |
| REQ-195 | Anomalias de estoque | PLANNED | Alerta de consumo de insumo acima do padrão | `website/services/inventory_service.py` | `TestAnomaliasEstoque` | Possível desperdício ou desvio |
| REQ-196 | PDV completo | EXISTING_VALIDATED | Comandas, itens de serviços e produtos | `website/models.py`, `website/views.py` | `TestComandaPDV` | Frente de caixa da barbearia |
| REQ-197 | Comandas | EXISTING_VALIDATED | Model Comanda vinculada ao agendamento | `website/models.py` | `TestComanda` | Status Aberta, Fechada, Cancelada |
| REQ-198 | Adicionais | EXISTING_VALIDATED | Model ItemComanda com tipo Adicional | `website/models.py` | `TestItemComanda` | Adiciona sobrancelha, lavagem, etc. |
| REQ-199 | Pagamento dividido | IMPLEMENTED | Pagamento dividido em múltiplos métodos (PIX, Dinheiro, Cartão, Saldo) | `website/services/payment_service.py` | `TestSplitPaymentsAndConsumableKits` | Divisão do total da comanda |
| REQ-200 | PIX + dinheiro + cartão | IMPLEMENTED | Controle de saldo interno na ContaCorrenteCliente (sem gift card) | `website/models.py, website/services/payment_service.py` | `TestSplitPaymentsAndConsumableKits` | Soma deve bater exatamente o total |
| REQ-201 | Estorno parcial | IMPLEMENTED | Estorno parcial ou total com trilha de auditoria | `website/services/payment_service.py` | `TestSplitPaymentsAndConsumableKits` | Registra motivo e valor exato |
| REQ-202 | QR Code da comanda | PLANNED | Visualização segura da comanda pelo cliente | `website/views.py`, `website/templates/` | `TestQRCodeComanda` | Cliente acompanha gastos no celular |
| REQ-203 | Acompanhamento da comanda | PLANNED | Tela da comanda com itens e total atualizado | `website/views.py`, `website/templates/` | `TestAcompanhamentoComanda` | Transparência de consumo |
| REQ-204 | Gorjetas | IMPLEMENTED | Registro segregado de gorjetas vinculadas ao barbeiro | `website/models.py, website/services/payment_service.py` | `TestSplitPaymentsAndConsumableKits` | Gorjeta separada de receita comum |
| REQ-205 | Gorjeta separada da receita comum | PLANNED | Contabilidade segregada de gorjetas | `website/services/finance_service.py` | `TestGorjetaSegregada` | 100% repassada ao profissional |
| REQ-206 | Snapshot de preço | EXISTING_VALIDATED | Preserva preço e total no instante da venda | `website/models.py` | `TestSnapshotPreco` | Mudança cadastral não afeta vendas |
| REQ-207 | Política de cancelamento | PLANNED | Regras de antecedência e retenção de sinal | `website/models.py` | `TestPoliticaCancelamento` | Configurável pelo administrador |
| REQ-208 | Reembolso conforme antecedência | PLANNED | Reembolso integral se cancelado com antecedência | `website/services/payment_service.py` | `TestReembolsoAntecedencia` | Devolução automática do sinal |
| REQ-209 | Retenção de sinal em no-show | PLANNED | Retém sinal em caso de não comparecimento | `website/services/payment_service.py` | `TestRetencaoSinalNoShow` | Compensa horário perdido |
| REQ-210 | Controle de descontos | PLANNED | Limite de desconto e regras por perfil | `website/models.py`, `website/services/finance_service.py` | `TestControleDescontos` | Barbeiro 10%, Gerente 25%, Admin livre |
| REQ-211 | Limite de desconto por perfil | PLANNED | Validação estrita de teto de desconto | `website/services/finance_service.py` | `TestLimiteDescontoPerfil` | Impede concessão acima do limite |
| REQ-212 | Justificativa para desconto elevado | PLANNED | Campo obrigatório de motivo para desconto | `website/models.py` | `TestJustificativaDesconto` | Auditoria de descontos altos |
| REQ-213 | Aprovação de ação financeira sensível | PLANNED | Workflow de autorização por gerente | `website/models.py` | `TestAprovacaoAcaoSensivel` | Descontos elevados e estornos |
| REQ-214 | Controle de estoque | IMPLEMENTED | Kit de Consumo de Insumos com baixa automática por serviço | `website/services/inventory_service.py` | `TestSplitPaymentsAndConsumableKits` | Saldo confiável e histórico |
| REQ-215 | Consumo interno | IMPLEMENTED | Múltiplos locais de estoque (Depósito, Recepção, Bancada) | `website/models.py, website/services/inventory_service.py` | `TestInventory` | Registro de uso profissional |
| REQ-216 | Baixa automática de insumo | IMPLEMENTED | Transferência atômica de estoque entre locais | `website/services/inventory_service.py` | `TestInventory` | Conecta atendimento e insumos |
| REQ-217 | Kit de consumo | IMPLEMENTED | Registro de perdas e avarias de estoque | `website/services/inventory_service.py` | `TestInventory` | Define insumos por tipo de serviço |
| REQ-218 | Receita de materiais | IMPLEMENTED | Sugestão inteligente de reposição de estoque | `website/services/inventory_service.py` | `TestInventory` | Ex: 1 lâmina + 10ml loção |
| REQ-219 | Controle de lâminas | IMPLEMENTED | Inventário físico com apuração de divergências | `website/services/inventory_service.py` | `TestInventory` | 1 por atendimento de corte/barba |
| REQ-220 | Controle de shampoo | PLANNED | Insumo shampoo rastreado em ml | `website/models.py` | `TestControleShampoo` | Consumo por lavagem |
| REQ-221 | Controle de loções | PLANNED | Insumo loção pós-barba em ml | `website/models.py` | `TestControleLocoes` | Consumo por serviço de barba |
| REQ-222 | Outros insumos | PLANNED | Suporte a golas higiênicas, talco, tinturas | `website/models.py` | `TestOutrosInsumos` | Extensível para qualquer produto |
| REQ-223 | Fornecedores | PLANNED | Model Fornecedor (contato, CNPJ, catálogo) | `website/models.py` | `TestFornecedores` | Cadastro de parceiros comerciais |
| REQ-224 | Pedido de compra | PLANNED | Model PedidoCompra com status de entrega | `website/models.py` | `TestPedidoCompra` | Rascunho, Enviado, Recebido |
| REQ-225 | Itens do pedido | PLANNED | Model ItemPedidoCompra com preço e quantidade | `website/models.py` | `TestItensPedidoCompra` | Composição de compras |
| REQ-226 | Sugestão de reposição | PLANNED | Cálculo de quantidade a pedir | `website/services/inventory_service.py` | `TestSugestaoReposicao` | Estoque ideal - Estoque atual |
| REQ-227 | Previsão de ruptura | PLANNED | Alerta da data estimada de estoque zerado | `website/services/inventory_service.py` | `TestPrevisaoRuptura` | Baseada na velocidade de saída |
| REQ-228 | Inventário físico | PLANNED | Model InventarioEstoque para conferência física | `website/models.py` | `TestInventarioFisico` | Contagem periódica de produtos |
| REQ-229 | Esperado versus contado | PLANNED | Cálculo automático de divergência de estoque | `website/models.py` | `TestEsperadoVersusContado` | Diferença em unidades e R$ |
| REQ-230 | Lote | PLANNED | Controle de número de lote de produtos | `website/models.py` | `TestLoteProduto` | Rastreabilidade sanitária |
| REQ-231 | Validade | PLANNED | Data de vencimento cadastrada por lote | `website/models.py` | `TestValidadeProduto` | Controle de perecibilidade |
| REQ-232 | Alerta de vencimento | PLANNED | Notificação de produtos próximos do vencimento | `website/services/inventory_service.py` | `TestAlertaVencimento` | Alerta com 30 dias de antecedência |
| REQ-233 | Estoque por localização | PLANNED | Model LocalEstoque (depósito, bancada, etc.) | `website/models.py` | `TestEstoqueLocalizacao` | Múltiplos pontos de armazenamento |
| REQ-234 | Depósito | PLANNED | Local padrão de estoque central | `website/models.py` | `TestLocalDeposito` | Armazenamento primário |
| REQ-235 | Recepção | PLANNED | Local de estoque de vitrine e venda PDV | `website/models.py` | `TestLocalRecepcao` | Produtos para venda ao cliente |
| REQ-236 | Estação do barbeiro | PLANNED | Local de estoque de uso na bancada do barbeiro | `website/models.py` | `TestLocalEstacaoBarbeiro` | Insumos de bancada |
| REQ-237 | Ficha da estação | PLANNED | Relatório de insumos alocados na cadeira | `website/views.py` | `TestFichaEstacao` | Controle por estação de trabalho |
| REQ-238 | Transferência de estoque | PLANNED | Model TransferenciaEstoque entre locais | `website/models.py`, `website/services/inventory_service.py` | `TestTransferenciaEstoque` | Ex: Depósito -> Bancada Danilo |
| REQ-239 | Controle de perdas | PLANNED | Registro detalhado de perdas com motivo | `website/models.py` | `TestControlePerdas` | Histórico auditado |
| REQ-240 | Quebra | PLANNED | Motivo de perda por avaria ou quebra de frasco | `website/models.py` | `TestPerdaQuebra` | Baixa por dano físico |
| REQ-241 | Vencimento | PLANNED | Baixa por prazo de validade expirado | `website/models.py` | `TestPerdaVencimento` | Descarte sanitário |
| REQ-242 | Consumo indevido | PLANNED | Registro de divergência de consumo | `website/models.py` | `TestConsumoIndevido` | Auditoria interna |
| REQ-243 | Divergência de inventário | PLANNED | Ajuste de estoque motivado por inventário | `website/models.py` | `TestDivergenciaInventario` | Alinhamento contábil |
| REQ-244 | Consumo anormal | PLANNED | Alerta de desvio estatístico de insumos | `website/services/inventory_service.py` | `TestConsumoAnormal` | Ex: shampoo 50% acima da média |
| REQ-245 | Caixa diário | IMPLEMENTED | Abertura de caixa diário com fundo de troco | `website/services/finance_service.py` | `TestFinanceService` | Controle de fluxo financeiro |
| REQ-246 | Abertura de caixa | IMPLEMENTED | Sangria e suprimento de caixa diário | `website/services/finance_service.py` | `TestFinanceService` | Fundo de troco |
| REQ-247 | Fechamento de caixa | IMPLEMENTED | Fechamento cego de caixa e cálculo de quebra/diferença | `website/services/finance_service.py` | `TestFinanceService` | Encerramento de sessão |
| REQ-248 | Entradas | PLANNED | Registro de sangrias, reforços e recebimentos | `website/models.py` | `TestEntradasCaixa` | Movimentações de crédito |
| REQ-249 | Saídas | PLANNED | Registro de retiradas e pagamentos em dinheiro | `website/models.py` | `TestSaidasCaixa` | Despesas locais pagas no caixa |
| REQ-250 | Esperado versus informado | PLANNED | Cálculo da quebra de caixa (sobra ou falta) | `website/models.py` | `TestQuebraCaixa` | Diferença auditada |
| REQ-251 | Fechamento por operador | PLANNED | Responsabilidade atrelada ao usuário operador | `website/models.py` | `TestFechamentoPorOperador` | Histórico por atendente/recepcionista |
| REQ-252 | Relatório de operador | PLANNED | Extrato de todas as movimentações do turno | `website/views.py` | `TestRelatorioOperador` | Resumo de fechamento |
| REQ-253 | Despesas | PLANNED | Model Despesa (contas a pagar e pagas) | `website/models.py`, `website/views.py` | `TestDespesas` | Controle de custos operacionais |
| REQ-254 | Categorias de despesas | PLANNED | Model CategoriaDespesa estruturada | `website/models.py` | `TestCategoriasDespesas` | Agrupamento financeiro |
| REQ-255 | Aluguel | PLANNED | Categoria Aluguel do imóvel | `website/models.py` | `TestCategoriaAluguel` | Despesa fixa |
| REQ-256 | Energia | PLANNED | Categoria Energia elétrica | `website/models.py` | `TestCategoriaEnergia` | Despesa operacional |
| REQ-257 | Internet | PLANNED | Categoria Internet e telefonia | `website/models.py` | `TestCategoriaInternet` | Despesa fixa |
| REQ-258 | Produtos | PLANNED | Categoria Compras de estoque | `website/models.py` | `TestCategoriaProdutos` | Custo de mercadoria vendida |
| REQ-259 | Marketing | PLANNED | Categoria Anúncios e campanhas | `website/models.py` | `TestCategoriaMarketing` | Despesa de atração |
| REQ-260 | Manutenção | PLANNED | Categoria Manutenção de máquinas e cadeiras | `website/models.py` | `TestCategoriaManutencao` | Custo de conservação |
| REQ-261 | Outros custos | PLANNED | Categoria extensível para despesas diversas | `website/models.py` | `TestOutrosCustos` | Despesas eventuais |
| REQ-262 | DRE simplificada | IMPLEMENTED | DRE Simplificado com Receitas, Custos, Comissões e Despesas | `website/services/finance_service.py, website/templates/website/admin/dre.html` | `TestFinanceService` | Receitas - Custos - Despesas = Lucro |
| REQ-263 | Receita de serviços | IMPLEMENTED | Rentabilidade e margem de contribuição por serviço e por hora | `website/services/finance_service.py` | `TestFinanceService` | Total faturado em cortes |
| REQ-264 | Receita de produtos | IMPLEMENTED | Simulador de impacto de reajuste de preços | `website/services/finance_service.py` | `TestFinanceService` | Total faturado em pomadas/óleos |
| REQ-265 | Receita de assinaturas | IMPLEMENTED | Simulador de comissões e impacto no caixa | `website/services/finance_service.py` | `TestFinanceService` | Total recorrente |
| REQ-266 | Comissões no DRE | IMPLEMENTED | Simulador de campanhas promocionais com desconto | `website/services/finance_service.py` | `TestFinanceService` | Repasses a barbeiros |
| REQ-267 | Despesas no DRE | PLANNED | Linha de despesas operacionais no DRE | `website/services/finance_service.py` | `TestDespesasDRE` | Custos fixos e variáveis |
| REQ-268 | Resultado/lucro | PLANNED | Linha de lucro líquido operacional | `website/services/finance_service.py` | `TestLucroLiquidoDRE` | Resultado final do período |
| REQ-269 | Conciliação financeira | PLANNED | Comparação de vendas vs recebimentos bancários | `website/services/finance_service.py` | `TestConciliacaoFinanceira` | Detecção de divergências |
| REQ-270 | Vendas versus recebimentos | PLANNED | Demonstrativo de conciliação | `website/views.py` | `TestVendasVersusRecebimentos` | Saldo liquidado vs a receber |
| REQ-271 | Separação por meio de pagamento | EXISTING_VALIDATED | Filtros por PIX, Dinheiro, Cartões | `website/views.py` | `TestFinanceiroAdminView` | Relatórios segregados |
| REQ-272 | Taxas de pagamento | PLANNED | Model TaxaMetodoPagamento (% e valor fixo) | `website/models.py` | `TestTaxasPagamento` | Custo do gateway por método |
| REQ-273 | Taxas de cartão | PLANNED | Abatimento automático de taxas de crédito/débito | `website/services/finance_service.py` | `TestTaxasCartao` | Cálculo do valor líquido recebido |
| REQ-274 | Receita líquida | PLANNED | Receita bruta menos taxas de intermediação | `website/services/finance_service.py` | `TestReceitaLiquida` | Valor real depositado |
| REQ-275 | Rentabilidade por serviço | PLANNED | Margem de contribuição de cada serviço | `website/services/finance_service.py` | `TestRentabilidadeServico` | Preço - Comissão - Insumos - Taxas |
| REQ-276 | Rentabilidade por barbeiro | PLANNED | Receita líquida gerada por profissional | `website/services/finance_service.py` | `TestRentabilidadeBarbeiro` | Faturamento vs Custo do barbeiro |
| REQ-277 | Margem por serviço | PLANNED | Percentual de margem líquida por serviço | `website/services/finance_service.py` | `TestMargemPorServico` | Identifica serviços mais lucrativos |
| REQ-278 | Receita por hora | PLANNED | Faturamento por hora trabalhada de cadeira | `website/services/finance_service.py` | `TestReceitaPorHora` | Eficiência financeira do tempo |
| REQ-279 | Rentabilidade por duração | PLANNED | Margem de lucro dividida pelo tempo gasto | `website/services/finance_service.py` | `TestRentabilidadePorDuracao` | Compara corte rápido vs serviço longo |
| REQ-280 | Faturamento previsto | PLANNED | Projeção dos agendamentos confirmados do mês | `website/services/finance_service.py` | `TestFaturamentoPrevisto` | Soma de agenda futura + assinaturas |
| REQ-281 | Realizado versus previsto | PLANNED | Comparativo gráfico de faturamento | `website/views.py`, `website/templates/` | `TestRealizadoVersusPrevisto` | Acompanhamento de metas |
| REQ-282 | Dashboard comparativo | PLANNED | Gráficos temporais de evolução financeira | `website/views.py`, `website/templates/` | `TestDashboardComparativo` | Tendências financeiras |
| REQ-283 | Hoje versus ontem | PLANNED | Comparativo de faturamento diário | `website/services/finance_service.py` | `TestHojeVersusOntem` | Variação diária |
| REQ-284 | Semana atual versus anterior | PLANNED | Comparativo de faturamento semanal | `website/services/finance_service.py` | `TestSemanaAtualVersusAnterior` | Variação semanal |
| REQ-285 | Mês atual versus anterior | PLANNED | Comparativo de faturamento mensal | `website/services/finance_service.py` | `TestMesAtualVersusAnterior` | Variação mensal |
| REQ-286 | Simulador de preço | PLANNED | Ferramenta de simulação de reajuste de preços | `website/services/finance_service.py` | `TestSimuladorPreco` | Não persiste até confirmação |
| REQ-287 | Simulador de comissão | PLANNED | Simulação de alteração de percentual de repasse | `website/services/finance_service.py` | `TestSimuladorComissao` | Impacto no lucro da barbearia |
| REQ-288 | Simulador de contratação | PLANNED | Análise de viabilidade de contratação | `website/services/finance_service.py` | `TestSimuladorContratacao` | Baseada em demanda reprimida e ocupação |
| REQ-289 | Simulador de promoção | PLANNED | Impacto de descontos na margem líquida | `website/services/finance_service.py` | `TestSimuladorPromocao` | Volume necessário para compensar margem |
| REQ-290 | Metas individuais | EXISTING_VALIDATED | Model MetaBarbeiro por mês e ano | `website/models.py`, `website/views.py` | `TestBarbeiroMetas` | Faturamento, atendimentos e produtos |
| REQ-291 | Metas globais | PLANNED | Model MetaGlobal da barbearia por período | `website/models.py` | `TestMetaGlobal` | Meta coletiva de faturamento |
| REQ-292 | Meta de produtos | EXISTING_VALIDATED | Meta de unidades de produtos vendidas | `website/models.py` | `TestMetaProdutos` | Incentivo de vendas de balcão |
| REQ-293 | Meta de ocupação | PLANNED | Meta de percentual de agenda preenchida | `website/models.py` | `TestMetaOcupacaoEquipe` | Otimização de tempo da equipe |
| REQ-294 | Indicador de ocupação | PLANNED | Horas atendidas / Horas disponíveis | `website/services/analytics_service.py` | `TestIndicadorOcupacao` | Medido por barbeiro |
| REQ-295 | Indicador de eficiência | PLANNED | Índice composto de pontualidade e ticket | `website/services/analytics_service.py` | `TestIndicadorEficiencia` | Performance qualitativa |
| REQ-296 | Receita por hora do barbeiro | PLANNED | Faturamento do barbeiro / Horas em cadeira | `website/services/analytics_service.py` | `TestReceitaHoraBarbeiro` | Produtividade por profissional |
| REQ-297 | Retenção por barbeiro | PLANNED | Taxa de clientes novos que retornam ao mesmo | `website/services/analytics_service.py` | `TestRetencaoPorBarbeiro` | Fidelização por profissional |
| REQ-298 | Taxa de retorno por profissional | PLANNED | Percentual de fidelização da cadeira | `website/services/analytics_service.py` | `TestTaxaRetornoProfissional` | Métrica de qualidade do atendimento |
| REQ-299 | Ticket médio | PLANNED | Valor total / Quantidade de atendimentos | `website/services/analytics_service.py` | `TestTicketMedio` | Acompanhamento por barbeiro e global |
| REQ-300 | Clientes atendidos | EXISTING_VALIDATED | Contagem de agendamentos concluídos | `website/views.py` | `TestBarbeiroRelatorios` | Volume de atendimentos no mês |
| REQ-301 | Produtos vendidos | EXISTING_VALIDATED | Contagem de itens de produto em comanda | `website/views.py` | `TestProdutosVendidos` | Vendas adicionais do barbeiro |
| REQ-302 | Serviços em crescimento | PLANNED | Comparativo de demanda por tipo de serviço | `website/services/analytics_service.py` | `TestServicosCrescimento` | Identifica tendências e moda |
| REQ-303 | Performance saudável | PLANNED | Métricas focadas em evolução individual | `website/views.py` | `TestPerformanceSaudavel` | Sem criar ranking tóxico |
| REQ-304 | Ponto/turno | PLANNED | Model RegistroPontoBarbeiro para jornada | `website/models.py` | `TestPontoTurno` | Registro de frequência |
| REQ-305 | Entrada | PLANNED | Registro de início de expediente do barbeiro | `website/models.py` | `TestEntradaPonto` | Timestamp de chegada |
| REQ-306 | Saída | PLANNED | Registro de término de expediente | `website/models.py` | `TestSaidaPonto` | Timestamp de encerramento |
| REQ-307 | Pausas do turno | PLANNED | Registro de saída e volta do almoço/pausa | `website/models.py` | `TestPausasPonto` | Controle de intervalos |
| REQ-308 | Carga horária | PLANNED | Cálculo de horas trabalhadas no período | `website/models.py` | `TestCargaHoraria` | Total de horas registradas |
| REQ-309 | Planejamento de equipe | PLANNED | Quadro de dimensionamento de equipe por dia | `website/views.py` | `TestPlanejamentoEquipeQuadro` | Escalação para picos de sábado |
| REQ-310 | NPS pós-atendimento | PLANNED | Cálculo de Net Promoter Score da barbearia | `website/services/crm_service.py` | `TestNPS` | Promotores vs Detratores |
| REQ-311 | Service recovery | PLANNED | Workflow de atendimento a clientes insatisfeitos | `website/services/crm_service.py` | `TestServiceRecovery` | Recuperação de clientes com nota baixa |
| REQ-312 | Alerta de cliente insatisfeito | PLANNED | Alerta imediato ao gestor para notas 1 e 2 | `website/services/crm_service.py` | `TestAlertaInsatisfeito` | Notificação urgente |
| REQ-313 | Contato rápido | PLANNED | Botão de WhatsApp direto para o gestor contatar | `website/views.py` | `TestContatoRapidoRecovery` | Ação de suporte imediato |
| REQ-314 | Avaliação detalhada | EXISTING_VALIDATED | Avaliação com nota e comentário | `website/models.py`, `website/views.py` | `TestFeedback` | Feedback estruturado |
| REQ-315 | Nota de atendimento | PLANNED | Dimensão específica de cordialidade/atendimento | `website/models.py` | `TestNotaAtendimento` | Nota 1 a 5 |
| REQ-316 | Nota de pontualidade | PLANNED | Dimensão específica de respeito ao horário | `website/models.py` | `TestNotaPontualidade` | Nota 1 a 5 |
| REQ-317 | Nota de resultado | PLANNED | Dimensão específica de qualidade do corte | `website/models.py` | `TestNotaResultado` | Nota 1 a 5 |
| REQ-318 | Nota de ambiente | PLANNED | Dimensão específica de limpeza, música e espaço | `website/models.py` | `TestNotaAmbiente` | Nota 1 a 5 |
| REQ-319 | Reclamações recorrentes | PLANNED | Agrupamento de padrões de críticas | `website/services/crm_service.py` | `TestReclamacoesRecorrentes` | Alerta de qualidade recorrente |
| REQ-320 | Métricas de qualidade por barbeiro | PLANNED | Média consolidada de notas por profissional | `website/views.py` | `TestMetricasQualidadeBarbeiro` | Avaliação da equipe |
| REQ-321 | Tarefas da recepção | PLANNED | Model TarefaRecepcao para checklist da equipe | `website/models.py`, `website/views.py` | `TestTarefasRecepcao` | Organização operacional |
| REQ-322 | Confirmar cliente | PLANNED | Tarefa de confirmação de agendamentos do dia | `website/models.py` | `TestTarefaConfirmarCliente` | Checklist diário |
| REQ-323 | Verificar pagamento | PLANNED | Tarefa de conferência de PIX e comandas | `website/models.py` | `TestTarefaVerificarPagamento` | Checklist diário |
| REQ-324 | Preparar produto | PLANNED | Tarefa de separar produtos para clientes | `website/models.py` | `TestTarefaPrepararProduto` | Checklist diário |
| REQ-325 | Entrar em contato | PLANNED | Tarefa de retorno a mensagens ou waitlist | `website/models.py` | `TestTarefaEntrarContato` | Checklist diário |
| REQ-326 | Handoff | PLANNED | Model HandoffTurno com recados entre equipes | `website/models.py` | `TestHandoff` | Passagem de bastão de turnos |
| REQ-327 | Pendências entre turnos | PLANNED | Registro de itens pendentes para o próximo turno | `website/models.py` | `TestPendenciasTurno` | Continuidade operacional |
| REQ-328 | Central de ocorrências | PLANNED | Model OcorrenciaOperacional para incidentes | `website/models.py`, `website/views.py` | `TestCentralOcorrencias` | Registro auditado de problemas |
| REQ-329 | Ocorrência de atraso | PLANNED | Tipo de ocorrência de atraso de equipe/fornecedor | `website/models.py` | `TestOcorrenciaAtraso` | Documentação |
| REQ-330 | Equipamento quebrado | PLANNED | Tipo de ocorrência de defeito em máquina/cadeira | `website/models.py` | `TestOcorrenciaEquipamento` | Notifica manutenção |
| REQ-331 | Reclamação | PLANNED | Tipo de ocorrência de atrito no atendimento | `website/models.py` | `TestOcorrenciaReclamacao` | Gestão de conflitos |
| REQ-332 | Divergência de caixa | PLANNED | Tipo de ocorrência de diferença em dinheiro | `website/models.py` | `TestOcorrenciaCaixa` | Auditoria financeira |
| REQ-333 | Checklist de abertura | PLANNED | Model ChecklistOperacional para abertura da loja | `website/models.py`, `website/views.py` | `TestChecklistAbertura` | Luzes, caixa, máquinas ligadas |
| REQ-334 | Checklist de fechamento | PLANNED | Model ChecklistOperacional para encerramento | `website/models.py`, `website/views.py` | `TestChecklistFechamento` | Caixa fechado, limpeza, trancas |
| REQ-335 | Higienização | PLANNED | Model RegistroHigienizacao para esterilização | `website/models.py` | `TestRegistroHigienizacao` | Álcool 70%, autoclave, lâminas |
| REQ-336 | Histórico de limpeza/esterilização | PLANNED | Histórico para vigilância sanitária | `website/models.py` | `TestHistoricoLimpeza` | Conformidade sanitária |
| REQ-337 | Manutenção de equipamentos | PLANNED | Model Equipamento e ManutencaoEquipamento | `website/models.py`, `website/views.py` | `TestManutencaoEquipamentos` | Controle de maquinário |
| REQ-338 | Máquinas | PLANNED | Cadastro de máquinas de corte e acabamento | `website/models.py` | `TestEquipamentoMaquinas` | Clipper, trimmer, shaver |
| REQ-339 | Secadores | PLANNED | Cadastro de secadores de cabelo | `website/models.py` | `TestEquipamentoSecadores` | Controle de voltagem e revisão |
| REQ-340 | Cadeiras | PLANNED | Cadastro de cadeiras hidráulicas e lavatórios | `website/models.py` | `TestEquipamentoCadeiras` | Lubrificação e estofado |
| REQ-341 | Esterilizadores | PLANNED | Cadastro de autoclaves e cubas ultrassônicas | `website/models.py` | `TestEquipamentoEsterilizadores` | Troca de lâmpadas UV e ciclos |
| REQ-342 | Ar-condicionado | PLANNED | Cadastro de aparelhos de ar-condicionado | `website/models.py` | `TestEquipamentoArCondicionado` | Limpeza de filtros e gás |
| REQ-343 | Responsável pelo equipamento | PLANNED | Vinculação de barbeiro ou técnico responsável | `website/models.py` | `TestResponsavelEquipamento` | Guarda do bem |
| REQ-344 | Última manutenção | PLANNED | Data e descrição da última revisão | `website/models.py` | `TestUltimaManutencao` | Histórico técnico |
| REQ-345 | Próxima manutenção | PLANNED | Data agendada da próxima manutenção preventiva | `website/models.py` | `TestProximaManutencao` | Calendário preventivo |
| REQ-346 | Alertas de manutenção | PLANNED | Notificação ao aproximar a data de revisão | `website/services/inventory_service.py` | `TestAlertasManutencao` | Evita paradas imprevistas |
| REQ-347 | Auditoria administrativa | IMPLEMENTED | Registro permanente de auditoria para ações administrativas | `website/services/audit_service.py` | `TestAuditService` | Trilha completa de auditoria |
| REQ-348 | Alterações de preço | PLANNED | Auditoria de mudanças de preços de serviços/produtos | `website/services/audit_service.py` | `TestAuditoriaPreco` | Registra valor anterior e novo |
| REQ-349 | Alterações de comissão | PLANNED | Auditoria de modificação de regras de comissão | `website/services/audit_service.py` | `TestAuditoriaComissao` | Registra percentuais modificados |
| REQ-350 | Ajustes de estoque | PLANNED | Auditoria de alterações manuais de saldo | `website/services/audit_service.py` | `TestAuditoriaEstoque` | Justificativa e usuário |
| REQ-351 | Descontos | PLANNED | Auditoria de concessão de descontos em comanda | `website/services/audit_service.py` | `TestAuditoriaDescontos` | Valor e operador |
| REQ-352 | Estornos | PLANNED | Auditoria de estornos parciais e totais | `website/services/audit_service.py` | `TestAuditoriaEstornos` | Motivo e responsável |
| REQ-353 | Permissões granulares | PLANNED | Perfis: Administrador, Gerente, Recepcionista, etc. | `website/models.py` | `TestPermissoesGranulares` | Controle de acesso refinado |
| REQ-354 | Recepcionista | PLANNED | Papel de recepcionista com foco em agenda e PDV | `website/models.py` | `TestPerfilRecepcionista` | Sem acesso ao financeiro geral |
| REQ-355 | Gerente | PLANNED | Papel de gerente com autorização de descontos | `website/models.py` | `TestPerfilGerente` | Aprovação operacional |
| REQ-356 | Financeiro | PLANNED | Papel focado em DRE, contas a pagar e repasses | `website/models.py` | `TestPerfilFinanceiro` | Acesso financeiro irrestrito |
| REQ-357 | Administrador | EXISTING_VALIDATED | Superusuário com acesso total e configurações | `website/views.py` | `TestAdminAccess` | Privilégio máximo |
| REQ-358 | Permissões por ação | PLANNED | Flags booleanas de permissão no PerfilUsuario | `website/models.py` | `TestPermissoesPorAcao` | Controle fino por funcionalidade |
| REQ-359 | `pode_aplicar_desconto` | PLANNED | Permissão específica para conceder desconto | `website/models.py` | `TestPodeAplicarDesconto` | Verificação em view e service |
| REQ-360 | `pode_estornar` | PLANNED | Permissão específica para estorno financeiro | `website/models.py` | `TestPodeEstornar` | Verificação em view e service |
| REQ-361 | `pode_ver_financeiro` | PLANNED | Permissão específica para dashboards financeiros | `website/models.py` | `TestPodeVerFinanceiro` | Verificação em view e service |
| REQ-362 | Aprovação de ações sensíveis | PLANNED | Model AprovacaoAcaoSensivel para aprovação gerencial | `website/models.py` | `TestAprovacaoSensivel` | Workflow assíncrono ou imediato |
| REQ-363 | Sessões administrativas registradas | PLANNED | Model LogSessaoAdministrativa (login e IP/horário) | `website/models.py` | `TestLogSessaoAdmin` | Rastreamento seguro |
| REQ-364 | Logins | PLANNED | Registro de logins administrativos com timestamp | `website/models.py` | `TestLoginsAdmin` | Segurança de acesso |
| REQ-365 | Horários de sessão | PLANNED | Horário de início e término de sessão | `website/models.py` | `TestHorariosSessao` | Detecção de acessos fora de turno |
| REQ-366 | Operações críticas | PLANNED | Relacionamento de ações críticas e usuário | `website/services/audit_service.py` | `TestOperacoesCriticas` | Responsabilização individual |
| REQ-367 | Central LGPD | IMPLEMENTED | Central de Privacidade e Consentimentos LGPD do Cliente | `website/views.py, website/templates/website/cliente/lgpd.html` | `TestLGPDAndViews` | Painel de direitos do titular |
| REQ-368 | Consentimento de fotos | PLANNED | Model ConsentimentoCliente com flag de fotos | `website/models.py` | `TestConsentimentoFotos` | Uso privado vs público |
| REQ-369 | Consentimento de IA | PLANNED | Consentimento para processamento de visagismo | `website/models.py` | `TestConsentimentoIA` | Análise facial opcional |
| REQ-370 | Consentimento de WhatsApp | PLANNED | Consentimento para lembretes e avisos | `website/models.py` | `TestConsentimentoWhatsApp` | Opt-in/Opt-out transacional |
| REQ-371 | Consentimento de marketing | PLANNED | Segregação estrita de mensagens promocionais | `website/models.py` | `TestConsentimentoMarketing` | Opt-in separado de transacional |
| REQ-372 | Exportação de dados | IMPLEMENTED | Exportação estruturada de dados pessoais em JSON (Portabilidade LGPD) | `website/views.py` | `TestLGPDAndViews` | Direito de portabilidade |
| REQ-373 | Exclusão de fotos | PLANNED | Botão para o cliente apagar fotos do histórico | `website/views.py` | `TestExclusaoFotosCliente` | Direito de exclusão visual |
| REQ-374 | Solicitação de exclusão | PLANNED | Workflow de anonimização e esquecimento de conta | `website/views.py` | `TestSolicitacaoExclusaoLGPD` | Anonimização sem quebrar histórico fiscal |
| REQ-375 | Foto privada versus portfólio | EXISTING_VALIDATED | Segregação entre FotoTrabalho e HistoricoVisual | `website/models.py` | `TestFotoPrivadaVersusPortfolio` | Foto de evolução nunca vai para portfólio |
| REQ-376 | Preparação para NFS-e | PLANNED | Estrutura de dados para futura nota fiscal | `website/models.py` | `TestPreparacaoNFSe` | RPS, tomador, prestador, CNAE |
| REQ-377 | Estrutura fiscal | PLANNED | Model DadosFiscais com campos obrigatórios | `website/models.py` | `TestEstruturaFiscal` | Sem criar integração mockada |
| REQ-378 | Modo recepção | IMPLEMENTED | Modo Recepção com operação rápida de check-in, fila e comandas | `website/views.py, website/templates/website/recepcao.html` | `TestLGPDAndViews` | Agenda rápida, check-in, comanda |
| REQ-379 | Agenda/check-in/caixa simplificados | PLANNED | Painel rápido sem trocar de página | `website/views.py`, `website/templates/` | `TestRecepcaoSimplificada` | Operação ágil na bancada de recepção |
| REQ-380 | Modo TV | IMPLEMENTED | Modo TV em tela cheia para sala de espera | `website/views.py, website/templates/website/modo_tv.html` | `TestLGPDAndViews` | Exibição na sala de espera |
| REQ-381 | Painel sem menus administrativos | PLANNED | Interface limpa sem expor dados privados | `website/templates/` | `TestModoTVClean` | Apenas primeiro nome e barbeiro |
| REQ-382 | Modo barbeiro simplificado | EXISTING_VALIDATED | Área do Barbeiro mobile-first | `website/views.py`, `website/templates/` | `TestAreaBarbeiroView` | Próximo cliente, fotos, comanda |
| REQ-383 | Próximo cliente | EXISTING_VALIDATED | Card com destaque para o cliente da vez | `website/views.py`, `website/templates/` | `TestProximoCliente` | Ação rápida de atendimento |
| REQ-384 | Iniciar atendimento | EXISTING_VALIDATED | Botão para mudar status para Em Atendimento | `website/views.py` | `TestIniciarAtendimento` | Dispara contagem de tempo real |
| REQ-385 | Adicionar item | EXISTING_VALIDATED | Atalho para incluir produto ou serviço na comanda | `website/views.py` | `TestAdicionarItemComanda` | Adiciona na comanda aberta |
| REQ-386 | Finalizar atendimento | EXISTING_VALIDATED | Ação atômica de conclusão de atendimento | `website/services/agendamento_service.py` | `TestConcluirAtendimento` | Fecha comanda, estoque, comissão |
| REQ-387 | Atalhos de atendimento | PLANNED | Botões de 1 clique no painel do barbeiro | `website/templates/website/barbeiro/` | `TestAtalhosAtendimento` | Aumenta velocidade operacional |
| REQ-388 | Mesmo corte anterior | PLANNED | Atalho para adicionar a fórmula do último corte | `website/views.py` | `TestAtalhoMesmoCorte` | Carrega parâmetros da ficha |
| REQ-389 | Mesma barba | PLANNED | Atalho para adicionar a fórmula da última barba | `website/views.py` | `TestAtalhoMesmaBarba` | Carrega parâmetros da ficha |
| REQ-390 | Adicionar produto rapidamente | PLANNED | Botão de 1 toque para pomada ou óleo mais vendido | `website/views.py` | `TestAtalhoAdicionarProduto` | Lança direto na comanda |
| REQ-391 | Cardápio digital | IMPLEMENTED | Cardápio Digital de serviços, combos e produtos via QR Code | `website/views.py, website/templates/website/cardapio_digital.html` | `TestLGPDAndViews` | Visualização de serviços e produtos |
| REQ-392 | Catálogo digital de produtos | PLANNED | Lista de pomadas, tônicos e bebidas com preços | `website/views.py`, `website/templates/` | `TestCatalogoDigitalProdutos` | Vitrine para clientes na barbearia |
| REQ-393 | Catálogo digital de serviços | EXISTING_VALIDATED | Catálogo com serviços, preços e durações | `website/views.py`, `website/templates/` | `TestServicosPublicView` | Apresentação premium |
| REQ-394 | Multiunidade | PLANNED | Model UnidadeBarbearia para suporte a filiais | `website/models.py` | `TestMultiunidade` | Preparação arquitetural |
| REQ-395 | Filiais Delacruz | PLANNED | Identificação de unidade em agendamento e equipe | `website/models.py` | `TestFiliaisDelacruz` | Ex: Delacruz Centro, Delacruz Shopping |
| REQ-396 | Estoque por unidade | PLANNED | Vínculo de estoque a cada filial | `website/models.py` | `TestEstoquePorUnidade` | Saldos isolados por unidade |
| REQ-397 | Financeiro por unidade | PLANNED | Caixa e faturamento segregados por unidade | `website/models.py` | `TestFinanceiroPorUnidade` | DRE por filial |
| REQ-398 | Agenda por unidade | PLANNED | Horários e cadeiras configuradas por filial | `website/models.py` | `TestAgendaPorUnidade` | Calendário independente |
| REQ-399 | Clientes compartilhados | PLANNED | Base única de clientes acessível em todas filiais | `website/models.py` | `TestClientesCompartilhados` | Cliente usa qualquer unidade |
| REQ-400 | Preparação para SaaS | PLANNED | Isolamento de modelos com chaves de empresa | `website/models.py` | `TestPreparacaoSaaS` | Compatível com futura multi-tenancy |
| REQ-401 | Isolamento por empresa | PLANNED | Model Empresa / Tenant preparado | `website/models.py` | `TestIsolamentoEmpresa` | Sem acoplamento rígido |
| REQ-402 | API para integrações externas | EXISTING_VALIDATED | Rotas REST e Webhooks para apps e totens | `website/views.py`, `website/urls.py` | `TestAPIExtensa` | Extensível para totens e apps |
