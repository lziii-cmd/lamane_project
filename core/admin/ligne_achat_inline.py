# core/admin/ligne_achat_inline.py
from django.contrib import admin
from core.models.ligne_achat import LigneAchat


class LigneAchatInline(admin.TabularInline):
    model = LigneAchat
    extra = 1
    fields = ('materiel', 'quantite', 'prix_unitaire', 'commentaire', 'total_ligne_affiche')
    #list_display  = ('materiel', 'quantite', 'prix_unitaire', 'commentaire', 'total_ligne_affiche')
    readonly_fields = ('total_ligne_affiche',)

    def total_ligne_affiche(self, obj):
        if obj.pk:
            return f"{obj.total_ligne:,.0f} FCFA"
        return ""
    total_ligne_affiche.short_description = "Total ligne HT"
