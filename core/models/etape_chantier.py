# core/models/etape_chantier.py

from django.db import models
from core.models.base import BaseModel
from core.models.projet import Projet


class EtapeChantier(BaseModel):
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name="etapes")
    nom = models.CharField("Nom de l'étape", max_length=150)

    def __str__(self):
        return f"{self.projet.nom} - {self.nom}"

    class Meta:
        verbose_name = "Étape de chantier"
        verbose_name_plural = "Étapes de chantier"
