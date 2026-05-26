# Tasks — Active

> Tarefas do MVP prontas para desenvolvimento.
> A IA só implementa tasks desta lista.
> Ao concluir uma task: marcar status, mover para done.md, atualizar INDEX.md

---

## MULTI-T001 — Lançamento múltiplo numa mensagem

**Épico:** Inteligência do Parser
**Prioridade:** Média
**Complexidade:** Média
**Status:** [x] Concluída
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

