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
    Projet, PlanMetre, TraceMetre, TypeElement, LotMetre, Devis,
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
    # Devis
    "devis_list_view",
    "devis_create_view",
    "devis_detail_view",
    "devis_edit_view",
    "devis_delete_view",
    "devis_plan_upload_view",
    "devis_plan_list_view",
    "devis_recap_view",
    "devis_convertir_projet_view",
    "devis_changer_statut_view",
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


# ═══════════════════════════════════════════════════════════════════════════
# DEVIS — CRUD
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def devis_list_view(request):
    """Liste de tous les devis."""
    devis = Devis.objects.all().order_by("-date_creation")
    statut_filter = request.GET.get("statut", "")
    if statut_filter:
        devis = devis.filter(statut=statut_filter)

    devis_data = []
    for d in devis:
        devis_data.append({
            "devis": d,
            "nb_plans": d.nb_plans,
            "total": d.total_metre,
            "total_ttc": d.total_ttc,
        })

    ctx = {
        "page": "devis",
        "devis_data": devis_data,
        "total_devis": Devis.objects.count(),
        "statut_filter": statut_filter,
    }
    return render(request, "lamane/devis_list.html", ctx)


@login_required
def devis_create_view(request):
    """Creer un nouveau devis."""
    if request.method == "POST":
        d = Devis.objects.create(
            titre=request.POST.get("titre", "").strip(),
            client_nom=request.POST.get("client_nom", "").strip(),
            client_telephone=request.POST.get("client_telephone", "").strip(),
            client_email=request.POST.get("client_email", "").strip(),
            localisation=request.POST.get("localisation", "").strip(),
            description=request.POST.get("description", "").strip(),
            marge_pourcentage=Decimal(request.POST.get("marge_pourcentage", "15")),
        )
        messages.success(request, f"Devis {d.reference} cree.")
        return redirect("ui_devis_detail", pk=d.pk)

    ctx = {"page": "devis", "title": "Nouveau devis", "action": "Creer"}
    return render(request, "lamane/forms/devis_form.html", ctx)


@login_required
def devis_detail_view(request, pk):
    """Detail d'un devis avec ses plans et recap."""
    d = get_object_or_404(Devis, pk=pk)
    plans = PlanMetre.objects.filter(devis=d).order_by("ordre")

    plans_data = []
    for p in plans:
        nb_traces = p.traces.count()
        total = sum(t.montant_total for t in p.traces.all())
        plans_data.append({"plan": p, "nb_traces": nb_traces, "total_montant": total})

    # Recap par lot
    recap = _build_recap_for_plans(plans)

    ctx = {
        "page": "devis", "devis": d,
        "plans_data": plans_data,
        "recap": recap["sections"],
        "total_metre": recap["total"],
        "total_marge": recap["total"] * float(d.marge_pourcentage) / 100,
        "total_ttc": recap["total"] * (1 + float(d.marge_pourcentage) / 100),
    }
    return render(request, "lamane/devis_detail.html", ctx)


@login_required
def devis_edit_view(request, pk):
    """Modifier un devis."""
    d = get_object_or_404(Devis, pk=pk)
    if request.method == "POST":
        d.titre = request.POST.get("titre", d.titre).strip()
        d.client_nom = request.POST.get("client_nom", d.client_nom).strip()
        d.client_telephone = request.POST.get("client_telephone", "").strip()
        d.client_email = request.POST.get("client_email", "").strip()
        d.localisation = request.POST.get("localisation", "").strip()
        d.description = request.POST.get("description", "").strip()
        d.marge_pourcentage = Decimal(request.POST.get("marge_pourcentage", "15"))
        d.save()
        messages.success(request, "Devis modifie.")
        return redirect("ui_devis_detail", pk=d.pk)

    ctx = {"page": "devis", "title": f"Modifier — {d.reference}", "action": "Enregistrer", "obj": d}
    return render(request, "lamane/forms/devis_form.html", ctx)


@login_required
def devis_delete_view(request, pk):
    d = get_object_or_404(Devis, pk=pk)
    if request.method == "POST":
        d.delete()
        messages.success(request, "Devis supprime.")
        return redirect("ui_devis_list")
    return render(request, "lamane/forms/confirm_delete.html", {
        "obj": d, "titre": str(d), "page": "devis", "back_url": f"/devis/{d.pk}/",
    })


@login_required
def devis_plan_upload_view(request, pk):
    """Uploader un plan pour un devis."""
    d = get_object_or_404(Devis, pk=pk)
    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        ordre = int(request.POST.get("ordre", 0))
        fichier = request.FILES.get("fichier_pdf")
        if nom and fichier:
            PlanMetre.objects.create(devis=d, nom=nom, ordre=ordre, fichier_pdf=fichier)
            messages.success(request, f"Plan « {nom} » ajoute.")
            return redirect("ui_devis_detail", pk=d.pk)
        else:
            messages.error(request, "Nom et fichier requis.")

    ctx = {"page": "devis", "devis": d, "title": "Ajouter un plan"}
    return render(request, "lamane/forms/devis_plan_form.html", ctx)


@login_required
def devis_plan_list_view(request, pk):
    """Redirige vers le detail du devis (les plans y sont affiches)."""
    return redirect("ui_devis_detail", pk=pk)


