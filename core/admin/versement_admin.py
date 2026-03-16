# core/admin/versement_admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from core.models.versement import Versement


@admin.register(Versement)
class VersementAdmin(admin.ModelAdmin):
    list_display = (
        'libelle',
        'get_nom_projet',
        'get_nom_client',
        'get_etape',
        'montant_aff',
        'date_versement',
        'type_versement',
        'facture_link',
    )
    list_filter = (
        'date_versement',
        'type_versement',
        'projet__proprietaire__est_moral',
        'etape__nom',
        'phase__libelle',
    )
    search_fields = (
        'projet__nom',
        'projet__proprietaire__nom',
        'projet__proprietaire__entreprise',
        'phase__libelle',
        'etape__nom',
    )
    autocomplete_fields = ['projet', 'phase', 'etape']
    readonly_fields = ['libelle', 'numero_facture', 'facture_pdf']
    ordering = ['-date_versement']

    fieldsets = (
        (None, {
            'fields': (
                'projet',
                'phase',
                'etape',
                'montant',
                'date_versement',
                'type_versement',
                'fichier_justificatif',
                'facture_pdf',
            )
        }),
        ('Données système', {
            'classes': ('collapse',),
            'fields': ('libelle','numero_facture',),

        }),
    )

    def get_nom_projet(self, obj):
        return obj.projet.nom
    get_nom_projet.short_description = 'Projet'

    def get_nom_client(self, obj):
        return obj.projet.proprietaire.nom_complet()
    get_nom_client.short_description = 'Client'

    def get_etape(self, obj):
        return obj.etape.nom if obj.etape else "-"
    get_etape.short_description = 'Étape'

    def montant_aff(self, obj):
        return f"{int(obj.montant):,}".replace(",", " ") + " FCFA"
    montant_aff.short_description = "Montant"

    def facture_link(self, obj):
        if obj.facture_pdf:
            return format_html(
                '<a href="{}" target="_blank">Afficher</a>', obj.facture_pdf.url)
        return "Aucune"
    facture_link.short_description = 'Facture'



    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            cl = response.context_data['cl']
            qs = cl.queryset

            total = qs.aggregate(total=Sum('montant'))['total'] or 0

            # position réelle de la colonne "Montant" dans list_display
            cols = list(self.get_list_display(request))
            idx = cols.index('montant_aff')  # ← si tu gardes 'montant_aff' dans list_display

            response.context_data['versement_totaux'] = {
                "montant_total": f"{int(total):,}".replace(",", " ") + " FCFA",
                "colspan_before_montant": idx,                  # nb de cellules AVANT
                "cols_after_montant": len(cols) - idx - 1,      # nb de cellules APRÈS
            }
        except Exception:
            pass
        return response
 

