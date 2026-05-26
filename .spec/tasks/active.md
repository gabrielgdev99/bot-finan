# Tasks — Active

> Tarefas do MVP prontas para desenvolvimento.
> A IA só implementa tasks desta lista.
> Ao concluir uma task: marcar status, mover para done.md, atualizar INDEX.md

---

---

## DATA-T001 — Parser de data flexível no lançamento

**Épico:** Parser
**Prioridade:** Alta
**Complexidade:** Baixa
**Status:** [x] Concluída — 25/05/2026

### Contexto
O parser atual aceita apenas `DD/MM/AA` (dois dígitos para dia, mês e ano). Qualquer variação rejeitada silenciosamente retorna erro de formato. O usuário quer digitar de forma natural sem decorar o formato exato.

### Descrição
Estender `_parse_data_gasto` em `parser.py` para aceitar as variações:

| Formato | Exemplo | Comportamento |
|---------|---------|---------------|
| `DD/MM/AA` | `25/05/26` | atual — ano = 2000 + AA |
| `DD/MM/AAAA` | `25/05/2026` | ano completo |
| `D/M/AA` | `5/5/26` | dia/mês com 1 dígito |
| `D/M/AAAA` | `5/5/2026` | dia/mês com 1 dígito + ano completo |
| `DD/MM` | `25/05` | sem ano → assume ano corrente |
| `D/M` | `25/5` | mês com 1 dígito, sem ano → assume ano corrente |

Regex unificado que cobre todos os casos de uma vez.

### Arquivos a modificar
- `app/services/parser.py` — reescrever `_parse_data_gasto` com regex flexível

### Critérios de aceitação
- [ ] `25/05/26` → `2026-05-25` ✅
- [ ] `25/05/2026` → `2026-05-25` ✅
- [ ] `25/5/26` → `2026-05-25` ✅
- [ ] `5/5/26` → `2026-05-05` ✅
- [ ] `25/05` → data com ano corrente ✅
- [ ] `25/5` → data com ano corrente ✅
- [ ] Data inválida (`32/05/26`, `25/13/26`) retorna `None` (comportamento atual mantido)
- [ ] Demais formatos inválidos continuam retornando `None`
- [ ] Nenhuma regressão nos outros testes do parser

---

## SUBGRUPO-T001 — Subgrupos como entidade com orçamento próprio

**Épico:** Estrutura de dados
**Prioridade:** Alta (bloqueante para ORCA-T001 e seed de dados)
**Complexidade:** Média
**Status:** [x] Concluída — 25/05/2026

### Contexto
Hoje `subgrupo` é texto livre em `lancamentos.subgrupo (String)` e os grupos têm `orcamento_mensal` próprio. Isso impede controle de orçamento por subgrupo e faz o "total do grupo" ser independente dos subgrupos — sem consistência. A solução é promover subgrupo a entidade própria e fazer o orçamento do grupo ser a soma dos seus subgrupos.

### Descrição
Criar tabela `subgrupos`, migrar a coluna `lancamentos.subgrupo` de string para FK, e recalcular orçamento do grupo como soma dos subgrupos. O comando de orçamento passa a receber grupo + subgrupo.

**Novo formato do comando de orçamento:**
```
orçamento: <grupo> - <subgrupo> - <valor>
```
**Exemplo:**
```
orçamento: Alimentação - Mercado - 800
```
**Resposta:**
```
✅ Orçamento de "Alimentação > Mercado" definido: R$ 800,00/mês
```

O grupo não tem mais orçamento próprio — o total exibido no resumo é `SUM(subgrupos.orcamento_mensal)` onde `subgrupo.grupo_id = grupo.id`.

No lançamento, subgrupo continua posicional (posição 5). Se o subgrupo não existir para aquele grupo, o bot cria automaticamente com `orcamento_mensal = 0`. Se o grupo também não existir, cria também.

### Arquivos a criar
- `alembic/versions/XXXX_add_subgrupos.py` — cria tabela `subgrupos`, migra dados e altera `lancamentos`

