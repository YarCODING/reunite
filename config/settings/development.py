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


STRIPE_PUBLIC_KEY = "pk_test_51TmyBCHHl6ggmM31TE57jvDpc6uxqv3kcPk5LD6bXkc6iEZQzC3WywMBL8jmWP3w6i7aUAX6qxyfq7iwA4KL6sE400vtwYnT0L"
STRIPE_SECRET_KEY = "sk_test_51TmyBCHHl6ggmM31RuIQsW5uIzqFmoAJq1mXewBGitlBQi6WZqPtAnyQlklLpnSzePps2lIkAFzEoL8ZVVYSwxFm00e3wAkVKf"
STRIPE_WEBHOOK_SECRET = "whsec_c9f75e944d2ebf2f0d629863c1935f41e833c2637153163721ba6ca3c3417d05"


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@reunite.com'
ADMIN_RECIPIENT_EMAIL = 'admin@reunite.com'