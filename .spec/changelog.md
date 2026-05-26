# Changelog — bot-finan

> Registro de decisões, mudanças e causa raiz de bugs.
> Formato: data, tipo, descrição.

## 25/05/2026 — Projeto iniciado
- Briefing realizado com Gabriel
- Spec gerado via vireum-spec distill

## 25/05/2026 — Refinamento do spec
- Requirements.md atualizado com formato de mensagem padrão, campos obrigatórios/opcionais e formato da resposta do bot
- Architecture.md corrigido: removido Prisma (Node.js) → SQLAlchemy 2.x async; removido BullMQ → sem fila no MVP
- T001 decomposta em 6 sub-tasks com critérios de aceitação detalhados
- Decisão: parser via regex (formato fixo, determinístico, sem custo de LLM)
- Decisão: sem fila de mensagens no MVP (volume ~100/mês não justifica)
- Decisão: hospedagem Railway free tier ($5 crédito/mês, sem cold start, PostgreSQL incluso)
- Decisão: orçamento configurável via WhatsApp (comando `orçamento: grupo - valor`)

## 25/05/2026 — Refinamento do formato e lógica de mês (pós-MVP)
- Formato de lançamento alterado: grupo e subgrupo agora são posicionais (posições 4 e 5), sem prefixos `grupo:` / `subgrupo:`
- Subgrupo passa a ser obrigatório — bot rejeita mensagem sem subgrupo
- Campo `pagamento do cartão` renomeado para `pagamento` no formato da mensagem
- Coluna `data_pagamento_cartao` renomeada para `data_pagamento` (migration 0002)
- `data_pagamento` agora é NOT NULL — default = `data_gasto` quando não informado
- Resumo mensal passa a filtrar por `data_pagamento` (antes filtrava por `data_gasto`)
- Decisão: casal controla gastos por mês de pagamento, não de compra

## 25/05/2026 — Bot em produção (Railway)
- Migrations passaram a rodar via `subprocess.run(["alembic", "upgrade", "head"])` no lifespan do FastAPI — `releaseCommand` do Railway free tier não disparava
- Dockerfile do baileys-service corrigido: adicionado `git`, `python3`, `make`, `g++` (Alpine não inclui; Baileys precisa compilar deps nativas)
- `WHATSAPP_GROUP_ID` configurado com ID real do grupo (`120363411203120829@g.us`) — filtro ativo em produção
- Bot validado ponta a ponta: lançamento recebido, salvo e resumo respondido via WhatsApp

## 25/05/2026 — BAILEYS-T001 concluída (substitui Evolution API)
- Criado serviço Node.js próprio com Baileys em `baileys-service/`
- Motivo: Evolution API v2.2.3 tem bug de loop infinito de reconexão, impedia geração do QR no Railway
- Serviço expõe: `GET /qrcode` (PNG), `POST /send`, `GET /health`
- `app/services/whatsapp.py` ajustado para chamar `BAILEYS_SERVICE_URL/send`
- `webhook.py` não alterado — payload encapsulado no formato `EvolutionWebhookPayload`
- Variáveis `EVOLUTION_API_URL`, `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCE` removidas → substituídas por `BAILEYS_SERVICE_URL`

## 25/05/2026 — DATA-T001 concluída — parser de data flexível
- `_parse_data_gasto` reescrito com regex `(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?`
- Aceita: `DD/MM/AA`, `DD/MM/AAAA`, `D/M/AA`, `D/M/AAAA`, `DD/MM`, `D/M`
- Sem ano → assume ano corrente; ano com 2 dígitos → 2000+AA; 4 dígitos → direto

## 25/05/2026 — Decisão estrutural: subgrupos como entidade própria
- Subgrupo promovido de texto livre (`lancamentos.subgrupo String`) para entidade com tabela própria
- Nova tabela `subgrupos (id, grupo_id FK, nome, orcamento_mensal)` com UNIQUE(grupo_id, nome)
- `lancamentos.subgrupo` (string) → `lancamentos.subgrupo_id` (FK para `subgrupos.id`)
- `grupos.orcamento_mensal` removido — orçamento do grupo passa a ser `SUM(subgrupos.orcamento_mensal)`
- Motivo: sem entidade própria, subgrupos não podem ter orçamento individual e o total do grupo fica inconsistente
- Task gerada: SUBGRUPO-T001 (bloqueante para ORCA-T001 e seed de dados)
- Comando de orçamento muda para: `orçamento: <grupo> - <subgrupo> - <valor>`

## 25/05/2026 — SUBGRUPO-T001 concluída — subgrupos com orçamento próprio
- Criado model `Subgrupo(id, grupo_id FK, nome, orcamento_mensal, UNIQUE(grupo_id, nome))`
- Migration 0003: cria tabela `subgrupos`, migra dados existentes, substitui `lancamentos.subgrupo` (string) por FK
- `grupos.orcamento_mensal` removido do model — agora é `SUM(subgrupos.orcamento_mensal)` via query
- Schema `OrcamentoDTO`: adicionado campo `subgrupo: str`
- Parser: `parse_orcamento` atualizado para regex 3 campos: `grupo - subgrupo - valor`
- Services: `salvar_lancamento` resolve/cria `Subgrupo` automaticamente; `definir_orcamento` salva em `Subgrupo.orcamento_mensal`
- Resumo: `calcular_resumo` usa `SUM(subgrupos.orcamento_mensal)` com join; `calcular_resumo_subgrupos` exibe orçamento por subgrupo
- Jobs: `job_resumo_diario` e `job_resumo_bidiario` atualizados para usar `Lancamento.subgrupo.nome` (relacionamento)
- Help: comando de orçamento atualizado no menu de ajuda para novo formato

## 25/05/2026 — INPUTAR-T001 concluída (MVP implementado)
- T001.1: setup base — FastAPI, Docker Compose, Alembic, railway.toml
- T001.2: models SQLAlchemy 2.x async — `Grupo` e `Lancamento` + migration inicial
- T001.3: parser regex — `parse_lancamento` e `parse_orcamento` (15/15 testes)
- T001.4: webhook receiver — `POST /webhook/whatsapp` com filtros e BackgroundTasks
- T001.5: serviço de persistência — deduplicação SHA-256 + proteção race condition
- T001.6: resumo + resposta — `calcular_resumo` + `enviar_mensagem` via Evolution API
- MVP completo: fluxo ponta a ponta funcional (webhook → parse → save → resumo → resposta)
