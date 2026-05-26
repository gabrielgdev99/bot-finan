# Tasks — Done

> Tasks concluídas. Arquivo de referência — raramente entra no contexto ativo.

## 26/05/2026 — LEMBRETE-T001 implementado

**Concluído em:** 26/05/2026
**Épico:** Inteligência Analítica

### Implementação:
- Migration `0007_add_lembretes.py`: tabela `lembretes (id, template_id FK, dia_vencimento INT 1-31, auto BOOL, criado_em TIMESTAMP)`
- Model `Lembrete` em `app/models/lembrete.py` com relationship lazy-loaded para `Template`
- Service `lembrete.py` com 4 funções:
  - `criar_lembrete(template_nome, dia_vencimento, auto, db)` — valida template e dia, cria lembrete
  - `remover_lembrete(template_nome, db)` — remove por template, retorna o removido ou None
  - `listar_lembretes(db)` — retorna lista com template eager-loaded
  - `processar_lembretes_do_dia(db)` — detecta lembretes que vencem hoje ou em 2 dias, retorna tupla (aviso_list, auto_list)
- Parser estendido em `app/services/parser.py`:
  - `parse_lembrete()` — detecta `lembrete: <template> - dia <N> [- auto]` e retorna `LembreteDTO`
  - `parse_remove_lembrete()` — detecta `remove lembrete: <template>` e retorna `RemoveLembreteDTO`
  - `parse_lancar_template()` — detecta `lançar <template>` e retorna `LancarTemplateDTO`
  - 3 novos regex adicionados
- Schemas estendidos em `app/schemas.py`:
  - `LembreteDTO`, `RemoveLembreteDTO`, `LancarTemplateDTO`
- Webhook estendido em `app/routers/webhook.py`:
  - `_detectar_tipo()` detecta 4 novos tipos: `lembrete`, `remove_lembrete`, `list_lembretes`, `lancar_template`
  - Ordem: detectados ANTES de `lancamento_multiplo` para evitar conflitos
- Service `mensagem.py` estendido:
  - Handler `lembrete`: cria lembrete, responde erro se template não encontrado ou dia inválido
  - Handler `remove_lembrete`: remove lembrete, responde erro se não encontrado
  - Handler `list_lembretes`: lista todos cadastrados via `_formatar_listar_lembretes`
  - Handler `lancar_template`: lança manualmente usando `salvar_lancamento_de_template`, retorna resumo normal
  - Função `_formatar_listar_lembretes(lembretes)` — formata resposta com modo (manual/auto), dia, descrição, valor, grupo>subgrupo
- Service `jobs.py` estendido:
  - `job_processar_lembretes()` — roda diário 08h BRT
  - Avisos: para lembretes manuais que vencem em 2 dias, envia mensagem com formato de confirmação
  - Auto: para lembretes automáticos que vencem hoje, lança via `salvar_lancamento_de_template` + envia confirmação
  - Deduplicação: delegada à função `salvar_lancamento_de_template` (por hash com data)
- Main.py estendido:
  - Importa `job_processar_lembretes`
  - Agendamento: `CronTrigger(hour=8, minute=0, timezone=BRT)` — diário 08h BRT
- Ajuda atualizada em `app/services/resumo.py`:
  - Adicionada seção "Lembretes" com formatos, exemplos, modo de uso (criar, confirmar, listar, remover)
- Models/__init__.py atualizado: exporta `Lembrete`

### Critérios de aceitação — TODOS implementados:
- ✅ Tabela `lembretes (id, template_id FK, dia_vencimento INT 1-31, auto BOOL)` criada via migration
- ✅ `lembrete: aluguel - dia 5` cria lembrete manual vinculado ao template "aluguel"
- ✅ `lembrete: aluguel - dia 5 - auto` cria lembrete em modo automático
- ✅ `lembrete:` com template inexistente responde com erro
- ✅ Job diário envia aviso 2 dias antes do vencimento no modo manual
- ✅ `lançar aluguel` após o aviso cria o lançamento a partir do template com data de hoje
- ✅ Job diário lança automaticamente no dia do vencimento no modo auto e envia confirmação
- ✅ Deduplicação: lembrete auto não lança duas vezes no mesmo mês (mesmo dia) — garantida por hash em `salvar_lancamento_de_template`
- ✅ `lembretes` lista todos com modo (manual/auto), dia e dados do template
- ✅ `remove lembrete: aluguel` remove e confirma; inexistente responde com erro
- ✅ Comando `ajuda` inclui seção de lembretes com formato e exemplos

