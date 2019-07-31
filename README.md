# Asseto
A simple online asset manager to manage assets within and across teams.  

Docker commands:

1) Starting django project  
	docker-compose run app sh -c "django-admin.py startproject asseto ."  
			OR  
	docker-compose run app django-admin.py startproject asseto .  

2) Running the application  
	docker-compose up  

3) Starting an App  
   All apps are to be placed within the app folder  
	docker-compose run app python manage.py startapp apps/<appname>	  

4) To list running docker images  
	docker ps  
