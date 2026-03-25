# core/admin/proprietaire_admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from core.models.proprietaire import Proprietaire
from core.forms.proprietaire_form import ProprietaireForm

@admin.register(Proprietaire)
class ProprietaireAdmin(admin.ModelAdmin):
    form = ProprietaireForm
    list_display = ('nom_complet', 'telephone', 'email', 'est_moral', 'sexe')
    list_filter = ('est_moral', 'sexe')
    search_fields = ('nom', 'prenom', 'entreprise', 'telephone', 'email')
    fieldsets = (
        (_('Type de client'), {
            'fields': ('est_moral',)
        }),
        (_('Informations Entreprise'), {
            'fields': ('entreprise', 'ninea'),
            'classes': ('collapse',),
        }),
        (_('Informations Personne Physique'), {
            'fields': ('prenom', 'nom', 'numero_identite', 'sexe'),
            'classes': ('collapse',),
        }),
        (_('Coordonnées'), {
            'fields': ('telephone', 'email', 'adresse'),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related()

    def nom_complet(self, obj):
        return obj.nom_complet()
    nom_complet.short_description = 'Nom du client'

    class Media:
        js = ("js/proprietaire_admin.js",)