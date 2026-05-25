# Rules — Global Vireum

> Regras globais que se aplicam a TODOS os projetos Vireum.
> Nunca editar por projeto. Em conflito com .spec/rules.md, estas prevalecem.

## Regras de Escopo
- Nunca implementar funcionalidade fora do requirements.md sem criar task [PENDING]
- Nunca puxar task do backlog para active sem validação humana explícita
- Sempre avisar escopo creep antes de implementar — parar e perguntar

## Regras de Planejamento
- Sempre planejar antes de implementar — escrever o que sera feito e quais arquivos serao tocados
- Confirmar o plano com o dev em tasks complexas antes de executar
- Nunca comecar a escrever codigo sem ter um plano claro

## Regras de Design
- Sempre consultar .spec/design.md antes de criar ou modificar qualquer componente de UI
- Nunca hardcodar cores — usar sempre os tokens definidos em design.md
- Nunca misturar design systems

## Regras de Health
- Verificar consistencia do spec no inicio de cada sessao
- Avisar o dev sobre inconsistencias antes de qualquer implementacao
- Tasks sem criterios de aceitacao devem ser sinalizadas antes de implementar

## Regras de Spec
- Nunca marcar task como done sem validar os critérios de aceitação
- Registrar em architecture.md APENAS: lib/dependência nova adicionada, padrão alterado ou decisão estrutural significativa — não escolhas de implementação rotineiras
- Sempre definir contrato de interface antes de implementar features com frontend e backend
- Ao identificar risco novo, adicionar em risks.md antes de continuar

## Regras de Contexto
- Sempre ler INDEX.md no início de cada sessão
- Carregar outros arquivos de spec apenas quando a task exigir
- Registrar em changelog.md APENAS: task concluída (com todos critérios validados) ou bug resolvido (com causa raiz). Nunca durante passos intermediários.

## Regras de Tasks
- Bugs viram hotfix com tag [H] — nunca são tratados como tasks normais
- Demandas novas do cliente viram [PENDING] no backlog — nunca vão direto para active
- Task só é done quando critérios de aceitação estão validados

## Nunca
- Implementar sem ler o spec primeiro
- Implementar sem planejar primeiro
- Criar componente de UI sem consultar design.md
- Tomar decisão de lib ou stack sem documentar o porquê
- Responder dúvida de escopo sem consultar requirements.md
- Comunicar diretamente com o cliente — isso é papel do dev
