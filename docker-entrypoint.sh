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

# Updating Haystack search index. TODO: Check later if this is really required?
echo "Updating Haystack search index"
python manage.py update_index

# Start server
echo "Starting server"
python manage.py runserver 0.0.0.0:8000
