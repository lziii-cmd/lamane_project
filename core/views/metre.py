# core/views/metre.py
"""Vues du module Metre sur plan — LAMANE BTP."""
import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, F
from django.contrib import messages

from core.models import (
    Projet, PlanMetre, TraceMetre, TypeElement, LotMetre,
)
from core.permissions import role_required

__all__ = [
    "metre_list_view",
    "metre_plan_upload_view",
    "metre_canvas_view",
    "metre_plan_delete_view",
    "metre_api_save_echelle",
    "metre_api_save_trace",
    "metre_api_delete_trace",
    "metre_api_get_traces",
    "metre_recap_view",
    "metre_types_elements_view",
    "metre_type_element_create_view",
    "metre_type_element_edit_view",
    "metre_type_element_delete_view",
    "metre_lots_view",
]


# ═══════════════════════════════════════════════════════════════════════════
# LISTE DES PLANS D'UN PROJET
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def metre_list_view(request, projet_pk):
    """Liste des plans de metre d'un projet."""
    projet = get_object_or_404(Projet, pk=projet_pk)
    plans = PlanMetre.objects.filter(projet=projet).order_by("ordre")

    plans_data = []
    for p in plans:
        nb_traces = p.traces.count()
        total_montant = 0
        for t in p.traces.all():
            total_montant += t.montant_total
        plans_data.append({
            "plan": p,
            "nb_traces": nb_traces,
            "total_montant": total_montant,
        })

    ctx = {
        "page": "projets",
        "projet": projet,
        "plans_data": plans_data,
        "types_elements": TypeElement.objects.filter(actif=True),
    }
    return render(request, "lamane/metre_list.html", ctx)


# ═══════════════════════════════════════════════════════════════════════════
# UPLOAD D'UN PLAN PDF
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def metre_plan_upload_view(request, projet_pk):
    """Uploader un nouveau plan PDF."""
    projet = get_object_or_404(Projet, pk=projet_pk)
    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        ordre = int(request.POST.get("ordre", 0))
        fichier = request.FILES.get("fichier_pdf")
        if nom and fichier:
            PlanMetre.objects.create(
                projet=projet, nom=nom, ordre=ordre, fichier_pdf=fichier,
            )
            messages.success(request, f"Plan « {nom} » ajoute.")
            return redirect("ui_metre_list", projet_pk=projet.pk)
        else:
            messages.error(request, "Nom et fichier PDF requis.")

    ctx = {
        "page": "projets", "projet": projet,
        "title": "Ajouter un plan",
    }
    return render(request, "lamane/forms/metre_plan_form.html", ctx)


@login_required
def metre_plan_delete_view(request, pk):
    """Supprimer un plan."""
    plan = get_object_or_404(PlanMetre, pk=pk)
    projet_pk = plan.projet.pk
    if request.method == "POST":
        plan.delete()
        messages.success(request, "Plan supprime.")
        return redirect("ui_metre_list", projet_pk=projet_pk)
    return render(request, "lamane/forms/confirm_delete.html", {
        "obj": plan, "titre": str(plan), "page": "projets",
        "back_url": f"/projets/{projet_pk}/metres/",
    })


# ═══════════════════════════════════════════════════════════════════════════
# CANVAS INTERACTIF — EDITEUR DE METRE
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def metre_canvas_view(request, pk):
    """Editeur de metre : canvas interactif sur le plan PDF."""
    plan = get_object_or_404(PlanMetre, pk=pk)
    types_elements = TypeElement.objects.filter(actif=True).order_by("ordre")
    traces = plan.traces.select_related("type_element").all()

    # Preparer les traces en JSON pour le canvas
    traces_json = []
    for t in traces:
        traces_json.append({
            "id": str(t.id),
            "type_element_id": str(t.type_element.id),
            "nom": t.type_element.nom,
            "couleur": t.type_element.couleur,
            "outil": t.type_element.outil,
            "unite": t.type_element.unite,
            "coordonnees": t.coordonnees,
            "longueur_metres": round(t.longueur_metres, 2),
            "surface_metres": round(t.surface_metres, 2),
            "volume_metres": round(t.volume_metres, 3),
            "quantite": round(t.quantite, 2),
            "commentaire": t.commentaire,
        })

    # Types elements en JSON
    types_json = []
    for te in types_elements:
        types_json.append({
            "id": str(te.id),
            "nom": te.nom,
            "couleur": te.couleur,
            "unite": te.unite,
            "outil": te.outil,
            "epaisseur": float(te.epaisseur_defaut),
            "prix_unitaire": float(te.prix_unitaire),
        })

    ctx = {
        "page": "projets",
        "plan": plan,
        "projet": plan.projet,
        "types_elements": types_elements,
        "types_json": json.dumps(types_json),
        "traces_json": json.dumps(traces_json),
        "echelle_pixels": plan.echelle_pixels,
        "echelle_metres": plan.echelle_metres,
    }
    return render(request, "lamane/metre_canvas.html", ctx)


