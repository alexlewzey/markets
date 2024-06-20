FROM python:3.12-bullseye

WORKDIR /workspaces/setup

COPY .pre-commit-config.yaml pyproject.toml poetry.lock ./

RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install && \
    git init . && \
    pre-commit install --install-hooks