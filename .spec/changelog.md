# Changelog — bot-finan

> Registro de decisões, mudanças e causa raiz de bugs.
> Formato: data, tipo, descrição.

## 26/05/2026 — [H] Corrigido loop infinito de sincronização Baileys
**Problema:** Em produção, após escanear QR code, WhatsApp ficava com "sincronização em andamento" infinita.
**Causa raiz:** Em `baileys-service/index.js`, o handler `connection.update` chamava `startSocket()` imediatamente a cada evento `close` sem debounce. Em conexões instáveis (Railway free tier), múltiplos eventos `close` em rápida sucessão criavam múltiplas instâncias de socket concorrentes, acionando loops agressivos de reconexão.
**Solução implementada:**
- Flag `isReconnecting` previne múltiplos `startSocket()` simultâneos
- Backoff exponencial: 2s → 4s → 8s → ... → 60s (máximo)
- Contador `reconnectAttempts` reseta ao reconectar com sucesso
**Resultado:** Reconexões agora ocorrem com delays progressivos, eliminando loops de sincronização.

## 26/05/2026 — LEMBRETE-T001 implementado
- Sistema de lembretes para contas fixas mensais (aluguel, condomínio, academia) integrado
- `Lembrete` model criado: `(id, template_id FK, dia_vencimento INT 1-31, auto BOOL, criado_em)`
- Service `lembrete.py` com CRUD: `criar_lembrete`, `remover_lembrete`, `listar_lembretes`, `processar_lembretes_do_dia`
- Parser estendido: `parse_lembrete` detecta `lembrete: template - dia N [- auto]`, `parse_remove_lembrete`, `parse_lancar_template`
- Job `job_processar_lembretes` roda diário 08h BRT:
  - Lembretes manuais: aviso enviado 2 dias antes do vencimento
  - Lembretes automáticos: lançamento criado no próprio dia do vencimento
  - Deduplicação: delegada a `salvar_lancamento_de_template` (hash com data)
- Webhook: tipos `lembrete`, `remove_lembrete`, `list_lembretes`, `lancar_template` adicionados
- Mensagem: handlers para CRUD e lançamento manual integrados
- Ajuda atualizada com nova seção de lembretes e exemplos

## 26/05/2026 — MULTI-T001 implementado
- Novo formato de lançamento múltiplo: primeira linha = data, resto = lançamentos
- Parser: `parse_lancamento_multiplo()` detecta e extrai formato automicamente
- Webhook: `_detectar_tipo()` agora diferencia `lancamento_multiplo` de `lancamento` simples
- Mensagem: handler dedicado processa cada linha, coleta sucessos/erros, formata resposta consolidada
- Resposta consolida lançamentos + resumo por grupo com orçamento e alertas
- Suporta todos os campos opcionais: cartão, parcelas, alias, grupo/subgrupo explícito
- Deduplicação funciona por linha (hash no `texto_original` preservado)
- Compatibilidade total com formato simples mantida (sem regressão)

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

## 26/05/2026 — ALIAS-T001 implementado
- Task de sistema de aliases para categorização automática de lançamentos concluída
- `Alias` model criado: `(id, palavra_chave VARCHAR unique, subgrupo_id FK, created_at)`
- Service `alias.py` com CRUD: `criar_alias`, `remover_alias`, `listar_aliases`, `resolver_alias`
- Normalização case-insensitive + sem acentuação: `unicodedata.normalize('NFD', x).encode('ascii', 'ignore')`
- Parser estendido: `parse_alias` detecta `alias: palavra → Grupo > Subgrupo` (aceita `→` ou `->`)
- `parse_lancamento` modificado: aceita formato curto (3+ partes) com grupo/subgrupo opcionais
- Webhook: tipos `alias`, `remove_alias`, `list_aliases` adicionados
- Lancamento: `salvar_lancamento` resolve alias antes de rejeitar sem grupo/subgrupo
- Mensagem: handlers para 3 tipos de alias; seção em `formatar_ajuda()`
- Testes: 15 novos casos em `test_parser.py` cobrindo alias, remove_alias, lançamento curto
- Critérios de aceitação: 100% implementados

---

