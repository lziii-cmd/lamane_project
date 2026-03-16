"""
URL configuration for lamane project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

from core import views_html

urlpatterns = [
    # ── Admin ─────────────────────────────────────────────────────────────
    path('admin/', admin.site.urls),

    # ── API JSON ──────────────────────────────────────────────────────────
    path('api/', include('core.api.urls')),
    path('api/', include('core.urls')),

    # ── Interface HTML ────────────────────────────────────────────────────
    path('', views_html.dashboard_view, name='ui_dashboard'),
    path('projets/', views_html.projets_list_view, name='ui_projets_list'),
    path('projets/<str:pk>/', views_html.projet_detail_view, name='ui_projet_detail'),
    path('finances/', views_html.finances_view, name='ui_finances'),
    path('chantiers/', views_html.chantiers_view, name='ui_chantiers'),
    path('marches/', views_html.marches_view, name='ui_marches'),
    path('sous-traitants/', views_html.sous_traitants_view, name='ui_sous_traitants'),
    path('rh/', views_html.rh_view, name='ui_rh'),
    path('fournisseurs/', views_html.fournisseurs_view, name='ui_fournisseurs'),
    path('chantiers/<str:pk>/', views_html.chantier_detail_view, name='ui_chantier_detail'),
    path('achats/', views_html.achats_list_view, name='ui_achats'),
    path('achats/<str:pk>/', views_html.achat_detail_view, name='ui_achat_detail'),
    path('versements/', views_html.versements_view, name='ui_versements'),
    path('clients/', views_html.clients_view, name='ui_clients'),
    path('clients/<int:pk>/', views_html.client_detail_view, name='ui_client_detail'),
    path('stock/', views_html.stock_view, name='ui_stock'),
    path('stock/detail/', views_html.stock_detail_view, name='ui_stock_detail'),
    path('stock/bons-sortie/', views_html.bons_sortie_list_view, name='ui_bons_sortie'),
    path('stock/bons-sortie/nouveau/', views_html.bon_sortie_create_view, name='ui_bon_sortie_create'),
    path('stock/bons-sortie/<str:pk>/', views_html.bon_sortie_detail_view, name='ui_bon_sortie_detail'),
    path('stock/materiaux/nouveau/', views_html.materiel_create_view, name='ui_materiel_create'),
    path('stock/materiaux/<str:pk>/modifier/', views_html.materiel_edit_view, name='ui_materiel_edit'),
    path('stock/categories/nouveau/', views_html.categorie_materiel_create_view, name='ui_categorie_create'),

    # ── Projets CRUD ──────────────────────────────────────────────────────────
    path('projets/nouveau/', views_html.projet_create_view, name='ui_projet_create'),
    path('projets/<str:pk>/modifier/', views_html.projet_edit_view, name='ui_projet_edit'),
    path('projets/<str:pk>/supprimer/', views_html.projet_delete_view, name='ui_projet_delete'),

    # ── Types de projets ──────────────────────────────────────────────────────
    path('types-projets/', views_html.types_projets_view, name='ui_types_projets'),
    path('types-projets/nouveau/', views_html.type_projet_create_view, name='ui_type_projet_create'),
    path('types-projets/<int:pk>/modifier/', views_html.type_projet_edit_view, name='ui_type_projet_edit'),
    path('types-projets/<int:pk>/supprimer/', views_html.type_projet_delete_view, name='ui_type_projet_delete'),

    # ── Clients CRUD ──────────────────────────────────────────────────────────
    path('clients/nouveau/', views_html.client_create_view, name='ui_client_create'),
    path('clients/<int:pk>/modifier/', views_html.client_edit_view, name='ui_client_edit'),

    # ── Fournisseurs CRUD ─────────────────────────────────────────────────────
    path('fournisseurs/nouveau/', views_html.fournisseur_create_view, name='ui_fournisseur_create'),
    path('fournisseurs/<int:pk>/modifier/', views_html.fournisseur_edit_view, name='ui_fournisseur_edit'),

    # ── Employés CRUD ─────────────────────────────────────────────────────────
    path('rh/employes/nouveau/', views_html.employe_create_view, name='ui_employe_create'),
    path('rh/employes/<int:pk>/modifier/', views_html.employe_edit_view, name='ui_employe_edit'),

    # ── Achats CRUD ───────────────────────────────────────────────────────────
    path('achats/nouveau/', views_html.achat_create_view, name='ui_achat_create'),
    path('achats/<str:pk>/modifier/', views_html.achat_edit_view, name='ui_achat_edit'),
    path('achats/<str:pk>/supprimer/', views_html.achat_delete_view, name='ui_achat_delete'),

    # ── Versements CRUD ───────────────────────────────────────────────────────
    path('versements/nouveau/', views_html.versement_create_view, name='ui_versement_create'),
    path('versements/<int:pk>/supprimer/', views_html.versement_delete_view, name='ui_versement_delete'),

    # ── Marchés CRUD ──────────────────────────────────────────────────────────
    path('marches/nouveau/', views_html.marche_create_view, name='ui_marche_create'),
    path('marches/<int:pk>/modifier/', views_html.marche_edit_view, name='ui_marche_edit'),

    # ── Avancement Chantier ───────────────────────────────────────────────────
    path('chantiers/avancement/nouveau/', views_html.avancement_create_view, name='ui_avancement_create'),

    # ── Sous-traitants CRUD ───────────────────────────────────────────────────
    path('sous-traitants/nouveau/', views_html.sous_traitant_create_view, name='ui_sous_traitant_create'),
    path('sous-traitants/<int:pk>/modifier/', views_html.sous_traitant_edit_view, name='ui_sous_traitant_edit'),

    # ── Bilans financiers ─────────────────────────────────────────────────────
    path('bilans/', views_html.bilans_view, name='ui_bilans'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)