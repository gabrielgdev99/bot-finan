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

---

## [PROJ-T001] Projeção de gasto e saldo no resumo mensal

**Concluído em:** 25/05/2026
**Épico:** Inteligência Analítica

### Implementação:
- `ProjecaoDTO` adicionado em `app/schemas.py` com campos: `ritmo_diario`, `projecao_fim_mes`, `orcamento_total`, `margem`, `alerta`
- `calcular_projecao(mes, ano, db)` implementado em `app/services/resumo.py`:
  - Calcula dias únicos com lançamentos no mês
  - Se `dias_passados = 0`, retorna `None` (omite bloco)
  - Ritmo = `total_gasto / dias_passados`
  - Projeção = `ritmo * dias_no_mes` (usa `calendar.monthrange` para contar dias corretamente)
  - Orçamento total = `SUM(subgrupos.orcamento_mensal)` (global, não apenas do grupo)
  - Margem = `orcamento_total - projecao`
  - Alerta: `⚠️` quando projeção >= 90% orçamento, `🚨` quando >= 100%
- `formatar_projecao(projecao, mes, ano)` implementado em `app/services/resumo.py` com formatação de resposta
- Integração em `app/services/mensagem.py`: resumo on-demand agora chama `calcular_projecao` e anexa bloco ao final
- Integração em `app/services/jobs.py`: job bidiário agora inclui projeção na resposta

### Critérios de aceitação — TODOS implementados:
- ✅ Resumo on-demand (`resumo`) exibe bloco de projeção ao final
- ✅ Job de 2 em 2 dias exibe projeção no relatório enviado
- ✅ Ritmo calculado como `total_gasto / dias_passados` (dias com ≥1 lançamento contam)
- ✅ Projeção = `ritmo * dias_no_mes` (considera meses com 28/29/30/31 dias)
- ✅ Alerta `⚠️` quando projeção > 90% do orçamento total
- ✅ Alerta `🚨` quando projeção > 100% do orçamento total
- ✅ Bloco omitido quando `dias_passados = 0` (dia 1 sem lançamentos)
- ✅ Funciona corretamente em meses com orçamento total = 0 (omite comparação de margem)

**Arquivos modificados:** `app/schemas.py`, `app/services/resumo.py`, `app/services/mensagem.py`, `app/services/jobs.py`

---

## [TEMPLATE-T001] Templates para lançamentos fixos recorrentes

**Concluído em:** 25/05/2026
**Épico:** Inteligência do Parser

### Implementação:
- Migration `0004_add_templates.py`: tabela `templates (id, nome VARCHAR unique, descricao, valor, subgrupo_id FK, cartao nullable)`
- Model `Template` em `app/models/template.py` com relationship para `Subgrupo`
- Service `template.py` com 4 funções:
  - `criar_template`: cria novo template, valida existência de grupo/subgrupo, retorna `None` se inválido
  - `remover_template`: deleta template por nome, retorna o removido ou `None`
  - `listar_templates`: retorna lista ordenada de templates
  - `resolver_template`: busca template por nome (case-sensitive)
- Parser estendido:
  - `parse_template`: regex que detecta `template: nome - desc - valor - Grupo - Subgrupo [-cartao: ...]` e retorna `TemplateDTO`
  - `parse_remove_template`: detecta `remove template: nome` e retorna `RemoveTemplateDTO`
- Schemas adicionados: `TemplateDTO`, `RemoveTemplateDTO`
- Webhook modificado:
  - `_detectar_tipo` estendido: detecta `template:`, `remove template:`, `templates` como tipos específicos
  - Tipo `possivel_template` para resolver nomes de template como possível lançamento
- Service `lancamento.py` estendido:
  - `salvar_lancamento_de_template(nome)`: cria lançamento com data de hoje + dados do template
  - Deduplicação por `hash(nome + data_hoje)` — permite usar o mesmo template múltiplas vezes em dias diferentes, mas não no mesmo dia
- Service `mensagem.py` completamente refatorado:
  - Handler para tipo `template`: cria template, responde erro se grupo/subgrupo inválido
  - Handler para tipo `remove_template`: remove e confirma, erro se não encontrado
  - Handler para tipo `templates`: lista todos cadastrados
  - Handler para tipo `possivel_template`: tenta resolver como template → salva lançamento com resumo, senão mostra ajuda
  - Funções auxiliares: `_fmt` (formatação monetária), `_formatar_template_criado`, `_formatar_listar_templates`
- Menu de ajuda estendido com seção de templates — formato, modo de uso (criar, usar, listar, remover) e exemplos

### Critérios de aceitação — TODOS implementados:
- ✅ Tabela `templates` criada via migration
- ✅ `template: aluguel - aluguel ap - 1500 - Moradia - Aluguel` cria template e confirma
- ✅ `template:` com grupo/subgrupo inexistente responde com erro
- ✅ Digitar `aluguel` cria lançamento com data de hoje usando dados do template
- ✅ Template inexistente como comando cai em `possivel_template` → mostra ajuda (não erro)
- ✅ `templates` lista todos com nome, descrição, valor, grupo>subgrupo, cartão se houver
- ✅ `remove template: aluguel` remove e confirma; inexistente responde com erro
- ✅ Deduplicação: mesmo template 2x no mesmo dia não duplica (1 salvo, 1 silencioso)
- ✅ Comando `ajuda` inclui seção de templates com formato e exemplos

**Arquivos criados:** `alembic/versions/0004_add_templates.py`, `app/models/template.py`, `app/services/template.py`
**Arquivos modificados:** `app/models/__init__.py`, `app/routers/webhook.py`, `app/services/lancamento.py`, `app/services/parser.py`, `app/services/mensagem.py`, `app/services/resumo.py`, `app/schemas.py`

