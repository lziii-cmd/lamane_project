# core/views/rh.py
"""Vues RH, employés, clients, fournisseurs — LAMANE BTP."""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal
import json

from core.models import (
    Employe, ProjetEmploye, Proprietaire, Projet, Fournisseur,
    Achat, Versement, AvancementChantier,
)
from core.forms import EmployeForm, ProprietaireForm, FournisseurForm
from core.permissions import role_required
from core.views._helpers import (
    _fmt, _success, apply_achat_filters, apply_versement_filters, apply_projet_filters,
)

__all__ = [
    "rh_view", "employe_create_view", "employe_detail_view",
    "employe_edit_view", "employe_delete_view",
    "clients_view", "client_create_view", "client_detail_view",
    "client_edit_view", "client_delete_view",
    "fournisseurs_view", "fournisseur_create_view",
    "fournisseur_detail_view", "fournisseur_edit_view", "fournisseur_delete_view",
]


@login_required
@role_required("comptable", "chef_chantier")
def rh_view(request):
    employes = Employe.objects.all().order_by("nom")
    hommes   = employes.filter(sexe="M").count()
    femmes   = employes.filter(sexe="F").count()
    postes   = employes.values("poste").annotate(count=Count("id")).order_by("-count")

    affectations_qs = ProjetEmploye.objects.select_related("employe", "projet")
    nb_affectes     = affectations_qs.values("employe").distinct().count()
    affectations    = affectations_qs.all()[:30]

    ctx = {
        "page": "rh", "employes": employes, "total_employes": employes.count(),
        "hommes": hommes, "femmes": femmes, "nb_affectes": nb_affectes,
        "postes": list(postes), "affectations": affectations,
        "genre_json":         json.dumps({"Hommes": hommes, "Femmes": femmes}),
        "postes_labels_json": json.dumps([p["poste"] for p in postes]),
        "postes_values_json": json.dumps([p["count"] for p in postes]),
    }
    return render(request, "lamane/rh.html", ctx)


@login_required
@role_required("comptable")
def employe_create_view(request):
    form = EmployeForm(request.POST or None)
    if form.is_valid():
        e = form.save()
        return _success(request, f"Employé « {e.nom_complet()} » créé.", "ui_rh")
    return render(request, "lamane/forms/employe_form.html",
                  {"form": form, "title": "Nouvel employé",
                   "action": "Créer", "page": "rh", "back_url": "/rh/"})


@login_required
@role_required("comptable", "chef_chantier")
def employe_detail_view(request, pk):
    employe = get_object_or_404(Employe, pk=pk)
    affectations = ProjetEmploye.objects.filter(employe=employe).select_related("projet").order_by("-projet__date_debut")
    ctx = {
        "page": "rh", "employe": employe,
        "affectations": affectations, "nb_projets": affectations.count(),
    }
    return render(request, "lamane/employe_detail.html", ctx)


@login_required
@role_required("comptable")
def employe_edit_view(request, pk):
    e = get_object_or_404(Employe, pk=pk)
    form = EmployeForm(request.POST or None, instance=e)
    if form.is_valid():
        form.save()
        return _success(request, "Employé modifié.", "ui_rh")
    return render(request, "lamane/forms/employe_form.html",
                  {"form": form, "title": f"Modifier — {e.nom_complet()}",
                   "action": "Enregistrer", "page": "rh", "back_url": "/rh/", "obj": e})


@login_required
@role_required()
def employe_delete_view(request, pk):
    employe = get_object_or_404(Employe, pk=pk)
    if request.method == "POST":
        employe.delete()
        return _success(request, f"Employé {employe} supprimé.", "ui_rh")
    return render(request, "lamane/forms/confirm_delete.html",
                  {"obj": employe, "titre": str(employe), "page": "rh", "back_url": "/rh/"})


# ─── CLIENTS ─────────────────────────────────────────────────────────────────