### Arquivos a modificar
- `app/models/grupo.py` — remover `orcamento_mensal` de `Grupo`; adicionar relationship para `Subgrupo`
- `app/models/subgrupo.py` — novo model `Subgrupo (id, grupo_id FK, nome, orcamento_mensal)`
- `app/models/__init__.py` — exportar `Subgrupo`
- `app/schemas.py` — `OrcamentoDTO` recebe `subgrupo: str`; `LancamentoInput` mantém `subgrupo: str` (resolve para FK no service)
- `app/services/parser.py` — `parse_orcamento` passa a exigir grupo + subgrupo + valor
- `app/services/lancamento.py` — `salvar_lancamento` resolve subgrupo por nome+grupo (cria se não existir); `definir_orcamento` salva em `subgrupos.orcamento_mensal`
- `app/services/resumo.py` — `calcular_resumo` usa `SUM(subgrupos.orcamento_mensal)` como orçamento do grupo; breakdown por subgrupo usa `subgrupos.orcamento_mensal`
- `app/services/mensagem.py` — ajustar formatação para novo formato de resposta de orçamento
- `app/services/jobs.py` — ajustar queries de resumo agendado se necessário
- `requirements.md` — atualizar seção "Dados a Persistir" e formato do comando orçamento

### Critérios de aceitação
- [ ] Tabela `subgrupos (id, grupo_id FK, nome, orcamento_mensal DECIMAL default 0, UNIQUE(grupo_id, nome))` criada via migration
- [ ] `lancamentos.subgrupo` (string) substituída por `lancamentos.subgrupo_id` (FK para `subgrupos.id`)
- [ ] Migration preserva dados existentes: subgrupos únicos por grupo são inseridos na nova tabela e os lançamentos recebem o `subgrupo_id` correto
- [ ] `grupos.orcamento_mensal` removida do model (orçamento vem dos subgrupos)
- [ ] `orçamento: Alimentação - Mercado - 800` salva em `subgrupos.orcamento_mensal`
- [ ] Lançamento com subgrupo inexistente cria o subgrupo automaticamente com `orcamento_mensal = 0`
- [ ] Lançamento com grupo inexistente cria grupo E subgrupo automaticamente
- [ ] Resumo exibe orçamento do grupo como soma dos orçamentos dos seus subgrupos
- [ ] `resumo: <grupo>` exibe breakdown por subgrupo com orçamento individual de cada um
- [ ] Comando antigo `orçamento: <grupo> - <valor>` responde com erro explicando o novo formato

---

## ORCA-T001 — Orçamento mensal por mês/ano específico

**Épico:** Gestão de Orçamento
**Prioridade:** Média
**Complexidade:** Média
**Status:** [ ] Não iniciada

### Contexto
O sistema atual armazena um único valor de orçamento por grupo (`orcamento_mensal` na tabela `grupos`), que se repete todo mês. O usuário quer poder definir orçamentos diferentes para meses específicos — ex: dezembro com orçamento maior por ser fim de ano, ou ajuste pontual de um mês sem alterar o padrão.

### Descrição
Adicionar suporte a orçamento mensal específico por mês/ano. A prioridade de uso:
1. Se houver orçamento definido para o mês exato → usa esse valor
2. Se não houver → usa o `orcamento_mensal` genérico do grupo (fallback)
3. Se nenhum dos dois existir → omite linha 📊 (comportamento atual)

**Novo formato de comando:**
```
orçamento: <grupo> - <valor> - mes: MM/AA
```
**Exemplo:**
```
orçamento: alimentação - 500 - mes: 12/26
```
**Resposta:**
```
✅ Orçamento de "alimentação" para 12/2026 definido: R$ 500,00
```

O comando existente sem `mes:` continua funcionando e atualiza o `orcamento_mensal` genérico:
```
orçamento: alimentação - 300
```

### Arquivos a criar
- `alembic/versions/XXXX_add_orcamentos_mensais.py` — nova tabela `orcamentos_mensais`

### Arquivos a modificar
- `app/models.py` — adicionar model `OrcamentoMensal` com colunas `grupo_id`, `mes` (DATE, primeiro dia do mês), `valor`
- `app/services/parser.py` — estender `parse_orcamento` para detectar campo `mes: MM/AA`
- `app/services/lancamento.py` — `definir_orcamento` passa a aceitar `mes` opcional; cria ou atualiza `OrcamentoMensal` quando informado
- `app/services/resumo.py` — `calcular_resumo` busca primeiro em `OrcamentoMensal` para o mês atual antes de usar o genérico
- `app/schemas.py` — atualizar `OrcamentoDTO` com campo `mes` opcional

