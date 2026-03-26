# core/models/document_btp.py
"""
Module Documents BTP — Attachements, bordereaux de prix, décomptes généraux définitifs.
"""
import uuid
from django.db import models
from django.conf import settings


class DocumentProjet(models.Model):
    """Document rattaché à un projet (PV, plan, attachement, etc.)."""

    TYPE_CHOICES = [
        ("pv_reunion", "PV de réunion"),
        ("pv_reception", "PV de réception"),
        ("plan", "Plan / Dessin"),
        ("attachement", "Attachement de travaux"),
        ("photo", "Photo de chantier"),
        ("rapport", "Rapport"),
        ("autre", "Autre"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    projet = models.ForeignKey(
        "core.Projet", on_delete=models.CASCADE, related_name="documents_btp"
    )
    type_document = models.CharField("Type", max_length=20, choices=TYPE_CHOICES)
    titre = models.CharField("Titre", max_length=200)
    description = models.TextField("Description", blank=True)
    fichier = models.FileField("Fichier", upload_to="documents_btp/")
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="documents_crees"
    )
    date_document = models.DateField("Date du document")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Document BTP"
        verbose_name_plural = "Documents BTP"
        ordering = ["-date_document"]

    def __str__(self):
        return f"{self.get_type_document_display()} — {self.titre}"


class BordereauPrix(models.Model):
    """Bordereau de prix d'un projet."""

    STATUT_CHOICES = [
        ("brouillon", "Brouillon"),
        ("valide", "Validé"),
        ("annule", "Annulé"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    projet = models.ForeignKey(
        "core.Projet", on_delete=models.CASCADE, related_name="bordereaux"
    )
    numero = models.CharField("Numéro", max_length=50)
    version = models.PositiveIntegerField("Version", default=1)
    date_edition = models.DateField("Date d'édition")
    statut = models.CharField("Statut", max_length=15, choices=STATUT_CHOICES, default="brouillon")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bordereau de prix"
        verbose_name_plural = "Bordereaux de prix"
        ordering = ["-date_edition"]
        unique_together = [("projet", "numero", "version")]

    def __str__(self):
        return f"BDP {self.numero} v{self.version} — {self.projet.nom}"

    @property
    def total_ht(self):
        return self.lignes.aggregate(
            t=models.Sum(models.F("quantite") * models.F("prix_unitaire"))
        )["t"] or 0


class LigneBordereau(models.Model):
    """Ligne d'un bordereau de prix."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bordereau = models.ForeignKey(
        BordereauPrix, on_delete=models.CASCADE, related_name="lignes"
    )
    numero_prix = models.CharField("N° prix", max_length=20)
    designation = models.CharField("Désignation", max_length=300)
    unite = models.CharField("Unité", max_length=20)
    quantite = models.DecimalField("Quantité", max_digits=12, decimal_places=3)
    prix_unitaire = models.DecimalField("Prix unitaire HT", max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Ligne de bordereau"
        verbose_name_plural = "Lignes de bordereau"
        ordering = ["numero_prix"]

    def __str__(self):
        return f"{self.numero_prix} — {self.designation}"

    @property
    def montant_total(self):
        return self.quantite * self.prix_unitaire


class DecompteGD(models.Model):
    """Décompte Général et Définitif (DGD)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    projet = models.OneToOneField(
        "core.Projet", on_delete=models.CASCADE, related_name="dgd"
    )
    marche = models.ForeignKey(
        "core.MarcheTravaux", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="dgd"
    )
    montant_travaux = models.DecimalField("Montant des travaux", max_digits=14, decimal_places=2, default=0)
    montant_avenants = models.DecimalField("Montant des avenants", max_digits=14, decimal_places=2, default=0)
    montant_penalites = models.DecimalField("Pénalités de retard", max_digits=14, decimal_places=2, default=0)
    montant_retenue_garantie = models.DecimalField("Retenue de garantie", max_digits=14, decimal_places=2, default=0)
    montant_avances = models.DecimalField("Avances versées", max_digits=14, decimal_places=2, default=0)
    montant_acomptes = models.DecimalField("Acomptes payés", max_digits=14, decimal_places=2, default=0)
    observations = models.TextField("Observations", blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Décompte Général Définitif"
        verbose_name_plural = "Décomptes Généraux Définitifs"

    def __str__(self):
        return f"DGD — {self.projet.nom}"

    @property
    def montant_total(self):
        return self.montant_travaux + self.montant_avenants

    @property
    def deductions(self):
        return self.montant_penalites + self.montant_retenue_garantie

    @property
    def solde_a_payer(self):
        return (self.montant_total - self.deductions
                - self.montant_avances - self.montant_acomptes)
