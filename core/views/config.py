# core/views/config.py
"""Vues configuration, phases versement, utilisateurs, profil — LAMANE BTP."""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.db.models.functions import Coalesce
from decimal import Decimal

from core.models import (
    Projet, TypeProjet, PhaseVersement, Versement,
    ProfilUtilisateur,
)
from core.forms import (
    TypeProjetForm, PhaseVersementForm, ProfilUtilisateurForm,
)
from core.permissions import role_required
from core.views._helpers import _fmt, _success, apply_versement_filters

__all__ = [
    "types_projets_view", "type_projet_create_view",
    "type_projet_edit_view", "type_projet_delete_view",
    "phases_versement_view", "phase_versement_create_view",
    "phase_versement_edit_view", "phase_versement_delete_view",
    "profil_view", "utilisateurs_view", "profil_edit_view",
]


# ─── TYPES DE PROJETS ─────────────────────────────────────────────────────────

@login_required
@role_required("comptable", "chef_chantier")
def types_projets_view(request):
    types = TypeProjet.objects.annotate(nb_projets=Count("projet")).order_by("nom")
    return render(request, "lamane/types_projets.html", {"page": "types_projets", "types": types})


@login_required
@role_required()
def type_projet_create_view(request):
    form = TypeProjetForm(request.POST or None)
    if form.is_valid():
        t = form.save()
        return _success(request, f"Type « {t.nom} » créé.", "ui_types_projets")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": "Nouveau type de projet",
                   "action": "Créer", "page": "types_projets", "back_url": "/types-projets/"})


@login_required
@role_required()
def type_projet_edit_view(request, pk):
    t = get_object_or_404(TypeProjet, pk=pk)
    form = TypeProjetForm(request.POST or None, instance=t)
    if form.is_valid():
        form.save()
        return _success(request, "Type modifié.", "ui_types_projets")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": f"Modifier — {t.nom}",
                   "action": "Enregistrer", "page": "types_projets",
                   "back_url": "/types-projets/", "obj": t})


@login_required
@role_required()
def type_projet_delete_view(request, pk):
    t = get_object_or_404(TypeProjet, pk=pk)
    if request.method == "POST":
        nom = t.nom
        t.delete()
        return _success(request, f"Type « {nom} » supprimé.", "ui_types_projets")
    return render(request, "lamane/forms/confirm_delete.html",
                  {"obj": t, "titre": t.nom, "page": "types_projets",
                   "back_url": "/types-projets/"})


# ─── PHASES DE VERSEMENT ─────────────────────────────────────────────────────

@login_required
@role_required("comptable")
def phases_versement_view(request):
    projet_id = request.GET.get("projet", "")
    phases = PhaseVersement.objects.select_related("projet", "etape_standard").all()
    if projet_id:
        phases = phases.filter(projet__pk=projet_id)
    phases = phases.order_by("projet__nom", "ordre")

    phases_data = []
    for p in phases:
        montant_verse = apply_versement_filters(Versement.objects.filter(phase=p), request).aggregate(
            s=Coalesce(Sum("montant"), Decimal("0")))["s"]
        phases_data.append({
            "phase": p,
            "montant_verse": montant_verse,
            "montant_verse_fmt": _fmt(montant_verse),
            "montant_prevu_fmt": _fmt(p.montant_prevu),
            "pct": round(float(montant_verse) / float(p.montant_prevu) * 100, 1) if p.montant_prevu > 0 else 0,
        })

    projets = Projet.objects.all().order_by("nom")
    ctx = {
        "page": "phases_versement", "phases_data": phases_data,
        "projets": projets, "projet_filter": projet_id,
        "total_phases": phases.count(),
    }
    return render(request, "lamane/phases_versement.html", ctx)


@login_required
@role_required("comptable")
def phase_versement_create_view(request):
    form = PhaseVersementForm(request.POST or None)
    if form.is_valid():
        p = form.save()
        return _success(request, f"Phase « {p} » créée.", "ui_phases_versement")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": "Nouvelle phase de versement",
                   "action": "Créer", "page": "phases_versement",
                   "back_url": "/phases-versement/"})


@login_required
@role_required("comptable")
def phase_versement_edit_view(request, pk):
    p = get_object_or_404(PhaseVersement, pk=pk)
    form = PhaseVersementForm(request.POST or None, instance=p)
    if form.is_valid():
        form.save()
        return _success(request, "Phase modifiée.", "ui_phases_versement")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": f"Modifier — {p}",
                   "action": "Enregistrer", "page": "phases_versement",
                   "back_url": "/phases-versement/", "obj": p})


@login_required
@role_required("comptable")
def phase_versement_delete_view(request, pk):
    p = get_object_or_404(PhaseVersement, pk=pk)
    if request.method == "POST":
        nom = str(p)
        p.delete()
        return _success(request, f"Phase « {nom} » supprimée.", "ui_phases_versement")
    return render(request, "lamane/forms/confirm_delete.html",
                  {"obj": p, "titre": str(p), "page": "phases_versement",
                   "back_url": "/phases-versement/"})


# ─── PROFIL + UTILISATEURS ─────────────────────────────────────────────────────

@login_required
def profil_view(request):
    user = request.user
    ctx = {"page": "profil", "user": user}
    return render(request, "lamane/profil.html", ctx)


@login_required
@role_required()
def utilisateurs_view(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    users = User.objects.all().select_related("profil" if hasattr(User, "profil") else None)
    users_data = []
    for u in users:
        try:
            profil = u.profil
        except ProfilUtilisateur.DoesNotExist:
            profil = None
        users_data.append({
            "user": u, "profil": profil,
            "role_display": profil.get_role_display() if profil else "—",
            "role": profil.role if profil else "",
        })
    ctx = {
        "page": "utilisateurs", "users_data": users_data,
        "total_users": len(users_data),
        "roles": ProfilUtilisateur.ROLE_CHOICES,
    }
    return render(request, "lamane/utilisateurs.html", ctx)


@login_required
@role_required()
def profil_edit_view(request, pk):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user_obj = get_object_or_404(User, pk=pk)
    profil, _ = ProfilUtilisateur.objects.get_or_create(user=user_obj)
    form = ProfilUtilisateurForm(request.POST or None, request.FILES or None, instance=profil)
    if form.is_valid():
        form.save()
        return _success(request, f"Profil de {user_obj.username} mis à jour.", "ui_utilisateurs")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form,
                   "title": f"Profil — {user_obj.get_full_name() or user_obj.username}",
                   "action": "Enregistrer", "page": "utilisateurs",
                   "back_url": "/utilisateurs/"})
