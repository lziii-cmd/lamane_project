# core/views/dashboard.py
"""Vue dashboard — LAMANE BTP."""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal
import json

from core.models import (
    Projet, Achat, Versement, MarcheTravaux,
    AvancementChantier, SousTraitant, Employe, Proprietaire,
)
from core.views._helpers import (
    _fmt, apply_achat_filters, apply_versement_filters, apply_projet_filters,
)

__all__ = ["dashboard_view"]


@login_required
def dashboard_view(request):
    from calendar import monthrange
    today = timezone.now().date()

    # Querysets filtrés par sélection globale
    projets_qs    = apply_projet_filters(Projet.objects.all(), request)
    achats_qs     = apply_achat_filters(Achat.objects.all(), request)
    versements_qs = apply_versement_filters(Versement.objects.all(), request)

    total_projets = projets_qs.count()
    en_cours      = projets_qs.filter(statut="En cours").count()
    termines      = projets_qs.filter(statut="Terminé").count()
    en_attente    = projets_qs.filter(statut="En attente").count()
    en_pause      = projets_qs.filter(statut="En pause").count()

    agg = achats_qs.aggregate(
        total_ht=Coalesce(Sum("total_ht"), Decimal("0")),
        total_tva=Coalesce(Sum("total_tva"), Decimal("0")),
        total_ttc=Coalesce(Sum("total_ttc"), Decimal("0")),
    )
    total_versements  = versements_qs.aggregate(s=Coalesce(Sum("montant"), Decimal("0")))["s"]
    solde             = float(total_versements) - float(agg["total_ttc"])
    total_marches     = MarcheTravaux.objects.count()
    montant_total_mch = MarcheTravaux.objects.aggregate(s=Coalesce(Sum("montant_marche"), Decimal("0")))["s"]
    avancement_moyen  = AvancementChantier.objects.filter(projet__statut="En cours").aggregate(avg=Avg("taux_physique"))["avg"] or 0

    statuts_data = {"En cours": en_cours, "Terminé": termines, "En attente": en_attente, "En pause": en_pause}

    monthly_labels, monthly_achats, monthly_versements_list = [], [], []
    for i in range(5, -1, -1):
        m = ((today.month - i - 1) % 12) + 1
        y = today.year if (today.month - i) > 0 else today.year - 1
        start = today.replace(year=y, month=m, day=1)
        end   = today.replace(year=y, month=m, day=monthrange(y, m)[1])
        va = achats_qs.filter(date_achat__range=[start, end]).aggregate(s=Coalesce(Sum("total_ttc"), Decimal("0")))["s"]
        vv = versements_qs.filter(date_versement__range=[start, end]).aggregate(s=Coalesce(Sum("montant"), Decimal("0")))["s"]
        monthly_labels.append(start.strftime("%b %Y"))
        monthly_achats.append(float(va))
        monthly_versements_list.append(float(vv))

    ctx = {
        "page": "dashboard", "today": today,
        "total_projets": total_projets, "en_cours": en_cours,
        "termines": termines, "en_attente": en_attente, "en_pause": en_pause,
        "total_ht_fmt": _fmt(agg["total_ht"]), "total_ttc_fmt": _fmt(agg["total_ttc"]),
        "total_versements_fmt": _fmt(total_versements),
        "solde_fmt": _fmt(abs(solde)), "solde_positif": solde >= 0,
        "total_marches": total_marches,
        "montant_marches_fmt": _fmt(montant_total_mch),
        "avancement_moyen": round(avancement_moyen, 1),
        "total_sous_traitants": SousTraitant.objects.count(),
        "total_employes": Employe.objects.count(),
        "total_clients": Proprietaire.objects.count(),
        "total_achats_count": achats_qs.count(),
        "total_versements_count": versements_qs.count(),
        "statuts_data_json": json.dumps(statuts_data),
        "monthly_labels_json": json.dumps(monthly_labels),
        "monthly_achats_json": json.dumps(monthly_achats),
        "monthly_versements_json": json.dumps(monthly_versements_list),
        "recent_achats": achats_qs.select_related("fournisseur", "projet").order_by("-date_achat")[:8],
    }
    return render(request, "lamane/dashboard.html", ctx)
