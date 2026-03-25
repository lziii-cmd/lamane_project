# core/services/dashboard.py  (remplace les parties concernées)

from datetime import date, datetime
from calendar import monthrange
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.db.models import Q

from core.models.projet import Projet
from core.models.achat import Achat
from core.models.versement import Versement

def _daterange_month_edges(y: int, m: int):
    start = date(y, m, 1)
    end = date(y, m, monthrange(y, m)[1])
    return start, end

def _last_n_months_labels(n=6):
    today = timezone.now().date()
    items = []
    for i in range(n - 1, -1, -1):
        m = ((today.month - i - 1) % 12) + 1
        y = today.year if (today.month - i) > 0 else today.year - 1
        items.append((y, m, datetime(y, m, 1).strftime("%b")))
    return items

def _supplier_label(f):
    if not f: return "—"
    if getattr(f, "est_moral", False):
        return getattr(f, "entreprise", "") or "Entreprise"
    return (f"{getattr(f, 'prenom', '')} {getattr(f, 'nom', '')}").strip() or "—"

def _filter_by_date(qs, field: str, start=None, end=None):
    """
    Filtre qs par [start, end] en gérant automatiquement DateField vs DateTimeField.
    Tente __date__gte/lte puis fallback vers __gte/lte si le lookup __date n'existe pas.
    """
    if start:
        try:
            qs = qs.filter(**{f"{field}__date__gte": start})
        except Exception:
            qs = qs.filter(**{f"{field}__gte": start})
    if end:
        try:
            qs = qs.filter(**{f"{field}__date__lte": end})
        except Exception:
            qs = qs.filter(**{f"{field}__lte": end})
    return qs

def compute_dashboard_stats(filters: dict):
    achats = Achat.objects.all()
    versements = Versement.objects.all()
    projets = Projet.objects.all()

    f_from = filters.get("from_date")
    f_to = filters.get("to_date")
    if f_from or f_to:
        achats = _filter_by_date(achats, "date_achat", f_from, f_to)
        versements = _filter_by_date(versements, "date_versement", f_from, f_to)

    pid = filters.get("projet_id")
    if pid:
        achats = achats.filter(projet_id=pid)
        versements = versements.filter(projet_id=pid)

    fid = filters.get("fournisseur_id")
    if fid:
        achats = achats.filter(fournisseur_id=fid)

    # KPI
    projects_count = projets.count() if not pid else projets.filter(pk=pid).count()

    agg_achats = achats.aggregate(
        ht=Coalesce(Sum("total_ht"), 0),
        tva=Coalesce(Sum("total_tva"), 0),
        ttc=Coalesce(Sum("total_ttc"), 0),
    )
    purchases_total_ht = float(agg_achats["ht"])
    purchases_total_tva = float(agg_achats["tva"])
    purchases_total_ttc = float(agg_achats["ttc"])

    agg_versements = versements.aggregate(total=Coalesce(Sum("montant"), 0))
    payments_total = float(agg_versements["total"])

    purchases_breakdown = [
        {"name": "HT", "value": purchases_total_ht},
        {"name": "TVA", "value": purchases_total_tva},
        {"name": "TTC", "value": purchases_total_ttc},
    ]

    # Séries mensuelles (6 derniers mois, TTC)
    quickview_monthly = []
    for y, m, label in _last_n_months_labels(6):
        start, end = _daterange_month_edges(y, m)
        monthly_qs = _filter_by_date(achats, "date_achat", start, end)
        total_month = monthly_qs.aggregate(total=Coalesce(Sum("total_ttc"), 0))["total"]
        quickview_monthly.append({"label": label, "value": float(total_month)})

    # Activité récente (5 derniers achats)
    recent_purchases = []
    for a in achats.select_related("fournisseur").order_by("-date_achat")[:5]:
        recent_purchases.append({
            "id": str(a.pk),
            "supplier": _supplier_label(getattr(a, "fournisseur", None)),
            "status": getattr(a, "mode_paiement", "—"),
            "amount": float(getattr(a, "total_ttc", 0)),
            "date": a.date_achat.strftime("%d/%m/%Y") if getattr(a, "date_achat", None) else "",
        })

    return {
        "projects_count": projects_count,
        "purchases_total_ht": purchases_total_ht,
        "purchases_total_tva": purchases_total_tva,
        "purchases_total_ttc": purchases_total_ttc,
        "payments_total": payments_total,
        "purchases_breakdown": purchases_breakdown,
        "quickview_monthly": quickview_monthly,
        "recent_purchases": recent_purchases,
    }
