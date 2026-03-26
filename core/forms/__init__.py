"""
core/forms/__init__.py — Tous les formulaires LAMANE BTP
Importe les formulaires des sous-modules existants +
expose les nouveaux formulaires CRUD définis ici.
"""
from .proprietaire_form import ProprietaireForm
from .projet_form import ProjetForm
from .fournisseur_form import FournisseurForm

from django import forms
from django.forms import inlineformset_factory

from core.models import (
    TypeProjet, Employe,
    Achat, LigneAchat, Materiel, CategorieMateriel,
    Versement, PhaseVersement, EtapeStandard,
    MarcheTravaux, AvancementChantier,
    SousTraitant, ContratSousTraitance,
    BonSortie, LigneBonSortie,
    CompteComptable, EcritureComptable, LigneEcriture,
    CompteBancaire, TransactionBancaire,
    DocumentProjet, BordereauPrix, LigneBordereau, DecompteGD,
    ProfilUtilisateur,
)


# ─── CLASSE DE BASE ────────────────────────────────────────────────────────────

class LamaneForm(forms.ModelForm):
    """Base form with consistent widget styling for all LAMANE forms."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            widget = field.widget
            base_class = "form-input"
            if isinstance(widget, forms.Select):
                widget.attrs.update({"class": f"{base_class} form-select"})
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs.update({"class": "form-checkbox"})
            elif isinstance(widget, forms.Textarea):
                widget.attrs.update({"class": f"{base_class} form-textarea", "rows": 3})
            elif isinstance(widget, forms.FileInput):
                widget.attrs.update({"class": "form-file"})
            else:
                widget.attrs.update({"class": base_class})


# ─── TYPE DE PROJET ────────────────────────────────────────────────────────────

class TypeProjetForm(LamaneForm):
    class Meta:
        model = TypeProjet
        fields = ["nom", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["description"].required = False


# ─── EMPLOYE ───────────────────────────────────────────────────────────────────

class EmployeForm(LamaneForm):
    class Meta:
        model = Employe
        fields = [
            "prenom", "nom", "sexe", "telephone", "email",
            "poste", "date_embauche", "adresse", "actif",
        ]
        widgets = {
            "date_embauche": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ["sexe", "telephone", "email", "adresse", "date_embauche"]:
            if f in self.fields:
                self.fields[f].required = False


# ─── ETAPE STANDARD ──────────────────────────────────────────────────────────

class EtapeStandardForm(LamaneForm):
    class Meta:
        model = EtapeStandard
        fields = ["nom", "ordre", "groupe", "multi_niveau"]


# ─── PHASE DE VERSEMENT ──────────────────────────────────────────────────────

class PhaseVersementForm(LamaneForm):
    class Meta:
        model = PhaseVersement
        fields = ["projet", "etape_standard", "libelle", "niveau", "montant_prevu", "echeance", "ordre"]
        widgets = {
            "echeance": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["etape_standard"].required = False
        self.fields["libelle"].required = False
        self.fields["niveau"].required = False
        self.fields["echeance"].required = False


# ─── CATEGORIE MATERIAU ────────────────────────────────────────────────────────

class CategorieMaterielForm(LamaneForm):
    class Meta:
        model = CategorieMateriel
        fields = ["nom"]


# ─── MATERIAU ──────────────────────────────────────────────────────────────────

class MaterielForm(LamaneForm):
    class Meta:
        model = Materiel
        fields = ["nom", "unite", "categorie"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categorie"].required = False


# ─── ACHAT ─────────────────────────────────────────────────────────────────────

class AchatForm(LamaneForm):
    class Meta:
        model = Achat
        fields = [
            "date_achat", "projet", "fournisseur",
            "mode_paiement", "numero_facture",
            "fichier_facture", "tva_active",
        ]
        widgets = {
            "date_achat": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fournisseur"].required = False
        self.fields["numero_facture"].required = False
        self.fields["fichier_facture"].required = False


class LigneAchatForm(LamaneForm):
    class Meta:
        model = LigneAchat
        fields = ["materiel", "quantite", "prix_unitaire", "commentaire"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["commentaire"].required = False


LigneAchatFormSet = inlineformset_factory(
    Achat, LigneAchat,
    form=LigneAchatForm,
    fields=["materiel", "quantite", "prix_unitaire", "commentaire"],
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


# ─── VERSEMENT ─────────────────────────────────────────────────────────────────

class VersementForm(LamaneForm):
    class Meta:
        model = Versement
        fields = [
            "projet", "phase", "etape",
            "montant", "date_versement",
            "type_versement", "reference_paiement",
            "fichier_justificatif",
        ]
        widgets = {
            "date_versement": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["etape"].required = False
        self.fields["reference_paiement"].required = False
        self.fields["fichier_justificatif"].required = False


# ─── MARCHÉ DE TRAVAUX ─────────────────────────────────────────────────────────

class MarcheTravauxForm(LamaneForm):
    class Meta:
        model = MarcheTravaux
        fields = [
            "projet", "numero_marche", "objet",
            "montant_marche", "montant_avance_demarrage",
            "taux_retenue_garantie", "penalite_journaliere_pct",
            "date_signature", "date_ordre_service",
            "delai_execution_jours", "statut",
            "date_reception_provisoire", "date_reception_definitive",
            "observations",
        ]
        widgets = {
            "date_signature": forms.DateInput(attrs={"type": "date"}),
            "date_ordre_service": forms.DateInput(attrs={"type": "date"}),
            "date_reception_provisoire": forms.DateInput(attrs={"type": "date"}),
            "date_reception_definitive": forms.DateInput(attrs={"type": "date"}),
            "objet": forms.Textarea(attrs={"rows": 2}),
            "observations": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ["objet", "date_signature", "date_ordre_service",
                  "date_reception_provisoire", "date_reception_definitive",
                  "observations", "montant_avance_demarrage"]:
            if f in self.fields:
                self.fields[f].required = False


# ─── AVANCEMENT CHANTIER ───────────────────────────────────────────────────────

class AvancementChantierForm(LamaneForm):
    class Meta:
        model = AvancementChantier
        fields = [
            "projet", "periode",
            "taux_physique", "taux_financier", "taux_planifie",
            "effectif_ouvriers", "effectif_encadrement",
            "observations",
        ]
        widgets = {
            "periode": forms.DateInput(attrs={"type": "date"}),
            "observations": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ["observations", "effectif_ouvriers", "effectif_encadrement"]:
            if f in self.fields:
                self.fields[f].required = False


# ─── SOUS-TRAITANT ─────────────────────────────────────────────────────────────

class SousTraitantForm(LamaneForm):
    class Meta:
        model = SousTraitant
        fields = ["nom", "specialite", "contact_nom", "adresse", "actif"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ["specialite", "contact_nom", "adresse"]:
            if f in self.fields:
                self.fields[f].required = False


# ─── CONTRAT SOUS-TRAITANCE ────────────────────────────────────────────────────

class ContratSousTraitanceForm(LamaneForm):
    class Meta:
        model = ContratSousTraitance
        fields = [
            "sous_traitant", "projet", "lot",
            "montant", "montant_paye",
            "date_debut", "date_fin_prevue", "statut",
            "observations",
        ]
        widgets = {
            "date_debut": forms.DateInput(attrs={"type": "date"}),
            "date_fin_prevue": forms.DateInput(attrs={"type": "date"}),
            "observations": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ["date_fin_prevue", "observations", "montant_paye"]:
            if f in self.fields:
                self.fields[f].required = False


# ─── BON DE SORTIE ─────────────────────────────────────────────────────────────

class BonSortieForm(LamaneForm):
    class Meta:
        model = BonSortie
        fields = ["projet", "date_sortie", "responsable", "observations"]
        widgets = {
            "date_sortie": forms.DateInput(attrs={"type": "date"}),
            "observations": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["responsable"].required = False
        self.fields["observations"].required = False


class LigneBonSortieForm(LamaneForm):
    class Meta:
        model = LigneBonSortie
        fields = ["materiel", "quantite", "commentaire"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["commentaire"].required = False


LigneBonSortieFormSet = inlineformset_factory(
    BonSortie, LigneBonSortie,
    form=LigneBonSortieForm,
    fields=["materiel", "quantite", "commentaire"],
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


# ─── COMPTABILITE ─────────────────────────────────────────────────────────

class CompteComptableForm(LamaneForm):
    class Meta:
        model = CompteComptable
        fields = ["code", "libelle", "type_compte", "classe", "actif"]


class EcritureComptableForm(LamaneForm):
    class Meta:
        model = EcritureComptable
        fields = ["date_ecriture", "libelle", "journal", "projet"]
        widgets = {
            "date_ecriture": forms.DateInput(attrs={"type": "date"}),
        }


class LigneEcritureForm(LamaneForm):
    class Meta:
        model = LigneEcriture
        fields = ["compte", "libelle", "debit", "credit"]


LigneEcritureFormSet = inlineformset_factory(
    EcritureComptable, LigneEcriture,
    form=LigneEcritureForm,
    fields=["compte", "libelle", "debit", "credit"],
    extra=4,
    can_delete=True,
    min_num=2,
    validate_min=True,
)


# ─── COMPTES BANCAIRES ───────────────────────────────────────────────────

class CompteBancaireForm(LamaneForm):
    class Meta:
        model = CompteBancaire
        fields = ["nom", "type_compte", "banque", "numero_compte", "solde_initial", "actif"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["banque"].required = False
        self.fields["numero_compte"].required = False


class TransactionBancaireForm(LamaneForm):
    class Meta:
        model = TransactionBancaire
        fields = [
            "compte", "type_transaction", "montant",
            "date_transaction", "libelle", "projet",
            "compte_destination",
        ]
        widgets = {
            "date_transaction": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["projet"].required = False
        self.fields["compte_destination"].required = False


# ─── DOCUMENTS BTP ────────────────────────────────────────────────────────

class DocumentProjetForm(LamaneForm):
    class Meta:
        model = DocumentProjet
        fields = ["projet", "type_document", "titre", "description",
                  "fichier", "date_document"]
        widgets = {
            "date_document": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["description"].required = False


class BordereauPrixForm(LamaneForm):
    class Meta:
        model = BordereauPrix
        fields = ["projet", "numero", "version", "date_edition", "statut"]
        widgets = {
            "date_edition": forms.DateInput(attrs={"type": "date"}),
        }


class LigneBordereauForm(LamaneForm):
    class Meta:
        model = LigneBordereau
        fields = ["numero_prix", "designation", "unite", "quantite", "prix_unitaire"]


LigneBordereauFormSet = inlineformset_factory(
    BordereauPrix, LigneBordereau,
    form=LigneBordereauForm,
    fields=["numero_prix", "designation", "unite", "quantite", "prix_unitaire"],
    extra=5,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class DecompteGDForm(LamaneForm):
    class Meta:
        model = DecompteGD
        fields = [
            "projet", "marche",
            "montant_travaux", "montant_avenants",
            "montant_penalites", "montant_retenue_garantie",
            "montant_avances", "montant_acomptes",
            "observations",
        ]
        widgets = {
            "observations": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["marche"].required = False
        self.fields["observations"].required = False


# ─── PROFIL UTILISATEUR ──────────────────────────────────────────────────

class ProfilUtilisateurForm(LamaneForm):
    class Meta:
        model = ProfilUtilisateur
        fields = ["role", "telephone", "photo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["telephone"].required = False
        self.fields["photo"].required = False
