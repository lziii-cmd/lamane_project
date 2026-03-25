# core/forms/fournisseur_form.py
from django import forms
from core.models.fournisseur import Fournisseur

class FournisseurForm(forms.ModelForm):
    class Meta:
        model = Fournisseur
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        est_moral = cleaned_data.get("est_moral")

        if est_moral:
            if not cleaned_data.get("entreprise"):
                self.add_error("entreprise", "Ce champ est obligatoire pour une entreprise.")
            if not cleaned_data.get("ninea"):
                self.add_error("ninea", "Ce champ est obligatoire pour une entreprise.")
            # Empêcher de remplir les champs de personne
            for field in ["prenom", "nom", "numero_identite", "sexe"]:
                if cleaned_data.get(field):
                    self.add_error(field, "Ce champ ne doit pas être rempli pour une entreprise.")
        else:
            for field in ["prenom", "nom", "numero_identite", "sexe"]:
                if not cleaned_data.get(field):
                    self.add_error(field, "Champ requis pour une personne physique.")
            if cleaned_data.get("entreprise") or cleaned_data.get("ninea"):
                self.add_error("entreprise", "Ne pas remplir ces champs pour une personne physique.")
                self.add_error("ninea", "Ne pas remplir ces champs pour une personne physique.")
