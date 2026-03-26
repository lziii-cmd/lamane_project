"""
core/views_html.py — Vues HTML (rendu serveur) — LAMANE BTP
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg, Q, Max, Min, F, Value, DecimalField as DjDecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal
import json

from core.models import (
    Projet, TypeProjet, Employe, Fournisseur, MarcheTravaux,
    AvancementChantier, SousTraitant, ContratSousTraitance,
    SituationMensuelle, Achat, Versement, Proprietaire,
    LigneAchat, PhaseVersement, ProjetEmploye,
    Materiel, CategorieMateriel, BonSortie, LigneBonSortie,
    EtapeStandard,
    CompteComptable, EcritureComptable, LigneEcriture,
    CompteBancaire, TransactionBancaire,
    DocumentProjet, BordereauPrix, LigneBordereau, DecompteGD,
    ProfilUtilisateur,
)
from core.forms import (
    ProjetForm, TypeProjetForm, ProprietaireForm, EmployeForm,
    FournisseurForm, AchatForm, LigneAchatFormSet,
    VersementForm, MaterielForm, CategorieMaterielForm,
    MarcheTravauxForm, AvancementChantierForm,
    SousTraitantForm, ContratSousTraitanceForm,
    BonSortieForm, LigneBonSortieFormSet,
    EtapeStandardForm, PhaseVersementForm,
    CompteComptableForm, EcritureComptableForm, LigneEcritureFormSet,
    CompteBancaireForm, TransactionBancaireForm,
    DocumentProjetForm, BordereauPrixForm, LigneBordereauFormSet,
    DecompteGDForm, ProfilUtilisateurForm,
)
from core.services.comptabilite import (
    generer_ecriture_achat,
    generer_ecriture_versement,
    generer_ecriture_sous_traitance,
)


def _fmt(val, dec=0):
    try:
        v = float(val or 0)
        return f"{v:,.{dec}f}".replace(",", " ")
    except Exception:
        return "0"


# ─── AUTHENTIFICATION ─────────────────────────────────────────────────────────
def login_view(request):
    """Page de connexion."""
    if request.user.is_authenticated:
        return redirect("ui_dashboard")
    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get("next") or request.POST.get("next") or "ui_dashboard"
            return redirect(next_url)
        else:
            error = "Nom d'utilisateur ou mot de passe incorrect."
    return render(request, "lamane/login.html", {"error": error, "next": request.GET.get("next", "")})


def logout_view(request):
    """Déconnexion puis redirection vers la page de reconnexion."""
    logout(request)
    return redirect("ui_logged_out")


def logged_out_view(request):
    """Page post-déconnexion avec option de reconnexion."""
    return render(request, "lamane/logged_out.html")


# ─── DASHBOARD ───────────────────────────────────────────────────────────────
@login_required
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
@login_required
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


@login_required
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
@login_required
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

    # Total sous-traitance global
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


# ─── ACHATS ──────────────────────────────────────────────────────────────────
@login_required
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


@login_required
def achat_detail_view(request, pk):
    achat  = get_object_or_404(Achat, pk=pk)
    lignes = LigneAchat.objects.filter(achat=achat).select_related("materiel")
    ctx = {"page": "achats", "achat": achat, "lignes": lignes}
    return render(request, "lamane/achat_detail.html", ctx)


# ─── VERSEMENTS ──────────────────────────────────────────────────────────────
@login_required
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
@login_required
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


@login_required
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
@login_required
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
@login_required
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
@login_required
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


@login_required
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
@login_required
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


# ─── RH ──────────────────────────────────────────────────────────────────────
@login_required
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
@login_required
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


# ═══════════════════════════════════════════════════════════════════════════════
# ─── VUES CRUD ─────────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

def _success(request, msg, url):
    messages.success(request, msg)
    return redirect(url)


# ─── PROJETS CRUD ────────────────────────────────────────────────────────────

@login_required
def projet_create_view(request):
    form = ProjetForm(request.POST or None)
    if form.is_valid():
        p = form.save()
        return _success(request, f"Projet « {p.nom} » créé avec succès.", "ui_projets_list")
    return render(request, "lamane/forms/projet_form.html",
                  {"form": form, "title": "Nouveau projet", "action": "Créer", "page": "projets"})


@login_required
def projet_edit_view(request, pk):
    projet = get_object_or_404(Projet, pk=pk)
    form = ProjetForm(request.POST or None, instance=projet)
    if form.is_valid():
        form.save()
        return _success(request, "Projet modifié.", f"/projets/{pk}/")
    return render(request, "lamane/forms/projet_form.html",
                  {"form": form, "title": f"Modifier — {projet.nom}",
                   "action": "Enregistrer", "page": "projets", "obj": projet})


@login_required
def projet_delete_view(request, pk):
    projet = get_object_or_404(Projet, pk=pk)
    if request.method == "POST":
        nom = projet.nom
        projet.delete()
        return _success(request, f"Projet « {nom} » supprimé.", "ui_projets_list")
    return render(request, "lamane/forms/confirm_delete.html",
                  {"obj": projet, "titre": projet.nom, "page": "projets",
                   "back_url": f"/projets/{pk}/"})


# ─── TYPES DE PROJETS CRUD ───────────────────────────────────────────────────

@login_required
def types_projets_view(request):
    types = TypeProjet.objects.annotate(nb_projets=Count("projet")).order_by("nom")
    return render(request, "lamane/types_projets.html",
                  {"page": "types_projets", "types": types})


@login_required
def type_projet_create_view(request):
    form = TypeProjetForm(request.POST or None)
    if form.is_valid():
        t = form.save()
        return _success(request, f"Type « {t.nom} » créé.", "ui_types_projets")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": "Nouveau type de projet",
                   "action": "Créer", "page": "types_projets",
                   "back_url": "/types-projets/"})


@login_required
def type_projet_edit_view(request, pk):
    t = get_object_or_404(TypeProjet, pk=pk)
    form = TypeProjetForm(request.POST or None, instance=t)
    if form.is_valid():
        form.save()
        return _success(request, "Type modifié.", "ui_types_projets")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": f"Modifier — {t.nom}",
                   "action": "Enregistrer", "page": "types_projets",
                   "back_url": "/types-projets/", "obj": t})


@login_required
def type_projet_delete_view(request, pk):
    t = get_object_or_404(TypeProjet, pk=pk)
    if request.method == "POST":
        nom = t.nom
        t.delete()
        return _success(request, f"Type « {nom} » supprimé.", "ui_types_projets")
    return render(request, "lamane/forms/confirm_delete.html",
                  {"obj": t, "titre": t.nom, "page": "types_projets",
                   "back_url": "/types-projets/"})


# ─── CLIENTS (PROPRIETAIRES) CRUD ────────────────────────────────────────────

@login_required
def client_create_view(request):
    form = ProprietaireForm(request.POST or None)
    if form.is_valid():
        c = form.save()
        return _success(request, f"Client « {c.nom_complet} » créé.", "ui_clients")
    return render(request, "lamane/forms/client_form.html",
                  {"form": form, "title": "Nouveau client / propriétaire",
                   "action": "Créer", "page": "clients", "back_url": "/clients/"})


@login_required
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


# ─── FOURNISSEURS CRUD ───────────────────────────────────────────────────────

@login_required
def fournisseur_create_view(request):
    form = FournisseurForm(request.POST or None)
    if form.is_valid():
        f = form.save()
        return _success(request, f"Fournisseur « {f} » créé.", "ui_fournisseurs")
    return render(request, "lamane/forms/fournisseur_form.html",
                  {"form": form, "title": "Nouveau fournisseur",
                   "action": "Créer", "page": "fournisseurs",
                   "back_url": "/fournisseurs/"})


@login_required
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


# ─── EMPLOYES CRUD ───────────────────────────────────────────────────────────

@login_required
def employe_create_view(request):
    form = EmployeForm(request.POST or None)
    if form.is_valid():
        e = form.save()
        return _success(request, f"Employé « {e.nom_complet()} » créé.", "ui_rh")
    return render(request, "lamane/forms/employe_form.html",
                  {"form": form, "title": "Nouvel employé",
                   "action": "Créer", "page": "rh", "back_url": "/rh/"})


@login_required
def employe_edit_view(request, pk):
    e = get_object_or_404(Employe, pk=pk)
    form = EmployeForm(request.POST or None, instance=e)
    if form.is_valid():
        form.save()
        return _success(request, "Employé modifié.", "ui_rh")
    return render(request, "lamane/forms/employe_form.html",
                  {"form": form, "title": f"Modifier — {e.nom_complet()}",
                   "action": "Enregistrer", "page": "rh",
                   "back_url": "/rh/", "obj": e})


# ─── MATERIAUX CRUD ──────────────────────────────────────────────────────────

@login_required
def materiel_create_view(request):
    form = MaterielForm(request.POST or None)
    if form.is_valid():
        m = form.save()
        return _success(request, f"Matériau « {m.nom} » créé.", "ui_stock")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": "Nouveau matériau",
                   "action": "Créer", "page": "stock", "back_url": "/stock/"})


@login_required
def materiel_edit_view(request, pk):
    m = get_object_or_404(Materiel, pk=pk)
    form = MaterielForm(request.POST or None, instance=m)
    if form.is_valid():
        form.save()
        return _success(request, "Matériau modifié.", "ui_stock")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": f"Modifier — {m.nom}",
                   "action": "Enregistrer", "page": "stock",
                   "back_url": "/stock/", "obj": m})


@login_required
def categorie_materiel_create_view(request):
    form = CategorieMaterielForm(request.POST or None)
    if form.is_valid():
        c = form.save()
        return _success(request, f"Catégorie « {c.nom} » créée.", "ui_stock")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": "Nouvelle catégorie de matériau",
                   "action": "Créer", "page": "stock", "back_url": "/stock/"})


# ─── ACHATS CRUD ─────────────────────────────────────────────────────────────

@login_required
def achat_create_view(request):
    form = AchatForm(request.POST or None, request.FILES or None)
    formset = LigneAchatFormSet(request.POST or None, prefix="lignes")
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        achat = form.save()
        formset.instance = achat
        formset.save()
        # Recalculer les totaux après sauvegarde des lignes
        achat.calcul_totaux()
        achat.save(update_fields=["total_ht", "total_tva", "total_ttc"])
        # Générer le bon d'entrée PDF
        try:
            achat.generate_bon_entree_pdf()
            achat.save(update_fields=["bon_entree_pdf"])
        except Exception as e:
            print(f"[BON ENTREE] Erreur PDF: {e}")
        # Écriture comptable automatique
        try:
            generer_ecriture_achat(achat)
        except Exception as e:
            print(f"[COMPTA] Erreur écriture achat: {e}")
        return _success(request,
                        f"Achat enregistré — Bon d'entrée généré automatiquement.",
                        "ui_achats")
    return render(request, "lamane/forms/achat_form.html",
                  {"form": form, "formset": formset,
                   "title": "Nouvel achat de matériaux",
                   "action": "Enregistrer", "page": "achats",
                   "back_url": "/achats/"})


@login_required
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
def achat_delete_view(request, pk):
    achat = get_object_or_404(Achat, pk=pk)
    if request.method == "POST":
        achat.delete()
        return _success(request, "Achat supprimé.", "ui_achats")
    return render(request, "lamane/forms/confirm_delete.html",
                  {"obj": achat, "titre": str(achat), "page": "achats",
                   "back_url": f"/achats/{pk}/"})


# ─── VERSEMENTS CRUD ─────────────────────────────────────────────────────────

@login_required
def versement_create_view(request):
    form = VersementForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        v = form.save()
        msg = f"Versement enregistre ({v.numero_facture})"
        if v.facture_pdf:
            msg += " — Facture PDF generee automatiquement."
        else:
            msg += " — Attention : la facture PDF n'a pas pu etre generee."
        # Écriture comptable automatique
        try:
            generer_ecriture_versement(v)
        except Exception as e:
            print(f"[COMPTA] Erreur écriture versement: {e}")
        messages.success(request, msg)
        return redirect("ui_versement_detail", pk=v.pk)
    return render(request, "lamane/forms/versement_form.html",
                  {"form": form, "title": "Nouveau versement",
                   "action": "Enregistrer", "page": "versements",
                   "back_url": "/versements/"})


@login_required
def versement_delete_view(request, pk):
    v = get_object_or_404(Versement, pk=pk)
    if request.method == "POST":
        v.delete()
        return _success(request, "Versement supprimé.", "ui_versements")
    return render(request, "lamane/forms/confirm_delete.html",
                  {"obj": v, "titre": str(v), "page": "versements",
                   "back_url": "/versements/"})


# ─── MARCHÉS CRUD ────────────────────────────────────────────────────────────

@login_required
def marche_create_view(request):
    form = MarcheTravauxForm(request.POST or None)
    if form.is_valid():
        m = form.save()
        return _success(request, f"Marché {m.numero_marche} créé.", "ui_marches")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": "Nouveau marché de travaux",
                   "action": "Créer", "page": "marches", "back_url": "/marches/"})


@login_required
def marche_edit_view(request, pk):
    marche = get_object_or_404(MarcheTravaux, pk=pk)
    form = MarcheTravauxForm(request.POST or None, instance=marche)
    if form.is_valid():
        form.save()
        return _success(request, "Marché modifié.", "ui_marches")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": f"Modifier — {marche.numero_marche}",
                   "action": "Enregistrer", "page": "marches",
                   "back_url": "/marches/", "obj": marche})


# ─── AVANCEMENT CHANTIER CRUD ────────────────────────────────────────────────

@login_required
def avancement_create_view(request):
    projet_id = request.GET.get("projet")
    initial = {}
    if projet_id:
        try:
            initial["projet"] = Projet.objects.get(pk=projet_id)
        except Projet.DoesNotExist:
            pass
    form = AvancementChantierForm(request.POST or None, initial=initial)
    if form.is_valid():
        form.save()
        proj_id = form.cleaned_data["projet"].id
        return _success(request, "Relevé d'avancement enregistré.", f"/chantiers/{proj_id}/")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": "Nouveau relevé d'avancement",
                   "action": "Enregistrer", "page": "chantiers",
                   "back_url": "/chantiers/"})


# ─── SOUS-TRAITANTS CRUD ─────────────────────────────────────────────────────

@login_required
def sous_traitant_create_view(request):
    form = SousTraitantForm(request.POST or None)
    if form.is_valid():
        st = form.save()
        return _success(request, f"Sous-traitant « {st.nom} » créé.", "ui_sous_traitants")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": "Nouveau sous-traitant",
                   "action": "Créer", "page": "sous_traitants",
                   "back_url": "/sous-traitants/"})


@login_required
def sous_traitant_edit_view(request, pk):
    st = get_object_or_404(SousTraitant, pk=pk)
    form = SousTraitantForm(request.POST or None, instance=st)
    if form.is_valid():
        form.save()
        return _success(request, "Sous-traitant modifié.", "ui_sous_traitants")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": f"Modifier — {st.nom}",
                   "action": "Enregistrer", "page": "sous_traitants",
                   "back_url": "/sous-traitants/", "obj": st})


# ─── BONS DE SORTIE CRUD ─────────────────────────────────────────────────────

@login_required
def bons_sortie_list_view(request):
    q = request.GET.get("q", "")
    bons = BonSortie.objects.select_related("projet").order_by("-date_sortie")
    if q:
        bons = bons.filter(
            Q(projet__nom__icontains=q) | Q(reference__icontains=q)
            | Q(responsable__icontains=q)
        )
    bons = bons[:100]

    agg = BonSortie.objects.count()
    total_lignes = LigneBonSortie.objects.count()

    ctx = {
        "page": "stock", "bons": bons, "q": q,
        "total_bons": agg, "total_lignes": total_lignes,
    }
    return render(request, "lamane/bons_sortie.html", ctx)


@login_required
def bon_sortie_create_view(request):
    form = BonSortieForm(request.POST or None)
    formset = LigneBonSortieFormSet(request.POST or None, prefix="lignes")
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        bon = form.save()
        formset.instance = bon
        formset.save()
        # Régénérer le PDF avec les lignes
        bon.bon_pdf = None
        try:
            bon._generate_pdf()
            bon.save(update_fields=["bon_pdf"])
        except Exception as e:
            print(f"[BON SORTIE PDF] Erreur: {e}")
        return _success(request,
                        f"Bon de sortie {bon.reference} créé — PDF généré.",
                        "ui_bons_sortie")
    return render(request, "lamane/forms/bon_sortie_form.html",
                  {"form": form, "formset": formset,
                   "title": "Nouveau bon de sortie matériaux",
                   "action": "Créer", "page": "stock",
                   "back_url": "/stock/bons-sortie/"})


@login_required
def bon_sortie_detail_view(request, pk):
    bon = get_object_or_404(BonSortie, pk=pk)
    lignes = bon.lignes.select_related("materiel")
    ctx = {"page": "stock", "bon": bon, "lignes": lignes}
    return render(request, "lamane/bon_sortie_detail.html", ctx)


# ─── BILANS FINANCIERS ────────────────────────────────────────────────────────

@login_required
def bilans_view(request):
    """Page de bilans financiers : P&L par projet, trésorerie, alertes, impayés."""
    from calendar import monthrange
    today = timezone.now().date()

    # ── P&L par projet (incluant sous-traitants) ────────────────────────────
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

        # Coûts sous-traitants
        st_montant = ContratSousTraitance.objects.filter(projet=p).aggregate(
            s=Coalesce(Sum("montant"), Decimal("0")))["s"]
        st_paye = ContratSousTraitance.objects.filter(projet=p).aggregate(
            s=Coalesce(Sum("montant_paye"), Decimal("0")))["s"]
        total_st_global += st_montant

        # Marge corrigée : Versements − (Achats TTC + Sous-traitance)
        total_depenses = float(achats_agg["ttc"]) + float(st_montant)
        marge = float(versements_sum) - total_depenses
        budget = float(p.cout_estime_lamane or 0)
        alerte_budget = budget > 0 and total_depenses > budget * 0.9

        # ── Retenue de garantie corrigée : sur montant du MARCHÉ (pas sur achats TTC)
        retenue = Decimal("0")
        try:
            marche = p.marche
            retenue = marche.retenue_garantie_montant  # = montant_marche * taux / 100
        except Exception:
            pass

        # Calcul pénalités
        penalites = Decimal("0")
        try:
            marche = p.marche
            penalites = marche.penalites_calculees
        except Exception:
            pass

        # Taux de marge
        taux_marge = round(marge / float(versements_sum) * 100, 1) if float(versements_sum) > 0 else 0

        pl_data.append({
            "projet": p,
            "versements": float(versements_sum),
            "versements_fmt": _fmt(versements_sum),
            "achats_ht": float(achats_agg["ht"]),
            "achats_ttc": float(achats_agg["ttc"]),
            "achats_ht_fmt": _fmt(achats_agg["ht"]),
            "achats_ttc_fmt": _fmt(achats_agg["ttc"]),
            # Sous-traitance
            "st_montant": float(st_montant),
            "st_montant_fmt": _fmt(st_montant),
            "st_paye": float(st_paye),
            "st_paye_fmt": _fmt(st_paye),
            "st_reste": _fmt(float(st_montant) - float(st_paye)),
            # Total dépenses & marge
            "total_depenses": total_depenses,
            "total_depenses_fmt": _fmt(total_depenses),
            "marge": marge,
            "marge_fmt": _fmt(abs(marge)),
            "marge_positive": marge >= 0,
            "taux_marge": taux_marge,
            "budget": budget,
            "budget_fmt": _fmt(budget),
            "alerte_budget": alerte_budget,
            "taux_budget": round(total_depenses / budget * 100, 1) if budget else 0,
            "retenue": _fmt(retenue),
            "penalites": _fmt(penalites),
        })

    # ── Totaux globaux ───────────────────────────────────────────────────────
    total_versements_g = Versement.objects.aggregate(
        s=Coalesce(Sum("montant"), Decimal("0")))["s"]
    total_achats_g = Achat.objects.aggregate(
        ht=Coalesce(Sum("total_ht"), Decimal("0")),
        ttc=Coalesce(Sum("total_ttc"), Decimal("0")),
    )
    total_depenses_g = float(total_achats_g["ttc"]) + float(total_st_global)
    solde_global = float(total_versements_g) - total_depenses_g

    # ── Impayés fournisseurs ─────────────────────────────────────────────────
    impayes = Achat.objects.filter(
        statut_paiement__in=["en_attente", "en_retard"]
    ).select_related("fournisseur", "projet").order_by("echeance_paiement")[:20]
    total_impayes = Achat.objects.filter(
        statut_paiement__in=["en_attente", "en_retard"]
    ).aggregate(s=Coalesce(Sum("total_ttc"), Decimal("0")))["s"]
    nb_en_retard = Achat.objects.filter(statut_paiement="en_retard").count()

    # ── Ventilation des dépenses ─────────────────────────────────────────────
    ventilation = {
        "achats_materiaux": float(total_achats_g["ttc"]),
        "sous_traitance": float(total_st_global),
    }

    # ── Trésorerie mensuelle sur 12 mois ────────────────────────────────────
    monthly_labels, monthly_entrees, monthly_sorties, monthly_solde = [], [], [], []
    cumul = 0.0
    for i in range(11, -1, -1):
        m = ((today.month - i - 1) % 12) + 1
        y = today.year if (today.month - i) > 0 else today.year - 1
        start = today.replace(year=y, month=m, day=1)
        end   = today.replace(year=y, month=m, day=monthrange(y, m)[1])
        entrees = float(Versement.objects.filter(
            date_versement__range=[start, end]).aggregate(
            s=Coalesce(Sum("montant"), Decimal("0")))["s"])
        sorties = float(Achat.objects.filter(
            date_achat__range=[start, end]).aggregate(
            s=Coalesce(Sum("total_ttc"), Decimal("0")))["s"])
        cumul += entrees - sorties
        monthly_labels.append(start.strftime("%b %Y"))
        monthly_entrees.append(entrees)
        monthly_sorties.append(sorties)
        monthly_solde.append(round(cumul, 2))

    # Top 5 projets par dépenses totales (achats + ST)
    top5 = sorted(pl_data, key=lambda x: x["total_depenses"], reverse=True)[:5]
    alertes = [d for d in pl_data if d["alerte_budget"]]

    ctx = {
        "page": "bilans",
        "pl_data": pl_data,
        "total_versements_fmt": _fmt(total_versements_g),
        "total_achats_ht_fmt": _fmt(total_achats_g["ht"]),
        "total_achats_ttc_fmt": _fmt(total_achats_g["ttc"]),
        "total_st_fmt": _fmt(total_st_global),
        "total_depenses_fmt": _fmt(total_depenses_g),
        "solde_global": _fmt(abs(solde_global)),
        "solde_positif": solde_global >= 0,
        "nb_projets": len(pl_data),
        "nb_alertes": len(alertes),
        "alertes": alertes,
        "top5": top5,
        # Impayés fournisseurs
        "impayes": impayes,
        "total_impayes_fmt": _fmt(total_impayes),
        "nb_impayes": impayes.count() if hasattr(impayes, 'count') else len(impayes),
        "nb_en_retard": nb_en_retard,
        # Ventilation dépenses
        "ventilation": ventilation,
        "ventilation_labels_json": json.dumps(["Achats matériaux", "Sous-traitance"]),
        "ventilation_values_json": json.dumps([
            ventilation["achats_materiaux"],
            ventilation["sous_traitance"],
        ]),
        # Graphiques
        "monthly_labels_json": json.dumps(monthly_labels),
        "monthly_entrees_json": json.dumps(monthly_entrees),
        "monthly_sorties_json": json.dumps(monthly_sorties),
        "monthly_solde_json": json.dumps(monthly_solde),
        "top5_labels_json": json.dumps([d["projet"].nom[:20] for d in top5]),
        "top5_values_json": json.dumps([d["total_depenses"] for d in top5]),
    }
    return render(request, "lamane/bilans.html", ctx)


# ─── STOCK TEMPS RÉEL (vue détaillée) ────────────────────────────────────────

@login_required
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
        # Entrées = total quantité dans LigneAchat
        entrees = LigneAchat.objects.filter(materiel=m).aggregate(
            s=Coalesce(Sum("quantite", output_field=DjDecimalField()), Decimal("0")))["s"]
        # Sorties = total quantité dans LigneBonSortie
        sorties = LigneBonSortie.objects.filter(materiel=m).aggregate(
            s=Coalesce(Sum("quantite", output_field=DjDecimalField()), Decimal("0")))["s"]
        stock_actuel = float(entrees) - float(sorties)
        valeur_unitaire_moy = LigneAchat.objects.filter(materiel=m).aggregate(
            avg=Coalesce(Avg("prix_unitaire"), Decimal("0")))["avg"]
        valeur_stock = stock_actuel * float(valeur_unitaire_moy)

        stock_data.append({
            "materiel": m,
            "entrees": float(entrees),
            "sorties": float(sorties),
            "stock_actuel": round(stock_actuel, 2),
            "stock_positif": stock_actuel >= 0,
            "alerte_rupture": stock_actuel <= 0,
            "valeur_stock": _fmt(valeur_stock),
            "prix_moyen": _fmt(valeur_unitaire_moy, 0),
        })

    # KPIs globaux
    total_entrees_valeur = sum(
        float(LigneAchat.objects.filter(materiel=m["materiel"]).aggregate(
            s=Coalesce(Sum(F("quantite") * F("prix_unitaire")), Decimal("0")))["s"])
        for m in stock_data
    )

    ctx = {
        "page": "stock", "stock_data": stock_data,
        "categories": categories, "q": q, "cat_filter": cat,
        "total_references": len(stock_data),
        "nb_ruptures": sum(1 for d in stock_data if d["alerte_rupture"]),
        "nb_alertes": sum(1 for d in stock_data if d["stock_actuel"] < 5 and not d["alerte_rupture"]),
    }
    return render(request, "lamane/stock_detail.html", ctx)


# ═══════════════════════════════════════════════════════════════════════════════
# ─── NOUVELLES VUES — DETAILS + SUPPRESSION + PROFIL ───────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

# ─── VERSEMENT DETAIL ────────────────────────────────────────────────────────

@login_required
def versement_detail_view(request, pk):
    versement = get_object_or_404(Versement, pk=pk)

    # Regenerer le PDF si demande ou si absent
    if request.GET.get("regenerer") == "1" or not versement.facture_pdf:
        try:
            versement.generate_facture_pdf()
            versement.save(update_fields=["facture_pdf"])
            if request.GET.get("regenerer") == "1":
                messages.success(request, "Facture PDF regeneree avec succes.")
                return redirect("ui_versement_detail", pk=pk)
        except Exception as e:
            messages.error(request, f"Erreur lors de la generation du PDF : {e}")

    ctx = {
        "page": "versements",
        "versement": versement,
    }
    return render(request, "lamane/versement_detail.html", ctx)


# ─── EMPLOYE DETAIL + SUPPRESSION ────────────────────────────────────────────

@login_required
def employe_detail_view(request, pk):
    employe = get_object_or_404(Employe, pk=pk)
    affectations = ProjetEmploye.objects.filter(employe=employe).select_related("projet").order_by("-projet__date_debut")
    ctx = {
        "page": "rh",
        "employe": employe,
        "affectations": affectations,
        "nb_projets": affectations.count(),
    }
    return render(request, "lamane/employe_detail.html", ctx)


@login_required
def employe_delete_view(request, pk):
    employe = get_object_or_404(Employe, pk=pk)
    if request.method == "POST":
        employe.delete()
        return _success(request, f"Employé {employe} supprimé.", "ui_rh")
    return render(request, "lamane/forms/confirm_delete.html",
                  {"obj": employe, "titre": str(employe), "page": "rh",
                   "back_url": "/rh/"})


# ─── SOUS-TRAITANT DETAIL + SUPPRESSION + CONTRAT ────────────────────────────

@login_required
def sous_traitant_detail_view(request, pk):
    st = get_object_or_404(SousTraitant, pk=pk)
    contrats = ContratSousTraitance.objects.filter(sous_traitant=st).select_related("projet").order_by("-date_debut")
    total_montant = contrats.aggregate(s=Coalesce(Sum("montant"), Decimal("0")))["s"]
    total_paye    = contrats.aggregate(s=Coalesce(Sum("montant_paye"), Decimal("0")))["s"]
    ctx = {
        "page": "sous_traitants",
        "st": st, "contrats": contrats,
        "total_montant": _fmt(total_montant),
        "total_paye": _fmt(total_paye),
        "reste": _fmt(float(total_montant) - float(total_paye)),
        "taux_paiement": round(float(total_paye) / float(total_montant) * 100 if total_montant > 0 else 0, 1),
    }
    return render(request, "lamane/sous_traitant_detail.html", ctx)


@login_required
def sous_traitant_delete_view(request, pk):
    st = get_object_or_404(SousTraitant, pk=pk)
    if request.method == "POST":
        st.delete()
        return _success(request, f"Sous-traitant « {st.nom} » supprimé.", "ui_sous_traitants")
    return render(request, "lamane/forms/confirm_delete.html",
                  {"obj": st, "titre": st.nom, "page": "sous_traitants",
                   "back_url": "/sous-traitants/"})


@login_required
def contrat_st_create_view(request):
    form = ContratSousTraitanceForm(request.POST or None)
    if form.is_valid():
        c = form.save(commit=False)
        c.save()
        try:
            c.generate_contrat_pdf()
            c.save(update_fields=["contrat_pdf"])
        except Exception:
            pass  # PDF generation optional
        # Écriture comptable automatique
        try:
            generer_ecriture_sous_traitance(c)
        except Exception as e:
            print(f"[COMPTA] Erreur écriture sous-traitance: {e}")
        return _success(request, "Contrat créé — PDF généré.", "ui_sous_traitants")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": "Nouveau contrat de sous-traitance",
                   "action": "Créer", "page": "sous_traitants",
                   "back_url": "/sous-traitants/"})


# ─── FOURNISSEUR DETAIL + SUPPRESSION ────────────────────────────────────────

@login_required
def fournisseur_detail_view(request, pk):
    four = get_object_or_404(Fournisseur, pk=pk)
    achats = Achat.objects.filter(fournisseur=four).select_related("projet").order_by("-date_achat")[:20]
    total_achats = Achat.objects.filter(fournisseur=four).aggregate(
        ht=Coalesce(Sum("total_ht"), Decimal("0")),
        ttc=Coalesce(Sum("total_ttc"), Decimal("0")),
    )
    ctx = {
        "page": "fournisseurs",
        "four": four, "achats": achats,
        "total_ht": _fmt(total_achats["ht"]),
        "total_ttc": _fmt(total_achats["ttc"]),
        "nb_achats": Achat.objects.filter(fournisseur=four).count(),
    }
    return render(request, "lamane/fournisseur_detail.html", ctx)


@login_required
def fournisseur_delete_view(request, pk):
    four = get_object_or_404(Fournisseur, pk=pk)
    if request.method == "POST":
        four.delete()
        return _success(request, "Fournisseur supprimé.", "ui_fournisseurs")
    return render(request, "lamane/forms/confirm_delete.html",
                  {"obj": four, "titre": str(four), "page": "fournisseurs",
                   "back_url": "/fournisseurs/"})


# ─── CLIENT SUPPRESSION ───────────────────────────────────────────────────────

@login_required
def client_delete_view(request, pk):
    client = get_object_or_404(Proprietaire, pk=pk)
    if request.method == "POST":
        client.delete()
        return _success(request, "Client supprimé.", "ui_clients")
    return render(request, "lamane/forms/confirm_delete.html",
                  {"obj": client, "titre": str(client), "page": "clients",
                   "back_url": "/clients/"})


# ─── MATERIAUX LIST + DETAIL ──────────────────────────────────────────────────

@login_required
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
        "page": "stock",
        "stock_data": stock_data,
        "categories": categories,
        "q": q, "cat_filter": cat,
        "total": len(stock_data),
    }
    return render(request, "lamane/materiaux_list.html", ctx)


@login_required
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
        "page": "stock",
        "materiel": materiel,
        "lignes_achat": lignes_achat,
        "lignes_sortie": lignes_sortie,
        "entrees": float(entrees),
        "sorties": float(sorties),
        "stock_actuel": round(stock_actuel, 2),
        "stock_positif": stock_actuel >= 0,
        "alerte_rupture": stock_actuel <= 0,
        "prix_moyen": _fmt(prix_moy, 0),
        "valeur_stock": _fmt(stock_actuel * float(prix_moy), 0),
    }
    return render(request, "lamane/materiel_detail.html", ctx)


# ─── PROFIL UTILISATEUR ───────────────────────────────────────────────────────

@login_required
def profil_view(request):
    user = request.user
    ctx = {
        "page": "profil",
        "user": user,
    }
    return render(request, "lamane/profil.html", ctx)


# ─── CATEGORIES MATERIAUX ────────────────────────────────────────────────────

@login_required
def categories_view(request):
    categories = CategorieMateriel.objects.annotate(
        nb_materiaux=Count("materiaux")
    ).order_by("nom")
    return render(request, "lamane/categories.html",
                  {"page": "categories", "categories": categories})


@login_required
def categorie_create_view(request):
    form = CategorieMaterielForm(request.POST or None)
    if form.is_valid():
        c = form.save()
        return _success(request, f"Categorie \u00ab {c.nom} \u00bb creee.", "ui_categories")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": "Nouvelle categorie",
                   "action": "Creer", "page": "categories",
                   "back_url": "/categories/"})


@login_required
def categorie_edit_view(request, pk):
    c = get_object_or_404(CategorieMateriel, pk=pk)
    form = CategorieMaterielForm(request.POST or None, instance=c)
    if form.is_valid():
        form.save()
        return _success(request, "Categorie modifiee.", "ui_categories")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": f"Modifier \u2014 {c.nom}",
                   "action": "Enregistrer", "page": "categories",
                   "back_url": "/categories/", "obj": c})


@login_required
def categorie_delete_view(request, pk):
    c = get_object_or_404(CategorieMateriel, pk=pk)
    if request.method == "POST":
        nom = c.nom
        c.delete()
        return _success(request, f"Categorie \u00ab {nom} \u00bb supprimee.", "ui_categories")
    return render(request, "lamane/forms/confirm_delete.html",
                  {"obj": c, "titre": c.nom, "page": "categories",
                   "back_url": "/categories/"})


# ─── ETAPES STANDARD ─────────────────────────────────────────────────────────

@login_required
def etapes_standard_view(request):
    etapes = EtapeStandard.objects.all().order_by("ordre")
    ctx = {
        "page": "etapes_standard",
        "etapes": etapes,
        "total_gros": etapes.filter(groupe="gros").count(),
        "total_second": etapes.filter(groupe="second").count(),
    }
    return render(request, "lamane/etapes_standard.html", ctx)


@login_required
def etape_standard_create_view(request):
    form = EtapeStandardForm(request.POST or None)
    if form.is_valid():
        e = form.save()
        return _success(request, f"Etape \u00ab {e.nom} \u00bb creee.", "ui_etapes_standard")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": "Nouvelle etape standard",
                   "action": "Creer", "page": "etapes_standard",
                   "back_url": "/etapes-standard/"})


@login_required
def etape_standard_edit_view(request, pk):
    e = get_object_or_404(EtapeStandard, pk=pk)
    form = EtapeStandardForm(request.POST or None, instance=e)
    if form.is_valid():
        form.save()
        return _success(request, "Etape modifiee.", "ui_etapes_standard")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": f"Modifier \u2014 {e.nom}",
                   "action": "Enregistrer", "page": "etapes_standard",
                   "back_url": "/etapes-standard/", "obj": e})


@login_required
def etape_standard_delete_view(request, pk):
    e = get_object_or_404(EtapeStandard, pk=pk)
    if request.method == "POST":
        nom = e.nom
        e.delete()
        return _success(request, f"Etape \u00ab {nom} \u00bb supprimee.", "ui_etapes_standard")
    return render(request, "lamane/forms/confirm_delete.html",
                  {"obj": e, "titre": e.nom, "page": "etapes_standard",
                   "back_url": "/etapes-standard/"})


# ─── PHASES DE VERSEMENT ─────────────────────────────────────────────────────

@login_required
def phases_versement_view(request):
    projet_id = request.GET.get("projet", "")
    phases = PhaseVersement.objects.select_related("projet", "etape_standard").all()
    if projet_id:
        phases = phases.filter(projet__pk=projet_id)
    phases = phases.order_by("projet__nom", "ordre")

    # Calcul du montant verse par phase
    phases_data = []
    for p in phases:
        montant_verse = Versement.objects.filter(phase=p).aggregate(
            s=Coalesce(Sum("montant"), Decimal("0")))["s"]
        phases_data.append({
            "phase": p,
            "montant_verse": montant_verse,
            "montant_verse_fmt": _fmt(montant_verse),
            "montant_prevu_fmt": _fmt(p.montant_prevu),
            "pct": round(float(montant_verse) / float(p.montant_prevu) * 100, 1) if p.montant_prevu > 0 else 0,
        })

    projets = Projet.objects.all().order_by("nom")
    ctx = {
        "page": "phases_versement",
        "phases_data": phases_data,
        "projets": projets,
        "projet_filter": projet_id,
        "total_phases": phases.count(),
    }
    return render(request, "lamane/phases_versement.html", ctx)


@login_required
def phase_versement_create_view(request):
    form = PhaseVersementForm(request.POST or None)
    if form.is_valid():
        p = form.save()
        return _success(request, f"Phase \u00ab {p} \u00bb creee.", "ui_phases_versement")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": "Nouvelle phase de versement",
                   "action": "Creer", "page": "phases_versement",
                   "back_url": "/phases-versement/"})


@login_required
def phase_versement_edit_view(request, pk):
    p = get_object_or_404(PhaseVersement, pk=pk)
    form = PhaseVersementForm(request.POST or None, instance=p)
    if form.is_valid():
        form.save()
        return _success(request, "Phase modifiee.", "ui_phases_versement")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": f"Modifier \u2014 {p}",
                   "action": "Enregistrer", "page": "phases_versement",
                   "back_url": "/phases-versement/", "obj": p})


@login_required
def phase_versement_delete_view(request, pk):
    p = get_object_or_404(PhaseVersement, pk=pk)
    if request.method == "POST":
        nom = str(p)
        p.delete()
        return _success(request, f"Phase \u00ab {nom} \u00bb supprimee.", "ui_phases_versement")
    return render(request, "lamane/forms/confirm_delete.html",
                  {"obj": p, "titre": str(p), "page": "phases_versement",
                   "back_url": "/phases-versement/"})


# ═══════════════════════════════════════════════════════════════════════════
#  MODULE COMPTABILITÉ
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def comptabilite_journal_view(request):
    """Journal comptable — liste des écritures."""
    journal_filter = request.GET.get("journal", "")
    qs = EcritureComptable.objects.select_related("projet").prefetch_related("lignes__compte")

    if journal_filter:
        qs = qs.filter(journal=journal_filter)

    ecritures = qs[:200]
    totaux = qs.aggregate(
        total_debit=Coalesce(Sum("lignes__debit"), Decimal("0")),
        total_credit=Coalesce(Sum("lignes__credit"), Decimal("0")),
    )
    ctx = {
        "page": "comptabilite",
        "ecritures": ecritures,
        "journal_filter": journal_filter,
        "journals": EcritureComptable.JOURNAL_CHOICES,
        "total_ecritures": qs.count(),
        "total_debit": _fmt(totaux["total_debit"]),
        "total_credit": _fmt(totaux["total_credit"]),
    }
    return render(request, "lamane/comptabilite_journal.html", ctx)


@login_required
def comptabilite_grand_livre_view(request):
    """Grand livre — mouvements par compte."""
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
        "page": "comptabilite",
        "comptes": comptes,
        "lignes": lignes,
        "compte_selectionne": compte_selectionne,
        "compte_id": compte_id,
    }
    return render(request, "lamane/comptabilite_grand_livre.html", ctx)


@login_required
def comptabilite_balance_view(request):
    """Balance des comptes — synthèse débit/crédit par compte."""
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
                "debit": _fmt(c.total_debit),
                "credit": _fmt(c.total_credit),
                "solde_debiteur": _fmt(solde) if solde > 0 else "",
                "solde_crediteur": _fmt(abs(solde)) if solde < 0 else "",
                "solde_raw": solde,
            })

    total_d = sum(c.total_debit for c in comptes)
    total_c = sum(c.total_credit for c in comptes)

    ctx = {
        "page": "comptabilite",
        "balance_data": balance_data,
        "total_debit": _fmt(total_d),
        "total_credit": _fmt(total_c),
    }
    return render(request, "lamane/comptabilite_balance.html", ctx)


@login_required
def comptabilite_plan_view(request):
    """Plan comptable SYSCOHADA — vue de tous les comptes."""
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
def ecriture_create_view(request):
    """Créer une écriture comptable manuelle."""
    form = EcritureComptableForm(request.POST or None)
    formset = LigneEcritureFormSet(request.POST or None, prefix="lignes")
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        ecriture = form.save()
        formset.instance = ecriture
        formset.save()
        return _success(request,
                        f"Écriture {ecriture.numero_piece} créée.",
                        "ui_comptabilite_journal")
    return render(request, "lamane/forms/ecriture_form.html",
                  {"form": form, "formset": formset,
                   "title": "Nouvelle écriture comptable",
                   "action": "Enregistrer", "page": "comptabilite",
                   "back_url": "/comptabilite/journal/"})


@login_required
def ecriture_detail_view(request, pk):
    """Détail d'une écriture comptable."""
    ecriture = get_object_or_404(
        EcritureComptable.objects.prefetch_related("lignes__compte"),
        pk=pk
    )
    ctx = {
        "page": "comptabilite",
        "ecriture": ecriture,
        "lignes": ecriture.lignes.all(),
    }
    return render(request, "lamane/ecriture_detail.html", ctx)


