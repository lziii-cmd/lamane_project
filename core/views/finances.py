# core/views/finances.py
"""Vues finances, achats, versements, bilans — LAMANE BTP."""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Avg, Q, F
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal
import json

from core.models import (
    Projet, Achat, LigneAchat, Versement, MarcheTravaux,
    ContratSousTraitance, SituationMensuelle,
)
from core.forms import AchatForm, LigneAchatFormSet, VersementForm
from core.permissions import role_required
from core.pagination import paginate_queryset
from core.services.comptabilite import generer_ecriture_achat, generer_ecriture_versement
from core.views._helpers import _fmt, _success

__all__ = [
    "finances_view", "achats_list_view", "achat_detail_view",
    "achat_create_view", "achat_edit_view", "achat_delete_view",
    "versements_view", "versement_create_view", "versement_detail_view",
    "versement_delete_view", "bilans_view",
]


@login_required
@role_required("comptable")
def finances_view(request):
    from calendar import monthrange
    today = timezone.now().date()
    agg = Achat.objects.aggregate(
        total_ht=Coalesce(Sum("total_ht"), Decimal("0")),
        total_tva=Coalesce(Sum("total_tva"), Decimal("0")),
        total_ttc=Coalesce(Sum("total_ttc"), Decimal("0")),
    )
    total_versements = Versement.objects.aggregate(s=Coalesce(Sum("montant"), Decimal("0")))["s"]
    modes = Achat.objects.values("mode_paiement").annotate(
        total=Coalesce(Sum("total_ttc"), Decimal("0")), count=Count("id")
    ).order_by("-total")
    top_fournisseurs = Achat.objects.values(
        "fournisseur__entreprise", "fournisseur__nom", "fournisseur__prenom"
    ).annotate(total=Coalesce(Sum("total_ttc"), Decimal("0")), count=Count("id")).order_by("-total")[:10]

    monthly_labels, monthly_ttc, monthly_verse = [], [], []
    for i in range(11, -1, -1):
        m = ((today.month - i - 1) % 12) + 1
        y = today.year if (today.month - i) > 0 else today.year - 1
        start = today.replace(year=y, month=m, day=1)
        end   = today.replace(year=y, month=m, day=monthrange(y, m)[1])
        monthly_labels.append(start.strftime("%b %Y"))
        monthly_ttc.append(float(Achat.objects.filter(date_achat__range=[start, end]).aggregate(s=Coalesce(Sum("total_ttc"), Decimal("0")))["s"]))
        monthly_verse.append(float(Versement.objects.filter(date_versement__range=[start, end]).aggregate(s=Coalesce(Sum("montant"), Decimal("0")))["s"]))

    top_projets = Achat.objects.values("projet__nom").annotate(total=Coalesce(Sum("total_ttc"), Decimal("0"))).order_by("-total")[:8]

    total_st = ContratSousTraitance.objects.aggregate(
        s=Coalesce(Sum("montant"), Decimal("0")))["s"]
    total_depenses = float(agg["total_ttc"]) + float(total_st)

    ctx = {
        "page": "finances", "today": today,
        "total_ht": _fmt(agg["total_ht"]), "total_tva": _fmt(agg["total_tva"]),
        "total_ttc": _fmt(agg["total_ttc"]), "total_versements": _fmt(total_versements),
        "total_st": _fmt(total_st),
        "total_depenses": _fmt(total_depenses),
        "solde": _fmt(abs(float(total_versements) - total_depenses)),
        "solde_positif": float(total_versements) >= total_depenses,
        "modes": list(modes), "top_fournisseurs": list(top_fournisseurs),
        "recent_achats": Achat.objects.select_related("fournisseur", "projet").order_by("-date_achat")[:15],
        "recent_versements": Versement.objects.select_related("projet", "phase").order_by("-date_versement")[:10],
        "situations_stats": SituationMensuelle.objects.aggregate(
            total_brut=Coalesce(Sum("montant_brut_cumule"), Decimal("0")),
            total_net=Coalesce(Sum("montant_a_payer"), Decimal("0")),
            total_retenue=Coalesce(Sum("retenue_garantie"), Decimal("0")),
        ),
        "top_projets": list(top_projets),
        "monthly_labels_json": json.dumps(monthly_labels),
        "monthly_ttc_json":    json.dumps(monthly_ttc),
        "monthly_verse_json":  json.dumps(monthly_verse),
        "modes_labels_json":   json.dumps([m.get("mode_paiement") or "Non précisé" for m in modes]),
        "modes_values_json":   json.dumps([float(m["total"]) for m in modes]),
        "top_projets_labels_json": json.dumps([p["projet__nom"] or "—" for p in top_projets]),
        "top_projets_values_json": json.dumps([float(p["total"]) for p in top_projets]),
    }
    return render(request, "lamane/finances.html", ctx)


