#!/bin/bash
# Heroku release phase script
# Runs before new release is deployed

set -e

echo "Running database migrations..."
cd backend
python3 -m alembic upgrade head

echo "Release phase complete!"
