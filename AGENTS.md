# bot-finan — Vireum Spec Protocol (Agentes)

> Protocolo completo e autossuficiente para agentes (Codex CLI, Gemini CLI, ou qualquer agente).
> Documento é **first-class** — não precisa ler CLAUDE.md.

---

## Início de cada sessão

1. Verifique se `.spec/INDEX.md` existe:
   - **Não existe** → execute o **Modo 0 — Onboarding** antes de qualquer coisa
   - **Existe** → leia o arquivo e continue normalmente
2. Verifique consistência:
   - `.spec/tasks/active.md` tem tasks sem critérios de aceitação? → avisar
   - `.spec/architecture.md` tem stack definida? → avisar se não
   - `.spec/INDEX.md` reflete estado real do MVP? → avisar se desatualizado
   - `.spec/requirements.md` tem funcionalidades mapeadas? → avisar se vago
3. Se encontrar inconsistências → avisar o desenvolvedor ANTES de qualquer implementação
4. Identifique o modo da sessão pela solicitação
5. **Carregue apenas os arquivos de spec que a task exigir**

---

## Modos de Operação

### Modo 0 — Onboarding (execute quando .spec/ não existe)

**Fase 1 — Contexto de IA existente**
Procure e leia todos os arquivos de configuração de IA presentes no projeto:
`CLAUDE.md`, `.claude/`, `.cursor/rules`, `.cursorrules`, `.windsurfrules`,
`.clinerules`, `.continue/config.json`, `.aider.conf.yml`,
`.github/copilot-instructions.md`, pastas `agents/`, `prompts/`, `.ai/`
Esses arquivos têm prioridade — o dev já documentou contexto neles.

**Fase 2 — Leitura estrutural**
Leia: `README.md`, `package.json`, schema (Prisma/Drizzle), `.env.example`,
`docker-compose.yml`, arquivos de entrada, rotas, services, models.

**Fase 3 — Síntese**
Escreva um resumo do que foi entendido antes de gerar qualquer arquivo.
Se houver ambiguidade em algo crítico, pergunte ao dev.

**Fase 4 — Gerar `.spec/`**
Gere os arquivos com conteúdo real inferido do código:
`briefing.md`, `requirements.md`, `architecture.md`, `users.md`,
`risks.md`, `rules.md`, `INDEX.md`, `changelog.md`,
`tasks/active.md`, `tasks/backlog.md`, `tasks/done.md`

**Fase 5 — Comunicar**
Informe o que foi encontrado, o que foi assumido e o que ficou em aberto.

### Modo 1 — Implementar Feature/Task
**Acionado por:** "desenvolve", "implementa", "cria", + nome de task ou feature

1. Leia `.spec/tasks/active.md` e identifique a task
2. Leia `.spec/requirements.md` para entender contexto da feature
3. Consulte **Context7** para documentação ATUALIZADA da lib que vai usar
   - Nunca assuma que conhece a API mais recente
4. **SE TASK FOR UI:** leia `.spec/design.md` ANTES de escrever qualquer componente
5. **SE Complexidade for "Complexa" e Status for "Aguardando breakdown":**
   - Analise o codebase atual e proponha a divisão em sub-tasks
   - **PARE. Aguarde confirmação do dev.**
   - Só após aprovação: atualize o campo Sub-tasks em active.md e mude Status para "[ ] Não iniciada"
   - **Nunca implemente task Complexa sem sub-tasks aprovadas pelo dev**
6. **PLANEJAR:** escreva o que será implementado, quais arquivos serão tocados, riscos identificados
7. Implemente rigorosamente segundo os **critérios de aceitação** da task
8. **Somente quando TODOS os critérios de aceitação estiverem validados:**
   - Marque task como done
   - Mova para `.spec/tasks/done.md`
   - Atualize `.spec/INDEX.md`
   - Registre em `.spec/changelog.md` com data
   Sub-passos, commits intermediários e refactors parciais **não disparam** nenhum desses passos.
