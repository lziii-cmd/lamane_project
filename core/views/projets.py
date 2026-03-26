# core/views/projets.py
"""Vues projets — LAMANE BTP."""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from decimal import Decimal
import json

from core.models import (
    Projet, Achat, Versement, MarcheTravaux, AvancementChantier,
    ContratSousTraitance, SituationMensuelle, ProjetEmploye,
)
from core.forms import ProjetForm
from core.permissions import role_required
from core.views._helpers import _fmt, _success

__all__ = [
    "projets_list_view", "projet_detail_view",
    "projet_create_view", "projet_edit_view", "projet_delete_view",
]


@login_required
def projets_list_view(request):
    q             = request.GET.get("q", "")
    statut_filter = request.GET.get("statut", "")
    projets = Projet.objects.select_related("proprietaire", "type_projet").all()
    if q:
        projets = projets.filter(Q(nom__icontains=q) | Q(localisation__icontains=q))
    if statut_filter:
        projets = projets.filter(statut=statut_filter)
    projets = projets.order_by("-date_debut")

    projets_data = []
    for p in projets[:60]:
        total_achats = Achat.objects.filter(projet=p).aggregate(s=Coalesce(Sum("total_ttc"), Decimal("0")))["s"]
        marche       = MarcheTravaux.objects.filter(projet=p).first()
        avancement   = AvancementChantier.objects.filter(projet=p).order_by("-periode").first()
        projets_data.append({
            "projet": p, "total_achats": float(total_achats),
            "total_achats_fmt": _fmt(total_achats), "marche": marche, "avancement": avancement,
        })

    ctx = {
        "page": "projets",
        "projets_data": projets_data,
        "total_projets": Projet.objects.count(),
        "q": q, "statut_filter": statut_filter,
        "statuts": ["En cours", "En attente", "En pause", "Terminé"],
        "nb_resultats": len(projets_data),
    }
    return render(request, "lamane/projets_list.html", ctx)


@login_required
def projet_detail_view(request, pk):
    projet     = get_object_or_404(Projet, pk=pk)
    achats     = Achat.objects.filter(projet=projet).select_related("fournisseur").order_by("-date_achat")
    versements = Versement.objects.filter(projet=projet).select_related("phase").order_by("-date_versement")
    marche     = MarcheTravaux.objects.filter(projet=projet).first()
    avancements = AvancementChantier.objects.filter(projet=projet).order_by("periode")
    situations  = SituationMensuelle.objects.filter(projet=projet).order_by("numero_situation")
    contrats_st = ContratSousTraitance.objects.filter(projet=projet).select_related("sous_traitant")
    employes_affectes = ProjetEmploye.objects.filter(projet=projet).select_related("employe")

    total_achats = achats.aggregate(
        ht=Coalesce(Sum("total_ht"), Decimal("0")),
        ttc=Coalesce(Sum("total_ttc"), Decimal("0")),
    )
    total_verse = versements.aggregate(s=Coalesce(Sum("montant"), Decimal("0")))["s"]
    solde_val   = float(total_verse) - float(total_achats["ttc"])

    av_labels    = [str(a.periode) for a in avancements]
    av_physique  = [float(a.taux_physique) for a in avancements]
    av_financier = [float(a.taux_financier) for a in avancements]
    av_planifie  = [float(a.taux_planifie) for a in avancements]

    ctx = {
        "page": "projets", "projet": projet,
        "achats": achats, "versements": versements, "marche": marche,
        "avancements": avancements, "situations": situations,
        "contrats_st": contrats_st, "employes_affectes": employes_affectes,
        "total_achats_ht": _fmt(total_achats["ht"]),
        "total_achats_ttc": _fmt(total_achats["ttc"]),
        "total_verse": _fmt(total_verse),
        "solde": _fmt(abs(solde_val)), "solde_positif": solde_val >= 0,
        "av_labels_json":    json.dumps(av_labels),
        "av_physique_json":  json.dumps(av_physique),
        "av_financier_json": json.dumps(av_financier),
        "av_planifie_json":  json.dumps(av_planifie),
    }
    return render(request, "lamane/projet_detail.html", ctx)


@login_required
@role_required("comptable", "chef_chantier")
def projet_create_view(request):
    form = ProjetForm(request.POST or None)
    if form.is_valid():
        p = form.save()
        return _success(request, f"Projet « {p.nom} » créé avec succès.", "ui_projets_list")
    return render(request, "lamane/forms/projet_form.html",
                  {"form": form, "title": "Nouveau projet", "action": "Créer", "page": "projets"})


@login_required
@role_required("comptable", "chef_chantier")
def projet_edit_view(request, pk):
    projet = get_object_or_404(Projet, pk=pk)
    form = ProjetForm(request.POST or None, instance=projet)
    if form.is_valid():
        form.save()
        return _success(request, "Projet modifié.", f"/projets/{pk}/")
    return render(request, "lamane/forms/projet_form.html",
                  {"form": form, "title": f"Modifier — {projet.nom}",
                   "action": "Enregistrer", "page": "projets", "obj": projet})


@login_required
@role_required()
def projet_delete_view(request, pk):
    projet = get_object_or_404(Projet, pk=pk)
    if request.method == "POST":
        nom = projet.nom
        projet.delete()
        return _success(request, f"Projet « {nom} » supprimé.", "ui_projets_list")
    return render(request, "lamane/forms/confirm_delete.html",
                  {"obj": projet, "titre": projet.nom, "page": "projets",
                   "back_url": f"/projets/{pk}/"})
