"""
Ce fichier centralise tous les modèles du module core.
Chaque modèle est défini dans un fichier distinct dans /models/
et importé ici pour faciliter l'accès depuis le reste du projet.
"""

from .base import BaseModel
from .type_projet import TypeProjet
from .personne import Personne
from .proprietaire import Proprietaire
from .employe import Employe
from .projet import Projet
from .projet_employe import ProjetEmploye
from .caracteristique import Caracteristique
from .categorie_materiel import CategorieMateriel
from .materiel import Materiel
from .fournisseur import Fournisseur
from .achat import Achat
from .ligne_achat import LigneAchat
from .etape_standard import EtapeStandard
from .phase_versement import PhaseVersement
from .versement import Versement

# ── Nouveaux modèles expert BTP / Finance / Comptabilité ──────────────────
from .marche_travaux import MarcheTravaux
from .avancement_chantier import AvancementChantier
from .sous_traitant import SousTraitant, ContratSousTraitance
from .situation_mensuelle import SituationMensuelle
from .bon_sortie import BonSortie, LigneBonSortie

# ── Comptabilité & Finance ────────────────────────────────────────────────
from .compte_comptable import CompteComptable, EcritureComptable, LigneEcriture
from .compte_bancaire import CompteBancaire, TransactionBancaire

# ── Documents BTP ─────────────────────────────────────────────────────────
from .document_btp import DocumentProjet, BordereauPrix, LigneBordereau, DecompteGD

# ── Gestion utilisateurs ─────────────────────────────────────────────────
from .profil_utilisateur import ProfilUtilisateur
