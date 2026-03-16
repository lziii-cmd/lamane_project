from core.models import Projet, Proprietaire, TypeProjet
from faker import Faker
import random

fake = Faker("fr_FR")
random.seed(42)

# Récupération des objets
noms_projets = [
    "Résidence Diallo", "Villa Horizon", "Immeuble Mermoz", "Projet Liberté",
    "Soleil Levant", "Résidence Khadija", "Résidence Faye", "Résidence Baobab",
    "Projet Renaissance", "Résidence Sahel", "Résidence Touba", "Résidence Niang",
    "Résidence Diouf", "Résidence Soleil", "Résidence Avenir", "Résidence Téranga",
    "Résidence Amitié", "Résidence Sérénité", "Villa Espoir", "Villa Diamono",
    "Projet Baye Laye", "Résidence Keur Gorgui", "Résidence Renaissance", "Résidence Almadies",
    "Résidence Liberté 6", "Résidence Cité Mixta", "Résidence Océan", "Résidence Dakar Plateau",
    "Projet Cité Gadaye", "Résidence Fass Mbao", "Résidence Ngor", "Projet Rufisque",
    "Résidence Wakhinane", "Résidence Pikine", "Projet Grand Médine", "Projet Keur Massar",
    "Projet HLM Grand Yoff", "Projet Diamaguène", "Projet Cambérène", "Résidence Yeumbeul",
    "Projet Technopole", "Résidence Thiès", "Projet Bargny", "Projet Sangalkam",
    "Résidence Diourbel", "Projet Saint-Louis", "Résidence Fatick", "Projet Kaolack",
    "Résidence Kaffrine", "Résidence Louga", "Projet Matam", "Projet Kédougou",
    "Résidence Tambacounda", "Projet Sédhiou", "Résidence Ziguinchor", "Projet Kolda",
    "Projet Parcelles Nord", "Projet Parcelles Sud", "Projet Mbao 2", "Résidence Malika",
    "Résidence Hann Maristes", "Projet Ouakam", "Projet Zone B", "Résidence Colobane",
    "Projet Dalifort", "Résidence Derklé", "Projet HLM Fass", "Projet Yoff",
    "Projet Niayes", "Projet Djily Mbaye", "Projet Sacré-Cœur 3", "Projet Camberène",
    "Résidence Cité Avion", "Projet Cité Port", "Projet Bel-Air", "Projet Sicap Baobab",
    "Projet SICAP Mermoz", "Projet Nord Foire", "Projet Patte d’Oie", "Projet Castors",
    "Projet Cité Keur Gorgui", "Projet Tivaouane", "Projet Rufisque Est", "Projet Bambilor",
    "Projet Ngor Extension", "Projet Dakar Plateau 2", "Projet Thiaroye", "Projet Guédiawaye",
    "Projet Golf Sud", "Projet Grand Yoff 2", "Projet Cambérène 2", "Projet Pikine Est",
    "Projet Mermoz Sacré Cœur", "Projet Zone A", "Projet Grand Dakar", "Projet Derklé 2",
    "Projet Fann", "Projet Ouakam Extension", "Projet Cité Biagui", "Projet Technopole 2",
    "Projet Hann Marinas", "Projet Aéroport", "Projet Cité Avion 2", "Projet Foire",
    "Projet Cité Damel", "Projet Dalifort Nord", "Projet Yoff Layène", "Projet SICAP Amitié",
    "Projet Liberté 1", "Projet Liberté 2", "Projet Liberté 5", "Projet Liberté 6 Extension",
    "Projet Almadies 2", "Projet Virage", "Projet Mamelles"
]

proprietaires = list(Proprietaire.objects.all())
types_projet = list(TypeProjet.objects.all())

# Création des projets
for i in range(110):
    Projet.objects.create(
        nom=noms_projets[i],
        localisation=fake.city(),
        type_projet=random.choice(types_projet),
        statut=random.choice(["En cours", "En pause", "Terminé"]),
        date_debut=fake.date_between(start_date="-3y", end_date="today"),
        description=fake.sentence(),
        superficie=random.randint(200, 1000),
        surface_batie=random.randint(100, 800),
        nombre_pieces=random.randint(2, 12),
        nombre_etages=random.randint(1, 5),
        a_piscine=random.choice([True, False]),
        volume_piscine=random.randint(10, 50) if random.random() > 0.7 else None,
        a_ascenseur=random.choice([True, False]),
        nombre_ascenseurs=random.randint(1, 3) if random.random() > 0.6 else None,
        a_climatisation=random.choice([True, False]),
        nombre_clims=random.randint(1, 8) if random.random() > 0.6 else None,
        a_panneaux_solaires=random.choice([True, False]),
        puissance_panneaux=random.randint(1, 10) if random.random() > 0.6 else None,
        proprietaire=random.choice(proprietaires),
    )

print("✅ 110 projets ajoutés à la base.")


#exec(open("scripts/load_projets.py", encoding="utf-8").read())