# ═══════════════════════════════════════════════════════════════════════════
#  MODULE TRÉSORERIE / COMPTES BANCAIRES
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def tresorerie_view(request):
    """Dashboard trésorerie — vue d'ensemble des comptes."""
    comptes = CompteBancaire.objects.filter(actif=True)
    comptes_data = []
    solde_total = Decimal("0")
    for c in comptes:
        solde = c.solde_actuel
        solde_total += solde
        nb_tx = c.transactions.count()
        comptes_data.append({
            "compte": c,
            "solde": _fmt(solde),
            "solde_raw": solde,
            "nb_transactions": nb_tx,
        })

    # Dernières transactions
    dernieres_tx = TransactionBancaire.objects.select_related(
        "compte", "projet"
    ).order_by("-date_transaction")[:20]

    ctx = {
        "page": "tresorerie",
        "comptes_data": comptes_data,
        "solde_total": _fmt(solde_total),
        "solde_total_raw": solde_total,
        "dernieres_tx": dernieres_tx,
        "total_comptes": comptes.count(),
    }
    return render(request, "lamane/tresorerie.html", ctx)


@login_required
def compte_bancaire_create_view(request):
    form = CompteBancaireForm(request.POST or None)
    if form.is_valid():
        c = form.save()
        return _success(request, f"Compte « {c.nom} » créé.", "ui_tresorerie")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": "Nouveau compte bancaire",
                   "action": "Créer", "page": "tresorerie",
                   "back_url": "/tresorerie/"})


