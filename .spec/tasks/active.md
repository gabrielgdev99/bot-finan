# Tasks — Active

> Tarefas do MVP prontas para desenvolvimento.
> A IA só implementa tasks desta lista.
> Ao concluir uma task: marcar status, mover para done.md, atualizar INDEX.md

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

