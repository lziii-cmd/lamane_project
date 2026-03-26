# core/models/compte_comptable.py
"""
Module Comptabilité SYSCOHADA — Plan comptable, écritures et lignes d'écriture.
"""
import uuid
from django.db import models
from django.utils import timezone


class CompteComptable(models.Model):
    """Compte du plan comptable SYSCOHADA."""

    TYPE_CHOICES = [
        ("actif", "Actif"),
        ("passif", "Passif"),
        ("charge", "Charge"),
        ("produit", "Produit"),
    ]

    CLASSE_CHOICES = [
        (1, "1 - Comptes de ressources durables"),
        (2, "2 - Comptes d'actif immobilisé"),
        (3, "3 - Comptes de stocks"),
        (4, "4 - Comptes de tiers"),
        (5, "5 - Comptes de trésorerie"),
        (6, "6 - Comptes de charges"),
        (7, "7 - Comptes de produits"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField("Code comptable", max_length=10, unique=True,
                            help_text="Ex: 411000, 601000")
    libelle = models.CharField("Libellé", max_length=200)
    type_compte = models.CharField("Type", max_length=10, choices=TYPE_CHOICES)
    classe = models.IntegerField("Classe SYSCOHADA", choices=CLASSE_CHOICES)
    actif = models.BooleanField("Actif", default=True)

    class Meta:
        verbose_name = "Compte comptable"
        verbose_name_plural = "Comptes comptables"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.libelle}"


class EcritureComptable(models.Model):
    """Écriture comptable (pièce avec plusieurs lignes débit/crédit)."""

    JOURNAL_CHOICES = [
        ("AC", "Journal des achats"),
        ("VT", "Journal des ventes / versements"),
        ("BQ", "Journal de banque"),
        ("CA", "Journal de caisse"),
        ("OD", "Opérations diverses"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_piece = models.CharField("N° pièce", max_length=20, unique=True, blank=True)
    date_ecriture = models.DateField("Date")
    libelle = models.CharField("Libellé", max_length=255)
    journal = models.CharField("Journal", max_length=2, choices=JOURNAL_CHOICES)
    projet = models.ForeignKey(
        "core.Projet", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="ecritures_comptables"
    )
    achat = models.ForeignKey(
        "core.Achat", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="ecritures_comptables"
    )
    versement = models.ForeignKey(
        "core.Versement", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="ecritures_comptables"
    )
    contrat_st = models.ForeignKey(
        "core.ContratSousTraitance", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="ecritures_comptables"
    )
    validee = models.BooleanField("Validée", default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Écriture comptable"
        verbose_name_plural = "Écritures comptables"
        ordering = ["-date_ecriture", "-date_creation"]

    def __str__(self):
        return f"{self.numero_piece} — {self.libelle}"

    def save(self, *args, **kwargs):
        if not self.numero_piece:
            year = timezone.now().year
            last = EcritureComptable.objects.filter(
                numero_piece__startswith=f"EC-{year}"
            ).order_by("-numero_piece").first()
            if last and last.numero_piece:
                try:
                    seq = int(last.numero_piece.split("-")[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.numero_piece = f"EC-{year}-{seq:05d}"
        super().save(*args, **kwargs)

    @property
    def total_debit(self):
        return self.lignes.aggregate(s=models.Sum("debit"))["s"] or 0

    @property
    def total_credit(self):
        return self.lignes.aggregate(s=models.Sum("credit"))["s"] or 0

    @property
    def est_equilibree(self):
        return self.total_debit == self.total_credit


class LigneEcriture(models.Model):
    """Ligne d'une écriture comptable (débit ou crédit)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ecriture = models.ForeignKey(
        EcritureComptable, on_delete=models.CASCADE, related_name="lignes"
    )
    compte = models.ForeignKey(
        CompteComptable, on_delete=models.PROTECT, related_name="lignes_ecriture"
    )
    libelle = models.CharField("Libellé", max_length=255, blank=True)
    debit = models.DecimalField("Débit", max_digits=14, decimal_places=2, default=0)
    credit = models.DecimalField("Crédit", max_digits=14, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Ligne d'écriture"
        verbose_name_plural = "Lignes d'écriture"
        ordering = ["-debit", "credit"]

    def __str__(self):
        d = f"D:{self.debit}" if self.debit else ""
        c = f"C:{self.credit}" if self.credit else ""
        return f"{self.compte.code} {d}{c}"
