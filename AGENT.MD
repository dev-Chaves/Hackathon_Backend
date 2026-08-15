# Contexto do Projeto — Sistema de Continuidade Operacional

## Visão geral

Este repositório contém o backend de uma plataforma de continuidade operacional para
ambientes industriais. O sistema reduz impactos provocados por absenteísmo, afastamentos,
acidentes, férias, treinamentos e outras indisponibilidades de operadores em linhas de
produção.

A plataforma centraliza dados de colaboradores, equipes, áreas, linhas, postos, habilidades,
capacitações, ausências e alocações. A partir desses dados, fornece inteligência operacional
para que supervisores identifiquem riscos de cobertura e encontrem substitutos adequados para
funções críticas.

O objetivo final é transformar conhecimento operacional hoje concentrado nas lideranças em
informação estruturada, auditável e utilizável por mecanismos de análise e otimização.

## Problema de negócio

A ausência de um colaborador pode causar:

- redução de produtividade;
- parada ou redução de capacidade da linha;
- reorganização manual e tardia das equipes;
- dependência do conhecimento individual do supervisor;
- aumento do risco operacional e de segurança;
- alocação de pessoas sem a capacitação necessária;
- baixa visibilidade sobre cobertura de habilidades e certificações.

Em muitos ambientes industriais, a escolha de substitutos depende exclusivamente da
experiência das lideranças. Isso torna a decisão lenta, pouco rastreável e sujeita a erros.

## Objetivos do produto

- Mapear competências, certificações e capacitações dos colaboradores.
- Avaliar a cobertura operacional de equipes, linhas e postos.
- Identificar pessoas, funções e áreas críticas.
- Recomendar substitutos compatíveis com cada posto.
- Apoiar supervisores, PCP, RH e engenharia na tomada de decisão.
- Reduzir o impacto operacional de faltas e afastamentos.
- Identificar lacunas e prioridades de treinamento.
- Melhorar a resiliência e a continuidade da produção.

## Público-alvo

- Supervisores de produção.
- Líderes de equipe.
- PCP — Planejamento e Controle da Produção.
- Recursos Humanos.
- Engenharia de processos.
- Coordenação e gerência industrial.

## Escopo deste repositório

Este repositório contém somente o backend.

Tecnologias definidas:

- Python 3.12 ou superior;
- FastAPI para a API HTTP;
- PostgreSQL como banco de dados;
- SQLAlchemy 2 com acesso assíncrono;
- Alembic para migrations;
- OR-Tools para otimização e matchmaking;
- Pydantic Settings para configuração;
- pytest para testes;
- Ruff para lint e formatação.

O frontend é um projeto separado, previsto em Next.js, TypeScript e TailwindCSS.

## Arquitetura atual

```text
app/
├── core/                  # Configurações globais
├── database/              # Base ORM, engine e sessões
├── models/                # Entidades e enums compartilhados
├── modules/
│   ├── motor1/            # Risco e cobertura operacional
│   ├── motor2/            # Matchmaking de substitutos
│   └── motor3/            # Lacunas de capacitação
└── main.py                # Inicialização da aplicação e registro das rotas
migrations/                # Histórico de alterações do banco com Alembic
tests/                     # Testes automatizados
```

Os módulos devem encapsular suas regras de negócio. Configuração, persistência e entidades
compartilhadas permanecem nas camadas comuns. Evite introduzir dependências diretas entre os
motores; quando precisarem compartilhar comportamento, extraia uma abstração comum.

## Responsabilidade dos motores

### Motor 1 — Previsão de risco e cobertura operacional

Calcula e expõe indicadores de risco para colaboradores, equipes, linhas e áreas.

Entradas relevantes:

- histórico e frequência de ausências;
- distância da residência até o trabalho;
- tempo e tipo de deslocamento;
- turno de trabalho;
- disponibilidade atual da equipe;
- habilidades e níveis de capacitação;
- validade das capacitações;
- criticidade do colaborador e do posto;
- alocações atuais.

Saídas esperadas:

- score de risco por colaborador;
- score de risco por equipe;
- índice de cobertura por linha;
- taxa de absenteísmo;
- identificação de áreas, postos e funções críticas;
- estimativa de exposição da produção a indisponibilidades.

Uma composição inicial de referência para o risco individual é:

