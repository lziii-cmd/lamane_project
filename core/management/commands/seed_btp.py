"""
Management command : seed_btp
Usage: python manage.py seed_btp [--reset]

Alimente la base de données avec des données réalistes pour :
  - Étapes standard BTP (20 étapes)
  - Employés LAMANE (10 profils)
  - Fournisseurs (7 supplémentaires)
  - Marchés de travaux (pour tous les projets)
  - Avancements chantier (7 mois × projets en cours)
  - Sous-traitants (10 spécialistes)
  - Contrats de sous-traitance
  - Situations mensuelles de travaux

Expert BTP / Expert Comptable / Expert Financier — LAMANE SARL
"""
import random
import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import (
    Projet, EtapeStandard, Employe, Fournisseur,
    MarcheTravaux, AvancementChantier,
    SousTraitant, ContratSousTraitance, SituationMensuelle,
)


def rnd_date(start: date, end: date) -> date:
    delta = (end - start).days
    if delta <= 0:
        return start
    return start + timedelta(days=random.randint(0, delta))


ETAPES_BTP = [
    (1,  "SIGNATURE DU MARCHE",         False, "gros"),
    (2,  "FONDATION",                   False, "gros"),
    (3,  "ELEVATION (MACONNERIE)",       True,  "gros"),
    (4,  "PLANCHER (DALLE)",            True,  "gros"),
    (5,  "TOITURE / CHARPENTE",         False, "gros"),
    (6,  "MENUISERIE EXTERIEURE",       False, "second"),
    (7,  "ENDUIT EXTERIEUR",            False, "second"),
    (8,  "PLOMBERIE SANITAIRE",         True,  "second"),
    (9,  "ELECTRICITE / CFA",           True,  "second"),
    (10, "CARRELAGE / FAIENCE",         True,  "second"),
    (11, "MENUISERIE INTERIEURE",       True,  "second"),
    (12, "PEINTURE INTERIEURE",         True,  "second"),
    (13, "FAUX PLAFOND",                True,  "second"),
    (14, "CLIMATISATION",               False, "second"),
    (15, "PANNEAUX SOLAIRES",           False, "second"),
    (16, "PISCINE",                     False, "second"),
    (17, "ASCENSEUR",                   False, "second"),
    (18, "AMENAGEMENT EXTERIEUR / VRD", False, "second"),
    (19, "RECEPTION PROVISOIRE",        False, "gros"),
    (20, "RECEPTION DEFINITIVE",        False, "gros"),
]

EMPLOYES_DATA = [
    ("Moussa",    "Ba",       "M", "Conducteur de Travaux",   "2020-01-15"),
    ("Fatou",     "Ndiaye",   "F", "Chef de Chantier",        "2019-06-01"),
    ("Abdoulaye", "Diallo",   "M", "Ingénieur Structure",     "2021-03-10"),
    ("Mariama",   "Sow",      "F", "Architecte",              "2018-09-01"),
    ("Ousmane",   "Diop",     "M", "Métreur BTP",             "2022-01-20"),
    ("Aissatou",  "Mbaye",    "F", "Comptable de Chantier",   "2021-07-01"),
    ("Cheikh",    "Fall",     "M", "Chef de Chantier",        "2020-11-15"),
    ("Rokhaya",   "Gueye",    "F", "Assistante Technique",    "2023-02-01"),
    ("Ibrahima",  "Niang",    "M", "Conducteur de Travaux",   "2019-04-01"),
    ("Sokhna",    "Diagne",   "F", "Ingénieur Génie Civil",   "2022-08-15"),
]

