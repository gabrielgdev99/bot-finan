# Tasks — Active

> Tarefas do MVP prontas para desenvolvimento.
> A IA só implementa tasks desta lista.
> Ao concluir uma task: marcar status, mover para done.md, atualizar INDEX.md

---

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
