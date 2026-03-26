# core/models/sous_traitant.py
"""
Sous-traitants & Contrats de sous-traitance — Expert BTP
Gères les spécialistes intervenants sur le chantier (plombiers, électriciens, etc.)
"""
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from django.db import models
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile


SPECIALITE_CHOICES = [
    ("gros_oeuvre", "Gros œuvre"),
    ("charpente_couverture", "Charpente / Couverture"),
    ("plomberie_sanitaire", "Plomberie / Sanitaire"),
    ("electricite_cfa", "Électricité / CFA"),
    ("menuiserie_bois", "Menuiserie Bois"),
    ("menuiserie_alu", "Menuiserie Aluminium"),
    ("carrelage_faience", "Carrelage / Faïence"),
    ("peinture_revetement", "Peinture / Revêtement"),
    ("climatisation", "Climatisation / Ventilation"),
    ("ascenseur", "Ascenseur / Élévation"),
    ("piscine", "Piscine / Traitement de l'eau"),
    ("panneaux_solaires", "Énergie Solaire"),
    ("vrd", "VRD / Terrassement"),
    ("domotique", "Domotique / Smart Building"),
    ("autre", "Autre"),
]


class SousTraitant(models.Model):
    nom = models.CharField("Raison sociale / Nom", max_length=200, unique=True)
    specialite = models.CharField(
        "Spécialité principale", max_length=30,
        choices=SPECIALITE_CHOICES, default="autre",
    )
    ninea = models.CharField("NINEA", max_length=20, blank=True)
    telephone = models.CharField("Téléphone", max_length=20, blank=True)
    email = models.EmailField("Email", blank=True)
    adresse = models.CharField("Adresse", max_length=255, blank=True)
    contact_nom = models.CharField("Nom du contact", max_length=100, blank=True)
    actif = models.BooleanField("Actif", default=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sous-traitant"
        verbose_name_plural = "Sous-traitants"
        ordering = ["nom"]

    def __str__(self):
        return f"{self.nom} ({self.get_specialite_display()})"


class ContratSousTraitance(models.Model):
    STATUT_CHOICES = [
        ("en_cours", "En cours"),
        ("termine", "Terminé"),
        ("suspendu", "Suspendu"),
        ("resilie", "Résilié"),
    ]

    projet = models.ForeignKey(
        "core.Projet",
        on_delete=models.CASCADE,
        related_name="contrats_sous_traitance",
        verbose_name="Projet",
    )
    sous_traitant = models.ForeignKey(
        SousTraitant,
        on_delete=models.PROTECT,
        related_name="contrats",
        verbose_name="Sous-traitant",
    )
    lot = models.CharField(
        "Lot / Désignation", max_length=200,
        help_text="Ex : Lot 3 - Plomberie sanitaire RDC+R+1",
    )
    montant = models.DecimalField(
        "Montant du contrat (FCFA)",
        max_digits=14, decimal_places=2, default=Decimal("0.00"),
    )
    montant_paye = models.DecimalField(
        "Montant déjà payé (FCFA)",
        max_digits=14, decimal_places=2, default=Decimal("0.00"),
    )
    date_debut = models.DateField("Date de début", null=True, blank=True)
    date_fin_prevue = models.DateField("Date de fin prévue", null=True, blank=True)
    date_fin_reelle = models.DateField("Date de fin réelle", null=True, blank=True)
    statut = models.CharField(
        "Statut", max_length=20, choices=STATUT_CHOICES, default="en_cours",
    )
    observations = models.TextField("Observations", blank=True)
    contrat_pdf = models.FileField(
        upload_to="contrats_sous_traitance/",
        verbose_name="Contrat PDF",
        blank=True, null=True,
    )

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Contrat de sous-traitance"
        verbose_name_plural = "Contrats de sous-traitance"
        ordering = ["projet", "sous_traitant"]

    def __str__(self):
        return f"{self.sous_traitant.nom} — {self.lot} ({self.projet.nom})"

    @property
    def reste_a_payer(self):
        return max(self.montant - self.montant_paye, Decimal("0.00"))

    @property
    def taux_paiement(self):
        if self.montant <= 0:
            return Decimal("0.00")
        return (self.montant_paye / self.montant * 100).quantize(Decimal("0.01"))

    def clean(self):
        if (self.date_fin_prevue and self.date_debut
                and self.date_fin_prevue < self.date_debut):
            raise ValidationError({
                "date_fin_prevue": "La date de fin ne peut précéder la date de début."
            })
        if self.montant_paye > self.montant:
            raise ValidationError({
                "montant_paye": "Le montant payé ne peut pas dépasser le montant du contrat."
            })

    # ─── PDF generation ──────────────────────────────────────────────────────

    def generate_contrat_pdf(self):
        """Generate a professional contract PDF and save to contrat_pdf field."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.units import cm
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                HRFlowable, Image as RLImage,
            )
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
            from django.conf import settings
        except ImportError:
            return  # ReportLab not installed

        NAVY   = colors.HexColor("#0f2547")
        GOLD   = colors.HexColor("#f0a500")
        BLUE   = colors.HexColor("#1a6b9e")
        GREY   = colors.HexColor("#4a5568")
        LIGHT  = colors.HexColor("#f7f8fc")
        WHITE  = colors.white
        BLACK  = colors.HexColor("#1a202c")

        buf = BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=A4,
            leftMargin=2*cm, rightMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm,
        )

        W = A4[0] - 4*cm  # usable width

        def _sty(name, **kw):
            defaults = dict(fontName="Helvetica", fontSize=10, leading=14,
                            textColor=BLACK, spaceAfter=4)
            defaults.update(kw)
            return ParagraphStyle(name, **defaults)

        def _safe_img(path, w=None, h=None):
            try:
                p = Path(path)
                for c in [p, p.with_suffix(p.suffix.swapcase())] + \
                          [p.with_suffix(e) for e in ['.png','.PNG','.jpg','.JPG']]:
                    if c.exists():
                        # proportional needs both w and h
                        if w and not h:
                            h = w
                        if h and not w:
                            w = h
                        return RLImage(str(c), width=w, height=h, kind='proportional')
            except Exception:
                pass
            return None

        def _fmt(n):
            try:
                return "{:,.0f}".format(float(n)).replace(",", " ") + " XOF"
            except Exception:
                return str(n)

        LOGOS = Path(getattr(settings, 'BASE_DIR', '.')) / 'logos'
        logo = _safe_img(LOGOS / 'lamane_logo.PNG', w=3.5*cm)
        sig  = _safe_img(LOGOS / 'lamane_signature.png', w=3.5*cm)
        cac  = _safe_img(LOGOS / 'lamane_cachet.png',    w=3.0*cm)

        story = []

        # ── HEADER ────────────────────────────────────────────────────────────
        header_left = [[logo or Paragraph("LAMANE BTP", _sty("lh", fontSize=18, textColor=NAVY, fontName="Helvetica-Bold"))],
                       [Paragraph("LAMANE BTP MANAGEMENT", _sty("ln", fontSize=11, textColor=NAVY, fontName="Helvetica-Bold"))],
                       [Paragraph("Gestion & Construction", _sty("ls", fontSize=8, textColor=GREY))]]

        doc_badge = [
            [Paragraph("CONTRAT DE<br/>SOUS-TRAITANCE",
                        _sty("db", fontSize=13, textColor=WHITE, fontName="Helvetica-Bold",
                             alignment=TA_CENTER, leading=18))],
            [Paragraph(f"N° CST-{self.pk or 'XXX'}",
                        _sty("dn", fontSize=9, textColor=GOLD, fontName="Helvetica-Bold",
                             alignment=TA_CENTER))],
        ]

        hdr_tbl = Table([
            [
                Table(header_left, colWidths=[8*cm]),
                Table(doc_badge,   colWidths=[6*cm],
                      style=TableStyle([
                          ('BACKGROUND', (0,0), (-1,-1), NAVY),
                          ('ROUNDEDCORNERS', [6]),
                          ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                          ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                          ('TOPPADDING', (0,0), (-1,-1), 10),
                          ('BOTTOMPADDING', (0,0), (-1,-1), 10),
                      ]))
            ]
        ], colWidths=[W - 6.2*cm, 6.2*cm])
        hdr_tbl.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(hdr_tbl)
        story.append(Spacer(1, 0.3*cm))
        story.append(HRFlowable(width=W, thickness=3, color=GOLD))
        story.append(Spacer(1, 0.4*cm))

        # ── PARTIES ───────────────────────────────────────────────────────────
        story.append(Paragraph("ENTRE LES SOUSSIGNES", _sty("h2", fontSize=11, fontName="Helvetica-Bold", textColor=NAVY)))
        story.append(Spacer(1, 0.2*cm))

        parties_data = [
            [
                Table([
                    [Paragraph("LE DONNEUR D'ORDRE", _sty("pl", fontSize=9, fontName="Helvetica-Bold", textColor=GOLD))],
                    [Paragraph("LAMANE BTP MANAGEMENT", _sty("pn", fontSize=11, fontName="Helvetica-Bold", textColor=NAVY))],
                    [Paragraph("Entreprise de construction et de gestion de projets BTP", _sty("pd", fontSize=9, textColor=GREY))],
                ], colWidths=[W/2 - 0.5*cm]),
                Table([
                    [Paragraph("LE SOUS-TRAITANT", _sty("pl2", fontSize=9, fontName="Helvetica-Bold", textColor=GOLD))],
                    [Paragraph(self.sous_traitant.nom, _sty("pn2", fontSize=11, fontName="Helvetica-Bold", textColor=NAVY))],
                    [Paragraph(self.sous_traitant.get_specialite_display(), _sty("pd2", fontSize=9, textColor=GREY))],
                ], colWidths=[W/2 - 0.5*cm]),
            ]
        ]
        parties_tbl = Table(parties_data, colWidths=[W/2, W/2])
        parties_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,0), LIGHT),
            ('BACKGROUND', (1,0), (1,0), LIGHT),
            ('BOX', (0,0), (0,0), 0.5, GOLD),
            ('BOX', (1,0), (1,0), 0.5, NAVY),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('COLUMNPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(parties_tbl)
        story.append(Spacer(1, 0.4*cm))

        # ── OBJET ─────────────────────────────────────────────────────────────
        story.append(HRFlowable(width=W, thickness=1, color=GOLD))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph("ARTICLE 1 — OBJET DU CONTRAT", _sty("art", fontSize=10, fontName="Helvetica-Bold", textColor=NAVY)))
        story.append(Spacer(1, 0.1*cm))
        story.append(Paragraph(
            f"Le présent contrat a pour objet la réalisation par le sous-traitant des travaux "
            f"suivants dans le cadre du projet <b>{self.projet.nom}</b> :<br/><br/>"
            f"<b>{self.lot}</b>",
            _sty("body", fontSize=10, leading=15)
        ))
        story.append(Spacer(1, 0.3*cm))

        # ── MONTANT ───────────────────────────────────────────────────────────
        story.append(HRFlowable(width=W, thickness=1, color=GOLD))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph("ARTICLE 2 — MONTANT ET CONDITIONS FINANCIÈRES", _sty("art2", fontSize=10, fontName="Helvetica-Bold", textColor=NAVY)))
        story.append(Spacer(1, 0.1*cm))

        fin_data = [
            ["Montant total du contrat", _fmt(self.montant)],
            ["Montant déjà payé",        _fmt(self.montant_paye)],
            ["Reste à payer",            _fmt(self.reste_a_payer)],
        ]
        fin_rows = [
            [Paragraph(r[0], _sty("fl", fontSize=10, textColor=GREY)),
             Paragraph(r[1], _sty("fv", fontSize=10, fontName="Helvetica-Bold", textColor=NAVY, alignment=TA_RIGHT))]
            for r in fin_data
        ]
        fin_tbl = Table(fin_rows, colWidths=[W*0.6, W*0.4])
        fin_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), LIGHT),
            ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#fff8e7")),
            ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor("#e2e8f0")),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ]))
        story.append(fin_tbl)
        story.append(Spacer(1, 0.3*cm))

        # ── DATES ─────────────────────────────────────────────────────────────
        story.append(HRFlowable(width=W, thickness=1, color=GOLD))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph("ARTICLE 3 — DÉLAIS D'EXÉCUTION", _sty("art3", fontSize=10, fontName="Helvetica-Bold", textColor=NAVY)))
        story.append(Spacer(1, 0.1*cm))

        fmt_date = lambda d: d.strftime("%d/%m/%Y") if d else "Non définie"
        story.append(Paragraph(
            f"Date de début : <b>{fmt_date(self.date_debut)}</b> &nbsp;&nbsp;&nbsp; "
            f"Date de fin prévue : <b>{fmt_date(self.date_fin_prevue)}</b>",
            _sty("dates", fontSize=10)
        ))
        story.append(Spacer(1, 0.3*cm))

        # ── OBSERVATIONS ──────────────────────────────────────────────────────
        if self.observations:
            story.append(HRFlowable(width=W, thickness=1, color=GOLD))
            story.append(Spacer(1, 0.2*cm))
            story.append(Paragraph("ARTICLE 4 — OBSERVATIONS", _sty("art4", fontSize=10, fontName="Helvetica-Bold", textColor=NAVY)))
            story.append(Spacer(1, 0.1*cm))
            story.append(Paragraph(self.observations, _sty("obs", fontSize=10, leading=15)))
            story.append(Spacer(1, 0.3*cm))

        # ── SIGNATURES ────────────────────────────────────────────────────────
        story.append(Spacer(1, 0.5*cm))
        story.append(HRFlowable(width=W, thickness=3, color=GOLD))
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph("SIGNATURES ET CACHETS", _sty("sigh", fontSize=10, fontName="Helvetica-Bold", textColor=NAVY)))
        story.append(Spacer(1, 0.4*cm))

        sig_left  = [sig or Spacer(1, 3*cm), Paragraph("Pour LAMANE BTP<br/><b>Le Gérant</b>", _sty("sl", fontSize=9, alignment=TA_CENTER))]
        sig_right = [cac or Spacer(1, 3*cm), Paragraph(f"Pour {self.sous_traitant.nom}<br/><b>Le Représentant</b>", _sty("sr", fontSize=9, alignment=TA_CENTER))]

        sig_tbl = Table([[sig_left[0], sig_right[0]], [sig_left[1], sig_right[1]]],
                        colWidths=[W/2, W/2])
        sig_tbl.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(sig_tbl)

        doc.build(story)
        pdf_bytes = buf.getvalue()
        buf.close()

        filename = f"contrat_ST_{self.pk or 'new'}.pdf"
        self.contrat_pdf.save(filename, ContentFile(pdf_bytes), save=False)
