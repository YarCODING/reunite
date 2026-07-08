from .base import *

DEBUG = True

BASE_URL = "http://localhost:8000"

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

SECRET_KEY = "django-insecure-wj+e88n4v5ax!$yjmm$arsg-$8@uhhrheegh17@@e3d!^*i8tg"

INSTALLED_APPS += ['django_browser_reload']
MIDDLEWARE += ['django_browser_reload.middleware.BrowserReloadMiddleware']

# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

MEDIA_ROOT = BASE_DIR / 'media'


STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@reunite.com'
ADMIN_RECIPIENT_EMAIL = 'admin@reunite.com'