@login_required
@role_required("comptable", "gestionnaire")
def achats_list_view(request):
    q             = request.GET.get("q", "")
    mode_filter   = request.GET.get("mode", "")
    achats = Achat.objects.select_related("fournisseur", "projet").order_by("-date_achat")
    if q:
        achats = achats.filter(
            Q(projet__nom__icontains=q) | Q(fournisseur__entreprise__icontains=q)
            | Q(fournisseur__nom__icontains=q) | Q(numero_facture__icontains=q)
        )
    if mode_filter:
        achats = achats.filter(mode_paiement=mode_filter)

    agg = Achat.objects.aggregate(
        total_ht=Coalesce(Sum("total_ht"), Decimal("0")),
        total_ttc=Coalesce(Sum("total_ttc"), Decimal("0")),
        count=Count("id"),
    )
    page_obj = paginate_queryset(request, achats, per_page=25)
    ctx = {
        "page": "achats", "achats": page_obj, "page_obj": page_obj,
        "q": q, "mode_filter": mode_filter,
        "total_achats": agg["count"],
        "total_ht_fmt": _fmt(agg["total_ht"]), "total_ttc_fmt": _fmt(agg["total_ttc"]),
        "modes_choices": ["espèces", "virement", "chèque", "autre"],
    }
    return render(request, "lamane/achats_list.html", ctx)


@login_required
@role_required("comptable", "gestionnaire")
def achat_detail_view(request, pk):
    achat  = get_object_or_404(Achat, pk=pk)
    lignes = LigneAchat.objects.filter(achat=achat).select_related("materiel")
    ctx = {"page": "achats", "achat": achat, "lignes": lignes}
    return render(request, "lamane/achat_detail.html", ctx)


@login_required
@role_required("comptable", "gestionnaire")
def achat_create_view(request):
    form = AchatForm(request.POST or None, request.FILES or None)
    formset = LigneAchatFormSet(request.POST or None, prefix="lignes")
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        achat = form.save()
        formset.instance = achat
        formset.save()
        achat.calcul_totaux()
        achat.save(update_fields=["total_ht", "total_tva", "total_ttc"])
        try:
            achat.generate_bon_entree_pdf()
            achat.save(update_fields=["bon_entree_pdf"])
        except Exception as e:
            print(f"[BON ENTREE] Erreur PDF: {e}")
        try:
            generer_ecriture_achat(achat)
        except Exception as e:
            print(f"[COMPTA] Erreur écriture achat: {e}")
        return _success(request, "Achat enregistré — Bon d'entrée généré automatiquement.", "ui_achats")
    return render(request, "lamane/forms/achat_form.html",
                  {"form": form, "formset": formset,
                   "title": "Nouvel achat de matériaux",
                   "action": "Enregistrer", "page": "achats", "back_url": "/achats/"})


@login_required
@role_required("comptable", "gestionnaire")
def achat_edit_view(request, pk):
    achat = get_object_or_404(Achat, pk=pk)
    form = AchatForm(request.POST or None, request.FILES or None, instance=achat)
    formset = LigneAchatFormSet(request.POST or None, instance=achat, prefix="lignes")
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        achat.calcul_totaux()
        achat.save(update_fields=["total_ht", "total_tva", "total_ttc"])
        return _success(request, "Achat modifié.", f"/achats/{pk}/")
    return render(request, "lamane/forms/achat_form.html",
                  {"form": form, "formset": formset,
                   "title": "Modifier l'achat",
                   "action": "Enregistrer", "page": "achats",
                   "back_url": f"/achats/{pk}/", "obj": achat})


@login_required
@role_required("comptable")
def achat_delete_view(request, pk):
    achat = get_object_or_404(Achat, pk=pk)
    if request.method == "POST":
        achat.delete()
        return _success(request, "Achat supprimé.", "ui_achats")
    return render(request, "lamane/forms/confirm_delete.html",
                  {"obj": achat, "titre": str(achat), "page": "achats",
                   "back_url": f"/achats/{pk}/"})