**Arquivos criados:** `alembic/versions/0007_add_lembretes.py`, `app/models/lembrete.py`, `app/services/lembrete.py`
**Arquivos modificados:** `app/models/__init__.py`, `app/schemas.py`, `app/services/parser.py`, `app/routers/webhook.py`, `app/services/mensagem.py`, `app/services/jobs.py`, `app/main.py`, `app/services/resumo.py`

## 26/05/2026 — MULTI-T001 implementado

**Concluído em:** 26/05/2026
**Épico:** Inteligência do Parser

### Implementação:
- Parser estendido:
  - `parse_lancamento_multiplo`: detecta formato múltiplo (primeira linha = data isolada, resto = linhas de lançamento) e retorna `(date, list[str])`
- Webhook modificado:
  - `_detectar_tipo` estendido: detecta `lancamento_multiplo` antes de `lancamento` simples
- Service `mensagem.py` estendido:
  - Handler para tipo `lancamento_multiplo`: itera sobre linhas, parseia cada uma com data do cabeçalho, processa sucessos/erros
  - Função auxiliar: `_formatar_resposta_multiplo` — formata resposta consolidada com lista de lançamentos e resumo por grupo
  - Tratamento de erros: linha sem alias + sem grupo/subgrupo indica qual linha falhou, continua processando
  - Deduplicação: por linha (hash preservado no `texto_original`)

### Critérios de aceitação — TODOS implementados:
- ✅ Mensagem com data isolada na primeira linha seguida de N linhas é detectada como formato múltiplo
- ✅ Cada linha é parseada independentemente com seus campos opcionais (cartão, parcelas, etc.)
- ✅ Linhas resolvem alias normalmente; linha sem alias e sem grupo/subgrupo retorna erro indicando a linha problemática, continua processando demais
- ✅ Linhas com `parcelas:` geram N lançamentos cada
- ✅ Deduplicação funciona por linha (reenvio da mensagem não duplica)
- ✅ Resposta consolida todos os lançamentos salvos e exibe resumo por grupo afetado
- ✅ Mensagem com apenas uma linha no formato múltiplo funciona normalmente (equivalente ao formato simples)
- ✅ Formato simples (`DD/MM/AA - desc - valor - ...`) continua funcionando sem regressão

**Exemplo do novo formato:**
```
25/05/26
padaria - 25
uber - 18 - cartao: nubank
tv samsung - 1200 - Casa - Eletrodoméstico - parcelas: 12 - inicio: 06/26
mercado - 95 - Alimentação - Mercado
```

**Resposta:**
```
✅ 4 lançamentos salvos!
• padaria — R$ 25,00 → Alimentação > Padaria
• uber — R$ 18,00 → Transporte > App
• tv samsung — R$ 1.200,00 em 12x → Casa > Eletrodoméstico
• mercado — R$ 95,00 → Alimentação > Mercado

📊 Alimentação: R$ 120,00 | Orçamento: R$ 800,00 | Restante: R$ 680,00 (15%)
📊 Transporte: R$ 18,00 | Orçamento: R$ 300,00 | Restante: R$ 282,00 (6%)
📊 Casa: R$ 100,00 gastos
```

**Arquivos modificados:** `app/services/parser.py`, `app/routers/webhook.py`, `app/services/mensagem.py`

## 26/05/2026 — ALIAS-T001 implementado

**Concluído em:** 26/05/2026
**Épico:** Inteligência do Parser

