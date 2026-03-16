import random
from uuid import uuid4
from decimal import Decimal
from faker import Faker

from core.models import (
    Proprietaire,
    Projet,
    Employe,
    ProjetEmploye,
    Materiel,
    Achat,
    LigneAchat,
)

fake = Faker("fr_FR")
random.seed(42)

# 1. Créer 25 propriétaires (15 personnes physiques, 10 entreprises)
noms = ["Diop", "Sow", "Faye", "Ndoye", "Ba", "Sy", "Fall", "Gueye", "Diallo", "Kane"]
prenoms = ["Mamadou", "Awa", "Ousmane", "Fatou", "Ibrahima", "Astou", "Amadou", "Khady", "Aliou", "Ndeye"]

numero_identites_utilises = set()

for i in range(15):
    identite = f"CNI-{random.randint(100000, 999999)}-{uuid4().hex[:4]}"
    while identite in numero_identites_utilises:
        identite = f"CNI-{random.randint(100000, 999999)}-{uuid4().hex[:4]}"
    numero_identites_utilises.add(identite)

    Proprietaire.objects.create(
        est_moral=False,
        nom=random.choice(noms),
        prenom=random.choice(prenoms),
        sexe=random.choice(["H", "F"]),
        numero_identite=identite,
        telephone=f"77{random.randint(1000000, 9999999)}",
        email=fake.email(),
        adresse=f"Quartier {random.randint(1, 50)} Dakar"
    )

for i in range(10):
    Proprietaire.objects.create(
        est_moral=True,
        entreprise=f"Entreprise {fake.company()}",
        ninea=f"NINEA-{random.randint(1000000, 9999999)}",
        telephone=f"78{random.randint(1000000, 9999999)}",
        email=fake.company_email(),
        adresse=f"Zone Industrielle {random.randint(1, 20)}"
    )

proprietaires = list(Proprietaire.objects.all())

# 2. Créer 20 employés par métier
metiers = ["Maçon", "Électricien", "Plombier", "Menuisier", "Carreleur"]
for metier in metiers:
    for i in range(4):
        Employe.objects.create(
            prenom=random.choice(prenoms),
            nom=random.choice(noms),
            sexe=random.choice(["H", "F"]),
            metier=metier,
            telephone=f"76{random.randint(1000000, 9999999)}",
            adresse=f"Commune {random.randint(1, 30)}"
        )

employes = list(Employe.objects.all())

# 3. Créer 60 projets
types = ["Résidentiel", "Immeuble", "Villa", "Commerce", "Bureau"]
statuts = ["En cours", "En pause", "Terminé"]
projets = []

for i in range(60):
    p = Projet.objects.create(
        nom=f"Projet {fake.word().capitalize()}-{i}",
        localisation=fake.city(),
        type_projet=random.choice(types),
        statut=random.choice(statuts),
        date_debut=fake.date_between(start_date="-2y", end_date="today"),
        description=fake.sentence(),
        superficie=random.randint(150, 1000),
        surface_batie=random.randint(80, 600),
        nombre_pieces=random.randint(2, 10),
        nombre_etages=random.randint(1, 5),
        a_piscine=random.choice([True, False]),
        volume_piscine=random.randint(10, 50) if random.random() > 0.5 else None,
        a_ascenseur=random.choice([True, False]),
        nombre_ascenseurs=random.randint(1, 3) if random.random() > 0.5 else None,
        a_climatisation=random.choice([True, False]),
        nombre_clims=random.randint(1, 8) if random.random() > 0.5 else None,
        a_panneaux_solaires=random.choice([True, False]),
        puissance_panneaux=random.randint(1, 10) if random.random() > 0.5 else None,
        proprietaire=random.choice(proprietaires)
    )
    projets.append(p)

# 4. Affecter des employés à chaque projet
for projet in projets:
    affectes = random.sample(employes, k=random.randint(3, 6))
    for e in affectes:
        ProjetEmploye.objects.create(
            projet=projet,
            employe=e,
            fonction="Ouvrier",
            date_affectation=projet.date_debut,
            commentaires="Affectation initiale"
        )

# 5. Générer 5 à 12 achats par projet avec 2 à 4 lignes chacun
materiels = list(Materiel.objects.all())
if not materiels:
    raise Exception("⚠️ Aucun matériel trouvé. Lance d’abord load_materiels.py.")

modes_paiement = ["Espèces", "Virement", "Chèque"]

for projet in projets:
    for _ in range(random.randint(5, 12)):
        date_achat = fake.date_between(start_date=projet.date_debut, end_date="today")
        fournisseur = fake.company()
        mode = random.choice(modes_paiement)
        numero_facture = f"F-{date_achat.strftime('%Y%m%d')}-{random.randint(100,999)}"
        tva_active = random.choice([True, False])

        achat = Achat.objects.create(
            date_achat=date_achat,
            projet=projet,
            fournisseur=fournisseur,
            mode_paiement=mode,
            numero_facture=numero_facture,
            tva_active=tva_active
        )

        lignes = random.sample(materiels, k=random.randint(2, 4))
        total_ht = Decimal("0.00")
        for m in lignes:
            quantite = random.randint(5, 50)
            pu = Decimal(random.randint(1000, 15000))
            total_ligne = quantite * pu
            total_ht += total_ligne
            LigneAchat.objects.create(
                achat=achat,
                materiel=m,
                quantite=quantite,
                prix_unitaire=pu,
                commentaire=f"Utilisé pour {fake.word()}",
            )

        achat.total_ht = total_ht
        achat.total_tva = Decimal("0.18") * total_ht if tva_active else Decimal("0.00")
        achat.total_ttc = achat.total_ht + achat.total_tva
        achat.save()

print("✅ Données de démonstration chargées avec succès.")

