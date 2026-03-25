# scripts/load_achats.py

import os
import django
import random
from faker import Faker
from decimal import Decimal
from uuid import uuid4
from datetime import timedelta

from core.models import Projet, Achat, LigneAchat, Materiel

fake = Faker("fr_FR")
random.seed(42)

# 1. Récupération des projets et des matériaux existants
projets = list(Projet.objects.all())
materiaux = list(Materiel.objects.all())

if not projets:
    raise Exception("❌ Aucun projet trouvé. Charge les projets d'abord.")
if not materiaux:
    raise Exception("❌ Aucun matériel trouvé. Charge les matériaux d'abord.")

modes_paiement = ["Espèces", "Virement", "Chèque"]

print(f"📦 Génération des achats pour {len(projets)} projets...")

for projet in projets:
    n_achats = random.randint(15, 25)
    for i in range(n_achats):
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

        lignes = random.sample(materiaux, k=random.randint(2, 5))
        total_ht = Decimal("0.00")

        for m in lignes:
            quantite = random.randint(2, 100)
            prix_unitaire = Decimal(random.randint(500, 25000))
            total_ligne = quantite * prix_unitaire
            total_ht += total_ligne

            LigneAchat.objects.create(
                achat=achat,
                materiel=m,
                quantite=quantite,
                prix_unitaire=prix_unitaire,
                commentaire=f"Utilisé pour {fake.word()}"
            )

        achat.total_ht = total_ht
        achat.total_tva = Decimal("0.18") * total_ht if tva_active else Decimal("0.00")
        achat.total_ttc = achat.total_ht + achat.total_tva
        achat.save()

print("✅ Tous les achats ont été générés avec succès.")
# scripts/load_achats.py

import os
import django
import random
from faker import Faker
from decimal import Decimal
from uuid import uuid4
from datetime import timedelta

from core.models import Projet, Achat, LigneAchat, Materiel

fake = Faker("fr_FR")
random.seed(42)

# 1. Récupération des projets et des matériaux existants
projets = list(Projet.objects.all())
materiaux = list(Materiel.objects.all())

if not projets:
    raise Exception("❌ Aucun projet trouvé. Charge les projets d'abord.")
if not materiaux:
    raise Exception("❌ Aucun matériel trouvé. Charge les matériaux d'abord.")

modes_paiement = ["Espèces", "Virement", "Chèque"]

print(f"📦 Génération des achats pour {len(projets)} projets...")

for projet in projets:
    n_achats = random.randint(15, 25)
    for i in range(n_achats):
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

        lignes = random.sample(materiaux, k=random.randint(2, 5))
        total_ht = Decimal("0.00")

        for m in lignes:
            quantite = random.randint(2, 100)
            prix_unitaire = Decimal(random.randint(500, 25000))
            total_ligne = quantite * prix_unitaire
            total_ht += total_ligne

            LigneAchat.objects.create(
                achat=achat,
                materiel=m,
                quantite=quantite,
                prix_unitaire=prix_unitaire,
                commentaire=f"Utilisé pour {fake.word()}"
            )

        achat.total_ht = total_ht
        achat.total_tva = Decimal("0.18") * total_ht if tva_active else Decimal("0.00")
        achat.total_ttc = achat.total_ht + achat.total_tva
        achat.save()

print("✅ Tous les achats ont été générés avec succès.")
#exec(open("scripts/load_achats.py", encoding="utf-8").read())
