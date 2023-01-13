#! /usr/bin/env bash
set -e

python /app/app/celery/celeryworker_pre_start.py

celery worker -A app.celery.worker -l info -Q main-queue -c 1