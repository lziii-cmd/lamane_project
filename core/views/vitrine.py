# core/views/vitrine.py
"""Vues du site vitrine LAMANE — pages publiques + gestion admin."""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from core.models import ConfigVitrine, ServiceVitrine, ProjetVitrine, TemoignageVitrine
from core.permissions import role_required

__all__ = [
    "vitrine_view",
    "vitrine_gestion_view",
    "vitrine_config_edit_view",
    "vitrine_service_create_view",
    "vitrine_service_edit_view",
    "vitrine_service_delete_view",
    "vitrine_projet_create_view",
    "vitrine_projet_edit_view",
    "vitrine_projet_delete_view",
    "vitrine_temoignage_create_view",
    "vitrine_temoignage_edit_view",
    "vitrine_temoignage_delete_view",
]


# ═══════════════════════════════════════════════════════════════════════════
# PAGE PUBLIQUE — VITRINE
# ═══════════════════════════════════════════════════════════════════════════

def vitrine_view(request):
    """Page d'accueil publique du site vitrine."""
    config = ConfigVitrine.get()
    services = ServiceVitrine.objects.filter(actif=True)
    projets = ProjetVitrine.objects.filter(actif=True)
    temoignages = TemoignageVitrine.objects.filter(actif=True)

    ctx = {
        "config": config,
        "services": services,
        "projets": projets,
        "temoignages": temoignages,
    }
    return render(request, "lamane/vitrine.html", ctx)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE DE GESTION — ADMIN VITRINE
# ═══════════════════════════════════════════════════════════════════════════

@login_required
@role_required()
def vitrine_gestion_view(request):
    """Dashboard de gestion du site vitrine."""
    config = ConfigVitrine.get()
    services = ServiceVitrine.objects.all()
    projets = ProjetVitrine.objects.all()
    temoignages = TemoignageVitrine.objects.all()

    ctx = {
        "page": "vitrine_gestion",
        "config": config,
        "services": services,
        "projets": projets,
        "temoignages": temoignages,
    }
    return render(request, "lamane/vitrine_gestion.html", ctx)


@login_required
@role_required()
def vitrine_config_edit_view(request):
    """Modifier la configuration generale du site vitrine."""
    config = ConfigVitrine.get()
    if request.method == "POST":
        # Mettre a jour chaque champ
        fields = [
            "hero_titre", "hero_sous_titre", "hero_bouton_texte", "hero_bouton_lien",
            "presentation_titre", "presentation_texte",
            "stat_1_nombre", "stat_1_label", "stat_2_nombre", "stat_2_label",
            "stat_3_nombre", "stat_3_label", "stat_4_nombre", "stat_4_label",
            "directeur_nom", "directeur_titre", "directeur_message",
            "diaspora_titre", "diaspora_texte",
            "diaspora_etape_1", "diaspora_etape_2", "diaspora_etape_3",
            "diaspora_etape_4", "diaspora_etape_5",
            "contact_adresse", "contact_telephone", "contact_email", "contact_whatsapp",
            "meta_description", "footer_texte",
        ]
        for f in fields:
            val = request.POST.get(f, "")
            if val or f in ("contact_whatsapp",):
                setattr(config, f, val)

        # Gestion des fichiers images
        if "hero_image" in request.FILES:
            config.hero_image = request.FILES["hero_image"]
        if "directeur_photo" in request.FILES:
            config.directeur_photo = request.FILES["directeur_photo"]

        config.save()
        messages.success(request, "Configuration du site vitrine mise a jour.")
        return redirect("ui_vitrine_gestion")

    return render(request, "lamane/forms/vitrine_config_form.html", {
        "config": config, "page": "vitrine_gestion",
        "title": "Modifier la configuration vitrine",
    })


# ── Services CRUD ─────────────────────────────────────────────────────────

@login_required
@role_required()
def vitrine_service_create_view(request):
    if request.method == "POST":
        ServiceVitrine.objects.create(
            titre=request.POST.get("titre", ""),
            description=request.POST.get("description", ""),
            icone=request.POST.get("icone", "fas fa-building"),
            ordre=int(request.POST.get("ordre", 0)),
        )
        messages.success(request, "Service ajoute.")
        return redirect("ui_vitrine_gestion")
    return render(request, "lamane/forms/vitrine_item_form.html", {
        "page": "vitrine_gestion", "title": "Nouveau service",
        "item_type": "service", "action": "Creer",
    })


@login_required
@role_required()
def vitrine_service_edit_view(request, pk):
    obj = get_object_or_404(ServiceVitrine, pk=pk)
    if request.method == "POST":
        obj.titre = request.POST.get("titre", obj.titre)
        obj.description = request.POST.get("description", obj.description)
        obj.icone = request.POST.get("icone", obj.icone)
        obj.ordre = int(request.POST.get("ordre", obj.ordre))
        obj.actif = "actif" in request.POST
        obj.save()
        messages.success(request, "Service modifie.")
        return redirect("ui_vitrine_gestion")
    return render(request, "lamane/forms/vitrine_item_form.html", {
        "page": "vitrine_gestion", "title": f"Modifier — {obj.titre}",
        "item_type": "service", "action": "Enregistrer", "obj": obj,
    })


