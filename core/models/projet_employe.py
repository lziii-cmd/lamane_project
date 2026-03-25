# core/models/projet_employe.py
from django.db import models
from django.core.exceptions import ValidationError
from core.models.projet import Projet
from core.models.employe import Employe


class ProjetEmploye(models.Model):
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name="affectations")
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name="affectations")
    role = models.CharField(max_length=100, blank=True, null=True)
    date_affectation = models.DateField()
    date_fin = models.DateField(blank=True, null=True)
    contrat = models.FileField(upload_to="contrats/", blank=True, null=True)
    observation = models.TextField(blank=True, null=True)
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Affectation d'employé"
        verbose_name_plural = "Affectations d'employés"
        unique_together = ("projet", "employe")

    def __str__(self):
        return f"{self.employe.nom_complet()} → {self.projet.nom} ({self.role or 'Sans rôle'})"

    def clean(self):
        super().clean()

        if not self.projet or not self.date_affectation:
            return

        if self.date_affectation < self.projet.date_debut:
            raise ValidationError({
                "date_affectation": "La date d’affectation ne peut pas précéder la date de début du projet."
            })

        if self.projet.date_fin and self.date_affectation > self.projet.date_fin:
            raise ValidationError({
                "date_affectation": "La date d’affectation ne peut pas dépasser la date de fin du projet."
            })
