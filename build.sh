#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Créer un superuser si aucun n'existe
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@lamane.sn', 'lamane2024')
    print('Superuser admin créé.')
else:
    print('Superuser existe déjà.')
"
