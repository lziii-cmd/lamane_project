# core/models/versement.py
import os
import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.files.base import ContentFile
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

from reportlab.platypus import Image, SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

from django.conf import settings
from pathlib import Path
from reportlab.lib.enums import TA_RIGHT, TA_CENTER

#ajout
THEME = {
    "brand": colors.HexColor("#5da5c9"),      # bleu lamane
    "brand_light": colors.HexColor("#e9f2f7"),
    "text_muted": colors.HexColor("#6b7280"), # gris
    "line": colors.HexColor("#e5e7eb"),
}

def _fmt_cfa(n):
    try:
        return f"{int(n):,}".replace(",", " ") + " FCFA"   # espace normal (pas de carrés)
    except Exception:
        return f"{n} FCFA"

def _load_img(p: Path, w=None, h=None):
    if p and p.exists():
        return Image(str(p), width=w, height=h, kind="proportional")
    return None

class Versement(models.Model):
    TYPE_VERSEMENT_CHOICES = [
        ('chèque', 'Chèque'),
        ('virement bancaire', 'Virement bancaire'),
        ('virement om', 'Virement Orange Money'),
        ('wave', 'Wave'),
        ('espèces', 'Espèces'),
        ('autres', 'Autres'),
    ]

    projet = models.ForeignKey(
        'core.Projet',
        on_delete=models.CASCADE,
        related_name='versements'
    )
    phase = models.ForeignKey(
        'core.PhaseVersement',
        on_delete=models.CASCADE,
        related_name='versements'
    )
    etape = models.ForeignKey(
        'core.EtapeStandard',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='versements'
    )
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    date_versement = models.DateField()
    type_versement = models.CharField(max_length=30, choices=TYPE_VERSEMENT_CHOICES)
    fichier_justificatif = models.FileField(
        upload_to='justificatifs_versement/', blank=True, null=True)
    facture_pdf = models.FileField(
        upload_to='factures_versement/', blank=True, null=True)
    libelle = models.CharField(max_length=100, blank=True, editable=False)
    
    #dioum
    numero_facture = models.CharField(max_length=20, blank=True, editable=False)
    reference_paiement = models.CharField("Référence du paiement", max_length=60, blank=True, null=True)

    class Meta:
        ordering = ['-date_versement']

    def __str__(self):
        return self.libelle if self.libelle else f"Versement de {self.montant} le {self.date_versement}"
    
    #dioum
    def save(self, *args, **kwargs):
        if not self.libelle and self.projet_id:
            count = Versement.objects.filter(projet=self.projet).count() + 1
            self.libelle = f"Versement {count} - {self.projet.nom}"

        # Auto-generer le numero de facture
        if not self.numero_facture:
            year = timezone.now().year
            last = Versement.objects.filter(
                numero_facture__startswith=f"FAC-{year}"
            ).order_by("-numero_facture").first()
            if last and last.numero_facture:
                try:
                    seq = int(last.numero_facture.split("-")[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.numero_facture = f"FAC-{year}-{seq:04d}"

        super().save(*args, **kwargs)

        if not self.facture_pdf:
            try:
                self.generate_facture_pdf()
                super().save(update_fields=['facture_pdf'])
            except Exception as e:
                import traceback
                print("[FACTURE] Erreur de generation:", e)
                traceback.print_exc()


#    def save(self, *args, **kwargs):
#        # Générer un libellé du style "Versement 1 - Projet ABC"
#        if not self.libelle:
##            count = Versement.objects.filter(projet=self.projet).count() + 1
#            self.libelle = f"Versement {count} - {self.projet.nom}"

#        super().save(*args, **kwargs)

        # Générer facture si absente
#        if not self.facture_pdf:
#            self.generate_facture_pdf()
#            super().save(update_fields=['facture_pdf'])


    def generate_facture_pdf(self):
        """Generate a professional payment receipt PDF using ReportLab."""
        from pathlib import Path
        from io import BytesIO
        from django.core.files.base import ContentFile
        from django.conf import settings
        from django.db.models import Sum
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
        from reportlab.graphics.barcode import qr
        from reportlab.graphics.shapes import Drawing
        from reportlab.graphics import renderPDF

        # ── Color palette ────────────────────────────────────────────────
        NAVY    = colors.HexColor("#0f2547")   # dark navy header
        BLUE    = colors.HexColor("#1a6b9e")   # secondary blue
        GOLD    = colors.HexColor("#f0a500")   # gold accent
        LIGHT   = colors.HexColor("#eef4fa")   # light blue background
        MUTED   = colors.HexColor("#6b7280")   # muted text
        GREEN   = colors.HexColor("#059669")   # positive amount
        WHITE   = colors.white
        BORDER  = colors.HexColor("#d1dce9")

        # ── Image helper ─────────────────────────────────────────────────
        def _safe_img(path, w=None, h=None):
            try:
                p = Path(path)
                for candidate in [p, p.with_suffix(p.suffix.swapcase())] + \
                                  [p.with_suffix(e) for e in ['.png','.PNG','.jpg','.JPG','.jpeg']]:
                    if candidate.exists():
                        return Image(str(candidate), width=w, height=h, kind="proportional")
            except Exception:
                pass
            return None

        def _fmt(n):
            try:
                return f"{int(n):,}".replace(",", "\u202f") + " FCFA"
            except Exception:
                return f"{n} FCFA"

        # ── Business data ─────────────────────────────────────────────────
        total_anterieur = (
            self.__class__.objects
            .filter(projet=self.projet, date_versement__lt=self.date_versement)
            .aggregate(s=Sum("montant"))["s"] or 0
        )
        total_ce_jour = total_anterieur + (self.montant or 0)
        budget = None
        for attr in ("cout_estime_lamane", "budget", "montant_total", "cout_previsionnel"):
            v = getattr(self.projet, attr, None)
            if v:
                budget = v
                break
        # Try marché
        if budget is None:
            try:
                m = self.projet.marche
                budget = m.montant_marche
            except Exception:
                pass
        reste = (budget - total_ce_jour) if budget is not None else None

        num_facture = getattr(self, "numero_facture", None) or f"FAC-{self.pk}"
        mode_paiement = getattr(self, "get_type_versement_display", lambda: str(self.type_versement).title())()
        ref_paiement  = getattr(self, "reference_paiement", None) or "—"

        # ── Images ────────────────────────────────────────────────────────
        base  = Path(settings.BASE_DIR)
        logo  = _safe_img(base / "logos" / "lamane_logo.png",       w=3.2*cm, h=3.2*cm)
        sign  = _safe_img(base / "logos" / "lamane_signature.png",  w=4*cm,   h=2.5*cm)
        stamp = _safe_img(base / "logos" / "lamane_cachet.png",     w=3.5*cm, h=3.5*cm)

        # ── Document ──────────────────────────────────────────────────────
        buf = BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=A4,
            leftMargin=1.8*cm, rightMargin=1.8*cm,
            topMargin=1.5*cm, bottomMargin=2.2*cm,
            title=f"Reçu de Versement – {self.projet.nom}",
        )
        W = A4[0] - 3.6*cm  # usable width

        # ── Styles ────────────────────────────────────────────────────────
        S = getSampleStyleSheet()
        def sty(name, **kw):
            base_sty = S.get(name, S["Normal"])
            return ParagraphStyle(
                f"_lm_{name}_{id(kw)}", parent=base_sty, **kw
            )

        body   = sty("Normal",    fontSize=9,  leading=13, textColor=colors.HexColor("#1e293b"))
        small  = sty("Normal",    fontSize=8,  leading=11, textColor=MUTED)
        bold   = sty("Normal",    fontSize=9,  leading=13, textColor=colors.HexColor("#1e293b"), fontName="Helvetica-Bold")
        right  = sty("Normal",    fontSize=9,  leading=13, alignment=TA_RIGHT, textColor=colors.HexColor("#1e293b"))
        center = sty("Normal",    fontSize=9,  leading=13, alignment=TA_CENTER)
        h2     = sty("Heading2",  fontSize=10, leading=14, textColor=NAVY, fontName="Helvetica-Bold", spaceAfter=4, spaceBefore=0)
        white_bold = sty("Normal", fontSize=11, fontName="Helvetica-Bold", textColor=WHITE, leading=15)
        white_sm   = sty("Normal", fontSize=8,  textColor=colors.HexColor("#cbd5e1"), leading=11)
        gold_big   = sty("Normal", fontSize=20, fontName="Helvetica-Bold", textColor=GOLD, alignment=TA_CENTER, leading=26)
        gold_lbl   = sty("Normal", fontSize=8,  textColor=MUTED, alignment=TA_CENTER, leading=11, fontName="Helvetica-Bold")

        story = []

        # ════════════════════════════════════════════════════════════════
        # 1. HEADER  (logo | company info | document badge)
        # ════════════════════════════════════════════════════════════════
        company_info = [
            Paragraph("<b>LAMANE CONSTRUCTION & GESTION</b>", white_bold),
            Spacer(1, 3),
            Paragraph("Dakar, Sénégal  ·  (+221) 77 000 00 00", white_sm),
            Paragraph("contact@lamane.sn  ·  www.lamane.sn", white_sm),
            Paragraph("NINEA : 00000000 0A1", white_sm),
        ]
        doc_badge = [
            Paragraph("<b><font size=18 color='#f0a500'>REÇU DE</font></b>", right),
            Paragraph("<b><font size=18 color='#f0a500'>VERSEMENT</font></b>", right),
            Spacer(1, 6),
            Paragraph(f"<font size=9 color='#94a3b8'>N° </font><b><font size=11 color='white'>{num_facture}</font></b>", right),
            Paragraph(f"<font size=8 color='#94a3b8'>Date : {self.date_versement.strftime('%d %B %Y')}</font>", right),
        ]

        logo_cell   = logo if logo else Paragraph("", body)
        header_data = [[logo_cell, company_info, doc_badge]]
        header = Table(header_data, colWidths=[3.5*cm, 8.5*cm, 5.5*cm])
        header.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), NAVY),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING",    (0,0), (-1,-1), 14),
            ("BOTTOMPADDING", (0,0), (-1,-1), 14),
            ("LEFTPADDING",   (0,0), (0,-1),  12),
            ("LEFTPADDING",   (1,0), (1,-1),  8),
            ("RIGHTPADDING",  (-1,0),(-1,-1), 14),
            ("LINEAFTER",     (0,0), (0,-1),  0.5, colors.HexColor("#1e3a5f")),
        ]))
        story.append(header)

        # Gold accent stripe
        story.append(Table([[""]], colWidths=[W], rowHeights=[4]))
        story[-1].setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1), GOLD)]))
        story.append(Spacer(1, 14))

        # ════════════════════════════════════════════════════════════════
        # 2. AMOUNT HIGHLIGHT BOX
        # ════════════════════════════════════════════════════════════════
        amount_box = Table(
            [[Paragraph("MONTANT DU VERSEMENT", gold_lbl)],
             [Paragraph(_fmt(self.montant), gold_big)]],
            colWidths=[W]
        )
        amount_box.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), LIGHT),
            ("LINEABOVE",     (0,0), (-1,0),  2, GOLD),
            ("LINEBELOW",     (0,-1),(-1,-1), 2, GOLD),
            ("TOPPADDING",    (0,0), (-1,-1), 10),
            ("BOTTOMPADDING", (0,0), (-1,-1), 10),
            ("LEFTPADDING",   (0,0), (-1,-1), 0),
            ("RIGHTPADDING",  (0,0), (-1,-1), 0),
        ]))
        story.append(amount_box)
        story.append(Spacer(1, 18))

        # ════════════════════════════════════════════════════════════════
        # 3. CLIENT  |  PROJET  (two-column info block)
        # ════════════════════════════════════════════════════════════════
        try:
            client_name = self.projet.proprietaire.nom_complet()
            try: client_tel  = self.projet.proprietaire.telephone or ""
            except: client_tel = ""
            try: client_addr = self.projet.proprietaire.adresse or ""
            except: client_addr = ""
        except Exception:
            client_name = "—"
            client_tel = client_addr = ""

        phase_str = self.phase.libelle if self.phase else "—"
        etape_str = self.etape.nom    if self.etape  else "—"

        left_col = [
            Paragraph("CLIENT", sty("Normal", fontSize=8, fontName="Helvetica-Bold",
                                    textColor=WHITE, leading=11)),
            Spacer(1, 4),
            Paragraph(f"<b>{client_name}</b>", body),
        ]
        if client_tel:
            left_col.append(Paragraph(f"Tél : {client_tel}", small))
        if client_addr:
            left_col.append(Paragraph(client_addr, small))

        right_col = [
            Paragraph("PROJET", sty("Normal", fontSize=8, fontName="Helvetica-Bold",
                                    textColor=WHITE, leading=11)),
            Spacer(1, 4),
            Paragraph(f"<b>{self.projet.nom}</b>", body),
            Paragraph(f"Phase : {phase_str}", small),
            Paragraph(f"Étape : {etape_str}", small),
            Paragraph(f"Localisation : {getattr(self.projet,'localisation','')}", small),
        ]

        info_tbl = Table([[left_col, right_col]], colWidths=[W/2, W/2])
        info_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (0,-1), NAVY),
            ("BACKGROUND",    (1,0), (1,-1), BLUE),
            ("VALIGN",        (0,0), (-1,-1), "TOP"),
            ("TOPPADDING",    (0,0), (-1,-1), 12),
            ("BOTTOMPADDING", (0,0), (-1,-1), 12),
            ("LEFTPADDING",   (0,0), (-1,-1), 14),
            ("RIGHTPADDING",  (0,0), (-1,-1), 14),
            ("LINEBEFORE",    (1,0), (1,-1), 0.5, colors.HexColor("#1e5a8f")),
            ("ROUNDEDCORNERS", [6]),
        ]))
        story.append(info_tbl)
        story.append(Spacer(1, 18))

        # ════════════════════════════════════════════════════════════════
        # 4. PAYMENT DETAILS TABLE
        # ════════════════════════════════════════════════════════════════
        story.append(Paragraph("DÉTAIL DU PAIEMENT", h2))
        story.append(HRFlowable(width=W, thickness=1.5, color=NAVY, spaceAfter=8))

        detail_data = [
            [Paragraph("<b>Description</b>", bold),    Paragraph("<b>Valeur</b>", bold)],
            [Paragraph("Mode de paiement", body),      Paragraph(mode_paiement, right)],
            [Paragraph("Date du versement", body),     Paragraph(self.date_versement.strftime("%d/%m/%Y"), right)],
            [Paragraph("Référence / N° transaction", body), Paragraph(ref_paiement, right)],
            [Paragraph("Phase de versement", body),    Paragraph(phase_str, right)],
            [Paragraph("Montant versé", sty("Normal", fontSize=10, fontName="Helvetica-Bold", textColor=GREEN)),
             Paragraph(f"<b><font color='#059669'>{_fmt(self.montant)}</font></b>", right)],
        ]
        detail_tbl = Table(detail_data, colWidths=[9*cm, W-9*cm])
        detail_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0),  NAVY),
            ("TEXTCOLOR",     (0,0), (-1,0),  WHITE),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, LIGHT]),
            ("LINEBELOW",     (0,0), (-1,-1), 0.5, BORDER),
            ("TOPPADDING",    (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ("LEFTPADDING",   (0,0), (-1,-1), 10),
            ("RIGHTPADDING",  (0,0), (-1,-1), 10),
            ("ALIGN",         (1,0), (1,-1),  "RIGHT"),
            ("BOX",           (0,0), (-1,-1), 0.8, BORDER),
            ("LINEBELOW",     (0,-1),(-1,-1), 1.5, NAVY),
        ]))
        story.append(detail_tbl)
        story.append(Spacer(1, 18))

        # ════════════════════════════════════════════════════════════════
        # 5. FINANCIAL SUMMARY
        # ════════════════════════════════════════════════════════════════
        story.append(Paragraph("RÉCAPITULATIF FINANCIER", h2))
        story.append(HRFlowable(width=W, thickness=1.5, color=NAVY, spaceAfter=8))

        recap_data = [
            [Paragraph("Versements antérieurs", body),
             Paragraph(_fmt(total_anterieur), right)],
            [Paragraph("Ce versement", body),
             Paragraph(f"<b>{_fmt(self.montant)}</b>", right)],
            [Paragraph("<b>Total versé à ce jour</b>",
                       sty("Normal", fontSize=10, fontName="Helvetica-Bold", textColor=NAVY)),
             Paragraph(f"<b><font color='#0f2547'>{_fmt(total_ce_jour)}</font></b>", right)],
        ]
        if reste is not None:
            color_reste = "#dc2626" if reste > 0 else "#059669"
            recap_data.append([
                Paragraph("Reste à payer", body),
                Paragraph(f"<b><font color='{color_reste}'>{_fmt(reste)}</font></b>", right),
            ])
        if budget:
            recap_data.insert(0, [
                Paragraph("Budget / Montant contrat", body),
                Paragraph(_fmt(budget), right),
            ])

        recap_tbl = Table(recap_data, colWidths=[10*cm, W-10*cm])
        recap_tbl.setStyle(TableStyle([
            ("LINEBELOW",     (0,0), (-1,-1), 0.5, BORDER),
            ("BACKGROUND",    (0,-2),(-1,-2), LIGHT),
            ("FONTNAME",      (0,-2),(-1,-2), "Helvetica-Bold"),
            ("TOPPADDING",    (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ("LEFTPADDING",   (0,0), (-1,-1), 10),
            ("RIGHTPADDING",  (0,0), (-1,-1), 10),
            ("ALIGN",         (1,0), (1,-1),  "RIGHT"),
            ("BOX",           (0,0), (-1,-1), 0.8, BORDER),
            ("LINEABOVE",     (0,-2),(-1,-2), 1.5, NAVY),
            ("LINEBELOW",     (0,-1),(-1,-1), 1.5, NAVY),
        ]))
        story.append(recap_tbl)
        story.append(Spacer(1, 26))

        # ════════════════════════════════════════════════════════════════
        # 6. SIGNATURE & STAMP BLOCK
        # ════════════════════════════════════════════════════════════════
        story.append(HRFlowable(width=W, thickness=0.5, color=BORDER, spaceAfter=12))

        sig_left = [
            Paragraph("<b>Approuvé par :</b>", body),
            Spacer(1, 6),
            Paragraph("<b>Direction Générale</b>", h2),
            Paragraph("LAMANE Construction & Gestion", small),
            Spacer(1, 8),
        ]
        if sign:
            sig_left.append(sign)

        sig_right = []
        if stamp:
            sig_right.append(stamp)
        else:
            sig_right.append(Paragraph("", body))

        sig_tbl = Table([[sig_left, sig_right]], colWidths=[W*0.6, W*0.4])
        sig_tbl.setStyle(TableStyle([
            ("VALIGN",       (0,0),(-1,-1), "TOP"),
            ("ALIGN",        (1,0),(1,-1),  "CENTER"),
            ("LINEAFTER",    (0,0),(0,-1),  0.5, BORDER),
            ("TOPPADDING",   (0,0),(-1,-1), 0),
            ("BOTTOMPADDING",(0,0),(-1,-1), 0),
        ]))
        story.append(sig_tbl)

        # ════════════════════════════════════════════════════════════════
        # 7. FOOTER (canvas — drawn outside story)
        # ════════════════════════════════════════════════════════════════
        site_url = getattr(settings, "SITE_URL", "http://127.0.0.1:8000")
        try:
            qrw = qr.QrCodeWidget(f"{site_url}/versements/{self.pk}/")
            b   = qrw.getBounds()
            qw, qh = b[2]-b[0], b[3]-b[1]
            qd  = Drawing(2*cm, 2*cm, transform=[2*cm/qw, 0, 0, 2*cm/qh, 0, 0])
            qd.add(qrw)
            qr_available = True
        except Exception:
            qr_available = False

        def on_page(canvas, _doc):
            canvas.saveState()
            # Bottom bar
            canvas.setFillColor(NAVY)
            canvas.rect(0, 0, A4[0], 1.8*cm, fill=1, stroke=0)
            # Gold line above footer
            canvas.setFillColor(GOLD)
            canvas.rect(0, 1.8*cm, A4[0], 3, fill=1, stroke=0)
            # Footer text
            canvas.setFont("Helvetica", 7.5)
            canvas.setFillColor(colors.HexColor("#94a3b8"))
            canvas.drawString(1.8*cm, 0.9*cm,
                f"Document généré le {self.date_versement.strftime('%d/%m/%Y')}  |  "
                f"Réf : {num_facture}  |  Ce document est valide sans signature manuscrite si muni du cachet officiel.")
            # QR code
            if qr_available:
                try:
                    renderPDF.draw(qd, canvas, A4[0]-2.6*cm, 0.2*cm)
                except Exception:
                    pass
            canvas.restoreState()

        doc.build(story, onFirstPage=on_page, onLaterPages=on_page)

        filename = f"recu_versement_{self.projet.nom}_{self.date_versement.strftime('%Y%m%d')}_{self.pk}.pdf"
        self.facture_pdf.save(filename, ContentFile(buf.getvalue()), save=False)
        buf.close()