FOURNISSEURS_DATA = [
    (True,  "SEDIMA MATERIAUX",         "SN2023001", "", "", "SNXXX0001", "", "77 123 45 67", "contact@sedima.sn",    "Dakar"),
    (True,  "CIMENTS DU SAHEL",         "SN2019034", "", "", "SNXXX0002", "", "33 456 78 90", "info@cimentssahel.sn", "Thiès"),
    (True,  "AFRIBAT SARL",             "SN2021045", "", "", "SNXXX0003", "", "77 234 56 78", "afribat@gmail.com",    "Dakar"),
    (False, "",                          "",         "Modou",   "Sarr",  "SNXXX0004","M", "76 345 67 89", "modou.sarr@gmail.com","Pikine"),
    (True,  "BTP DISTRIBUTION SENEGAL", "SN2020078", "", "", "SNXXX0006", "", "33 567 89 01", "bds@bds.sn",           "Rufisque"),
    (True,  "QUINCAILLERIE DU BAOBAB",  "SN2022011", "", "", "SNXXX0007", "", "77 678 90 12", "qbaobab@gmail.com",    "Dakar"),
]

SOUS_TRAITANTS_DATA = [
    ("ELECTRO SERVICES SARL",    "electricite_cfa",     "SN2021099", "77 111 22 33", "electro@gmail.com",  "Dakar"),
    ("PLOMB'OK DAKAR",           "plomberie_sanitaire", "SN2020087", "77 222 33 44", "plombok@gmail.com",  "Dakar"),
    ("ESPACE BOIS SENEGAL",      "menuiserie_bois",     "SN2019065", "76 333 44 55", "espacebois@sn.com",  "Thiès"),
    ("CLIMATIC SOLUTIONS",       "climatisation",       "SN2022034", "70 444 55 66", "climatic@gmail.com", "Dakar"),
    ("CARRELAGE & DESIGN SN",    "carrelage_faience",   "SN2023012", "77 555 66 77", "carrelage@gmail.com","Rufisque"),
    ("SOLAIRE WEST AFRICA",      "panneaux_solaires",   "SN2021078", "77 666 77 88", "solaire@sn.com",     "Dakar"),
    ("PISCINE PRESTIGE DAKAR",   "piscine",             "SN2020055", "76 777 88 99", "piscine@dakar.sn",   "Dakar"),
    ("ELEV'UP ASCENSEURS",       "ascenseur",           "SN2019043", "33 888 99 00", "elevup@gmail.com",   "Dakar"),
    ("ALUM'ART SENEGAL",         "menuiserie_alu",      "SN2022067", "77 999 00 11", "alumart@sn.com",     "Dakar"),
    ("TERR'AMENAGE SARL",        "vrd",                 "SN2018098", "77 012 34 56", "terramena@sn.com",   "Dakar"),
]

LOTS_SPEC = [
    ("electricite_cfa",     "Lot Électricité CFA",           Decimal("0.06")),
    ("plomberie_sanitaire", "Lot Plomberie Sanitaire",        Decimal("0.05")),
    ("menuiserie_bois",     "Lot Menuiserie Bois",            Decimal("0.04")),
    ("climatisation",       "Lot Climatisation",              Decimal("0.07")),
    ("carrelage_faience",   "Lot Carrelage / Faïence",        Decimal("0.05")),
]


