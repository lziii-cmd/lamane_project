"""
Vues d'authentification — LAMANE BTP
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout


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
    return redirect("ui_logged_out")


def logged_out_view(request):
    """Page post-déconnexion avec option de reconnexion."""
    return render(request, "lamane/logged_out.html")
