FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

RUN pip install uv

COPY pyproject.toml ./
RUN uv sync --no-dev

COPY . .

EXPOSE 3000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]