## 26/05/2026 — PARCELA-T001 implementado
- Tarefa de lançamento parcelado concluída
- `LancamentoDTO` estendido em schemas.py: adicionados campos `parcelas: int = 1` e `inicio_parcela: date | None = None`
- Parser estendido: `parse_lancamento()` detecta campos `parcelas: N` (valida 1 ≤ N ≤ 60) e `inicio: MM/AA` (obrigatório quando N > 1)
- Helpers implementados: `_parse_parcelas()` valida range e retorna None se inválido; `_parse_inicio_parcela()` valida mês 1-12, infere ano 20XX
- Novo detector de erro: `detectar_erro_parcelas()` identifica erros antes do parse falhar (parcelas 0/-N, > 60, sem inicio, mês inválido) com mensagens específicas
- Webhook estendido: `_detectar_tipo()` verifica "erro_parcelas" ANTES de "lancamento" para dar feedback imediato sobre erros de formato
- Handler em mensagem.py: tipo "erro_parcelas" dispara resposta de erro e retorna; tipo "lancamento" detecta se resultado é lista (parcelas) ou Lancamento (único)
- Serviço lancamento modificado: `salvar_lancamento()` retorna agora `Lancamento | list[Lancamento] | None`; detecta `parcelas > 1` e chama `_salvar_parcelas()`
- `_salvar_parcelas()` implementado: calcula `valor_parcela = valor_total / N` (quantize 2 casas); loop de N iterações com `descricao_parcela = f"{desc} ({i}/{N})"`
- `data_pagamento` incrementa 1 mês a cada iteração via `_proximo_mes()`; hash único por parcela via `_hash(f"{hash_base}_{i}")` para deduplicação
- Deduplicação funcional: verifica se cada parcela já existe no banco (rejeita toda a operação se encontrar duplicata)
- Resposta formatada: nova função `formatar_resumo_parcelas()` em resumo.py exibe "✅ N parcelas salvas!", produto (R$ total em Nx), período (primeira/última), gasto do mês
- Ajuda atualizada em resumo.py: nova seção "Lançamento parcelado" com formato, obrigatoriedade de `inicio:`, exemplo 12x
- Testes adicionados: 9 casos em test_parser.py cobrindo parcelas válidas, sem inicio obrigatório, inicio inválido, 0/-N/> 60, parcela 1 sem inicio, default 1
- Critérios de aceitação: 100% implementados
- Regressão testada: `parcelas: 1` (default) mantém comportamento de lançamento único sem alterações

## 26/05/2026 — PERIODO-T001 implementado
- Tarefa de resumo por período customizado concluída
- Padrão detectado: `resumo: DD/MM a DD/MM` (assume ano corrente)
- `ResumoPeriodoDTO` e `ResumoPeriodoGrupoDTO` adicionados em schemas.py
- Parser estendido: `parse_resumo_periodo()` detecta padrão via regex `_RESUMO_PERIODO_RE`, valida `data_inicio <= data_fim`
- Helper `_parse_data_periodo()` parseia formato DD/MM e assume ano corrente
- Serviço resumo expandido: `calcular_resumo_periodo()` implementado com query `BETWEEN data_pagamento`, agrupamento por grupo>subgrupo
- Formatação implementada: `formatar_resumo_periodo()` exibe breakdown por grupo com subgrupos indentados, total por grupo + total geral (SEM orçamento, SEM percentual)
- Webhook estendido: `_detectar_tipo()` detecta "resumo_periodo" ANTES de "resumo_comando" (prioritário) para não conflitar com `resumo: <grupo>`
- Handler em mensagem.py: valida intervalo, responde erro se invertido, exibe "📭 Nenhum lançamento..." se vazio
- Testes adicionados: 12 casos de teste em test_parser.py cobrindo formatos válidos, invertidos, inválidos, sem "a", datas inválidas, etc.
- Critérios de aceitação: 100% implementados
- Regressão testada: `resumo`, `resumo: <grupo>`, `resumo: MM/AA` continuam funcionando

---

## 25/05/2026 — TEMPLATE-T001 implementado
- Criada tabela `templates` com migration 0004: `(id, nome VARCHAR unique, descricao, valor, subgrupo_id FK, cartao nullable)`
- Model `Template` adicionado com relationship para `Subgrupo`
- Service `template.py` com funções: `criar_template`, `remover_template`, `listar_templates`, `resolver_template`
- Parser estendido: `parse_template` (detecta `template: nome - desc - valor - Grupo - Subgrupo [-cartao: ...]`) e `parse_remove_template` (detecta `remove template: nome`)
- Webhook detecta: comandos de template (`template:`, `remove template:`, `templates`) e nomes de template como possível lançamento (`possivel_template`)
- Service `lancamento.py` adicionado: `salvar_lancamento_de_template(nome) → Lancamento` que usa data de hoje + deduplicação por `hash(nome + data_hoje)`
- Mensagem.py implementado: handlers para todos os tipos de template, formatações de resposta (criado, removido, listado) e funções auxiliares `_fmt` e `_formatar_listar_templates`
- Menu `ajuda` estendido com seção de templates — formato, exemplos e modo de uso
- Critérios de aceitação: 100% implementados e testados
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

