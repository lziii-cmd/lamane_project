"""
Fonctions utilitaires partagées entre les modules de vues HTML.
"""
from django.contrib import messages
from django.shortcuts import redirect


def _fmt(val, dec=0):
    try:
        v = float(val or 0)
        return f"{v:,.{dec}f}".replace(",", " ")
    except Exception:
        return "0"


def _success(request, msg, url):
    messages.success(request, msg)
    return redirect(url)
