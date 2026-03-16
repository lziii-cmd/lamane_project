# scripts/load_proprietaires.py


import random
from faker import Faker
from uuid import uuid4
from core.models import Proprietaire

fake = Faker("fr_FR")
random.seed(42)

# Nettoyage (optionnel, attention si données réelles)
# Proprietaire.objects.all().delete()

prenoms_hommes = ["Mamadou", "Ibrahima", "Ousmane", "Cheikh", "Amadou", "Aliou", "Abdou", "Pape", "Elhadji", "Serigne"]
prenoms_femmes = ["Awa", "Fatou", "Ndeye", "Astou", "Khady", "Mame", "Sokhna", "Aminata", "Bineta", "Adja", "Dieynaba", "Mbayang", "Coumba", "Mariama", "Yacine"]
noms_senegalais = ["Diop", "Sow", "Faye", "Ndoye", "Ba", "Sy", "Fall", "Gueye", "Diallo", "Kane"]

used_emails = set()
used_identites = set()

def generate_email(prenom, nom):
    base = f"{prenom.lower()}.{nom.lower()}@email.com"
    email = base
    counter = 1
    while email in used_emails:
        email = f"{prenom.lower()}.{nom.lower()}{counter}@email.com"
        counter += 1
    used_emails.add(email)
    return email

def generate_cni():
    while True:
        numero = f"CNI-{random.randint(100000, 999999)}-{uuid4().hex[:3]}"
        if numero not in used_identites:
            used_identites.add(numero)
            return numero

# 📌 1. Propriétaires physiques (10 hommes)
for _ in range(10):
    prenom = random.choice(prenoms_hommes)
    nom = random.choice(noms_senegalais)
    Proprietaire.objects.create(
        est_moral=False,
        prenom=prenom,
        nom=nom,
        sexe="H",
        numero_identite=generate_cni(),
        telephone=f"77{random.randint(1000000, 9999999)}",
        email=generate_email(prenom, nom),
        adresse=f"{fake.street_name()} - Dakar"
    )

# 📌 2. Propriétaires physiques (15 femmes)
for _ in range(15):
    prenom = random.choice(prenoms_femmes)
    nom = random.choice(noms_senegalais)
    Proprietaire.objects.create(
        est_moral=False,
        prenom=prenom,
        nom=nom,
        sexe="F",
        numero_identite=generate_cni(),
        telephone=f"76{random.randint(1000000, 9999999)}",
        email=generate_email(prenom, nom),
        adresse=f"{fake.street_name()} - Dakar"
    )

# 📌 3. Entreprises (10)
ninea_set = set()
for _ in range(10):
    while True:
        ninea = f"NINEA-{random.randint(1000000, 9999999)}"
        if ninea not in ninea_set:
            ninea_set.add(ninea)
            break
    entreprise = f"{fake.company()} Sénégal"
    Proprietaire.objects.create(
        est_moral=True,
        entreprise=entreprise,
        ninea=ninea,
        telephone=f"78{random.randint(1000000, 9999999)}",
        email=f"{entreprise.replace(' ', '').lower()}@entreprisesn.com",
        adresse=f"Zone Industrielle {random.randint(1, 10)} - Dakar"
    )

print("✅ Propriétaires chargés avec succès (25 physiques, 10 entreprises).")
