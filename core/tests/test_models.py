# core/tests/test_models.py
"""
Tests unitaires des modèles — LAMANE BTP Management.
Utilise des données réalistes du secteur BTP au Sénégal.
"""
from decimal import Decimal
from datetime import date, timedelta

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils import timezone

from core.models import (
    TypeProjet, Proprietaire, Projet, Employe,
    Fournisseur, SousTraitant, ContratSousTraitance,
    CategorieMateriel, Materiel, Achat, LigneAchat,
    EtapeStandard, PhaseVersement, Versement,
    BonSortie, LigneBonSortie,
    MarcheTravaux,
    CompteComptable, EcritureComptable, LigneEcriture,
    CompteBancaire, TransactionBancaire,
    DocumentProjet, BordereauPrix, LigneBordereau, DecompteGD,
    ProfilUtilisateur,
)


# ═══════════════════════════════════════════════════════════════════════════
# Helpers — Fixtures réutilisables
# ═══════════════════════════════════════════════════════════════════════════

class DonneesTestMixin:
    """Mixin fournissant des données de test réalistes BTP Sénégal."""

    @classmethod
    def creer_type_projet(cls, nom="Villa R+1"):
        return TypeProjet.objects.create(nom=nom, description="Villa résidentielle")

    @classmethod
    def creer_proprietaire_physique(cls):
        return Proprietaire.objects.create(
            est_moral=False,
            prenom="Mamadou",
            nom="Diallo",
            telephone="+221 77 123 45 67",
            email="mamadou.diallo@gmail.com",
            adresse="Almadies, Dakar",
            sexe="M",
            numero_identite="SN-CNI-1234567890",
        )

    @classmethod
    def creer_proprietaire_moral(cls):
        return Proprietaire.objects.create(
            est_moral=True,
            entreprise="SENEGAL IMMOBILIER SA",
            ninea="005467832 0G3",
            telephone="+221 33 821 00 00",
            email="contact@senegalimmobilier.sn",
            adresse="Plateau, Dakar",
        )

    @classmethod
    def creer_projet(cls, proprietaire=None, type_projet=None, **kwargs):
        if proprietaire is None:
            proprietaire = cls.creer_proprietaire_physique()
        if type_projet is None:
            type_projet = cls.creer_type_projet()
        defaults = dict(
            nom="Villa Ngor R+2",
            localisation="Ngor, Dakar",
            statut="En cours",
            date_debut=date(2025, 3, 1),
            description="Construction villa haut standing à Ngor",
            superficie=500,
            surface_batie=320,
            nombre_pieces=8,
            nombre_etages=2,
            cout_estime_lamane=Decimal("45000000.00"),
            type_projet=type_projet,
            proprietaire=proprietaire,
        )
        defaults.update(kwargs)
        return Projet.objects.create(**defaults)

    @classmethod
    def creer_fournisseur_physique(cls):
        return Fournisseur.objects.create(
            est_moral=False,
            prenom="Ibrahima",
            nom="Sow",
            numero_identite="SN-PP-9876543210",
            telephone="+221 76 500 00 00",
            adresse="Colobane, Dakar",
        )

    @classmethod
    def creer_fournisseur_moral(cls):
        return Fournisseur.objects.create(
            est_moral=True,
            entreprise="SOCOCIM INDUSTRIES",
            ninea="123456789 0A1",
            telephone="+221 33 879 50 00",
            adresse="Route de Rufisque, Dakar",
            numero_identite="SN-NINEA-SOCOCIM",
        )

    @classmethod
    def creer_categorie_materiel(cls, nom="Gros oeuvre"):
        return CategorieMateriel.objects.create(nom=nom)

    @classmethod
    def creer_materiel(cls, nom="Ciment CEM II 42.5", unite="Tonne", categorie=None):
        if categorie is None:
            categorie = cls.creer_categorie_materiel()
        return Materiel.objects.create(nom=nom, unite=unite, categorie=categorie)

    @classmethod
    def creer_etape_standard(cls, nom="Fondation", ordre=1, multi_niveau=False):
        return EtapeStandard.objects.create(
            nom=nom, ordre=ordre, multi_niveau=multi_niveau, groupe="gros"
        )

    @classmethod
    def creer_phase_versement(cls, projet, libelle="Fondation RDC"):
        return PhaseVersement.objects.create(
            projet=projet, libelle=libelle, montant_prevu=Decimal("5000000.00")
        )

    @classmethod
    def creer_sous_traitant(cls, nom="ETS Diop Electricite"):
        return SousTraitant.objects.create(
            nom=nom,
            specialite="electricite_cfa",
            ninea="987654321 0B2",
            telephone="+221 77 888 00 00",
            email="diop.elec@gmail.com",
            adresse="Parcelles Assainies, Dakar",
            contact_nom="Ousmane Diop",
        )


# ═══════════════════════════════════════════════════════════════════════════
# Tests Projet
# ═══════════════════════════════════════════════════════════════════════════

