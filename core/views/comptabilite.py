# core/views/comptabilite.py
"""Vues comptabilité SYSCOHADA — LAMANE BTP."""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import Coalesce
from decimal import Decimal

from core.models import CompteComptable, EcritureComptable, LigneEcriture
from core.forms import EcritureComptableForm, LigneEcritureFormSet
from core.permissions import role_required
from core.views._helpers import _fmt, _success

__all__ = [
    "comptabilite_journal_view", "comptabilite_grand_livre_view",
    "comptabilite_balance_view", "comptabilite_plan_view",
    "ecriture_create_view", "ecriture_detail_view",
]


@login_required
@role_required("comptable")
def comptabilite_journal_view(request):
    journal_filter = request.GET.get("journal", "")
    qs = EcritureComptable.objects.select_related("projet").prefetch_related("lignes__compte")
    if journal_filter:
        qs = qs.filter(journal=journal_filter)

    from core.pagination import paginate_queryset
    page_obj = paginate_queryset(request, qs, per_page=30)
    totaux = qs.aggregate(
        total_debit=Coalesce(Sum("lignes__debit"), Decimal("0")),
        total_credit=Coalesce(Sum("lignes__credit"), Decimal("0")),
    )
    ctx = {
        "page": "comptabilite",
        "ecritures": page_obj, "page_obj": page_obj,
        "journal_filter": journal_filter,
        "journals": EcritureComptable.JOURNAL_CHOICES,
        "total_ecritures": qs.count(),
        "total_debit": _fmt(totaux["total_debit"]),
        "total_credit": _fmt(totaux["total_credit"]),
    }
    return render(request, "lamane/comptabilite_journal.html", ctx)


@login_required
@role_required("comptable")
def comptabilite_grand_livre_view(request):
    compte_id = request.GET.get("compte", "")
    comptes = CompteComptable.objects.filter(actif=True)
    lignes = []
    compte_selectionne = None
    if compte_id:
        compte_selectionne = get_object_or_404(CompteComptable, pk=compte_id)
        lignes = LigneEcriture.objects.filter(
            compte=compte_selectionne
        ).select_related("ecriture", "ecriture__projet").order_by("ecriture__date_ecriture")
    ctx = {
        "page": "comptabilite", "comptes": comptes, "lignes": lignes,
        "compte_selectionne": compte_selectionne, "compte_id": compte_id,
    }
    return render(request, "lamane/comptabilite_grand_livre.html", ctx)


@login_required
@role_required("comptable")
def comptabilite_balance_view(request):
    comptes = CompteComptable.objects.filter(actif=True).annotate(
        total_debit=Coalesce(Sum("lignes_ecriture__debit"), Decimal("0")),
        total_credit=Coalesce(Sum("lignes_ecriture__credit"), Decimal("0")),
    ).order_by("code")

    balance_data = []
    for c in comptes:
        solde = c.total_debit - c.total_credit
        if c.total_debit > 0 or c.total_credit > 0:
            balance_data.append({
                "compte": c,
                "debit": _fmt(c.total_debit), "credit": _fmt(c.total_credit),
                "solde_debiteur": _fmt(solde) if solde > 0 else "",
                "solde_crediteur": _fmt(abs(solde)) if solde < 0 else "",
                "solde_raw": solde,
            })

    total_d = sum(c.total_debit for c in comptes)
    total_c = sum(c.total_credit for c in comptes)
    ctx = {
        "page": "comptabilite", "balance_data": balance_data,
        "total_debit": _fmt(total_d), "total_credit": _fmt(total_c),
    }
    return render(request, "lamane/comptabilite_balance.html", ctx)


@login_required
@role_required("comptable")
def comptabilite_plan_view(request):
    classe_filter = request.GET.get("classe", "")
    qs = CompteComptable.objects.all()
    if classe_filter:
        qs = qs.filter(classe=int(classe_filter))

    comptes_par_classe = {}
    for c in qs:
        comptes_par_classe.setdefault(c.classe, []).append(c)

    ctx = {
        "page": "comptabilite",
        "comptes_par_classe": dict(sorted(comptes_par_classe.items())),
        "classe_filter": classe_filter,
        "classes": CompteComptable.CLASSE_CHOICES,
        "total_comptes": qs.count(),
    }
    return render(request, "lamane/comptabilite_plan.html", ctx)


@login_required
@role_required("comptable")
def ecriture_create_view(request):
    form = EcritureComptableForm(request.POST or None)
    formset = LigneEcritureFormSet(request.POST or None, prefix="lignes")
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        ecriture = form.save()
        formset.instance = ecriture
        formset.save()
        return _success(request, f"Écriture {ecriture.numero_piece} créée.", "ui_comptabilite_journal")
    return render(request, "lamane/forms/ecriture_form.html",
                  {"form": form, "formset": formset,
                   "title": "Nouvelle écriture comptable",
                   "action": "Enregistrer", "page": "comptabilite",
                   "back_url": "/comptabilite/journal/"})


@login_required
@role_required("comptable")
def ecriture_detail_view(request, pk):
    ecriture = get_object_or_404(
        EcritureComptable.objects.prefetch_related("lignes__compte"), pk=pk
    )
    ctx = {
        "page": "comptabilite", "ecriture": ecriture,
        "lignes": ecriture.lignes.all(),
    }
    return render(request, "lamane/ecriture_detail.html", ctx)
