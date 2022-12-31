FROM python3.10
RUN pip install poetry && poetry config virtualenvs.create false
WORKDIR /app/app
COPY ./pyproject.toml ./poetry.lock /app/
RUN poetry install
COPY ./app /app/app/
CMD ["python", "/app/app/utils/schedule.py"]
