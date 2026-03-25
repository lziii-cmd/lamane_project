# core/models/type_projet.py
from django.db import models

class TypeProjet(models.Model):
    nom = models.CharField("Type de projet", max_length=100, unique=True)
    description = models.TextField("Description", blank=True)

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Type de projet"
        verbose_name_plural = "Types de projet"
        ordering = ["nom"]
