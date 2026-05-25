# Briefing — bot-finan

## 📌 1. Informações Gerais
- **Projeto:** bot-finan
- **Cliente:** Gabriel
- **Responsável:** 
- **Data da reunião:** 25/05/2026
- **Tipo:** Automação
- **Versão:** 1.0

## 🎯 2. Trigger e Contexto
- **O que faz:** Inputar lançamentos financeiros padronizados em uma database e enviar resumos de gastos
- **Processo atual (manual):** uma pessoa lança manual
- **Trigger:** Webhook
- **Frequência:** a cada mensagem nova no grupo
- **Volume por execução:** 100 registros por mes
- **Tempo de execução estimado:** Menos de 1 minuto
- **Prazo de entrega:** 2 dias

## 📥 3. Entrada e Saída de Dados
- **Fonte de dados:** API externa
- **Detalhe da fonte:** api da evolution api
- **Transformação:** trata e salva
- **Destino:** Banco de dados
- **Detalhe do destino:** salvar em um db na nuvem

## 🛡️ 4. Confiabilidade e Alertas
- Retry em caso de falha: Sim
- Alerta de falha: Sim
- Canal de alerta: whatsapp
- Notificação de sucesso: Não
- Idempotente: Não (cuidado com duplicatas)

## 📊 5. Monitoramento e Deploy
- Logs de execução: Não
- Dashboard de monitoramento: Não
- **Linguagem:** Python
- **Deploy:** A definir
- Custo operacional estimado: A definir