### Critérios de aceitação
- [ ] Nova tabela `orcamentos_mensais (id, grupo_id FK, mes DATE, valor DECIMAL)` criada via migration
- [ ] `orçamento: alimentação - 500 - mes: 12/26` salva orçamento específico para dezembro/2026
- [ ] `orçamento: alimentação - 300` continua funcionando e atualiza o campo genérico do grupo
- [ ] Resumo do mês usa orçamento específico se existir, senão usa o genérico
- [ ] Resposta distingue: "para 12/2026" vs "/mês" dependendo do tipo definido
- [ ] `mes:` inválido (ex: `mes: 13/26`) responde com erro de formato

---

## PARCELA-T001 — Lançamento de compra parcelada

**Épico:** Lançamentos
**Prioridade:** Média
**Complexidade:** Média
**Status:** [ ] Não iniciada

### Contexto
Atualmente toda compra é registrada como um único lançamento. O usuário quer registrar compras parceladas (ex: TV em 12x) de uma só vez — o bot cria N lançamentos automáticos, um por mês, com `data_pagamento` distribuída mensalmente.

### Descrição
Novo campo posicional/chave no formato de lançamento: `parcelas: N`

**Formato:**
```
DD/MM/AA - <descrição> - <valor total> - <Grupo> - <Subgrupo> - parcelas: N - inicio: MM/AA [- cartao: <cartão>]
```

- `parcelas: N` — número de parcelas (obrigatório para ativar o modo parcelado)
- `inicio: MM/AA` — mês da primeira parcela (obrigatório quando parcelado)

**Exemplo:**
```
01/05/26 - tv samsung - 1200 - Casa - Eletrodoméstico - parcelas: 12 - inicio: 06/26 - cartao: bradesco
```

O bot cria 12 lançamentos:
- `valor = 1200 / 12 = R$ 100,00` cada
- `data_gasto = 01/05/2026` (igual para todos — data da compra)
- `data_pagamento` = primeiro dia dos meses 06/26, 07/26, ..., 05/27 (a partir de `inicio:`)
- `descricao = "tv samsung (1/12)", "tv samsung (2/12)", ...`
- `cartao = bradesco` (se informado, igual para todos)
- `hash_msg` único por lançamento (hash do texto + índice da parcela)

**Resposta do bot:**
```
✅ 12 parcelas salvas!
📦 tv samsung — R$ 1.200,00 em 12x de R$ 100,00
📅 Primeira parcela: 06/2026 | Última: 05/2027
📂 Casa: R$ 100,00 gastos em 06/2026
📊 Orçamento: R$ 500,00 | Gasto: R$ 100,00 | Restante: R$ 400,00
```

### Arquivos a modificar
- `app/services/parser.py` — `parse_lancamento` detecta campos `parcelas: N` e `inicio: MM/AA`; retorna `LancamentoInput` com `parcelas: int` (default 1) e `inicio_parcela: date | None`
- `app/services/lancamento.py` — quando `parcelas > 1`: loop de N iterações gerando lançamentos com `data_pagamento` incrementando mês a mês; each com hash único; retorna lista de IDs salvos
- `app/schemas.py` — `LancamentoInput` recebe campos `parcelas: int = 1` e `inicio_parcela: date | None = None`
- `app/services/mensagem.py` — `formatar_resposta_lancamento` detecta lançamento parcelado e usa template de resposta multi-parcela
- `app/routers/webhook.py` — ajustar chamada a `salvar_lancamento` para tratar retorno como lista quando parcelado

### Critérios de aceitação
- [ ] `parcelas: 12` no lançamento cria exatamente 12 registros no banco
- [ ] Cada lançamento tem `valor = valor_total / N` (arredondado 2 casas)
- [ ] `data_pagamento` incrementa 1 mês a cada lançamento, começando em `inicio: MM/AA`
- [ ] `descricao` de cada parcela inclui sufixo `(X/N)`
- [ ] Deduplicação funciona: reenvio da mesma mensagem não duplica as parcelas
- [ ] `parcelas: N` sem `inicio:` → responde com erro pedindo o campo obrigatório
- [ ] `inicio:` com mês inválido (ex: `inicio: 13/26`) → responde com erro de formato
- [ ] `parcelas: 1` (ou sem campo) mantém comportamento atual sem regressão
- [ ] `parcelas: 0` ou negativo → responde com erro de formato
- [ ] `parcelas > 60` → responde com aviso de limite (máximo razoável)
- [ ] Resposta do bot exibe total, valor por parcela, mês inicial e final
- [ ] Resumo do mês atual reflete apenas a parcela do mês (não o total)