9. Registre em `.spec/architecture.md` **somente se** adicionou lib/dependência nova ao projeto, mudou um padrão existente (ex: REST → tRPC, fetch → axios) ou tomou decisão estrutural significativa. Escolhas de implementação rotineiras (como qual função usar, como nomear variável) **não contam**.

### Modo 2 — Bug / Fix Crítico
**Acionado por:** "erro", "bug", "quebrou", "não funciona", "falha"

1. **PLANEJAR:** descreva o que será investigado, quais arquivos serão analisados
2. Crie hotfix em `.spec/tasks/active.md` com tag **[H]** e prioridade crítica
3. Identifique causa raiz (não apenas sintoma)
4. **Somente ao resolver:** registre a causa raiz em `.spec/changelog.md` com data. Não registre hipóteses, investigações intermediárias ou tentativas.
5. Verifique se o bug afeta outras tasks em `.spec/tasks/active.md`

### Modo 3 — Nova Demanda do Cliente
**Acionado por:** "cliente pediu", "adiciona", "quero incluir", "pode fazer"

1. Verifique se já existe em `.spec/requirements.md`
2. Se não existir: crie task com tag **[PENDING]** em `.spec/tasks/backlog.md`
3. Descreva o impacto estimado (esforço, risco, dependências)
4. **NUNCA implemente demanda nova sem aprovação explícita do dev**

### Modo 4 — Dúvida de Escopo / Comportamento
**Acionado por:** "como deve funcionar", "qual comportamento foi combinado", "o que faz isso"

1. Consulte `.spec/requirements.md` — lá está o comportamento esperado
2. Responda **com base no spec** — não invente comportamento
3. Se spec estiver vago: peça ao dev para clarificar em requirements.md

---

## Context7 — Documentação Atualizada

Quando for usar qualquer lib do projeto:
1. Consulte **Context7** ANTES de implementar
2. Nunca assuma que conhece a versão/API mais recente
3. Libs deste projeto: Python + FastAPI, Prisma, Redis + BullMQ

---

## Stack Completo do Projeto

### Frontend
- Framework: Nenhum

### Backend
- Framework: Python + FastAPI

### Banco de Dados
- BD: PostgreSQL
- ORM: Prisma

### Cache / Filas
- Redis + BullMQ

### Autenticação
- JWT + Refresh Token

### Infraestrutura
- Hospedagem: Outro
- Containerização: Docker + Docker Compose
- CI/CD: GitHub Actions

---

## MCPs Ativos Neste Projeto

- **context7** — usar para tarefas relacionadas
- **github** — usar para tarefas relacionadas
- **database** — usar para tarefas relacionadas
- **docker** — usar para tarefas relacionadas

**Quando usar cada MCP:**
- Antes de usar qualquer lib → **context7:** buscar docs atualizadas
- Task concluída → **github:** criar PR referenciando a task
- Bug identificado → **github:** abrir issue com contexto
- Decisão de schema → **database:** validar antes de implementar
- Feature implementada → **browser:** testar endpoint ou fluxo
- Jornada de UI → **puppeteer:** validar fluxo completo

---

## Arquivos de Spec — Mapa Completo

| Arquivo | Propósito | Quando Ler |
|---------|-----------|-----------|
| `.spec/INDEX.md` | Estado atual, tasks ativas mapeadas | SEMPRE no início de sessão |
| `.spec/requirements.md` | Escopo completo, features MVP, Fase 2 | Antes de implementar feature |
| `.spec/architecture.md` | Decisões técnicas, stack, MCPs | Antes de tomar decisão arquitetural |
| `.spec/users.md` | Perfis de usuário, permissões, jornadas | Se task envolver acesso/permissões |
| `.spec/risks.md` | Riscos técnicos, compliance, mitigações | Ao identificar risco novo |
| `.spec/tasks/active.md` | Tasks em progresso, critérios de aceitação | Quando vai implementar |
| `.spec/tasks/backlog.md` | Demandas futuras, [PENDING], ideias | Quando cliente pede feature nova |
| `.spec/tasks/done.md` | Funcionalidades já entregues | Raramente — histórico |
| `.spec/changelog.md` | Histórico de decisões e causa raiz de bugs | Ao investigar ou documentar decisão |
| `.spec/rules.md` | Regras específicas DO PROJETO | Se task envolver lógica especial |
| `.spec/design.md` | Design system, cores, fontes, componentes | SEMPRE antes de criar UI |
| `.vireum/rules.md` | Regras globais do Vireum Framework | Referência — aplicam-se a tudo |

