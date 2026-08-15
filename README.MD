# Sistema de Continuidade Operacional

Estrutura inicial do backend em FastAPI, PostgreSQL, SQLAlchemy, Alembic e OR-Tools.

## Modulos

- `motor1`: previsao de risco e cobertura operacional.
- `motor2`: matchmaking e otimizacao de substitutos.
- `motor3`: lacunas de capacitacao e planejamento de treinamento.

## Execucao local

Copie a connection string do Neon para `DATABASE_URL` no arquivo `.env`. A URL pode ser
copiada diretamente do painel; a aplicacao normaliza URLs iniciadas por `postgresql://` para
o driver `psycopg`. Mantenha `sslmode=require`.

```bash
cp .env.example .env
uv sync --extra dev
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

A documentacao fica disponivel em `http://localhost:8000/docs`.

## Execucao com Docker

O Compose inicia somente a API e usa o banco remoto configurado no `.env`. As migrations sao
aplicadas no Neon automaticamente antes da inicializacao da API:

```bash
docker compose up --build
```

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

Para encerrar os containers:

```bash
docker compose down
```

## Dados ficticios de demonstracao

A migration `20260815_0002` cria uma massa deterministica de uma montadora ficticia chamada
Nissa Motors, incluindo 3.000 colaboradores e dados relacionados para os tres motores. Ela e
aplicada automaticamente no `docker compose up` ou manualmente com:

```bash
uv run alembic upgrade head
```

Para conferir o espaco ocupado no PostgreSQL:

```sql
SELECT pg_size_pretty(pg_database_size(current_database()));
```

Os nomes, matriculas e CPFs dessa massa sao artificiais e nao devem ser tratados como dados
reais.

## Estrutura

```text
app/
  core/           # configuracao
  database/       # engine, sessao e base ORM
  models/         # entidades e enums compartilhados
  modules/
    motor1/
    motor2/
    motor3/
migrations/       # migrations Alembic
tests/
```
