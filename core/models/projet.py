# core/models/projet.py
import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal


class Projet(models.Model):
    STATUT_CHOICES = [
        ("En attente", "En attente"),
        ("En cours", "En cours"),
        ("En pause", "En pause"),
        ("Terminé", "Terminé"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identifiant unique global (UUID4)",
    )
    nom = models.CharField("Nom du projet", max_length=200)
    localisation = models.CharField("Localisation", max_length=200)
    statut = models.CharField("Statut", max_length=100, choices=STATUT_CHOICES)
    date_debut = models.DateField("Date de début")
    date_fin = models.DateField("Date de fin", null=True, blank=True)
    description = models.TextField("Description", blank=True)

    superficie = models.PositiveIntegerField("Superficie du terrain (m²)", null=True, blank=True)
    surface_batie = models.PositiveIntegerField("Surface bâtie (m²)", null=True, blank=True)
    nombre_pieces = models.PositiveIntegerField("Nombre de pièces", null=True, blank=True)
    nombre_etages = models.PositiveIntegerField("Nombre d'étages", null=True, blank=True)

    cout_estime_lamane = models.DecimalField(
        "Coût estimé Lamane (XOF)",
        max_digits=14, decimal_places=2,
        default=Decimal("0.00"),
        help_text="Estimation interne du coût de réalisation du projet.",
    )

    a_piscine = models.BooleanField("Piscine", default=False)
    volume_piscine = models.PositiveIntegerField("Volume de la piscine (m³)", null=True, blank=True)

    a_ascenseur = models.BooleanField("Ascenseur", default=False)
    nombre_ascenseurs = models.PositiveIntegerField("Nombre d'ascenseurs", null=True, blank=True)

    a_climatisation = models.BooleanField("Climatisation", default=False)
    nombre_clims = models.PositiveIntegerField("Nombre de climatiseurs", null=True, blank=True)

    a_panneaux_solaires = models.BooleanField("Panneaux solaires", default=False)
    puissance_panneaux = models.PositiveIntegerField("Puissance panneaux (kWc)", null=True, blank=True)

    type_projet = models.ForeignKey(
        "core.TypeProjet",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Type de projet",
    )
    proprietaire = models.ForeignKey(
        "core.Proprietaire",
        on_delete=models.PROTECT,
        verbose_name="Propriétaire",
    )

    date_creation = models.DateTimeField(auto_now_add=True, help_text="Date de création de l'objet")
    date_modification = models.DateTimeField(auto_now=True, help_text="Date de dernière modification")

    class Meta:
        verbose_name = "Projet"
        verbose_name_plural = "Projets"

    def __str__(self):
        return self.nom

    def clean(self):
        """Validation métier du projet."""
        super().clean()

        # Règle 1 : cohérence des dates
        if self.date_fin and self.date_debut and self.date_fin < self.date_debut:
            raise ValidationError({
                "date_fin": "La date de fin ne peut pas être antérieure à la date de début."
            })

        # Règle 2 : statut Terminé → forcer date_fin si absente
        if self.statut == "Terminé" and not self.date_fin:
            self.date_fin = timezone.now().date()

        # Règle 3 : vérifier cohérence avec le marché de travaux (si existant)
        try:
            marche = self.marche
            if marche and marche.montant_marche and self.cout_estime_lamane:
                if marche.montant_marche < self.cout_estime_lamane:
                    raise ValidationError({
                        "cout_estime_lamane": (
                            "Le coût estimé Lamane ne peut pas dépasser le montant du marché "
                            f"({marche.montant_marche:,.0f} FCFA)."
                        )
                    })
        except Exception:
            pass  # Le marché n'existe pas encore : aucune contrainte

    @property
    def total_achats_ht(self):
        """Total HT des achats matériaux sur ce projet."""
        from django.db.models import Sum
        return self.achats.aggregate(s=Sum("total_ht"))["s"] or Decimal("0.00")

    @property
    def total_versements(self):
        """Total des versements clients sur ce projet."""
        from django.db.models import Sum
        return self.versements.aggregate(s=Sum("montant"))["s"] or Decimal("0.00")

    @property
    def total_achats_ttc(self):
        """Total TTC des achats matériaux sur ce projet."""
        from django.db.models import Sum
        return self.achats.aggregate(s=Sum("total_ttc"))["s"] or Decimal("0.00")

    @property
    def total_sous_traitance(self):
        """Total des contrats de sous-traitance sur ce projet."""
        from django.db.models import Sum
        return (
            self.contrats_sous_traitance.aggregate(s=Sum("montant"))["s"]
            or Decimal("0.00")
        )

    @property
    def total_depenses(self):
        """Total des dépenses = Achats TTC + Sous-traitance."""
        return self.total_achats_ttc + self.total_sous_traitance

    @property
    def marge_brute_estimee(self):
        """Marge brute = Versements clients − (Achats TTC + Sous-traitance)."""
        return self.total_versements - self.total_depenses

    @property
    def taux_marge(self):
        """Taux de marge en % par rapport aux versements."""
        if self.total_versements <= 0:
            return Decimal("0.00")
        return (self.marge_brute_estimee / self.total_versements * 100).quantize(Decimal("0.01"))
