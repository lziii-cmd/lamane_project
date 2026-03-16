# core/forms/proprietaire_form.py
from django import forms
from core.models.proprietaire import Proprietaire

class ProprietaireForm(forms.ModelForm):
    class Meta:
        model = Proprietaire
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        est_moral = cleaned_data.get('est_moral')

        # Champs entreprise
        entreprise = cleaned_data.get('entreprise')
        ninea = cleaned_data.get('ninea')

        # Champs personne physique
        prenom = cleaned_data.get('prenom')
        nom = cleaned_data.get('nom')
        numero_identite = cleaned_data.get('numero_identite')
        sexe = cleaned_data.get('sexe')

        if est_moral:
            # Cas entreprise
            if not entreprise:
                self.add_error('entreprise', "Le nom de l'entreprise est requis.")
            if not ninea:
                self.add_error('ninea', "Le NINEA est requis.")
            # Ne doit pas remplir les champs personne
            if prenom or nom or numero_identite or sexe:
                raise forms.ValidationError("Ne remplissez pas les champs de personne physique si le client est une entreprise.")
        else:
            # Cas personne physique
            if not prenom:
                self.add_error('prenom', "Le prénom est requis.")
            if not nom:
                self.add_error('nom', "Le nom est requis.")
            if not numero_identite:
                self.add_error('numero_identite', "Le numéro de pièce est requis.")
            if not sexe:
                self.add_error('sexe', "Le sexe est requis.")
            # Ne doit pas remplir les champs entreprise
            if entreprise or ninea:
                raise forms.ValidationError("Ne remplissez pas les champs d’entreprise si le client est une personne physique.")
