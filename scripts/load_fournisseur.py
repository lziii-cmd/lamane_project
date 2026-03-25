# scripts/load_demo_fournisseurs.py
# -*- coding: utf-8 -*-
"""
Script de génération de fournisseurs de démonstration.
Exécution :
    python manage.py shell < scripts/load_demo_fournisseurs.py
"""

import random
from django.utils import timezone
from django.apps import apps

Fournisseur = apps.get_model("core", "Fournisseur")

random.seed(42)

def rand_phone():
    return f"+221{random.randint(70,79)}{random.randint(1000000,9999999)}"

def rand_name():
    prenoms = ["Mamadou","Ibrahima","Cheikh","Abdoulaye","Moustapha",
               "Fatou","Awa","Aminata","Mareme","Khady","Ousmane","Adama"]
    noms = ["Diop","Ndiaye","Ba","Faye","Sow","Fall","Gueye","Camara","Sy","Diallo","Ndour"]
    return random.choice(prenoms), random.choice(noms)

def rand_company():
    prefixes = ["SENBAT", "ECOBAT", "MATPRO", "AFRICA", "GLOBAL"]
    suffixes = ["SARL", "SA", "Group", "Industries", "Matériaux"]
    return f"{random.choice(prefixes)} {random.choice(suffixes)}"

def rand_address():
    rues = ["Avenue Cheikh Anta Diop", "VDN", "Route de Rufisque", "Cité Keur Gorgui", "Point E"]
    villes = ["Dakar","Thiès","Saint-Louis","Mbour","Kaolack"]
    return f"{random.choice(rues)}, {random.randint(1, 300)} - {random.choice(villes)}"

def rand_identity():
    return f"CNI{random.randint(100000000, 999999999)}"

def rand_ninea():
    return f"{random.randint(1000000, 9999999)}-{random.randint(1,9)}"

def create_fournisseurs():
    fournisseurs = []

    # Entreprises
    for i in range(10):
        f = Fournisseur(
            est_moral=True,
            entreprise=rand_company(),
            ninea=rand_ninea(),
            telephone=rand_phone(),
            email=f"contact{i}@fournisseur.com",
            adresse=rand_address()
        )
        f.save()
        fournisseurs.append(f)

    # Personnes physiques
    for i in range(10):
        prenom, nom = rand_name()
        f = Fournisseur(
            est_moral=False,
            prenom=prenom,
            nom=nom,
            numero_identite=rand_identity(),
            sexe=random.choice(["H","F"]),
            telephone=rand_phone(),
            email=f"{prenom.lower()}.{nom.lower()}@example.com",
            adresse=rand_address()
        )
        f.save()
        fournisseurs.append(f)

    print(f"[OK] Fournisseurs créés : {len(fournisseurs)}")

if __name__ == "__main__":
    create_fournisseurs()
 
print("✅ 110 projets ajoutés à la base.")
