# INDEX — bot-finan

> Arquivo de entrada. Sempre carregado pela IA no início de cada sessão.
> Arquivos pesados são carregados por referência — apenas quando a tarefa exigir.

## Projeto
- **Cliente:** Gabriel
- **Responsável:** Gabriel
- **Data do briefing:** 25/05/2026
- **Fase atual:** Pós-MVP — bot em produção no Railway

## Estado das Tasks

### Épico: Bot WhatsApp de Gestão Financeira Pessoal (MVP — concluído)

| Task | Descrição | Status |
|------|-----------|--------|
| INPUTAR-T001.1 | Setup do projeto: estrutura base + Docker + banco | [x] Concluída |
| INPUTAR-T001.2 | Schema do banco: tabelas `lancamentos` e `grupos` | [x] Concluída |
| INPUTAR-T001.3 | Parser de mensagens no formato padrão | [x] Concluída |
| INPUTAR-T001.4 | Webhook receiver da Evolution API | [x] Concluída |
| INPUTAR-T001.5 | Salvar lançamento com deduplicação | [x] Concluída |
| INPUTAR-T001.6 | Calcular resumo de gastos e responder via WhatsApp | [x] Concluída |

### Épico: Comandos Interativos (Fase 2 — Backlog)

| Task | Descrição | Status |
|------|-----------|--------|
| CMD-T001 | Menu de ajuda completo | [x] Concluída |
| CMD-T002 | Relatório de gastos por cartão (comando) | [x] Concluída |
| CMD-T003 | Resumo on-demand por grupo/mês | [x] Concluída |
| CMD-T004 | Listar lançamentos recentes | [x] Concluída |
| CMD-T005 | Cancelar/deletar lançamento por ID | [x] Concluída |

### Épico: Alertas no Resumo (Fase 2 — Concluído)

| Task | Descrição | Status |
|------|-----------|--------|
| ALERTA-T001 | Percentual + alertas na resposta de lançamento | [x] Concluída |

### Épico: Jobs Agendados (Fase 2 — Concluído)

| Task | Descrição | Status |
|------|-----------|--------|
| JOB-T001 | Job diário 06h — resumo do dia anterior | [x] Concluída |
| JOB-T002 | Job a cada 2 dias 08h — resumo por grupo/subgrupo | [x] Concluída |

### Épico: Infraestrutura WhatsApp (Concluído)

| Task | Descrição | Status |
|------|-----------|--------|
| BAILEYS-T001 | Serviço Baileys próprio — substitui Evolution API | [x] Concluída |

### Épico: Estrutura de Dados (Refactor Estrutural)

| Task | Descrição | Status |
|------|-----------|--------|
| SUBGRUPO-T001 | Subgrupos como entidade com orçamento próprio | [x] Concluída |

### Épico: Gestão de Orçamento

| Task | Descrição | Status |
|------|-----------|--------|
| ORCA-T001 | Orçamento mensal por mês/ano específico | [x] Concluída |

### Épico: Lançamentos Avançados

| Task | Descrição | Status |
|------|-----------|--------|
| PARCELA-T001 | Lançamento de compra parcelada | [x] Concluída |

### Épico: Inteligência do Parser (Backlog — depende de SUBGRUPO-T001)

| Task | Descrição | Status |
|------|-----------|--------|
| ALIAS-T001 | Aliases para categorização automática de lançamentos | [x] Concluída |
| TEMPLATE-T001 | Templates para lançamentos fixos recorrentes | [x] Concluída |
| MULTI-T001 | Lançamento múltiplo numa mensagem | [x] Concluída |

### Épico: Inteligência Analítica (Backlog)

| Task | Descrição | Status |
|------|-----------|--------|
| PROJ-T001 | Projeção de gasto e saldo no resumo mensal | [x] Concluída |
| COMPARE-T001 | Comparativo mensal automático no dia 1 | [x] Concluída |
| HISTORICO-T001 | Histórico mensal de grupo ou subgrupo | [x] Concluída |
| LEMBRETE-T001 | Lembretes de contas vinculados a templates | [x] Concluída |
| PERIODO-T001 | Resumo por período customizado | [x] Concluída |

## Arquivos de contexto disponíveis
Não carregue esses arquivos automaticamente.
Carregue apenas quando a tarefa exigir:

- Escopo e features → `.spec/requirements.md`
- Decisões técnicas → `.spec/architecture.md`
- Tarefas ativas → `.spec/tasks/active.md`
- Histórico de decisões → `.spec/changelog.md`
- Regras do projeto → `.spec/rules.md`

## Resumo do Sistema
Bot WhatsApp pessoal que recebe mensagens padronizadas de gastos, salva em PostgreSQL e responde com resumo do orçamento mensal por grupo. Integração via serviço Baileys próprio (`baileys-service/`) rodando no Railway. Bot em produção e funcional.
