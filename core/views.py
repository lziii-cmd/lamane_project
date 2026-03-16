from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from datetime import datetime
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_GET
from django.db.models import Sum, Q

from .services.dashboard import compute_dashboard_stats
from .services.finances import compute_finance_stats

from math import ceil


# Models
from core.models.projet import Projet
from core.models.achat import Achat
from core.models.versement import Versement
from core.models.projet_employe import ProjetEmploye
from core.models.proprietaire import Proprietaire



def parse_date_or_none(s: str):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


class DashboardStatsView(APIView):
    def get(self, request):
        f_from = parse_date_or_none(request.query_params.get("from", ""))
        f_to = parse_date_or_none(request.query_params.get("to", ""))
        pid = request.query_params.get("projet")
        fid = request.query_params.get("fournisseur")

        filters = {
            "from_date": f_from,
            "to_date": f_to,
            "projet_id": int(pid) if pid and pid.isdigit() else None,
            "fournisseur_id": int(fid) if fid and fid.isdigit() else None,
        }

        cache_key = f"dash:{filters['from_date']}:{filters['to_date']}:{filters['projet_id']}:{filters['fournisseur_id']}"
        data = cache.get(cache_key)
        if not data:
            data = compute_dashboard_stats(filters)
            cache.set(cache_key, data, 60)

        return Response(data, status=status.HTTP_200_OK)


@require_GET
def dashboard_stats(request):
    """Endpoint GET /api/dashboard/stats/ — KPIs généraux."""
    try:
        f_from = _parse_date(request.GET.get("from", ""))
        f_to = _parse_date(request.GET.get("to", ""))
        pid = request.GET.get("projet")
        fid = request.GET.get("fournisseur")
        filters = {
            "from_date": f_from,
            "to_date": f_to,
            "projet_id": pid if pid else None,
            "fournisseur_id": fid if fid else None,
        }
        data = compute_dashboard_stats(filters)
        return JsonResponse(data, safe=True, json_dumps_params={"ensure_ascii": False})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=200)


def _parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def dashboard_stats_finances(request):
    try:
        f_from = _parse_date(request.GET.get("from", ""))
        f_to = _parse_date(request.GET.get("to", ""))
        pid = request.GET.get("projet")
        fid = request.GET.get("fournisseur")

        data = compute_finance_stats(
            from_date=f_from,
            to_date=f_to,
            projet_id=int(pid) if pid and pid.isdigit() else None,
            fournisseur_id=int(fid) if fid and fid.isdigit() else None,
        )
        return JsonResponse(data, json_dumps_params={"ensure_ascii": False})
    except Exception as e:
        empty = {
            "projects_count": 0,
            "purchases_total_ht": 0,
            "purchases_total_tva": 0,
            "purchases_total_ttc": 0,
            "payments_total": 0,
            "purchases_breakdown": [],
            "quickview_monthly": [],
            "recent_purchases": [],
            "error": str(e),
        }
        return JsonResponse(empty, status=200)


# -------------------- PROJETS --------------------

def projets_list(request):
    
    print("projets_list called with GET:", request.GET)
    PAGE_SIZE = 20  # 20 projets par page


    projets = Projet.objects.select_related("proprietaire", "type_projet").all()

    # --- Filtres GET ---
    proprietaire = request.GET.get("proprietaire")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    cout_min = request.GET.get("cout_min")
    cout_max = request.GET.get("cout_max")
    achat_min = request.GET.get("achat_min")
    achat_max = request.GET.get("achat_max")
    localisation = request.GET.get("localisation")

    if proprietaire:
        projets = projets.filter(
            Q(proprietaire__nom__icontains=proprietaire) |
            Q(proprietaire__prenom__icontains=proprietaire) |
            Q(proprietaire__entreprise__icontains=proprietaire)
        )

    if date_from:
        projets = projets.filter(date_debut__gte=date_from)
    if date_to:
        projets = projets.filter(date_debut__lte=date_to)

    if cout_min:
        projets = projets.filter(cout_estime__gte=cout_min)
    if cout_max:
        projets = projets.filter(cout_estime__lte=cout_max)

    if localisation:
        projets = projets.filter(localisation__icontains=localisation)

    # --- Construction JSON ---
    data = []
    for p in projets:
        total_achats = (
            Achat.objects.filter(projet=p).aggregate(s=Sum("total_ttc"))["s"] or 0
        )

        if achat_min and total_achats < float(achat_min):
            continue
        if achat_max and total_achats > float(achat_max):
            continue

        data.append({
            "id": p.id,
            "nom": p.nom,
            "statut": p.statut,
            "localisation": p.localisation,
            "date_debut": p.date_debut,
            "type_projet_nom": p.type_projet.nom if p.type_projet else None,
            "proprietaire_nom": p.proprietaire.nom_complet() if p.proprietaire else None,
            "cout_estime_lamane": p.cout_estime_lamane,
            "total_achats": total_achats,
        })

            # --- Pagination ---
    page = int(request.GET.get("page", 1))
    total_items = len(data)
    total_pages = ceil(total_items / PAGE_SIZE)
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    paged_data = data[start:end]

    response = {
        "results": paged_data,
        "page": page,
        "total_pages": total_pages,
        "total_items": total_items,
    }

    return JsonResponse(response, safe=False)


def projet_detail(request, pk):
    try:
        projet = Projet.objects.get(pk=pk)
    except Projet.DoesNotExist:
        raise Http404("Projet non trouvé")

    achats = list(Achat.objects.filter(projet=projet).values(
        "id", "date_achat", "total_ht", "total_tva", "total_ttc", "fournisseur__entreprise"
    ))

    versements = list(Versement.objects.filter(projet=projet).values(
        "id", "date_versement", "montant", "phase__libelle", "type_versement"
    ))

    employes = list(ProjetEmploye.objects.filter(projet=projet).values(
        "id", "employe__nom", "employe__prenom", "role"
    ))

    data = {
        "id": str(projet.id),
        "nom": projet.nom,
        "type": projet.type_projet.nom if projet.type_projet else None,
        "localisation": projet.localisation,
        "statut": projet.statut,
        "date_debut": str(projet.date_debut),
        "date_fin": str(projet.date_fin) if projet.date_fin else None,
        "cout_estime_lamane": float(projet.cout_estime_lamane),
        "achats": achats,
        "versements": versements,
        "employes": employes,
    }
    return JsonResponse(data, safe=False)


def proprietaire_detail(request, pk):
    try:
        p = Proprietaire.objects.get(pk=pk)
    except Proprietaire.DoesNotExist:
        raise Http404("Propriétaire non trouvé")

    data = {
        "id": p.id,
        "nom": p.nom,
        "prenom": p.prenom,
        "entreprise": p.entreprise,
        "ninea": p.ninea,
        "numero_identite": p.numero_identite,
        "date_naissance": p.date_naissance,
        "type": "Entreprise" if p.est_moral else "Personne Physique",
        # tu peux ajouter tous les champs pertinents
    }
    return JsonResponse(data, safe=False)