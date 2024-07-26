#!/bin/sh

# apply database migrations
python manage.py migrate --noinput

# collect static files
python manage.py collectstatic --noinput

# copy default media files if they don't exist in the volume
if [ -d "/app/media" ]; then
  cp -rn /app/media/* /var/www/iaro-project/media/
fi

# start gunicorn server
gunicorn iaroapp.wsgi:application --bind 0.0.0.0:8000 --workers 5 --threads 2
