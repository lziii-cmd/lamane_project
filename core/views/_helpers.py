# core/views/_helpers.py
"""Helpers partagés entre toutes les vues."""
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Q


def _fmt(val, dec=0):
    """Formater un nombre en chaîne lisible (espaces comme séparateur de milliers)."""
    try:
        v = float(val or 0)
        return f"{v:,.{dec}f}".replace(",", " ")
    except Exception:
        return "0"


def _success(request, msg, url):
    """Ajouter un message de succès et rediriger."""
    messages.success(request, msg)
    return redirect(url)


# ═══════════════════════════════════════════════════════════════════════════
# Filtres globaux projet / année
# ═══════════════════════════════════════════════════════════════════════════

def get_global_filters(request):
    """Retourne (projet_id, annee) depuis la session."""
    projet_id = request.session.get("filtre_projet_id", "")
    annee = request.session.get("filtre_annee", "")
    return projet_id, int(annee) if annee else None


def apply_achat_filters(qs, request):
    """Applique les filtres globaux projet/année sur un queryset d'Achats."""
    projet_id, annee = get_global_filters(request)
    if projet_id:
        qs = qs.filter(projet_id=projet_id)
    if annee:
        qs = qs.filter(date_achat__year=annee)
    return qs


def apply_versement_filters(qs, request):
    """Applique les filtres globaux projet/année sur un queryset de Versements."""
    projet_id, annee = get_global_filters(request)
    if projet_id:
        qs = qs.filter(projet_id=projet_id)
    if annee:
        qs = qs.filter(date_versement__year=annee)
    return qs


def apply_projet_filters(qs, request):
    """Applique les filtres globaux sur un queryset de Projets."""
    projet_id, annee = get_global_filters(request)
    if projet_id:
        qs = qs.filter(pk=projet_id)
    return qs


@require_POST
@login_required
def set_global_filter(request):
    """Sauvegarde le filtre projet/année dans la session et redirige."""
    projet_id = request.POST.get("filtre_projet", "")
    annee = request.POST.get("filtre_annee", "")

    if projet_id:
        request.session["filtre_projet_id"] = projet_id
    else:
        request.session.pop("filtre_projet_id", None)

    if annee:
        request.session["filtre_annee"] = annee
    else:
        request.session.pop("filtre_annee", None)

    # Rediriger vers la page d'origine
    referer = request.META.get("HTTP_REFERER", "/")
    return redirect(referer)
