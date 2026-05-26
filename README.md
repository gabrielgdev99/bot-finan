# 💰 bot-finan — Gestor de Finanças Pessoais via WhatsApp

Um bot de automação financeira que permite que casais gerenciem gastos compartilhados diretamente pelo WhatsApp, com categorização automática, orçamento por subgrupo e resumos periódicos.

**Status:** ✅ Produção | **Versão:** 1.0 | **Atualizado:** 26/05/2026

---

## 🎯 Features

- ✅ **Lançamento de gastos** — Parse inteligente de mensagens padronizadas
- ✅ **Categorização automática** — Sistema de aliases para grupos e subgrupos
- ✅ **Orçamento por subgrupo** — Controle granular de gastos por categoria
- ✅ **Alertas visuais** — ⚠️ em 80%, 🚨 em 100% do orçamento
- ✅ **Resumos on-demand** — Consulte gastos por período ou categoria
- ✅ **Histórico mensal** — Acompanhe tendências de gastos
- ✅ **Lançamentos parcelados** — Suporte a 1-60 parcelas com autoincrementação
- ✅ **Templates de lançamento** — Crie templates para gastos recorrentes
- ✅ **Lembretes automáticos** — Aviso antes de contas mensais fixas
- ✅ **Lançamento múltiplo** — Vários gastos em uma única mensagem
- ✅ **Relatório por cartão** — Filtre gastos pelo cartão utilizado
- ✅ **Jobs agendados** — Resumos automáticos diários e bidiários

---

## 💬 Como Usar

### 1. Lançar um Gasto

Envie uma mensagem no formato:
```
DD/MM/AA - descrição - valor - Grupo - Subgrupo [- cartao: nome] [- pagamento: DD/MM]
```

**Exemplos:**

```
25/05/26 - padaria - 25 - Alimentação - Padaria
26/05/26 - uber - 18,50 - Transporte - App - cartao: nubank
20/05/26 - mcdonald - 35 - Alimentação - Fast Food - pagamento: 10/06
```

**Resposta:**
```
✅ Lançamento #42 salvo!
📂 Alimentação: R$ 60,50 gastos este mês
📊 Orçamento: R$ 300,00 | Gasto: R$ 60,50 | Restante: R$ 239,50 (20%)
```

### 2. Definir Orçamento

```
orçamento: Alimentação - Padaria - 500
```

**Resposta:**
```
✅ Orçamento de "Alimentação > Padaria" definido: R$ 500,00/mês
```

### 3. Consultar Resumo

```
resumo                           # Todos os grupos (mês atual)
resumo: Alimentação             # Breakdown por subgrupo
resumo: 05/26                   # Mês específico
resumo: 20/05 a 30/05          # Período customizado
```

### 4. Histórico de Gastos

```
historico: Alimentação          # Últimos 3 meses de um grupo
historico: Alimentação > Padaria # Subgrupo específico
```

### 5. Templates (Gastos Recorrentes)

```
template: Aluguel - aluguel mensal - 1500 - Moradia - Aluguel - cartao: bradesco
lancar: Aluguel                 # Lança o template com data de hoje
remove template: Aluguel        # Remove o template
templates                       # Lista todos os templates
```

### 6. Lembretes (Contas Fixas)

```
lembrete: Aluguel - 5 - auto              # Auto-lança no dia 5
lembrete: Academia - 15                    # Aviso 2 dias antes
lembretes                                  # Lista todos
remove lembrete: Academia                  # Remove
```

### 7. Lançamento Múltiplo

```
26/05/26
padaria - 25 - Alimentação - Padaria
uber - 18 - Transporte - App
Netflix - 45 - Streaming - Entreterimento
```

### 8. Lançamento Parcelado

```
25/05/26 - sofá novo - 3000 - Móvel - Sala - parcelas: 12 - inicio: 06/26
```

Cria 12 parcelas de R$ 250 cada, começando em junho/2026.

### 9. Cancelar Lançamento

```
cancela: 42
```

**Resposta:**
```
✅ Lançamento #42 cancelado: padaria — R$ 25,00
📂 Alimentação: R$ 35,50 gastos este mês (novo saldo)
```

### 10. Relatório por Cartão

```
cartao: bradesco                # Gastos no Bradesco (mês atual)
cartao: nubank - mes: 04/26     # Gastos em abril
```

### 11. Listar Lançamentos Recentes

```
ultimos: 10                     # Últimos 10 lançamentos
```

### 12. Criar Alias (Categorização Automática)

```
alias: padaria → Alimentação > Padaria
```

Próximas mensagens com "padaria" são automaticamente categorizadas.

```
25/05/26 - padaria - 30 - Alimentação - Padaria
```

Vire apenas:
```
25/05/26 - padaria - 30
```

### 13. Menu de Ajuda

```
ajuda
```

Receba a lista completa de comandos e exemplos.

---

## 📋 Requisitos

**Backend:**
- Python 3.12+
- FastAPI
- SQLAlchemy 2.x (async)
- PostgreSQL
- APScheduler
- Baileys (Node.js, serviço próprio)