---

## ALIAS-T001 — Sistema de aliases para categorização automática de lançamentos

**Épico:** Inteligência do Parser
**Prioridade:** Média
**Complexidade:** Média
**Status:** [ ] Não iniciada
**Depende de:** SUBGRUPO-T001

### Contexto
O formato atual exige 5 campos posicionais em todo lançamento, incluindo grupo e subgrupo. Para gastos recorrentes (padaria, uber, netflix), o usuário digita os mesmos campos toda vez. Um sistema de aliases mapeia palavras-chave de descrição para grupo+subgrupo automaticamente, permitindo lançamentos mais curtos. O usuário cadastra os aliases via WhatsApp e o bot os aplica automaticamente.

### Descrição

**Cadastrar alias:**
```
alias: <palavra-chave> → <Grupo> > <Subgrupo>
```
Exemplo:
```
alias: padaria → Alimentação > Padaria
alias: uber → Transporte > App
alias: netflix → Lazer > Streaming
```
Resposta:
```
✅ Alias criado: "padaria" → Alimentação > Padaria
```

**Lançamento com alias (formato curto):**
Quando a descrição bater exatamente com um alias cadastrado, grupo e subgrupo são inferidos automaticamente:
```
25/05/26 - padaria - 25
```
É equivalente a:
```
25/05/26 - padaria - 25 - Alimentação - Padaria
```
Se a descrição não tiver alias, o bot exige o formato completo normalmente.

**Listar aliases:**
```
aliases
```
Resposta:
```
📋 Aliases cadastrados:
• padaria → Alimentação > Padaria
• uber → Transporte > App
• netflix → Lazer > Streaming
```

**Remover alias:**
```
remove alias: <palavra-chave>
```
Resposta:
```
✅ Alias "padaria" removido.
```

**Menu de ajuda:** seção "Aliases" adicionada ao comando `ajuda` com formato e exemplos.

### Arquivos a criar
- `alembic/versions/XXXX_add_aliases.py` — nova tabela `aliases`

### Arquivos a modificar
- `app/models/alias.py` — novo model `Alias (id, palavra_chave String unique, subgrupo_id FK → subgrupos.id)`
- `app/models/__init__.py` — exportar `Alias`
- `app/services/parser.py` — `parse_lancamento` aceita formato curto (sem grupo/subgrupo); retorna `subgrupo_id=None` quando ausente para resolução posterior
- `app/services/lancamento.py` — antes de salvar, se `subgrupo_id=None`: busca alias pela descrição normalizada; se encontrar, usa o `subgrupo_id` do alias; se não encontrar, rejeita com mensagem de erro e formato esperado
- `app/services/alias.py` — novo service: `criar_alias`, `remover_alias`, `listar_aliases`, `resolver_alias(descricao) → Alias | None`
- `app/routers/webhook.py` — detectar comandos `alias:`, `aliases`, `remove alias:` e rotear para o service
- `app/services/mensagem.py` — templates de resposta para alias criado/removido/listado; seção de aliases no menu de ajuda

### Critérios de aceitação
- [ ] Tabela `aliases (id, palavra_chave VARCHAR unique, subgrupo_id FK)` criada via migration
- [ ] `alias: padaria → Alimentação > Padaria` cria registro e responde confirmação
- [ ] `alias:` com grupo ou subgrupo inexistente responde com erro indicando o nome inválido
- [ ] Lançamento `25/05/26 - padaria - 25` resolve grupo e subgrupo pelo alias e salva corretamente
- [ ] Lançamento sem alias e sem grupo/subgrupo explícito responde com erro e formato esperado
- [ ] `aliases` lista todos os aliases cadastrados (resposta vazia se não houver nenhum)
- [ ] `remove alias: padaria` remove o registro e confirma; alias inexistente responde com erro
- [ ] Matching de alias é case-insensitive e ignora acentuação (`Padaria` = `padaria` = `pãdaria`)
- [ ] Comando `ajuda` inclui seção de aliases com formato e exemplos
- [ ] Alias com `→` ou `->` são ambos aceitos no cadastro

---

