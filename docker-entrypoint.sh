#!/bin/bash

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

echo "Waiting for elasticsearch..."
# Note: Using the service name "elasticsearch" and port "9200" defined in docker-compose 
# file. Ideally the depends-on in compose file should take care of this, but if we donot
# wait here, the haystack plugin seems to be connecting to elastic search and throws 
# errors like below.
# Starting new HTTP connection (15): elasticsearch:9200
# ConnectionRefusedError: [Errno 111] Connection refused

while ! nc -z elasticsearch 9200; do
  sleep 0.1
done
echo "Elasticsearch started."

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
