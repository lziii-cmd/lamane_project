# core/views/stock.py
"""Vues stock, matériaux, bons de sortie, catégories — LAMANE BTP."""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg, Q, F, DecimalField as DjDecimalField
from django.db.models.functions import Coalesce
from decimal import Decimal

from core.models import (
    Materiel, CategorieMateriel, LigneAchat, BonSortie, LigneBonSortie,
)
from core.forms import (
    MaterielForm, CategorieMaterielForm, BonSortieForm, LigneBonSortieFormSet,
)
from core.permissions import role_required
from core.views._helpers import _fmt, _success

__all__ = [
    "stock_view", "stock_detail_view",
    "materiaux_list_view", "materiel_create_view", "materiel_detail_view", "materiel_edit_view",
    "bons_sortie_list_view", "bon_sortie_create_view", "bon_sortie_detail_view",
    "categorie_materiel_create_view", "categories_view",
    "categorie_create_view", "categorie_edit_view", "categorie_delete_view",
]


@login_required
@role_required("gestionnaire", "chef_chantier")
def stock_view(request):
    q   = request.GET.get("q", "")
    cat = request.GET.get("cat", "")
    materiaux = Materiel.objects.select_related("categorie").all()
    if q:
        materiaux = materiaux.filter(Q(nom__icontains=q) | Q(unite__icontains=q))
    if cat:
        materiaux = materiaux.filter(categorie__id=cat)
    materiaux = materiaux.order_by("categorie__nom", "nom")

    categories = CategorieMateriel.objects.annotate(nb=Count("materiaux")).order_by("nom")

    materiaux_data = []
    for m in materiaux[:100]:
        lignes    = LigneAchat.objects.filter(materiel=m)
        qty_total = lignes.aggregate(s=Coalesce(Sum("quantite"), 0))["s"]
        nb_achats = lignes.values("achat").distinct().count()
        valeur_ht = lignes.aggregate(s=Coalesce(Sum("prix_unitaire"), Decimal("0")))["s"]
        materiaux_data.append({
            "materiel": m, "qty_total": qty_total, "nb_achats": nb_achats,
            "valeur_ht": _fmt(valeur_ht),
        })

    ctx = {
        "page": "stock", "materiaux_data": materiaux_data, "categories": categories,
        "total_materiaux": Materiel.objects.count(),
        "total_categories": CategorieMateriel.objects.count(),
        "total_bons_sortie": BonSortie.objects.count(),
        "q": q, "cat_filter": cat,
    }
    return render(request, "lamane/stock.html", ctx)


@login_required
@role_required("gestionnaire", "chef_chantier")
def stock_detail_view(request):
    """Stock réel par matériau : entrées (achats) − sorties (bons de sortie)."""
    q   = request.GET.get("q", "")
    cat = request.GET.get("cat", "")
    materiaux = Materiel.objects.select_related("categorie").all()
    if q:
        materiaux = materiaux.filter(Q(nom__icontains=q) | Q(unite__icontains=q))
    if cat:
        materiaux = materiaux.filter(categorie__id=cat)
    materiaux = materiaux.order_by("categorie__nom", "nom")

    categories = CategorieMateriel.objects.annotate(nb=Count("materiaux")).order_by("nom")

    stock_data = []
    for m in materiaux:
        entrees = LigneAchat.objects.filter(materiel=m).aggregate(
            s=Coalesce(Sum("quantite", output_field=DjDecimalField()), Decimal("0")))["s"]
        sorties = LigneBonSortie.objects.filter(materiel=m).aggregate(
            s=Coalesce(Sum("quantite", output_field=DjDecimalField()), Decimal("0")))["s"]
        stock_actuel = float(entrees) - float(sorties)
        valeur_unitaire_moy = LigneAchat.objects.filter(materiel=m).aggregate(
            avg=Coalesce(Avg("prix_unitaire"), Decimal("0")))["avg"]
        valeur_stock = stock_actuel * float(valeur_unitaire_moy)

        stock_data.append({
            "materiel": m,
            "entrees": float(entrees), "sorties": float(sorties),
            "stock_actuel": round(stock_actuel, 2),
            "stock_positif": stock_actuel >= 0,
            "alerte_rupture": stock_actuel <= 0,
            "valeur_stock": _fmt(valeur_stock),
            "prix_moyen": _fmt(valeur_unitaire_moy, 0),
        })

    ctx = {
        "page": "stock", "stock_data": stock_data,
        "categories": categories, "q": q, "cat_filter": cat,
        "total_references": len(stock_data),
        "nb_ruptures": sum(1 for d in stock_data if d["alerte_rupture"]),
        "nb_alertes": sum(1 for d in stock_data if d["stock_actuel"] < 5 and not d["alerte_rupture"]),
    }
    return render(request, "lamane/stock_detail.html", ctx)