## TEMPLATE-T001 — Templates para lançamentos fixos recorrentes

**Épico:** Inteligência do Parser
**Prioridade:** Média
**Complexidade:** Baixa
**Status:** [x] Concluída — 25/05/2026
**Depende de:** SUBGRUPO-T001

### Contexto
Gastos fixos mensais (aluguel, academia, assinaturas) têm sempre o mesmo valor, grupo e subgrupo. O usuário precisa digitar tudo toda vez. Templates guardam o lançamento completo — na hora de registrar, basta digitar o nome do template.

### Descrição

**Cadastrar template:**
```
template: <nome> - <descrição> - <valor> - <Grupo> - <Subgrupo> [- cartao: <cartão>]
```
Exemplo:
```
template: aluguel - aluguel ap - 1500 - Moradia - Aluguel
template: academia - smartfit - 99,90 - Saúde - Academia - cartao: nubank
```
Resposta:
```
✅ Template "aluguel" criado: aluguel ap — R$ 1.500,00 → Moradia > Aluguel
```

**Usar template (cria lançamento com data de hoje):**
```
aluguel
```
Resposta igual a um lançamento normal, com data do dia atual.

**Listar templates:**
```
templates
```
Resposta:
```
📋 Templates cadastrados:
• aluguel → aluguel ap | R$ 1.500,00 | Moradia > Aluguel
• academia → smartfit | R$ 99,90 | Saúde > Academia | nubank
```

**Remover template:**
```
remove template: <nome>
```

### Arquivos a criar
- `alembic/versions/XXXX_add_templates.py` — nova tabela `templates`
- `app/models/template.py` — model `Template (id, nome String unique, descricao, valor, subgrupo_id FK, cartao nullable)`
- `app/services/template.py` — `criar_template`, `remover_template`, `listar_templates`, `resolver_template(nome) → Template | None`

### Arquivos a modificar
- `app/models/__init__.py` — exportar `Template`
- `app/routers/webhook.py` — detectar `template:`, `templates`, `remove template:` e mensagem que bate com nome de template existente
- `app/services/lancamento.py` — `salvar_lancamento_de_template` usa data de hoje + dados do template
- `app/services/mensagem.py` — templates de resposta para criado/removido/listado; seção no menu de ajuda

### Critérios de aceitação
- [x] Tabela `templates (id, nome VARCHAR unique, descricao, valor, subgrupo_id FK, cartao nullable)` criada via migration
- [x] `template: aluguel - aluguel ap - 1500 - Moradia - Aluguel` cria o template e confirma
- [x] `template:` com grupo/subgrupo inexistente responde com erro
- [x] Digitar `aluguel` cria lançamento com data de hoje usando os dados do template
- [x] Template inexistente digitado como comando cai no fluxo normal (não dá erro de template)
- [x] `templates` lista todos com nome, descrição, valor, grupo>subgrupo e cartão se houver
- [x] `remove template: aluguel` remove e confirma; inexistente responde com erro
- [x] Deduplicação funciona: usar o mesmo template duas vezes no mesmo dia não duplica
- [x] Comando `ajuda` inclui seção de templates com formato e exemplos

---

## MULTI-T001 — Lançamento múltiplo numa mensagem

**Épico:** Inteligência do Parser
**Prioridade:** Média
**Complexidade:** Média
**Status:** [ ] Não iniciada
**Depende de:** ALIAS-T001, PARCELA-T001

### Contexto
Ao acumular vários gastos durante o dia, o usuário precisa mandar uma mensagem por lançamento. O formato múltiplo permite registrar tudo de uma vez com uma única mensagem: data no cabeçalho e um lançamento por linha.

### Descrição

**Formato:**
```
DD/MM/AA
<descrição> - <valor> [- <Grupo> - <Subgrupo>] [- cartao: <cartão>] [- parcelas: N - inicio: MM/AA]
<descrição> - <valor> [- <Grupo> - <Subgrupo>] [- cartao: <cartão>]
...
```

Exemplo:
```
25/05/26
padaria - 25
uber - 18 - cartao: nubank
tv samsung - 1200 - Casa - Eletrodoméstico - parcelas: 12 - inicio: 06/26 - cartao: bradesco
mercado - 95 - Alimentação - Mercado
```

