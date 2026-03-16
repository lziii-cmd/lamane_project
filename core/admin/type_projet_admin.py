# core/admin/type_projet_admin.py
from django.contrib import admin
from core.models.type_projet import TypeProjet

@admin.register(TypeProjet)
class TypeProjetAdmin(admin.ModelAdmin):
    list_display = ["nom"]
    search_fields = ["nom"]
