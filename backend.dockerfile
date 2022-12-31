FROM python:3.10

WORKDIR /app/
ENV PYTHONPATH=/app

RUN pip install poetry fastapi uvicorn gunicorn

# Install Poetry
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./app/pyproject.toml ./app/poetry.lock /app/

COPY ./gunicorn_conf.py ./start-server.sh  /
COPY ./app .
CMD [ "bash", "/start-server.sh" ]

