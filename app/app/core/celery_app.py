from celery import Celery

from app.core.config import settings


BROKER_URL = f"amqp://{settings.RABBITMQ_USERNAME}:{settings.RABBITMQ_PASSWORD}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}"
print(f"---------{BROKER_URL}-----")
celery_app = Celery("worker", backend="rpc://", broker=BROKER_URL)

celery_app.conf.task_routes = {"app.celery.worker.test_celery": "main-queue"}
celery_app.conf.update(task_track_started=True)
