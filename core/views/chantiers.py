# core/views/chantiers.py
"""Vues chantiers, avancements, étapes — LAMANE BTP."""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg
from django.db.models.functions import Coalesce
import json

from core.models import (
    Projet, AvancementChantier, MarcheTravaux,
    ContratSousTraitance, SituationMensuelle, EtapeStandard,
)
from core.forms import AvancementChantierForm, EtapeStandardForm
from core.permissions import role_required
from core.views._helpers import _success

__all__ = [
    "chantiers_view", "chantier_detail_view", "avancement_create_view",
    "etapes_standard_view", "etape_standard_create_view",
    "etape_standard_edit_view", "etape_standard_delete_view",
]


@login_required
@role_required("chef_chantier", "comptable")
def chantiers_view(request):
    projets_actifs = Projet.objects.filter(statut="En cours").select_related("proprietaire", "type_projet")
    chantiers_data = []
    for p in projets_actifs:
        chantiers_data.append({
            "projet": p,
            "dernier_avancement": AvancementChantier.objects.filter(projet=p).order_by("-periode").first(),
            "marche": MarcheTravaux.objects.filter(projet=p).first(),
            "nb_contrats_st": ContratSousTraitance.objects.filter(projet=p).count(),
        })

    ctx = {
        "page": "chantiers", "chantiers_data": chantiers_data,
        "avancements_all": AvancementChantier.objects.select_related("projet").order_by("-periode")[:50],
        "avg_physique":  round(AvancementChantier.objects.filter(projet__statut="En cours").aggregate(avg=Avg("taux_physique"))["avg"] or 0, 1),
        "avg_financier": round(AvancementChantier.objects.filter(projet__statut="En cours").aggregate(avg=Avg("taux_financier"))["avg"] or 0, 1),
        "avg_planifie":  round(AvancementChantier.objects.filter(projet__statut="En cours").aggregate(avg=Avg("taux_planifie"))["avg"] or 0, 1),
        "total_ouvriers":    AvancementChantier.objects.filter(projet__statut="En cours").aggregate(s=Coalesce(Sum("effectif_ouvriers"), 0))["s"],
        "total_encadrement": AvancementChantier.objects.filter(projet__statut="En cours").aggregate(s=Coalesce(Sum("effectif_encadrement"), 0))["s"],
        "nb_chantiers": len(chantiers_data),
    }
    return render(request, "lamane/chantiers.html", ctx)


@login_required
@role_required("chef_chantier", "comptable")
def chantier_detail_view(request, pk):
    projet      = get_object_or_404(Projet, pk=pk)
    avancements = AvancementChantier.objects.filter(projet=projet).order_by("periode")
    marche      = MarcheTravaux.objects.filter(projet=projet).first()
    contrats_st = ContratSousTraitance.objects.filter(projet=projet).select_related("sous_traitant")
    situations  = SituationMensuelle.objects.filter(projet=projet).order_by("numero_situation")

    dernier_av      = avancements.last()
    avg_ouvriers    = avancements.aggregate(avg=Avg("effectif_ouvriers"))["avg"] or 0
    avg_encadrement = avancements.aggregate(avg=Avg("effectif_encadrement"))["avg"] or 0

    ctx = {
        "page": "chantiers", "projet": projet, "marche": marche,
        "avancements": avancements, "dernier_av": dernier_av,
        "contrats_st": contrats_st, "situations": situations,
        "avg_ouvriers": round(avg_ouvriers, 0), "avg_encadrement": round(avg_encadrement, 0),
        "nb_releves": avancements.count(),
        "av_labels_json":    json.dumps([str(a.periode) for a in avancements]),
        "av_physique_json":  json.dumps([float(a.taux_physique) for a in avancements]),
        "av_financier_json": json.dumps([float(a.taux_financier) for a in avancements]),
        "av_planifie_json":  json.dumps([float(a.taux_planifie) for a in avancements]),
        "av_ouvriers_json":  json.dumps([a.effectif_ouvriers for a in avancements]),
    }
    return render(request, "lamane/chantier_detail.html", ctx)


@login_required
@role_required("chef_chantier")
def avancement_create_view(request):
    projet_id = request.GET.get("projet")
    initial = {}
    if projet_id:
        try:
            initial["projet"] = Projet.objects.get(pk=projet_id)
        except Projet.DoesNotExist:
            pass
    form = AvancementChantierForm(request.POST or None, initial=initial)
    if form.is_valid():
        form.save()
        proj_id = form.cleaned_data["projet"].id
        return _success(request, "Relevé d'avancement enregistré.", f"/chantiers/{proj_id}/")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": "Nouveau relevé d'avancement",
                   "action": "Enregistrer", "page": "chantiers", "back_url": "/chantiers/"})


@login_required
@role_required("chef_chantier")
def etapes_standard_view(request):
    etapes = EtapeStandard.objects.all().order_by("ordre")
    ctx = {
        "page": "etapes_standard", "etapes": etapes,
        "total_gros": etapes.filter(groupe="gros").count(),
        "total_second": etapes.filter(groupe="second").count(),
    }
    return render(request, "lamane/etapes_standard.html", ctx)


@login_required
@role_required("chef_chantier")
def etape_standard_create_view(request):
    form = EtapeStandardForm(request.POST or None)
    if form.is_valid():
        e = form.save()
        return _success(request, f"Étape « {e.nom} » créée.", "ui_etapes_standard")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": "Nouvelle étape standard",
                   "action": "Créer", "page": "etapes_standard", "back_url": "/etapes-standard/"})


@login_required
@role_required("chef_chantier")
def etape_standard_edit_view(request, pk):
    e = get_object_or_404(EtapeStandard, pk=pk)
    form = EtapeStandardForm(request.POST or None, instance=e)
    if form.is_valid():
        form.save()
        return _success(request, "Étape modifiée.", "ui_etapes_standard")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": f"Modifier — {e.nom}",
                   "action": "Enregistrer", "page": "etapes_standard",
                   "back_url": "/etapes-standard/", "obj": e})


@login_required
@role_required()
def etape_standard_delete_view(request, pk):
    e = get_object_or_404(EtapeStandard, pk=pk)
    if request.method == "POST":
        nom = e.nom
        e.delete()
        return _success(request, f"Étape « {nom} » supprimée.", "ui_etapes_standard")
    return render(request, "lamane/forms/confirm_delete.html",
                  {"obj": e, "titre": e.nom, "page": "etapes_standard",
                   "back_url": "/etapes-standard/"})
