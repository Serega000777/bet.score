FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN addgroup --system betscore && adduser --system --ingroup betscore betscore
COPY backend/pyproject.toml backend/README.md ./
COPY backend/src ./src
COPY database ./database
RUN pip install --no-cache-dir .

USER betscore
EXPOSE 8000
CMD ["uvicorn", "bet_score.main:app", "--host", "0.0.0.0", "--port", "8000"]
