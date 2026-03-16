from django import forms
from django.forms import formset_factory
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from core.models.etape_standard import EtapeStandard

class GenerationPhasesHeaderForm(forms.Form):
    phase_standard = forms.ModelChoiceField(
        label=_("Étape standard"),
        queryset=EtapeStandard.objects.all().order_by("ordre", "nom"),
        help_text=_("Si l’étape est multi-niveau, vous pourrez saisir des niveaux (R+0, R+1, S-1...).")
    )
    nb_lignes = forms.IntegerField(
        label=_("Nombre de lignes à saisir"),
        min_value=1, initial=6,
        help_text=_("Vous indiquerez ensuite niveau (optionnel), échéance (facultative) et montant (requis) pour chaque ligne.")
    )

class GenerationPhasesRowForm(forms.Form):
    niveau = forms.IntegerField(
        required=False, label=_("Niveau (ex. 0=R+0, 1=R+1, -1=S-1)")
    )
    echeance = forms.DateField(
        required=False, label=_("Échéance"), widget=forms.DateInput(attrs={"type": "date"})
    )
    montant_prevu = forms.DecimalField(
        required=True, label=_("Montant prévu (XOF)"),
        min_value=Decimal("0.00"), decimal_places=2
    )
    ordre = forms.IntegerField(required=False, label=_("Ordre (optionnel)"))

GenerationPhasesRowFormSet = formset_factory(GenerationPhasesRowForm, extra=0, can_delete=False)