class ProjetModelTest(DonneesTestMixin, TestCase):
    """Tests du modele Projet."""

    def setUp(self):
        self.proprietaire = self.creer_proprietaire_physique()
        self.type_projet = self.creer_type_projet()
        self.projet = self.creer_projet(
            proprietaire=self.proprietaire,
            type_projet=self.type_projet,
        )

    def test_creation_projet(self):
        """Un projet est cree correctement avec tous les champs."""
        self.assertEqual(self.projet.nom, "Villa Ngor R+2")
        self.assertEqual(self.projet.localisation, "Ngor, Dakar")
        self.assertEqual(self.projet.statut, "En cours")
        self.assertEqual(self.projet.cout_estime_lamane, Decimal("45000000.00"))
        self.assertIsNotNone(self.projet.id)

    def test_str_representation(self):
        """__str__ retourne le nom du projet."""
        self.assertEqual(str(self.projet), "Villa Ngor R+2")

    def test_total_achats_sans_achats(self):
        """total_achats_ht vaut 0 si aucun achat."""
        self.assertEqual(self.projet.total_achats_ht, Decimal("0.00"))

    def test_total_versements_sans_versements(self):
        """total_versements vaut 0 si aucun versement."""
        self.assertEqual(self.projet.total_versements, Decimal("0.00"))

    def test_total_depenses_sans_depenses(self):
        """total_depenses = achats_ttc + sous_traitance, ici 0."""
        self.assertEqual(self.projet.total_depenses, Decimal("0.00"))

    def test_marge_brute_estimee_sans_donnees(self):
        """marge_brute = versements - depenses, ici 0."""
        self.assertEqual(self.projet.marge_brute_estimee, Decimal("0.00"))

    def test_taux_marge_sans_versements(self):
        """taux_marge = 0 quand pas de versements."""
        self.assertEqual(self.projet.taux_marge, Decimal("0.00"))

    def test_validation_date_fin_avant_debut(self):
        """La date de fin ne peut pas preceder la date de debut."""
        self.projet.date_fin = date(2024, 1, 1)
        with self.assertRaises(ValidationError) as ctx:
            self.projet.clean()
        self.assertIn("date_fin", ctx.exception.message_dict)

    def test_statut_termine_auto_date_fin(self):
        """Le statut Termine genere automatiquement une date_fin si absente."""
        self.projet.statut = "Terminé"
        self.projet.date_fin = None
        self.projet.clean()
        self.assertIsNotNone(self.projet.date_fin)

    def test_uuid_primary_key(self):
        """Le PK est un UUID, pas un entier auto-increment."""
        import uuid
        self.assertIsInstance(self.projet.id, uuid.UUID)


# ═══════════════════════════════════════════════════════════════════════════
# Tests Proprietaire / Client
# ═══════════════════════════════════════════════════════════════════════════

class ProprietaireModelTest(DonneesTestMixin, TestCase):
    """Tests du modele Proprietaire (Client)."""

    def test_personne_physique_nom_complet(self):
        """nom_complet pour une personne physique."""
        proprio = self.creer_proprietaire_physique()
        self.assertEqual(proprio.nom_complet(), "Mamadou Diallo")
        self.assertEqual(str(proprio), "Mamadou Diallo")

    def test_personne_morale_nom_complet(self):
        """nom_complet pour une personne morale retourne le nom entreprise."""
        proprio = self.creer_proprietaire_moral()
        self.assertEqual(proprio.nom_complet(), "SENEGAL IMMOBILIER SA")
        self.assertEqual(str(proprio), "SENEGAL IMMOBILIER SA")

    def test_personne_morale_sans_nom(self):
        """Personne morale sans nom entreprise retourne texte par defaut."""
        proprio = Proprietaire.objects.create(
            est_moral=True, telephone="+221 33 800 00 00"
        )
        self.assertEqual(proprio.nom_complet(), "Entreprise sans nom")


# ═══════════════════════════════════════════════════════════════════════════
# Tests Employe
# ═══════════════════════════════════════════════════════════════════════════

class EmployeModelTest(DonneesTestMixin, TestCase):
    """Tests du modele Employe avec auto-generation du matricule."""

    def test_auto_matricule_generation(self):
        """Le matricule est auto-genere au format PPNN + PK zero-padded."""
        employe = Employe.objects.create(
            nom="Ndiaye",
            prenom="Fatou",
            sexe="Femme",
            poste="Conductrice de travaux",
            date_embauche=date(2024, 6, 1),
            telephone="+221 77 200 00 00",
        )
        self.assertTrue(employe.matricule.startswith("FAND"))
        self.assertGreater(len(employe.matricule), 4)

    def test_str_avec_matricule(self):
        """__str__ affiche le matricule et le nom complet."""
        employe = Employe.objects.create(
            nom="Ba", prenom="Moussa", sexe="Homme",
            telephone="+221 76 100 00 00",
        )
        self.assertIn("Ba", str(employe))
        self.assertIn(employe.matricule, str(employe))

    def test_validation_date_embauche_future(self):
        """La date d'embauche ne peut pas etre dans le futur."""
        employe = Employe(
            nom="Fall", prenom="Awa", sexe="Femme",
            date_embauche=date.today() + timedelta(days=30),
            telephone="+221 77 300 00 00",
        )
        with self.assertRaises(ValidationError) as ctx:
            employe.clean()
        self.assertIn("date_embauche", ctx.exception.message_dict)


