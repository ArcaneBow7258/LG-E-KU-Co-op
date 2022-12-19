"""
Django settings for DashboardWebapp project.

Generated by 'django-admin startproject' using Django 3.1.6.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

import os

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ''

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
#https://stackoverflow.com/questions/68567653/do-i-have-to-switch-to-https-to-use-sharedarraybuffer-in-chrome-92
SECURE_CROSS_ORIGIN_OPENER_POLICY = None
ALLOWED_HOSTS = ['','','170.119.7.15']

#Max Data Send by Post - ALvin (default =2.5 MB) * 2
#DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440 * 2; 
#number of fields; default is (1000)Q
#DATA_UPLOAD_MAX_NUMBER_FIELDS = None;
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'DashboardWebappApp',

    # 'channels',
    # 'bootstrap4',

    # 'DashboardWebappApp.apps.DjangoPlotlyDashConfig',
    # 'dpd_static_support',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # 'whitenoise.middleware.WhiteNoiseMiddleware',
    # 'DashboardWebapp.middleware.BaseMiddleware',
    # 'DashboardWebapp.middleware.ExternalRedirectionMiddleware',
]
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

X_FRAME_OPTIONS = 'SAMEORIGIN'

ROOT_URLCONF = 'DashboardWebapp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'), os.getcwd() +'/downloadCSV'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'DashboardWebapp.wsgi.application'

ASGI_APPLICATION = 'DashboardWebappApp.routing.application'

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'

# To use home.html as default home page
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

# Define folder location of 'static' folder
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# 'DashboardWebappApp': django app name
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'DashboardWebappApp', 'static'),
    ]