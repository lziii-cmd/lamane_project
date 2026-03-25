from django.db import models

class Caracteristique(models.Model):
    projet = models.OneToOneField(
        "core.Projet",
        on_delete=models.CASCADE,
        related_name="caracteristique"
    )

    superficie_totale = models.FloatField(null=True, blank=True, help_text="Superficie du terrain (en m²)")
    surface_batie = models.FloatField(null=True, blank=True, help_text="Surface construite (en m²)")
    nombre_etages = models.PositiveIntegerField(null=True, blank=True)
    nombre_pieces = models.PositiveIntegerField(null=True, blank=True)

    piscine = models.BooleanField(default=False)
    ascenseur = models.BooleanField(default=False)
    groupe_electrogene = models.BooleanField(default=False)
    panneau_solaire = models.BooleanField(default=False)
    parking_souterrain = models.BooleanField(default=False)
    climatisation = models.BooleanField(default=False)
    acces_handicapes = models.BooleanField(default=False)

    performance_energetique = models.CharField(
        max_length=5,
        blank=True,
        null=True,
        help_text="Ex: A, B, C..."
    )

    def __str__(self):
        return f"Caractéristiques du projet {self.projet.nom}"