@login_required
@role_required("comptable", "chef_chantier")
def clients_view(request):
    q = request.GET.get("q", "")
    clients = Proprietaire.objects.all()
    if q:
        clients = clients.filter(
            Q(entreprise__icontains=q) | Q(nom__icontains=q)
            | Q(prenom__icontains=q) | Q(telephone__icontains=q)
        )
    clients = clients.order_by("entreprise", "nom")

    clients_data = []
    for c in clients:
        projets_c    = apply_projet_filters(Projet.objects.filter(proprietaire=c), request)
        total_achats = apply_achat_filters(Achat.objects.filter(projet__proprietaire=c), request).aggregate(s=Coalesce(Sum("total_ttc"), Decimal("0")))["s"]
        clients_data.append({
            "client": c, "nb_projets": projets_c.count(),
            "total_achats_fmt": _fmt(total_achats),
            "derniers_projets": projets_c.order_by("-date_debut")[:2],
        })

    ctx = {
        "page": "clients", "clients_data": clients_data,
        "total_clients": Proprietaire.objects.count(),
        "q": q, "nb_resultats": len(clients_data),
    }
    return render(request, "lamane/clients_list.html", ctx)


@login_required
@role_required("comptable", "chef_chantier")
def client_detail_view(request, pk):
    from calendar import monthrange
    client  = get_object_or_404(Proprietaire, pk=pk)
    projets = apply_projet_filters(Projet.objects.filter(proprietaire=client), request).select_related("type_projet").order_by("-date_debut")
    total_achats = apply_achat_filters(Achat.objects.filter(projet__proprietaire=client), request).aggregate(
        ht=Coalesce(Sum("total_ht"), Decimal("0")),
        ttc=Coalesce(Sum("total_ttc"), Decimal("0")),
    )
    total_verse = apply_versement_filters(Versement.objects.filter(projet__proprietaire=client), request).aggregate(s=Coalesce(Sum("montant"), Decimal("0")))["s"]

    projets_data = []
    for p in projets:
        av = AvancementChantier.objects.filter(projet=p).order_by("-periode").first()
        ta = apply_achat_filters(Achat.objects.filter(projet=p), request).aggregate(s=Coalesce(Sum("total_ttc"), Decimal("0")))["s"]
        projets_data.append({"projet": p, "avancement": av, "total_achats": _fmt(ta)})

    today = timezone.now().date()
    monthly_labels, monthly_vers = [], []
    for i in range(5, -1, -1):
        m = ((today.month - i - 1) % 12) + 1
        y = today.year if (today.month - i) > 0 else today.year - 1
        start = today.replace(year=y, month=m, day=1)
        end   = today.replace(year=y, month=m, day=monthrange(y, m)[1])
        monthly_labels.append(start.strftime("%b %Y"))
        monthly_vers.append(float(apply_versement_filters(Versement.objects.filter(projet__proprietaire=client), request).filter(date_versement__range=[start, end]).aggregate(s=Coalesce(Sum("montant"), Decimal("0")))["s"]))

    ctx = {
        "page": "clients", "client": client, "projets_data": projets_data,
        "total_achats_ht":  _fmt(total_achats["ht"]),
        "total_achats_ttc": _fmt(total_achats["ttc"]),
        "total_verse":      _fmt(total_verse),
        "solde_positif": float(total_verse) >= float(total_achats["ttc"]),
        "monthly_labels_json": json.dumps(monthly_labels),
        "monthly_vers_json":   json.dumps(monthly_vers),
    }
    return render(request, "lamane/client_detail.html", ctx)


@login_required
@role_required("comptable")
def client_create_view(request):
    form = ProprietaireForm(request.POST or None)
    if form.is_valid():
        c = form.save()
        return _success(request, f"Client « {c.nom_complet} » créé.", "ui_clients")
    return render(request, "lamane/forms/client_form.html",
                  {"form": form, "title": "Nouveau client / propriétaire",
                   "action": "Créer", "page": "clients", "back_url": "/clients/"})


@login_required
@role_required("comptable")
def client_edit_view(request, pk):
    client = get_object_or_404(Proprietaire, pk=pk)
    form = ProprietaireForm(request.POST or None, instance=client)
    if form.is_valid():
        form.save()
        return _success(request, "Client modifié.", f"/clients/{pk}/")
    return render(request, "lamane/forms/client_form.html",
                  {"form": form, "title": f"Modifier — {client.nom_complet}",
                   "action": "Enregistrer", "page": "clients",
                   "back_url": f"/clients/{pk}/", "obj": client})