@login_required
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
def compte_bancaire_detail_view(request, pk):
    """Détail d'un compte bancaire avec ses transactions."""
    compte = get_object_or_404(CompteBancaire, pk=pk)
    transactions = compte.transactions.select_related("projet").order_by("-date_transaction")
    ctx = {
        "page": "tresorerie",
        "compte": compte,
        "transactions": transactions,
        "solde": _fmt(compte.solde_actuel),
    }
    return render(request, "lamane/compte_bancaire_detail.html", ctx)


@login_required
def transaction_create_view(request):
    form = TransactionBancaireForm(request.POST or None)
    if form.is_valid():
        tx = form.save()
        return _success(request,
                        f"Transaction enregistrée — {tx.montant} XOF",
                        "ui_tresorerie")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": "Nouvelle transaction",
                   "action": "Enregistrer", "page": "tresorerie",
                   "back_url": "/tresorerie/"})


# ═══════════════════════════════════════════════════════════════════════════
#  MODULE DOCUMENTS BTP
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def documents_btp_view(request):
    """Liste des documents BTP."""
    type_filter = request.GET.get("type", "")
    projet_filter = request.GET.get("projet", "")
    qs = DocumentProjet.objects.select_related("projet", "auteur")

    if type_filter:
        qs = qs.filter(type_document=type_filter)
    if projet_filter:
        qs = qs.filter(projet_id=projet_filter)

    projets = Projet.objects.all()
    ctx = {
        "page": "documents_btp",
        "documents": qs[:100],
        "total_documents": qs.count(),
        "type_filter": type_filter,
        "projet_filter": projet_filter,
        "types": DocumentProjet.TYPE_CHOICES,
        "projets": projets,
    }
    return render(request, "lamane/documents_btp.html", ctx)