| Fator | Peso inicial |
|---|---:|
| Histórico de faltas | 35% |
| Distância de deslocamento | 15% |
| Tempo de deslocamento | 15% |
| Criticidade da função | 20% |
| Turno | 15% |

Esses pesos são parâmetros iniciais de negócio, não constantes definitivas. A implementação
deve permitir calibração futura e registrar a versão da regra usada em cada resultado.

Indicadores básicos:

- cobertura da equipe = funcionários disponíveis / funcionários planejados;
- taxa de absenteísmo = ausências consideradas / escalas ou jornadas planejadas;
- baixa cobertura ocorre quando poucos colaboradores válidos atendem integralmente aos
  requisitos de um posto.

Não invente dados de escalas para calcular indicadores. O modelo atual ainda não possui uma
entidade de escala ou calendário de trabalho; se ela for necessária, proponha e implemente uma
migration explícita.

### Motor 2 — Matchmaking operacional

Recomenda e ranqueia substitutos quando houver falta, acidente, afastamento, férias,
treinamento ou outra indisponibilidade.

Critérios mínimos:

- atendimento a todas as habilidades obrigatórias do posto;
- nível de proficiência igual ou superior ao mínimo exigido;
- capacitação ou certificação dentro da validade;
- status e disponibilidade atual do colaborador;
- ausência de conflito com outra alocação;
- experiência ou nível de habilidade;
- criticidade do posto;
- impacto de retirar o candidato de sua alocação atual.

Saídas esperadas:

- ranking de substitutos;
- percentual ou score explicável de compatibilidade;
- requisitos atendidos e não atendidos;
- impacto previsto na cobertura e na produção;
- justificativa da recomendação;
- indicação clara quando não existir substituto seguro.

Exemplo de resposta conceitual:

```text
Posto P101
1º Pedro — 98%
2º Lucas — 94%
3º Carlos — 89%
```

OR-Tools deve ser utilizado quando o problema envolver otimização conjunta de múltiplas
ausências, postos ou restrições. Um ranking simples e isolado pode usar uma função de score
determinística, desde que seja testável e explicável.

Uma recomendação nunca deve sugerir como apto um colaborador que não cumpra requisito
obrigatório de segurança ou cuja capacitação esteja vencida. Esses critérios são restrições,
não apenas penalizações de score.

### Motor 3 — Lacunas de capacitação

Analisa a matriz de habilidades e identifica fragilidades estruturais de cobertura.

Saídas esperadas:

- postos sem cobertura ou com apenas um operador apto;
- habilidades críticas com baixa disponibilidade;
- capacitações vencidas ou próximas do vencimento;
- pessoas prioritárias para treinamento;
- treinamentos com maior ganho potencial de cobertura;
- simulações de aumento de resiliência após capacitações.

O motor deve priorizar treinamento pelo ganho operacional esperado, considerando criticidade
do posto, número atual de pessoas aptas e impacto sobre linhas expostas.

## Domínio e modelo de dados

Entidades existentes:

- `Area`: setor de atuação, como Solda, Montagem, Qualidade, Logística ou Pintura.
- `Equipe`: grupo operacional ao qual colaboradores pertencem.
- `Funcionario`: cadastro, situação, turno, deslocamento e criticidade do colaborador.
- `HistoricoAusencia`: eventos de falta, atestado, acidente, férias, licença ou treinamento.
- `Habilidade`: competência existente na fábrica e sua criticidade.
- `FuncionarioHabilidade`: proficiência, última avaliação e validade da capacitação.
- `Linha`: linha produtiva vinculada a uma área e sua meta diária.
- `Posto`: posição de trabalho dentro de uma linha e sua criticidade.
- `PostoHabilidade`: habilidade e nível mínimo exigidos por um posto.
- `Alocacao`: vínculo temporal entre um colaborador e um posto.

Relacionamentos principais:

```text
Area
├── Linha
│   └── Posto
│       ├── PostoHabilidade ── Habilidade
│       └── Alocacao ───────── Funcionario
└── Funcionario
    ├── HistoricoAusencia
    ├── FuncionarioHabilidade ── Habilidade
    └── Alocacao

Equipe
└── Funcionario
```

Escala de criticidade:

- 1: baixa;
- 2: média;
- 3: alta;
- 4: muito alta;
- 5: crítica.

