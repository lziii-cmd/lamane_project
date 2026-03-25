"""
core/forms.py — Formulaires CRUD pour toute l'application LAMANE BTP
"""
from django import forms
from django.forms import inlineformset_factory

from core.models import (
    Projet, TypeProjet, Proprietaire, Employe,
    Fournisseur, Achat, LigneAchat, Materiel, CategorieMateriel,
    Versement, PhaseVersement, EtapeStandard,
    MarcheTravaux, AvancementChantier,
    SousTraitant, ContratSousTraitance,
    BonSortie, LigneBonSortie,
)


# ─── CLASSES DE BASE ──────────────────────────────────────────────────────────

class LamaneForm(forms.ModelForm):
    """Base form with consistent styling for all LAMANE forms."""

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


# ─── PROJET ───────────────────────────────────────────────────────────────────

class ProjetForm(LamaneForm):
    class Meta:
        model = Projet
        fields = [
            "nom", "localisation", "statut", "type_projet", "proprietaire",
            "date_debut", "date_fin", "description",
            "cout_estime_lamane",
            "superficie", "surface_batie", "nombre_pieces", "nombre_etages",
            "a_piscine", "volume_piscine",
            "a_ascenseur", "nombre_ascenseurs",
            "a_climatisation", "nombre_clims",
            "a_panneaux_solaires", "puissance_panneaux",
        ]
        widgets = {
            "date_debut": forms.DateInput(attrs={"type": "date"}),
            "date_fin": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["date_fin"].required = False
        self.fields["description"].required = False
        self.fields["type_projet"].required = False
        self.fields["superficie"].required = False
        self.fields["surface_batie"].required = False
        self.fields["nombre_pieces"].required = False
        self.fields["nombre_etages"].required = False
        self.fields["cout_estime_lamane"].required = False


# ─── TYPE DE PROJET ───────────────────────────────────────────────────────────

class TypeProjetForm(LamaneForm):
    class Meta:
        model = TypeProjet
        fields = ["nom", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}


# ─── PROPRIETAIRE (CLIENT) ────────────────────────────────────────────────────

class ProprietaireForm(LamaneForm):
    class Meta:
        model = Proprietaire
        fields = [
            "est_moral", "entreprise", "ninea",
            "prenom", "nom", "numero_identite",
            "telephone", "email", "adresse",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ["entreprise", "ninea", "prenom", "nom",
                  "numero_identite", "email", "adresse"]:
            self.fields[f].required = False


# ─── EMPLOYE ──────────────────────────────────────────────────────────────────

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
            self.fields[f].required = False


# ─── FOURNISSEUR ──────────────────────────────────────────────────────────────

class FournisseurForm(LamaneForm):
    class Meta:
        model = Fournisseur
        fields = [
            "est_moral", "entreprise", "ninea",
            "prenom", "nom", "telephone", "email", "adresse",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ["entreprise", "ninea", "prenom", "nom",
                  "telephone", "email", "adresse"]:
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


# ─── CATEGORIE MATERIAU ───────────────────────────────────────────────────────

class CategorieMaterielForm(LamaneForm):
    class Meta:
        model = CategorieMateriel
        fields = ["nom"]


# ─── MATERIAU ─────────────────────────────────────────────────────────────────

class MaterielForm(LamaneForm):
    class Meta:
        model = Materiel
        fields = ["nom", "unite", "categorie"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categorie"].required = False


# ─── ACHAT ────────────────────────────────────────────────────────────────────

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


# ─── VERSEMENT ────────────────────────────────────────────────────────────────

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


# ─── MARCHÉ DE TRAVAUX ────────────────────────────────────────────────────────

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
            self.fields[f].required = False


# ─── AVANCEMENT CHANTIER ──────────────────────────────────────────────────────

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
        self.fields["observations"].required = False
        self.fields["effectif_ouvriers"].required = False
        self.fields["effectif_encadrement"].required = False


# ─── SOUS-TRAITANT ────────────────────────────────────────────────────────────

class SousTraitantForm(LamaneForm):
    class Meta:
        model = SousTraitant
        fields = ["nom", "specialite", "ninea", "telephone", "email",
                  "contact_nom", "adresse", "actif"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ["specialite", "contact_nom", "adresse", "ninea", "telephone", "email"]:
            if f in self.fields:
                self.fields[f].required = False


# ─── CONTRAT SOUS-TRAITANCE ───────────────────────────────────────────────────

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
        for f in ["date_debut", "date_fin_prevue", "observations", "montant_paye"]:
            if f in self.fields:
                self.fields[f].required = False


# ─── BON DE SORTIE ────────────────────────────────────────────────────────────

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
