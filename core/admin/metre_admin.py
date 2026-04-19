# core/admin/metre_admin.py
from django.contrib import admin
from core.models import Devis, LotMetre, TypeElement, PlanMetre, TraceMetre


@admin.register(Devis)
class DevisAdmin(admin.ModelAdmin):
    list_display = ("reference", "titre", "client_nom", "statut", "date_creation")
    list_filter = ("statut",)
    search_fields = ("reference", "titre", "client_nom")


@admin.register(LotMetre)
class LotMetreAdmin(admin.ModelAdmin):
    list_display = ("code", "nom", "ordre")
    list_editable = ("ordre",)
    search_fields = ("nom", "code")


@admin.register(TypeElement)
class TypeElementAdmin(admin.ModelAdmin):
    list_display = ("nom", "lot", "unite", "outil", "couleur", "prix_unitaire", "actif", "ordre")
    list_editable = ("ordre", "actif")
    list_filter = ("lot", "unite", "outil", "actif")
    search_fields = ("nom",)


@admin.register(PlanMetre)
class PlanMetreAdmin(admin.ModelAdmin):
    list_display = ("nom", "projet", "ordre", "echelle_definie")
    list_filter = ("projet",)
    search_fields = ("nom",)

    def echelle_definie(self, obj):
        return obj.echelle_definie
    echelle_definie.boolean = True
    echelle_definie.short_description = "Echelle OK"


@admin.register(TraceMetre)
class TraceMetreAdmin(admin.ModelAdmin):
    list_display = ("type_element", "plan", "quantite", "longueur_metres", "surface_metres")
    list_filter = ("type_element", "plan__projet")
    readonly_fields = ("longueur_metres", "surface_metres", "volume_metres", "quantite")