---

## [COMPARE-T001] Comparativo mensal automático no dia 1

**Concluído em:** 25/05/2026
**Épico:** Inteligência Analítica

### Implementação:
- `ComparativoDTO` e `ComparativoGrupoDTO` adicionados em `app/schemas.py`
- `calcular_comparativo(mes_atual, ano_atual, db)` implementado em `app/services/resumo.py`:
  - Compara mês M-1 vs mês M-2 (ex: 1º de junho compara maio vs abril)
  - Calcula gasto, orçamento e delta (absoluto + percentual) por grupo
  - Omite grupos sem gasto em nenhum dos dois meses
  - Marca grupos com novo gasto (sem referência anterior) como "novo neste mês"
  - Calcula também totais consolidados (gasto, orçamento, delta)
- `formatar_comparativo(comparativo)` implementado em `app/services/resumo.py`:
  - Exibe: gasto real, orçamento e percentual de cada grupo
  - Ícones: `⬆️` (aumento), `⬇️` (redução), `➡️` (variação < 5%)
  - Alerta: `🚨` para grupos com estourado de orçamento, `✅` para ok
  - Total consolidado ao final com delta geral
- `job_comparativo_mensal()` implementado em `app/services/jobs.py`
  - Agendado para executar todo dia 1 às 08h00 BRT via `CronTrigger(day=1, hour=8, minute=0)`
  - Envia comparativo do mês que fechou vs anterior via WhatsApp
  - Silencioso se nenhum gasto registrado em nenhum mês
- Job registrado no scheduler em `app/main.py`

### Critérios de aceitação — TODOS implementados:
- ✅ Job executa todo dia 1 às 08h00 BRT
- ✅ Compara mês `M-1` vs mês `M-2` (ex: no dia 1/06 compara mai vs abr)
- ✅ Exibe gasto real, orçamento e percentual de cada grupo
- ✅ Exibe delta absoluto e percentual vs mês anterior por grupo
- ✅ Ícone `⬆️` quando aumento, `⬇️` quando redução, `➡️` quando variação < 5%
- ✅ Alerta `🚨` em grupos que estouraram orçamento no mês fechado
- ✅ Grupos sem lançamento em nenhum dos dois meses são omitidos
- ✅ Grupo sem lançamento no mês anterior mas com gasto no mês fechado aparece como "novo" sem delta
- ✅ Total consolidado ao final com delta geral

**Arquivos modificados:** `app/schemas.py`, `app/services/resumo.py`, `app/services/jobs.py`, `app/main.py`

---

## [HISTORICO-T001] Histórico mensal de grupo ou subgrupo

**Concluído em:** 26/05/2026
**Épico:** Inteligência Analítica

### Implementação:
- `HistoricoMesDTO` adicionado em `app/schemas.py` com campos: `mes`, `ano`, `gasto`, `orcamento`, `percentual`, `em_andamento`
- `calcular_historico(grupo_id, subgrupo_id=None, n_meses=3, db)` implementado em `app/services/resumo.py`:
  - Calcula histórico de gastos dos últimos N meses (padrão 3)
  - Se `subgrupo_id` informado: retorna apenas daquele subgrupo
  - Se `subgrupo_id=None`: retorna soma de todos os subgrupos do grupo
  - Marca mês atual com `em_andamento=True`
  - Inclui meses sem lançamento como gasto=0 (não omitidos)
  - Usa orçamento vigente (não histórico) para todos os meses
  - Calcula percentual = `gasto / orcamento * 100`
- `formatar_historico(historico, grupo_nome, subgrupo_nome=None)` implementado em `app/services/resumo.py`:
  - Cabeçalho: `📈 Histórico — Grupo [> Subgrupo]`
  - Cada linha: `• mes/aa: R$ gasto [/ R$ orcamento (pct%) icone] [← em andamento]`
  - Ícones: `✅` (< 80%), `⚠️` (80-99%), `🚨` (>= 100%)
  - Omite orçamento se orcamento = 0 (exibe apenas ✅)
- `parse_historico(texto)` implementado em `app/services/parser.py`:
  - Detecta `historico: <Grupo>` e `historico: <Grupo> > <Subgrupo>`
  - Retorna `HistoricoComandoDTO` com campos `grupo` e `subgrupo` (opcional)
- Webhook estendido em `app/routers/webhook.py`:
  - `_detectar_tipo()` detecta tipo "historico"
  - Tipo "historico" roteado para handler em `mensagem.py`
- Handler implementado em `app/services/mensagem.py`:
  - Busca grupo por nome (case-sensitive)
  - Se subgrupo informado, busca e valida
  - Retorna erro se grupo/subgrupo não encontrado
  - Chamada a `calcular_historico` e `formatar_historico`
  - Envio da resposta via WhatsApp

### Critérios de aceitação — TODOS implementados:
- ✅ `historico: Alimentação > Mercado` retorna os últimos 3 meses do subgrupo
- ✅ `historico: Alimentação` retorna os últimos 3 meses do grupo (soma dos subgrupos)
- ✅ Mês atual aparece com `← em andamento`
- ✅ Meses sem lançamento aparecem como `R$ 0,00` (não são omitidos)
- ✅ Grupo ou subgrupo inexistente responde com erro indicando o nome inválido
- ✅ Ícones ⚠️/🚨 aplicados conforme percentual (>= 80% e >= 100%)
- ✅ Funciona corretamente para grupos/subgrupos com orçamento = 0 (omite coluna de orçamento)

**Arquivos modificados:** `app/schemas.py`, `app/services/resumo.py`, `app/services/parser.py`, `app/routers/webhook.py`, `app/services/mensagem.py`
