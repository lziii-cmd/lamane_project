# core/admin/achat_admin.py
from django.contrib import admin
from django.db.models import Sum
from django.utils.html import format_html
from core.models.achat import Achat
from core.models.ligne_achat import LigneAchat
from core.admin.ligne_achat_inline import LigneAchatInline

@admin.register(Achat)
class AchatAdmin(admin.ModelAdmin):
    list_display = (
        'date_achat',
        'projet',
        'fournisseur',
        'mode_paiement',
        'total_ht',
        'total_tva',
        'total_ttc',
        'afficher_facture',
    )
    list_filter = ('projet', 'date_achat', 'fournisseur')
    search_fields = ('projet__nom', 'fournisseur__nom', 'numero_facture')
    inlines = [LigneAchatInline]
    readonly_fields = ('total_ht', 'total_tva', 'total_ttc')
    change_list_template = 'admin/core/achat/change_list.html'

    def afficher_facture(self, obj):
        if obj.fichier_facture:
            return format_html('<a href="{}" target="_blank">Voir la facture</a>', obj.fichier_facture.url)
        return "-"
    afficher_facture.short_description = "Facture"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.calcul_totaux()
        obj.save(update_fields=['total_ht', 'total_tva', 'total_ttc'])

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        if isinstance(form.instance, Achat):
            form.instance.calcul_totaux()
            form.instance.save(update_fields=['total_ht', 'total_tva', 'total_ttc'])

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)

        try:
            qs = response.context_data['cl'].queryset
            total_ht = qs.aggregate(total=Sum('total_ht'))['total'] or 0
            total_tva = qs.aggregate(total=Sum('total_tva'))['total'] or 0
            total_ttc = qs.aggregate(total=Sum('total_ttc'))['total'] or 0

            extra_context = extra_context or {}
            extra_context['totaux'] = {
                'total_ht': total_ht,
                'total_tva': total_tva,
                'total_ttc': total_ttc,
            }
            response.context_data.update(extra_context)
        except (AttributeError, KeyError):
            pass

        return response
