# core/models/proprietaire.py
from django.db import models

class Proprietaire(models.Model):
    est_moral = models.BooleanField(default=False, verbose_name="Entreprise ?")

    # Entreprise
    entreprise = models.CharField(max_length=100, blank=True, null=True)
    ninea = models.CharField(max_length=100, blank=True, null=True)

    # Personne physique
    prenom = models.CharField(max_length=100, blank=True, null=True)
    nom = models.CharField(max_length=100, blank=True, null=True)
    numero_identite = models.CharField(max_length=100, blank=True, null=True)
    sexe = models.CharField(
        max_length=10,
        choices=[('M', 'Masculin'), ('F', 'Féminin')],
        blank=True,
        null=True
    )

    # Coordonnées
    telephone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    adresse = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['entreprise', 'nom']
        verbose_name = "Client"
        verbose_name_plural = "Clients"

    def __str__(self):
        return self.nom_complet()

    def nom_complet(self):
        if self.est_moral:
            return self.entreprise or "Entreprise sans nom"
        else:
            return f"{self.prenom or ''} {self.nom or ''}".strip()
