FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN addgroup --system sportai && adduser --system --ingroup sportai sportai
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

USER sportai
EXPOSE 8000
CMD ["uvicorn", "bet_score.main:app", "--host", "0.0.0.0", "--port", "8000"]
