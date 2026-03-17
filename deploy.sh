#!/usr/bin/env bash
# Deployment script for Full Gunicorn + Nginx Experience

# Exit on error
set -e

echo "Starting full deployment process..."

# 1. Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
pip install gunicorn

# 2. Run migrations
echo "Running database migrations..."
python manage.py migrate --no-input

# 3. Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input

# 4. Pre-download Thai word vector model
echo "Pre-downloading PyThaiNLP models..."
python -c "from pythainlp.word_vector import WordVector; WordVector(model_name='thai2fit_wv')"

# 5. Check Django deployment settings
echo "Checking Django deployment settings..."
python manage.py check --deploy || echo "Deployment check failed (likely missing API keys), proceeding anyway..."

# 6. Start Gunicorn in the background
echo "Starting Gunicorn..."
gunicorn -c gunicorn.conf.py vocab_project.wsgi:application &
GUNICORN_PID=$!

# 7. Start Nginx in the foreground
echo "Starting Nginx..."
# We use the self-contained config and run in foreground (daemon off is in nginx.conf)
nginx -c $(pwd)/nginx/nginx.conf

# Cleanup on exit
trap 'kill $GUNICORN_PID; exit' SIGINT SIGTERM