# ═══════════════════════════════════════════════════════════════════════════
# Tests Fournisseur
# ═══════════════════════════════════════════════════════════════════════════

class FournisseurModelTest(DonneesTestMixin, TestCase):
    """Tests du modele Fournisseur."""

    def test_fournisseur_physique_str(self):
        """__str__ affiche prenom + nom pour personne physique."""
        fournisseur = self.creer_fournisseur_physique()
        self.assertEqual(str(fournisseur), "Ibrahima Sow")

    def test_fournisseur_moral_str(self):
        """__str__ affiche le nom de l'entreprise pour personne morale."""
        fournisseur = self.creer_fournisseur_moral()
        self.assertEqual(str(fournisseur), "SOCOCIM INDUSTRIES")

    def test_numero_identite_unique(self):
        """Le numero_identite est unique parmi les fournisseurs."""
        self.creer_fournisseur_physique()
        with self.assertRaises(Exception):
            Fournisseur.objects.create(
                est_moral=False,
                prenom="Autre",
                nom="Personne",
                numero_identite="SN-PP-9876543210",  # doublon
            )


# ═══════════════════════════════════════════════════════════════════════════
# Tests SousTraitant & ContratSousTraitance
# ═══════════════════════════════════════════════════════════════════════════

class SousTraitantModelTest(DonneesTestMixin, TestCase):
    """Tests des modeles SousTraitant et ContratSousTraitance."""

    def setUp(self):
        self.projet = self.creer_projet()
        self.st = self.creer_sous_traitant()

    def test_sous_traitant_str(self):
        """__str__ inclut le nom et la specialite."""
        self.assertIn("ETS Diop Electricite", str(self.st))
        self.assertIn("Électricité", str(self.st))

    def test_contrat_reste_a_payer(self):
        """reste_a_payer = montant - montant_paye."""
        contrat = ContratSousTraitance.objects.create(
            projet=self.projet,
            sous_traitant=self.st,
            lot="Lot 4 - Electricite courant fort/faible",
            montant=Decimal("8500000.00"),
            montant_paye=Decimal("3000000.00"),
            date_debut=date(2025, 4, 1),
        )
        self.assertEqual(contrat.reste_a_payer, Decimal("5500000.00"))

    def test_contrat_taux_paiement(self):
        """taux_paiement = montant_paye / montant * 100."""
        contrat = ContratSousTraitance.objects.create(
            projet=self.projet,
            sous_traitant=self.st,
            lot="Lot 5 - Plomberie",
            montant=Decimal("4000000.00"),
            montant_paye=Decimal("2000000.00"),
            date_debut=date(2025, 5, 1),
        )
        self.assertEqual(contrat.taux_paiement, Decimal("50.00"))

    def test_contrat_taux_paiement_montant_zero(self):
        """taux_paiement = 0 si montant du contrat est 0."""
        contrat = ContratSousTraitance.objects.create(
            projet=self.projet,
            sous_traitant=self.st,
            lot="Lot test",
            montant=Decimal("0.00"),
            montant_paye=Decimal("0.00"),
            date_debut=date(2025, 6, 1),
        )
        self.assertEqual(contrat.taux_paiement, Decimal("0.00"))

    def test_contrat_validation_montant_paye_excessif(self):
        """montant_paye ne peut pas depasser le montant du contrat."""
        contrat = ContratSousTraitance(
            projet=self.projet,
            sous_traitant=self.st,
            lot="Lot test",
            montant=Decimal("5000000.00"),
            montant_paye=Decimal("6000000.00"),
            date_debut=date(2025, 6, 1),
        )
        with self.assertRaises(ValidationError) as ctx:
            contrat.clean()
        self.assertIn("montant_paye", ctx.exception.message_dict)

    def test_contrat_validation_dates_incoherentes(self):
        """date_fin_prevue ne peut preceder date_debut."""
        contrat = ContratSousTraitance(
            projet=self.projet,
            sous_traitant=self.st,
            lot="Lot test",
            montant=Decimal("5000000.00"),
            date_debut=date(2025, 6, 1),
            date_fin_prevue=date(2025, 5, 1),
        )
        with self.assertRaises(ValidationError) as ctx:
            contrat.clean()
        self.assertIn("date_fin_prevue", ctx.exception.message_dict)

    def test_contrat_str(self):
        """__str__ du contrat inclut le sous-traitant, le lot et le projet."""
        contrat = ContratSousTraitance.objects.create(
            projet=self.projet,
            sous_traitant=self.st,
            lot="Lot 4 - Electricite",
            montant=Decimal("8000000.00"),
            date_debut=date(2025, 4, 1),
        )
        self.assertIn("ETS Diop Electricite", str(contrat))
        self.assertIn("Lot 4", str(contrat))


# ═══════════════════════════════════════════════════════════════════════════
# Tests Achat & LigneAchat
# ═══════════════════════════════════════════════════════════════════════════

