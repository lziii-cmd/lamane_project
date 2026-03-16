# core/models/fournisseur.py
from django.db import models
from core.models.base import BaseModel

class Fournisseur(BaseModel):
    est_moral = models.BooleanField(default=False)

    # Bloc Entreprise
    entreprise = models.CharField("Nom de l’entreprise", max_length=150, blank=True)
    ninea = models.CharField("NINEA", max_length=100, blank=True)

    # Bloc Personne Physique
    prenom = models.CharField("Prénom", max_length=100, blank=True)
    nom = models.CharField("Nom", max_length=100, blank=True)
    numero_identite = models.CharField("N° Pièce d’identité", max_length=100, unique=True, blank=True)
    sexe = models.CharField("Sexe", max_length=10, choices=(("H", "Homme"), ("F", "Femme")), blank=True)
    photo_identite = models.ImageField(upload_to="fournisseurs/photos", blank=True, null=True)

    # Coordonnées
    telephone = models.CharField("Téléphone", max_length=100, blank=True)
    email = models.EmailField("Email", blank=True)
    adresse = models.CharField("Adresse", max_length=255, blank=True)

    def __str__(self):
        return self.entreprise if self.est_moral else f"{self.prenom} {self.nom}".strip()

    class Meta:
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"
