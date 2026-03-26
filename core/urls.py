"""
URLs du module core — LAMANE BTP
"""
from django.urls import path
from . import views_api

urlpatterns = [
    # ── API JSON ───────────────────────────────────────────────────────────
    path("dashboard/stats/", views_api.dashboard_stats, name="dashboard_stats"),
    path("dashboard/stats-finances/", views_api.dashboard_stats_finances, name="dashboard_stats_finances"),
    path("projets/", views_api.projets_list, name="api_projets_list"),
    path("projets/<str:pk>/", views_api.projet_detail, name="api_projet_detail"),
]
