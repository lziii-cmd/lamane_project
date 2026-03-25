# core/models/bon_sortie.py
"""
BonSortie — Bon de sortie de matériaux du stock vers un chantier/projet.
Chaque sortie de matériau décrémente le stock disponible.
"""
import uuid
from decimal import Decimal
from io import BytesIO
from pathlib import Path

from django.db import models
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone


class BonSortie(models.Model):
    """En-tête du bon de sortie matériaux."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(
        "Référence", max_length=30, unique=True, blank=True,
        help_text="Auto-générée à la sauvegarde (ex: BS-2025-001)"
    )
    projet = models.ForeignKey(
        "core.Projet",
        on_delete=models.CASCADE,
        related_name="bons_sortie",
        verbose_name="Projet / Chantier",
    )
    date_sortie = models.DateField("Date de sortie", default=timezone.now)
    responsable = models.CharField(
        "Responsable de la sortie", max_length=100, blank=True,
        help_text="Nom du chef de chantier ou conducteur de travaux"
    )
    observations = models.TextField("Observations", blank=True)
    bon_pdf = models.FileField(
        upload_to="bons_sortie/", verbose_name="Bon de sortie PDF",
        blank=True, null=True
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bon de sortie"
        verbose_name_plural = "Bons de sortie"
        ordering = ["-date_sortie"]

    def __str__(self):
        return f"{self.reference or self.id} — {self.projet.nom}"

    def save(self, *args, **kwargs):
        # Auto-générer la référence
        if not self.reference:
            year = timezone.now().year
            count = BonSortie.objects.filter(
                date_creation__year=year
            ).count() + 1
            self.reference = f"BS-{year}-{count:03d}"
        super().save(*args, **kwargs)
        # Générer le PDF si absent
        if not self.bon_pdf:
            try:
                self._generate_pdf()
                super().save(update_fields=["bon_pdf"])
            except Exception as e:
                import traceback
                print(f"[BON SORTIE PDF] Erreur : {e}")
                traceback.print_exc()

    def total_lignes(self):
        return self.lignes.count()

    def _generate_pdf(self):
        """Génère le PDF du bon de sortie via ReportLab."""
        try:
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.units import cm
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER, TA_RIGHT
        except ImportError:
            return

        buf = BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=A4,
            leftMargin=2*cm, rightMargin=2*cm,
            topMargin=1.5*cm, bottomMargin=2*cm,
            title=f"Bon de Sortie {self.reference}",
        )
        S = getSampleStyleSheet()
        P = S["BodyText"]; P.fontSize = 10
        head = ParagraphStyle("head", parent=S["Heading2"],
                               textColor=colors.HexColor("#2f6f8f"), spaceAfter=8)
        center = ParagraphStyle("center", parent=P, alignment=TA_CENTER)
        right = ParagraphStyle("right", parent=P, alignment=TA_RIGHT)

        # Header
        header = Table(
            [[Paragraph(f"<b><font color='white' size=14>BON DE SORTIE MATÉRIAUX</font></b>", right)]],
            colWidths=[16*cm]
        )
        header.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#2f6f8f")),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("BOTTOMPADDING", (0,0), (-1,-1), 14),
            ("TOPPADDING", (0,0), (-1,-1), 14),
        ]))

        # Infos
        infos = Table([
            [Paragraph(f"<b>Référence :</b> {self.reference}", P),
             Paragraph(f"<b>Date :</b> {self.date_sortie.strftime('%d/%m/%Y')}", right)],
            [Paragraph(f"<b>Projet :</b> {self.projet.nom}", P),
             Paragraph(f"<b>Responsable :</b> {self.responsable or '—'}", right)],
        ], colWidths=[8*cm, 8*cm])
        infos.setStyle(TableStyle([
            ("LINEBELOW", (0,0), (-1,-1), 0.5, colors.HexColor("#e5e7eb")),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ]))

        # Table des lignes
        rows = [["Matériau", "Unité", "Quantité", "Observations"]]
        for lg in self.lignes.select_related("materiel").all():
            rows.append([
                lg.materiel.nom,
                lg.materiel.unite or "—",
                str(lg.quantite),
                lg.commentaire or "—",
            ])

        table = Table(rows, colWidths=[6*cm, 3*cm, 3*cm, 4*cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e9f2f7")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.HexColor("#2f6f8f")),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e5e7eb")),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.white]),
            ("ALIGN", (2,0), (2,-1), "CENTER"),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ]))

        story = [
            header, Spacer(1, 12),
            infos, Spacer(1, 16),
            Paragraph("<b>Matériaux sortis</b>", head),
            table,
        ]
        if self.observations:
            story += [Spacer(1, 14), Paragraph(f"<b>Observations :</b> {self.observations}", P)]

        # Signatures
        sig_table = Table([
            [Paragraph("<b>Remis par</b>", center), Paragraph("<b>Reçu par</b>", center)],
            [Paragraph("", P), Paragraph("", P)],
            [Paragraph("Signature", center), Paragraph("Signature", center)],
        ], colWidths=[8*cm, 8*cm])
        sig_table.setStyle(TableStyle([
            ("LINEABOVE", (0,2), (-1,2), 0.5, colors.grey),
            ("TOPPADDING", (0,1), (-1,1), 30),
        ]))
        story += [Spacer(1, 30), sig_table]

        doc.build(story)
        fname = f"bon_sortie_{self.reference.replace('-', '_')}_{self.date_sortie.strftime('%Y%m%d')}.pdf"
        self.bon_pdf.save(fname, ContentFile(buf.getvalue()), save=False)
        buf.close()


class LigneBonSortie(models.Model):
    """Une ligne (matériau) dans un bon de sortie."""

    bon = models.ForeignKey(
        BonSortie,
        on_delete=models.CASCADE,
        related_name="lignes",
        verbose_name="Bon de sortie",
    )
    materiel = models.ForeignKey(
        "core.Materiel",
        on_delete=models.PROTECT,
        related_name="sorties",
        verbose_name="Matériau",
    )
    quantite = models.DecimalField(
        "Quantité", max_digits=10, decimal_places=2,
        help_text="Quantité sortie (en unité du matériau)"
    )
    commentaire = models.CharField("Commentaire", max_length=200, blank=True)

    class Meta:
        verbose_name = "Ligne bon de sortie"
        verbose_name_plural = "Lignes bon de sortie"

    def __str__(self):
        return f"{self.quantite} × {self.materiel.nom} → {self.bon.projet.nom}"