class AchatModelTest(DonneesTestMixin, TestCase):
    """Tests du modele Achat avec calcul_totaux et double-save."""

    def setUp(self):
        self.projet = self.creer_projet()
        self.fournisseur = self.creer_fournisseur_moral()
        self.categorie = self.creer_categorie_materiel()
        self.ciment = self.creer_materiel(
            nom="Ciment CEM II", unite="Tonne", categorie=self.categorie
        )
        self.fer = self.creer_materiel(
            nom="Fer a beton HA12", unite="Barre", categorie=self.categorie
        )

    def test_creation_achat_et_str(self):
        """Un achat est cree et __str__ affiche la date et le projet."""
        achat = Achat(
            date_achat=date(2025, 4, 15),
            projet=self.projet,
            fournisseur=self.fournisseur,
            mode_paiement="virement",
            numero_facture="F-2025-0042",
            tva_active=False,
        )
        achat.save()
        self.assertIn("2025-04-15", str(achat))
        self.assertIn("Villa Ngor", str(achat))

    def test_calcul_totaux_sans_tva(self):
        """calcul_totaux sans TVA : total_ttc = total_ht."""
        achat = Achat(
            date_achat=date(2025, 4, 15),
            projet=self.projet,
            fournisseur=self.fournisseur,
            mode_paiement="espèces",
            tva_active=False,
        )
        achat.save()
        LigneAchat.objects.create(
            achat=achat, materiel=self.ciment,
            quantite=10, prix_unitaire=Decimal("85000"),
        )
        LigneAchat.objects.create(
            achat=achat, materiel=self.fer,
            quantite=200, prix_unitaire=Decimal("3500"),
        )
        achat.calcul_totaux()
        # 10 * 85000 + 200 * 3500 = 850000 + 700000 = 1 550 000
        self.assertEqual(achat.total_ht, Decimal("1550000"))
        self.assertEqual(achat.total_tva, Decimal("0.00"))
        self.assertEqual(achat.total_ttc, Decimal("1550000"))

    def test_calcul_totaux_avec_tva(self):
        """calcul_totaux avec TVA 18%."""
        achat = Achat(
            date_achat=date(2025, 4, 20),
            projet=self.projet,
            fournisseur=self.fournisseur,
            mode_paiement="virement",
            tva_active=True,
        )
        achat.save()
        LigneAchat.objects.create(
            achat=achat, materiel=self.ciment,
            quantite=5, prix_unitaire=Decimal("90000"),
        )
        achat.calcul_totaux()
        # 5 * 90000 = 450 000 HT ; TVA = 81 000 ; TTC = 531 000
        self.assertEqual(achat.total_ht, Decimal("450000"))
        self.assertEqual(achat.total_tva, Decimal("81000.00"))
        self.assertEqual(achat.total_ttc, Decimal("531000.00"))

    def test_double_save_pattern(self):
        """save() appelle calcul_totaux et re-sauvegarde (double-save)."""
        achat = Achat(
            date_achat=date(2025, 5, 1),
            projet=self.projet,
            mode_paiement="chèque",
            tva_active=False,
        )
        achat.save()
        LigneAchat.objects.create(
            achat=achat, materiel=self.ciment,
            quantite=1, prix_unitaire=Decimal("100000"),
        )
        # Re-save pour declencher calcul_totaux
        achat.save()
        achat.refresh_from_db()
        self.assertEqual(achat.total_ht, Decimal("100000"))

    def test_ligne_achat_total_ligne(self):
        """LigneAchat.total_ligne = quantite * prix_unitaire."""
        achat = Achat(
            date_achat=date(2025, 5, 5),
            projet=self.projet,
            mode_paiement="espèces",
            tva_active=False,
        )
        achat.save()
        ligne = LigneAchat.objects.create(
            achat=achat, materiel=self.ciment,
            quantite=20, prix_unitaire=Decimal("85000"),
        )
        self.assertEqual(ligne.total_ligne, Decimal("1700000"))


# ═══════════════════════════════════════════════════════════════════════════
# Tests Versement
# ═══════════════════════════════════════════════════════════════════════════

class VersementModelTest(DonneesTestMixin, TestCase):
    """Tests du modele Versement avec auto-generation du numero_facture."""

    def setUp(self):
        self.projet = self.creer_projet()
        self.phase = self.creer_phase_versement(self.projet)

    def test_auto_numero_facture(self):
        """Le numero_facture est auto-genere au format FAC-YYYY-NNNN."""
        versement = Versement.objects.create(
            projet=self.projet,
            phase=self.phase,
            montant=Decimal("5000000.00"),
            date_versement=date(2025, 4, 1),
            type_versement="virement bancaire",
        )
        year = timezone.now().year
        self.assertTrue(versement.numero_facture.startswith(f"FAC-{year}-"))

    def test_auto_libelle(self):
        """Le libelle est auto-genere avec le compteur et le nom du projet."""
        versement = Versement.objects.create(
            projet=self.projet,
            phase=self.phase,
            montant=Decimal("3000000.00"),
            date_versement=date(2025, 4, 15),
            type_versement="espèces",
        )
        self.assertIn("Versement", versement.libelle)
        self.assertIn(self.projet.nom, versement.libelle)

    def test_str_avec_libelle(self):
        """__str__ retourne le libelle si present."""
        versement = Versement.objects.create(
            projet=self.projet,
            phase=self.phase,
            montant=Decimal("2000000.00"),
            date_versement=date(2025, 5, 1),
            type_versement="wave",
        )
        self.assertEqual(str(versement), versement.libelle)

    def test_sequence_numero_facture(self):
        """Les numeros de facture s'incrementent correctement."""
        v1 = Versement.objects.create(
            projet=self.projet, phase=self.phase,
            montant=Decimal("1000000.00"),
            date_versement=date(2025, 6, 1),
            type_versement="chèque",
        )
        v2 = Versement.objects.create(
            projet=self.projet, phase=self.phase,
            montant=Decimal("2000000.00"),
            date_versement=date(2025, 6, 15),
            type_versement="virement bancaire",
        )
        # Extraire les numeros de sequence
        seq1 = int(v1.numero_facture.split("-")[-1])
        seq2 = int(v2.numero_facture.split("-")[-1])
        self.assertEqual(seq2, seq1 + 1)


