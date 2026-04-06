"""
URL configuration for lamane project.
"""
from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

from core import views as views_html

urlpatterns = [
    # ── Admin ─────────────────────────────────────────────────────────────
    path('admin/', admin.site.urls),

    # ── Authentification ──────────────────────────────────────────────────
    path('connexion/', views_html.login_view, name='ui_login'),
    path('deconnexion/', views_html.logout_view, name='ui_logout'),
    path('deconnecte/', views_html.logged_out_view, name='ui_logged_out'),

    # ── API JSON ──────────────────────────────────────────────────────────
    path('api/', include('core.api.urls')),
    path('api/', include('core.urls')),

    # ── Filtre global projet / année ────────────────────────────────────
    path('set-filter/', views_html.set_global_filter, name='set_global_filter'),

    # ── Site Vitrine (page publique) ────────────────────────────────────
    path('', views_html.vitrine_view, name='ui_vitrine'),

    # ── Dashboard ────────────────────────────────────────────────────────
    path('dashboard/', views_html.dashboard_view, name='ui_dashboard'),

    # ── Gestion du site vitrine ──────────────────────────────────────────
    path('vitrine/gestion/', views_html.vitrine_gestion_view, name='ui_vitrine_gestion'),
    path('vitrine/gestion/config/', views_html.vitrine_config_edit_view, name='ui_vitrine_config_edit'),
    path('vitrine/gestion/services/nouveau/', views_html.vitrine_service_create_view, name='ui_vitrine_service_create'),
    path('vitrine/gestion/services/<str:pk>/modifier/', views_html.vitrine_service_edit_view, name='ui_vitrine_service_edit'),
    path('vitrine/gestion/services/<str:pk>/supprimer/', views_html.vitrine_service_delete_view, name='ui_vitrine_service_delete'),
    path('vitrine/gestion/projets/nouveau/', views_html.vitrine_projet_create_view, name='ui_vitrine_projet_create'),
    path('vitrine/gestion/projets/<str:pk>/modifier/', views_html.vitrine_projet_edit_view, name='ui_vitrine_projet_edit'),
    path('vitrine/gestion/projets/<str:pk>/supprimer/', views_html.vitrine_projet_delete_view, name='ui_vitrine_projet_delete'),
    path('vitrine/gestion/temoignages/nouveau/', views_html.vitrine_temoignage_create_view, name='ui_vitrine_temoignage_create'),
    path('vitrine/gestion/temoignages/<str:pk>/modifier/', views_html.vitrine_temoignage_edit_view, name='ui_vitrine_temoignage_edit'),
    path('vitrine/gestion/temoignages/<str:pk>/supprimer/', views_html.vitrine_temoignage_delete_view, name='ui_vitrine_temoignage_delete'),

    # ── Projets (CRUD avant <str:pk>) ────────────────────────────────────
    path('projets/', views_html.projets_list_view, name='ui_projets_list'),
    path('projets/nouveau/', views_html.projet_create_view, name='ui_projet_create'),
    path('projets/<str:pk>/', views_html.projet_detail_view, name='ui_projet_detail'),
    path('projets/<str:pk>/modifier/', views_html.projet_edit_view, name='ui_projet_edit'),
    path('projets/<str:pk>/supprimer/', views_html.projet_delete_view, name='ui_projet_delete'),

    # ── Types de projets ─────────────────────────────────────────────────
    path('types-projets/', views_html.types_projets_view, name='ui_types_projets'),
    path('types-projets/nouveau/', views_html.type_projet_create_view, name='ui_type_projet_create'),
    path('types-projets/<int:pk>/modifier/', views_html.type_projet_edit_view, name='ui_type_projet_edit'),
    path('types-projets/<int:pk>/supprimer/', views_html.type_projet_delete_view, name='ui_type_projet_delete'),

    # ── Finances ──────────────────────────────────────────────────────────
    path('finances/', views_html.finances_view, name='ui_finances'),

    # ── Chantiers ─────────────────────────────────────────────────────────
    path('chantiers/', views_html.chantiers_view, name='ui_chantiers'),
    path('chantiers/avancement/nouveau/', views_html.avancement_create_view, name='ui_avancement_create'),
    path('chantiers/<str:pk>/', views_html.chantier_detail_view, name='ui_chantier_detail'),

    # ── Marchés ───────────────────────────────────────────────────────────
    path('marches/', views_html.marches_view, name='ui_marches'),
    path('marches/nouveau/', views_html.marche_create_view, name='ui_marche_create'),
    path('marches/<int:pk>/modifier/', views_html.marche_edit_view, name='ui_marche_edit'),

    # ── Sous-traitants ────────────────────────────────────────────────────
    path('sous-traitants/', views_html.sous_traitants_view, name='ui_sous_traitants'),
    path('sous-traitants/nouveau/', views_html.sous_traitant_create_view, name='ui_sous_traitant_create'),
    path('sous-traitants/contrats/nouveau/', views_html.contrat_st_create_view, name='ui_contrat_st_create'),
    path('sous-traitants/<int:pk>/', views_html.sous_traitant_detail_view, name='ui_sous_traitant_detail'),
    path('sous-traitants/<int:pk>/modifier/', views_html.sous_traitant_edit_view, name='ui_sous_traitant_edit'),
    path('sous-traitants/<int:pk>/supprimer/', views_html.sous_traitant_delete_view, name='ui_sous_traitant_delete'),

    # ── RH ────────────────────────────────────────────────────────────────
    path('rh/', views_html.rh_view, name='ui_rh'),
    path('rh/employes/nouveau/', views_html.employe_create_view, name='ui_employe_create'),
    path('rh/employes/<int:pk>/', views_html.employe_detail_view, name='ui_employe_detail'),
    path('rh/employes/<int:pk>/modifier/', views_html.employe_edit_view, name='ui_employe_edit'),
    path('rh/employes/<int:pk>/supprimer/', views_html.employe_delete_view, name='ui_employe_delete'),

    # ── Clients ───────────────────────────────────────────────────────────
    path('clients/', views_html.clients_view, name='ui_clients'),
    path('clients/nouveau/', views_html.client_create_view, name='ui_client_create'),
    path('clients/<int:pk>/', views_html.client_detail_view, name='ui_client_detail'),
    path('clients/<int:pk>/modifier/', views_html.client_edit_view, name='ui_client_edit'),
    path('clients/<int:pk>/supprimer/', views_html.client_delete_view, name='ui_client_delete'),

    # ── Fournisseurs ──────────────────────────────────────────────────────
    path('fournisseurs/', views_html.fournisseurs_view, name='ui_fournisseurs'),
    path('fournisseurs/nouveau/', views_html.fournisseur_create_view, name='ui_fournisseur_create'),
    path('fournisseurs/<str:pk>/', views_html.fournisseur_detail_view, name='ui_fournisseur_detail'),
    path('fournisseurs/<str:pk>/modifier/', views_html.fournisseur_edit_view, name='ui_fournisseur_edit'),
    path('fournisseurs/<str:pk>/supprimer/', views_html.fournisseur_delete_view, name='ui_fournisseur_delete'),

    # ── Achats ────────────────────────────────────────────────────────────
    path('achats/', views_html.achats_list_view, name='ui_achats'),
    path('achats/nouveau/', views_html.achat_create_view, name='ui_achat_create'),
    path('achats/<str:pk>/', views_html.achat_detail_view, name='ui_achat_detail'),
    path('achats/<str:pk>/modifier/', views_html.achat_edit_view, name='ui_achat_edit'),
    path('achats/<str:pk>/supprimer/', views_html.achat_delete_view, name='ui_achat_delete'),

    # ── Versements ────────────────────────────────────────────────────────
    path('versements/', views_html.versements_view, name='ui_versements'),
    path('versements/nouveau/', views_html.versement_create_view, name='ui_versement_create'),
    path('versements/<int:pk>/', views_html.versement_detail_view, name='ui_versement_detail'),
    path('versements/<int:pk>/supprimer/', views_html.versement_delete_view, name='ui_versement_delete'),

    # ── Stock ─────────────────────────────────────────────────────────────
    path('stock/', views_html.stock_view, name='ui_stock'),
    path('stock/detail/', views_html.stock_detail_view, name='ui_stock_detail'),
    path('stock/bons-sortie/', views_html.bons_sortie_list_view, name='ui_bons_sortie'),
    path('stock/bons-sortie/nouveau/', views_html.bon_sortie_create_view, name='ui_bon_sortie_create'),
    path('stock/bons-sortie/<str:pk>/', views_html.bon_sortie_detail_view, name='ui_bon_sortie_detail'),
    path('stock/materiaux/', views_html.materiaux_list_view, name='ui_materiaux_list'),
    path('stock/materiaux/nouveau/', views_html.materiel_create_view, name='ui_materiel_create'),
    path('stock/materiaux/<str:pk>/', views_html.materiel_detail_view, name='ui_materiel_detail'),
    path('stock/materiaux/<str:pk>/modifier/', views_html.materiel_edit_view, name='ui_materiel_edit'),
    path('stock/categories/nouveau/', views_html.categorie_materiel_create_view, name='ui_categorie_create'),

    # ── Bilans financiers ─────────────────────────────────────────────────
    path('bilans/', views_html.bilans_view, name='ui_bilans'),

    # ── Categories materiaux ─────────────────────────────────────────────
    path('categories/', views_html.categories_view, name='ui_categories'),
    path('categories/nouveau/', views_html.categorie_create_view, name='ui_categorie_create'),
    path('categories/<str:pk>/modifier/', views_html.categorie_edit_view, name='ui_categorie_edit'),
    path('categories/<str:pk>/supprimer/', views_html.categorie_delete_view, name='ui_categorie_delete'),

    # ── Etapes standard ──────────────────────────────────────────────────
    path('etapes-standard/', views_html.etapes_standard_view, name='ui_etapes_standard'),
    path('etapes-standard/nouveau/', views_html.etape_standard_create_view, name='ui_etape_standard_create'),
    path('etapes-standard/<int:pk>/modifier/', views_html.etape_standard_edit_view, name='ui_etape_standard_edit'),
    path('etapes-standard/<int:pk>/supprimer/', views_html.etape_standard_delete_view, name='ui_etape_standard_delete'),

    # ── Phases de versement ──────────────────────────────────────────────
    path('phases-versement/', views_html.phases_versement_view, name='ui_phases_versement'),
    path('phases-versement/nouveau/', views_html.phase_versement_create_view, name='ui_phase_versement_create'),
    path('phases-versement/<int:pk>/modifier/', views_html.phase_versement_edit_view, name='ui_phase_versement_edit'),
    path('phases-versement/<int:pk>/supprimer/', views_html.phase_versement_delete_view, name='ui_phase_versement_delete'),

    # ── Profil utilisateur ────────────────────────────────────────────────
    path('profil/', views_html.profil_view, name='ui_profil'),

    # ── Comptabilité ────────────────────────────────────────────────────
    path('comptabilite/journal/', views_html.comptabilite_journal_view, name='ui_comptabilite_journal'),
    path('comptabilite/grand-livre/', views_html.comptabilite_grand_livre_view, name='ui_comptabilite_grand_livre'),
    path('comptabilite/balance/', views_html.comptabilite_balance_view, name='ui_comptabilite_balance'),
    path('comptabilite/plan-comptable/', views_html.comptabilite_plan_view, name='ui_comptabilite_plan'),
    path('comptabilite/ecritures/nouveau/', views_html.ecriture_create_view, name='ui_ecriture_create'),
    path('comptabilite/ecritures/<str:pk>/', views_html.ecriture_detail_view, name='ui_ecriture_detail'),

    # ── Trésorerie / Comptes bancaires ─────────────────────────────────
    path('tresorerie/', views_html.tresorerie_view, name='ui_tresorerie'),
    path('tresorerie/comptes/nouveau/', views_html.compte_bancaire_create_view, name='ui_compte_bancaire_create'),
    path('tresorerie/comptes/<str:pk>/', views_html.compte_bancaire_detail_view, name='ui_compte_bancaire_detail'),
    path('tresorerie/comptes/<str:pk>/modifier/', views_html.compte_bancaire_edit_view, name='ui_compte_bancaire_edit'),
    path('tresorerie/transactions/nouveau/', views_html.transaction_create_view, name='ui_transaction_create'),

    # ── Documents BTP ──────────────────────────────────────────────────
    path('documents-btp/', views_html.documents_btp_view, name='ui_documents_btp'),
    path('documents-btp/nouveau/', views_html.document_btp_create_view, name='ui_document_btp_create'),
    path('documents-btp/bordereaux/', views_html.bordereaux_view, name='ui_bordereaux'),
    path('documents-btp/bordereaux/nouveau/', views_html.bordereau_create_view, name='ui_bordereau_create'),
    path('documents-btp/bordereaux/<str:pk>/', views_html.bordereau_detail_view, name='ui_bordereau_detail'),
    path('documents-btp/dgd/', views_html.dgd_list_view, name='ui_dgd_list'),
    path('documents-btp/dgd/nouveau/', views_html.dgd_create_view, name='ui_dgd_create'),
    path('documents-btp/dgd/<str:pk>/', views_html.dgd_detail_view, name='ui_dgd_detail'),
    path('documents-btp/<str:pk>/', views_html.document_btp_detail_view, name='ui_document_btp_detail'),
    path('documents-btp/<str:pk>/supprimer/', views_html.document_btp_delete_view, name='ui_document_btp_delete'),

    # ── Gestion utilisateurs ───────────────────────────────────────────
    path('utilisateurs/', views_html.utilisateurs_view, name='ui_utilisateurs'),
    path('utilisateurs/<int:pk>/profil/', views_html.profil_edit_view, name='ui_profil_edit'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
