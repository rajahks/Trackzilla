"""
Django settings for asseto project.

Generated by 'django-admin startproject' using Django 2.2.3.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR,'templates')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'p@hut1!tboz^5af#2@%c1jfiajyuk!d7!+4%=#0k0q+k3$vs$n'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'apps.Organization',
    'apps.Users',
    'crispy_forms',
    'social_django',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites', # Sites framework
    'haystack', # to power our search
    'apps.Resource',
    'apps.ChangeHistory',
    # Apps required for mail
    'naomi', # Helps seeing the mail in browser
    'django_inlinecss', #Used to inline the css.
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.ChangeHistory.middleware.RequestMiddleware',
    'apps.Users.middleware.CurrentOrgMiddleware',
]

ROOT_URLCONF = 'asseto.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATES_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'asseto.wsgi.application'

# Letting Django know about the User model to use.
# When needing to refer to this User model either use
# 1) "from django.conf import settings" and then "settings.AUTH_USER_MODEL" will give the class name.
# 2) "from django.contrib.auth import get_user_model" and then
#     "User = get_user_model()". "User" now should have the model.
AUTH_USER_MODEL = 'Users.AssetUser'

# authentication backends for single sign on using social profiles
AUTHENTICATION_BACKENDS = (
    'social_core.backends.open_id.OpenIdAuth',  # for Google authentication
    'social_core.backends.google.GoogleOpenId',  # for Google authentication
    'social_core.backends.google.GoogleOAuth2',  # for Google authentication

    'django.contrib.auth.backends.ModelBackend',
)

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

# AUTH_PASSWORD_VALIDATORS = [
#     {
#         'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
#     },
# ]
# TODO: Not having any validators as of now as it enforces the user to have complex
# passwords. Enable this later once the app is a bit stable
AUTH_PASSWORD_VALIDATORS = []

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/
STATIC_ROOT = ''
STATIC_URL = '/static/'
STATICFILES_DIRS = ( os.path.join('static'), )

# Crispy forms by default use bootstrap 2. Suggesting here that they use bootstrap4 for styling.
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# Django by default tries to access a url /accounts/profile to which it tries to redirect a user when he logs in
# But we do not want to take a user to his profile ever when he logs in. We want to go to the landing page.
LOGIN_REDIRECT_URL = 'home'
LOGIN_URL = 'login'

# Google oauth ID and key
# TODO : add this as an env variable or something later
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY ='929102862935-fkigc7c93b98eo9chln2l3foci4bmlgp.apps.googleusercontent.com'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = 'NcvQb0ZFKy91G5CA0BK8h1TF'

# LOGGING configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {filename} {funcName} {lineno} {process:d} {thread:d} [ {message} ]',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'Logs/debug.log',
            'formatter' : 'verbose',
        },
        'console':{
            'level': 'DEBUG',  # Maybe change this to INFO later
            'class' : 'logging.StreamHandler',
            'formatter': 'simple',
        }
        # TODO: Add Sentry handler and redirect all logs for 'warning' and above to it
    },
    'loggers': {
        #root logger. Loggers from all files will use this.
        '': {
            'handlers': ['file', 'console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'), #Set the env for custom filtering. TODO: Change this to INFO later
            #'propagate': True,
        },
    },
}

#############################################################################################3
# Email settings
# Django provides us multiple email backends such as Console, SMTP, File etc.
# The Console backend will write the email to the console message, whereas the
# SMTP will send out a mail externally using SMTP protocol.
# For SMTP, the settings below are configured to use SendGrid service
# Sendgrid alllows 100 free email per day. We can change to gmail as well by providing similar settings.
# Sendgrid example: https://sendgrid.com/docs/for-developers/sending-email/django/
# TODO: Move the above example to documentation later.

# Uncomment the required backend.
# OUR_EMAIL_BACKEND = "console"
# OUR_EMAIL_BACKEND = "smtp"
OUR_EMAIL_BACKEND = "naomi"

if OUR_EMAIL_BACKEND == "console":
    # Console backend - Enable this during development so that the email is written to the console.
    print("EMAIL_BACKEND = Console")
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
elif OUR_EMAIL_BACKEND == "naomi":
    print("EMAIL_BACKEND = naomi")
    EMAIL_BACKEND = "naomi.mail.backends.naomi.NaomiBackend"
    EMAIL_FILE_PATH = "/code/tmp"
elif OUR_EMAIL_BACKEND == "smtp":
    # SMTP backend
    print("EMAIL_BACKEND = SMTP")
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.sendgrid.net'
    EMAIL_HOST_USER = 'apikey'
    #SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
    #EMAIL_HOST_PASSWORD = SENDGRID_API_KEY
    EMAIL_HOST_PASSWORD = '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' #TODO: Change this to read from env variable later.
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
else:
    print("EMAIL_BACKEND = None")

# Email address mentioned in 'From' when mails are sent.
EMAIL_FROM_ADDRESS = 'no-reply<no-reply@trackzilla.in'

######################################################################################
# Configure Search
# Using Haystack plugin with ElasticSearch 2.x backend

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch2_backend.Elasticsearch2SearchEngine',
        'URL': 'http://elasticsearch:9200/',
        'INDEX_NAME': 'haystack',
        'INCLUDE_SPELLING': True,
        'TIMEOUT' : 60,
    },
}

# Add the RealtimeSignalsProcessor so that the index is updated everytime new data is added.
# This should be ok for our application because the frequency with which new resources are
# added or updated would be quite low.
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'
######################################################################################
# Setting required by the django.contrib.sites package.
SITE_ID = 1
DOMAIN_NAME = '127.0.0.1:8000' #TODO: Change this the appropriate name later when hosting. 
DISPLAY_NAME = 'localhost'
######################################################################################
