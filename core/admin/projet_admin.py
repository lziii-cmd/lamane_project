# core/admin/projet_admin.py
from django.contrib import admin
from django.utils.html import format_html
from core.models.projet import Projet
from core.forms.projet_form import ProjetForm
from django.db.models import Max
from core.models.phase_versement import PhaseVersement
from core.models.etape_standard import EtapeStandard

class PhaseVersementInline(admin.TabularInline):
    model = PhaseVersement
    extra = 0
    fields = ("ordre", "etape_standard", "niveau", "echeance", "montant_prevu")
    ordering = ("ordre",)
    autocomplete_fields = ()  # optionnel si tu actives l'autocomplete
    # Pour que le JS sache à quel groupe d’inlines s’accrocher
    template = "admin/edit_inline/tabular.html"

@admin.register(Projet)
class ProjetAdmin(admin.ModelAdmin):

    inlines = [PhaseVersementInline]

    form = ProjetForm
    list_display = (
        'nom', 'proprietaire_nom', 'localisation',
        'statut', 'date_debut', 'date_fin',
        'a_piscine', 'a_ascenseur', 'a_climatisation'
    )
    list_filter = ('statut', 'a_piscine', 'a_ascenseur', 'a_climatisation', 'a_panneaux_solaires')
    search_fields = ('nom', 'localisation', 'proprietaire__nom', 'proprietaire__entreprise')
    autocomplete_fields = ['proprietaire', 'type_projet']
    readonly_fields = ('date_creation', 'date_modification')

    fieldsets = (
        ('Informations générales', {
            'fields': (
                'nom', 'localisation', 'description',
                'statut', 'date_debut', 'date_fin',
                'proprietaire', 'type_projet'
            )
        }),
        ('Caractéristiques Techniques', {
            'fields': (
                'superficie', 'surface_batie', 'nombre_pieces', 'nombre_etages'
            )
        }),
        ('Options supplémentaires', {
            'fields': (
                'a_piscine', 'volume_piscine',
                'a_ascenseur', 'nombre_ascenseurs',
                'a_climatisation', 'nombre_clims',
                'a_panneaux_solaires', 'puissance_panneaux'
            )
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification')
        })
    )

    def proprietaire_nom(self, obj):
        return obj.proprietaire.nom_complet() if hasattr(obj.proprietaire, 'nom_complet') else obj.proprietaire
    proprietaire_nom.short_description = 'Client'

    class Media:
        js = ('js/projet_admin.js',
#              'js/phasage_generator.js',
              )
