# core/management/commands/seed_all.py
"""
Commande de seed complet — Remplit TOUTES les tables avec des donnees
realistes de type BTP Senegal / Dakar.
"""
import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

from core.models import (
    TypeProjet, Proprietaire, Projet, Employe, Fournisseur,
    CategorieMateriel, Materiel, EtapeStandard, PhaseVersement,
    Achat, LigneAchat, Versement,
    MarcheTravaux, AvancementChantier,
    SousTraitant, ContratSousTraitance,
    BonSortie, LigneBonSortie,
    CompteComptable, EcritureComptable, LigneEcriture,
    CompteBancaire, TransactionBancaire,
    DocumentProjet, BordereauPrix, LigneBordereau, DecompteGD,
    ProfilUtilisateur,
)


def D(val):
    return Decimal(str(val))


class Command(BaseCommand):
    help = "Remplit la base avec des donnees realistes BTP Senegal"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("  SEED COMPLET — LAMANE BTP")
        self.stdout.write("=" * 60)

        self._users()
        self._types_projets()
        self._categories_materiaux()
        self._materiaux()
        self._etapes_standard()
        self._clients()
        self._fournisseurs()
        self._sous_traitants()
        self._employes()
        self._projets()
        self._marches()
        self._phases_versement()
        self._achats()
        self._versements()
        self._avancements()
        self._bons_sortie()
        self._comptes_bancaires()
        self._transactions()
        self._documents_btp()
        self._bordereaux()
        self._dgd()
        self._ecritures_comptables()

        self.stdout.write(self.style.SUCCESS("\n  SEED TERMINE — Toutes les tables sont remplies !"))

    # ═══════════════════════════════════════════════════════════════════
    #  UTILISATEURS
    # ═══════════════════════════════════════════════════════════════════
    def _users(self):
        users_data = [
            ("admin", "Admin", "Lamane", "admin@lamane.sn", "direction", True),
            ("mdiallo", "Mamadou", "Diallo", "m.diallo@lamane.sn", "comptable", True),
            ("andiaye", "Aminata", "Ndiaye", "a.ndiaye@lamane.sn", "chef_chantier", False),
            ("ifall", "Ibrahima", "Fall", "i.fall@lamane.sn", "gestionnaire", False),
            ("fdiop", "Fatou", "Diop", "f.diop@lamane.sn", "direction", False),
        ]
        for uname, first, last, email, role, is_staff in users_data:
            u, created = User.objects.get_or_create(
                username=uname,
                defaults={
                    "first_name": first, "last_name": last,
                    "email": email, "is_staff": is_staff,
                }
            )
            if created:
                u.set_password("Lamane2025!")
                u.save()
            ProfilUtilisateur.objects.get_or_create(
                user=u, defaults={"role": role, "telephone": f"+221 77 {random.randint(100,999)} {random.randint(10,99)} {random.randint(10,99)}"}
            )
        self.stdout.write(f"  Utilisateurs : {User.objects.count()}")

    # ═══════════════════════════════════════════════════════════════════
    #  TYPES DE PROJETS
    # ═══════════════════════════════════════════════════════════════════
    def _types_projets(self):
        types = [
            ("Villa individuelle", "Construction de villa residentielle"),
            ("Immeuble R+2", "Immeuble a etages type R+2"),
            ("Immeuble R+4", "Immeuble a etages type R+4"),
            ("Batiment commercial", "Locaux commerciaux, boutiques, bureaux"),
            ("Entrepot / Hangar", "Construction industrielle legere"),
            ("Renovation", "Renovation et rehabilitation de batiment"),
            ("Amenagement exterieur", "Cloture, piscine, VRD, paysage"),
            ("Batiment public", "Ecole, centre de sante, mosquee"),
        ]
        for nom, desc in types:
            TypeProjet.objects.get_or_create(nom=nom, defaults={"description": desc})
        self.stdout.write(f"  Types projets : {TypeProjet.objects.count()}")

    # ═══════════════════════════════════════════════════════════════════
    #  CATEGORIES MATERIAUX
    # ═══════════════════════════════════════════════════════════════════
    def _categories_materiaux(self):
        cats = [
            "Ciment & Liants", "Sable & Gravier", "Fer & Acier",
            "Bois & Coffrage", "Plomberie", "Electricite",
            "Carrelage & Faience", "Peinture", "Quincaillerie",
            "Menuiserie Aluminium", "Etancheite", "Outillage",
        ]
        for c in cats:
            CategorieMateriel.objects.get_or_create(nom=c)
        self.stdout.write(f"  Categories : {CategorieMateriel.objects.count()}")

    # ═══════════════════════════════════════════════════════════════════
    #  MATERIAUX
    # ═══════════════════════════════════════════════════════════════════
    def _materiaux(self):
        cats = {c.nom: c for c in CategorieMateriel.objects.all()}
        mats = [
            ("Ciment CEM II 42.5", "Sac (50kg)", "Ciment & Liants"),
            ("Ciment blanc", "Sac (25kg)", "Ciment & Liants"),
            ("Sable de mer", "m3", "Sable & Gravier"),
            ("Sable de dune", "m3", "Sable & Gravier"),
            ("Gravier 5/15", "m3", "Sable & Gravier"),
            ("Gravier 15/25", "m3", "Sable & Gravier"),
            ("Fer a beton HA 8", "Barre (12m)", "Fer & Acier"),
            ("Fer a beton HA 10", "Barre (12m)", "Fer & Acier"),
            ("Fer a beton HA 12", "Barre (12m)", "Fer & Acier"),
            ("Fer a beton HA 14", "Barre (12m)", "Fer & Acier"),
            ("Fer a beton HA 16", "Barre (12m)", "Fer & Acier"),
            ("Fil de fer recuit", "Kg", "Fer & Acier"),
            ("Treillis soude", "Panneau", "Fer & Acier"),
            ("Bois de coffrage (chevron)", "Unite", "Bois & Coffrage"),
            ("Contreplaque 15mm", "Panneau", "Bois & Coffrage"),
            ("Madrier 8x22", "Unite", "Bois & Coffrage"),
            ("Tuyau PVC 100mm", "Barre (4m)", "Plomberie"),
            ("Tuyau PVC 50mm", "Barre (4m)", "Plomberie"),
            ("Coude PVC 100mm", "Unite", "Plomberie"),
            ("Robinet mitigeur", "Unite", "Plomberie"),
            ("WC complet (cuvette+reservoir)", "Unite", "Plomberie"),
            ("Lavabo ceramique", "Unite", "Plomberie"),
            ("Cable electrique 2.5mm2", "Rouleau (100m)", "Electricite"),
            ("Cable electrique 4mm2", "Rouleau (100m)", "Electricite"),
            ("Disjoncteur 20A", "Unite", "Electricite"),
            ("Tableau electrique 12 modules", "Unite", "Electricite"),
            ("Prise double", "Unite", "Electricite"),
            ("Interrupteur simple", "Unite", "Electricite"),
            ("Spot LED encastrable", "Unite", "Electricite"),
            ("Carrelage sol 40x40 gres", "m2", "Carrelage & Faience"),
            ("Carrelage mural 25x40", "m2", "Carrelage & Faience"),
            ("Colle a carrelage", "Sac (25kg)", "Carrelage & Faience"),
            ("Joint carrelage", "Sac (5kg)", "Carrelage & Faience"),
            ("Peinture vinylique (seau 15L)", "Seau", "Peinture"),
            ("Peinture glycero (seau 4L)", "Seau", "Peinture"),
            ("Enduit de lissage", "Sac (25kg)", "Peinture"),
            ("Serrure porte", "Unite", "Quincaillerie"),
            ("Charniere 100mm", "Paire", "Quincaillerie"),
            ("Pointe 80mm", "Kg", "Quincaillerie"),
            ("Vis a bois 5x50", "Boite (200)", "Quincaillerie"),
            ("Fenetre alu coulissante 120x120", "Unite", "Menuiserie Aluminium"),
            ("Porte alu vitree", "Unite", "Menuiserie Aluminium"),
            ("Baie vitree coulissante", "Unite", "Menuiserie Aluminium"),
            ("Rouleau etancheite bitumineux", "Rouleau (10m)", "Etancheite"),
            ("Produit d'impermeabilisation", "Bidon (20L)", "Etancheite"),
        ]
        for nom, unite, cat_nom in mats:
            cat = cats.get(cat_nom)
            Materiel.objects.get_or_create(nom=nom, defaults={"unite": unite, "categorie": cat})
        self.stdout.write(f"  Materiaux : {Materiel.objects.count()}")

    # ═══════════════════════════════════════════════════════════════════
    #  ETAPES STANDARD
    # ═══════════════════════════════════════════════════════════════════
    def _etapes_standard(self):
        etapes = [
            ("Terrassement & Fouilles", 1, "gros", False),
            ("Fondations", 2, "gros", False),
            ("Soubassement", 3, "gros", True),
            ("Dalle basse / Plancher RDC", 4, "gros", False),
            ("Elevation murs", 5, "gros", True),
            ("Linteaux & Chainage", 6, "gros", True),
            ("Dalle de compression", 7, "gros", True),
            ("Escalier", 8, "gros", True),
            ("Acrotere & Terrasse", 9, "gros", False),
            ("Etancheite toiture", 10, "second", False),
            ("Enduit ciment", 11, "second", True),
            ("Installation electrique", 12, "second", True),
            ("Installation plomberie", 13, "second", True),
            ("Chape & Carrelage", 14, "second", True),
            ("Menuiserie aluminium", 15, "second", False),
            ("Menuiserie bois", 16, "second", False),
            ("Peinture interieure", 17, "second", True),
            ("Peinture exterieure", 18, "second", False),
            ("Revetement facade", 19, "second", False),
            ("VRD & Cloture", 20, "second", False),
            ("Amenagement exterieur", 21, "second", False),
            ("Nettoyage & Livraison", 22, "second", False),
        ]
        for nom, ordre, groupe, multi in etapes:
            EtapeStandard.objects.get_or_create(
                nom=nom, defaults={"ordre": ordre, "groupe": groupe, "multi_niveau": multi}
            )
        self.stdout.write(f"  Etapes standard : {EtapeStandard.objects.count()}")

    # ═══════════════════════════════════════════════════════════════════
    #  CLIENTS (PROPRIETAIRES)
    # ═══════════════════════════════════════════════════════════════════
    def _clients(self):
        clients = [
            (False, "Ousmane", "Sow", "M", "77 111 22 33", "ousmane.sow@gmail.com", "Almadies, Dakar"),
            (False, "Aissatou", "Ba", "F", "78 222 33 44", "aissatou.ba@yahoo.fr", "Mermoz, Dakar"),
            (False, "Cheikh", "Diagne", "M", "76 333 44 55", "c.diagne@hotmail.com", "Ngor, Dakar"),
            (False, "Mariama", "Gueye", "F", "77 444 55 66", "mariama.g@gmail.com", "Plateau, Dakar"),
            (False, "Abdoulaye", "Ndoye", "M", "78 555 66 77", "a.ndoye@outlook.com", "Ouakam, Dakar"),
            (False, "Dieynaba", "Sarr", "F", "77 666 77 88", "d.sarr@gmail.com", "Fann, Dakar"),
            (True, None, None, None, "33 820 11 22", "contact@immosn.sn", "Point E, Dakar"),
            (True, None, None, None, "33 821 22 33", "info@sahelimmo.sn", "VDN, Dakar"),
            (True, None, None, None, "33 822 33 44", "contact@groupeseck.sn", "Rufisque"),
        ]
        entreprises = ["IMMO SN SARL", "SAHEL IMMOBILIER SA", "GROUPE SECK & FILS"]
        ent_idx = 0
        for est_moral, prenom, nom, sexe, tel, email, adresse in clients:
            defaults = {"telephone": tel, "email": email, "adresse": adresse, "est_moral": est_moral}
            if est_moral:
                defaults["entreprise"] = entreprises[ent_idx]
                defaults["ninea"] = f"{random.randint(1000000, 9999999)} {random.choice('ABCDEF')}{random.randint(1,9)}"
                ent_idx += 1
                Proprietaire.objects.get_or_create(entreprise=defaults["entreprise"], defaults=defaults)
            else:
                defaults["prenom"] = prenom
                defaults["nom"] = nom
                defaults["sexe"] = sexe
                import uuid as _uuid
                defaults["numero_identite"] = f"CLI-{_uuid.uuid4().hex[:10].upper()}"
                Proprietaire.objects.get_or_create(prenom=prenom, nom=nom, defaults=defaults)
        self.stdout.write(f"  Clients : {Proprietaire.objects.count()}")

    # ═══════════════════════════════════════════════════════════════════
    #  FOURNISSEURS
    # ═══════════════════════════════════════════════════════════════════
    def _fournisseurs(self):
        fourns = [
            (True, "SOCOCIM INDUSTRIES", "", "", "33 879 10 00", "Rufisque", "Ciment et materiaux"),
            (True, "DANGOTE CEMENT SENEGAL", "", "", "33 859 20 00", "Pout, Thies", "Ciment"),
            (True, "MATFORCE SA", "", "", "33 832 15 15", "Zone Industrielle, Dakar", "Fer et acier"),
            (True, "QUINCAILLERIE KHADIM", "", "", "77 640 55 12", "Colobane, Dakar", "Quincaillerie generale"),
            (True, "ETS ESPACE CARRELAGE", "", "", "33 824 88 90", "Ouest Foire, Dakar", "Carrelage et sanitaire"),
            (True, "SENEGINDIA SA", "", "", "33 849 50 50", "Diamniadio", "Peinture et revetement"),
            (True, "ALU DESIGN SENEGAL", "", "", "78 315 22 00", "Yoff, Dakar", "Menuiserie aluminium"),
            (False, "", "Moussa", "Diouf", "77 510 33 45", "Keur Massar", "Sable et gravier"),
            (False, "", "Abdou", "Mbaye", "76 620 44 56", "Diamniadio", "Bois de coffrage"),
            (False, "", "Pape", "Gueye", "78 730 55 67", "Parcelles Assainies", "Electricite"),
        ]
        for est_moral, entreprise, prenom, nom, tel, adresse, _ in fourns:
            defaults = {
                "est_moral": est_moral, "telephone": tel, "adresse": adresse,
            }
            import uuid as _uuid
            defaults["numero_identite"] = f"FRN-{_uuid.uuid4().hex[:10].upper()}"
            if est_moral:
                defaults["entreprise"] = entreprise
                defaults["ninea"] = f"{random.randint(1000000, 9999999)} {random.choice('ABCDEF')}{random.randint(1,9)}"
                if not Fournisseur.objects.filter(entreprise=entreprise).exists():
                    Fournisseur.objects.create(**defaults)
            else:
                defaults["prenom"] = prenom
                defaults["nom"] = nom
                if not Fournisseur.objects.filter(prenom=prenom, nom=nom).exists():
                    Fournisseur.objects.create(**defaults)
        self.stdout.write(f"  Fournisseurs : {Fournisseur.objects.count()}")

    # ═══════════════════════════════════════════════════════════════════
    #  SOUS-TRAITANTS
    # ═══════════════════════════════════════════════════════════════════
    def _sous_traitants(self):
        sts = [
            ("SENELEC INSTALL", "electricite_cfa", "77 800 11 22", "Electricite courant fort et faible"),
            ("DIOP PLOMBERIE", "plomberie_sanitaire", "78 801 22 33", "Plomberie et sanitaire"),
            ("ALUMINIUM PLUS", "menuiserie_alu", "76 802 33 44", "Menuiserie aluminium et PVC"),
            ("PEINTURE PRO DAKAR", "peinture_revetement", "77 803 44 55", "Peinture et decoration"),
            ("CARRELAGE EXPERT", "carrelage_faience", "78 804 55 66", "Carrelage, faience, marbre"),
            ("TOP CLIM SENEGAL", "climatisation", "77 805 66 77", "Climatisation et ventilation"),
            ("ASCENSEUR AFRIQUE", "ascenseur", "33 806 77 88", "Installation ascenseurs"),
            ("VRD TERRASSEMENT SN", "vrd", "76 807 88 99", "Terrassement et VRD"),
            ("ETANCHEITE SAHEL", "autre", "77 808 99 00", "Etancheite et impermeabilisation"),
            ("DOMOTIQUE DAKAR", "domotique", "78 809 00 11", "Domotique et smart building"),
        ]
        for nom, spe, tel, obs in sts:
            SousTraitant.objects.get_or_create(
                nom=nom,
                defaults={"specialite": spe, "telephone": tel, "adresse": "Dakar, Senegal", "contact_nom": nom.split()[0]}
            )
        self.stdout.write(f"  Sous-traitants : {SousTraitant.objects.count()}")

    # ═══════════════════════════════════════════════════════════════════
    #  EMPLOYES
    # ═══════════════════════════════════════════════════════════════════
    def _employes(self):
        employes = [
            ("Moustapha", "Diop", "M", "77 100 10 10", "Chef de chantier", "2021-03-15"),
            ("Fatimata", "Sy", "F", "78 100 20 20", "Conductrice de travaux", "2022-01-10"),
            ("Aliou", "Kane", "M", "76 100 30 30", "Macon qualifie", "2020-06-01"),
            ("Bineta", "Faye", "F", "77 100 40 40", "Comptable", "2023-02-20"),
            ("Modou", "Seck", "M", "78 100 50 50", "Chef d'equipe gros oeuvre", "2019-09-01"),
            ("Rokhaya", "Tall", "F", "76 100 60 60", "Assistante administrative", "2023-05-15"),
            ("Omar", "Gaye", "M", "77 100 70 70", "Electricien", "2021-08-01"),
            ("Ndeye", "Mbengue", "F", "78 100 80 80", "Gestionnaire de stock", "2022-11-01"),
            ("Pape", "Thiam", "M", "76 100 90 90", "Plombier", "2020-04-15"),
            ("Awa", "Camara", "F", "77 101 10 10", "Ingenieure structure", "2024-01-08"),
            ("Serigne", "Wade", "M", "78 101 20 20", "Ferailleur", "2019-07-20"),
            ("Daba", "Cisse", "F", "76 101 30 30", "Architecte d'interieur", "2023-09-01"),
        ]
        for prenom, nom, sexe, tel, poste, date_emb in employes:
            if not Employe.objects.filter(prenom=prenom, nom=nom).exists():
                Employe.objects.create(
                    prenom=prenom, nom=nom, sexe=sexe, telephone=tel,
                    poste=poste, date_embauche=date_emb,
                )
        self.stdout.write(f"  Employes : {Employe.objects.count()}")

    # ═══════════════════════════════════════════════════════════════════
    #  PROJETS
    # ═══════════════════════════════════════════════════════════════════
    def _projets(self):
        clients = list(Proprietaire.objects.all())
        types = list(TypeProjet.objects.all())
        if not clients or not types:
            return

        projets_data = [
            ("Villa Ngor Ocean View", "Ngor, Dakar", "En cours", "2024-09-01", None, 450, 280, 8, 2, D("85000000"), False, False, True, 4, True, 5),
            ("Residence Les Almadies R+3", "Almadies, Dakar", "En cours", "2024-06-15", None, 800, 1200, 24, 3, D("250000000"), False, False, True, 12, False, 0),
            ("Villa Mermoz Standing", "Mermoz, Dakar", "En cours", "2025-01-10", None, 350, 220, 6, 1, D("65000000"), True, 25, True, 3, False, 0),
            ("Immeuble Plateau Business", "Plateau, Dakar", "En attente", "2025-06-01", None, 600, 2000, 20, 4, D("450000000"), False, False, True, 20, True, 8),
            ("Villa Fann Hock", "Fann, Dakar", "Termine", "2023-06-01", "2024-12-15", 500, 300, 7, 1, D("72000000"), True, 30, True, 4, False, 0),
            ("Entrepot Diamniadio", "Diamniadio", "En cours", "2024-11-01", None, 2000, 1500, 0, 0, D("120000000"), False, False, False, 0, False, 0),
            ("Renovation Bureau VDN", "VDN, Dakar", "En pause", "2025-02-01", None, 200, 180, 6, 1, D("35000000"), False, False, True, 3, False, 0),
            ("Villa Ouakam Piscine", "Ouakam, Dakar", "En cours", "2024-08-15", None, 600, 350, 9, 2, D("110000000"), True, 40, True, 5, True, 6),
        ]

        for i, (nom, loc, statut, dd, df, sup, sb, np, ne, cout, pisc, vol_p, clim, nb_c, asc, nb_a) in enumerate(projets_data):
            if Projet.objects.filter(nom=nom).exists():
                continue
            Projet.objects.create(
                nom=nom, localisation=loc, statut=statut,
                date_debut=dd, date_fin=df,
                superficie=sup, surface_batie=sb,
                nombre_pieces=np, nombre_etages=ne,
                cout_estime_lamane=cout,
                a_piscine=pisc, volume_piscine=vol_p if pisc else None,
                a_climatisation=clim, nombre_clims=nb_c if clim else None,
                a_ascenseur=asc, nombre_ascenseurs=nb_a if asc else None,
                type_projet=types[i % len(types)],
                proprietaire=clients[i % len(clients)],
                description=f"Projet de construction {nom} situe a {loc}. Superficie {sup}m2.",
            )
        self.stdout.write(f"  Projets : {Projet.objects.count()}")

    # ═══════════════════════════════════════════════════════════════════
    #  MARCHES DE TRAVAUX
    # ═══════════════════════════════════════════════════════════════════
    def _marches(self):
        projets = list(Projet.objects.all())
        for i, p in enumerate(projets):
            if MarcheTravaux.objects.filter(projet=p).exists():
                continue
            coeff = D(str(random.uniform(1.15, 1.4)))
            montant = (p.cout_estime_lamane * coeff).quantize(D("1"))
            import uuid as _uuid
            MarcheTravaux.objects.create(
                projet=p,
                numero_marche=f"MT-2024-{_uuid.uuid4().hex[:6].upper()}",
                objet=f"Travaux de construction — {p.nom}",
                montant_marche=montant,
                montant_avance_demarrage=(montant * D("0.20")).quantize(D("1")),
                date_signature=p.date_debut - timedelta(days=random.randint(15, 45)),
                date_ordre_service=p.date_debut,
                delai_execution_jours=random.choice([365, 540, 730, 270, 450]),
                statut="en_cours" if p.statut == "En cours" else ("reception_provisoire" if p.statut == "Termine" else "signe"),
            )
        self.stdout.write(f"  Marches : {MarcheTravaux.objects.count()}")

    # ═══════════════════════════════════════════════════════════════════
    #  PHASES DE VERSEMENT
    # ═══════════════════════════════════════════════════════════════════
    def _phases_versement(self):
        projets = list(Projet.objects.all())
        etapes = list(EtapeStandard.objects.all()[:6])
        phases_template = [
            ("Avance de demarrage", 1, D("0.20")),
            ("Fondation terminee", 2, D("0.15")),
            ("Elevation RDC terminee", 3, D("0.15")),
            ("Dalle etage terminee", 4, D("0.15")),
            ("Second oeuvre 50%", 5, D("0.15")),
            ("Finitions et livraison", 6, D("0.20")),
        ]
        for p in projets:
            if p.phases.exists():
                continue
            for lib, ordre, pct in phases_template:
                montant = (p.cout_estime_lamane * pct).quantize(D("1"))
                ech = p.date_debut + timedelta(days=ordre * 60)
                et = etapes[ordre - 1] if ordre <= len(etapes) else None
                PhaseVersement.objects.create(
                    projet=p, libelle=lib, ordre=ordre,
                    montant_prevu=montant, echeance=ech,
                    etape_standard=et,
                )
        self.stdout.write(f"  Phases versement : {PhaseVersement.objects.count()}")

    # ═══════════════════════════════════════════════════════════════════
    #  ACHATS
    # ═══════════════════════════════════════════════════════════════════
    def _achats(self):
        projets = list(Projet.objects.filter(statut__in=["En cours", "Termine"]))
        fournisseurs = list(Fournisseur.objects.all())
        materiaux = list(Materiel.objects.all())
        if not projets or not fournisseurs or not materiaux:
            return

        modes = ["especes", "virement", "cheque"]
        for p in projets:
            if p.achats.count() >= 3:
                continue
            nb_achats = random.randint(4, 8)
            for j in range(nb_achats):
                date_a = p.date_debut + timedelta(days=random.randint(10, 300))
                f = random.choice(fournisseurs)
                mode = random.choice(modes)
                achat = Achat(
                    date_achat=date_a, projet=p, fournisseur=f,
                    mode_paiement=mode,
                    numero_facture=f"FA-{date_a.year}-{random.randint(1000,9999)}",
                    tva_active=random.choice([True, False]),
                    statut_paiement=random.choice(["paye", "en_attente"]),
                )
                achat.save()
                nb_lignes = random.randint(2, 5)
                mats_choisis = random.sample(materiaux, min(nb_lignes, len(materiaux)))
                for mat in mats_choisis:
                    LigneAchat.objects.create(
                        achat=achat, materiel=mat,
                        quantite=random.randint(5, 200),
                        prix_unitaire=D(str(random.choice([2500, 5000, 8000, 12000, 15000, 25000, 45000, 75000, 150000]))),
                    )
                achat.calcul_totaux()
                achat.save(update_fields=["total_ht", "total_tva", "total_ttc"])
        self.stdout.write(f"  Achats : {Achat.objects.count()} ({LigneAchat.objects.count()} lignes)")

    # ═══════════════════════════════════════════════════════════════════
    #  VERSEMENTS
    # ═══════════════════════════════════════════════════════════════════
    def _versements(self):
        projets = list(Projet.objects.filter(statut__in=["En cours", "Termine"]))
        types_v = ["cheque", "virement bancaire", "especes", "wave", "virement om"]
        for p in projets:
            if p.versements.count() >= 2:
                continue
            phases = list(p.phases.all().order_by("ordre"))
            nb_v = min(random.randint(2, 4), len(phases))
            for i in range(nb_v):
                phase = phases[i] if i < len(phases) else phases[-1]
                date_v = p.date_debut + timedelta(days=(i + 1) * 60 + random.randint(-10, 10))
                montant = phase.montant_prevu * D(str(random.uniform(0.8, 1.0)))
                montant = montant.quantize(D("1"))
                etapes = list(EtapeStandard.objects.all())
                Versement.objects.create(
                    projet=p, phase=phase,
                    etape=random.choice(etapes) if etapes else None,
                    montant=montant,
                    date_versement=date_v,
                    type_versement=random.choice(types_v),
                    reference_paiement=f"REF-{random.randint(100000, 999999)}",
                )
        self.stdout.write(f"  Versements : {Versement.objects.count()}")

    # ═══════════════════════════════════════════════════════════════════
    #  AVANCEMENTS CHANTIER
    # ═══════════════════════════════════════════════════════════════════
    def _avancements(self):
        projets = list(Projet.objects.filter(statut__in=["En cours", "Termine"]))
        for p in projets:
            if p.avancements.count() >= 2:
                continue
            start = p.date_debut.replace(day=1)
            taux = D("0")
            for m in range(random.randint(4, 10)):
                periode = start + timedelta(days=30 * m)
                if periode.day != 1:
                    periode = periode.replace(day=1)
                incr = D(str(random.uniform(5, 15)))
                taux = min(taux + incr, D("100"))
                taux_fin = min(taux - D(str(random.uniform(0, 5))), D("100"))
                taux_plan = D(str(min(10 + m * 10, 100)))
                if AvancementChantier.objects.filter(projet=p, periode=periode).exists():
                    continue
                AvancementChantier.objects.create(
                    projet=p, periode=periode,
                    taux_physique=taux.quantize(D("0.01")),
                    taux_financier=max(D("0"), taux_fin).quantize(D("0.01")),
                    taux_planifie=taux_plan.quantize(D("0.01")),
                    effectif_ouvriers=random.randint(8, 35),
                    effectif_encadrement=random.randint(2, 6),
                    observations=random.choice([
                        "Avancement normal, pas d'incident.",
                        "Legere pluie, travaux ralentis 2 jours.",
                        "Retard livraison ciment, rattrape en fin de mois.",
                        "Coulage dalle reussi, bonne qualite.",
                        "Equipe renforcee pour rattraper le retard.",
                        "",
                    ]),
                )
        self.stdout.write(f"  Avancements : {AvancementChantier.objects.count()}")

    # ═══════════════════════════════════════════════════════════════════
    #  BONS DE SORTIE
    # ═══════════════════════════════════════════════════════════════════
    def _bons_sortie(self):
        projets = list(Projet.objects.filter(statut="En cours"))
        materiaux = list(Materiel.objects.all())
        if not projets or not materiaux:
            return
        for p in projets:
            if p.bons_sortie.count() >= 2:
                continue
            for _ in range(random.randint(2, 4)):
                date_s = p.date_debut + timedelta(days=random.randint(30, 200))
                bs = BonSortie(
                    projet=p, date_sortie=date_s,
                    responsable=random.choice(["Moustapha Diop", "Fatimata Sy", "Aliou Kane"]),
                    observations=random.choice(["Chantier RDC", "Etage 1", "Finitions", ""]),
                )
                bs.save()
                mats = random.sample(materiaux, min(random.randint(2, 5), len(materiaux)))
                for mat in mats:
                    LigneBonSortie.objects.create(
                        bon=bs, materiel=mat,
                        quantite=D(str(random.randint(5, 50))),
                        commentaire=random.choice(["", "Urgent", "Stock faible"]),
                    )
        self.stdout.write(f"  Bons de sortie : {BonSortie.objects.count()}")

    # ═══════════════════════════════════════════════════════════════════
    #  COMPTES BANCAIRES
    # ═══════════════════════════════════════════════════════════════════
    def _comptes_bancaires(self):
        comptes = [
            ("Compte courant CBAO", "banque", "CBAO Groupe Attijariwafa", "SN012 0100 0001 2345 6789", D("5000000")),
            ("Compte BIS", "banque", "Banque Islamique du Senegal", "SN015 0200 0009 8765 4321", D("2000000")),
            ("Caisse chantier", "caisse", "", "", D("500000")),
            ("Orange Money Entreprise", "mobile_money", "Orange Money", "77 000 00 00", D("200000")),
            ("Wave Business", "mobile_money", "Wave", "78 000 00 00", D("150000")),
        ]
        for nom, type_c, banque, num, solde in comptes:
            CompteBancaire.objects.get_or_create(
                nom=nom, defaults={"type_compte": type_c, "banque": banque, "numero_compte": num, "solde_initial": solde}
            )
        self.stdout.write(f"  Comptes bancaires : {CompteBancaire.objects.count()}")

    # ═══════════════════════════════════════════════════════════════════
    #  TRANSACTIONS BANCAIRES
    # ═══════════════════════════════════════════════════════════════════
    def _transactions(self):
        comptes = list(CompteBancaire.objects.all())
        projets = list(Projet.objects.all())
        if not comptes or TransactionBancaire.objects.count() >= 10:
            return

        for _ in range(20):
            c = random.choice(comptes)
            p = random.choice(projets) if random.random() > 0.3 else None
            type_t = random.choice(["entree", "sortie"])
            montant = D(str(random.choice([50000, 100000, 250000, 500000, 1000000, 2500000, 5000000])))
            date_t = date(2025, random.randint(1, 3), random.randint(1, 28))
            libelles_entree = ["Versement client", "Virement recu", "Encaissement cheque", "Depot especes"]
            libelles_sortie = ["Paiement fournisseur", "Salaires", "Achat materiaux", "Sous-traitant", "Frais de fonctionnement"]
            lib = random.choice(libelles_entree if type_t == "entree" else libelles_sortie)
            TransactionBancaire.objects.create(
                compte=c, type_transaction=type_t, montant=montant,
                date_transaction=date_t, libelle=f"{lib} — {p.nom if p else 'General'}",
                projet=p,
            )
        self.stdout.write(f"  Transactions : {TransactionBancaire.objects.count()}")

    # ═══════════════════════════════════════════════════════════════════
    #  DOCUMENTS BTP
    # ═══════════════════════════════════════════════════════════════════
    def _documents_btp(self):
        projets = list(Projet.objects.all())
        users = list(User.objects.all())
        if not projets or DocumentProjet.objects.count() >= 5:
            return

        docs_templates = [
            ("pv_reunion", "PV reunion de chantier n{n}"),
            ("pv_reunion", "PV reunion coordination n{n}"),
            ("rapport", "Rapport mensuel d'avancement n{n}"),
            ("attachement", "Attachement travaux lot {n}"),
            ("photo", "Photos avancement mois {n}"),
            ("plan", "Plan d'execution modifie v{n}"),
            ("autre", "Note technique n{n}"),
        ]
        for p in projets[:5]:
            for i in range(random.randint(2, 4)):
                tmpl = random.choice(docs_templates)
                titre = tmpl[1].format(n=i + 1)
                date_d = p.date_debut + timedelta(days=random.randint(30, 300))
                DocumentProjet.objects.create(
                    projet=p, type_document=tmpl[0], titre=titre,
                    description=f"Document {titre} pour le projet {p.nom}",
                    fichier="documents_btp/placeholder.txt",
                    auteur=random.choice(users) if users else None,
                    date_document=date_d,
                )
        self.stdout.write(f"  Documents BTP : {DocumentProjet.objects.count()}")

    # ═══════════════════════════════════════════════════════════════════
    #  BORDEREAUX DE PRIX
    # ═══════════════════════════════════════════════════════════════════
    def _bordereaux(self):
        projets = list(Projet.objects.all())
        if not projets or BordereauPrix.objects.count() >= 3:
            return

        postes_btp = [
            ("1.1", "Terrassement en pleine masse", "m3", 150, 8500),
            ("1.2", "Fouilles en rigole", "ml", 200, 5000),
            ("2.1", "Beton de proprete dose a 150kg/m3", "m3", 15, 85000),
            ("2.2", "Beton arme dose a 350kg/m3", "m3", 80, 125000),
            ("2.3", "Coffrage soigne", "m2", 300, 6500),
            ("2.4", "Acier HA en armatures", "Kg", 5000, 1200),
            ("3.1", "Maconnerie agglos pleins 20x20x40", "m2", 400, 12000),
            ("3.2", "Maconnerie agglos creux 15x20x40", "m2", 350, 9500),
            ("4.1", "Enduit ciment interieur", "m2", 600, 4500),
            ("4.2", "Enduit ciment exterieur", "m2", 400, 5000),
            ("5.1", "Carrelage gres cerame 40x40", "m2", 250, 18000),
            ("5.2", "Faience murale 25x40", "m2", 80, 15000),
            ("6.1", "Peinture vinylique 2 couches", "m2", 500, 3500),
            ("6.2", "Peinture glycero boiseries", "m2", 100, 5500),
            ("7.1", "Installation electrique complete", "Fft", 1, 8500000),
            ("7.2", "Installation plomberie complete", "Fft", 1, 6500000),
        ]

        for p in projets[:3]:
            bdp = BordereauPrix.objects.create(
                projet=p, numero=f"BDP-{p.nom[:3].upper()}-001",
                version=1, date_edition=p.date_debut, statut="valide",
            )
            for np, des, unite, qte, pu in postes_btp:
                LigneBordereau.objects.create(
                    bordereau=bdp, numero_prix=np, designation=des,
                    unite=unite, quantite=D(str(qte)), prix_unitaire=D(str(pu)),
                )
        self.stdout.write(f"  Bordereaux : {BordereauPrix.objects.count()} ({LigneBordereau.objects.count()} lignes)")

    # ═══════════════════════════════════════════════════════════════════
    #  DGD
    # ═══════════════════════════════════════════════════════════════════
    def _dgd(self):
        projets_termines = list(Projet.objects.filter(statut="Termine"))
        for p in projets_termines:
            if DecompteGD.objects.filter(projet=p).exists():
                continue
            marche = getattr(p, 'marche', None)
            mt = marche.montant_marche if marche else p.cout_estime_lamane
            DecompteGD.objects.create(
                projet=p,
                marche=marche,
                montant_travaux=mt,
                montant_avenants=D(str(random.randint(0, int(mt * D("0.05"))))),
                montant_penalites=D("0"),
                montant_retenue_garantie=(mt * D("0.05")).quantize(D("1")),
                montant_avances=(mt * D("0.20")).quantize(D("1")),
                montant_acomptes=(mt * D("0.65")).quantize(D("1")),
                observations="Travaux acheves conformement au cahier des charges.",
            )
        self.stdout.write(f"  DGD : {DecompteGD.objects.count()}")

    # ═══════════════════════════════════════════════════════════════════
    #  ECRITURES COMPTABLES
    # ═══════════════════════════════════════════════════════════════════
    def _ecritures_comptables(self):
        if EcritureComptable.objects.count() >= 5:
            return
        from core.services.comptabilite import generer_ecriture_achat, generer_ecriture_versement

        # Generer ecritures pour les achats existants
        for achat in Achat.objects.all()[:15]:
            try:
                generer_ecriture_achat(achat)
            except Exception:
                pass

        # Generer ecritures pour les versements existants
        for v in Versement.objects.all()[:15]:
            try:
                generer_ecriture_versement(v)
            except Exception:
                pass

        self.stdout.write(f"  Ecritures comptables : {EcritureComptable.objects.count()} ({LigneEcriture.objects.count()} lignes)")
