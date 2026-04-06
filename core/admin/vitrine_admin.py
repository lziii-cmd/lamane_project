# core/admin/vitrine_admin.py
"""Admin pour les modeles du site vitrine."""
from django.contrib import admin
from core.models import ConfigVitrine, ServiceVitrine, ProjetVitrine, TemoignageVitrine


@admin.register(ConfigVitrine)
class ConfigVitrineAdmin(admin.ModelAdmin):
    list_display = ("__str__", "hero_titre", "contact_email")
    fieldsets = (
        ("Hero", {"fields": ("hero_titre", "hero_sous_titre", "hero_bouton_texte", "hero_bouton_lien", "hero_image")}),
        ("Presentation", {"fields": ("presentation_titre", "presentation_texte")}),
        ("Chiffres cles", {"fields": (
            "stat_1_nombre", "stat_1_label",
            "stat_2_nombre", "stat_2_label",
            "stat_3_nombre", "stat_3_label",
            "stat_4_nombre", "stat_4_label",
        )}),
        ("Mot du directeur", {"fields": ("directeur_nom", "directeur_titre", "directeur_message", "directeur_photo")}),
        ("Investissement Diaspora", {"fields": (
            "diaspora_titre", "diaspora_texte",
            "diaspora_etape_1", "diaspora_etape_2", "diaspora_etape_3",
            "diaspora_etape_4", "diaspora_etape_5",
        )}),
        ("Contact", {"fields": ("contact_adresse", "contact_telephone", "contact_email", "contact_whatsapp")}),
        ("SEO & Footer", {"fields": ("meta_description", "footer_texte")}),
    )

    def has_add_permission(self, request):
        return not ConfigVitrine.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ServiceVitrine)
class ServiceVitrineAdmin(admin.ModelAdmin):
    list_display = ("titre", "icone", "ordre", "actif")
    list_editable = ("ordre", "actif")
    list_filter = ("actif",)


@admin.register(ProjetVitrine)
class ProjetVitrineAdmin(admin.ModelAdmin):
    list_display = ("nom", "localisation", "statut", "ordre", "actif")
    list_editable = ("ordre", "actif")
    list_filter = ("statut", "actif")


@admin.register(TemoignageVitrine)
class TemoignageVitrineAdmin(admin.ModelAdmin):
    list_display = ("nom", "titre", "ordre", "actif")
    list_editable = ("ordre", "actif")
    list_filter = ("actif",)
