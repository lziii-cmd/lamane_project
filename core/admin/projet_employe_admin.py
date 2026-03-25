# core/admin/projet_employe_admin.py
from django.contrib import admin
from core.models.projet_employe import ProjetEmploye


@admin.register(ProjetEmploye)
class ProjetEmployeAdmin(admin.ModelAdmin):
    list_display = (
        "projet",
        "employe",
        "role",
        "date_affectation",
        "date_fin",
        "actif",
    )
    list_filter = ("projet", "employe", "actif")
    search_fields = ("projet__nom", "employe__nom", "employe__prenom", "role")
