# Asseto
A simple online asset manager to manage assets within and across teams.  

Docker commands:

1) Running the application
	sudo docker-compose up 

2) Running the application with force build
	sudo docker-compose up --build

3) Getting to the container shell
	sudo docker-compose exec app bash

	From this shell we can run all django commands such as 
		- python manage.py startapp apps/<appName>
		- python manage.py makemigrations
		- python manage.py migrate

4) To list running docker images  
	docker ps  

5) Stopping the container
	sudo docker stop <containerId>  # just few letters are enough.
	container id can be obtained from docker ps
		OR
	sudo docker-compose stop    # to stop all containers


6) Running commands within the container from Host

	Starting django project  
	docker-compose exec app sh -c "django-admin.py startproject asseto ."  
			OR  
	docker-compose exec app django-admin.py startproject asseto .  

 7) Creating Apps  IMPORTANT 

   All apps are to be placed within the app folder.
   Read the readme under apps folder.

	.) mkdir apps/<appName>
	.) docker-compose exec app python manage.py startapp <appName> apps/<appname>	  

				OR 
	Execute the same command from docker shell
	.) docker-compose exec app bash
	.) mkdir apps/<appName>
	.) python manage.py startapp <appName> apps/<appname>	  