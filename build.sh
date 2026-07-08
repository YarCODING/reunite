#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate

python manage.py shell -c "
from django.contrib.auth import get_user_model; 
User = get_user_model(); 
import os;
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@reunite.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if password and not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print('=== SUPERUSER CREATED SUCCESSFULLY ===')
else:
    print('=== SUPERUSER ALREADY EXISTS OR NO PASSWORD PROVIDED ===')
"