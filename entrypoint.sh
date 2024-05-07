#!/bin/sh

# apply database migrations
python manage.py migrate --noinput

# collect static files
python manage.py collectstatic --noinput

# start gunicorn server
gunicorn iaroapp.wsgi:application --bind 0.0.0.0:8000