# ═══════════════════════════════════════════════════════════════════════════
# Tests BonSortie
# ═══════════════════════════════════════════════════════════════════════════

class BonSortieModelTest(DonneesTestMixin, TestCase):
    """Tests du modele BonSortie avec auto-generation de la reference."""

    def setUp(self):
        self.projet = self.creer_projet()
        self.categorie = self.creer_categorie_materiel()
        self.materiel = self.creer_materiel(
            nom="Sable de mer", unite="m3", categorie=self.categorie
        )

    def test_auto_reference_generation(self):
        """La reference est auto-generee au format BS-YYYY-NNN."""
        bon = BonSortie.objects.create(
            projet=self.projet,
            date_sortie=date(2025, 5, 10),
            responsable="Cheikh Diop",
        )
        year = timezone.now().year
        self.assertTrue(bon.reference.startswith(f"BS-{year}-"))

    def test_str_representation(self):
        """__str__ inclut la reference et le nom du projet."""
        bon = BonSortie.objects.create(
            projet=self.projet,
            date_sortie=date(2025, 5, 10),
            responsable="Cheikh Diop",
        )
        self.assertIn(self.projet.nom, str(bon))

    def test_total_lignes(self):
        """total_lignes retourne le nombre de lignes du bon."""
        bon = BonSortie.objects.create(
            projet=self.projet,
            date_sortie=date(2025, 5, 15),
        )
        LigneBonSortie.objects.create(
            bon=bon, materiel=self.materiel,
            quantite=Decimal("5.00"), commentaire="Pour fondation",
        )
        self.assertEqual(bon.total_lignes(), 1)

    def test_ligne_bon_sortie_str(self):
        """__str__ de LigneBonSortie affiche quantite, materiel et projet."""
        bon = BonSortie.objects.create(
            projet=self.projet,
            date_sortie=date(2025, 5, 15),
        )
        ligne = LigneBonSortie.objects.create(
            bon=bon, materiel=self.materiel,
            quantite=Decimal("3.50"),
        )
        self.assertIn("3.50", str(ligne))
        self.assertIn("Sable de mer", str(ligne))


# ═══════════════════════════════════════════════════════════════════════════
# Tests Materiel
# ═══════════════════════════════════════════════════════════════════════════

class MaterielModelTest(DonneesTestMixin, TestCase):
    """Tests du modele Materiel."""

    def test_materiel_str(self):
        """__str__ affiche nom et unite."""
        m = self.creer_materiel(nom="Gravier concasse", unite="m3")
        self.assertEqual(str(m), "Gravier concasse (m3)")

    def test_materiel_nom_unique(self):
        """Le nom du materiel doit etre unique."""
        self.creer_materiel(nom="Ciment Portland", unite="Tonne")
        with self.assertRaises(Exception):
            self.creer_materiel(nom="Ciment Portland", unite="Sac")


# ═══════════════════════════════════════════════════════════════════════════
# Tests MarcheTravaux
# ═══════════════════════════════════════════════════════════════════════════

class MarcheTravauxModelTest(DonneesTestMixin, TestCase):
    """Tests du modele MarcheTravaux (one-to-one avec Projet)."""

    def setUp(self):
        self.projet = self.creer_projet()
        self.marche = MarcheTravaux.objects.create(
            projet=self.projet,
            numero_marche="MT-2025-001",
            objet="Construction villa R+2 Ngor",
            montant_marche=Decimal("65000000.00"),
            montant_avance_demarrage=Decimal("13000000.00"),
            taux_retenue_garantie=Decimal("5.00"),
            penalite_journaliere_pct=Decimal("0.0500"),
            plafond_penalites_pct=Decimal("10.00"),
            date_signature=date(2025, 2, 15),
            date_ordre_service=date(2025, 3, 1),
            delai_execution_jours=365,
            statut="en_cours",
        )

    def test_one_to_one_avec_projet(self):
        """Le marche est accessible via projet.marche."""
        self.assertEqual(self.projet.marche, self.marche)

    def test_str_representation(self):
        """__str__ inclut le numero du marche et le nom du projet."""
        self.assertIn("MT-2025-001", str(self.marche))
        self.assertIn("Villa Ngor", str(self.marche))

    def test_date_fin_prevue(self):
        """date_fin_prevue = date_ordre_service + delai_execution_jours."""
        expected = date(2025, 3, 1) + timedelta(days=365)
        self.assertEqual(self.marche.date_fin_prevue, expected)

    def test_retenue_garantie_montant(self):
        """retenue_garantie = 5% de 65M = 3 250 000 FCFA."""
        self.assertEqual(
            self.marche.retenue_garantie_montant,
            Decimal("3250000.00")
        )

    def test_plafond_penalites(self):
        """plafond_penalites = 10% de 65M = 6 500 000 FCFA."""
        self.assertEqual(
            self.marche.plafond_penalites_montant,
            Decimal("6500000.00")
        )

    def test_validation_reception_avant_signature(self):
        """La reception provisoire ne peut preceder la signature."""
        self.marche.date_reception_provisoire = date(2025, 1, 1)
        with self.assertRaises(ValidationError) as ctx:
            self.marche.clean()
        self.assertIn("date_reception_provisoire", ctx.exception.message_dict)


