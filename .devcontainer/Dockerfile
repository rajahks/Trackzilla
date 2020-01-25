FROM python:3
# MAINTAINER -> Fill this in later

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create workdir and set it as start dir
RUN mkdir /code
WORKDIR /code

ENV SHELL /bin/bash

# Run update and install all the requirements.
# install psycopg2 dependencies.
RUN apt-get update \
    && apt-get install -y postgresql postgresql-client

COPY requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy all our code into /code folder.
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
# sudo docker-compose build --build-arg USER_UID=`id -u` --build-arg USER_GID=`id -g` app

# ARG values can be passed via command line are can be passed via compose file.
# The args are setup in docker-compose.yml which inturn read it from the ".env" file
# run ./setupEnv.sh so that the env variables are setup.

ARG USERNAME=coder
# Or your actual UID, GID on Linux if not the default 1000
ARG USER_UID=1000
ARG USER_GID=1000

# Create the user 'coder' who has the same uid/gid as our user on host
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    #
    # [Optional] Add sudo support
    && apt-get update && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME


# ** Anything else you want to do like clean up goes here **

# Technically optional
ENV HOME /home/$USERNAME

# Set the default user
USER $USERNAME

# Commented out because we donot want our server started in the dev container.
# We would instead want to launch it using the debugger.
#CMD ["bash", "docker-entrypoint.sh"]