@login_required
def devis_recap_view(request, pk):
    """Recapitulatif metre d'un devis."""
    d = get_object_or_404(Devis, pk=pk)
    plans = PlanMetre.objects.filter(devis=d).order_by("ordre")
    recap = _build_recap_for_plans(plans)

    ctx = {
        "page": "devis", "devis": d, "projet": None,
        "plans": plans, "recap": recap["sections"],
        "total_general": recap["total"],
        "marge_pct": float(d.marge_pourcentage),
        "total_marge": recap["total"] * float(d.marge_pourcentage) / 100,
        "total_ttc": recap["total"] * (1 + float(d.marge_pourcentage) / 100),
    }
    return render(request, "lamane/devis_recap.html", ctx)


@login_required
def devis_changer_statut_view(request, pk):
    """Changer le statut d'un devis (envoyer, valider, refuser)."""
    d = get_object_or_404(Devis, pk=pk)
    if request.method == "POST":
        from django.utils import timezone
        nouveau = request.POST.get("statut", "")
        if nouveau in dict(Devis.STATUT_CHOICES):
            d.statut = nouveau
            if nouveau == "envoye" and not d.date_envoi:
                d.date_envoi = timezone.now()
            if nouveau == "valide" and not d.date_validation:
                d.date_validation = timezone.now()
            d.save()
            labels = dict(Devis.STATUT_CHOICES)
            messages.success(request, f"Statut passe a « {labels[nouveau]} ».")
    return redirect("ui_devis_detail", pk=d.pk)


@login_required
def devis_convertir_projet_view(request, pk):
    """Convertir un devis valide en projet."""
    d = get_object_or_404(Devis, pk=pk)
    if d.projet:
        messages.info(request, "Ce devis est deja lie a un projet.")
        return redirect("ui_projet_detail", pk=d.projet.pk)

    if request.method == "POST":
        from django.utils import timezone
        from core.models import Proprietaire

        # Trouver ou creer le proprietaire/client
        # Proprietaire utilise prenom + nom separement
        parts = d.client_nom.strip().split(" ", 1)
        prenom_client = parts[0] if len(parts) > 1 else ""
        nom_client = parts[1] if len(parts) > 1 else parts[0]

        proprio, _ = Proprietaire.objects.get_or_create(
            nom=nom_client,
            defaults={
                "prenom": prenom_client,
                "telephone": d.client_telephone or "N/A",
                "email": d.client_email or None,
            },
        )

        # Creer le projet
        projet = Projet.objects.create(
            nom=d.titre,
            localisation=d.localisation or "A definir",
            statut="En attente",
            date_debut=timezone.now().date(),
            description=f"Cree a partir du devis {d.reference}.\n{d.description}",
            cout_estime_lamane=Decimal(str(round(d.total_ttc, 0))),
            proprietaire=proprio,
        )

        # Lier les plans au projet
        for plan in d.plans_metre.all():
            plan.projet = projet
            plan.save()

        # Lier le devis au projet
        d.projet = projet
        d.statut = "valide"
        if not d.date_validation:
            d.date_validation = timezone.now()
        d.save()

        messages.success(request, f"Projet « {projet.nom} » cree a partir du devis {d.reference}.")
        return redirect("ui_projet_detail", pk=projet.pk)

    ctx = {"page": "devis", "devis": d}
    return render(request, "lamane/forms/devis_convertir.html", ctx)


# ═══════════════════════════════════════════════════════════════════════════
# HELPER — Construire le recap par lot pour un queryset de plans
# ═══════════════════════════════════════════════════════════════════════════

def _build_recap_for_plans(plans):
    """Construit le recap par lot pour un ensemble de plans. Retourne {sections, total}."""
    lots = LotMetre.objects.all().order_by("ordre")
    sections = []
    total = 0

    plan_ids = [p.pk for p in plans]

    for lot in lots:
        lignes = []
        total_lot = 0
        types = TypeElement.objects.filter(lot=lot, actif=True)
        for te in types:
            traces = TraceMetre.objects.filter(plan_id__in=plan_ids, type_element=te)
            if not traces.exists():
                continue
            total_quantite = sum(t.quantite for t in traces)
            total_montant = sum(t.montant_total for t in traces)
            total_lot += total_montant
            lignes.append({
                "type_element": te, "nb_traces": traces.count(),
                "quantite": round(total_quantite, 2),
                "prix_unitaire": float(te.prix_unitaire),
                "montant": round(total_montant, 0),
            })
        if lignes:
            sections.append({"lot": lot, "lignes": lignes, "total": total_lot})
            total += total_lot

    # Sans lot
    types_sans = TypeElement.objects.filter(lot__isnull=True, actif=True)
    lignes_sans = []
    total_sans = 0
    for te in types_sans:
        traces = TraceMetre.objects.filter(plan_id__in=plan_ids, type_element=te)
        if not traces.exists():
            continue
        total_quantite = sum(t.quantite for t in traces)
        total_montant = sum(t.montant_total for t in traces)
        total_sans += total_montant
        lignes_sans.append({
            "type_element": te, "nb_traces": traces.count(),
            "quantite": round(total_quantite, 2),
            "prix_unitaire": float(te.prix_unitaire),
            "montant": round(total_montant, 0),
        })
    if lignes_sans:
        sections.append({"lot": None, "lignes": lignes_sans, "total": total_sans})
        total += total_sans

    return {"sections": sections, "total": total}
