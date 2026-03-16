# core/models/materiel.py
import uuid
from django.db import models
from core.models.categorie_materiel import CategorieMateriel

class Materiel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,
                          help_text="Identifiant unique global (UUID4)")
    date_creation = models.DateTimeField(auto_now_add=True, help_text="Date de création de l’objet")
    date_modification = models.DateTimeField(auto_now=True, help_text="Date de dernière modification")

    nom = models.CharField(max_length=255, unique=True)
    unite = models.CharField(max_length=100)
    categorie = models.ForeignKey(
        CategorieMateriel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='materiaux'
    )

    class Meta:
        verbose_name = "Matériel"
        verbose_name_plural = "Matériaux"
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.unite})"
