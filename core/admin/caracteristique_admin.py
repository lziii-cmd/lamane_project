from django.contrib import admin
from core.models import Caracteristique

@admin.register(Caracteristique)
class CaracteristiqueAdmin(admin.ModelAdmin):
    list_display = (
        "projet",
        "superficie_totale",
        "surface_batie",
        "piscine",
        "ascenseur",
        "performance_energetique"
    )
    search_fields = ("projet__nom",)