@login_required
def document_btp_create_view(request):
    form = DocumentProjetForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        doc = form.save(commit=False)
        doc.auteur = request.user
        doc.save()
        return _success(request, f"Document « {doc.titre} » ajouté.", "ui_documents_btp")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": "Nouveau document BTP",
                   "action": "Ajouter", "page": "documents_btp",
                   "back_url": "/documents-btp/"})


@login_required
def document_btp_detail_view(request, pk):
    doc = get_object_or_404(DocumentProjet.objects.select_related("projet", "auteur"), pk=pk)
    ctx = {"page": "documents_btp", "doc": doc}
    return render(request, "lamane/document_btp_detail.html", ctx)


@login_required
def document_btp_delete_view(request, pk):
    doc = get_object_or_404(DocumentProjet, pk=pk)
    if request.method == "POST":
        doc.delete()
        return _success(request, "Document supprimé.", "ui_documents_btp")
    return render(request, "lamane/forms/confirm_delete.html",
                  {"obj": doc, "titre": doc.titre, "page": "documents_btp",
                   "back_url": "/documents-btp/"})


# ── Bordereaux de prix ────────────────────────────────────────────────────

@login_required
def bordereaux_view(request):
    """Liste des bordereaux de prix."""
    qs = BordereauPrix.objects.select_related("projet").prefetch_related("lignes")
    ctx = {
        "page": "documents_btp",
        "bordereaux": qs,
        "total_bordereaux": qs.count(),
    }
    return render(request, "lamane/bordereaux.html", ctx)