# ═══════════════════════════════════════════════════════════════════════════
# API JSON — SAUVEGARDE DEPUIS LE CANVAS
# ═══════════════════════════════════════════════════════════════════════════

@require_POST
@login_required
def metre_api_save_echelle(request, pk):
    """Sauvegarder l'echelle du plan."""
    plan = get_object_or_404(PlanMetre, pk=pk)
    try:
        data = json.loads(request.body)
        plan.echelle_pixels = float(data.get("pixels", 0))
        plan.echelle_metres = float(data.get("metres", 1))
        plan.save()

        # Recalculer tous les traces existants
        for trace in plan.traces.all():
            trace.save()  # Declenche calculer()

        return JsonResponse({"ok": True, "ratio": plan.ratio_pixel_metre})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)


@require_POST
@login_required
def metre_api_save_trace(request, pk):
    """Sauvegarder un trace (nouveau ou modifie)."""
    plan = get_object_or_404(PlanMetre, pk=pk)
    try:
        data = json.loads(request.body)
        trace_id = data.get("id")
        type_element_id = data.get("type_element_id")
        coordonnees = data.get("coordonnees", {})
        longueur_pixels = float(data.get("longueur_pixels", 0))
        surface_pixels = float(data.get("surface_pixels", 0))
        commentaire = data.get("commentaire", "")

        type_element = get_object_or_404(TypeElement, pk=type_element_id)

        if trace_id:
            trace = get_object_or_404(TraceMetre, pk=trace_id, plan=plan)
        else:
            trace = TraceMetre(plan=plan)

        trace.type_element = type_element
        trace.coordonnees = coordonnees
        trace.longueur_pixels = longueur_pixels
        trace.surface_pixels = surface_pixels
        trace.commentaire = commentaire

        # Surcharges optionnelles
        epaisseur = data.get("epaisseur")
        if epaisseur is not None:
            trace.epaisseur = Decimal(str(epaisseur))
        prix = data.get("prix_unitaire")
        if prix is not None:
            trace.prix_unitaire = Decimal(str(prix))

        trace.save()  # Declenche calculer()

        return JsonResponse({
            "ok": True,
            "id": str(trace.id),
            "longueur_metres": round(trace.longueur_metres, 2),
            "surface_metres": round(trace.surface_metres, 2),
            "volume_metres": round(trace.volume_metres, 3),
            "quantite": round(trace.quantite, 2),
            "montant": round(trace.montant_total, 0),
        })
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)


@require_POST
@login_required
def metre_api_delete_trace(request, pk):
    """Supprimer un trace."""
    trace = get_object_or_404(TraceMetre, pk=pk)
    trace.delete()
    return JsonResponse({"ok": True})


@login_required
def metre_api_get_traces(request, pk):
    """Retourner tous les traces d'un plan en JSON."""
    plan = get_object_or_404(PlanMetre, pk=pk)
    traces = plan.traces.select_related("type_element").all()
    data = []
    for t in traces:
        data.append({
            "id": str(t.id),
            "type_element_id": str(t.type_element.id),
            "nom": t.type_element.nom,
            "couleur": t.type_element.couleur,
            "outil": t.type_element.outil,
            "unite": t.type_element.unite,
            "coordonnees": t.coordonnees,
            "longueur_metres": round(t.longueur_metres, 2),
            "surface_metres": round(t.surface_metres, 2),
            "volume_metres": round(t.volume_metres, 3),
            "quantite": round(t.quantite, 2),
            "montant": round(t.montant_total, 0),
            "commentaire": t.commentaire,
        })
    return JsonResponse({"traces": data, "echelle_definie": plan.echelle_definie})


# ═══════════════════════════════════════════════════════════════════════════
# RECAP DU METRE
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def metre_recap_view(request, projet_pk):
    """Tableau recapitulatif du metre complet d'un projet."""
    projet = get_object_or_404(Projet, pk=projet_pk)
    plans = PlanMetre.objects.filter(projet=projet).order_by("ordre")
    lots = LotMetre.objects.all().order_by("ordre")

    # Construire le recap par lot
    recap = []
    total_general = 0

    for lot in lots:
        lignes = []
        total_lot = 0
        types = TypeElement.objects.filter(lot=lot, actif=True)
        for te in types:
            traces = TraceMetre.objects.filter(
                plan__projet=projet, type_element=te,
            )
            if not traces.exists():
                continue
            total_quantite = sum(t.quantite for t in traces)
            total_montant = sum(t.montant_total for t in traces)
            total_lot += total_montant
            lignes.append({
                "type_element": te,
                "nb_traces": traces.count(),
                "quantite": round(total_quantite, 2),
                "prix_unitaire": float(te.prix_unitaire),
                "montant": round(total_montant, 0),
            })
        if lignes:
            recap.append({"lot": lot, "lignes": lignes, "total": total_lot})
            total_general += total_lot

    # Elements sans lot
    types_sans_lot = TypeElement.objects.filter(lot__isnull=True, actif=True)
    lignes_sans_lot = []
    total_sans_lot = 0
    for te in types_sans_lot:
        traces = TraceMetre.objects.filter(plan__projet=projet, type_element=te)
        if not traces.exists():
            continue
        total_quantite = sum(t.quantite for t in traces)
        total_montant = sum(t.montant_total for t in traces)
        total_sans_lot += total_montant
        lignes_sans_lot.append({
            "type_element": te,
            "nb_traces": traces.count(),
            "quantite": round(total_quantite, 2),
            "prix_unitaire": float(te.prix_unitaire),
            "montant": round(total_montant, 0),
        })
    if lignes_sans_lot:
        recap.append({"lot": None, "lignes": lignes_sans_lot, "total": total_sans_lot})
        total_general += total_sans_lot

    ctx = {
        "page": "projets", "projet": projet,
        "plans": plans, "recap": recap,
        "total_general": total_general,
    }
    return render(request, "lamane/metre_recap.html", ctx)