**Serviço WhatsApp:**
- Node.js 18+
- @whiskeysockets/baileys
- Express

---

## 🚀 Instalação Local

### 1. Clone o repositório

```bash
git clone https://github.com/gabrielgdev99/bot-finan.git
cd bot-finan
```

### 2. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite `.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/finanpessoal
BAILEYS_SERVICE_URL=http://localhost:3000
WHATSAPP_GROUP_ID=120363411203120829@g.us
BOT_PHONE_NUMBER=5511999999999
BOT_WEBHOOK_URL=http://localhost:8000/webhook/whatsapp
```

**Nota sobre `WHATSAPP_GROUP_ID`:**
- Se configurada: Baileys só envia webhook para mensagens desse grupo (economiza bandwidth)
- Se vazia: Baileys envia webhook para todas as mensagens (DMs, todos os grupos)

### 3. Inicie com Docker Compose

```bash
docker compose up -d
```

Isso inicia:
- **API FastAPI** em `http://localhost:8000`
- **PostgreSQL** em `localhost:5432`
- **Baileys Service** em `http://localhost:3000`

### 4. Acesse o QR Code

```
http://localhost:3000/qrcode
```

Aponte com seu WhatsApp para sincronizar.

### 5. Teste a API

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

---

## 🌐 Deploy em Produção (Railway)

### 1. Prepare o repositório

```bash
git remote add railway <seu-repo-railway>
```

### 2. Deploy automático

```bash
git push railway main
```

Railway detecta `railway.toml` e faz o build/deploy automaticamente.

### 3. Configure as variáveis de ambiente

No dashboard Railway, adicione:
```
DATABASE_URL=postgresql://... (Railway fornece automaticamente)
BAILEYS_SERVICE_URL=https://baileys-service-xxx.railway.app
WHATSAPP_GROUP_ID=120363411203120829@g.us
BOT_PHONE_NUMBER=5511999999999
```

### 4. Conecte o webhook

Na sua integração WhatsApp (Evolution API, WhatsApp Business, etc.), aponte para:
```
https://bot-finan-xxx.railway.app/webhook/whatsapp
```

---

## 🏗️ Arquitetura

```
bot-finan/
├── app/                          # Backend FastAPI
│   ├── main.py                   # Lifespan, routers, scheduler
│   ├── routers/webhook.py        # Webhook receiver
│   ├── models/                   # SQLAlchemy models
│   ├── schemas.py                # Pydantic DTOs
│   ├── services/                 # Lógica de negócio
│   │   ├── parser.py             # Parse de mensagens (regex)
│   │   ├── lancamento.py         # CRUD lançamentos
│   │   ├── resumo.py             # Cálculos e formatações
│   │   ├── mensagem.py           # Handlers de tipos
│   │   ├── whatsapp.py           # Cliente HTTP para Baileys
│   │   ├── alias.py              # Sistema de aliases
│   │   ├── template.py           # Templates de lançamento
│   │   └── lembrete.py           # Lembretes e auto-lançamento
│   └── core/
│       ├── config.py             # Settings (env vars)
│       └── database.py           # Sessão SQLAlchemy
├── baileys-service/              # Serviço Node.js (WhatsApp)
│   ├── index.js                  # Socket.io + Baileys
│   └── package.json
├── alembic/                      # Migrations SQLAlchemy
├── docker-compose.yml            # Dev local
├── Dockerfile                    # Container FastAPI
├── railway.toml                  # Config Railway
├── .spec/                        # Documentação Spec-Driven
└── README.md                     # Este arquivo
```

### Stack

| Componente | Tecnologia | Por quê |
|-----------|-----------|--------|
| **Frontend** | WhatsApp | Usuários finais usam algo que já têm |
| **Backend** | FastAPI + Python 3.12 | Async nativo, simples, rápido |
| **ORM** | SQLAlchemy 2.x async | Padrão Python, migrations com Alembic |
| **WhatsApp** | Baileys (Node.js) | Sem API oficial; Baileys é confiável |
| **Banco** | PostgreSQL | ACID, sem cold start no Railway |
| **Scheduler** | APScheduler | Integra nativamente com FastAPI |
| **Deploy** | Railway | Free tier inclui PostgreSQL, sem cold start |

### Otimizações para Free Tier

- **Filtro de grupo no Baileys:** Mensagens de outros grupos/DMs são descartadas no serviço Node.js (não geram requisição HTTP desnecessária)
- **Backoff exponencial:** Reconexões do Baileys com delays progressivos (economiza síncronizações em excesso)
- **BackgroundTasks:** Jobs assíncronos em background (não bloqueia requisições)
- **Parser determinístico:** Regex, não LLM (sem custos por token)

---

## 🔧 Decisões Técnicas

### Parser via Regex (não LLM)
- ✅ Determinístico (sem custo, sem alucinações)
- ✅ Formato controlado pelo usuário (não ambíguo)
- ✅ Feedback imediato sobre erros

