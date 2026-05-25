# Tasks — Backlog

> Fase 2 — todas as tasks foram implementadas em 25/05/2026. Backlog vazio.

---

## Épico: Comandos Interativos

### CMD-T001 — Menu de ajuda completo
**Trigger:** Qualquer mensagem inválida ou comando `ajuda`
**Complexidade:** Baixa
**Critérios de aceitação:**
- [ ] Comando `ajuda` retorna lista completa de todos os comandos disponíveis com formato e exemplo
- [ ] Mensagem inválida continua retornando o menu de ajuda (comportamento atual preservado)
- [ ] Menu inclui: lançamento, orçamento, resumo, relatório cartão, últimos, cancelar

---

### CMD-T002 — Relatório de gastos por cartão
**Trigger:** Comando no WhatsApp
**Formato:** `cartao: <nome> [- mes: MM/AA]`
**Exemplo:** `cartao: bradesco` ou `cartao: bradesco - mes: 05/26`
**Complexidade:** Média
**Critérios de aceitação:**
- [ ] Filtra lançamentos pelo campo `cartao` (case-insensitive)
- [ ] Sem `mes:` → usa mês atual (filtra por `data_pagamento`)
- [ ] Com `mes:` → filtra pelo mês especificado
- [ ] Resposta lista total gasto no cartão + breakdown por grupo
- [ ] Cartão não encontrado → responde "Nenhum lançamento para o cartão X"

---

### CMD-T003 — Resumo on-demand
**Trigger:** Comando no WhatsApp
**Formato:** `resumo` ou `resumo: <grupo>` ou `resumo: <MM/AA>`
**Exemplos:** `resumo`, `resumo: alimentação`, `resumo: 04/26`
**Complexidade:** Média
**Critérios de aceitação:**
- [ ] `resumo` → mostra todos os grupos do mês atual com gasto vs orçamento e percentual
- [ ] `resumo: <grupo>` → mostra apenas aquele grupo, com breakdown por subgrupo
- [ ] `resumo: <MM/AA>` → mostra todos os grupos do mês especificado
- [ ] Inclui alerta visual quando grupo >= 80% do orçamento (ex: ⚠️)
- [ ] Inclui alerta quando grupo >= 100% do orçamento (ex: 🚨)
- [ ] Grupo sem orçamento definido → mostra gasto sem linha de percentual

---

### CMD-T004 — Listar lançamentos recentes
**Trigger:** Comando no WhatsApp
**Formato:** `ultimos: <N>`
**Exemplo:** `ultimos: 5`
**Complexidade:** Baixa
**Critérios de aceitação:**
- [ ] Retorna os N lançamentos mais recentes ordenados por `criado_em` DESC
- [ ] Cada item mostra: ID, data, descrição, valor, grupo/subgrupo
- [ ] N máximo: 20 (acima disso responde com aviso)
- [ ] N inválido ou ausente → responde com formato correto

---

### CMD-T005 — Cancelar/deletar lançamento
**Trigger:** Comando no WhatsApp
**Formato:** `cancela: <id>`
**Exemplo:** `cancela: 42`
**Complexidade:** Média
**Dependência:** CMD-T004 (usuário usa `ultimos` para descobrir o ID)
**Critérios de aceitação:**
- [ ] Resposta de confirmação de lançamento salvo passa a incluir o ID (ex: `✅ Lançamento #42 salvo!`)
- [ ] `cancela: <id>` deleta o lançamento do banco
- [ ] Confirma: "✅ Lançamento #42 cancelado: padaria — R$ 25,00"
- [ ] ID não encontrado → "❌ Lançamento #42 não encontrado"
- [ ] Após cancelar: recalcula e exibe novo resumo do grupo afetado

---

## Épico: Alertas no Resumo

### ALERTA-T001 — Percentual de orçamento na resposta de lançamento
**Trigger:** Automático — junto com a resposta de cada lançamento salvo
**Complexidade:** Baixa
**Dependência:** Funcionalidade já existe, é expansão do response atual
**Critérios de aceitação:**
- [ ] Resposta de lançamento salvo passa a incluir percentual do orçamento usado
- [ ] Ex: `📊 Orçamento: R$ 300,00 | Gasto: R$ 185,00 | Restante: R$ 115,00 (61%)`
- [ ] Se >= 80%: adiciona `⚠️ Atenção: 80% do orçamento utilizado`
- [ ] Se >= 100%: adiciona `🚨 Orçamento estourado!`
- [ ] Grupo sem orçamento → comportamento atual (omite linha 📊)

---

## Épico: Jobs Agendados

### JOB-T001 — Job diário 06h — resumo do dia anterior
**Trigger:** Cron todo dia às 06h00 (horário de Brasília)
**Complexidade:** Média
**Critérios de aceitação:**
- [ ] Roda todos os dias às 06h (BRT = UTC-3)
- [ ] Busca lançamentos onde `data_gasto` = ontem
- [ ] Se nenhum gasto ontem → envia mensagem "📭 Nenhum gasto registrado ontem."
- [ ] Se houver gastos → envia lista: data, descrição, valor, grupo/subgrupo, cartão (se houver)
- [ ] Ao final da lista: total do dia
- [ ] Envia via Evolution API para o mesmo grupo

---

### JOB-T002 — Job a cada 2 dias — resumo por grupo/subgrupo
**Trigger:** Cron a cada 2 dias às 08h00 (horário de Brasília)
**Complexidade:** Média
**Critérios de aceitação:**
- [ ] Roda a cada 2 dias às 08h (BRT)
- [ ] Mostra gastos do mês corrente agrupados por grupo → subgrupo
- [ ] Cada grupo: total do grupo + breakdown por subgrupo com valor
- [ ] Inclui percentual do orçamento se definido (+ alertas ⚠️/🚨 quando aplicável)
- [ ] Envia via Evolution API para o mesmo grupo

---

## Notas de implementação

- Jobs precisam de scheduler: **APScheduler** (recomendado, integra com FastAPI) ou cron no Docker
- Timezone dos jobs: `America/Sao_Paulo`
- CMD-T005 (cancela) requer que o ID seja exposto na resposta → implementar junto com ALERTA-T001 (que já toca na resposta de confirmação)
