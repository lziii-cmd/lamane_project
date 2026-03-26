# core/permissions.py
"""
Décorateur de rôle pour restreindre l'accès aux vues par profil utilisateur.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

from core.models import ProfilUtilisateur


def role_required(*roles):
    """
    Décorateur qui vérifie que l'utilisateur a un des rôles spécifiés.
    Les admins et la direction ont toujours accès.
    Usage : @role_required("comptable", "direction")
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("ui_login")
            # Superuser a toujours accès
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            try:
                profil = request.user.profil
            except ProfilUtilisateur.DoesNotExist:
                # Pas de profil = accès total (rétro-compatibilité)
                return view_func(request, *args, **kwargs)
            # Direction et admin ont toujours accès
            if profil.role in ("direction", "admin"):
                return view_func(request, *args, **kwargs)
            if profil.role in roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, "Vous n'avez pas les droits pour accéder à cette page.")
            return redirect("ui_dashboard")
        return wrapper
    return decorator
