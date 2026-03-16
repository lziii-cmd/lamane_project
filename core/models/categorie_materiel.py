# core/models/categorie_materiel.py
import uuid
from django.db import models

class CategorieMateriel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identifiant unique global (UUID4)"
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        help_text="Date de création de l’objet"
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        help_text="Date de dernière modification"
    )
    nom = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nom de la catégorie"
    )

    class Meta:
        verbose_name = "Catégorie de Matériel"
        verbose_name_plural = "Catégories de Matériaux"
        ordering = ['nom']

    def __str__(self):
        return self.nom
