from django.db import models
from django.core.exceptions import ValidationError
import re

class Personne(models.Model):
    SEXE_CHOICES = [
        ('Homme', 'Homme'),
        ('Femme', 'Femme'),
    ]

    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100, blank=True, null=True)
    date_naissance = models.DateField(blank=True, null=True)
    sexe = models.CharField(max_length=10, choices=SEXE_CHOICES, blank=True, null=True)

    numero_identite = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Numéro de pièce d'identité (CNI, passeport, etc.)"
    )

    telephone = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    photo_identite = models.ImageField(upload_to='photos_identite/', blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.nom_complet()

    def nom_complet(self):
        return f"{self.prenom or ''} {self.nom}".strip()

    def civilite(self):
        if self.sexe == 'Femme':
            return "Mme"
        elif self.sexe == 'Homme':
            return "M."
        return ""

    def clean(self):
        super().clean()

        # Validation 1 — numéro d'identité unique si renseigné
        if self.numero_identite:
            cls = self.__class__
            if cls.objects.exclude(pk=self.pk).filter(numero_identite=self.numero_identite).exists():
                raise ValidationError({
                    "numero_identite": "Ce numéro de pièce d’identité est déjà utilisé par une autre personne."
                })

        # Validation 2 — sexe facultatif (null autorisé sur le champ)

        # Validation 3 — téléphone format simple si renseigné
        if self.telephone:
            pattern = r'^\+?[0-9\s\-]{6,20}$'
            if not re.match(pattern, self.telephone):
                raise ValidationError({
                    "telephone": "Le numéro de téléphone n’est pas dans un format valide."
                })