### Implementação:
- Migration `0006_add_aliases.py`: tabela `aliases (id, palavra_chave VARCHAR unique, subgrupo_id FK, created_at)`
- Model `Alias` em `app/models/alias.py` com relationship para `Subgrupo`
- Service `alias.py` com 4 funções:
  - `criar_alias`: cria novo alias, valida existência de grupo/subgrupo, retorna `None` se inválido
  - `remover_alias`: deleta alias por palavra-chave, retorna o removido ou `None`
  - `listar_aliases`: retorna lista ordenada de aliases
  - `resolver_alias`: busca alias por palavra-chave (case-insensitive, sem acentuação)
  - `_normalizar_palavra_chave`: helper para normalização (lowercase + remove diacríticos)
- Parser estendido:
  - `parse_alias`: regex que detecta `alias: palavra → Grupo > Subgrupo` (aceita `→` ou `->`) e retorna `AliasDTO`
  - `parse_remove_alias`: detecta `remove alias: palavra` e retorna `RemoveAliasDTO`
  - `parse_lancamento`: modificado para aceitar formato curto (3+ partes); grupo/subgrupo opcionais
- Schemas adicionados: `AliasDTO`, `RemoveAliasDTO`, `AliasInfoDTO`
- Webhook modificado:
  - `_detectar_tipo` estendido: detecta `alias:`, `remove alias:`, `aliases` como tipos específicos
- Service `lancamento.py` estendido:
  - `salvar_lancamento`: antes de rejeitar sem grupo/subgrupo, chama `resolver_alias(descricao)`
  - Se encontrado: usa grupo/subgrupo do alias; senão: retorna `None` (rejeita lançamento)
- Service `mensagem.py` completamente estendido:
  - Handler para tipo `alias`: cria alias, responde erro se grupo/subgrupo inválido
  - Handler para tipo `remove_alias`: remove e confirma, erro se não encontrado
  - Handler para tipo `list_aliases`: lista todos cadastrados
  - Função auxiliar: `_formatar_listar_aliases`
- Menu de ajuda estendido com seção de aliases — formato, exemplos, modo de uso (criar, usar, listar, remover)

### Critérios de aceitação — TODOS implementados:
- ✅ Tabela `aliases` criada via migration
- ✅ `alias: padaria → Alimentação > Padaria` cria alias e confirma
- ✅ `alias:` com grupo/subgrupo inexistente responde com erro
- ✅ Lançamento `25/05/26 - padaria - 25` resolve grupo+subgrupo pelo alias
- ✅ Lançamento sem alias e sem grupo/subgrupo responde com erro
- ✅ `aliases` lista todos cadastrados (resposta vazia se nenhum)
- ✅ `remove alias: padaria` remove e confirma; inexistente → erro
- ✅ Matching case-insensitive e sem acentuação (`Padaria` = `padaria` = `pádaria`)
- ✅ Comando `ajuda` inclui seção de aliases com exemplos
- ✅ `→` e `->` ambos aceitos no cadastro

**Arquivos criados:** `alembic/versions/0006_add_aliases.py`, `app/models/alias.py`, `app/services/alias.py`
**Arquivos modificados:** `app/models/__init__.py`, `app/schemas.py`, `app/services/parser.py`, `app/services/lancamento.py`, `app/routers/webhook.py`, `app/services/mensagem.py`, `app/services/resumo.py`, `tests/test_parser.py`

---

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

---

## [DATA-T001] Parser de data flexível no lançamento

**Concluído em:** 25/05/2026
**Épico:** Parser

### Implementação:
- `_parse_data_gasto()` refatorado em `app/services/parser.py` com regex unificado
- Suporta formatos: `DD/MM/AA`, `DD/MM/AAAA`, `D/M/AA`, `D/M/AAAA`, `DD/MM` (sem ano), `D/M` (sem ano)
- Ano completo (4 dígitos) preservado como-é; ano curto (2 dígitos) convertido: `2000 + AA`
- Sem ano: assume ano corrente via `datetime.now().year`
- Datas inválidas (`32/05/26`, `25/13/26`) retornam `None` (comportamento mantido)
- Todos os 8 formatos com testes unitários passando

