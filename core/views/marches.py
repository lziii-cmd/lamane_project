# core/views/marches.py
"""Vues marchés de travaux — LAMANE BTP."""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.db.models.functions import Coalesce
from decimal import Decimal
import json

from core.models import MarcheTravaux
from core.forms import MarcheTravauxForm
from core.permissions import role_required
from core.views._helpers import _fmt, _success

__all__ = ["marches_view", "marche_create_view", "marche_edit_view"]


@login_required
@role_required("chef_chantier", "comptable")
def marches_view(request):
    statut_filter = request.GET.get("statut", "")
    marches = MarcheTravaux.objects.select_related("projet").order_by("-date_signature")
    if statut_filter:
        marches = marches.filter(statut=statut_filter)
    montant_total = MarcheTravaux.objects.aggregate(s=Coalesce(Sum("montant_marche"), Decimal("0")))["s"]
    avance_totale = MarcheTravaux.objects.aggregate(s=Coalesce(Sum("montant_avance_demarrage"), Decimal("0")))["s"]
    statuts_marche = MarcheTravaux.objects.values("statut").annotate(
        count=Count("id"), total=Coalesce(Sum("montant_marche"), Decimal("0"))
    )
    LABELS = {"en_attente": "En attente", "en_cours": "En cours",
              "reception_provisoire": "Récept. provisoire", "reception_definitive": "Récept. définitive"}
    ctx = {
        "page": "marches", "marches": marches, "statut_filter": statut_filter,
        "total_marches": MarcheTravaux.objects.count(),
        "montant_total": _fmt(montant_total), "avance_totale": _fmt(avance_totale),
        "en_cours_m": MarcheTravaux.objects.filter(statut="en_cours").count(),
        "termines_m": MarcheTravaux.objects.filter(statut="reception_definitive").count(),
        "statuts_marche": list(statuts_marche), "statuts_labels": LABELS,
        "statuts_marche_json": json.dumps([
            {"statut": s["statut"], "count": s["count"], "total": float(s["total"])}
            for s in statuts_marche
        ]),
    }
    return render(request, "lamane/marches.html", ctx)


@login_required
@role_required("comptable", "chef_chantier")
def marche_create_view(request):
    form = MarcheTravauxForm(request.POST or None)
    if form.is_valid():
        m = form.save()
        return _success(request, f"Marché {m.numero_marche} créé.", "ui_marches")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": "Nouveau marché de travaux",
                   "action": "Créer", "page": "marches", "back_url": "/marches/"})


@login_required
@role_required("comptable", "chef_chantier")
def marche_edit_view(request, pk):
    marche = get_object_or_404(MarcheTravaux, pk=pk)
    form = MarcheTravauxForm(request.POST or None, instance=marche)
    if form.is_valid():
        form.save()
        return _success(request, "Marché modifié.", "ui_marches")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": f"Modifier — {marche.numero_marche}",
                   "action": "Enregistrer", "page": "marches",
                   "back_url": "/marches/", "obj": marche})
