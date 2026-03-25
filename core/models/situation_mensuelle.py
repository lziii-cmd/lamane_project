# core/models/situation_mensuelle.py
"""
Situation mensuelle de travaux — Expert BTP & Expert Comptable
Document de facturation émis périodiquement par l'entrepreneur
pour certifier les travaux exécutés et demander le règlement.
Conforme aux pratiques CCAG Travaux (Sénégal / UEMOA).
"""
from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator


class SituationMensuelle(models.Model):
    STATUT_CHOICES = [
        ("brouillon", "Brouillon"),
        ("soumise", "Soumise au maître d'ouvrage"),
        ("validee", "Validée"),
        ("rejetee", "Rejetée"),
        ("payee", "Payée"),
    ]

    projet = models.ForeignKey(
        "core.Projet",
        on_delete=models.CASCADE,
        related_name="situations_mensuelles",
        verbose_name="Projet",
    )
    numero_situation = models.PositiveIntegerField(
        "N° Situation", default=1,
        help_text="Numéro séquentiel de la situation (Situation N°1, N°2, etc.).",
    )
    periode = models.DateField(
        "Période (1er du mois)",
        help_text="Mois de situation (toujours le 1er du mois).",
    )

    # ── Montants ───────────────────────────────────────────────────────────
    montant_brut_cumule = models.DecimalField(
        "Montant brut cumulé HT (FCFA)",
        max_digits=16, decimal_places=2, default=Decimal("0.00"),
        help_text="Cumul des travaux réalisés depuis le début jusqu'à cette période.",
    )
    taux_avancement = models.DecimalField(
        "Taux d'avancement (%)",
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=Decimal("0.00"),
    )
    retenue_garantie = models.DecimalField(
        "Retenue de garantie (FCFA)",
        max_digits=14, decimal_places=2, default=Decimal("0.00"),
        help_text="Retenue de garantie prélevée sur cette situation (5% standard).",
    )
    montant_net_cumule = models.DecimalField(
        "Montant net cumulé HT (FCFA)",
        max_digits=16, decimal_places=2, default=Decimal("0.00"),
        help_text="Montant brut cumulé moins retenue de garantie.",
    )
    montant_precedentes_situations = models.DecimalField(
        "Montant situations précédentes (FCFA)",
        max_digits=16, decimal_places=2, default=Decimal("0.00"),
    )
    montant_a_payer = models.DecimalField(
        "Montant à payer cette situation (FCFA)",
        max_digits=16, decimal_places=2, default=Decimal("0.00"),
        help_text="= Montant net cumulé - Situations précédentes.",
    )

    statut = models.CharField(
        "Statut", max_length=20, choices=STATUT_CHOICES, default="brouillon",
    )
    date_soumission = models.DateField("Date de soumission", null=True, blank=True)
    date_validation = models.DateField("Date de validation", null=True, blank=True)
    observations = models.TextField("Observations / Réserves", blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Situation mensuelle"
        verbose_name_plural = "Situations mensuelles"
        ordering = ["projet", "numero_situation"]
        unique_together = [("projet", "numero_situation")]

    def __str__(self):
        return f"Situation N°{self.numero_situation} — {self.projet.nom} ({self.periode.strftime('%B %Y')})"

    def auto_calcul(self, taux_retenue=Decimal("5.00")):
        """Recalcule les montants selon le taux d'avancement et le marché."""
        try:
            marche = self.projet.marche
            montant_marche = marche.montant_marche
        except Exception:
            return
        self.montant_brut_cumule = (montant_marche * self.taux_avancement / 100).quantize(Decimal("0.01"))
        self.retenue_garantie = (self.montant_brut_cumule * taux_retenue / 100).quantize(Decimal("0.01"))
        self.montant_net_cumule = self.montant_brut_cumule - self.retenue_garantie
        self.montant_a_payer = max(
            self.montant_net_cumule - self.montant_precedentes_situations, Decimal("0.00")
        )