### Critérios de aceitação — TODOS implementados:
- ✅ `25/05/26` → `2026-05-25`
- ✅ `25/05/2026` → `2026-05-25`
- ✅ `25/5/26` → `2026-05-25`
- ✅ `5/5/26` → `2026-05-05`
- ✅ `25/05` → data com ano corrente
- ✅ `25/5` → data com ano corrente
- ✅ Data inválida (`32/05/26`, `25/13/26`) retorna `None`
- ✅ Nenhuma regressão nos outros testes do parser

**Arquivos modificados:** `app/services/parser.py`

---

## [SUBGRUPO-T001] Subgrupos como entidade com orçamento próprio

**Concluído em:** 25/05/2026
**Épico:** Estrutura de dados

### Implementação:
- Migration `0003_add_subgrupos.py` criada:
  - Nova tabela `subgrupos (id, grupo_id FK, nome VARCHAR, orcamento_mensal DECIMAL default 0, UNIQUE(grupo_id, nome))`
  - Migração de dados: extrai subgrupos únicos de `lancamentos`, insere em tabela nova
  - `lancamentos.subgrupo` (string) → `lancamentos.subgrupo_id` (FK)
  - `grupos.orcamento_mensal` removida
- Model `Subgrupo` criado em `app/models/subgrupo.py` com relationship bidirecional com `Grupo`
- Model `Grupo` atualizado: remove `orcamento_mensal`, adiciona relationship para `Subgrupo`
- Parser estendido:
  - `parse_orcamento()` detecta novo formato: `orçamento: <Grupo> - <Subgrupo> - <valor>`
  - Retorna `OrcamentoDTO` com campos `grupo`, `subgrupo`, `valor`
  - Comando antigo sem subgrupo detecta tipo "comando_invalido" e responde com erro + novo formato
- Service `lancamento.py` atualizado:
  - `salvar_lancamento()` resolve subgrupo por nome+grupo
  - Se subgrupo não existir: cria automaticamente com `orcamento_mensal = 0`
  - Se grupo não existir: cria grupo E subgrupo automaticamente
  - `definir_orcamento()` salva em `subgrupos.orcamento_mensal` (não mais em `grupos`)
- Service `resumo.py` atualizado:
  - `calcular_resumo()` usa `SUM(subgrupos.orcamento_mensal)` como orçamento do grupo
  - Breakdown por subgrupo usa `subgrupos.orcamento_mensal` individual
  - Queries ajustadas com JOINs corretos
- Service `mensagem.py` atualizado: formatação de resposta de orçamento refatorada
- Service `jobs.py` atualizado: queries de resumo agendado ajustadas
- `requirements.md` atualizado: seção "Dados a Persistir" reflete nova estrutura

### Critérios de aceitação — TODOS implementados:
- ✅ Tabela `subgrupos` criada via migration
- ✅ `lancamentos.subgrupo` (string) → `lancamentos.subgrupo_id` (FK)
- ✅ Migration preserva dados existentes
- ✅ `grupos.orcamento_mensal` removida
- ✅ `orçamento: Alimentação - Mercado - 800` salva em `subgrupos.orcamento_mensal`
- ✅ Lançamento com subgrupo inexistente cria automaticamente com `orcamento_mensal = 0`
- ✅ Lançamento com grupo inexistente cria grupo E subgrupo automaticamente
- ✅ Resumo exibe orçamento do grupo como soma dos seus subgrupos
- ✅ `resumo: <grupo>` exibe breakdown por subgrupo com orçamento individual
- ✅ Comando antigo `orçamento: <grupo> - <valor>` responde com erro explicando novo formato

**Arquivos criados:** `alembic/versions/0003_add_subgrupos.py`, `app/models/subgrupo.py`
**Arquivos modificados:** `app/models/__init__.py`, `app/models/grupo.py`, `app/schemas.py`, `app/services/parser.py`, `app/services/lancamento.py`, `app/services/resumo.py`, `app/services/mensagem.py`, `app/services/jobs.py`, `app/requirements.md`

