# core/models/vitrine.py
"""Modeles editables pour le site vitrine LAMANE."""
from django.db import models
from core.models.base import BaseModel


class ConfigVitrine(BaseModel):
    """Configuration generale du site vitrine (singleton)."""

    # ── Hero Section ──────────────────────────────────────────────────
    hero_titre = models.CharField(
        "Titre principal (Hero)",
        max_length=200,
        default="Investissez dans l'immobilier au Senegal en toute securite",
    )
    hero_sous_titre = models.TextField(
        "Sous-titre Hero",
        default="LAMANE concoit, finance et realise des projets immobiliers fiables et structures.",
    )
    hero_bouton_texte = models.CharField(
        "Texte du bouton CTA",
        max_length=60,
        default="Decouvrir nos projets",
    )
    hero_bouton_lien = models.CharField(
        "Lien du bouton CTA",
        max_length=200,
        default="#projets",
    )
    hero_image = models.ImageField(
        "Image Hero (fond)",
        upload_to="vitrine/hero/",
        blank=True,
        null=True,
    )

    # ── Presentation rapide ───────────────────────────────────────────
    presentation_titre = models.CharField(
        "Titre presentation",
        max_length=150,
        default="Qui sommes-nous ?",
    )
    presentation_texte = models.TextField(
        "Texte de presentation",
        default=(
            "LAMANE est une societe de promotion immobiliere moderne basee au Senegal. "
            "Nous intervenons dans la conception, le montage, le financement et la "
            "realisation de projets immobiliers, principalement residentiels. Notre "
            "approche structuree et integree nous permet de maitriser l'ensemble de "
            "la chaine de valeur."
        ),
    )

    # ── Chiffres cles ─────────────────────────────────────────────────
    stat_1_nombre = models.CharField("Chiffre 1 (nombre)", max_length=20, default="3+")
    stat_1_label = models.CharField("Chiffre 1 (label)", max_length=60, default="Projets realises")
    stat_2_nombre = models.CharField("Chiffre 2 (nombre)", max_length=20, default="10+")
    stat_2_label = models.CharField("Chiffre 2 (label)", max_length=60, default="Annees d'experience")
    stat_3_nombre = models.CharField("Chiffre 3 (nombre)", max_length=20, default="100%")
    stat_3_label = models.CharField("Chiffre 3 (label)", max_length=60, default="Projets livres")
    stat_4_nombre = models.CharField("Chiffre 4 (nombre)", max_length=20, default="50+")
    stat_4_label = models.CharField("Chiffre 4 (label)", max_length=60, default="Clients satisfaits")

    # ── Mot du directeur ──────────────────────────────────────────────
    directeur_nom = models.CharField("Nom du directeur", max_length=100, default="Fondateur & Directeur General")
    directeur_titre = models.CharField("Titre / poste", max_length=100, default="Ingenieur Genie Civil - Geotechnique")
    directeur_message = models.TextField(
        "Mot du directeur",
        default=(
            "LAMANE est nee d'une volonte de structurer le secteur immobilier et de "
            "creer des opportunites fiables pour la diaspora. Nous combinons expertise "
            "technique, innovation financiere et digitalisation pour transformer "
            "l'investissement immobilier au Senegal."
        ),
    )
    directeur_photo = models.ImageField(
        "Photo du directeur",
        upload_to="vitrine/directeur/",
        blank=True,
        null=True,
    )

    # ── Section Diaspora ──────────────────────────────────────────────
    diaspora_titre = models.CharField(
        "Titre section diaspora",
        max_length=150,
        default="Investir depuis l'etranger",
    )
    diaspora_texte = models.TextField(
        "Description du modele diaspora",
        default=(
            "Vous vivez a l'etranger et souhaitez investir dans l'immobilier au Senegal ? "
            "LAMANE vous offre un modele securise : apport initial, structuration "
            "financiere, gestion centralisee et livraison dans les delais."
        ),
    )
    diaspora_etape_1 = models.CharField(max_length=100, default="Inscription & etude de votre projet")
    diaspora_etape_2 = models.CharField(max_length=100, default="Structuration du financement")
    diaspora_etape_3 = models.CharField(max_length=100, default="Lancement de la construction")
    diaspora_etape_4 = models.CharField(max_length=100, default="Suivi en temps reel")
    diaspora_etape_5 = models.CharField(max_length=100, default="Livraison cles en main")

    # ── Contact ───────────────────────────────────────────────────────
    contact_adresse = models.CharField("Adresse", max_length=200, default="Dakar, Senegal")
    contact_telephone = models.CharField("Telephone", max_length=30, default="+221 XX XXX XX XX")
    contact_email = models.EmailField("Email", default="contact@lamane.sn")
    contact_whatsapp = models.CharField("WhatsApp", max_length=30, blank=True, default="")

    # ── SEO / Meta ────────────────────────────────────────────────────
    meta_description = models.CharField(
        "Meta description (SEO)",
        max_length=300,
        default="LAMANE - Societe de promotion immobiliere au Senegal. Construction, investissement diaspora, projets residentiels.",
    )

    # ── Footer ────────────────────────────────────────────────────────
    footer_texte = models.CharField(
        "Texte footer",
        max_length=200,
        default="LAMANE SARL - Promotion immobiliere & Gestion de projets BTP",
    )

    class Meta:
        verbose_name = "Configuration du site vitrine"
        verbose_name_plural = "Configuration du site vitrine"

    def __str__(self):
        return "Configuration Vitrine"

    def save(self, *args, **kwargs):
        """Singleton : un seul objet autorise."""
        self.pk = self.__class__.objects.first().pk if self.__class__.objects.exists() else self.pk
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        """Retourne l'instance unique ou en cree une par defaut."""
        obj, _ = cls.objects.get_or_create(pk=cls.objects.first().pk if cls.objects.exists() else None)
        return obj


