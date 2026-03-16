"""
core/views_html.py — Vues HTML (rendu serveur) — LAMANE BTP
"""
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, Count, Avg, Q, Max, Min
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal
import json

from core.models import (
    Projet, Employe, Fournisseur, MarcheTravaux,
    AvancementChantier, SousTraitant, ContratSousTraitance,
    SituationMensuelle, Achat, Versement, Proprietaire,
    LigneAchat, PhaseVersement, ProjetEmploye,
    Materiel, CategorieMateriel,
)


def _fmt(val, dec=0):
    try:
        v = float(val or 0)
        return f"{v:,.{dec}f}".replace(",", " ")
    except Exception:
        return "0"


# ─── DASHBOARD ───────────────────────────────────────────────────────────────
def dashboard_view(request):
    from calendar import monthrange
    today = timezone.now().date()

    total_projets = Projet.objects.count()
    en_cours      = Projet.objects.filter(statut="En cours").count()
    termines      = Projet.objects.filter(statut="Terminé").count()
    en_attente    = Projet.objects.filter(statut="En attente").count()
    en_pause      = Projet.objects.filter(statut="En pause").count()

    agg = Achat.objects.aggregate(
        total_ht=Coalesce(Sum("total_ht"), Decimal("0")),
        total_tva=Coalesce(Sum("total_tva"), Decimal("0")),
        total_ttc=Coalesce(Sum("total_ttc"), Decimal("0")),
    )
    total_versements  = Versement.objects.aggregate(s=Coalesce(Sum("montant"), Decimal("0")))["s"]
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
        va = Achat.objects.filter(date_achat__range=[start, end]).aggregate(s=Coalesce(Sum("total_ttc"), Decimal("0")))["s"]
        vv = Versement.objects.filter(date_versement__range=[start, end]).aggregate(s=Coalesce(Sum("montant"), Decimal("0")))["s"]
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
        "total_achats_count": Achat.objects.count(),
        "total_versements_count": Versement.objects.count(),
        "statuts_data_json": json.dumps(statuts_data),
        "monthly_labels_json": json.dumps(monthly_labels),
        "monthly_achats_json": json.dumps(monthly_achats),
        "monthly_versements_json": json.dumps(monthly_versements_list),
        "recent_achats": Achat.objects.select_related("fournisseur", "projet").order_by("-date_achat")[:8],
    }
    return render(request, "lamane/dashboard.html", ctx)


# ─── PROJETS ─────────────────────────────────────────────────────────────────
def projets_list_view(request):
    q             = request.GET.get("q", "")
    statut_filter = request.GET.get("statut", "")
    projets = Projet.objects.select_related("proprietaire", "type_projet").all()
    if q:
        projets = projets.filter(Q(nom__icontains=q) | Q(localisation__icontains=q))
    if statut_filter:
        projets = projets.filter(statut=statut_filter)
    projets = projets.order_by("-date_debut")

    projets_data = []
    for p in projets[:60]:
        total_achats = Achat.objects.filter(projet=p).aggregate(s=Coalesce(Sum("total_ttc"), Decimal("0")))["s"]
        marche       = MarcheTravaux.objects.filter(projet=p).first()
        avancement   = AvancementChantier.objects.filter(projet=p).order_by("-periode").first()
        projets_data.append({
            "projet": p, "total_achats": float(total_achats),
            "total_achats_fmt": _fmt(total_achats), "marche": marche, "avancement": avancement,
        })

    ctx = {
        "page": "projets",
        "projets_data": projets_data,
        "total_projets": Projet.objects.count(),
        "q": q, "statut_filter": statut_filter,
        "statuts": ["En cours", "En attente", "En pause", "Terminé"],
        "nb_resultats": len(projets_data),
    }
    return render(request, "lamane/projets_list.html", ctx)


