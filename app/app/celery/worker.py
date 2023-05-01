from app.core.celery_app import celery_app


@celery_app.task(name="app.celery.worker.test_celery")
def test_celery(word: str) -> str:
    return f"test task return {word}"
