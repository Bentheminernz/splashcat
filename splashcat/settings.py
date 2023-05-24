"""
Django settings for splashcat project.

Generated by 'django-admin startproject' using Django 4.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""
import os
import sys
from pathlib import Path
from socket import gethostname, gethostbyname

import dj_database_url
import sentry_sdk
from django.conf import global_settings
from dotenv import load_dotenv
from sentry_sdk.integrations.django import DjangoIntegration

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

GITHUB_SPONSORS_WEBHOOK_TOKEN = os.environ.get('GITHUB_SPONSORS_WEBHOOK_TOKEN')
GITHUB_OAUTH_CLIENT_ID = os.environ.get('GITHUB_OAUTH_CLIENT_ID')
GITHUB_OAUTH_CLIENT_SECRET = os.environ.get('GITHUB_OAUTH_CLIENT_SECRET')
GITHUB_PERSONAL_ACCESS_TOKEN = os.environ.get('GITHUB_PERSONAL_ACCESS_TOKEN')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
ALLOWED_HOSTS += [gethostname(), gethostbyname(gethostname()), ]
CSRF_TRUSTED_ORIGINS = ['https://splashcat.ink']

SITE_ID = 1

INTERNAL_IPS = [
    '127.0.0.1',
]

# Application definition

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.sites',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django_celery_results',
    'django_celery_beat',
    'debug_toolbar',
    'django_htmx',
    'django_unicorn',
    'anymail',
    'battles',
    'users',
    'splatnet_assets',
    'notifications',
]

MIDDLEWARE = [
    'django_htmx.middleware.HtmxMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'splashcat.urls'

LOGIN_URL = 'users:login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
            ],
        },
    },
]

ASGI_APPLICATION = 'splashcat.asgi.application'
WSGI_APPLICATION = 'splashcat.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

database_url = os.environ.get("DATABASE_URL")

if database_url is None:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
elif len(sys.argv) > 0 and sys.argv[1] != 'collectstatic':
    DATABASES = {
        "default": dj_database_url.parse(database_url),
    }

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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

AUTHENTICATION_BACKENDS = [
    'splashcat.auth.AuthBackend'
]

AUTH_USER_MODEL = 'users.User'

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True
USE_L10N = True

USE_TZ = True

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

LANGUAGES = global_settings.LANGUAGES + [
    ('en-cat', 'Cat English'),
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

if not DEBUG:
    STORAGES = global_settings.STORAGES | {"default": {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"}}
AWS_S3_ACCESS_KEY_ID = os.environ.get('B2_ACCESS_KEY_ID')
AWS_S3_SECRET_ACCESS_KEY = os.environ.get('B2_SECRET_ACCESS_KEY')
AWS_S3_REGION_NAME = 'us-west-004'
AWS_S3_ENDPOINT_URL = 'https://s3.us-west-004.backblazeb2.com'
AWS_S3_CUSTOM_DOMAIN = 'cdn.splashcat.ink'
AWS_STORAGE_BUCKET_NAME = 'splashcat-assets'
AWS_QUERYSTRING_AUTH = False

B2_ENDPOINT_URL = 'https://s3.us-west-004.backblazeb2.com'
B2_ACCESS_KEY_ID = os.environ.get('B2_ACCESS_KEY_ID')
B2_SECRET_ACCESS_KEY = os.environ.get('B2_SECRET_ACCESS_KEY')

BUNNY_NET_DATA_EXPORTS_TOKEN = os.environ.get('BUNNY_NET_DATA_EXPORTS_TOKEN')
BUNNY_NET_DATA_EXPORTS_CDN_HOST = 'data-exports.splashcat.ink'

HCAPTCHA_SECRET_KEY = os.environ.get('HCAPTCHA_SECRET_KEY')

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

sentry_sdk.init(
    dsn='https://9babb5ac79274bed8e3c56a222b44ab6@o4505055559352320.ingest.sentry.io/4505055561449472',
    integrations=[
        DjangoIntegration(),
    ],

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,

    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True,
    profiles_sample_rate=1.0,
)

if DEBUG:
    sentry_sdk.init()  # when debugging locally don't send to sentry

# Celery

CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'default'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')

# Email

ANYMAIL = {
    'POSTMARK_SERVER_TOKEN': os.environ.get('POSTMARK_SERVER_TOKEN'),
}
EMAIL_BACKEND = 'anymail.backends.postmark.EmailBackend'
DEFAULT_FROM_EMAIL = 'grizzco@splashcat.ink'
SERVER_EMAIL = 'server@splashcat.ink'
