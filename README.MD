# Sistema de Continuidade Operacional

Estrutura inicial do backend em FastAPI, PostgreSQL, SQLAlchemy, Alembic e OR-Tools.

## Modulos

- `motor1`: previsao de risco e cobertura operacional.
- `motor2`: matchmaking e otimizacao de substitutos.
- `motor3`: lacunas de capacitacao e planejamento de treinamento.

## Execucao local

```bash
cp .env.example .env
uv sync --extra dev
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

A documentacao fica disponivel em `http://localhost:8000/docs`.

## Execucao com Docker

Para iniciar a API e o PostgreSQL, aplicando as migrations automaticamente:

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

Os dados do PostgreSQL permanecem no volume `postgres_data`. Para também remover os dados,
execute explicitamente `docker compose down --volumes`.

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