---

## Planejamento Obrigatório (Resumo)

Antes de QUALQUER implementação, você deve:

1. **Escrever o plano:**
   - O que será feito (resumo)
   - Quais arquivos serão tocados
   - Quais riscos foram identificados
   - Dependências externas (bibliotecas, APIs, etc)

2. **Validar com o desenvolvedor** (em tasks complexas)
   - Mostrar plano antes de começar
   - Aguardar feedback/aprovação

3. **Implementar seguindo o plano**
   - Não saia do escopo da task
   - Registre decisões em architecture.md
   - Use os tokens de design.md (se UI)

4. **Validar antes de marcar como done**
   - Todos os critérios de aceitação foram atendidos?
   - Testes passam?
   - Sem regressões em outras features?

---

## Regras Globais — Vireum Framework

## Regras Globais (Vireum Framework)

**Regras de Escopo**
- Nunca implementar funcionalidade fora do requirements.md sem criar task [PENDING]
- Nunca puxar task do backlog para active sem validação humana
- Sempre avisar escopo creep antes de implementar

**Regras de Planejamento**
- SEMPRE planejar antes de implementar — escrever o que será feito, quais arquivos serão tocados
- Confirmar o plano com o dev em tasks complexas antes de executar
- Nunca começar código sem plano claro

**Regras de Design**
- SEMPRE consultar design.md antes de criar ou modificar qualquer componente UI
- Nunca hardcodar cores/fontes — usar sempre os tokens definidos
- Nunca misturar design systems

**Regras de Spec**
- Nunca marcar task como done sem validar critérios de aceitação
- Registrar em architecture.md APENAS: lib/dependência nova adicionada, padrão alterado ou decisão estrutural significativa — não escolhas de implementação rotineiras
- Sempre definir contrato de interface antes de implementar features frontend+backend
- Ao identificar risco novo, adicionar em risks.md antes de continuar

**Regras de Contexto**
- SEMPRE ler INDEX.md no início de cada sessão
- Carregar outros arquivos de spec apenas quando a task exigir
- Registrar em changelog.md APENAS: task concluída (todos critérios validados) ou bug resolvido (causa raiz confirmada). Nunca durante passos intermediários.

**Regras de Tasks**
- Bugs viram hotfix [H] — nunca tasks normais
- Demandas novas do cliente viram [PENDING] em backlog — nunca vão direto para active
- Task só é done quando critérios validados

**Nunca**
- Implementar sem ler spec primeiro
- Implementar sem planejar
- Criar UI sem consultar design.md
- Tomar decisão de lib/stack sem documentar
- Comunicar com cliente — isso é papel do dev

---

## Resumo Rápido

- **Pense antes de agir:** planejar é metade do trabalho
- **Leia o spec:** sempre há resposta documentada antes de você perguntar
- **Consulte Context7:** doc atualizada antes de assumir conhecimento
- **Respeite design.md:** nunca hardcode cores ou componentes
- **Registre decisões:** não é "óbvio" para o próximo — documenta
- **Valide critérios:** task só é done quando TUDO foi testado
- **Comunique com dev:** você não fala com cliente, dev fala

---

## Stack Resumido para Referência Rápida

**Stack:** Python + FastAPI + PostgreSQL + Prisma + JWT + Refresh Token

**Design:** none

**MCPs:** context7, github, database (+ 1 mais)

---

*Documento gerado por Vireum Spec. Última atualização: setup.*