def projet_detail_view(request, pk):
    projet     = get_object_or_404(Projet, pk=pk)
    achats     = Achat.objects.filter(projet=projet).select_related("fournisseur").order_by("-date_achat")
    versements = Versement.objects.filter(projet=projet).select_related("phase").order_by("-date_versement")
    marche     = MarcheTravaux.objects.filter(projet=projet).first()
    avancements = AvancementChantier.objects.filter(projet=projet).order_by("periode")
    situations  = SituationMensuelle.objects.filter(projet=projet).order_by("numero_situation")
    contrats_st = ContratSousTraitance.objects.filter(projet=projet).select_related("sous_traitant")
    employes_affectes = ProjetEmploye.objects.filter(projet=projet).select_related("employe")

    total_achats = achats.aggregate(
        ht=Coalesce(Sum("total_ht"), Decimal("0")),
        ttc=Coalesce(Sum("total_ttc"), Decimal("0")),
    )
    total_verse = versements.aggregate(s=Coalesce(Sum("montant"), Decimal("0")))["s"]
    solde_val   = float(total_verse) - float(total_achats["ttc"])

    av_labels    = [str(a.periode) for a in avancements]
    av_physique  = [float(a.taux_physique) for a in avancements]
    av_financier = [float(a.taux_financier) for a in avancements]
    av_planifie  = [float(a.taux_planifie) for a in avancements]

    ctx = {
        "page": "projets", "projet": projet,
        "achats": achats, "versements": versements, "marche": marche,
        "avancements": avancements, "situations": situations,
        "contrats_st": contrats_st, "employes_affectes": employes_affectes,
        "total_achats_ht": _fmt(total_achats["ht"]),
        "total_achats_ttc": _fmt(total_achats["ttc"]),
        "total_verse": _fmt(total_verse),
        "solde": _fmt(abs(solde_val)), "solde_positif": solde_val >= 0,
        "av_labels_json":    json.dumps(av_labels),
        "av_physique_json":  json.dumps(av_physique),
        "av_financier_json": json.dumps(av_financier),
        "av_planifie_json":  json.dumps(av_planifie),
    }
    return render(request, "lamane/projet_detail.html", ctx)


