# core/models/metre.py
"""Modeles pour le module Metre sur plan — LAMANE BTP."""
from django.db import models
from core.models.base import BaseModel


class LotMetre(BaseModel):
    """Lot / chapitre du metre (Gros oeuvre, Second oeuvre, VRD...)."""
    nom = models.CharField("Nom du lot", max_length=150)
    code = models.CharField("Code", max_length=20, blank=True, default="")
    ordre = models.PositiveIntegerField("Ordre", default=0)

    class Meta:
        ordering = ["ordre", "nom"]
        verbose_name = "Lot de metre"
        verbose_name_plural = "Lots de metre"

    def __str__(self):
        if self.code:
            return f"{self.code} — {self.nom}"
        return self.nom


class TypeElement(BaseModel):
    """Type d'element tracable sur le plan (Mur porteur, Cloison, Porte...)."""
    UNITE_CHOICES = [
        ("ml", "Metre lineaire (ml)"),
        ("m2", "Metre carre (m2)"),
        ("m3", "Metre cube (m3)"),
        ("u", "Unite (U)"),
        ("ff", "Forfait (FF)"),
        ("kg", "Kilogramme (kg)"),
    ]
    OUTIL_CHOICES = [
        ("ligne", "Ligne (longueur)"),
        ("rectangle", "Rectangle (surface)"),
        ("polygone", "Polygone (surface)"),
        ("point", "Point (comptage)"),
    ]

    nom = models.CharField("Nom", max_length=100)
    lot = models.ForeignKey(
        LotMetre, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="types_elements", verbose_name="Lot",
    )
    couleur = models.CharField(
        "Couleur (hex)", max_length=7, default="#FF0000",
        help_text="Code couleur hexadecimal, ex: #FF0000 pour rouge",
    )
    unite = models.CharField("Unite", max_length=5, choices=UNITE_CHOICES, default="ml")
    outil = models.CharField("Outil de trace", max_length=15, choices=OUTIL_CHOICES, default="ligne")
    epaisseur_defaut = models.DecimalField(
        "Epaisseur par defaut (m)", max_digits=6, decimal_places=3,
        default=0, help_text="Pour calcul de volume : surface x epaisseur",
    )
    prix_unitaire = models.DecimalField(
        "Prix unitaire par defaut (FCFA)", max_digits=12, decimal_places=2,
        default=0,
    )
    ordre = models.PositiveIntegerField("Ordre d'affichage", default=0)
    actif = models.BooleanField("Actif", default=True)

    class Meta:
        ordering = ["ordre", "nom"]
        verbose_name = "Type d'element"
        verbose_name_plural = "Types d'elements"

    def __str__(self):
        return f"{self.nom} ({self.get_unite_display()})"


class PlanMetre(BaseModel):
    """Un plan PDF uploade pour faire le metre (un par etage)."""
    projet = models.ForeignKey(
        "core.Projet", on_delete=models.CASCADE,
        related_name="plans_metre", verbose_name="Projet",
    )
    nom = models.CharField("Nom du plan", max_length=150, help_text="Ex: RDC, Etage 1, Toiture")
    fichier_pdf = models.FileField("Fichier PDF", upload_to="metres/plans/")
    ordre = models.PositiveIntegerField("Ordre (etage)", default=0)

    # Echelle — definie par l'utilisateur sur le canvas
    echelle_pixels = models.FloatField(
        "Longueur de reference en pixels", default=0,
        help_text="Nombre de pixels du segment de reference trace",
    )
    echelle_metres = models.FloatField(
        "Longueur de reference en metres", default=1.0,
        help_text="Longueur reelle correspondante en metres",
    )

    class Meta:
        ordering = ["projet", "ordre", "nom"]
        verbose_name = "Plan de metre"
        verbose_name_plural = "Plans de metre"

    def __str__(self):
        return f"{self.projet.nom} — {self.nom}"

    @property
    def ratio_pixel_metre(self):
        """Retourne le ratio pixels/metre pour les calculs."""
        if self.echelle_pixels and self.echelle_pixels > 0:
            return self.echelle_pixels / self.echelle_metres
        return 0

    @property
    def echelle_definie(self):
        """True si l'echelle a ete calibree."""
        return self.echelle_pixels > 0


