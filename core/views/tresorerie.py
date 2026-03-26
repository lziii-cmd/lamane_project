# core/views/tresorerie.py
"""Vues trésorerie / comptes bancaires — LAMANE BTP."""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from decimal import Decimal

from core.models import CompteBancaire, TransactionBancaire
from core.forms import CompteBancaireForm, TransactionBancaireForm
from core.permissions import role_required
from core.views._helpers import _fmt, _success

__all__ = [
    "tresorerie_view", "compte_bancaire_create_view",
    "compte_bancaire_detail_view", "compte_bancaire_edit_view",
    "transaction_create_view",
]


@login_required
@role_required("comptable")
def tresorerie_view(request):
    comptes = CompteBancaire.objects.filter(actif=True)
    comptes_data = []
    solde_total = Decimal("0")
    for c in comptes:
        solde = c.solde_actuel
        solde_total += solde
        nb_tx = c.transactions.count()
        comptes_data.append({
            "compte": c, "solde": _fmt(solde),
            "solde_raw": solde, "nb_transactions": nb_tx,
        })

    dernieres_tx = TransactionBancaire.objects.select_related(
        "compte", "projet"
    ).order_by("-date_transaction")[:20]

    ctx = {
        "page": "tresorerie", "comptes_data": comptes_data,
        "solde_total": _fmt(solde_total), "solde_total_raw": solde_total,
        "dernieres_tx": dernieres_tx, "total_comptes": comptes.count(),
    }
    return render(request, "lamane/tresorerie.html", ctx)


@login_required
@role_required("comptable")
def compte_bancaire_create_view(request):
    form = CompteBancaireForm(request.POST or None)
    if form.is_valid():
        c = form.save()
        return _success(request, f"Compte « {c.nom} » créé.", "ui_tresorerie")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": "Nouveau compte bancaire",
                   "action": "Créer", "page": "tresorerie", "back_url": "/tresorerie/"})


@login_required
@role_required("comptable")
def compte_bancaire_edit_view(request, pk):
    c = get_object_or_404(CompteBancaire, pk=pk)
    form = CompteBancaireForm(request.POST or None, instance=c)
    if form.is_valid():
        form.save()
        return _success(request, "Compte modifié.", "ui_tresorerie")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": f"Modifier — {c.nom}",
                   "action": "Enregistrer", "page": "tresorerie",
                   "back_url": "/tresorerie/", "obj": c})


@login_required
@role_required("comptable")
def compte_bancaire_detail_view(request, pk):
    compte = get_object_or_404(CompteBancaire, pk=pk)
    transactions = compte.transactions.select_related("projet").order_by("-date_transaction")
    ctx = {
        "page": "tresorerie", "compte": compte,
        "transactions": transactions, "solde": _fmt(compte.solde_actuel),
    }
    return render(request, "lamane/compte_bancaire_detail.html", ctx)


@login_required
@role_required("comptable")
def transaction_create_view(request):
    form = TransactionBancaireForm(request.POST or None)
    if form.is_valid():
        tx = form.save()
        return _success(request, f"Transaction enregistrée — {tx.montant} XOF", "ui_tresorerie")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": "Nouvelle transaction",
                   "action": "Enregistrer", "page": "tresorerie", "back_url": "/tresorerie/"})