# ─── FINANCES ────────────────────────────────────────────────────────────────
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

    ctx = {
        "page": "finances", "today": today,
        "total_ht": _fmt(agg["total_ht"]), "total_tva": _fmt(agg["total_tva"]),
        "total_ttc": _fmt(agg["total_ttc"]), "total_versements": _fmt(total_versements),
        "solde": _fmt(abs(float(total_versements) - float(agg["total_ttc"]))),
        "solde_positif": float(total_versements) >= float(agg["total_ttc"]),
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


# ─── ACHATS ──────────────────────────────────────────────────────────────────
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
    achats = achats[:100]

    agg = Achat.objects.aggregate(
        total_ht=Coalesce(Sum("total_ht"), Decimal("0")),
        total_ttc=Coalesce(Sum("total_ttc"), Decimal("0")),
        count=Count("id"),
    )
    ctx = {
        "page": "achats", "achats": achats, "q": q, "mode_filter": mode_filter,
        "total_achats": agg["count"],
        "total_ht_fmt": _fmt(agg["total_ht"]), "total_ttc_fmt": _fmt(agg["total_ttc"]),
        "modes_choices": ["espèces", "virement", "chèque", "autre"],
    }
    return render(request, "lamane/achats_list.html", ctx)


def achat_detail_view(request, pk):
    achat  = get_object_or_404(Achat, pk=pk)
    lignes = LigneAchat.objects.filter(achat=achat).select_related("materiel")
    ctx = {"page": "achats", "achat": achat, "lignes": lignes}
    return render(request, "lamane/achat_detail.html", ctx)


# ─── VERSEMENTS ──────────────────────────────────────────────────────────────
def versements_view(request):
    q           = request.GET.get("q", "")
    type_filter = request.GET.get("type", "")
    # BUG FIX: ne pas select_related("phase") — PhaseVersement.__str__ accède à EtapeStandard
    # qui peut être supprimé (FK cassée → DoesNotExist). On passe les IDs bruts.
    versements  = Versement.objects.select_related("projet").order_by("-date_versement")
    if q:
        versements = versements.filter(
            Q(projet__nom__icontains=q) | Q(libelle__icontains=q) | Q(reference_paiement__icontains=q)
        )
    if type_filter:
        versements = versements.filter(type_versement=type_filter)
    versements = versements[:100]

    agg = Versement.objects.aggregate(total=Coalesce(Sum("montant"), Decimal("0")), count=Count("id"))
    types_stats = Versement.objects.values("type_versement").annotate(
        total=Coalesce(Sum("montant"), Decimal("0")), count=Count("id")
    ).order_by("-total")

    ctx = {
        "page": "versements", "versements": versements, "q": q, "type_filter": type_filter,
        "total_versements": agg["count"], "montant_total": _fmt(agg["total"]),
        "types_stats": list(types_stats),
        "types_choices": ["chèque", "virement bancaire", "virement om", "wave", "espèces", "autres"],
        "types_labels_json": json.dumps([t.get("type_versement") or "—" for t in types_stats]),
        "types_values_json": json.dumps([float(t["total"]) for t in types_stats]),
    }
    return render(request, "lamane/versements_list.html", ctx)


# ─── CHANTIERS ───────────────────────────────────────────────────────────────
def chantiers_view(request):
    projets_actifs = Projet.objects.filter(statut="En cours").select_related("proprietaire", "type_projet")
    chantiers_data = []
    for p in projets_actifs:
        chantiers_data.append({
            "projet": p,
            "dernier_avancement": AvancementChantier.objects.filter(projet=p).order_by("-periode").first(),
            "marche": MarcheTravaux.objects.filter(projet=p).first(),
            "nb_contrats_st": ContratSousTraitance.objects.filter(projet=p).count(),
        })

    ctx = {
        "page": "chantiers",
        "chantiers_data": chantiers_data,
        "avancements_all": AvancementChantier.objects.select_related("projet").order_by("-periode")[:50],
        "avg_physique":  round(AvancementChantier.objects.filter(projet__statut="En cours").aggregate(avg=Avg("taux_physique"))["avg"] or 0, 1),
        "avg_financier": round(AvancementChantier.objects.filter(projet__statut="En cours").aggregate(avg=Avg("taux_financier"))["avg"] or 0, 1),
        "avg_planifie":  round(AvancementChantier.objects.filter(projet__statut="En cours").aggregate(avg=Avg("taux_planifie"))["avg"] or 0, 1),
        "total_ouvriers":    AvancementChantier.objects.filter(projet__statut="En cours").aggregate(s=Coalesce(Sum("effectif_ouvriers"), 0))["s"],
        "total_encadrement": AvancementChantier.objects.filter(projet__statut="En cours").aggregate(s=Coalesce(Sum("effectif_encadrement"), 0))["s"],
        "nb_chantiers": len(chantiers_data),
    }
    return render(request, "lamane/chantiers.html", ctx)


def chantier_detail_view(request, pk):
    projet      = get_object_or_404(Projet, pk=pk)
    avancements = AvancementChantier.objects.filter(projet=projet).order_by("periode")
    marche      = MarcheTravaux.objects.filter(projet=projet).first()
    contrats_st = ContratSousTraitance.objects.filter(projet=projet).select_related("sous_traitant")
    situations  = SituationMensuelle.objects.filter(projet=projet).order_by("numero_situation")

    dernier_av      = avancements.last()
    avg_ouvriers    = avancements.aggregate(avg=Avg("effectif_ouvriers"))["avg"] or 0
    avg_encadrement = avancements.aggregate(avg=Avg("effectif_encadrement"))["avg"] or 0

    ctx = {
        "page": "chantiers",
        "projet": projet, "marche": marche,
        "avancements": avancements, "dernier_av": dernier_av,
        "contrats_st": contrats_st, "situations": situations,
        "avg_ouvriers": round(avg_ouvriers, 0), "avg_encadrement": round(avg_encadrement, 0),
        "nb_releves": avancements.count(),
        "av_labels_json":    json.dumps([str(a.periode) for a in avancements]),
        "av_physique_json":  json.dumps([float(a.taux_physique) for a in avancements]),
        "av_financier_json": json.dumps([float(a.taux_financier) for a in avancements]),
        "av_planifie_json":  json.dumps([float(a.taux_planifie) for a in avancements]),
        "av_ouvriers_json":  json.dumps([a.effectif_ouvriers for a in avancements]),
    }
    return render(request, "lamane/chantier_detail.html", ctx)


# ─── MARCHÉS ─────────────────────────────────────────────────────────────────
def marches_view(request):
    statut_filter = request.GET.get("statut", "")
    marches = MarcheTravaux.objects.select_related("projet").order_by("-date_signature")
    if statut_filter:
        marches = marches.filter(statut=statut_filter)
    montant_total = MarcheTravaux.objects.aggregate(s=Coalesce(Sum("montant_marche"), Decimal("0")))["s"]
    avance_totale = MarcheTravaux.objects.aggregate(s=Coalesce(Sum("montant_avance_demarrage"), Decimal("0")))["s"]
    statuts_marche = MarcheTravaux.objects.values("statut").annotate(
        count=Count("id"), total=Coalesce(Sum("montant_marche"), Decimal("0"))
    )
    LABELS = {"en_attente": "En attente", "en_cours": "En cours",
              "reception_provisoire": "Récept. provisoire", "reception_definitive": "Récept. définitive"}
    ctx = {
        "page": "marches", "marches": marches, "statut_filter": statut_filter,
        "total_marches": MarcheTravaux.objects.count(),
        "montant_total": _fmt(montant_total), "avance_totale": _fmt(avance_totale),
        "en_cours_m": MarcheTravaux.objects.filter(statut="en_cours").count(),
        "termines_m": MarcheTravaux.objects.filter(statut="reception_definitive").count(),
        "statuts_marche": list(statuts_marche), "statuts_labels": LABELS,
        "statuts_marche_json": json.dumps([
            {"statut": s["statut"], "count": s["count"], "total": float(s["total"])}
            for s in statuts_marche
        ]),
    }
    return render(request, "lamane/marches.html", ctx)


# ─── SOUS-TRAITANTS ──────────────────────────────────────────────────────────
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

    # BUG FIX: le related_name est "contrats" (pas "contratsoustraitance")
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


# ─── CLIENTS ─────────────────────────────────────────────────────────────────
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
        projets_c    = Projet.objects.filter(proprietaire=c)
        total_achats = Achat.objects.filter(projet__proprietaire=c).aggregate(s=Coalesce(Sum("total_ttc"), Decimal("0")))["s"]
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


def client_detail_view(request, pk):
    from calendar import monthrange
    client  = get_object_or_404(Proprietaire, pk=pk)
    projets = Projet.objects.filter(proprietaire=client).select_related("type_projet").order_by("-date_debut")
    total_achats = Achat.objects.filter(projet__proprietaire=client).aggregate(
        ht=Coalesce(Sum("total_ht"), Decimal("0")),
        ttc=Coalesce(Sum("total_ttc"), Decimal("0")),
    )
    total_verse = Versement.objects.filter(projet__proprietaire=client).aggregate(s=Coalesce(Sum("montant"), Decimal("0")))["s"]

    projets_data = []
    for p in projets:
        av = AvancementChantier.objects.filter(projet=p).order_by("-periode").first()
        ta = Achat.objects.filter(projet=p).aggregate(s=Coalesce(Sum("total_ttc"), Decimal("0")))["s"]
        projets_data.append({"projet": p, "avancement": av, "total_achats": _fmt(ta)})

    today = timezone.now().date()
    monthly_labels, monthly_vers = [], []
    for i in range(5, -1, -1):
        m = ((today.month - i - 1) % 12) + 1
        y = today.year if (today.month - i) > 0 else today.year - 1
        start = today.replace(year=y, month=m, day=1)
        end   = today.replace(year=y, month=m, day=monthrange(y, m)[1])
        monthly_labels.append(start.strftime("%b %Y"))
        monthly_vers.append(float(Versement.objects.filter(projet__proprietaire=client, date_versement__range=[start, end]).aggregate(s=Coalesce(Sum("montant"), Decimal("0")))["s"]))

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


# ─── STOCK ───────────────────────────────────────────────────────────────────
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
        "q": q, "cat_filter": cat,
    }
    return render(request, "lamane/stock.html", ctx)


# ─── RH ──────────────────────────────────────────────────────────────────────
def rh_view(request):
    employes = Employe.objects.all().order_by("nom")
    hommes   = employes.filter(sexe="M").count()
    femmes   = employes.filter(sexe="F").count()
    postes   = employes.values("poste").annotate(count=Count("id")).order_by("-count")

    # BUG FIX: calculer nb_affectes AVANT le slice [:30]
    affectations_qs = ProjetEmploye.objects.select_related("employe", "projet")
    nb_affectes     = affectations_qs.values("employe").distinct().count()
    affectations    = affectations_qs.all()[:30]

    ctx = {
        "page": "rh",
        "employes": employes, "total_employes": employes.count(),
        "hommes": hommes, "femmes": femmes, "nb_affectes": nb_affectes,
        "postes": list(postes), "affectations": affectations,
        "genre_json":         json.dumps({"Hommes": hommes, "Femmes": femmes}),
        "postes_labels_json": json.dumps([p["poste"] for p in postes]),
        "postes_values_json": json.dumps([p["count"] for p in postes]),
    }
    return render(request, "lamane/rh.html", ctx)


# ─── FOURNISSEURS ────────────────────────────────────────────────────────────
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
        achats = Achat.objects.filter(fournisseur=f)
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
