# CLAUDE.md

## Planejamento

- Discutir requisitos e abordagem
- Identificar casos de teste
- Definir interface/contrato

## 2. Implementação (TDD)

1. Escrever teste que falha
2. Implementar código mínimo
3. Refatorar
4. Repetir para próximo requisito

## 3. Revisão

- Revisar código juntos
- Verificar cobertura de testes
- Validar contra requisitos

## 4. Integração

- Commitar com mensagem clara
- Executar suite completa de testes
- Documentar mudanças

## 🚨 Lidando com Erros

Quando eu (Claude) erro:

1. Me aponte o erro: Específico e construtivo
2. Explique o correto: Qual seria a abordagem certa
3. Peça correção: Peça para eu corrigir o código
4. Aprenda juntos: Use como oportunidade de ajustar meu entendimento

Padrões de erro comuns:

- Over-engineering: Muita complexidade desnecessária
- Under-testing: Cobertura insuficiente de testes
- Pattern mismatch: Usar padrão errado para o problema
- Assumption errors: Suposições incorretas sobre requisitos

## 📊 Métricas de Qualidade

Devemos monitorar:

- Cobertura de testes: > 80% para código crítico
- Complexidade ciclomática: < 10 por função
- Tamanho de funções: < 20 linhas por função
- Tempo de execução de testes: < 30 segundos total
- Debt técnico: Refatorar quando identificado

## 🤖 Como me instruir melhor

Frases que me ajudam:

- "Vamos fazer TDD para essa feature"
- "Qual seria a abordagem mais simples?"
- "Vamos refatorar isso primeiro"
- "Escreva um teste para esse cenário"
- "Isso está muito complexo, podemos simplificar?"

Coisas a evitar:

- "Faça o que achar melhor" (sem contexto)
- Implementações grandes de uma vez
- Pular a fase de testes
- Ignorar refatoração necessária
