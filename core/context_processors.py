# core/context_processors.py
"""
Context processors globaux — profil utilisateur + filtres projet/année.
"""
from core.models import ProfilUtilisateur, Projet, Achat, Versement
from django.db.models.functions import ExtractYear


def user_profil(request):
    """Ajoute le profil utilisateur au contexte de chaque template."""
    if request.user.is_authenticated:
        try:
            profil = request.user.profil
        except ProfilUtilisateur.DoesNotExist:
            profil = None
        return {
            "user_profil": profil,
            "user_role": profil.role if profil else "direction",
            "est_direction": profil.est_direction if profil else True,
            "est_comptable": profil.est_comptable if profil else True,
        }
    return {
        "user_profil": None,
        "user_role": None,
        "est_direction": False,
        "est_comptable": False,
    }


def global_filters(request):
    """
    Injecte les filtres globaux projet/année dans tous les templates.
    Les valeurs sont stockées dans request.session.
    """
    # Lire la session
    selected_projet_id = request.session.get("filtre_projet_id", "")
    selected_annee = request.session.get("filtre_annee", "")

    # Liste des projets disponibles
    projets_list = Projet.objects.values_list("id", "nom").order_by("nom")

    # Liste des années disponibles (union achats + versements)
    annees = set()
    for y in Achat.objects.annotate(y=ExtractYear("date_achat")).values_list("y", flat=True).distinct():
        if y:
            annees.add(y)
    for y in Versement.objects.annotate(y=ExtractYear("date_versement")).values_list("y", flat=True).distinct():
        if y:
            annees.add(y)
    annees_list = sorted(annees, reverse=True)

    # Objet projet sélectionné
    selected_projet = None
    if selected_projet_id:
        try:
            selected_projet = Projet.objects.get(pk=selected_projet_id)
        except Projet.DoesNotExist:
            request.session.pop("filtre_projet_id", None)
            selected_projet_id = ""

    return {
        "gf_projets": projets_list,
        "gf_annees": annees_list,
        "gf_projet_id": str(selected_projet_id),
        "gf_annee": str(selected_annee),
        "gf_projet": selected_projet,
    }
