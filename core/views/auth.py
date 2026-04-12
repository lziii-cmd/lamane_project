# core/views/auth.py
"""Vues d'authentification — LAMANE BTP."""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.conf import settings

__all__ = ["login_view", "logout_view", "logged_out_view", "setup_admin_view"]


def login_view(request):
    """Page de connexion."""
    if request.user.is_authenticated:
        return redirect("ui_dashboard")
    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get("next") or request.POST.get("next") or "ui_dashboard"
            return redirect(next_url)
        else:
            error = "Nom d'utilisateur ou mot de passe incorrect."
    return render(request, "lamane/login.html", {"error": error, "next": request.GET.get("next", "")})


def logout_view(request):
    """Déconnexion puis redirection vers la page de reconnexion."""
    logout(request)
    return redirect("ui_vitrine")


def logged_out_view(request):
    """Page post-déconnexion avec option de reconnexion."""
    return render(request, "lamane/logged_out.html")


def setup_admin_view(request, key):
    """Page secrète de création du premier compte admin."""
    if key != settings.ADMIN_SETUP_KEY:
        from django.http import Http404
        raise Http404

    success = False
    error = None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")

        if not username or not password:
            error = "Le nom d'utilisateur et le mot de passe sont obligatoires."
        elif password != password_confirm:
            error = "Les mots de passe ne correspondent pas."
        elif User.objects.filter(username=username).exists():
            error = f"L'utilisateur « {username} » existe déjà."
        else:
            User.objects.create_superuser(username=username, email=email, password=password)
            success = True

    return render(request, "lamane/create_admin.html", {"success": success, "error": error})
