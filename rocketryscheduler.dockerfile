FROM python:3.10

WORKDIR /app/
ENV PYTHONPATH=/app/app/


# Install Poetry version 1
RUN pip install poetry fastapi uvicorn gunicorn
RUN poetry config virtualenvs.create false
# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./app/pyproject.toml ./app/poetry.lock* /app/
RUN poetry export -f requirements.txt --without-hashes --output /tour-core/requirements.txt
RUN pip install -r requirements.txt

# Install Poetry version 2
# RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
#     cd /usr/local/bin && \
#     ln -s /opt/poetry/bin/poetry && \
#     poetry config virtualenvs.create false

# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./app/pyproject.toml ./app/poetry.lock /app/

COPY ./app/ /app/
CMD ["python", "/app/app/utils/schedule.py"]