@login_required
@role_required("comptable")
def versements_view(request):
    q           = request.GET.get("q", "")
    type_filter = request.GET.get("type", "")
    versements  = Versement.objects.select_related("projet").order_by("-date_versement")
    if q:
        versements = versements.filter(
            Q(projet__nom__icontains=q) | Q(libelle__icontains=q) | Q(reference_paiement__icontains=q)
        )
    if type_filter:
        versements = versements.filter(type_versement=type_filter)

    agg = Versement.objects.aggregate(total=Coalesce(Sum("montant"), Decimal("0")), count=Count("id"))
    types_stats = Versement.objects.values("type_versement").annotate(
        total=Coalesce(Sum("montant"), Decimal("0")), count=Count("id")
    ).order_by("-total")

    page_obj = paginate_queryset(request, versements, per_page=25)
    ctx = {
        "page": "versements", "versements": page_obj, "page_obj": page_obj,
        "q": q, "type_filter": type_filter,
        "total_versements": agg["count"], "montant_total": _fmt(agg["total"]),
        "types_stats": list(types_stats),
        "types_choices": ["chèque", "virement bancaire", "virement om", "wave", "espèces", "autres"],
        "types_labels_json": json.dumps([t.get("type_versement") or "—" for t in types_stats]),
        "types_values_json": json.dumps([float(t["total"]) for t in types_stats]),
    }
    return render(request, "lamane/versements_list.html", ctx)


@login_required
@role_required("comptable")
def versement_create_view(request):
    form = VersementForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        v = form.save()
        msg = f"Versement enregistre ({v.numero_facture})"
        if v.facture_pdf:
            msg += " — Facture PDF generee automatiquement."
        else:
            msg += " — Attention : la facture PDF n'a pas pu etre generee."
        try:
            generer_ecriture_versement(v)
        except Exception as e:
            print(f"[COMPTA] Erreur écriture versement: {e}")
        messages.success(request, msg)
        return _success(request, msg, "ui_versements")
    return render(request, "lamane/forms/versement_form.html",
                  {"form": form, "title": "Nouveau versement",
                   "action": "Enregistrer", "page": "versements", "back_url": "/versements/"})


@login_required
@role_required("comptable")
def versement_detail_view(request, pk):
    versement = get_object_or_404(Versement, pk=pk)
    if request.GET.get("regenerer") == "1" or not versement.facture_pdf:
        try:
            versement.generate_facture_pdf()
            versement.save(update_fields=["facture_pdf"])
            if request.GET.get("regenerer") == "1":
                messages.success(request, "Facture PDF regeneree avec succes.")
                from django.shortcuts import redirect
                return redirect("ui_versement_detail", pk=pk)
        except Exception as e:
            messages.error(request, f"Erreur lors de la generation du PDF : {e}")
    ctx = {"page": "versements", "versement": versement}
    return render(request, "lamane/versement_detail.html", ctx)


@login_required
@role_required("comptable")
def versement_delete_view(request, pk):
    v = get_object_or_404(Versement, pk=pk)
    if request.method == "POST":
        v.delete()
        return _success(request, "Versement supprimé.", "ui_versements")
    return render(request, "lamane/forms/confirm_delete.html",
                  {"obj": v, "titre": str(v), "page": "versements", "back_url": "/versements/"})