---

## [PERIODO-T001] Resumo por período customizado

**Concluído em:** 26/05/2026
**Épico:** Inteligência Analítica

### Implementação:
- `ResumoPeriodoDTO` e `ResumoPeriodoGrupoDTO` adicionados em `app/schemas.py`
- `_parse_data_periodo(texto)` implementado em `app/services/parser.py`:
  - Parseia formato DD/MM (sem ano)
  - Assume ano corrente via `date.today().year`
  - Retorna `None` para datas inválidas
- `parse_resumo_periodo(texto)` implementado em `app/services/parser.py`:
  - Detecta padrão `resumo: DD/MM a DD/MM` via regex `_RESUMO_PERIODO_RE`
  - Valida que `data_inicio <= data_fim` (rejeita períodos invertidos)
  - Retorna `ResumoPeriodoDTO(data_inicio, data_fim)` ou `None`
- `calcular_resumo_periodo(data_inicio, data_fim, db)` implementado em `app/services/resumo.py`:
  - Query: `SELECT grupo, subgrupo, SUM(valor) WHERE data_pagamento BETWEEN data_inicio AND data_fim`
  - Agrupa por grupo → subgrupo
  - Retorna `list[ResumoPeriodoGrupoDTO]` ou `None` se nenhum lançamento
- `formatar_resumo_periodo(grupos, data_inicio, data_fim)` implementado em `app/services/resumo.py`:
  - Cabeçalho: `📊 Resumo: DD/MM a DD/MM/AAAA`
  - Cada grupo com subgrupos indentados (└)
  - Total por grupo + total geral do período
  - **Sem orçamento, sem percentual** — apenas totais reais
- Parser estendido em `app/routers/webhook.py`:
  - `_detectar_tipo()` detecta tipo "resumo_periodo" (verificado ANTES de "resumo_comando" para não conflitar)
- Handler implementado em `app/services/mensagem.py`:
  - Valida intervalo: se `data_inicio > data_fim` → erro `❌ Período inválido: data inicial não pode ser posterior à final.`
  - Se nenhum lançamento: responde `📭 Nenhum lançamento no período informado.`
  - Caso contrário: chamada a `calcular_resumo_periodo` e `formatar_resumo_periodo`
- Testes unitários adicionados em `tests/test_parser.py` com 12 casos (formatos válidos, invertidos, inválidos, etc.)

### Critérios de aceitação — TODOS implementados:
- ✅ `resumo: 01/05 a 15/05` retorna lançamentos com `data_pagamento` entre 01/05 e 15/05 do ano corrente
- ✅ Exibe breakdown por grupo > subgrupo com total por grupo e total geral do período
- ✅ `data_inicio > data_fim` responde com erro de intervalo inválido
- ✅ Período sem lançamentos responde `📭 Nenhum lançamento no período informado.`
- ✅ Não exibe orçamento nem percentual (apenas totais reais)
- ✅ Formato existente `resumo`, `resumo: <grupo>` e `resumo: MM/AA` continuam funcionando sem regressão (detecção em ordem: período, depois comando)

**Arquivos modificados:** `app/schemas.py`, `app/services/parser.py`, `app/services/resumo.py`, `app/services/mensagem.py`, `app/routers/webhook.py`, `tests/test_parser.py`

---

## [PARCELA-T001] Lançamento de compra parcelada

**Concluído em:** 26/05/2026
**Épico:** Lançamentos Avançados

### Implementação:
- `LancamentoDTO` estendido em `app/schemas.py` com campos `parcelas: int = 1` e `inicio_parcela: date | None = None`
- `parse_lancamento(texto)` modificado em `app/services/parser.py`:
  - Detecta campo `parcelas: N` (valida 1 ≤ N ≤ 60)
  - Quando `parcelas > 1`: exige campo `inicio: MM/AA` (obrigatório)
  - `_parse_parcelas(texto)` retorna `None` se inválido
  - `_parse_inicio_parcela(texto)` valida mês 1-12, infere ano 20XX
  - Retorna `None` se parcelas > 1 mas `inicio` falta ou é inválido
