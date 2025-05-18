#!/bin/sh

echo "Waiting for database..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done
echo "Database started"

echo "Applying migrations..."
python manage.py migrate

echo "Creating admin user if not exists..."
python manage.py create_admin

echo "Starting server..."
python manage.py runserver 0.0.0.0:8000 