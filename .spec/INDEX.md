# INDEX — bot-finan

> Arquivo de entrada. Sempre carregado pela IA no início de cada sessão.
> Arquivos pesados são carregados por referência — apenas quando a tarefa exigir.

## Projeto
- **Cliente:** Gabriel
- **Responsável:** Gabriel
- **Data do briefing:** 25/05/2026
- **Fase atual:** MVP — concluído em 25/05/2026

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

## Arquivos de contexto disponíveis
Não carregue esses arquivos automaticamente.
Carregue apenas quando a tarefa exigir:

- Escopo e features → `.spec/requirements.md`
- Decisões técnicas → `.spec/architecture.md`
- Tarefas ativas → `.spec/tasks/active.md`
- Histórico de decisões → `.spec/changelog.md`
- Regras do projeto → `.spec/rules.md`

## Resumo do Sistema
Bot WhatsApp pessoal que recebe mensagens padronizadas de gastos, salva em PostgreSQL e responde com resumo do orçamento mensal por grupo. Integração via Evolution API (webhook + envio de mensagens).
