#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Pre-download Thai word vector model to avoid issues during runtime
python -c "from pythainlp.word_vector import WordVector; WordVector(model_name='thai2fit_wv')"
