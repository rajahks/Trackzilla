#!/bin/bash

#Setup the UID and GID

echo "USERID=`id -u`"   > .env    # > overwrites the old content
echo "GROUPID=`id -g`" >> .env    # >> appends to the file

# The UID and GID are to be set based on the machine.

# We need these other params as well which are used in docker compose file and django
# settings.py file. Adding there here itself so that they are also written into the env
# script.
# IMPORTANT: Change the values of SECRET_KEY and SQL_PASSWORD before running the container.

echo "DEBUG=1" >> .env

echo "SECRET_KEY=foo" >> .env

echo "DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]" >> .env

DATABASE=postgres
# DATABASE="sqllite"

# Database settings
if [ $DATABASE = "postgres" ]
then
    echo "DATABASE=postgres" >> .env
    echo "SQL_ENGINE=django.db.backends.postgresql" >> .env
    echo "SQL_DATABASE=trackzilla" >> .env
    echo "SQL_USER=trackzilla" >> .env
    echo "SQL_PASSWORD=trackzilla" >> .env
    echo "SQL_HOST=db" >> .env
    echo "SQL_PORT=5432" >> .env
else
    # Other values will be picked up as defaults in settings.py
    echo "DATABASE=sqllite" >> .env
fi