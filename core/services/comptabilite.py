# core/services/comptabilite.py
"""
Service de génération automatique des écritures comptables.
Norme SYSCOHADA — comptes BTP Sénégal / UEMOA.
"""
from decimal import Decimal
from django.db import transaction

from core.models import (
    CompteComptable,
    EcritureComptable,
    LigneEcriture,
)


def _get_or_none(code):
    """Retourne le CompteComptable par code ou None."""
    try:
        return CompteComptable.objects.get(code=code)
    except CompteComptable.DoesNotExist:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# ACHAT  →  Écriture comptable automatique
# ═══════════════════════════════════════════════════════════════════════════

@transaction.atomic
def generer_ecriture_achat(achat):
    """
    Génère une écriture comptable pour un achat.
    Débit  : 601000 Achats matières premières (HT)
             445000 TVA déductible (si TVA active)
    Crédit : 401000 Fournisseurs (TTC)
    """
    # Éviter les doublons
    if achat.ecritures_comptables.exists():
        return achat.ecritures_comptables.first()

    compte_achat = _get_or_none("601000")
    compte_tva = _get_or_none("445000")
    compte_fournisseur = _get_or_none("401000")

    if not compte_achat or not compte_fournisseur:
        return None  # Plan comptable pas encore initialisé

    fournisseur_nom = ""
    if achat.fournisseur:
        fournisseur_nom = (achat.fournisseur.entreprise
                          if achat.fournisseur.est_moral
                          else f"{achat.fournisseur.prenom} {achat.fournisseur.nom}").strip()

    ecriture = EcritureComptable.objects.create(
        date_ecriture=achat.date_achat,
        libelle=f"Achat matériaux — {fournisseur_nom or 'Fournisseur'} — {achat.projet.nom}",
        journal="AC",
        projet=achat.projet,
        achat=achat,
    )

    # Débit achats HT
    LigneEcriture.objects.create(
        ecriture=ecriture,
        compte=compte_achat,
        libelle=f"Achat HT — {achat.numero_facture or achat.pk}",
        debit=achat.total_ht,
        credit=0,
    )

    # Débit TVA si active
    if achat.tva_active and achat.total_tva > 0 and compte_tva:
        LigneEcriture.objects.create(
            ecriture=ecriture,
            compte=compte_tva,
            libelle=f"TVA déductible — {achat.numero_facture or achat.pk}",
            debit=achat.total_tva,
            credit=0,
        )

    # Crédit fournisseur TTC
    LigneEcriture.objects.create(
        ecriture=ecriture,
        compte=compte_fournisseur,
        libelle=f"Fournisseur — {fournisseur_nom}",
        debit=0,
        credit=achat.total_ttc,
    )

    return ecriture


# ═══════════════════════════════════════════════════════════════════════════
# VERSEMENT  →  Écriture comptable automatique
# ═══════════════════════════════════════════════════════════════════════════

@transaction.atomic
def generer_ecriture_versement(versement):
    """
    Génère une écriture comptable pour un versement reçu du client.
    Débit  : 521000 Banque (ou 571000 Caisse)
    Crédit : 411000 Clients
    """
    if versement.ecritures_comptables.exists():
        return versement.ecritures_comptables.first()

    # Choisir le compte de trésorerie en fonction du type de versement
    type_v = versement.type_versement
    if type_v in ("espèces",):
        compte_tresorerie = _get_or_none("571000")  # Caisse
    elif type_v in ("wave", "virement om"):
        compte_tresorerie = _get_or_none("521000") or _get_or_none("571000")  # Mobile / Banque
    else:
        compte_tresorerie = _get_or_none("521000")  # Banque

    compte_client = _get_or_none("411000")

    if not compte_tresorerie or not compte_client:
        return None

    ecriture = EcritureComptable.objects.create(
        date_ecriture=versement.date_versement,
        libelle=f"Versement client — {versement.projet.nom} — {versement.libelle}",
        journal="VT",
        projet=versement.projet,
        versement=versement,
    )

    # Débit trésorerie
    LigneEcriture.objects.create(
        ecriture=ecriture,
        compte=compte_tresorerie,
        libelle=f"Encaissement — {versement.numero_facture}",
        debit=versement.montant,
        credit=0,
    )

    # Crédit client
    LigneEcriture.objects.create(
        ecriture=ecriture,
        compte=compte_client,
        libelle=f"Client — {versement.projet.nom}",
        debit=0,
        credit=versement.montant,
    )

    return ecriture


# ═══════════════════════════════════════════════════════════════════════════
# CONTRAT SOUS-TRAITANCE  →  Écriture comptable
# ═══════════════════════════════════════════════════════════════════════════

@transaction.atomic
def generer_ecriture_sous_traitance(contrat):
    """
    Écriture pour un paiement de sous-traitant.
    Débit  : 611000 Sous-traitance générale
    Crédit : 401000 Fournisseurs
    """
    if contrat.ecritures_comptables.exists():
        return contrat.ecritures_comptables.first()

    compte_st = _get_or_none("611000")
    compte_fournisseur = _get_or_none("401000")

    if not compte_st or not compte_fournisseur:
        return None

    ecriture = EcritureComptable.objects.create(
        date_ecriture=contrat.date_debut,
        libelle=f"Sous-traitance — {contrat.sous_traitant.nom} — {contrat.projet.nom}",
        journal="AC",
        projet=contrat.projet,
        contrat_st=contrat,
    )

    LigneEcriture.objects.create(
        ecriture=ecriture,
        compte=compte_st,
        libelle=f"Sous-traitance — {contrat.lot or contrat.sous_traitant.nom}",
        debit=contrat.montant,
        credit=0,
    )

    LigneEcriture.objects.create(
        ecriture=ecriture,
        compte=compte_fournisseur,
        libelle=f"Fournisseur ST — {contrat.sous_traitant.nom}",
        debit=0,
        credit=contrat.montant,
    )

    return ecriture
