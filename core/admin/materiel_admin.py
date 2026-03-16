# core/admin/materiel_admin.py
from django.contrib import admin
from core.models.materiel import Materiel

@admin.register(Materiel)
class MaterielAdmin(admin.ModelAdmin):
    list_display = ('nom', 'categorie', 'unite')
    list_filter = ('categorie',)
    search_fields = ('nom', 'unite')
