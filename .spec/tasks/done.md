# Tasks — Done

> Tasks concluídas. Arquivo de referência — raramente entra no contexto ativo.

## 25/05/2026

- Projeto iniciado — spec gerado via vireum-spec distill

---

## [INPUTAR-T001] Inputar lançamentos financeiros via WhatsApp e enviar resumo de gastos

**Concluído em:** 25/05/2026
**Épico:** Bot de gestão financeira pessoal

### [INPUTAR-T001.1] Setup do projeto: estrutura base + Docker + banco
- Estrutura de pastas criada, docker-compose.yml, .env.example, requirements.txt, Alembic, GET /health, railway.toml

### [INPUTAR-T001.2] Schema do banco: tabelas `lancamentos` e `grupos`
- Models SQLAlchemy 2.x: `Grupo` e `Lancamento`
- Migration `0001_create_grupos_lancamentos.py` via Alembic

### [INPUTAR-T001.3] Parser de mensagens no formato padrão
- `parse_lancamento` e `parse_orcamento` implementados
- 15/15 testes unitários passando
- Infere ano do pagamento do cartão automaticamente

### [INPUTAR-T001.4] Webhook receiver da Evolution API
- `POST /webhook/whatsapp` com filtros de grupo, fromMe, e detecção de tipo
- Processamento via FastAPI BackgroundTasks (retorna 200 imediatamente)

### [INPUTAR-T001.5] Salvar lançamento com deduplicação
- `salvar_lancamento`: hash SHA-256 + proteção contra race condition via IntegrityError
- `definir_orcamento`: cria ou atualiza orçamento do grupo
- Grupo criado automaticamente se não existir

### [INPUTAR-T001.6] Calcular resumo de gastos e responder via WhatsApp
- `calcular_resumo`: soma lançamentos do mês por grupo
- `enviar_mensagem`: POST para Evolution API via httpx
- Formatação condicional: sem orçamento definido omite linha de restante
- Duplicata silenciosa; mensagem inválida recebe ajuda com formato

---

## 25/05/2026 — Fase 2: Comandos interativos, alertas e jobs agendados

### [ALERTA-T001] Percentual de orçamento na resposta de lançamento
- `formatar_resumo_lancamento` atualizado: exibe ID do lançamento, percentual de uso do orçamento
- Alertas automáticos: ⚠️ >= 80%, 🚨 >= 100%
- Propriedades `percentual` e `alerta` adicionadas ao `ResumoDTO`

### [CMD-T001] Menu de ajuda completo
- `parse_ajuda` detecta "ajuda", "help" ou "?"
- `formatar_ajuda` expandido com todos os 6 comandos disponíveis
- "ajuda" e "desconhecido" ambos disparam o menu

### [CMD-T002] Relatório de gastos por cartão
- `parse_relatorio_cartao`: detecta `cartao: nome` e `cartao: nome - mes: MM/AA`
- `calcular_relatorio_cartao`: query com `func.lower()` (case-insensitive), filtra por `data_pagamento`
- `formatar_relatorio_cartao`: total + breakdown por grupo

### [CMD-T003] Resumo on-demand
- `parse_resumo_comando`: detecta `resumo`, `resumo: Grupo`, `resumo: MM/AA`
- `calcular_resumo_todos`: todos os grupos do mês com orçamento e percentual
- `calcular_resumo_subgrupos`: breakdown por subgrupo de um grupo específico
- Alertas ⚠️/🚨 incluídos nos formatadores

### [CMD-T004] Listar lançamentos recentes
- `parse_ultimos`: detecta `ultimos: N`; N > 20 → mensagem de erro
- `listar_ultimos(n, db)`: JOIN com grupos, ORDER BY criado_em DESC, LIMIT n
- `formatar_ultimos`: exibe ID, data, descrição, valor, grupo/subgrupo, cartão

### [CMD-T005] Cancelar lançamento por ID
- `parse_cancela`: detecta `cancela: ID`
- `cancelar_lancamento(id, db)`: captura dados antes de deletar (evita expired instance), retorna `LancamentoInfo`
- `formatar_cancela_sucesso`: confirmação + novo resumo do grupo afetado
- `LancamentoInfo` adicionado ao `schemas.py` como snapshot pós-delete

### [JOB-T001] Job diário 06h — resumo do dia anterior
- `job_resumo_diario()` em `services/jobs.py`
- APScheduler `AsyncIOScheduler` com `CronTrigger(hour=6)`, timezone `America/Sao_Paulo`
- Envia "📭 Nenhum gasto registrado ontem." se sem gastos

### [JOB-T002] Job a cada 2 dias 08h — resumo por grupo/subgrupo
- `job_resumo_bidiario()` em `services/jobs.py`
- `IntervalTrigger(days=2)` com start_date 2026-05-26 08h00 BRT
- Agrega gastos do mês corrente em dois níveis: grupo → subgrupo

**Arquivos modificados:** `schemas.py`, `services/parser.py`, `services/resumo.py`, `services/lancamento.py`, `routers/webhook.py`, `services/mensagem.py`, `services/jobs.py` (novo), `main.py`, `requirements.txt`

---

## [BAILEYS-T001] Serviço Baileys customizado (substitui Evolution API)

**Concluído em:** 25/05/2026
**Épico:** Infraestrutura WhatsApp

- `baileys-service/index.js`: servidor Express + Baileys com `useMultiFileAuthState`, QR via `GET /qrcode` (PNG), repasse de mensagens ao webhook FastAPI no formato compatível com `EvolutionWebhookPayload`, envio via `POST /send`
- `baileys-service/package.json`: deps `@whiskeysockets/baileys`, `express`, `qrcode`, `pino`
- `baileys-service/Dockerfile`: Node 20 Alpine
- `app/core/config.py`: removidas `EVOLUTION_API_URL`, `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCE`; adicionada `BAILEYS_SERVICE_URL`
- `app/services/whatsapp.py`: ajustado para `POST BAILEYS_SERVICE_URL/send`
- `webhook.py` não alterado — formato do payload mantido compatível
