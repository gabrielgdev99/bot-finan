# MCPs — Global Vireum

> MCPs padrão disponíveis nos projetos Vireum.
> MCPs ativos por projeto estão em .spec/architecture.md

## Stack Padrão
- context7   — documentação atualizada das libs (sempre ativo)
- filesystem — leitura e escrita no projeto (nativo)
- github     — PRs, issues, branches referenciando tasks
- database   — validar schema e dados em desenvolvimento
- browser    — testar endpoints e validar fluxos
- puppeteer  — testes de jornada de UI
- docker     — gerenciar containers em desenvolvimento
- redis      — inspecionar cache e filas (quando aplicável)

## MCPs Ativos Neste Projeto
- context7
- github
- database
- docker

## Quando usar cada MCP
- Antes de usar qualquer lib → context7: buscar docs atualizadas
- Task concluída → github: criar PR referenciando a task
- Bug identificado → github: abrir issue com contexto
- Decisão de schema → database: validar antes de implementar
- Feature implementada → browser: testar endpoint ou fluxo
- Jornada de UI → puppeteer: validar fluxo completo