- `detectar_erro_parcelas(texto)` implementado em `app/services/parser.py`:
  - Detecta erros antes do parse falhar: parcelas 0/negativo, > 60, sem `inicio`, mês inválido
  - Retorna mensagem de erro específica (ex: "❌ Campo 'parcelas' não pode ser > 60")
  - Integrado ao webhook via tipo "erro_parcelas"
- `salvar_lancamento(dto, db)` modificado em `app/services/lancamento.py`:
  - Retorna `Lancamento | list[Lancamento] | None`
  - Detecta `parcelas > 1` e chama `_salvar_parcelas()`
- `_salvar_parcelas()` implementado em `app/services/lancamento.py`:
  - Calcula `valor_parcela = valor_total / N` (quantize 2 casas)
  - Loop de N iterações (1 a N)
  - Cada parcela: `descricao_parcela = f"{descricao} ({i}/{N})"`
  - `data_pagamento` incrementa 1 mês a cada iteração (via `_proximo_mes()`)
  - Hash único: `_hash(f"{hash_base}_{i}")` para deduplicação por parcela
  - Deduplicação: verifica se hash de cada parcela já existe (rejeita se encontrar)
  - Retorna `list[Lancamento]` em sucesso ou `None` em falha
- `formatar_resumo_parcelas()` implementado em `app/services/resumo.py`:
  - Cabeçalho: `✅ {N} parcelas salvas!`
  - Linha de produto: `📦 descrição — R$ total em Nx de R$ por_parcela`
  - Linha de período: `📅 Primeira parcela: MM/AAAA | Última: MM/AAAA`
  - Linha de gasto: `📂 Grupo: R$ gasto_do_mes gastos em MM/AAAA`
  - Orçamento/alerta: idêntico a `formatar_resumo_lancamento` (reflete apenas parcela do mês)
- Handler em `app/services/mensagem.py`:
  - Valida tipo "erro_parcelas": envia mensagem de erro e retorna
  - Handler "lancamento": detecta se resultado é lista (parcelas) vs único lançamento
  - Chama `formatar_resumo_parcelas` para listas, `formatar_resumo_lancamento` para único
- Parser webhook (`app/routers/webhook.py`):
  - Adiciona `detectar_erro_parcelas()` check em `_detectar_tipo()` antes de `parse_lancamento`
  - Importa `detectar_erro_parcelas` do parser
  - Tipo "erro_parcelas" disparado se houver erro detectável
- Ajuda atualizada em `app/services/resumo.py`:
  - Nova seção "Lançamento parcelado" com formato, obrigatoriedade de `inicio:`, exemplo 12x
- Testes adicionados em `tests/test_parser.py`: 9 novos casos
  - Parcelas válidas (12, com inicio válido)
  - Sem inicio obrigatório (deve falhar)
  - Inicio inválido (mês 13)
  - Parcelas 0, negativo, > 60 (devem falhar)
  - Parcela 1 sem inicio (válido, default)
  - Sem campo parcelas (default 1, válido)

### Critérios de aceitação — TODOS implementados:
- ✅ `parcelas: 12` cria 12 registros com hash único
- ✅ Valor arredondado: `valor_total / N` (2 casas decimais)
- ✅ `data_pagamento` incrementa 1 mês cada parcela (a partir de `inicio:`)
- ✅ Descrição com sufixo `(X/N)` em cada parcela
- ✅ Deduplicação: reenvio não duplica (hash único por parcela)
- ✅ Sem `inicio:` com `parcelas > 1` → erro específico
- ✅ Mês inválido em `inicio:` → erro de formato
- ✅ `parcelas: 1` (default) sem regressão
- ✅ `parcelas: 0/-N` → erro
- ✅ `parcelas > 60` → erro
- ✅ Resposta exibe total, por_parcela, mês_inicial, mês_final
- ✅ Resumo mensal reflete apenas valor da parcela do mês

