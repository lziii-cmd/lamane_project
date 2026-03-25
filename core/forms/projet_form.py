# core/forms/projet_form.py
from django import forms
from core.models.projet import Projet

class ProjetForm(forms.ModelForm):
    """
    Formulaire ModelForm personnalisé pour le modèle Projet,
    permettant la validation conditionnelle des champs
    en fonction des choix utilisateur (ex: piscine, ascenseur...).
    """

    class Meta:
        model = Projet
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()

        # Validation piscine
        a_piscine = cleaned_data.get('a_piscine')
        volume_piscine = cleaned_data.get('volume_piscine')
        if a_piscine and not volume_piscine:
            self.add_error('volume_piscine', "Veuillez renseigner le volume de la piscine.")

        if not a_piscine:
            cleaned_data['volume_piscine'] = None

        # Validation ascenseur
        a_ascenseur = cleaned_data.get('a_ascenseur')
        nombre_ascenseurs = cleaned_data.get('nombre_ascenseurs')
        if a_ascenseur and not nombre_ascenseurs:
            self.add_error('nombre_ascenseurs', "Veuillez renseigner le nombre d’ascenseurs.")
        if not a_ascenseur:
            cleaned_data['nombre_ascenseurs'] = None

        # Validation climatisation
        a_climatisation = cleaned_data.get('a_climatisation')
        nombre_clims = cleaned_data.get('nombre_clims')
        if a_climatisation and not nombre_clims:
            self.add_error('nombre_clims', "Veuillez renseigner le nombre de climatiseurs.")
        if not a_climatisation:
            cleaned_data['nombre_clims'] = None

        # Validation panneaux solaires
        a_panneaux_solaires = cleaned_data.get('a_panneaux_solaires')
        puissance_panneaux = cleaned_data.get('puissance_panneaux')
        if a_panneaux_solaires and not puissance_panneaux:
            self.add_error('puissance_panneaux', "Veuillez renseigner la puissance des panneaux solaires.")
        if not a_panneaux_solaires:
            cleaned_data['puissance_panneaux'] = None

        return cleaned_data
