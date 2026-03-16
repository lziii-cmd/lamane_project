# core/admin/categorie_materiel_admin.py
from django.contrib import admin
from core.models.categorie_materiel import CategorieMateriel

@admin.register(CategorieMateriel)
class CategorieMaterielAdmin(admin.ModelAdmin):
    list_display = ('nom', 'date_creation', 'date_modification')
    search_fields = ('nom',)
    ordering = ('nom',)