@login_required
def bordereau_create_view(request):
    form = BordereauPrixForm(request.POST or None)
    formset = LigneBordereauFormSet(request.POST or None, prefix="lignes")
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        bdp = form.save()
        formset.instance = bdp
        formset.save()
        return _success(request, f"Bordereau {bdp.numero} créé.", "ui_bordereaux")
    return render(request, "lamane/forms/bordereau_form.html",
                  {"form": form, "formset": formset,
                   "title": "Nouveau bordereau de prix",
                   "action": "Créer", "page": "documents_btp",
                   "back_url": "/documents-btp/bordereaux/"})


@login_required
def bordereau_detail_view(request, pk):
    bdp = get_object_or_404(
        BordereauPrix.objects.select_related("projet").prefetch_related("lignes"),
        pk=pk
    )
    ctx = {
        "page": "documents_btp",
        "bordereau": bdp,
        "lignes": bdp.lignes.all(),
        "total_ht": _fmt(bdp.total_ht),
    }
    return render(request, "lamane/bordereau_detail.html", ctx)


# ── Décompte Général Définitif ────────────────────────────────────────────

@login_required
def dgd_list_view(request):
    """Liste des DGD."""
    qs = DecompteGD.objects.select_related("projet", "marche")
    ctx = {
        "page": "documents_btp",
        "dgds": qs,
        "total_dgds": qs.count(),
    }
    return render(request, "lamane/dgd_list.html", ctx)


