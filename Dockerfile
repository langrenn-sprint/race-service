FROM python:3.11

RUN mkdir -p /app
WORKDIR /app

RUN pip install --upgrade pip
RUN pip install "poetry==1.4.1"
COPY poetry.lock pyproject.toml /app/

# Project initialization:
RUN poetry config virtualenvs.create false \
  && poetry install --no-dev --no-interaction --no-ansi

ADD race_service /app/race_service

EXPOSE 8080

CMD gunicorn "race_service:create_app"  --config=race_service/gunicorn_config.py --worker-class aiohttp.GunicornWebWorker