# ═══════════════════════════════════════════════════════════════════════════
# Tests CompteComptable & EcritureComptable
# ═══════════════════════════════════════════════════════════════════════════

class CompteComptableModelTest(TestCase):
    """Tests du modele CompteComptable."""

    def test_str_representation(self):
        """__str__ affiche code + libelle."""
        compte = CompteComptable.objects.create(
            code="601000",
            libelle="Achats matieres premieres",
            type_compte="charge",
            classe=6,
        )
        self.assertEqual(str(compte), "601000 — Achats matieres premieres")


class EcritureComptableModelTest(DonneesTestMixin, TestCase):
    """Tests du modele EcritureComptable avec equilibre debit/credit."""

    def setUp(self):
        self.compte_achat = CompteComptable.objects.create(
            code="601000", libelle="Achats", type_compte="charge", classe=6,
        )
        self.compte_fournisseur = CompteComptable.objects.create(
            code="401000", libelle="Fournisseurs", type_compte="passif", classe=4,
        )

    def test_auto_numero_piece(self):
        """Le numero_piece est auto-genere au format EC-YYYY-NNNNN."""
        ecriture = EcritureComptable.objects.create(
            date_ecriture=date(2025, 5, 1),
            libelle="Achat test",
            journal="AC",
        )
        year = timezone.now().year
        self.assertTrue(ecriture.numero_piece.startswith(f"EC-{year}-"))

    def test_ecriture_equilibree(self):
        """est_equilibree = True quand total_debit == total_credit."""
        ecriture = EcritureComptable.objects.create(
            date_ecriture=date(2025, 5, 1),
            libelle="Achat materiaux test",
            journal="AC",
        )
        LigneEcriture.objects.create(
            ecriture=ecriture, compte=self.compte_achat,
            debit=Decimal("1000000"), credit=0,
        )
        LigneEcriture.objects.create(
            ecriture=ecriture, compte=self.compte_fournisseur,
            debit=0, credit=Decimal("1000000"),
        )
        self.assertTrue(ecriture.est_equilibree)
        self.assertEqual(ecriture.total_debit, Decimal("1000000"))
        self.assertEqual(ecriture.total_credit, Decimal("1000000"))

    def test_ecriture_non_equilibree(self):
        """est_equilibree = False quand debit != credit."""
        ecriture = EcritureComptable.objects.create(
            date_ecriture=date(2025, 5, 2),
            libelle="Ecriture desequilibree",
            journal="AC",
        )
        LigneEcriture.objects.create(
            ecriture=ecriture, compte=self.compte_achat,
            debit=Decimal("500000"), credit=0,
        )
        LigneEcriture.objects.create(
            ecriture=ecriture, compte=self.compte_fournisseur,
            debit=0, credit=Decimal("300000"),
        )
        self.assertFalse(ecriture.est_equilibree)

    def test_ligne_ecriture_str(self):
        """__str__ de LigneEcriture affiche le code du compte et les montants."""
        ecriture = EcritureComptable.objects.create(
            date_ecriture=date(2025, 5, 3),
            libelle="Test str",
            journal="OD",
        )
        ligne = LigneEcriture.objects.create(
            ecriture=ecriture, compte=self.compte_achat,
            debit=Decimal("750000"), credit=0,
        )
        self.assertIn("601000", str(ligne))
        self.assertIn("D:", str(ligne))


# ═══════════════════════════════════════════════════════════════════════════
# Tests CompteBancaire & TransactionBancaire
# ═══════════════════════════════════════════════════════════════════════════

