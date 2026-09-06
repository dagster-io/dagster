FROM python:3.13-slim AS builder

RUN pip install uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

FROM python:3.13-slim

COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app