@login_required
@role_required("comptable")
def bilans_view(request):
    """Page de bilans financiers : P&L par projet, trésorerie, alertes, impayés."""
    from calendar import monthrange
    today = timezone.now().date()

    projets = Projet.objects.prefetch_related(
        "achats", "versements", "contrats_sous_traitance"
    ).all()
    pl_data = []
    total_st_global = Decimal("0")

    for p in projets:
        versements_sum = Versement.objects.filter(projet=p).aggregate(
            s=Coalesce(Sum("montant"), Decimal("0")))["s"]
        achats_agg = Achat.objects.filter(projet=p).aggregate(
            ht=Coalesce(Sum("total_ht"), Decimal("0")),
            ttc=Coalesce(Sum("total_ttc"), Decimal("0")),
        )
        st_montant = ContratSousTraitance.objects.filter(projet=p).aggregate(
            s=Coalesce(Sum("montant"), Decimal("0")))["s"]
        st_paye = ContratSousTraitance.objects.filter(projet=p).aggregate(
            s=Coalesce(Sum("montant_paye"), Decimal("0")))["s"]
        total_st_global += st_montant

        total_depenses = float(achats_agg["ttc"]) + float(st_montant)
        marge = float(versements_sum) - total_depenses
        budget = float(p.cout_estime_lamane or 0)
        alerte_budget = budget > 0 and total_depenses > budget * 0.9

        retenue = Decimal("0")
        try:
            marche = p.marche
            retenue = marche.retenue_garantie_montant
        except Exception:
            pass

        penalites = Decimal("0")
        try:
            marche = p.marche
            penalites = marche.penalites_calculees
        except Exception:
            pass

        taux_marge = round(marge / float(versements_sum) * 100, 1) if float(versements_sum) > 0 else 0

        pl_data.append({
            "projet": p,
            "versements": float(versements_sum), "versements_fmt": _fmt(versements_sum),
            "achats_ht": float(achats_agg["ht"]), "achats_ttc": float(achats_agg["ttc"]),
            "achats_ht_fmt": _fmt(achats_agg["ht"]), "achats_ttc_fmt": _fmt(achats_agg["ttc"]),
            "st_montant": float(st_montant), "st_montant_fmt": _fmt(st_montant),
            "st_paye": float(st_paye), "st_paye_fmt": _fmt(st_paye),
            "st_reste": _fmt(float(st_montant) - float(st_paye)),
            "total_depenses": total_depenses, "total_depenses_fmt": _fmt(total_depenses),
            "marge": marge, "marge_fmt": _fmt(abs(marge)), "marge_positive": marge >= 0,
            "taux_marge": taux_marge, "budget": budget, "budget_fmt": _fmt(budget),
            "alerte_budget": alerte_budget,
            "taux_budget": round(total_depenses / budget * 100, 1) if budget else 0,
            "retenue": _fmt(retenue), "penalites": _fmt(penalites),
        })

    total_versements_g = Versement.objects.aggregate(s=Coalesce(Sum("montant"), Decimal("0")))["s"]
    total_achats_g = Achat.objects.aggregate(
        ht=Coalesce(Sum("total_ht"), Decimal("0")),
        ttc=Coalesce(Sum("total_ttc"), Decimal("0")),
    )
    total_depenses_g = float(total_achats_g["ttc"]) + float(total_st_global)
    solde_global = float(total_versements_g) - total_depenses_g

    impayes = Achat.objects.filter(
        statut_paiement__in=["en_attente", "en_retard"]
    ).select_related("fournisseur", "projet").order_by("echeance_paiement")[:20]
    total_impayes = Achat.objects.filter(
        statut_paiement__in=["en_attente", "en_retard"]
    ).aggregate(s=Coalesce(Sum("total_ttc"), Decimal("0")))["s"]
    nb_en_retard = Achat.objects.filter(statut_paiement="en_retard").count()

    ventilation = {
        "achats_materiaux": float(total_achats_g["ttc"]),
        "sous_traitance": float(total_st_global),
    }

    monthly_labels, monthly_entrees, monthly_sorties, monthly_solde = [], [], [], []
    cumul = 0.0
    for i in range(11, -1, -1):
        m = ((today.month - i - 1) % 12) + 1
        y = today.year if (today.month - i) > 0 else today.year - 1
        start = today.replace(year=y, month=m, day=1)
        end   = today.replace(year=y, month=m, day=monthrange(y, m)[1])
        entrees = float(Versement.objects.filter(date_versement__range=[start, end]).aggregate(
            s=Coalesce(Sum("montant"), Decimal("0")))["s"])
        sorties = float(Achat.objects.filter(date_achat__range=[start, end]).aggregate(
            s=Coalesce(Sum("total_ttc"), Decimal("0")))["s"])
        cumul += entrees - sorties
        monthly_labels.append(start.strftime("%b %Y"))
        monthly_entrees.append(entrees)
        monthly_sorties.append(sorties)
        monthly_solde.append(round(cumul, 2))

    top5 = sorted(pl_data, key=lambda x: x["total_depenses"], reverse=True)[:5]
    alertes = [d for d in pl_data if d["alerte_budget"]]

    ctx = {
        "page": "bilans", "pl_data": pl_data,
        "total_versements_fmt": _fmt(total_versements_g),
        "total_achats_ht_fmt": _fmt(total_achats_g["ht"]),
        "total_achats_ttc_fmt": _fmt(total_achats_g["ttc"]),
        "total_st_fmt": _fmt(total_st_global),
        "total_depenses_fmt": _fmt(total_depenses_g),
        "solde_global": _fmt(abs(solde_global)), "solde_positif": solde_global >= 0,
        "nb_projets": len(pl_data), "nb_alertes": len(alertes), "alertes": alertes, "top5": top5,
        "impayes": impayes, "total_impayes_fmt": _fmt(total_impayes),
        "nb_impayes": impayes.count() if hasattr(impayes, 'count') else len(impayes),
        "nb_en_retard": nb_en_retard,
        "ventilation": ventilation,
        "ventilation_labels_json": json.dumps(["Achats matériaux", "Sous-traitance"]),
        "ventilation_values_json": json.dumps([ventilation["achats_materiaux"], ventilation["sous_traitance"]]),
        "monthly_labels_json": json.dumps(monthly_labels),
        "monthly_entrees_json": json.dumps(monthly_entrees),
        "monthly_sorties_json": json.dumps(monthly_sorties),
        "monthly_solde_json": json.dumps(monthly_solde),
        "top5_labels_json": json.dumps([d["projet"].nom[:20] for d in top5]),
        "top5_values_json": json.dumps([d["total_depenses"] for d in top5]),
    }
    return render(request, "lamane/bilans.html", ctx)
