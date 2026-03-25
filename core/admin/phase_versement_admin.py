from django.contrib import admin
from django.forms.models import BaseInlineFormSet

from core.models.phase_versement import PhaseVersement
from core.models.etape_standard import EtapeStandard


class PhaseVersementInlineFormSet(BaseInlineFormSet):
    """
    Aucune dépendance JS pour la 1ʳᵉ ligne.
    Pré-remplit la empty_form et la 1ʳᵉ ligne affichée : Signature + Ordre=1.
    Renumérote proprement à l’enregistrement.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._signature = EtapeStandard.objects.filter(nom__icontains="signature").first()

        # 1) Initialiser le gabarit cloné par "Ajouter..."
        if hasattr(self, "empty_form"):
            if "etape_standard" in self.empty_form.fields and self._signature:
                self.empty_form.fields["etape_standard"].initial = self._signature
            if "ordre" in self.empty_form.fields:
                self.empty_form.fields["ordre"].initial = 1

        # 2) Si aucune instance existante, initialiser aussi la 1ʳᵉ ligne matérielle
        if self.total_form_count() > 0 and self.initial_form_count() == 0:
            f0 = self.forms[0]
            if "etape_standard" in f0.fields and self._signature:
                f0.fields["etape_standard"].initial = self._signature
            if "ordre" in f0.fields:
                f0.fields["ordre"].initial = 1

    def clean(self):
        super().clean()
        forms_ok = []
        for form in self.forms:
            cd = getattr(form, "cleaned_data", None)
            if cd and not cd.get("DELETE", False):
                forms_ok.append(form)

        if not forms_ok:
            return

        # Première ligne : jamais vide
        f0 = forms_ok[0]
        if not f0.cleaned_data.get("etape_standard") and self._signature:
            f0.cleaned_data["etape_standard"] = self._signature
            f0.instance.etape_standard = self._signature
        if not f0.cleaned_data.get("ordre"):
            f0.cleaned_data["ordre"] = 1
            f0.instance.ordre = 1

        # Renumérotation séquentielle 1..n
        forms_ok.sort(key=lambda fr: fr.cleaned_data.get("ordre") or 10**9)
        for idx, form in enumerate(forms_ok, start=1):
            form.cleaned_data["ordre"] = idx
            form.instance.ordre = idx


class PhaseVersementInline(admin.TabularInline):
    model = PhaseVersement
    formset = PhaseVersementInlineFormSet


    # Empêche Django d'insérer une ligne "extra" ou "min_num"
    extra = 0
    #min_num = 0
    classes = ('collapse',)   # ⬅️ inline fermé par défaut (toggle au clic sur le titre)


    fields = ("ordre", "etape_standard", "niveau", "echeance", "montant_prevu")
    ordering = ("ordre",)

    # Ce blindage garantit 0 ligne tant que l’utilisateur n’a pas cliqué
    def get_extra(self, request, obj=None, **kwargs):
        return 0

    def get_min_num(self, request, obj=None, **kwargs):
        return 0


@admin.register(PhaseVersement)
class PhaseVersementAdmin(admin.ModelAdmin):
    list_display = ("projet", "etape_standard", "niveau", "ordre", "echeance", "montant_prevu")
    list_filter = ("projet", "etape_standard")
    search_fields = ("projet__nom", "etape_standard__nom")
    autocomplete_fields = ("projet", "etape_standard")
    ordering = ("projet", "ordre")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("projet", "etape_standard")