- Data do cabeçalho se aplica a todos os lançamentos da mensagem
- Cada linha pode ter campos opcionais próprios (cartão, parcelas)
- Linhas sem grupo/subgrupo resolvem por alias; sem alias → erro indicando qual linha falhou
- Linhas com `parcelas:` geram N lançamentos normalmente

**Resposta consolidada:**
```
✅ 4 lançamentos salvos!
• padaria — R$ 25,00 → Alimentação > Padaria
• uber — R$ 18,00 → Transporte > App
• tv samsung — R$ 1.200,00 em 12x → Casa > Eletrodoméstico
• mercado — R$ 95,00 → Alimentação > Mercado

📊 Alimentação: R$ 120,00 gastos | Orçamento: R$ 800,00 | Restante: R$ 680,00
📊 Transporte: R$ 18,00 gastos | Orçamento: R$ 300,00 | Restante: R$ 282,00
📊 Casa: R$ 100,00 gastos (1ª parcela em 06/2026)
```

### Arquivos a modificar
- `app/services/parser.py` — detectar formato múltiplo (primeira linha = data isolada, demais = lançamentos); retornar lista de `LancamentoInput`
- `app/routers/webhook.py` — quando parser retornar lista, processar cada item e agregar respostas
- `app/services/lancamento.py` — sem mudança (já processa um lançamento por vez)
- `app/services/mensagem.py` — `formatar_resposta_multiplo` — template de resposta consolidada com breakdown por grupo

### Critérios de aceitação
- [ ] Mensagem com data isolada na primeira linha seguida de N linhas é detectada como formato múltiplo
- [ ] Cada linha é parseada independentemente com seus campos opcionais
- [ ] Linhas resolvem alias normalmente; linha sem alias e sem grupo/subgrupo retorna erro indicando a linha problemática e continua processando as demais
- [ ] Linhas com `parcelas:` geram N lançamentos cada
- [ ] Deduplicação funciona por linha (reenvio da mensagem não duplica)
- [ ] Resposta consolida todos os lançamentos salvos e exibe resumo por grupo afetado
- [ ] Mensagem com apenas uma linha no formato múltiplo funciona normalmente (equivalente ao formato simples)
- [ ] Formato simples (`DD/MM/AA - desc - valor - ...`) continua funcionando sem regressão

---

---

## COMPARE-T001 — Comparativo mensal automático no dia 1

**Épico:** Inteligência Analítica
**Prioridade:** Média
**Complexidade:** Baixa
**Status:** [x] Concluída — 25/05/2026

### Contexto
No dia 1 de cada mês o usuário não tem visibilidade de como foi o mês que fechou vs o anterior. O job automático entrega esse comparativo direto no WhatsApp sem precisar pedir nada.

### Descrição
Novo job agendado: todo dia 1 às 08h00 BRT, envia comparativo do mês que acabou de fechar vs o mês anterior.

**Formato da mensagem:**
```
📊 Fechamento de abril/2026

📂 Alimentação
  Gasto: R$ 620,00 | Orçamento: R$ 800,00 (77%) ✅
  vs março: R$ 540,00 → +R$ 80,00 (+14%) ⬆️

📂 Transporte
  Gasto: R$ 180,00 | Orçamento: R$ 300,00 (60%) ✅
  vs março: R$ 210,00 → -R$ 30,00 (-14%) ⬇️

📂 Lazer
  Gasto: R$ 350,00 | Orçamento: R$ 200,00 (175%) 🚨
  vs março: R$ 120,00 → +R$ 230,00 (+191%) ⬆️

💰 Total gasto: R$ 1.150,00 | Orçamento total: R$ 1.300,00 (88%)
vs março: R$ 870,00 → +R$ 280,00 (+32%)
```

Ícones de variação:
- `⬆️` aumento de gasto
- `⬇️` redução de gasto
- `➡️` variação < 5% (estável)

### Arquivos a modificar
- `app/services/resumo.py` — `calcular_comparativo(mes_atual, mes_anterior) → ComparativoDTO` com delta absoluto e percentual por grupo
- `app/schemas.py` — `ComparativoDTO` e `ComparativoGrupoDTO`
- `app/services/mensagem.py` — `formatar_comparativo(comparativo: ComparativoDTO) → str`
- `app/services/jobs.py` — novo job `job_comparativo_mensal` agendado para dia 1 às 08h00 BRT; registrar no scheduler do FastAPI

