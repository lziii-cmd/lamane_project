# core/views/documents.py
"""Vues documents BTP, bordereaux, DGD — LAMANE BTP."""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from core.models import (
    Projet, DocumentProjet, BordereauPrix, LigneBordereau, DecompteGD,
)
from core.forms import (
    DocumentProjetForm, BordereauPrixForm, LigneBordereauFormSet, DecompteGDForm,
)
from core.permissions import role_required
from core.views._helpers import _fmt, _success

__all__ = [
    "documents_btp_view", "document_btp_create_view",
    "document_btp_detail_view", "document_btp_delete_view",
    "bordereaux_view", "bordereau_create_view", "bordereau_detail_view",
    "dgd_list_view", "dgd_create_view", "dgd_detail_view",
]


@login_required
@role_required("chef_chantier", "comptable")
def documents_btp_view(request):
    type_filter = request.GET.get("type", "")
    projet_filter = request.GET.get("projet", "")
    qs = DocumentProjet.objects.select_related("projet", "auteur")
    if type_filter:
        qs = qs.filter(type_document=type_filter)
    if projet_filter:
        qs = qs.filter(projet_id=projet_filter)

    from core.pagination import paginate_queryset
    page_obj = paginate_queryset(request, qs, per_page=25)
    projets = Projet.objects.all()
    ctx = {
        "page": "documents_btp",
        "documents": page_obj, "page_obj": page_obj,
        "total_documents": qs.count(),
        "type_filter": type_filter, "projet_filter": projet_filter,
        "types": DocumentProjet.TYPE_CHOICES, "projets": projets,
    }
    return render(request, "lamane/documents_btp.html", ctx)


@login_required
@role_required("chef_chantier", "comptable")
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
@role_required("chef_chantier", "comptable")
def document_btp_detail_view(request, pk):
    doc = get_object_or_404(DocumentProjet.objects.select_related("projet", "auteur"), pk=pk)
    ctx = {"page": "documents_btp", "doc": doc}
    return render(request, "lamane/document_btp_detail.html", ctx)


@login_required
@role_required("chef_chantier")
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
@role_required("chef_chantier", "comptable")
def bordereaux_view(request):
    qs = BordereauPrix.objects.select_related("projet").prefetch_related("lignes")
    ctx = {
        "page": "documents_btp", "bordereaux": qs,
        "total_bordereaux": qs.count(),
    }
    return render(request, "lamane/bordereaux.html", ctx)


@login_required
@role_required("chef_chantier", "comptable")
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
@role_required("chef_chantier", "comptable")
def bordereau_detail_view(request, pk):
    bdp = get_object_or_404(
        BordereauPrix.objects.select_related("projet").prefetch_related("lignes"), pk=pk
    )
    ctx = {
        "page": "documents_btp", "bordereau": bdp,
        "lignes": bdp.lignes.all(), "total_ht": _fmt(bdp.total_ht),
    }
    return render(request, "lamane/bordereau_detail.html", ctx)


# ── Décompte Général Définitif ────────────────────────────────────────────

@login_required
@role_required("chef_chantier", "comptable")
def dgd_list_view(request):
    qs = DecompteGD.objects.select_related("projet", "marche")
    ctx = {"page": "documents_btp", "dgds": qs, "total_dgds": qs.count()}
    return render(request, "lamane/dgd_list.html", ctx)


@login_required
@role_required("chef_chantier", "comptable")
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
@role_required("chef_chantier", "comptable")
def dgd_detail_view(request, pk):
    dgd = get_object_or_404(DecompteGD.objects.select_related("projet", "marche"), pk=pk)
    ctx = {"page": "documents_btp", "dgd": dgd}
    return render(request, "lamane/dgd_detail.html", ctx)