class Command(BaseCommand):
    help = "Alimente la base avec des données BTP réalistes (marchés, avancements, sous-traitance)"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Réinitialise les données avant de seeder")

    @transaction.atomic
    def handle(self, *args, **options):
        today = date.today()

        if options["reset"]:
            SituationMensuelle.objects.all().delete()
            ContratSousTraitance.objects.all().delete()
            SousTraitant.objects.all().delete()
            AvancementChantier.objects.all().delete()
            MarcheTravaux.objects.all().delete()
            self.stdout.write(self.style.WARNING("🗑️  Données existantes supprimées"))

        # ── 1. Étapes standard ─────────────────────────────────────────────
        EtapeStandard.objects.all().delete()
        for ordre, nom, multi, groupe in ETAPES_BTP:
            EtapeStandard.objects.create(nom=nom, ordre=ordre, multi_niveau=multi, groupe=groupe)
        self.stdout.write(self.style.SUCCESS(f"✅ {len(ETAPES_BTP)} étapes standard créées"))

        # ── 2. Employés ────────────────────────────────────────────────────
        if Employe.objects.count() == 0:
            for i, (prenom, nom, sexe, poste, embauche) in enumerate(EMPLOYES_DATA, 1):
                Employe.objects.create(
                    prenom=prenom, nom=nom, sexe=sexe, poste=poste,
                    date_embauche=embauche,
                    numero_identite=f"SN{i:07d}B",
                    telephone=f"77{random.randint(1000000,9999999)}",
                    email=f"{prenom.lower()}.{nom.lower()}@lamane.sn",
                    adresse="Dakar, Sénégal",
                )
            self.stdout.write(self.style.SUCCESS(f"✅ {len(EMPLOYES_DATA)} employés créés"))

        # ── 3. Fournisseurs ────────────────────────────────────────────────
        for (est_moral, entreprise, ninea, prenom, nom, ni, sexe, tel, email, adresse) in FOURNISSEURS_DATA:
            Fournisseur.objects.get_or_create(
                numero_identite=ni,
                defaults=dict(
                    est_moral=est_moral, entreprise=entreprise, ninea=ninea,
                    prenom=prenom, nom=nom, sexe=sexe, telephone=tel,
                    email=email, adresse=adresse,
                )
            )
        self.stdout.write(self.style.SUCCESS("✅ Fournisseurs créés/existants"))

        # ── 4. Marchés de travaux ──────────────────────────────────────────
        STATUTS_MARCHE = {
            "En attente": "en_attente",
            "En cours": "en_cours",
            "En pause": "en_attente",
            "Terminé": "reception_definitive",
        }
        projets = list(Projet.objects.all()[:30])
        marches_crees = 0
        for i, projet in enumerate(projets):
            if MarcheTravaux.objects.filter(projet=projet).exists():
                continue
            montant = max(
                float(projet.cout_estime_lamane or 0),
                random.randint(80, 600) * 1_000_000,
            )
            statut_m = STATUTS_MARCHE.get(projet.statut, "en_cours")
            dsign = rnd_date(date(2022, 1, 1), date(2025, 6, 1))
            dos = dsign + timedelta(days=random.randint(7, 30))
            delai = random.choice([180, 270, 365, 450, 540])
            d_rp = d_rd = None
            if projet.statut == "Terminé":
                d_rp = rnd_date(dos + timedelta(days=delai - 30), dos + timedelta(days=delai + 60))
                d_rd = min(d_rp + timedelta(days=random.randint(30, 180)), today)
            MarcheTravaux.objects.create(
                projet=projet,
                numero_marche=f"MRK-{dsign.year}-{str(projet.id)[:8].upper()}",
                objet=f"Construction / Rénovation — {projet.nom}",
                montant_marche=round(montant, -3),
                montant_avance_demarrage=round(montant * 0.25, -3),
                taux_retenue_garantie=Decimal("5.00"),
                penalite_journaliere_pct=Decimal("0.0500"),
                plafond_penalites_pct=Decimal("10.00"),
                date_signature=dsign,
                date_ordre_service=dos,
                delai_execution_jours=delai,
                statut=statut_m,
                date_reception_provisoire=d_rp,
                date_reception_definitive=d_rd,
                observations="Marché BTP conforme CCAG Sénégal",
            )
            marches_crees += 1
        self.stdout.write(self.style.SUCCESS(f"✅ {marches_crees} marchés de travaux créés"))

        # ── 5. Avancements chantier ────────────────────────────────────────
        projets_en_cours = Projet.objects.filter(statut="En cours")[:12]
        av_crees = 0
        for projet in projets_en_cours:
            taux_cumul = 0.0
            for m in range(7, 0, -1):
                mois = ((today.month - m - 1) % 12) + 1
                annee = today.year if (today.month - m) > 0 else today.year - 1
                periode = date(annee, mois, 1)
                taux_cumul = min(100.0, taux_cumul + random.uniform(5, 16))
                tp = min(100.0, taux_cumul + random.uniform(-2, 3))
                tf = min(tp, tp * random.uniform(0.82, 0.96))
                tpl = min(100.0, taux_cumul)
                _, created = AvancementChantier.objects.get_or_create(
                    projet=projet, periode=periode,
                    defaults=dict(
                        taux_physique=round(tp, 1),
                        taux_financier=round(tf, 1),
                        taux_planifie=round(tpl, 1),
                        effectif_ouvriers=random.randint(8, 25),
                        effectif_encadrement=random.randint(2, 5),
                        observations=random.choice([
                            "Travaux conformes au planning.",
                            "Légère avance sur le programme.",
                            "RAS — chantier en bonne marche.",
                            "Quelques retards fournisseurs absorbés.",
                        ]),
                    ),
                )
                if created:
                    av_crees += 1
        self.stdout.write(self.style.SUCCESS(f"✅ {av_crees} avancements chantier créés"))

        # ── 6. Sous-traitants ──────────────────────────────────────────────
        st_by_spec = {}
        for nom, spec, ninea, tel, email, adresse in SOUS_TRAITANTS_DATA:
            st, _ = SousTraitant.objects.get_or_create(
                nom=nom,
                defaults=dict(specialite=spec, ninea=ninea, telephone=tel, email=email, adresse=adresse),
            )
            st_by_spec[spec] = st
        self.stdout.write(self.style.SUCCESS(f"✅ {len(SOUS_TRAITANTS_DATA)} sous-traitants créés"))

        # ── 7. Contrats de sous-traitance ──────────────────────────────────
        marches = MarcheTravaux.objects.select_related("projet")[:10]
        cst_crees = 0
        for marche in marches:
            lots_choisis = random.sample(LOTS_SPEC, random.randint(2, 3))
            for spec_key, lot_nom, taux in lots_choisis:
                if spec_key not in st_by_spec:
                    continue
                st = st_by_spec[spec_key]
                montant_lot = round(float(marche.montant_marche) * float(taux), -3)
                montant_paye = round(montant_lot * random.uniform(0.3, 0.9), -3)
                d_deb = date(2024, random.randint(1, 6), 1)
                d_fin = d_deb + timedelta(days=random.randint(90, 180))
                ContratSousTraitance.objects.get_or_create(
                    projet=marche.projet, sous_traitant=st, lot=lot_nom,
                    defaults=dict(
                        montant=montant_lot, montant_paye=montant_paye,
                        date_debut=d_deb, date_fin_prevue=d_fin,
                        statut="en_cours", observations="Conforme CCAG sous-traitance.",
                    ),
                )
                cst_crees += 1
        self.stdout.write(self.style.SUCCESS(f"✅ {cst_crees} contrats de sous-traitance créés"))

        # ── 8. Situations mensuelles ───────────────────────────────────────
        sm_crees = 0
        for marche in MarcheTravaux.objects.select_related("projet")[:15]:
            mm = float(marche.montant_marche)
            taux_cumul = 0.0
            cumul_prev = 0.0
            for s in range(random.randint(3, 8)):
                mois = min(12, s + 1)
                periode_s = date(2024, mois, 1)
                taux_cumul = min(100.0, taux_cumul + random.uniform(6, 20))
                montant_brut = round(mm * taux_cumul / 100, 2)
                ret_g = round(montant_brut * 0.05, 2)
                net_c = montant_brut - ret_g
                a_payer = max(0, round(net_c - cumul_prev, 2))
                statut_s = "payee" if s < 3 else ("validee" if s < 5 else "soumise")
                num_s = s + 1
                _, created = SituationMensuelle.objects.get_or_create(
                    projet=marche.projet, numero_situation=num_s,
                    defaults=dict(
                        periode=periode_s,
                        montant_brut_cumule=montant_brut,
                        taux_avancement=round(taux_cumul, 2),
                        retenue_garantie=ret_g,
                        montant_net_cumule=net_c,
                        montant_precedentes_situations=cumul_prev,
                        montant_a_payer=a_payer,
                        statut=statut_s,
                        date_soumission=periode_s + timedelta(days=5),
                        observations=f"Situation N°{num_s} — Travaux conformes.",
                    ),
                )
                if created:
                    sm_crees += 1
                cumul_prev = net_c
        self.stdout.write(self.style.SUCCESS(f"✅ {sm_crees} situations mensuelles créées"))

        self.stdout.write(self.style.SUCCESS("\n🎉 Seed BTP terminé avec succès !"))
        self.stdout.write("  → Lance: python manage.py seed_btp --reset  pour réinitialiser")