@login_required
@role_required("gestionnaire", "chef_chantier")
def materiaux_list_view(request):
    q = request.GET.get("q", "")
    cat = request.GET.get("cat", "")
    materiaux = Materiel.objects.select_related("categorie").all()
    if q:
        materiaux = materiaux.filter(Q(nom__icontains=q) | Q(unite__icontains=q))
    if cat:
        materiaux = materiaux.filter(categorie__id=cat)
    materiaux = materiaux.order_by("categorie__nom", "nom")
    categories = CategorieMateriel.objects.all().order_by("nom")

    stock_data = []
    for m in materiaux:
        entrees = LigneAchat.objects.filter(materiel=m).aggregate(
            s=Coalesce(Sum("quantite", output_field=DjDecimalField()), Decimal("0")))["s"]
        sorties = LigneBonSortie.objects.filter(materiel=m).aggregate(
            s=Coalesce(Sum("quantite", output_field=DjDecimalField()), Decimal("0")))["s"]
        stock_actuel = float(entrees) - float(sorties)
        stock_data.append({
            "materiel": m,
            "stock_actuel": round(stock_actuel, 2),
            "alerte_rupture": stock_actuel <= 0,
        })

    ctx = {
        "page": "stock", "stock_data": stock_data,
        "categories": categories, "q": q, "cat_filter": cat,
        "total": len(stock_data),
    }
    return render(request, "lamane/materiaux_list.html", ctx)


@login_required
@role_required("gestionnaire", "chef_chantier")
def materiel_detail_view(request, pk):
    materiel = get_object_or_404(Materiel, pk=pk)
    lignes_achat = LigneAchat.objects.filter(materiel=materiel).select_related("achat__projet").order_by("-achat__date_achat")[:20]
    lignes_sortie = LigneBonSortie.objects.filter(materiel=materiel).select_related("bon__projet").order_by("-bon__date_sortie")[:20]
    entrees = LigneAchat.objects.filter(materiel=materiel).aggregate(
        s=Coalesce(Sum("quantite", output_field=DjDecimalField()), Decimal("0")))["s"]
    sorties = LigneBonSortie.objects.filter(materiel=materiel).aggregate(
        s=Coalesce(Sum("quantite", output_field=DjDecimalField()), Decimal("0")))["s"]
    stock_actuel = float(entrees) - float(sorties)
    prix_moy = LigneAchat.objects.filter(materiel=materiel).aggregate(
        avg=Coalesce(Avg("prix_unitaire"), Decimal("0")))["avg"]
    ctx = {
        "page": "stock", "materiel": materiel,
        "lignes_achat": lignes_achat, "lignes_sortie": lignes_sortie,
        "entrees": float(entrees), "sorties": float(sorties),
        "stock_actuel": round(stock_actuel, 2),
        "stock_positif": stock_actuel >= 0, "alerte_rupture": stock_actuel <= 0,
        "prix_moyen": _fmt(prix_moy, 0),
        "valeur_stock": _fmt(stock_actuel * float(prix_moy), 0),
    }
    return render(request, "lamane/materiel_detail.html", ctx)


@login_required
@role_required("gestionnaire")
def materiel_create_view(request):
    form = MaterielForm(request.POST or None)
    if form.is_valid():
        m = form.save()
        return _success(request, f"Matériau « {m.nom} » créé.", "ui_stock")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": "Nouveau matériau",
                   "action": "Créer", "page": "stock", "back_url": "/stock/"})


@login_required
@role_required("gestionnaire")
def materiel_edit_view(request, pk):
    m = get_object_or_404(Materiel, pk=pk)
    form = MaterielForm(request.POST or None, instance=m)
    if form.is_valid():
        form.save()
        return _success(request, "Matériau modifié.", "ui_stock")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": f"Modifier — {m.nom}",
                   "action": "Enregistrer", "page": "stock", "back_url": "/stock/", "obj": m})


