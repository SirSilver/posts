# syntax=docker/dockerfile:1.4

################################################################################
# Python base stage for images
################################################################################
FROM python:3.10-slim-bullseye as base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWIRTEBYTECODE=1 \
    PYSETUP_PATH=/opt/pysetup \
    APPLICATION_PATH=/usr/app \
    ENVIRONMENT=production
ENV VENV_PATH=$PYSETUP_PATH/.venv
ENV PATH=$VENV_PATH/bin:$PATH

RUN adduser --disabled-password posts \
    && mkdir $APPLICATION_PATH \
    && chown posts: $APPLICATION_PATH

COPY docker-entrypoint.sh /usr/local/bin
RUN chmod +x /usr/local/bin/docker-entrypoint.sh


################################################################################
# Dependency builder stage (build only production dependencies)
################################################################################
FROM base as builder

ENV POETRY_HOME=/opt/poetry/ \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=1.1.13
ENV PATH=$POETRY_HOME/bin:$PATH

WORKDIR $PYSETUP_PATH

RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get install --no-install-recommends -y curl

RUN curl -sSL https://install.python-poetry.org  | python

RUN python -m venv $VENV_PATH

COPY poetry.lock pyproject.toml ./

RUN --mount=type=cache,target=/root/.cache \
    . $VENV_PATH/bin/activate && poetry install --no-dev


################################################################################
# Development stage (for local development)
################################################################################
FROM base as development

ENV POETRY_HOME=/opt/poetry/ \
    POETRY_VIRTUALENVS_IN_PROJECT=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=1.1.13 \
    VIRTUAL_ENV=$VENV_PATH
ENV PATH=$POETRY_HOME/bin:$PATH

COPY --from=builder $POETRY_HOME $POETRY_HOME
COPY --from=builder $VENV_PATH $VENV_PATH

WORKDIR $APPLICATION_PATH

COPY poetry.lock pyproject.toml ./

RUN --mount=type=cache,target=/root/.cache \
    . $VENV_PATH/bin/activate && poetry install

COPY . .

RUN --mount=type=cache,target=/root/.cache \
    . $VENV_PATH/bin/activate && poetry install

USER posts

ENTRYPOINT ["docker-entrypoint.sh"]

CMD ["uvicorn", "web:create_app", "--host", "0.0.0.0", "--factory", "--reload"]


################################################################################
# Production stage (deployment ready)
################################################################################
FROM base as production

COPY --from=builder $PYSETUP_PATH $PYSETUP_PATH

WORKDIR $APPLICATION_PATH

COPY src/ ./

USER posts

ENTRYPOINT ["docker-entrypoint.sh"]

CMD ["uvicorn", "web:create_app", "--host", "0.0.0.0", "--factory"]