class CompteBancaireModelTest(DonneesTestMixin, TestCase):
    """Tests du modele CompteBancaire avec solde_actuel."""

    def test_str_representation(self):
        """__str__ affiche le nom et le type du compte."""
        compte = CompteBancaire.objects.create(
            nom="CBAO Compte courant",
            type_compte="banque",
            banque="CBAO Groupe Attijariwafa",
            solde_initial=Decimal("10000000.00"),
        )
        self.assertIn("CBAO", str(compte))
        self.assertIn("Compte bancaire", str(compte))

    def test_solde_actuel_avec_transactions(self):
        """solde_actuel = solde_initial + entrees - sorties."""
        compte = CompteBancaire.objects.create(
            nom="BOA Compte projet",
            type_compte="banque",
            banque="BOA Senegal",
            solde_initial=Decimal("5000000.00"),
        )
        TransactionBancaire.objects.create(
            compte=compte,
            type_transaction="entree",
            montant=Decimal("3000000.00"),
            date_transaction=date(2025, 4, 1),
            libelle="Versement client Diallo",
        )
        TransactionBancaire.objects.create(
            compte=compte,
            type_transaction="sortie",
            montant=Decimal("1500000.00"),
            date_transaction=date(2025, 4, 5),
            libelle="Paiement SOCOCIM",
        )
        # 5M + 3M - 1.5M = 6.5M
        self.assertEqual(compte.solde_actuel, Decimal("6500000.00"))

    def test_solde_actuel_sans_transactions(self):
        """Sans transactions, solde_actuel = solde_initial."""
        compte = CompteBancaire.objects.create(
            nom="Wave Business",
            type_compte="mobile_money",
            banque="Wave",
            solde_initial=Decimal("500000.00"),
        )
        self.assertEqual(compte.solde_actuel, Decimal("500000.00"))

    def test_transaction_str(self):
        """__str__ de TransactionBancaire affiche type, montant et libelle."""
        compte = CompteBancaire.objects.create(
            nom="Caisse chantier",
            type_compte="caisse",
            solde_initial=Decimal("200000.00"),
        )
        tx = TransactionBancaire.objects.create(
            compte=compte,
            type_transaction="sortie",
            montant=Decimal("50000.00"),
            date_transaction=date(2025, 5, 1),
            libelle="Achat consommables",
        )
        self.assertIn("Sortie", str(tx))
        self.assertIn("50000", str(tx))


# ═══════════════════════════════════════════════════════════════════════════
# Tests Documents BTP
# ═══════════════════════════════════════════════════════════════════════════

class DocumentBTPModelTest(DonneesTestMixin, TestCase):
    """Tests des modeles DocumentProjet, BordereauPrix, LigneBordereau, DecompteGD."""

    def setUp(self):
        self.projet = self.creer_projet()

    def test_document_projet_str(self):
        """__str__ de DocumentProjet affiche type et titre."""
        doc = DocumentProjet.objects.create(
            projet=self.projet,
            type_document="pv_reunion",
            titre="PV reunion de chantier n12",
            date_document=date(2025, 5, 1),
            fichier="documents_btp/pv_12.pdf",
        )
        self.assertIn("PV de réunion", str(doc))
        self.assertIn("reunion de chantier", str(doc))

    def test_bordereau_total_ht(self):
        """total_ht d'un bordereau = somme(quantite * prix_unitaire)."""
        bdp = BordereauPrix.objects.create(
            projet=self.projet,
            numero="BDP-001",
            version=1,
            date_edition=date(2025, 3, 15),
        )
        LigneBordereau.objects.create(
            bordereau=bdp,
            numero_prix="1.1",
            designation="Terrassement en pleine masse",
            unite="m3",
            quantite=Decimal("150.000"),
            prix_unitaire=Decimal("12000.00"),
        )
        LigneBordereau.objects.create(
            bordereau=bdp,
            numero_prix="1.2",
            designation="Beton de proprete dose 150kg/m3",
            unite="m3",
            quantite=Decimal("8.000"),
            prix_unitaire=Decimal("95000.00"),
        )
        # 150 * 12000 + 8 * 95000 = 1 800 000 + 760 000 = 2 560 000
        self.assertEqual(bdp.total_ht, Decimal("2560000.000"))

    def test_ligne_bordereau_montant_total(self):
        """montant_total d'une ligne = quantite * prix_unitaire."""
        bdp = BordereauPrix.objects.create(
            projet=self.projet,
            numero="BDP-002",
            version=1,
            date_edition=date(2025, 3, 20),
        )
        ligne = LigneBordereau.objects.create(
            bordereau=bdp,
            numero_prix="2.1",
            designation="Acier HA en fondation",
            unite="kg",
            quantite=Decimal("2500.000"),
            prix_unitaire=Decimal("1200.00"),
        )
        self.assertEqual(ligne.montant_total, Decimal("3000000.000"))

    def test_decompte_gd_proprietes(self):
        """DecompteGD : montant_total, deductions, solde_a_payer."""
        dgd = DecompteGD.objects.create(
            projet=self.projet,
            montant_travaux=Decimal("60000000.00"),
            montant_avenants=Decimal("5000000.00"),
            montant_penalites=Decimal("1000000.00"),
            montant_retenue_garantie=Decimal("3250000.00"),
            montant_avances=Decimal("13000000.00"),
            montant_acomptes=Decimal("40000000.00"),
        )
        # montant_total = 60M + 5M = 65M
        self.assertEqual(dgd.montant_total, Decimal("65000000.00"))
        # deductions = 1M + 3.25M = 4.25M
        self.assertEqual(dgd.deductions, Decimal("4250000.00"))
        # solde = 65M - 4.25M - 13M - 40M = 7.75M
        self.assertEqual(dgd.solde_a_payer, Decimal("7750000.00"))

    def test_decompte_gd_str(self):
        """__str__ du DGD inclut le nom du projet."""
        dgd = DecompteGD.objects.create(
            projet=self.projet,
            montant_travaux=Decimal("50000000.00"),
        )
        self.assertIn("Villa Ngor", str(dgd))


