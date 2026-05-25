# bot-finan — Vireum Spec Protocol

> Este projeto usa Spec Driven Development pela Vireum Desenvolvimento.
> Leia este arquivo completamente antes de qualquer ação.

## Início de cada sessão
1. Verifique se `.spec/INDEX.md` existe:
   - **Não existe** → execute o Modo 0 — Onboarding antes de qualquer coisa
   - **Existe** → leia o arquivo e continue normalmente
2. Verifique consistencia do spec:
   - tasks/active.md tem tasks sem criterios de aceitacao? → avisar o dev
   - architecture.md tem stack definida? → se nao, avisar
   - INDEX.md reflete o estado real do MVP? → se desatualizado, avisar
3. Se encontrar inconsistencias criticas → avisar antes de qualquer implementacao
4. Identifique o modo da sessão pela solicitação do dev
5. Carregue arquivos adicionais apenas se a task exigir

## Modos de operação

### Modo 0 — Onboarding (execute quando .spec/ não existe)
Acionado automaticamente quando `.spec/INDEX.md` não for encontrado.

Execute o skill `/vireum/onboarding` — ele contém o protocolo completo de análise.

Se o skill não estiver disponível, siga o protocolo manual:

**Fase 1 — Varredura de contexto existente**
Procure e leia todos os arquivos de configuração de IA que existirem no projeto:
- `CLAUDE.md`, `.claude/`, `.cursor/rules`, `.cursorrules`, `.windsurfrules`
- `.clinerules`, `.continue/config.json`, `.aider.conf.yml`
- `.github/copilot-instructions.md`, pastas `agents/`, `prompts/`, `.ai/`
Esses arquivos têm prioridade — extraia regras, convenções e contexto já documentados.

**Fase 2 — Leitura estrutural**
Leia: `README.md`, `package.json`, arquivos de schema (Prisma, Drizzle), `.env.example`,
`docker-compose.yml`, arquivos de entrada (`main.ts`, `server.ts`, `app.ts`).
Depois leia uma amostra representativa de rotas, services e models.

**Fase 3 — Síntese antes de gerar**
Antes de criar qualquer arquivo, escreva um resumo do que foi entendido.
Se houver ambiguidade em algo crítico, pergunte ao dev — uma pergunta precisa
vale mais do que dez suposições erradas no spec.

**Fase 4 — Gerar `.spec/`**
Gere os arquivos com conteúdo real inferido do código:
`briefing.md`, `requirements.md`, `architecture.md`, `users.md`,
`risks.md`, `rules.md`, `INDEX.md`, `changelog.md`,
`tasks/active.md`, `tasks/backlog.md`, `tasks/done.md`.

**Fase 5 — Comunicar**
Informe o dev: o que foi encontrado, o que foi assumido, o que ficou em aberto.

### Modo 1 — Implementar
Acionado por: "desenvolve", "implementa", "cria", + nome de task
1. Leia `.spec/tasks/active.md`
2. Leia `.spec/requirements.md` para contexto da feature
3. Consulte o Context7 para docs atualizadas da lib que vai usar
4. Se task de UI: leia `.spec/design.md` antes de qualquer componente
5. **Se Complexidade for "Complexa" e Status for "Aguardando breakdown":**
   - Proponha a divisão em sub-tasks com base no codebase atual
   - PARE e aguarde confirmação do dev
   - Só após aprovação: atualize o campo Sub-tasks em active.md e mude Status para "[ ] Não iniciada"
   - Nunca implemente task Complexa sem sub-tasks aprovadas
6. PLANEJAR: escreva o que sera implementado, quais arquivos serao tocados e riscos identificados
7. Confirme o plano com o dev antes de executar em tasks complexas
8. Implemente seguindo os critérios de aceitação da task
9. Somente quando TODOS os critérios de aceitação estiverem validados: marque como done, mova para `tasks/done.md`, atualize `INDEX.md` e registre em `changelog.md`. Sub-passos e commits intermediários não disparam isso.
10. Registre em `architecture.md` APENAS se: adicionou lib/dependência nova ao projeto, mudou um padrão existente (ex: REST → tRPC) ou tomou decisão estrutural significativa. Escolhas de implementação rotineiras não contam.

### Modo 2 — Bug
Acionado por: "erro", "bug", "quebrou", "não funciona"
1. PLANEJAR: descreva o que sera investigado e quais arquivos serao tocados
2. Crie hotfix em `tasks/active.md` com tag [H] e prioridade crítica
3. Identifique e resolva a causa raiz
4. Somente ao resolver: registre a causa raiz em `changelog.md` com data. Não registre investigações intermediárias.
5. Verifique se o bug afeta outras tasks em `tasks/active.md`

### Modo 3 — Nova demanda
Acionado por: "cliente pediu", "adiciona", "quero incluir" (fora do spec)
1. Verifique se já existe em `.spec/requirements.md`
2. Se não existir: crie task com tag [PENDING] em `tasks/backlog.md`
3. Informe o impacto estimado e aguarde decisão do dev
4. NUNCA implemente demanda nova sem aprovação explícita

### Modo 4 — Dúvida de escopo
Acionado por: "como deve funcionar", "o que foi combinado", "qual o comportamento"
1. Leia `.spec/requirements.md`
2. Responda com base no spec — não invente comportamento

## Context7 — Documentação atualizada
Sempre que for usar uma lib do projeto, consulte a documentação atualizada via Context7 antes de implementar.
Nunca assuma que você conhece a API mais recente — sempre verifique.
Libs deste projeto: Python + FastAPI, Prisma, Redis + BullMQ

## Arquivos de contexto disponíveis
- Escopo e features → leia `.spec/requirements.md`
- Decisoes tecnicas → leia `.spec/architecture.md`
- Perfis e permissoes → leia `.spec/users.md`
- Riscos → leia `.spec/risks.md`
- Tarefas ativas → leia `.spec/tasks/active.md`
- Historico → leia `.spec/changelog.md`
- Design e componentes → leia `.spec/design.md` antes de qualquer UI

## Regras globais
Leia `.vireum/rules.md` — aplicam-se a todas as sessões.

## Regras do projeto
Leia `.spec/rules.md` — regras específicas deste projeto.

## Stack
- Frontend: Nenhum
- Backend: Python + FastAPI
- Banco: PostgreSQL
- Auth: JWT + Refresh Token

## MCPs ativos
- context7
- github
- database
- docker

## Alertas
- Escopo creep: se a solicitação não está em requirements.md → PARAR e avisar
- Decisão de lib nova: registrar em architecture.md antes de usar
- Risco identificado: adicionar em risks.md antes de continuar
- UI sem consultar design.md → PARAR e consultar primeiro
- Spec inconsistente → avisar o dev antes de implementar
