# core/admin/etape_standard_admin.py
from django.contrib import admin
from core.models.etape_standard import EtapeStandard


@admin.register(EtapeStandard)
class EtapeStandardAdmin(admin.ModelAdmin):
    list_display = ('ordre', 'nom', 'groupe', 'multi_niveau')
    ordering = ('ordre', 'groupe')
    search_fields = ('nom',)