class TraceMetre(BaseModel):
    """Un trace sur le plan (ligne, rectangle, polygone ou point)."""
    plan = models.ForeignKey(
        PlanMetre, on_delete=models.CASCADE,
        related_name="traces", verbose_name="Plan",
    )
    type_element = models.ForeignKey(
        TypeElement, on_delete=models.CASCADE,
        related_name="traces", verbose_name="Type d'element",
    )

    # Coordonnees du trace (JSON) — format depend de l'outil
    # Ligne: {"points": [{"x": 10, "y": 20}, {"x": 300, "y": 20}]}
    # Rectangle: {"x": 10, "y": 20, "width": 200, "height": 150}
    # Polygone: {"points": [{"x": 10, "y": 20}, {"x": 300, "y": 20}, ...]}
    # Point: {"x": 150, "y": 80}
    coordonnees = models.JSONField("Coordonnees du trace", default=dict)

    # Valeurs calculees
    longueur_pixels = models.FloatField("Longueur en pixels", default=0)
    surface_pixels = models.FloatField("Surface en pixels carres", default=0)

    longueur_metres = models.FloatField("Longueur (m)", default=0)
    surface_metres = models.FloatField("Surface (m2)", default=0)
    volume_metres = models.FloatField("Volume (m3)", default=0)
    quantite = models.FloatField("Quantite", default=0)

    # Surcharges optionnelles
    epaisseur = models.DecimalField(
        "Epaisseur (m)", max_digits=6, decimal_places=3,
        null=True, blank=True,
        help_text="Surcharge l'epaisseur du type d'element",
    )
    prix_unitaire = models.DecimalField(
        "Prix unitaire (FCFA)", max_digits=12, decimal_places=2,
        null=True, blank=True,
        help_text="Surcharge le prix unitaire du type d'element",
    )
    commentaire = models.CharField("Commentaire", max_length=200, blank=True, default="")

    class Meta:
        ordering = ["plan", "type_element__ordre", "date_creation"]
        verbose_name = "Trace de metre"
        verbose_name_plural = "Traces de metre"

    def __str__(self):
        return f"{self.type_element.nom} — {self.quantite_display}"

    @property
    def quantite_display(self):
        """Affiche la quantite avec l'unite."""
        unite = self.type_element.unite
        if unite == "ml":
            return f"{self.longueur_metres:.2f} ml"
        elif unite == "m2":
            return f"{self.surface_metres:.2f} m2"
        elif unite == "m3":
            return f"{self.volume_metres:.3f} m3"
        elif unite == "u":
            return f"{int(self.quantite)} U"
        return f"{self.quantite}"

    @property
    def prix_unit(self):
        """Prix unitaire effectif (surcharge ou defaut du type)."""
        if self.prix_unitaire is not None:
            return float(self.prix_unitaire)
        return float(self.type_element.prix_unitaire)

    @property
    def epaisseur_effective(self):
        """Epaisseur effective (surcharge ou defaut du type)."""
        if self.epaisseur is not None:
            return float(self.epaisseur)
        return float(self.type_element.epaisseur_defaut)

    @property
    def montant_total(self):
        """Montant = quantite x prix unitaire."""
        return self.quantite * self.prix_unit

    def calculer(self):
        """Calcule longueur, surface, volume, quantite a partir des pixels et de l'echelle."""
        ratio = self.plan.ratio_pixel_metre
        if ratio <= 0:
            return

        outil = self.type_element.outil

        if outil == "ligne":
            self.longueur_metres = self.longueur_pixels / ratio
            self.quantite = self.longueur_metres

        elif outil in ("rectangle", "polygone"):
            ratio_carre = ratio * ratio
            self.surface_metres = self.surface_pixels / ratio_carre
            self.quantite = self.surface_metres
            # Volume = surface x epaisseur
            ep = self.epaisseur_effective
            if ep > 0:
                self.volume_metres = self.surface_metres * ep

        elif outil == "point":
            self.quantite = 1

    def save(self, *args, **kwargs):
        self.calculer()
        super().save(*args, **kwargs)
