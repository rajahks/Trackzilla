#!/bin/bash

# Collect static files
echo "Collect static files"
python manage.py collectstatic --noinput

# Make database migrations
echo "Making database migrations"
python manage.py makemigrations

# Apply database migrations
echo "Apply database migrations"
python manage.py migrate

# Rebuilding Haystack search index. Remove entries which are not in DB
echo "Rebuilding Haystack search index"
python manage.py rebuild_index --noinput

# Start server
echo "Starting server"
python manage.py runserver 0.0.0.0:8000