### Sem fila de mensagens (BackgroundTasks)
- Volume estimado: ~100 gastos/mês
- Não justifica infraestrutura de fila (Redis + Celery)
- FastAPI BackgroundTasks é suficiente

### Subgrupo como entidade própria
- Permite orçamento independente por subgrupo
- Cálculo de orçamento do grupo = `SUM(subgrupos.orcamento_mensal)`
- Flexibilidade para expansões futuras

### `data_pagamento` vs `data_gasto`
- Casal controla gastos por mês de **pagamento**, não compra
- Cartão de maio com fatura em junho entra no resumo de junho
- Transações à vista (PIX, dinheiro) têm pagamento imediato

### Baileys em vez de Evolution API
- Evolution API v2.2.3 tem bug de loop infinito de reconexão
- Baileys direto elimina dependência externa instável
- Serviço próprio = total controle

---

## 📊 Monitoramento

### Logs

Todos os eventos são logados em stdout:
- Mensagens recebidas e processadas
- Erros de parse
- Operações de banco
- Tentativas de reconexão

Railway coleta logs automaticamente:
```bash
railway logs
```

### Health Check

```bash
curl https://bot-finan.railway.app/health
# {"status":"ok"}
```

---

## 🐛 Troubleshooting

### WhatsApp fica sincronizando infinitamente

**Causa:** Reconexão agressiva do Baileys em conexão instável.

**Solução:** Redeploy. Versão atual implementa backoff exponencial.

### Lançamento não é salvo (duplicata silenciosa)

**Esperado:** O bot verifica hash SHA-256 do texto original. Se já foi lançado, ignora silenciosamente (idempotente).

**Solução:** Envie a mensagem novamente com texto ligeiramente diferente ou consulte `ultimos: 5`.

### Erro "Grupo não encontrado" no resumo

**Causa:** Nome do grupo digitado diferente da primeira vez que foi criado (case-sensitive).

**Solução:** Verifique o nome exato com `resumo` (lista todos os grupos).

### Parser rejeitou meu lançamento

**Esperado:** Formato deve ser exatamente: `DD/MM/AA - desc - valor - Grupo - Subgrupo`

Envie `ajuda` para ver exemplos e todos os campos opcionais.

---

## 📝 Exemplos Reais

### Cenário 1: Casal usando para controlar gastos mensais

```
# Dia 1 — configuram orçamentos
orçamento: Alimentação - Mercado - 800
orçamento: Alimentação - Restaurante - 300
orçamento: Transporte - App - 200

# Dia 25 — casal lança gastos ao longo do mês
25/05/26 - mercado extra - 120 - Alimentação - Mercado
25/05/26 - restaurante japonês - 85 - Alimentação - Restaurante - pagamento: 10/06
26/05/26 - uber para o trabalho - 18,50 - Transporte - App

# Dia 26 — consultam resumo
resumo: Alimentação
# Bot responde com gasto vs orçamento por subgrupo + alertas
```

### Cenário 2: Casal com gastos parcelados (sofá)

```
# Sofá 3000 em 12 parcelas começando junho
20/05/26 - sofá novo - 3000 - Móvel - Sala - parcelas: 12 - inicio: 06/26

# Bot cria 12 lançamentos de R$ 250 (3000/12) com datas incrementadas
# 01/06/26 - sofá novo (1/12) - R$ 250
# 01/07/26 - sofá novo (2/12) - R$ 250
# ...
# 01/05/27 - sofá novo (12/12) - R$ 250
```

### Cenário 3: Gastos recorrentes (aluguel)

```
# Criar template
template: Aluguel - aluguel mensal - 1500 - Moradia - Aluguel - cartao: bradesco

# No dia do vencimento (com auto-lançamento)
# Bot lança automaticamente: 05/06/26 - aluguel mensal - 1500 - Moradia - Aluguel

# Ou lançar manualmente quando quiser
lancar: Aluguel
```

---

## 📈 Roadmap (Futuro)

- [ ] Dashboard web para visualização de dados
- [ ] App mobile nativa
- [ ] Integração com Open Banking (conectar contas)
- [ ] Análise de gastos com IA
- [ ] Compartilhamento de gastos com múltiplos usuários
- [ ] Exportar relatórios em PDF/Excel

---

## 📜 Licença

MIT License — Use livremente, com ou sem modificações.

---

## 👨‍💻 Créditos

- **Desenvolvido por:** Gabriel Gonçalves
- **Spec-Driven Development:** Vireum Desenvolvimento
- **Hospedagem:** Railway
- **WhatsApp:** Baileys (@whiskeysockets)

---

## 💬 Suporte

Encontrou um bug? Abra uma issue no GitHub:
```
https://github.com/gabrielgdev99/bot-finan/issues
```

Tem uma feature request? Deixe comentário em uma issue existente ou crie uma nova com a tag `[FEATURE]`.

---

**Última atualização:** 26 de maio de 2026 | **Status:** ✅ Produção
