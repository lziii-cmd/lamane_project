# core/services/finances.py
from datetime import date, datetime
from calendar import monthrange
from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone

def _month_edges(y: int, m: int):
    start = date(y, m, 1); end = date(y, m, monthrange(y, m)[1]); return start, end

def _last_n_months(n=6):
    today = timezone.now().date(); out = []
    for i in range(n - 1, -1, -1):
        m = ((today.month - i - 1) % 12) + 1
        y = today.year if (today.month - i) > 0 else today.year - 1
        out.append((y, m, datetime(y, m, 1).strftime("%b")))
    return out

def _supplier_label(f):
    if not f: return "—"
    if getattr(f, "est_moral", False): return getattr(f, "entreprise", "") or "Entreprise"
    return (f"{getattr(f, 'prenom', '')} {getattr(f, 'nom', '')}").strip() or "—"

def _date_filter(qs, field: str, start=None, end=None):
    if start:
        try: qs = qs.filter(**{f"{field}__date__gte": start})
        except Exception: qs = qs.filter(**{f"{field}__gte": start})
    if end:
        try: qs = qs.filter(**{f"{field}__date__lte": end})
        except Exception: qs = qs.filter(**{f"{field}__lte": end})
    return qs

def compute_finance_stats(*, from_date=None, to_date=None, projet_id=None, fournisseur_id=None):
    # imports “lazy” (évite les soucis d’ordre de chargement)
    from core.models.projet import Projet
    from core.models.achat import Achat
    from core.models.versement import Versement

    achats = Achat.objects.all()
    versements = Versement.objects.all()

    if from_date or to_date:
        achats = _date_filter(achats, "date_achat", from_date, to_date)
        versements = _date_filter(versements, "date_versement", from_date, to_date)
    if projet_id:
        achats = achats.filter(projet_id=projet_id)
        versements = versements.filter(projet_id=projet_id)
    if fournisseur_id:
        achats = achats.filter(fournisseur_id=fournisseur_id)

    zero = Value(0, output_field=DecimalField(max_digits=20, decimal_places=2))

    agg_achats = achats.aggregate(
        ht=Coalesce(Sum("total_ht"), zero),
        tva=Coalesce(Sum("total_tva"), zero),
        ttc=Coalesce(Sum("total_ttc"), zero),
    )
    purchases_total_ht  = float(agg_achats["ht"])
    purchases_total_tva = float(agg_achats["tva"])
    purchases_total_ttc = float(agg_achats["ttc"])

    payments_total = float(versements.aggregate(total=Coalesce(Sum("montant"), zero))["total"])

    purchases_breakdown = [
        {"name": "HT",  "value": purchases_total_ht},
        {"name": "TVA", "value": purchases_total_tva},
        {"name": "TTC", "value": purchases_total_ttc},
    ]

    quickview_monthly = []
    for y, m, label in _last_n_months(6):
        start, end = _month_edges(y, m)
        monthly = _date_filter(achats, "date_achat", start, end)
        total = monthly.aggregate(total=Coalesce(Sum("total_ttc"), zero))["total"]
        quickview_monthly.append({"label": label, "value": float(total)})

    recent_purchases = []
    for a in achats.select_related("fournisseur").order_by("-date_achat")[:5]:
        recent_purchases.append({
            "id": str(a.pk),
            "supplier": _supplier_label(getattr(a, "fournisseur", None)),
            "status": getattr(a, "mode_paiement", "—"),
            "amount": float(getattr(a, "total_ttc", 0)),
            "date": a.date_achat.strftime("%d/%m/%Y") if getattr(a, "date_achat", None) else "",
        })

    projects_count = Projet.objects.count() if not projet_id else Projet.objects.filter(pk=projet_id).count()

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
