# Digital Mohalla API image: FastAPI app plus its Alembic migrations.
# Render builds it from this folder (see render.yaml). To build and run it locally:
#   docker build -t dm-api backend
#   docker run --rm -p 8000:8000 --env-file backend/.env dm-api
# (inside a container, "localhost" is the container itself: use host.docker.internal for a database on your PC)
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Dependencies first, so this layer is reused until uv.lock changes. Exactly the locked versions, no dev tools.
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev --no-install-project

COPY . .

# run as an unprivileged user, not root
RUN useradd --create-home --uid 10001 app
USER app

# Render sets PORT; 8000 is the local default
ENV PORT=8000
EXPOSE 8000

# Apply any new migrations (Alembic skips ones already applied), then start the API.
# If a migration fails the container exits, the deploy fails and Render keeps the previous version live.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port \"$PORT\""]
