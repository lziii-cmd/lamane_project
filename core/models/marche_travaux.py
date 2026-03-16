# core/models/marche_travaux.py
"""
Modèle MarcheTravaux — Expert BTP & Comptable
Représente le contrat principal de construction (marché de travaux).
Gère : montant, retenue de garantie, pénalités de retard, avances.
"""
from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class MarcheTravaux(models.Model):
    STATUT_CHOICES = [
        ("en_attente", "En attente de signature"),
        ("signe", "Signé"),
        ("en_cours", "En cours d'exécution"),
        ("reception_provisoire", "Réception provisoire"),
        ("reception_definitive", "Réception définitive"),
        ("resilie", "Résilié"),
    ]

    projet = models.OneToOneField(
        "core.Projet",
        on_delete=models.CASCADE,
        related_name="marche",
        verbose_name="Projet",
    )
    numero_marche = models.CharField("N° Marché", max_length=50, unique=True)
    objet = models.TextField("Objet du marché", blank=True)

    # ── Montants contractuels ──────────────────────────────────────────────
    montant_marche = models.DecimalField(
        "Montant du marché (FCFA HT)",
        max_digits=16, decimal_places=2, default=Decimal("0.00"),
    )
    montant_avance_demarrage = models.DecimalField(
        "Avance de démarrage (FCFA)",
        max_digits=14, decimal_places=2, default=Decimal("0.00"),
        help_text="Avance versée au démarrage (généralement 20-30% du marché).",
    )

    # ── Retenue de garantie ────────────────────────────────────────────────
    taux_retenue_garantie = models.DecimalField(
        "Taux retenue de garantie (%)",
        max_digits=5, decimal_places=2, default=Decimal("5.00"),
        help_text="Prélevée sur chaque situation de travaux (standard : 5%).",
    )

    # ── Pénalités de retard ────────────────────────────────────────────────
    penalite_journaliere_pct = models.DecimalField(
        "Pénalité journalière (%)",
        max_digits=5, decimal_places=4, default=Decimal("0.0500"),
        help_text="% du montant du marché par jour de retard (norme CCAG : 0,05%).",
    )
    plafond_penalites_pct = models.DecimalField(
        "Plafond pénalités (%)",
        max_digits=5, decimal_places=2, default=Decimal("10.00"),
        help_text="Plafond des pénalités exprimé en % du montant du marché.",
    )

    # ── Délais ────────────────────────────────────────────────────────────
    date_signature = models.DateField("Date de signature", null=True, blank=True)
    date_ordre_service = models.DateField("Date ordre de service", null=True, blank=True)
    delai_execution_jours = models.PositiveIntegerField(
        "Délai d'exécution (jours calendaires)", default=365,
    )

    statut = models.CharField(
        "Statut", max_length=30, choices=STATUT_CHOICES, default="en_attente",
    )

    # ── Réception ─────────────────────────────────────────────────────────
    date_reception_provisoire = models.DateField(
        "Date réception provisoire", null=True, blank=True,
    )
    date_reception_definitive = models.DateField(
        "Date réception définitive", null=True, blank=True,
    )

    observations = models.TextField("Observations", blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Marché de travaux"
        verbose_name_plural = "Marchés de travaux"
        ordering = ["-date_signature"]

    def __str__(self):
        return f"{self.numero_marche} — {self.projet.nom}"

    # ── Méthodes calculées ─────────────────────────────────────────────────
    @property
    def date_fin_prevue(self):
        """Date de fin prévisionnelle = ordre de service + délai."""
        if self.date_ordre_service and self.delai_execution_jours:
            from datetime import timedelta
            return self.date_ordre_service + timedelta(days=self.delai_execution_jours)
        return None

    @property
    def retenue_garantie_montant(self):
        """Montant de la retenue de garantie (sur montant marché)."""
        return (self.montant_marche * self.taux_retenue_garantie / 100).quantize(Decimal("0.01"))

    @property
    def plafond_penalites_montant(self):
        return (self.montant_marche * self.plafond_penalites_pct / 100).quantize(Decimal("0.01"))

    @property
    def jours_retard(self):
        """Calcule le retard en jours (si dépassement du délai)."""
        if not self.date_ordre_service or not self.delai_execution_jours:
            return 0
        from datetime import timedelta
        date_fin_th = self.date_ordre_service + timedelta(days=self.delai_execution_jours)
        today = timezone.now().date()
        ref = self.date_reception_provisoire or today
        if ref > date_fin_th:
            return (ref - date_fin_th).days
        return 0

    @property
    def penalites_calculees(self):
        """Montant des pénalités de retard calculées."""
        retard = self.jours_retard
        if retard <= 0:
            return Decimal("0.00")
        penalite = (self.montant_marche * self.penalite_journaliere_pct / 100 * retard).quantize(Decimal("0.01"))
        plafond = self.plafond_penalites_montant
        return min(penalite, plafond)

    def clean(self):
        if (self.date_reception_provisoire and self.date_signature
                and self.date_reception_provisoire < self.date_signature):
            raise ValidationError({
                "date_reception_provisoire": "La réception provisoire ne peut précéder la signature."
            })
        if (self.date_reception_definitive and self.date_reception_provisoire
                and self.date_reception_definitive < self.date_reception_provisoire):
            raise ValidationError({
                "date_reception_definitive": "La réception définitive ne peut précéder la réception provisoire."
            })
