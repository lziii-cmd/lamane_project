# core/models/achat.py
import uuid
from decimal import Decimal
from django.db import models
from core.models.projet import Projet
from core.models.fournisseur import Fournisseur

class Achat(models.Model):

    MODE_PAIEMENT_CHOICES = [
        ("espèces", "Espèces"),
        ("virement", "Virement"),
        ("chèque", "Chèque"),
        ("autre", "Autre"),
    ]


    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
        help_text="Identifiant unique global (UUID4)"
    )
    date_creation = models.DateTimeField(auto_now_add=True, help_text="Date de création de l’objet")
    date_modification = models.DateTimeField(auto_now=True, help_text="Date de dernière modification")
    
    date_achat = models.DateField(verbose_name="Date d’achat")
    projet = models.ForeignKey(
        Projet, on_delete=models.CASCADE, related_name="achats"
    )
#    fournisseur = models.CharField("Fournisseur", max_length=255, blank=True)
    fournisseur = models.ForeignKey(
        Fournisseur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Fournisseur",
        related_name="achats"
    )

    #mode_paiement = models.CharField("Mode de paiement", max_length=100)
    mode_paiement = models.CharField(max_length=50, choices=MODE_PAIEMENT_CHOICES)

    numero_facture = models.CharField("N° Facture", max_length=100, blank=True)
    fichier_facture = models.FileField(
        upload_to="achats/factures", verbose_name="Scan Facture", null=True, blank=True
    )
    bon_entree_pdf = models.FileField(
        upload_to="bons_entree/", verbose_name="Bon d'entrée PDF",
        blank=True, null=True
    )

    tva_active = models.BooleanField("TVA active ?", default=False)

    total_ht = models.DecimalField("Total HT", max_digits=12, decimal_places=2, default=0)
    total_tva = models.DecimalField("Montant TVA", max_digits=12, decimal_places=2, default=0)
    total_ttc = models.DecimalField("Total TTC", max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Achat"
        verbose_name_plural = "Achats"
        ordering = ["-date_achat"]

    def __str__(self):
        return f"Achat du {self.date_achat} - {self.projet.nom}"

    def calcul_totaux(self):
        total_ht = sum(l.quantite * l.prix_unitaire for l in self.lignes.all())
        self.total_ht = total_ht
        self.total_tva = total_ht * Decimal("0.18") if self.tva_active else Decimal("0.00")
        self.total_ttc = self.total_ht + self.total_tva

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # save to create ID
        self.calcul_totaux()
        super().save(*args, **kwargs)