class ServiceVitrine(BaseModel):
    """Un service propose par LAMANE (section Services)."""
    icone = models.CharField(
        "Classe icone FontAwesome",
        max_length=50,
        default="fas fa-building",
        help_text="Ex: fas fa-building, fas fa-hard-hat, fas fa-chart-line",
    )
    titre = models.CharField("Titre du service", max_length=100)
    description = models.TextField("Description du service")
    ordre = models.PositiveIntegerField("Ordre d'affichage", default=0)
    actif = models.BooleanField("Actif", default=True)

    class Meta:
        ordering = ["ordre", "titre"]
        verbose_name = "Service vitrine"
        verbose_name_plural = "Services vitrine"

    def __str__(self):
        return self.titre


class ProjetVitrine(BaseModel):
    """Un projet mis en avant sur le site vitrine."""
    nom = models.CharField("Nom du projet", max_length=150)
    description = models.TextField("Description narrative")
    localisation = models.CharField("Localisation", max_length=100)
    statut = models.CharField(
        "Statut",
        max_length=30,
        choices=[
            ("en_cours", "En cours"),
            ("livre", "Livre"),
            ("a_venir", "A venir"),
        ],
        default="en_cours",
    )
    image = models.ImageField("Image du projet", upload_to="vitrine/projets/", blank=True, null=True)
    points_forts = models.TextField(
        "Points forts (un par ligne)",
        blank=True,
        help_text="Saisissez un point fort par ligne",
    )
    ordre = models.PositiveIntegerField("Ordre d'affichage", default=0)
    actif = models.BooleanField("Actif", default=True)

    class Meta:
        ordering = ["ordre", "nom"]
        verbose_name = "Projet vitrine"
        verbose_name_plural = "Projets vitrine"

    def __str__(self):
        return self.nom

    def points_forts_list(self):
        """Retourne les points forts comme liste."""
        if not self.points_forts:
            return []
        return [l.strip() for l in self.points_forts.splitlines() if l.strip()]


class TemoignageVitrine(BaseModel):
    """Temoignage client pour la vitrine."""
    nom = models.CharField("Nom du client", max_length=100)
    titre = models.CharField("Titre / profession", max_length=100, blank=True, default="")
    texte = models.TextField("Temoignage")
    photo = models.ImageField("Photo", upload_to="vitrine/temoignages/", blank=True, null=True)
    ordre = models.PositiveIntegerField("Ordre d'affichage", default=0)
    actif = models.BooleanField("Actif", default=True)

    class Meta:
        ordering = ["ordre", "nom"]
        verbose_name = "Temoignage vitrine"
        verbose_name_plural = "Temoignages vitrine"

    def __str__(self):
        return f"Temoignage de {self.nom}"
