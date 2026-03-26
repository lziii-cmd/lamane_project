# core/models/profil_utilisateur.py
"""
Profil utilisateur étendu avec rôle et projets autorisés.
"""
import uuid
from django.db import models
from django.conf import settings


class ProfilUtilisateur(models.Model):
    """Extension du User Django avec rôle et droits par projet."""

    ROLE_CHOICES = [
        ("direction", "Direction générale"),
        ("comptable", "Comptable"),
        ("chef_chantier", "Chef de chantier"),
        ("gestionnaire", "Gestionnaire de stock"),
        ("admin", "Administrateur"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profil"
    )
    role = models.CharField("Rôle", max_length=20, choices=ROLE_CHOICES, default="direction")
    projets_autorises = models.ManyToManyField(
        "core.Projet", blank=True,
        related_name="utilisateurs_autorises",
        verbose_name="Projets autorisés"
    )
    telephone = models.CharField("Téléphone", max_length=20, blank=True)
    photo = models.ImageField("Photo de profil", upload_to="profils/", blank=True, null=True)

    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateur"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"

    @property
    def est_direction(self):
        return self.role in ("direction", "admin")

    @property
    def est_comptable(self):
        return self.role in ("comptable", "direction", "admin")

    @property
    def est_chef_chantier(self):
        return self.role == "chef_chantier"
