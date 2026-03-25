# core/models/etape_standard.py
from django.db import models


class EtapeStandard(models.Model):

    GROUPE_CHOICES = (
        ("gros", "Gros œuvre"),
        ("second", "Second œuvre"),
    )

    """
    Liste des étapes types utilisées dans les projets (fondation, électricité, peinture, etc.).
    Ce modèle sert de référence commune pour tous les projets.
    """
    nom = models.CharField(max_length=100, unique=True)
    ordre = models.PositiveIntegerField(default=0, help_text="Ordre d’apparition dans le cycle de construction")
    # 🔧 AJOUTER CE CHAMP dans EtapeStandard
    multi_niveau = models.BooleanField(
    
    default=False,
    help_text="Cochez si l’étape se décline par niveaux (R+0, R+1… ou S-1)."
)
    groupe = models.CharField(max_length=10, choices=GROUPE_CHOICES, default="gros", db_index=True)

    class Meta:
        verbose_name = "Étape standard"
        verbose_name_plural = "Étapes standards"
        ordering = ['ordre']

    def __str__(self):
        return f"{self.ordre:02d} - {self.nom}"