@login_required
@role_required()
def vitrine_service_delete_view(request, pk):
    obj = get_object_or_404(ServiceVitrine, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Service supprime.")
        return redirect("ui_vitrine_gestion")
    return render(request, "lamane/forms/confirm_delete.html", {
        "obj": obj, "titre": obj.titre, "page": "vitrine_gestion",
        "back_url": "/vitrine/gestion/",
    })


# ── Projets Vitrine CRUD ─────────────────────────────────────────────────

@login_required
@role_required()
def vitrine_projet_create_view(request):
    if request.method == "POST":
        kwargs = {
            "nom": request.POST.get("nom", ""),
            "description": request.POST.get("description", ""),
            "localisation": request.POST.get("localisation", ""),
            "statut": request.POST.get("statut", "en_cours"),
            "points_forts": request.POST.get("points_forts", ""),
            "ordre": int(request.POST.get("ordre", 0)),
        }
        if "image" in request.FILES:
            kwargs["image"] = request.FILES["image"]
        ProjetVitrine.objects.create(**kwargs)
        messages.success(request, "Projet vitrine ajoute.")
        return redirect("ui_vitrine_gestion")
    return render(request, "lamane/forms/vitrine_item_form.html", {
        "page": "vitrine_gestion", "title": "Nouveau projet vitrine",
        "item_type": "projet", "action": "Creer",
    })


@login_required
@role_required()
def vitrine_projet_edit_view(request, pk):
    obj = get_object_or_404(ProjetVitrine, pk=pk)
    if request.method == "POST":
        obj.nom = request.POST.get("nom", obj.nom)
        obj.description = request.POST.get("description", obj.description)
        obj.localisation = request.POST.get("localisation", obj.localisation)
        obj.statut = request.POST.get("statut", obj.statut)
        obj.points_forts = request.POST.get("points_forts", obj.points_forts)
        obj.ordre = int(request.POST.get("ordre", obj.ordre))
        obj.actif = "actif" in request.POST
        if "image" in request.FILES:
            obj.image = request.FILES["image"]
        obj.save()
        messages.success(request, "Projet vitrine modifie.")
        return redirect("ui_vitrine_gestion")
    return render(request, "lamane/forms/vitrine_item_form.html", {
        "page": "vitrine_gestion", "title": f"Modifier — {obj.nom}",
        "item_type": "projet", "action": "Enregistrer", "obj": obj,
    })


@login_required
@role_required()
def vitrine_projet_delete_view(request, pk):
    obj = get_object_or_404(ProjetVitrine, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Projet vitrine supprime.")
        return redirect("ui_vitrine_gestion")
    return render(request, "lamane/forms/confirm_delete.html", {
        "obj": obj, "titre": obj.nom, "page": "vitrine_gestion",
        "back_url": "/vitrine/gestion/",
    })


# ── Temoignages CRUD ──────────────────────────────────────────────────────

@login_required
@role_required()
def vitrine_temoignage_create_view(request):
    if request.method == "POST":
        kwargs = {
            "nom": request.POST.get("nom", ""),
            "titre": request.POST.get("titre", ""),
            "texte": request.POST.get("texte", ""),
            "ordre": int(request.POST.get("ordre", 0)),
        }
        if "photo" in request.FILES:
            kwargs["photo"] = request.FILES["photo"]
        TemoignageVitrine.objects.create(**kwargs)
        messages.success(request, "Temoignage ajoute.")
        return redirect("ui_vitrine_gestion")
    return render(request, "lamane/forms/vitrine_item_form.html", {
        "page": "vitrine_gestion", "title": "Nouveau temoignage",
        "item_type": "temoignage", "action": "Creer",
    })


@login_required
@role_required()
def vitrine_temoignage_edit_view(request, pk):
    obj = get_object_or_404(TemoignageVitrine, pk=pk)
    if request.method == "POST":
        obj.nom = request.POST.get("nom", obj.nom)
        obj.titre = request.POST.get("titre", obj.titre)
        obj.texte = request.POST.get("texte", obj.texte)
        obj.ordre = int(request.POST.get("ordre", obj.ordre))
        obj.actif = "actif" in request.POST
        if "photo" in request.FILES:
            obj.photo = request.FILES["photo"]
        obj.save()
        messages.success(request, "Temoignage modifie.")
        return redirect("ui_vitrine_gestion")
    return render(request, "lamane/forms/vitrine_item_form.html", {
        "page": "vitrine_gestion", "title": f"Modifier — Temoignage de {obj.nom}",
        "item_type": "temoignage", "action": "Enregistrer", "obj": obj,
    })


@login_required
@role_required()
def vitrine_temoignage_delete_view(request, pk):
    obj = get_object_or_404(TemoignageVitrine, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Temoignage supprime.")
        return redirect("ui_vitrine_gestion")
    return render(request, "lamane/forms/confirm_delete.html", {
        "obj": obj, "titre": f"Temoignage de {obj.nom}", "page": "vitrine_gestion",
        "back_url": "/vitrine/gestion/",
    })
