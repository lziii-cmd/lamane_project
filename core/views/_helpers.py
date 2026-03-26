# core/views/_helpers.py
"""Helpers partagés entre toutes les vues."""
from django.shortcuts import redirect
from django.contrib import messages


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
