# Backend bet.score

FastAPI-приложение организовано по слоям domain, application, infrastructure и presentation.

```bash
python -m venv .venv
.venv/Scripts/activate
pip install -e ".[dev]"
uvicorn bet_score.main:app --reload
```

Проверки:

```bash
ruff check .
ruff format --check .
mypy src
pytest
```

