# core/context_processors.py
"""
Context processor global — injecte le profil utilisateur et le rôle dans tous les templates.
"""
from core.models import ProfilUtilisateur


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
