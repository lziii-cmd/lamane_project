# core/admin/fournisseur_admin.py
from django.contrib import admin
from core.models.fournisseur import Fournisseur
from core.forms.fournisseur_form import FournisseurForm

@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    form = FournisseurForm

    list_display = ("__str__", "telephone", "email")
    search_fields = (
        "entreprise", "ninea",
        "prenom", "nom", "numero_identite",
        "telephone", "email"
    )

    fieldsets = (
        ("Type de fournisseur", {
            "fields": ("est_moral",),
        }),
        ("Informations Entreprise", {
            "fields": ("entreprise", "ninea"),
        }),
        ("Personne Physique", {
            "fields": ("prenom", "nom", "sexe", "numero_identite"),
        }),
        ("Coordonnées & Pièce", {
            "fields": ("telephone", "email", "adresse", "photo_identite"),
        }),
    )

    class Media:
        js = ("js/fournisseur_admin.js",)