### Critérios de aceitação
- [x] Job executa todo dia 1 às 08h00 BRT
- [x] Compara mês `M-1` vs mês `M-2` (ex: no dia 1/06 compara mai vs abr)
- [x] Exibe gasto real, orçamento e percentual de cada grupo
- [x] Exibe delta absoluto e percentual vs mês anterior por grupo
- [x] Ícone `⬆️` quando aumento, `⬇️` quando redução, `➡️` quando variação < 5%
- [x] Alerta `🚨` em grupos que estouraram orçamento no mês fechado
- [x] Grupos sem lançamento em nenhum dos dois meses são omitidos
- [x] Grupo sem lançamento no mês anterior mas com gasto no mês fechado aparece como "novo" sem delta
- [x] Total consolidado ao final com delta geral

---

## LEMBRETE-T001 — Lembretes de contas vinculados a templates

**Épico:** Inteligência Analítica
**Prioridade:** Média
**Complexidade:** Média
**Status:** [ ] Não iniciada
**Depende de:** TEMPLATE-T001

### Contexto
Contas fixas mensais (aluguel, condomínio, academia) têm vencimento previsível. O usuário quer ser avisado antes do vencimento e confirmar o lançamento respondendo uma mensagem — sem precisar digitar nada além da confirmação.

### Descrição

**Cadastrar lembrete (referencia um template existente):**
```
lembrete: <nome-template> - dia <N>
```
Exemplo:
```
lembrete: aluguel - dia 5
lembrete: academia - dia 1
```
Resposta:
```
✅ Lembrete criado: "aluguel" vence todo dia 5.
Você será avisado 2 dias antes.
```

**Modo automático (lança sem precisar confirmar):**
```
lembrete: aluguel - dia 5 - auto
```
Resposta:
```
✅ Lembrete criado: "aluguel" será lançado automaticamente todo dia 5.
```

**Mensagem de lembrete (enviada 2 dias antes do vencimento, 08h00 BRT):**
```
⏰ Aluguel vence em 2 dias (dia 5)!
aluguel ap — R$ 1.500,00 → Moradia > Aluguel

Responda "lançar aluguel" para registrar automaticamente.
```

**Usuário confirma:**
```
lançar aluguel
```
Bot cria o lançamento a partir do template com data de hoje e responde normalmente como um lançamento salvo.

**Modo auto:** bot lança no próprio dia do vencimento às 08h00 sem precisar de confirmação, e envia a confirmação de registro.

**Listar lembretes:**
```
lembretes
```
Resposta:
```
📋 Lembretes cadastrados:
• aluguel → dia 5 | aluguel ap | R$ 1.500,00 (manual)
• academia → dia 1 | smartfit | R$ 99,90 (auto)
```

**Remover lembrete:**
```
remove lembrete: <nome-template>
```

### Arquivos a criar
- `alembic/versions/XXXX_add_lembretes.py` — nova tabela `lembretes`
- `app/models/lembrete.py` — model `Lembrete (id, template_id FK, dia_vencimento INT, auto BOOL default false)`
- `app/services/lembrete.py` — `criar_lembrete`, `remover_lembrete`, `listar_lembretes`, `processar_lembretes_do_dia`

### Arquivos a modificar
- `app/models/__init__.py` — exportar `Lembrete`
- `app/services/jobs.py` — job diário 08h00 BRT chama `processar_lembretes_do_dia`: envia aviso 2 dias antes (manual) ou lança automaticamente no dia (auto)
- `app/routers/webhook.py` — detectar `lembrete:`, `lembretes`, `remove lembrete:`, `lançar <template>`
- `app/services/mensagem.py` — templates de resposta para lembrete criado/removido/listado e mensagem de aviso de vencimento

### Critérios de aceitação
- [ ] Tabela `lembretes (id, template_id FK, dia_vencimento INT 1-31, auto BOOL)` criada via migration
- [ ] `lembrete: aluguel - dia 5` cria lembrete manual vinculado ao template "aluguel"
- [ ] `lembrete: aluguel - dia 5 - auto` cria lembrete em modo automático
- [ ] `lembrete:` com template inexistente responde com erro
- [ ] Job diário envia aviso 2 dias antes do vencimento no modo manual
- [ ] `lançar aluguel` após o aviso cria o lançamento a partir do template com data de hoje
- [ ] Job diário lança automaticamente no dia do vencimento no modo auto e envia confirmação
- [ ] Deduplicação: lembrete auto não lança duas vezes no mesmo mês (mesmo dia)
- [ ] `lembretes` lista todos com modo (manual/auto), dia e dados do template
- [ ] `remove lembrete: aluguel` remove e confirma; inexistente responde com erro
- [ ] Comando `ajuda` inclui seção de lembretes com formato e exemplos

