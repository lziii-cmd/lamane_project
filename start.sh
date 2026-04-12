#!/usr/bin/env bash
set -o errexit

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

# Creer les lots et types d'elements metre si vides
python manage.py shell -c "
from core.models import LotMetre, TypeElement
if LotMetre.objects.count() == 0:
    lots_data = [
        ('GO', 'Gros oeuvre', 1), ('SO', 'Second oeuvre', 2), ('VRD', 'VRD', 3),
        ('CHARP', 'Charpente & Couverture', 4), ('ELEC', 'Electricite', 5), ('PLOMB', 'Plomberie', 6),
    ]
    lots = {}
    for code, nom, ordre in lots_data:
        lot = LotMetre.objects.create(code=code, nom=nom, ordre=ordre)
        lots[code] = lot
    types_data = [
        ('Mur porteur','GO','#E74C3C','ml','ligne',0.20,45000,1),
        ('Mur de cloture','GO','#C0392B','ml','ligne',0.15,35000,2),
        ('Cloison','SO','#3498DB','ml','ligne',0.10,25000,3),
        ('Poteau','GO','#E67E22','u','point',0,85000,4),
        ('Dalle','GO','#27AE60','m2','rectangle',0.15,35000,5),
        ('Fondation','GO','#8E44AD','ml','ligne',0.40,55000,6),
        ('Porte','SO','#F39C12','u','point',0,75000,7),
        ('Fenetre','SO','#1ABC9C','u','point',0,65000,8),
        ('Carrelage','SO','#2ECC71','m2','rectangle',0,12000,9),
        ('Enduit','SO','#95A5A6','m2','polygone',0.02,8000,10),
        ('Peinture','SO','#D35400','m2','polygone',0,3500,11),
        ('Tranchee VRD','VRD','#7F8C8D','ml','ligne',0.60,15000,12),
        ('Regard','VRD','#34495E','u','point',0,45000,13),
        ('Toiture','CHARP','#A93226','m2','polygone',0,18000,14),
    ]
    for nom,lc,coul,unite,outil,ep,prix,ordre in types_data:
        TypeElement.objects.create(nom=nom,lot=lots.get(lc),couleur=coul,unite=unite,outil=outil,epaisseur_defaut=ep,prix_unitaire=prix,ordre=ordre)
    print('Lots et types metre crees.')
else:
    print(f'Lots metre existent deja ({LotMetre.objects.count()}).')
"

gunicorn lamane.wsgi:application
