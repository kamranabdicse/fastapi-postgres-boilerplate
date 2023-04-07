#! /usr/bin/env sh
set -e

########################
### run with uvicorn ###
########################
# exec uvicorn --reload --host 0.0.0.0 --port 80 --log-level info "app.main:app"

# Run migrations
alembic upgrade head


#########################
### run with gunicorn ###
#########################
export GUNICORN_CONF="/gunicorn_conf.py"
export WORKER_CLASS="uvicorn.workers.UvicornWorker"
export WORKERS_NUM=1
export APP_MODULE="app.main:app"
exec gunicorn -k "$WORKER_CLASS" -c "$GUNICORN_CONF" --workers $WORKERS_NUM $APP_MODULE
