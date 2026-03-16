# core/models/phase_versement.py
from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError

from core.models.projet import Projet
from core.models.etape_standard import EtapeStandard

class PhaseVersement(models.Model):
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name="phases")

    # ⚠️ Compat : on garde libelle tel quel (legacy / editable)
    libelle = models.CharField(max_length=255, help_text="Libellé libre (legacy). Sera auto-généré si étape/niveau fournis.", blank=True)

    # ✅ Nouveau : rattachement au catalogue d’étapes
    etape_standard = models.ForeignKey(
        EtapeStandard, on_delete=models.PROTECT, related_name="phases_projets",
        null=True, blank=True
    )

    # ✅ Nouveau : niveau (ex. -1=S-1, 0=R+0, 1=R+1). Laisser vide si l’étape n’est pas multi-niveau
    niveau = models.IntegerField(null=True, blank=True)

    # ✅ Nouveau : échéance facultative
    echeance = models.DateField(null=True, blank=True)

    # ✅ Nouveau : montant prévu (requis pour le suivi financier)
    montant_prevu = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))

    # ✅ Nouveau : ordre d’affichage dans le projet
    ordre = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Phase de versement"
        verbose_name_plural = "Phases de versement"
        ordering = ["projet", "ordre", "id"]
        # Évite les doublons (projet, même étape, même niveau)
        constraints = [
            models.UniqueConstraint(
                fields=["projet", "etape_standard", "niveau"],
                name="uniq_projet_etape_niveau",
                deferrable=models.Deferrable.DEFERRED
            )
        ]
        indexes = [
            models.Index(fields=["echeance"]),
            models.Index(fields=["projet", "ordre"]),
        ]

    def __str__(self):
        # Affichage intelligent : "Élévation — R+2" OU libellé libre si pas d’étape
        if self.etape_standard:
            base = self.etape_standard.nom
            if self.etape_standard.multi_niveau and self.niveau is not None:
                suffix = f"R+{self.niveau}" if self.niveau >= 0 else f"S{self.niveau}"
                return f"{base} — {suffix}"
            return base
        return self.libelle or "Phase"

    def clean(self):
        errors = {}
        # Si étape non multi-niveau → niveau doit rester vide
        if self.etape_standard and not self.etape_standard.multi_niveau and self.niveau is not None:
            errors["niveau"] = "Cette étape n’est pas multi-niveau : laissez le niveau vide."
        # Si étape multi-niveau → niveau recommandé (on peut le rendre obligatoire si tu veux strict)
        if self.etape_standard and self.etape_standard.multi_niveau and self.niveau is None:
            errors["niveau"] = "Cette étape est multi-niveau : renseignez un niveau (ex. 0 pour R+0, 1 pour R+1, -1 pour S-1)."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Auto-libellé si possible, sans empêcher l’édition manuelle existante
        if (self.etape_standard and not self.libelle):
            if self.etape_standard.multi_niveau and self.niveau is not None:
                suffix = f"R+{self.niveau}" if self.niveau >= 0 else f"S{self.niveau}"
                self.libelle = f"{self.etape_standard.nom} — {suffix}"
            else:
                self.libelle = self.etape_standard.nom
        super().save(*args, **kwargs)
    