## Task Management Tool

- http://localhost:8000

### API Documentation:

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Useful Development Commands:

### Run the App in Development Mode

Launches the app using `Dockerfile.dev`, with development tools, testing tools and live reload enabled:

```bash
docker compose -f docker-compose.dev.yml up --build
```

## Testing and Code Quality

Run the following inside the dev container:

#### Run Tests with Pytest:
```bash
docker compose -f docker-compose.dev.yml run --rm fastapi pytest
```

#### Check static typing with mypy:
```bash
docker compose -f docker-compose.dev.yml run --rm fastapi mypy app/
```

#### Lint and auto-fixes common issues, then format the code, all using [Ruff](https://docs.astral.sh/ruff/):
```bash
docker compose -f docker-compose.dev.yml run --rm fastapi ruff check --fix app/ && ruff format .
```

## Run the App in Production Mode

### Builds and runs the app using the production Dockerfile (no reload, no dev tools).
```bash
docker compose up --build
```