@login_required
@role_required()
def client_delete_view(request, pk):
    client = get_object_or_404(Proprietaire, pk=pk)
    if request.method == "POST":
        client.delete()
        return _success(request, "Client supprimé.", "ui_clients")
    return render(request, "lamane/forms/confirm_delete.html",
                  {"obj": client, "titre": str(client), "page": "clients", "back_url": "/clients/"})


# ─── FOURNISSEURS ─────────────────────────────────────────────────────────────

@login_required
@role_required("comptable", "gestionnaire")
def fournisseurs_view(request):
    q = request.GET.get("q", "")
    fournisseurs = Fournisseur.objects.all()
    if q:
        fournisseurs = fournisseurs.filter(
            Q(entreprise__icontains=q) | Q(nom__icontains=q) | Q(prenom__icontains=q)
        )
    fournisseurs = fournisseurs.order_by("entreprise", "nom")

    f_data = []
    for f in fournisseurs:
        achats = apply_achat_filters(Achat.objects.filter(fournisseur=f), request)
        total  = achats.aggregate(s=Coalesce(Sum("total_ttc"), Decimal("0")))["s"]
        f_data.append({
            "fournisseur": f, "nb_achats": achats.count(),
            "total_ttc": float(total), "total_ttc_fmt": _fmt(total),
        })

    ctx = {
        "page": "fournisseurs", "f_data": f_data,
        "total_fournisseurs": Fournisseur.objects.count(),
        "q": q, "nb_resultats": len(f_data),
    }
    return render(request, "lamane/fournisseurs.html", ctx)


@login_required
@role_required("comptable", "gestionnaire")
def fournisseur_create_view(request):
    form = FournisseurForm(request.POST or None)
    if form.is_valid():
        f = form.save()
        return _success(request, f"Fournisseur « {f} » créé.", "ui_fournisseurs")
    return render(request, "lamane/forms/fournisseur_form.html",
                  {"form": form, "title": "Nouveau fournisseur",
                   "action": "Créer", "page": "fournisseurs", "back_url": "/fournisseurs/"})


@login_required
@role_required("comptable", "gestionnaire")
def fournisseur_detail_view(request, pk):
    four = get_object_or_404(Fournisseur, pk=pk)
    achats_qs = apply_achat_filters(Achat.objects.filter(fournisseur=four), request)
    achats = achats_qs.select_related("projet").order_by("-date_achat")[:20]
    total_achats = achats_qs.aggregate(
        ht=Coalesce(Sum("total_ht"), Decimal("0")),
        ttc=Coalesce(Sum("total_ttc"), Decimal("0")),
    )
    ctx = {
        "page": "fournisseurs", "four": four, "achats": achats,
        "total_ht": _fmt(total_achats["ht"]),
        "total_ttc": _fmt(total_achats["ttc"]),
        "nb_achats": achats_qs.count(),
    }
    return render(request, "lamane/fournisseur_detail.html", ctx)


@login_required
@role_required("comptable", "gestionnaire")
def fournisseur_edit_view(request, pk):
    f = get_object_or_404(Fournisseur, pk=pk)
    form = FournisseurForm(request.POST or None, instance=f)
    if form.is_valid():
        form.save()
        return _success(request, "Fournisseur modifié.", "ui_fournisseurs")
    return render(request, "lamane/forms/fournisseur_form.html",
                  {"form": form, "title": f"Modifier — {f}",
                   "action": "Enregistrer", "page": "fournisseurs",
                   "back_url": "/fournisseurs/", "obj": f})


@login_required
@role_required("comptable")
def fournisseur_delete_view(request, pk):
    four = get_object_or_404(Fournisseur, pk=pk)
    if request.method == "POST":
        four.delete()
        return _success(request, "Fournisseur supprimé.", "ui_fournisseurs")
    return render(request, "lamane/forms/confirm_delete.html",
                  {"obj": four, "titre": str(four), "page": "fournisseurs",
                   "back_url": "/fournisseurs/"})
