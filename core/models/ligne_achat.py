# core/models/ligne_achat.py
import uuid
from decimal import Decimal
from django.db import models
from core.models.achat import Achat
from core.models.materiel import Materiel


class LigneAchat(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identifiant unique global (UUID4)"
    )
    date_creation = models.DateTimeField(auto_now_add=True, help_text="Date de création de l’objet")
    date_modification = models.DateTimeField(auto_now=True, help_text="Date de dernière modification")

    achat = models.ForeignKey(
        Achat,
        on_delete=models.CASCADE,
        related_name='lignes'
    )
    materiel = models.ForeignKey(
        Materiel,
        on_delete=models.PROTECT
    )
    quantite = models.PositiveIntegerField(verbose_name="Quantité", default=Decimal("0"))
    prix_unitaire = models.DecimalField(max_digits=10, default=Decimal("0"), decimal_places=0, verbose_name="Prix unitaire HT")
    commentaire = models.CharField(max_length=255, blank=True, verbose_name="Commentaire")
    #unite = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "Ligne d’achat"
        verbose_name_plural = "Lignes d’achat"

    def __str__(self):
        return f"{self.quantite} x {self.materiel.nom} ({self.achat.numero_facture or 'sans N°'})"

    @property
    def total_ligne(self):
        return self.quantite * self.prix_unitaire
