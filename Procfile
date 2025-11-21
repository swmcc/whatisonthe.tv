release: bash bin/release.sh
web: cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
worker: cd backend && celery -A app.workers.celery_app worker --loglevel=info
