# core/admin/employe_admin.py
from django.contrib import admin
from core.models.employe import Employe
from core.models.projet_employe import ProjetEmploye


class ProjetAffectationInline(admin.TabularInline):
    model = ProjetEmploye
    extra = 0
    fields = (
        "projet",
        "role",
        "date_affectation",
        "date_fin",
        "actif",
        "contrat",
        "observation",
    )
    readonly_fields = fields
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Employe)
class EmployeAdmin(admin.ModelAdmin):
    list_display = ("matricule", "nom", "prenom", "poste", "actif")
    search_fields = ("matricule", "nom", "prenom", "poste")
    readonly_fields = ("matricule",)
    inlines = [ProjetAffectationInline]
