FROM public.ecr.aws/lambda/python:3.12

COPY pyproject.toml poetry.lock ./

RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

COPY src ${LAMBDA_TASK_ROOT}

CMD ["markets.app.handler"]
