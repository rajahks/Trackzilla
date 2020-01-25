FROM python:3
# MAINTAINER -> Fill this in later

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir /code
# Set work directory
WORKDIR /code

# Run update and install all the requirements.
# install psycopg2 dependencies.
RUN apt-get update \
    && apt-get install -y postgresql postgresql-client

# Install packages from requirements.txt
COPY requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . /code/

# create a user which will be used to run the applications done for security purpose.

# In addition to security, this solves another problem of file ownership.
# Since we are using docker for development, any files created by using "docker-compose run" or 
# "docker-compose exec" Eg: "sudo docker exec app python manage.py startapp testApp" will create
# the testApp and all the files will be owned by root.
# One solution is to run "sudo chown $USER:$USER -R ." in the host machine and that should change
# the permissions of all files. Instead of that, the below steps attempt to create a user within
# docker having the same UID and GID as that of the host machine. This way all files created
# will be accessible from the host machine.
#
# By default creates with UID and GID of 1000. Override the value by running the below command
# in case your uid and gid are different.
# sudo docker-compose build --build-arg UID=`id -u` --build-arg GID=`id -g` app

# ARG values can be passed via command line are can be passed via compose file.
# The args are setup in docker-compose.yml which inturn read it from the ".env" file
# run ./setupEnv.sh so that the env variables are setup.

ARG UID=1000    
ARG GID=1000
#ARG user=dummy
#ARG group=dummyGroup

RUN groupadd -g ${UID} dummyGroup && \
    useradd -u ${UID} -g ${GID} dummy
USER dummy


CMD ["bash", "docker-entrypoint.sh"]