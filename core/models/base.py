from django.db import models
import uuid

class BaseModel(models.Model):
    """
    Modèle abstrait de base que tous les modèles métiers vont hériter.
    Fournit un identifiant UUID et les timestamps de création/modification.
    """

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

    class Meta:
        abstract = True  # Ne sera pas migré directement en base
        ordering = ['-date_creation']  # Ordre par défaut dans les requêtes
