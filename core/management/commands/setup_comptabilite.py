# core/management/commands/setup_comptabilite.py
"""
Commande pour initialiser le plan comptable SYSCOHADA BTP
et les rôles utilisateur par défaut.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from core.models import CompteComptable


PLAN_COMPTABLE = [
    # Classe 1 - Ressources durables
    ("101000", "Capital social", "passif", 1),
    ("106000", "Réserves", "passif", 1),
    ("162000", "Emprunts bancaires", "passif", 1),

    # Classe 2 - Actif immobilisé
    ("213000", "Constructions", "actif", 2),
    ("215000", "Matériel et outillage", "actif", 2),
    ("218000", "Matériel de transport", "actif", 2),
    ("244000", "Matériel et mobilier de bureau", "actif", 2),
    ("281300", "Amort. constructions", "actif", 2),
    ("281500", "Amort. matériel et outillage", "actif", 2),

    # Classe 3 - Stocks
    ("311000", "Matières premières", "actif", 3),
    ("321000", "Matières consommables", "actif", 3),
    ("371000", "Stocks de marchandises", "actif", 3),

    # Classe 4 - Tiers
    ("401000", "Fournisseurs", "passif", 4),
    ("408000", "Fournisseurs — factures non parvenues", "passif", 4),
    ("411000", "Clients", "actif", 4),
    ("418000", "Clients — produits non encore facturés", "actif", 4),
    ("421000", "Personnel — rémunérations dues", "passif", 4),
    ("431000", "Sécurité sociale (IPRES, CSS)", "passif", 4),
    ("441000", "État — impôts sur les bénéfices", "passif", 4),
    ("443000", "État — TVA facturée", "passif", 4),
    ("445000", "État — TVA récupérable / déductible", "actif", 4),
    ("447000", "État — impôts retenus à la source", "passif", 4),
    ("449000", "État — charges à payer / produits à recevoir", "passif", 4),
    ("471000", "Débiteurs divers", "actif", 4),
    ("472000", "Créditeurs divers", "passif", 4),
    ("481000", "Fournisseurs d'investissements", "passif", 4),

    # Classe 5 - Trésorerie
    ("521000", "Banque", "actif", 5),
    ("522000", "Banque (compte 2)", "actif", 5),
    ("531000", "Chèques à encaisser", "actif", 5),
    ("571000", "Caisse", "actif", 5),
    ("585000", "Virements de fonds internes", "actif", 5),

    # Classe 6 - Charges
    ("601000", "Achats de matières premières", "charge", 6),
    ("602000", "Achats de matières consommables", "charge", 6),
    ("604000", "Achats de matériels et fournitures stockés", "charge", 6),
    ("605000", "Autres achats", "charge", 6),
    ("611000", "Sous-traitance générale", "charge", 6),
    ("612000", "Redevances de crédit-bail", "charge", 6),
    ("613000", "Locations et charges locatives", "charge", 6),
    ("614000", "Charges d'entretien et réparations", "charge", 6),
    ("616000", "Assurances", "charge", 6),
    ("618000", "Autres charges externes", "charge", 6),
    ("621000", "Personnel intérimaire", "charge", 6),
    ("622000", "Rémunérations intermédiaires et honoraires", "charge", 6),
    ("624000", "Transports de biens", "charge", 6),
    ("625000", "Déplacements, missions et réceptions", "charge", 6),
    ("626000", "Frais postaux et de télécommunications", "charge", 6),
    ("627000", "Services bancaires", "charge", 6),
    ("631000", "Frais de personnel — rémunérations", "charge", 6),
    ("632000", "Charges sociales", "charge", 6),
    ("641000", "Impôts et taxes (hors impôt sur bénéfice)", "charge", 6),
    ("651000", "Pertes sur créances clients", "charge", 6),
    ("681000", "Dotations aux amortissements d'exploitation", "charge", 6),

    # Classe 7 - Produits
    ("706000", "Services vendus — travaux BTP", "produit", 7),
    ("707000", "Ventes de marchandises", "produit", 7),
    ("708000", "Produits des activités annexes", "produit", 7),
    ("711000", "Production stockée", "produit", 7),
    ("721000", "Production immobilisée", "produit", 7),
    ("758000", "Produits divers", "produit", 7),
    ("771000", "Intérêts de prêts et placements", "produit", 7),
    ("781000", "Reprises d'amortissements", "produit", 7),
]


ROLES = {
    "Direction": [
        "view_*", "add_*", "change_*", "delete_*",
    ],
    "Comptable": [
        "view_comptecomptable", "view_ecriturecomptable", "add_ecriturecomptable",
        "change_ecriturecomptable", "view_ligneEcriture",
        "view_comptebancaire", "view_transactionbancaire", "add_transactionbancaire",
        "view_achat", "view_versement", "view_projet",
    ],
    "Chef de chantier": [
        "view_projet", "view_avancementchantier", "add_avancementchantier",
        "change_avancementchantier", "view_materiel", "view_bonsortie",
        "add_bonsortie", "view_documentprojet", "add_documentprojet",
    ],
    "Gestionnaire de stock": [
        "view_materiel", "add_materiel", "change_materiel",
        "view_achat", "add_achat", "view_bonsortie", "add_bonsortie",
        "view_categoriemateriel", "add_categoriemateriel",
    ],
}


class Command(BaseCommand):
    help = "Initialise le plan comptable SYSCOHADA BTP et les rôles utilisateur"

    def handle(self, *args, **options):
        # ── Plan comptable ──────────────────────────────────────────────
        created = 0
        for code, libelle, type_c, classe in PLAN_COMPTABLE:
            _, is_new = CompteComptable.objects.get_or_create(
                code=code,
                defaults={
                    "libelle": libelle,
                    "type_compte": type_c,
                    "classe": classe,
                }
            )
            if is_new:
                created += 1
        self.stdout.write(self.style.SUCCESS(
            f"Plan comptable : {created} comptes créés "
            f"({CompteComptable.objects.count()} total)"
        ))

        # ── Rôles (groupes Django) ──────────────────────────────────────
        for role_name, _ in ROLES.items():
            group, _ = Group.objects.get_or_create(name=role_name)
            # On peut affiner les permissions plus tard
            self.stdout.write(f"  Groupe « {role_name} » OK")

        self.stdout.write(self.style.SUCCESS("Setup comptabilité terminé !"))
