#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python backend/manage.py migrate
python backend/manage.py collectstatic --no-input

# Crear superusuario admin si no existe
python backend/manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@viajaya.com', 'admin1234')
    print('Superusuario admin creado con éxito.')
"