@login_required
def dgd_create_view(request):
    form = DecompteGDForm(request.POST or None)
    if form.is_valid():
        dgd = form.save()
        return _success(request, f"DGD créé pour {dgd.projet.nom}.", "ui_dgd_list")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form, "title": "Nouveau Décompte Général Définitif",
                   "action": "Créer", "page": "documents_btp",
                   "back_url": "/documents-btp/dgd/"})


@login_required
def dgd_detail_view(request, pk):
    dgd = get_object_or_404(DecompteGD.objects.select_related("projet", "marche"), pk=pk)
    ctx = {
        "page": "documents_btp",
        "dgd": dgd,
    }
    return render(request, "lamane/dgd_detail.html", ctx)


# ═══════════════════════════════════════════════════════════════════════════
#  GESTION UTILISATEURS / PROFILS
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def utilisateurs_view(request):
    """Liste des utilisateurs avec leurs profils et rôles."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    users = User.objects.all().select_related("profil" if hasattr(User, "profil") else None)
    users_data = []
    for u in users:
        try:
            profil = u.profil
        except ProfilUtilisateur.DoesNotExist:
            profil = None
        users_data.append({
            "user": u,
            "profil": profil,
            "role_display": profil.get_role_display() if profil else "—",
            "role": profil.role if profil else "",
        })
    ctx = {
        "page": "utilisateurs",
        "users_data": users_data,
        "total_users": len(users_data),
        "roles": ProfilUtilisateur.ROLE_CHOICES,
    }
    return render(request, "lamane/utilisateurs.html", ctx)


@login_required
def profil_edit_view(request, pk):
    """Modifier le profil/rôle d'un utilisateur."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user_obj = get_object_or_404(User, pk=pk)
    profil, _ = ProfilUtilisateur.objects.get_or_create(user=user_obj)
    form = ProfilUtilisateurForm(request.POST or None, request.FILES or None, instance=profil)
    if form.is_valid():
        form.save()
        return _success(request, f"Profil de {user_obj.username} mis à jour.", "ui_utilisateurs")
    return render(request, "lamane/forms/generic_form.html",
                  {"form": form,
                   "title": f"Profil — {user_obj.get_full_name() or user_obj.username}",
                   "action": "Enregistrer", "page": "utilisateurs",
                   "back_url": "/utilisateurs/"})