# ═══════════════════════════════════════════════════════════════════════════
# Tests ProfilUtilisateur
# ═══════════════════════════════════════════════════════════════════════════

class ProfilUtilisateurModelTest(DonneesTestMixin, TestCase):
    """Tests du modele ProfilUtilisateur."""

    def test_role_choices(self):
        """Tous les roles sont disponibles."""
        roles_attendus = {"direction", "comptable", "chef_chantier", "gestionnaire", "admin"}
        roles_existants = {code for code, _ in ProfilUtilisateur.ROLE_CHOICES}
        self.assertEqual(roles_attendus, roles_existants)

    def test_str_representation(self):
        """__str__ affiche le nom complet et le role."""
        user = User.objects.create_user(
            username="mdiallo", password="test1234",
            first_name="Mamadou", last_name="Diallo",
        )
        profil = ProfilUtilisateur.objects.create(
            user=user, role="comptable",
        )
        self.assertIn("Diallo", str(profil))
        self.assertIn("Comptable", str(profil))

    def test_est_direction(self):
        """est_direction = True pour direction et admin."""
        user_dir = User.objects.create_user(username="dir", password="test1234")
        profil_dir = ProfilUtilisateur.objects.create(user=user_dir, role="direction")
        self.assertTrue(profil_dir.est_direction)

        user_admin = User.objects.create_user(username="adm", password="test1234")
        profil_admin = ProfilUtilisateur.objects.create(user=user_admin, role="admin")
        self.assertTrue(profil_admin.est_direction)

    def test_est_comptable(self):
        """est_comptable = True pour comptable, direction et admin."""
        user = User.objects.create_user(username="compta", password="test1234")
        profil = ProfilUtilisateur.objects.create(user=user, role="comptable")
        self.assertTrue(profil.est_comptable)

    def test_est_chef_chantier(self):
        """est_chef_chantier = True seulement pour chef_chantier."""
        user = User.objects.create_user(username="chef", password="test1234")
        profil = ProfilUtilisateur.objects.create(user=user, role="chef_chantier")
        self.assertTrue(profil.est_chef_chantier)

        user2 = User.objects.create_user(username="compta2", password="test1234")
        profil2 = ProfilUtilisateur.objects.create(user=user2, role="comptable")
        self.assertFalse(profil2.est_chef_chantier)


# ═══════════════════════════════════════════════════════════════════════════
# Tests Projet avec Achats et Versements (proprietes calculees)
# ═══════════════════════════════════════════════════════════════════════════

class ProjetProprietesCalculeesTest(DonneesTestMixin, TestCase):
    """Tests des proprietes calculees du projet avec des donnees liees."""

    def setUp(self):
        self.projet = self.creer_projet()
        self.categorie = self.creer_categorie_materiel(nom="Materiaux de base")
        self.ciment = self.creer_materiel(
            nom="Ciment CEM test", unite="Tonne", categorie=self.categorie,
        )
        self.phase = self.creer_phase_versement(self.projet, "Phase test")

    def test_total_achats_ht_avec_achats(self):
        """total_achats_ht calcule la somme des achats HT."""
        achat = Achat(
            date_achat=date(2025, 5, 1),
            projet=self.projet,
            mode_paiement="espèces",
            tva_active=False,
        )
        achat.save()
        LigneAchat.objects.create(
            achat=achat, materiel=self.ciment,
            quantite=10, prix_unitaire=Decimal("85000"),
        )
        achat.save()  # trigger calcul_totaux
        self.assertEqual(self.projet.total_achats_ht, Decimal("850000"))

    def test_total_versements_avec_versements(self):
        """total_versements calcule la somme des versements clients."""
        Versement.objects.create(
            projet=self.projet, phase=self.phase,
            montant=Decimal("5000000.00"),
            date_versement=date(2025, 4, 1),
            type_versement="virement bancaire",
        )
        Versement.objects.create(
            projet=self.projet, phase=self.phase,
            montant=Decimal("3000000.00"),
            date_versement=date(2025, 5, 1),
            type_versement="espèces",
        )
        self.assertEqual(self.projet.total_versements, Decimal("8000000.00"))

    def test_marge_brute_et_taux(self):
        """marge_brute = versements - depenses ; taux_marge en %."""
        # Versement de 10M
        Versement.objects.create(
            projet=self.projet, phase=self.phase,
            montant=Decimal("10000000.00"),
            date_versement=date(2025, 4, 1),
            type_versement="virement bancaire",
        )
        # Achat de 4M TTC
        achat = Achat(
            date_achat=date(2025, 5, 1),
            projet=self.projet,
            mode_paiement="espèces",
            tva_active=False,
        )
        achat.save()
        LigneAchat.objects.create(
            achat=achat, materiel=self.ciment,
            quantite=40, prix_unitaire=Decimal("100000"),
        )
        achat.save()

        # marge = 10M - 4M = 6M
        self.assertEqual(self.projet.marge_brute_estimee, Decimal("6000000.00"))
        # taux = 6M / 10M * 100 = 60%
        self.assertEqual(self.projet.taux_marge, Decimal("60.00"))
