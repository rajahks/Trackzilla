FROM python:3
# MAINTAINER -> Fill this in later

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir /code
# Set work directory
WORKDIR /code

COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/

# create a user which will be used to run the applications
# done for security purpose. The app will be run with appUser instead of root
#RUN adduser -D appUser 
#USER appUser

CMD ["bash", "docker-entrypoint.sh"]