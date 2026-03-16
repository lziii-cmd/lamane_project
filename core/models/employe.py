# core/models/employe.py
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models.personne import Personne


class Employe(Personne):
    matricule = models.CharField(max_length=50, unique=True, editable=False)
    poste = models.CharField(max_length=100, blank=True, null=True)
    date_embauche = models.DateField(blank=True, null=True)
    adresse = models.CharField("Adresse", max_length=255, blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Employé"
        verbose_name_plural = "Employés"

    def __str__(self):
        return f"{self.matricule or 'N/A'} - {self.nom_complet()}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            prefix_prenom = (self.prenom[:2] if self.prenom else 'XX').upper()
            prefix_nom = (self.nom[:2] if self.nom else 'YY').upper()
            numero = str(self.pk).zfill(4)
            self.matricule = f"{prefix_prenom}{prefix_nom}{numero}"
            super().save(update_fields=["matricule"])

    def clean(self):
        super().clean()
        if self.date_embauche and self.date_embauche > timezone.now().date():
            raise ValidationError({
                "date_embauche": "La date d’embauche ne peut pas être dans le futur."
            })