# ═══════════════════════════════════════════════════════════════════════════
# CONFIG — TYPES D'ELEMENTS & LOTS
# ═══════════════════════════════════════════════════════════════════════════

@login_required
@role_required("comptable", "chef_chantier")
def metre_types_elements_view(request):
    """Liste des types d'elements configurables."""
    types = TypeElement.objects.select_related("lot").all()
    lots = LotMetre.objects.all()
    ctx = {
        "page": "types_elements_metre",
        "types": types, "lots": lots,
        "total": types.count(),
    }
    return render(request, "lamane/metre_types_elements.html", ctx)


@login_required
@role_required("comptable", "chef_chantier")
def metre_type_element_create_view(request):
    if request.method == "POST":
        lot_id = request.POST.get("lot")
        lot = LotMetre.objects.filter(pk=lot_id).first() if lot_id else None
        TypeElement.objects.create(
            nom=request.POST.get("nom", ""),
            lot=lot,
            couleur=request.POST.get("couleur", "#FF0000"),
            unite=request.POST.get("unite", "ml"),
            outil=request.POST.get("outil", "ligne"),
            epaisseur_defaut=Decimal(request.POST.get("epaisseur_defaut", "0")),
            prix_unitaire=Decimal(request.POST.get("prix_unitaire", "0")),
            ordre=int(request.POST.get("ordre", 0)),
        )
        messages.success(request, "Type d'element cree.")
        return redirect("ui_metre_types_elements")
    lots = LotMetre.objects.all()
    return render(request, "lamane/forms/metre_type_element_form.html", {
        "page": "types_elements_metre", "title": "Nouveau type d'element",
        "action": "Creer", "lots": lots,
    })


@login_required
@role_required("comptable", "chef_chantier")
def metre_type_element_edit_view(request, pk):
    obj = get_object_or_404(TypeElement, pk=pk)
    if request.method == "POST":
        lot_id = request.POST.get("lot")
        obj.lot = LotMetre.objects.filter(pk=lot_id).first() if lot_id else None
        obj.nom = request.POST.get("nom", obj.nom)
        obj.couleur = request.POST.get("couleur", obj.couleur)
        obj.unite = request.POST.get("unite", obj.unite)
        obj.outil = request.POST.get("outil", obj.outil)
        obj.epaisseur_defaut = Decimal(request.POST.get("epaisseur_defaut", "0"))
        obj.prix_unitaire = Decimal(request.POST.get("prix_unitaire", "0"))
        obj.ordre = int(request.POST.get("ordre", obj.ordre))
        obj.actif = "actif" in request.POST
        obj.save()
        messages.success(request, "Type d'element modifie.")
        return redirect("ui_metre_types_elements")
    lots = LotMetre.objects.all()
    return render(request, "lamane/forms/metre_type_element_form.html", {
        "page": "types_elements_metre", "title": f"Modifier — {obj.nom}",
        "action": "Enregistrer", "obj": obj, "lots": lots,
    })


@login_required
@role_required("comptable", "chef_chantier")
def metre_type_element_delete_view(request, pk):
    obj = get_object_or_404(TypeElement, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Type d'element supprime.")
        return redirect("ui_metre_types_elements")
    return render(request, "lamane/forms/confirm_delete.html", {
        "obj": obj, "titre": obj.nom, "page": "types_elements_metre",
        "back_url": "/metres/types-elements/",
    })


@login_required
@role_required("comptable", "chef_chantier")
def metre_lots_view(request):
    """Gestion des lots de metre."""
    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        code = request.POST.get("code", "").strip()
        ordre = int(request.POST.get("ordre", 0))
        if nom:
            LotMetre.objects.create(nom=nom, code=code, ordre=ordre)
            messages.success(request, f"Lot « {nom} » cree.")
        return redirect("ui_metre_lots")

    lots = LotMetre.objects.all()
    ctx = {"page": "types_elements_metre", "lots": lots}
    return render(request, "lamane/metre_lots.html", ctx)
