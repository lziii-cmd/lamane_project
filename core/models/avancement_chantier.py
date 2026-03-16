# core/models/avancement_chantier.py
"""
Suivi d'avancement de chantier — Expert BTP
Enregistre mensuellement le taux d'avancement physique et financier.
Permet de comparer l'avancement réel vs planifié (S-curve).
"""
from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator


class AvancementChantier(models.Model):
    projet = models.ForeignKey(
        "core.Projet",
        on_delete=models.CASCADE,
        related_name="avancements",
        verbose_name="Projet",
    )
    periode = models.DateField(
        "Période (1er du mois)",
        help_text="Date représentant le mois concerné (toujours le 1er du mois).",
    )

    # ── Taux d'avancement ──────────────────────────────────────────────────
    taux_physique = models.DecimalField(
        "Avancement physique (%)",
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=Decimal("0.00"),
        help_text="Pourcentage des travaux physiquement réalisés.",
    )
    taux_financier = models.DecimalField(
        "Avancement financier (%)",
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=Decimal("0.00"),
        help_text="Pourcentage du montant du marché déjà facturé/certifié.",
    )
    taux_planifie = models.DecimalField(
        "Avancement planifié (%)",
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=Decimal("0.00"),
        help_text="Avancement prévu selon le planning initial (courbe S).",
    )

    # ── Effectifs & ressources ─────────────────────────────────────────────
    effectif_ouvriers = models.PositiveIntegerField(
        "Effectif ouvriers", default=0,
        help_text="Nombre d'ouvriers présents sur le chantier ce mois.",
    )
    effectif_encadrement = models.PositiveIntegerField(
        "Effectif encadrement", default=0,
        help_text="Chefs de chantier + conducteurs de travaux.",
    )

    # ── Observations & incidents ───────────────────────────────────────────
    observations = models.TextField("Observations techniques", blank=True)
    incidents = models.TextField(
        "Incidents / Non-conformités", blank=True,
        help_text="Mauvaises conditions météo, sinistres, non-conformités qualité.",
    )
    mesures_correctives = models.TextField("Mesures correctives", blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Avancement chantier"
        verbose_name_plural = "Avancements chantier"
        ordering = ["projet", "-periode"]
        unique_together = [("projet", "periode")]

    def __str__(self):
        return f"{self.projet.nom} — {self.periode.strftime('%B %Y')} ({self.taux_physique}%)"

    @property
    def ecart_avancement(self):
        """Écart entre avancement physique et planifié (positif = avance)."""
        return self.taux_physique - self.taux_planifie

    @property
    def ecart_physique_financier(self):
        """Écart physique vs financier (négatif = sous-facturation)."""
        return self.taux_physique - self.taux_financier

    def clean(self):
        # Forcer la date au 1er du mois
        if self.periode and self.periode.day != 1:
            raise ValidationError({
                "periode": "La période doit toujours être fixée au 1er du mois."
            })
        if self.taux_physique < self.taux_financier - 20:
            raise ValidationError({
                "taux_financier": "L'avancement financier ne peut pas dépasser l'avancement physique de plus de 20%."
            })
