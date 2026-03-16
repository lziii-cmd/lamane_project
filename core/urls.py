"""
URLs du module core — LAMANE BTP
"""
from django.urls import path
from . import views
from . import views_html

urlpatterns = [
    # ── API JSON ───────────────────────────────────────────────────────────
    path("dashboard/stats/", views.dashboard_stats, name="dashboard_stats"),
    path("dashboard/stats-finances/", views.dashboard_stats_finances, name="dashboard_stats_finances"),
    path("projets/", views.projets_list, name="api_projets_list"),
    path("projets/<str:pk>/", views.projet_detail, name="api_projet_detail"),
]
