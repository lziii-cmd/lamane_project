from .caracteristique_admin import *
from .proprietaire_admin import *
from .type_projet_admin import *
from .projet_admin import *
from .etape_projet_admin import *
from .employe_admin import *
from .projet_employe_admin import *
from .categorie_materiel_admin import *
from .materiel_admin import *
from .fournisseur_admin import *
from .achat_admin import *
from .ligne_achat_inline import *
from .versement_admin import *
from .phase_versement_admin import *
from .fournisseur_admin import *


# core/admin/__init__.py
from .proprietaire_admin import ProprietaireAdmin
from .projet_admin import ProjetAdmin
from .type_projet_admin import TypeProjetAdmin
from .employe_admin import EmployeAdmin
from .projet_employe_admin import ProjetEmployeAdmin
from .achat_admin import AchatAdmin
from .materiel_admin import MaterielAdmin
from .categorie_materiel_admin import CategorieMaterielAdmin
from .versement_admin import VersementAdmin
from .etape_standard_admin import EtapeStandardAdmin
from .fournisseur_admin import FournisseurAdmin
from .phase_versement_admin import PhaseVersementAdmin
from .vitrine_admin import ConfigVitrineAdmin, ServiceVitrineAdmin, ProjetVitrineAdmin, TemoignageVitrineAdmin
from .metre_admin import LotMetreAdmin, TypeElementAdmin, PlanMetreAdmin, TraceMetreAdmin
