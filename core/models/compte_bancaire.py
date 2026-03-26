# core/models/compte_bancaire.py
"""
Gestion multi-comptes bancaires et trésorerie.
"""
import uuid
from django.db import models


class CompteBancaire(models.Model):
    """Compte bancaire, caisse ou mobile money."""

    TYPE_CHOICES = [
        ("banque", "Compte bancaire"),
        ("caisse", "Caisse"),
        ("mobile_money", "Mobile Money (Wave/OM)"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField("Nom du compte", max_length=100)
    type_compte = models.CharField("Type", max_length=15, choices=TYPE_CHOICES)
    banque = models.CharField("Banque / Opérateur", max_length=100, blank=True)
    numero_compte = models.CharField("N° de compte", max_length=50, blank=True)
    solde_initial = models.DecimalField("Solde initial", max_digits=14, decimal_places=2, default=0)
    actif = models.BooleanField("Actif", default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Compte bancaire"
        verbose_name_plural = "Comptes bancaires"
        ordering = ["nom"]

    def __str__(self):
        return f"{self.nom} ({self.get_type_compte_display()})"

    @property
    def solde_actuel(self):
        entrees = self.transactions.filter(
            type_transaction="entree"
        ).aggregate(s=models.Sum("montant"))["s"] or 0
        sorties = self.transactions.filter(
            type_transaction="sortie"
        ).aggregate(s=models.Sum("montant"))["s"] or 0
        return self.solde_initial + entrees - sorties


class TransactionBancaire(models.Model):
    """Mouvement sur un compte bancaire."""

    TYPE_CHOICES = [
        ("entree", "Entrée"),
        ("sortie", "Sortie"),
        ("virement_interne", "Virement interne"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    compte = models.ForeignKey(
        CompteBancaire, on_delete=models.CASCADE, related_name="transactions"
    )
    type_transaction = models.CharField("Type", max_length=20, choices=TYPE_CHOICES)
    montant = models.DecimalField("Montant", max_digits=14, decimal_places=2)
    date_transaction = models.DateField("Date")
    libelle = models.CharField("Libellé", max_length=255)
    projet = models.ForeignKey(
        "core.Projet", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="transactions_bancaires"
    )
    achat = models.ForeignKey(
        "core.Achat", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="transactions_bancaires"
    )
    versement = models.ForeignKey(
        "core.Versement", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="transactions_bancaires"
    )
    compte_destination = models.ForeignKey(
        CompteBancaire, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="virements_recus",
        verbose_name="Compte destination (virement interne)"
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Transaction bancaire"
        verbose_name_plural = "Transactions bancaires"
        ordering = ["-date_transaction", "-date_creation"]

    def __str__(self):
        return f"{self.get_type_transaction_display()} — {self.montant} XOF — {self.libelle}"