@login_required
@role_required("gestionnaire")
def categorie_materiel_create_view(request):
    form = CategorieMaterielForm(request.POST or None)
    if form.is_valid():
        c = form.save()
        return _success(request, f"Catégorie « {c.nom} » créée.", "ui_stock")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": "Nouvelle catégorie de matériau",
                   "action": "Créer", "page": "stock", "back_url": "/stock/"})


@login_required
@role_required("gestionnaire", "chef_chantier")
def bons_sortie_list_view(request):
    q = request.GET.get("q", "")
    bons = BonSortie.objects.select_related("projet").order_by("-date_sortie")
    if q:
        bons = bons.filter(
            Q(projet__nom__icontains=q) | Q(reference__icontains=q) | Q(responsable__icontains=q)
        )

    from core.pagination import paginate_queryset
    page_obj = paginate_queryset(request, bons, per_page=25)
    ctx = {
        "page": "stock", "bons": page_obj, "page_obj": page_obj, "q": q,
        "total_bons": BonSortie.objects.count(),
        "total_lignes": LigneBonSortie.objects.count(),
    }
    return render(request, "lamane/bons_sortie.html", ctx)


@login_required
@role_required("gestionnaire", "chef_chantier")
def bon_sortie_create_view(request):
    form = BonSortieForm(request.POST or None)
    formset = LigneBonSortieFormSet(request.POST or None, prefix="lignes")
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        bon = form.save()
        formset.instance = bon
        formset.save()
        bon.bon_pdf = None
        try:
            bon._generate_pdf()
            bon.save(update_fields=["bon_pdf"])
        except Exception as e:
            print(f"[BON SORTIE PDF] Erreur: {e}")
        return _success(request, f"Bon de sortie {bon.reference} créé — PDF généré.", "ui_bons_sortie")
    return render(request, "lamane/forms/bon_sortie_form.html",
                  {"form": form, "formset": formset,
                   "title": "Nouveau bon de sortie matériaux",
                   "action": "Créer", "page": "stock", "back_url": "/stock/bons-sortie/"})


@login_required
@role_required("gestionnaire", "chef_chantier")
def bon_sortie_detail_view(request, pk):
    bon = get_object_or_404(BonSortie, pk=pk)
    lignes = bon.lignes.select_related("materiel")
    ctx = {"page": "stock", "bon": bon, "lignes": lignes}
    return render(request, "lamane/bon_sortie_detail.html", ctx)


# ─── CATEGORIES ───────────────────────────────────────────────────────────────

@login_required
@role_required("gestionnaire")
def categories_view(request):
    categories = CategorieMateriel.objects.annotate(nb_materiaux=Count("materiaux")).order_by("nom")
    return render(request, "lamane/categories.html", {"page": "categories", "categories": categories})


@login_required
@role_required("gestionnaire")
def categorie_create_view(request):
    form = CategorieMaterielForm(request.POST or None)
    if form.is_valid():
        c = form.save()
        return _success(request, f"Catégorie « {c.nom} » créée.", "ui_categories")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": "Nouvelle catégorie",
                   "action": "Créer", "page": "categories", "back_url": "/categories/"})


@login_required
@role_required("gestionnaire")
def categorie_edit_view(request, pk):
    c = get_object_or_404(CategorieMateriel, pk=pk)
    form = CategorieMaterielForm(request.POST or None, instance=c)
    if form.is_valid():
        form.save()
        return _success(request, "Catégorie modifiée.", "ui_categories")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": f"Modifier — {c.nom}",
                   "action": "Enregistrer", "page": "categories",
                   "back_url": "/categories/", "obj": c})


@login_required
@role_required("gestionnaire")
def categorie_delete_view(request, pk):
    c = get_object_or_404(CategorieMateriel, pk=pk)
    if request.method == "POST":
        nom = c.nom
        c.delete()
        return _success(request, f"Catégorie « {nom} » supprimée.", "ui_categories")
    return render(request, "lamane/forms/confirm_delete.html",
                  {"obj": c, "titre": c.nom, "page": "categories", "back_url": "/categories/"})
