# core/views/sous_traitants.py
"""Vues sous-traitants — LAMANE BTP."""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.db.models.functions import Coalesce
from decimal import Decimal
import json

from core.models import SousTraitant, ContratSousTraitance
from core.forms import SousTraitantForm, ContratSousTraitanceForm
from core.permissions import role_required
from core.services.comptabilite import generer_ecriture_sous_traitance
from core.views._helpers import _fmt, _success

__all__ = [
    "sous_traitants_view", "sous_traitant_create_view",
    "sous_traitant_detail_view", "sous_traitant_edit_view",
    "sous_traitant_delete_view", "contrat_st_create_view",
]


@login_required
@role_required("chef_chantier", "comptable")
def sous_traitants_view(request):
    sous_traitants = SousTraitant.objects.all().order_by("nom")
    st_data = []
    for st in sous_traitants:
        contrats = ContratSousTraitance.objects.filter(sous_traitant=st)
        total_m  = contrats.aggregate(s=Coalesce(Sum("montant"), Decimal("0")))["s"]
        total_p  = contrats.aggregate(s=Coalesce(Sum("montant_paye"), Decimal("0")))["s"]
        st_data.append({
            "st": st, "nb_contrats": contrats.count(),
            "total_montant": float(total_m), "total_montant_fmt": _fmt(total_m),
            "total_paye": float(total_p), "total_paye_fmt": _fmt(total_p),
            "reste": _fmt(float(total_m) - float(total_p)),
            "taux_paiement": round(float(total_p) / float(total_m) * 100 if total_m > 0 else 0, 1),
        })

    specialites = SousTraitant.objects.values("specialite").annotate(
        count=Count("id"),
        total=Coalesce(Sum("contrats__montant"), Decimal("0")),
    )
    ctx = {
        "page": "sous_traitants", "st_data": st_data,
        "total_st": len(st_data),
        "total_contrats": ContratSousTraitance.objects.count(),
        "total_montant_st": _fmt(ContratSousTraitance.objects.aggregate(s=Coalesce(Sum("montant"), Decimal("0")))["s"]),
        "total_paye_st":    _fmt(ContratSousTraitance.objects.aggregate(s=Coalesce(Sum("montant_paye"), Decimal("0")))["s"]),
        "specialites": list(specialites),
        "contrats_recents": ContratSousTraitance.objects.select_related("sous_traitant", "projet").order_by("-date_debut")[:15],
        "st_labels_json":   json.dumps([d["st"].nom for d in st_data]),
        "st_montants_json": json.dumps([d["total_montant"] for d in st_data]),
    }
    return render(request, "lamane/sous_traitants.html", ctx)


@login_required
@role_required("chef_chantier", "comptable")
def sous_traitant_create_view(request):
    form = SousTraitantForm(request.POST or None)
    if form.is_valid():
        st = form.save()
        return _success(request, f"Sous-traitant « {st.nom} » créé.", "ui_sous_traitants")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": "Nouveau sous-traitant",
                   "action": "Créer", "page": "sous_traitants", "back_url": "/sous-traitants/"})


@login_required
@role_required("chef_chantier", "comptable")
def sous_traitant_detail_view(request, pk):
    st = get_object_or_404(SousTraitant, pk=pk)
    contrats = ContratSousTraitance.objects.filter(sous_traitant=st).select_related("projet").order_by("-date_debut")
    total_montant = contrats.aggregate(s=Coalesce(Sum("montant"), Decimal("0")))["s"]
    total_paye    = contrats.aggregate(s=Coalesce(Sum("montant_paye"), Decimal("0")))["s"]
    ctx = {
        "page": "sous_traitants", "st": st, "contrats": contrats,
        "total_montant": _fmt(total_montant), "total_paye": _fmt(total_paye),
        "reste": _fmt(float(total_montant) - float(total_paye)),
        "taux_paiement": round(float(total_paye) / float(total_montant) * 100 if total_montant > 0 else 0, 1),
    }
    return render(request, "lamane/sous_traitant_detail.html", ctx)


@login_required
@role_required("chef_chantier", "comptable")
def sous_traitant_edit_view(request, pk):
    st = get_object_or_404(SousTraitant, pk=pk)
    form = SousTraitantForm(request.POST or None, instance=st)
    if form.is_valid():
        form.save()
        return _success(request, "Sous-traitant modifié.", "ui_sous_traitants")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": f"Modifier — {st.nom}",
                   "action": "Enregistrer", "page": "sous_traitants",
                   "back_url": "/sous-traitants/", "obj": st})


@login_required
@role_required("comptable")
def sous_traitant_delete_view(request, pk):
    st = get_object_or_404(SousTraitant, pk=pk)
    if request.method == "POST":
        st.delete()
        return _success(request, f"Sous-traitant « {st.nom} » supprimé.", "ui_sous_traitants")
    return render(request, "lamane/forms/confirm_delete.html",
                  {"obj": st, "titre": st.nom, "page": "sous_traitants",
                   "back_url": "/sous-traitants/"})


@login_required
@role_required("chef_chantier", "comptable")
def contrat_st_create_view(request):
    form = ContratSousTraitanceForm(request.POST or None)
    if form.is_valid():
        c = form.save(commit=False)
        c.save()
        try:
            c.generate_contrat_pdf()
            c.save(update_fields=["contrat_pdf"])
        except Exception:
            pass
        try:
            generer_ecriture_sous_traitance(c)
        except Exception as e:
            print(f"[COMPTA] Erreur écriture sous-traitance: {e}")
        return _success(request, "Contrat créé — PDF généré.", "ui_sous_traitants")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": "Nouveau contrat de sous-traitance",
                   "action": "Créer", "page": "sous_traitants", "back_url": "/sous-traitants/"})
