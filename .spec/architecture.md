# Architecture — bot-finan

> Atualizado em 25/05/2026
> A IA deve registrar aqui cada decisão técnica relevante

## Stack
- **Frontend:** Nenhum
- **Backend:** Python 3.12 + FastAPI
- **Banco de dados:** PostgreSQL (Railway free tier)
- **ORM:** SQLAlchemy 2.x (async) + Alembic (migrations)
- **WhatsApp:** Evolution API (webhook receiver + envio via httpx)
- **Containerização:** Docker + Docker Compose (dev local)
- **Hospedagem:** Railway (free tier — $5 crédito/mês)

## Infraestrutura
- **Dev local:** Docker Compose (api + postgres)
- **Produção:** Railway — serviço web (FastAPI) + PostgreSQL plugin
- **Deploy:** push para `main` → Railway faz build automático via `railway.toml`
- **CI/CD:** Não no MVP

## Variáveis de Ambiente

| Variável | Descrição |
|----------|-----------|
| `DATABASE_URL` | URL de conexão PostgreSQL (Railway injeta automaticamente) |
| `EVOLUTION_API_URL` | URL base da Evolution API (ex: `https://evo.seudominio.com`) |
| `EVOLUTION_API_KEY` | API key da Evolution API |
| `EVOLUTION_INSTANCE` | Nome da instância conectada ao celular |
| `WHATSAPP_GROUP_ID` | ID do grupo WhatsApp que o bot escuta |
| `BOT_PHONE_NUMBER` | Número do bot para ignorar próprias mensagens |

## MCPs Ativos
- context7
- github

## Decisões Arquiteturais

| Data | Decisão | Alternativas descartadas | Motivo |
|------|---------|--------------------------|--------|
| 25/05/2026 | ORM: SQLAlchemy 2.x async | Prisma (Node.js), Tortoise ORM | SQLAlchemy é o padrão Python, suporte async nativo no 2.x |
| 25/05/2026 | Sem fila de mensagens no MVP | Redis + Celery | Volume ~100 msgs/mês não justifica fila; FastAPI BackgroundTasks suficiente |
| 25/05/2026 | Parser via regex | LLM parser, NLP | Formato fixo e controlado pelo usuário; determinístico e sem custo |
| 25/05/2026 | Hospedagem: Railway free tier | Render+Neon, Fly.io | Railway inclui PostgreSQL no mesmo plano, sem cold start, $5 crédito/mês gratuito |
| 25/05/2026 | HTTP client: httpx | requests, aiohttp | Suporte async nativo, integra bem com FastAPI |
| 25/05/2026 | Orçamento configurável via WhatsApp | Só via banco/admin | Usuário pode definir/redefinir orçamento por grupo sem acessar infra |
| 25/05/2026 | Formato posicional: grupo e subgrupo na posição 4 e 5 | Prefixos `grupo:` / `subgrupo:` | Mais limpo para digitar; ambos obrigatórios — bot rejeita se faltar um |
| 25/05/2026 | Resumo filtra por `data_pagamento` (não por `data_gasto`) | Filtrar por data_gasto | Casal controla por quando o dinheiro sai; cartão de maio com fatura em junho entra no resumo de junho |
| 25/05/2026 | `data_pagamento` default = `data_gasto` quando não informado | NULL, valor obrigatório | Gastos à vista e PIX têm pagamento imediato; evita NULLs e simplifica queries |