Escala de capacitação:

- 0: não capacitado;
- 1: em treinamento;
- 2: assistido;
- 3: operacional;
- 4: avançado;
- 5: especialista.

Status de funcionário:

- `ATIVO`;
- `FERIAS`;
- `AFASTADO`;
- `TREINAMENTO`;
- `DESLIGADO`.

Somente o status `ATIVO` deve ser presumido disponível, mas o status sozinho não prova
disponibilidade: ausências, turno, alocação e calendário também precisam ser considerados.

## Princípios de implementação

- Mantenha regras de negócio fora dos routers.
- Routers validam entrada, chamam serviços e traduzem resultados para contratos HTTP.
- Serviços dos motores coordenam regras de domínio e casos de uso.
- Acesso ao banco deve usar sessões assíncronas e consultas SQLAlchemy 2 tipadas.
- Use schemas Pydantic específicos para entrada e saída; não exponha entidades ORM diretamente.
- Scores devem ser determinísticos, explicáveis e acompanhados dos fatores que os compõem.
- Percentuais devem ter faixa e escala documentadas, preferencialmente de `0` a `100`.
- Datas e horários devem ser armazenados com semântica explícita; timestamps usam timezone.
- CPFs e outros dados pessoais não devem aparecer em logs, scores ou respostas sem necessidade.
- Toda mudança de schema deve incluir migration Alembic reversível.
- Não altere migrations já aplicadas; crie uma nova revisão.
- Use constraints no banco para invariantes estruturais e validação na aplicação para mensagens
  amigáveis.
- Não implemente recomendação que relaxe requisitos obrigatórios de segurança.
- Evite lógica escondida em propriedades ORM ou eventos de banco; regras relevantes devem ser
  fáceis de testar.

## Convenções da API

- Prefixo atual: `/api/v1`.
- Rotas dos motores: `/api/v1/motor1`, `/api/v1/motor2` e `/api/v1/motor3`.
- Health check global: `/health`.
- Use nomes de recursos consistentes e respostas estruturadas.
- Erros de validação de negócio devem explicar o motivo sem vazar informações sensíveis.
- Endpoints de cálculo devem informar a data de referência e, quando aplicável, a versão do
  algoritmo.
- Operações potencialmente demoradas de otimização devem ser desenhadas para futura execução
  assíncrona, sem antecipar infraestrutura que ainda não seja necessária.

## Testes e qualidade

Ao implementar funcionalidades:

- escreva testes unitários para fórmulas, filtros e restrições;
- escreva testes de integração para persistência e endpoints relevantes;
- cubra casos sem candidatos, capacitação vencida e conflito de alocação;
- valide limites das escalas de criticidade e proficiência;
- garanta que o ranking seja estável em caso de empate, usando um critério explícito;
- teste migrations em upgrade e downgrade quando houver mudança de schema;
- execute `ruff check .` e `pytest` antes da entrega, quando as dependências estiverem
  disponíveis.

## Configuração e comandos

Crie o arquivo de ambiente a partir do exemplo:

```bash
cp .env.example .env
```

Fluxo previsto com `uv`:

```bash
uv sync --extra dev
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
uv run ruff check .
uv run pytest
```

Não versionar `.env`, credenciais ou dados reais de colaboradores.

## Fora do escopo atual

- Implementação do frontend.
- Integração definitiva com sistemas de RH, ponto ou ERP.
- Autenticação e autorização corporativas.
- Inferência de disponibilidade sem dados de escala.
- Modelos preditivos treinados sem dataset validado.
- Decisões automáticas que removam a supervisão humana em situações de segurança.

Esses itens podem ser adicionados posteriormente, mas exigem decisões explícitas de produto,
segurança, privacidade e arquitetura.

## Resultado esperado

O backend deve evoluir para responder de forma confiável e explicável:

- Qual equipe possui maior risco operacional?
- Qual linha está mais exposta ao absenteísmo?
- Quem pode substituir determinado colaborador ou cobrir um posto?
- Quais postos possuem baixa cobertura?
- Quais habilidades precisam de treinamento adicional?
- Qual é o impacto previsto de uma ausência na operação?

Priorize sempre segurança operacional, rastreabilidade das recomendações e clareza para quem
toma a decisão na fábrica.
