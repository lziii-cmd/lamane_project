#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Charger les données initiales si la base est vide
python manage.py shell -c "
from core.models import Projet
if Projet.objects.count() == 0:
    import subprocess
    subprocess.run(['python', 'manage.py', 'loaddata', 'core/fixtures/initial_data.json'], check=True)
    print('Donnees initiales chargees (3 projets).')
else:
    print(f'Base deja peuplee ({Projet.objects.count()} projets).')
"

# Créer un superuser si aucun n'existe
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@lamane.sn', 'lamane2024')
    print('Superuser admin cree.')
else:
    print('Superuser existe deja.')
"
