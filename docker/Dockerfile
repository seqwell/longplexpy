FROM debian:bookworm-20240513-slim AS base

ENV LANG=C.UTF-8

RUN apt-get update \
    && apt upgrade --yes \
    && apt-get install -y --no-install-recommends \
        curl \
        python3.11-dev \
        python3.11-full \
        procps \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - --yes

ENV PATH="/root/.local/bin:$PATH"

ENV POETRY_VIRTUALENVS_CREATE=false

ARG POETRY_VERSION=1.8.4

RUN poetry self update ${POETRY_VERSION}

# Install longplexpy
ENV PATH="/opt/venv-longplexpy/bin:$PATH"

RUN python3 -m venv /opt/venv-longplexpy

COPY ./ /longplexpy

RUN . /opt/venv-longplexpy/bin/activate \
    && cd longplexpy \
    && poetry build \
    && pip install dist/*.whl

RUN ln -s /opt/venv-longplexpy/bin/longplexpy /bin/longplexpy
