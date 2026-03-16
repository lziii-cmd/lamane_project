# core/models/sous_traitant.py
"""
Sous-traitants & Contrats de sous-traitance — Expert BTP
Gère les spécialistes intervenants sur le chantier (plombiers, électriciens, etc.)
"""
from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError


SPECIALITE_CHOICES = [
    ("gros_oeuvre", "Gros œuvre"),
    ("charpente_couverture", "Charpente / Couverture"),
    ("plomberie_sanitaire", "Plomberie / Sanitaire"),
    ("electricite_cfa", "Électricité / CFA"),
    ("menuiserie_bois", "Menuiserie Bois"),
    ("menuiserie_alu", "Menuiserie Aluminium"),
    ("carrelage_faience", "Carrelage / Faïence"),
    ("peinture_revetement", "Peinture / Revêtement"),
    ("climatisation", "Climatisation / Ventilation"),
    ("ascenseur", "Ascenseur / Élévation"),
    ("piscine", "Piscine / Traitement de l'eau"),
    ("panneaux_solaires", "Énergie Solaire"),
    ("vrd", "VRD / Terrassement"),
    ("domotique", "Domotique / Smart Building"),
    ("autre", "Autre"),
]


class SousTraitant(models.Model):
    nom = models.CharField("Raison sociale / Nom", max_length=200, unique=True)
    specialite = models.CharField(
        "Spécialité principale", max_length=30,
        choices=SPECIALITE_CHOICES, default="autre",
    )
    ninea = models.CharField("NINEA", max_length=20, blank=True)
    telephone = models.CharField("Téléphone", max_length=20, blank=True)
    email = models.EmailField("Email", blank=True)
    adresse = models.CharField("Adresse", max_length=255, blank=True)
    contact_nom = models.CharField("Nom du contact", max_length=100, blank=True)
    actif = models.BooleanField("Actif", default=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sous-traitant"
        verbose_name_plural = "Sous-traitants"
        ordering = ["nom"]

    def __str__(self):
        return f"{self.nom} ({self.get_specialite_display()})"


class ContratSousTraitance(models.Model):
    STATUT_CHOICES = [
        ("en_cours", "En cours"),
        ("termine", "Terminé"),
        ("suspendu", "Suspendu"),
        ("resilie", "Résilié"),
    ]

    projet = models.ForeignKey(
        "core.Projet",
        on_delete=models.CASCADE,
        related_name="contrats_sous_traitance",
        verbose_name="Projet",
    )
    sous_traitant = models.ForeignKey(
        SousTraitant,
        on_delete=models.PROTECT,
        related_name="contrats",
        verbose_name="Sous-traitant",
    )
    lot = models.CharField(
        "Lot / Désignation", max_length=200,
        help_text="Ex : Lot 3 - Plomberie sanitaire RDC+R+1",
    )
    montant = models.DecimalField(
        "Montant du contrat (FCFA)",
        max_digits=14, decimal_places=2, default=Decimal("0.00"),
    )
    montant_paye = models.DecimalField(
        "Montant déjà payé (FCFA)",
        max_digits=14, decimal_places=2, default=Decimal("0.00"),
    )
    date_debut = models.DateField("Date de début", null=True, blank=True)
    date_fin_prevue = models.DateField("Date de fin prévue", null=True, blank=True)
    date_fin_reelle = models.DateField("Date de fin réelle", null=True, blank=True)
    statut = models.CharField(
        "Statut", max_length=20, choices=STATUT_CHOICES, default="en_cours",
    )
    observations = models.TextField("Observations", blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Contrat de sous-traitance"
        verbose_name_plural = "Contrats de sous-traitance"
        ordering = ["projet", "sous_traitant"]

    def __str__(self):
        return f"{self.sous_traitant.nom} — {self.lot} ({self.projet.nom})"

    @property
    def reste_a_payer(self):
        return max(self.montant - self.montant_paye, Decimal("0.00"))

    @property
    def taux_paiement(self):
        if self.montant <= 0:
            return Decimal("0.00")
        return (self.montant_paye / self.montant * 100).quantize(Decimal("0.01"))

    def clean(self):
        if (self.date_fin_prevue and self.date_debut
                and self.date_fin_prevue < self.date_debut):
            raise ValidationError({
                "date_fin_prevue": "La date de fin ne peut précéder la date de début."
            })
        if self.montant_paye > self.montant:
            raise ValidationError({
                "montant_paye": "Le montant payé ne peut pas dépasser le montant du contrat."
            })