---

## PERIODO-T001 — Resumo por período customizado

**Épico:** Inteligência Analítica
**Prioridade:** Baixa
**Complexidade:** Baixa
**Status:** [ ] Não iniciada

### Contexto
O resumo padrão sempre cobre o mês inteiro. Para ver gastos de uma viagem, uma quinzena ou qualquer recorte específico, o usuário precisa de flexibilidade de data.

### Descrição

**Formato:**
```
resumo: DD/MM a DD/MM
```
Exemplos:
```
resumo: 01/05 a 15/05
resumo: 10/05 a 25/05
```
Assume o ano corrente. Filtra por `data_pagamento` no intervalo inclusivo.

Resposta (sem comparação de orçamento — só totais do período):
```
📊 Resumo: 01/05 a 15/05/2026

📂 Alimentação
  └ Mercado: R$ 95,00
  └ Padaria: R$ 42,00
  Total: R$ 137,00

📂 Transporte
  └ App: R$ 54,00
  Total: R$ 54,00

💰 Total do período: R$ 191,00
```

### Arquivos a modificar
- `app/services/parser.py` — detectar padrão `resumo: DD/MM a DD/MM` e retornar `ResumoInput` com `data_inicio` e `data_fim`
- `app/services/resumo.py` — `calcular_resumo_periodo(data_inicio, data_fim) → ResumoPeriodoDTO` filtrando por `data_pagamento BETWEEN`
- `app/schemas.py` — `ResumoPeriodoDTO`
- `app/services/mensagem.py` — `formatar_resumo_periodo → str`
- `app/routers/webhook.py` — rotear para `calcular_resumo_periodo` quando detectar o padrão de período

### Critérios de aceitação
- [ ] `resumo: 01/05 a 15/05` retorna lançamentos com `data_pagamento` entre 01/05 e 15/05 do ano corrente
- [ ] Exibe breakdown por grupo > subgrupo com total por grupo e total geral do período
- [ ] `data_inicio > data_fim` responde com erro de intervalo inválido
- [ ] Período sem lançamentos responde `📭 Nenhum lançamento no período informado.`
- [ ] Não exibe orçamento nem percentual (apenas totais reais)
- [ ] Formato existente `resumo`, `resumo: <grupo>` e `resumo: MM/AA` continuam funcionando sem regressão

---

## BAILEYS-T001 — Serviço Baileys customizado (substitui Evolution API)

**Épico:** Infraestrutura WhatsApp
**Prioridade:** Alta
**Complexidade:** Média
**Status:** [x] Concluída — 25/05/2026

### Contexto
A Evolution API apresenta bug de loop infinito de reconexão em todas as versões publicadas (v2.2.3 e anteriores), impedindo a geração do QR code no Railway. A solução é um serviço Node.js minimalista com Baileys direto, sem dependência de terceiros.

### Descrição
Criar um serviço Node.js com Baileys dentro do repositório `bot-finan`, em `baileys-service/`. O serviço deve:
- Conectar ao WhatsApp e expor o QR code via endpoint HTTP
- Receber mensagens e repassá-las ao webhook do bot FastAPI
- Expor endpoint `/send` para o bot enviar mensagens

### Arquivos a criar
- `baileys-service/index.js`
- `baileys-service/package.json`
- `baileys-service/Dockerfile`

### Arquivos a modificar
- `app/services/whatsapp.py` — ajustar URL e formato do payload de envio

### Critérios de aceitação
- [ ] Serviço sobe no Railway como segundo serviço do projeto
- [ ] QR code gerado e acessível via `GET /qrcode`
- [ ] Celular conectado com sucesso após scan do QR
- [ ] Mensagem enviada pelo WhatsApp chega no webhook do bot (`/webhook/evolution`)
- [ ] Bot consegue responder via endpoint `/send` do serviço Baileys
- [ ] Variável `EVOLUTION_API_URL` substituída por `BAILEYS_SERVICE_URL` no bot
