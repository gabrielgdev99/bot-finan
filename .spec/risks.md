# Risks — bot-finan

> Gerado automaticamente a partir do briefing em 25/05/2026

## Riscos Identificados no Briefing

### Técnico
Automação não idempotente — risco de duplicar dados em retry

### Jurídico
Nenhum identificado


### Operacional
Nenhum identificado

## Riscos Identificados Durante o Desenvolvimento
> A IA deve adicionar entradas aqui ao identificar novos riscos

| Data | Risco | Impacto | Mitigação |
|------|-------|---------|-----------|
| 25/05/2026 | Sessão WhatsApp (Baileys) perdida em restart do Railway | Bot para de responder até novo scan do QR | Filesystem efêmero é trade-off aceito no MVP — Railway free tier raramente reinicia sem deploy |