**Arquivos modificados:** `app/schemas.py`, `app/services/parser.py`, `app/services/lancamento.py`, `app/services/resumo.py`, `app/services/mensagem.py`, `app/routers/webhook.py`, `tests/test_parser.py`

---

## [ORCA-T001] Orçamento mensal por mês/ano específico

**Concluído em:** 26/05/2026
**Épico:** Gestão de Orçamento

### Implementação:
- Migration `0005_add_orcamentos_mensais.py` criada:
  - Nova tabela `orcamentos_mensais (id, grupo_id FK, mes DATE, valor DECIMAL, UNIQUE(grupo_id, mes))`
  - Armazena orçamento específico por grupo/mês
- Model `OrcamentoMensal` criado em `app/models/orcamento_mensal.py`:
  - Relationship bidirecional com `Grupo`
  - `mes` é DATE (sempre primeiro dia do mês)
- Model `Grupo` atualizado: adiciona relationship para `orcamentos_mensais`
- Parser estendido em `app/services/parser.py`:
  - `_ORCAMENTO_RE` refatorado para detectar formato: `orçamento: <grupo> - <subgrupo> - <valor> [- mes: MM/AA]`
  - `parse_orcamento()` retorna `OrcamentoDTO` com campo `mes: date | None`
  - Adicionada `_parse_mes_ano(texto)` — converte MM/AA para `date(ano, mes, 1)`
- Service `lancamento.py` atualizado:
  - `definir_orcamento()` verifica se `dto.mes` é informado
  - Se sim: cria/atualiza `OrcamentoMensal` para o mês específico
  - Se não: atualiza `subgrupo.orcamento_mensal` (comportamento anterior)
- Service `resumo.py` atualizado:
  - Adicionada `_obter_orcamento_grupo(grupo_id, mes, ano, db)` — helper que busca orçamento com fallback:
    1. Tenta buscar `OrcamentoMensal` para mês/ano específico
    2. Se não encontra → busca `SUM(subgrupos.orcamento_mensal)` genérico
  - `calcular_resumo()` usa helper para buscar orçamento correto
  - `calcular_resumo_todos()` usa helper para cada grupo
  - `calcular_resumo_subgrupos()` usa helper para o grupo
- Função `formatar_confirmacao_orcamento()` modificada em `app/services/resumo.py`:
  - Novo parâmetro `mes: date | None = None`
  - Se `mes` informado: resposta `✅ Orçamento de "grupo" para MM/AAAA definido: R$ valor`
  - Se sem `mes`: resposta `✅ Orçamento de "grupo" definido: R$ valor/mês` (anterior)
- Ajuda atualizada em `app/services/resumo.py`:
  - Adicionada seção "Orçamento para mês específico" com formato e exemplo
- Handler em `app/services/mensagem.py`:
  - Modificado para passar `dto.mes` à função `formatar_confirmacao_orcamento`

### Critérios de aceitação — TODOS implementados:
- ✅ Tabela `orcamentos_mensais` criada via migration
- ✅ `orçamento: Alimentação - Mercado - 500 - mes: 12/26` salva orçamento específico
- ✅ `orçamento: Alimentação - Mercado - 300` continua atualizando genérico
- ✅ Resumo busca específico primeiro, fallback para genérico
- ✅ Resposta distingue: "para 12/2026" (específico) vs "/mês" (genérico)
- ✅ Mês inválido (ex: `mes: 13/26`) retorna `None` no parser

**Arquivos criados:** `alembic/versions/0005_add_orcamentos_mensais.py`, `app/models/orcamento_mensal.py`
**Arquivos modificados:** `app/models/__init__.py`, `app/models/grupo.py`, `app/schemas.py`, `app/services/parser.py`, `app/services/lancamento.py`, `app/services/resumo.py`, `app/services/mensagem.py`
