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

## 25/05/2026 — INPUTAR-T001 concluída (MVP implementado)
- T001.1: setup base — FastAPI, Docker Compose, Alembic, railway.toml
- T001.2: models SQLAlchemy 2.x async — `Grupo` e `Lancamento` + migration inicial
- T001.3: parser regex — `parse_lancamento` e `parse_orcamento` (15/15 testes)
- T001.4: webhook receiver — `POST /webhook/whatsapp` com filtros e BackgroundTasks
- T001.5: serviço de persistência — deduplicação SHA-256 + proteção race condition
- T001.6: resumo + resposta — `calcular_resumo` + `enviar_mensagem` via Evolution API
- MVP completo: fluxo ponta a ponta funcional (webhook → parse → save → resumo → resposta)
