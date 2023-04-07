#! /usr/bin/env bash
set -e

python /app/app/celery/celeryworker_pre_start.py

celery -A app.celery.worker worker --loglevel=INFO -Q main-queue
