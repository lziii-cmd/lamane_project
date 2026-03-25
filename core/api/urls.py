# core/api/urls.py
from django.urls import path
from core.api.dashboard_views import dashboard_stats

from django.urls import path
from core.views import projets_list, projet_detail

urlpatterns = [
    path("dashboard/stats/", dashboard_stats),
    path("projets/", projets_list, name="api_projets_list"),
    path("projets/<int:pk>/", projet_detail, name="api_projet_detail"),
    
]
