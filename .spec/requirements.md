# Requirements — bot-finan

> Atualizado em 25/05/2026
> Tipo: Automação — Bot WhatsApp de gestão financeira pessoal

## O que Faz

Bot de gestão financeira pessoal integrado ao WhatsApp via Evolution API.
O usuário envia mensagens padronizadas em um grupo próprio e o bot:
1. Faz o parse da mensagem
2. Salva o lançamento no banco de dados
3. Responde automaticamente com o saldo restante do orçamento do grupo

## Comandos Suportados

### 1. Lançamento de gasto

**Formato:**
```
DD/MM/AA - <descrição> - <valor> - <Grupo> - <Subgrupo> [- cartao: <cartão>] [- pagamento: DD/MM]
```

**Exemplo completo:**
```
25/05/26 - padaria - 25 - Alimentação - Padaria - cartao: bradesco - pagamento: 20/06
```

**Exemplo mínimo:**
```
25/05/26 - uber - 18 - Transporte - App
```

**Campos:**
| Campo | Obrigatório | Posição | Descrição |
|-------|-------------|---------|-----------|
| data | Sim | 1 | Data do gasto (DD/MM/AA) |
| descrição | Sim | 2 | Nome do estabelecimento ou gasto |
| valor | Sim | 3 | Valor gasto (número, ex: 25 ou 25,90) |
| grupo | Sim | 4 | Categoria principal (posicional, sem prefixo) |
| subgrupo | Sim | 5 | Subcategoria (posicional, sem prefixo) |
| cartao | Não | chave | Cartão utilizado (`cartao: nome`) |
| pagamento | Não | chave | Data de pagamento da fatura (`pagamento: DD/MM`) |

> Grupo e subgrupo são posicionais — vêm direto por posição, sem `grupo:` ou `subgrupo:` na frente.
> Se grupo ou subgrupo estiver ausente, o bot rejeita e mostra o formato correto.

**Resposta do bot:**
```
✅ Lançamento salvo!
📂 ref. fora de casa: R$ 25,00 gastos este mês
📊 Orçamento: R$ 300,00 | Gasto: R$ 185,00 | Restante: R$ 115,00
```
> Se orçamento não definido (= 0): omite a linha 📊

### 2. Definir/redefinir orçamento de grupo

**Formato:**
```
orçamento: <grupo> - <valor>
```

**Exemplo:**
```
orçamento: ref. fora de casa - 300
```

**Resposta do bot:**
```
✅ Orçamento de "ref. fora de casa" definido: R$ 300,00/mês
```

### 3. Menu de ajuda

**Trigger:** Mensagem inválida **ou** comando `ajuda`

Bot responde com menu completo listando todos os comandos disponíveis, formato e exemplo de cada um.

---

### 4. Relatório por cartão

**Formato:** `cartao: <nome>` ou `cartao: <nome> - mes: MM/AA`

**Resposta:** Total gasto no cartão + breakdown por grupo, filtrado por `data_pagamento`.

---

### 5. Resumo on-demand

**Formato:** `resumo` | `resumo: <grupo>` | `resumo: <MM/AA>`

**Resposta:**
- Sem argumento → todos os grupos do mês atual com gasto, orçamento e percentual
- Com grupo → breakdown por subgrupo daquele grupo
- Com mês → resumo do mês especificado

**Alertas de orçamento:**
- >= 80% → `⚠️ Atenção: X% do orçamento utilizado`
- >= 100% → `🚨 Orçamento estourado!`

---

### 6. Listar lançamentos recentes

**Formato:** `ultimos: <N>` (N máximo: 20)

**Resposta:** Lista dos N lançamentos mais recentes com ID, data, descrição, valor, grupo/subgrupo.

---

### 7. Cancelar lançamento

**Formato:** `cancela: <id>`

**Resposta:** Confirmação com descrição e valor do lançamento removido + novo resumo do grupo afetado.

> O ID é exibido na resposta de confirmação de cada lançamento salvo (ex: `✅ Lançamento #42 salvo!`).
> Usuário usa `ultimos: N` para consultar IDs de lançamentos antigos.

## Alertas na Resposta de Lançamento

A resposta de confirmação de lançamento salvo exibe percentual do orçamento utilizado:
```
✅ Lançamento #42 salvo!
📂 Alimentação: R$ 185,00 gastos este mês
📊 Orçamento: R$ 300,00 | Gasto: R$ 185,00 | Restante: R$ 115,00 (61%)
⚠️ Atenção: 61% do orçamento utilizado
```
- Alerta `⚠️` quando >= 80% do orçamento
- Alerta `🚨 Orçamento estourado!` quando >= 100%
- Grupo sem orçamento: omite linha 📊 (comportamento atual)

## Jobs Agendados

### Job Diário — 06h00 BRT
Envia para o grupo WhatsApp o resumo de todos os gastos do dia anterior.
- Se nenhum gasto: "📭 Nenhum gasto registrado ontem."
- Se houver: lista com descrição, valor, grupo/subgrupo, cartão (se houver) + total do dia

### Job a cada 2 dias — 08h00 BRT
Envia para o grupo WhatsApp o resumo do mês corrente agrupado por grupo → subgrupo.
- Inclui percentual do orçamento e alertas ⚠️/🚨 quando aplicável

> Scheduler: APScheduler integrado ao FastAPI. Timezone: `America/Sao_Paulo`.

## Trigger e Frequência
- **Trigger principal:** Webhook da Evolution API (mensagem nova no grupo)
- **Frequência:** A cada mensagem no grupo
- **Jobs:** Diário 06h + a cada 2 dias 08h (APScheduler)
- **Volume estimado:** ~100 lançamentos/mês

## Dados a Persistir

**Tabela `grupos`:** id, nome (unique), orcamento_mensal (Decimal, default 0)

**Tabela `lancamentos`:** id, criado_em, data_gasto, descricao, valor, grupo_id (FK), subgrupo (not null), cartao, data_pagamento (not null — default = data_gasto quando não informado), hash_msg (unique, SHA-256 do texto original)

> Resumo mensal filtra por `data_pagamento`. Compra em cartão com pagamento em mês seguinte aparece no resumo do mês de pagamento.

## Fluxo Principal
1. Mensagem chega via webhook da Evolution API
2. Valida origem (grupo correto, não é o bot)
3. Detecta tipo: lançamento, comando de orçamento, ou desconhecido
4. Para lançamento: parseia → deduplica → salva → calcula resumo → responde
5. Para orçamento: parseia → salva/atualiza grupo → confirma
6. Para desconhecido: responde com ajuda

## Confiabilidade
- **Retry:** Não no MVP (Evolution API tem retry próprio)
- **Deduplicação:** Hash SHA-256 do texto original antes de salvar
- **Mensagem inválida:** Responde com formato esperado
- **Duplicata:** Silencioso (não responde)

## Monitoramento
- Logs stdout (Railway coleta automaticamente)
- Dashboard: Não no MVP
