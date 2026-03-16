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
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)