## 26/05/2026 — HISTORICO-T001 concluída — histórico mensal de gastos
- Novo schema `HistoricoMesDTO` com campos: `mes`, `ano`, `gasto`, `orcamento`, `percentual`, `em_andamento`
- Função `calcular_historico(grupo_id, subgrupo_id=None, n_meses=3, db)` em `resumo.py`:
  - Retorna últimos N meses (padrão 3) de um grupo ou subgrupo
  - Marca mês atual com `em_andamento=True`
  - Inclui meses sem lançamento como `gasto=0` (não omitidos)
  - Usa orçamento vigente (não histórico) para cálculo de percentual
- Função `formatar_historico(historico, grupo_nome, subgrupo_nome=None)` em `resumo.py`:
  - Cabeçalho: `📈 Histórico — Grupo [> Subgrupo]`
  - Linhas: `• mes/aa: R$ gasto [/ R$ orcamento (pct%) icone] [← em andamento]`
  - Ícones conforme percentual: ✅ (<80%), ⚠️ (80-99%), 🚨 (≥100%)
  - Omite coluna de orçamento se orcamento=0 (apenas ✅)
- Parser `parse_historico(texto)` em `parser.py`:
  - Detecta `historico: <Grupo>` (todo o grupo) e `historico: <Grupo> > <Subgrupo>` (subgrupo específico)
  - Retorna `HistoricoComandoDTO(grupo, subgrupo=None)`
- Webhook detecta tipo "historico" em `_detectar_tipo()`
- Handler em `mensagem.py`:
  - Busca grupo por nome; se subgrupo informado, busca também
  - Retorna erro se grupo/subgrupo não encontrado (case-sensitive)
  - Chamada a `calcular_historico` e `formatar_historico`
  - Envio da resposta via WhatsApp
- Critérios de aceitação: 100% implementados e testados

## 25/05/2026 — INPUTAR-T001 concluída (MVP implementado)
- T001.1: setup base — FastAPI, Docker Compose, Alembic, railway.toml
- T001.2: models SQLAlchemy 2.x async — `Grupo` e `Lancamento` + migration inicial
- T001.3: parser regex — `parse_lancamento` e `parse_orcamento` (15/15 testes)
- T001.4: webhook receiver — `POST /webhook/whatsapp` com filtros e BackgroundTasks
- T001.5: serviço de persistência — deduplicação SHA-256 + proteção race condition
- T001.6: resumo + resposta — `calcular_resumo` + `enviar_mensagem` via Evolution API
- MVP completo: fluxo ponta a ponta funcional (webhook → parse → save → resumo → resposta)

## 25/05/2026 — PROJ-T001 concluída — projeção de gasto no resumo mensal
- `ProjecaoDTO` adicionado em `schemas.py`: `ritmo_diario`, `projecao_fim_mes`, `orcamento_total`, `margem`, `alerta`
- `calcular_projecao(mes, ano, db)` implementado: calcula dias únicos com lançamentos, ritmo diário, projeção até fim do mês
  - Retorna `None` se `dias_passados = 0` (bloco omitido no dia 1 sem gastos)
  - Orçamento total = `SUM(subgrupos.orcamento_mensal)` em escopo global
  - Usa `calendar.monthrange()` para contar dias corretamente (28/29/30/31)
  - Alerta: `⚠️` quando projeção >= 90% orçamento, `🚨` quando >= 100%
- `formatar_projecao(projecao, mes, ano)` implementado: formatação com ritmo, projeção, orçamento, margem e alerta
- Integração em `processar_mensagem`: resumo on-demand agora anexa projeção ao final se houver
- Integração em `job_resumo_bidiario()`: job a cada 2 dias agora inclui projeção na resposta
- Critério de aceitação: bloco funciona corretamente com orçamento = 0 (omite margem)
