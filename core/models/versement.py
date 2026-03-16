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

        super().save(*args, **kwargs)

        if not self.facture_pdf:
            try:
                self.generate_facture_pdf()
                super().save(update_fields=['facture_pdf'])
            except Exception as e:
                import traceback
                print("[FACTURE] Erreur de génération:", e)
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
        # ---------- HELPERS ----------
        def _fmt_cfa(n):
            try:
                return f"{int(n):,}".replace(",", " ") + " FCFA"
            except Exception:
                return f"{n} FCFA"

        from pathlib import Path
        from io import BytesIO
        from django.core.files.base import ContentFile
        from django.conf import settings
        from django.db.models import Sum
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_RIGHT
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
        from reportlab.graphics.barcode import qr
        from reportlab.graphics.shapes import Drawing
        from reportlab.graphics import renderPDF

        def _safe_img(path, w=None, h=None):
            try:
                p = Path(path)
                if p.exists():
                    return Image(str(p), width=w, height=h, kind="proportional")
            except Exception:
                pass
            return None

        # ---------- DONNÉES MÉTIER (comme ta 1ère facture) ----------
        # cumul avant CE versement (sur même projet, jusqu'à la date courante exclue)
        total_anterieur = (
            self.__class__
            .objects.filter(projet=self.projet, date_versement__lt=self.date_versement)
            .aggregate(s=Sum("montant"))["s"] or 0
        )
        total_verse_ce_jour = total_anterieur + (self.montant or 0)

        # budget/contrat du projet si présent (on essaie plusieurs noms possibles)
        budget = None
        for attr in ("budget", "montant_total", "cout_previsionnel", "montant_marche"):
            if hasattr(self.projet, attr) and getattr(self.projet, attr):
                budget = getattr(self.projet, attr)
                break
        reste = (budget - total_verse_ce_jour) if budget is not None else None

        # ---------- DOC & STYLES ----------
        buf = BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=A4,
            leftMargin=2*cm, rightMargin=2*cm, topMargin=1.5*cm, bottomMargin=2*cm,
            title=f"Facture de Versement - {self.projet.nom}",
        )
        S = getSampleStyleSheet()
        P = S["BodyText"]; P.fontSize = 10; P.leading = 14
        small = ParagraphStyle("small", parent=P, fontSize=9, textColor=colors.HexColor("#6b7280"))
        right = ParagraphStyle("right", parent=P, alignment=TA_RIGHT)
        head  = ParagraphStyle("head", parent=S["Heading2"], textColor=colors.HexColor("#2f6f8f"), spaceAfter=8)

        # ---------- IMAGES (optionnelles) ----------
        base = Path(settings.BASE_DIR)
        logo      = _safe_img(base / "logos" / "lamane_logo.png",      w=2.5*cm, h=2.5*cm)
        sign      = _safe_img(base / "logos" / "lamane_signature.png", w=3.5*cm, h=2*cm)
        stamp     = _safe_img(base / "logos" / "lamane_cachet.png",    w=3*cm,   h=3*cm)

        # ---------- HEADER STYLÉ (bleu) + infos facture (NUMÉRO + DATE) ----------
        header_table = Table(
            [[logo,
            Paragraph("<b><font color='white' size=14>FACTURE DE VERSEMENT</font></b>", right)]],
            colWidths=[5*cm, 11*cm]
        )
        header_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#2f6f8f")),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("TEXTCOLOR", (0,0), (-1,-1), colors.white),
            ("BOTTOMPADDING", (0,0), (-1,-1), 12),
            ("TOPPADDING", (0,0), (-1,-1), 12),
        ]))

        fac_infos = Table(
            [[Paragraph(f"<b>N° facture :</b> {getattr(self, 'numero_facture', '')}", P),
            Paragraph(f"<b>Date :</b> {self.date_versement.strftime('%d/%m/%Y')}", right)]],
            colWidths=[8*cm, 8*cm]
        )
        fac_infos.setStyle(TableStyle([
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("LINEBELOW", (0,0), (-1,0), 0.6, colors.HexColor("#e5e7eb")),
        ]))

        # ---------- CLIENT / PROJET (avec Phase & Étape comme avant) ----------
        client = [
            Paragraph("<b>Client</b>", head),
            Paragraph(self.projet.proprietaire.nom_complet(), P),
        ]
        projet_lines = [
            Paragraph("<b>Projet</b>", head),
            Paragraph(self.projet.nom, P),
        ]
        if self.phase:
            projet_lines.append(Paragraph(f"Phase : {self.phase.libelle}", small))
        if self.etape:
            projet_lines.append(Paragraph(f"Étape : {self.etape.nom}", small))
        cp = Table([[client, projet_lines]], colWidths=[8*cm, 8*cm])
        cp.setStyle(TableStyle([
            ("BOX", (0,0), (-1,-1), 1, colors.HexColor("#e5e7eb")),
            ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#e9f2f7")),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("TOPPADDING", (0,0), (-1,-1), 8),
            ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ]))

        # ---------- DÉTAIL DU VERSEMENT (toutes les infos de la 1ère facture) ----------
        rows = [
            ["Montant payé",       _fmt_cfa(self.montant)],
            ["Mode de paiement",   getattr(self, "get_type_versement_display", lambda: str(self.type_versement).title())()],
            ["Date du paiement",   self.date_versement.strftime("%d/%m/%Y")],
            ["Référence paiement", getattr(self, "reference_paiement", None) or "-"],
        ]
        detail = Table(rows, colWidths=[6*cm, 10*cm])
        detail.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e5e7eb")),
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e9f2f7")),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.white]),
            ("ALIGN", (1,0), (1,-1), "LEFT"),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ]))

        # ---------- RÉCAP (avec cumul & reste à payer comme ta 1ère version) ----------
        recap_rows = [
            ["Total déjà versé avant ce paiement", _fmt_cfa(total_anterieur)],
            ["Montant de ce versement",            _fmt_cfa(self.montant)],
            ["Total versé à ce jour",              _fmt_cfa(total_verse_ce_jour)],
            ["Reste à payer",                      (_fmt_cfa(reste) if reste is not None else "-")],
        ]
        recap = Table(recap_rows, colWidths=[9*cm, 7*cm])
        recap.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.6, colors.HexColor("#e5e7eb")),
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e9f2f7")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.HexColor("#2f6f8f")),
            ("ALIGN", (1,0), (1,-1), "RIGHT"),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ]))

        # ---------- SIGNATURE & CACHET (comme ta 2ᵉ version) ----------
        sign_title = Paragraph("<b>LAMANE</b>", head)
        
        
            # ---------- SIGNATURE & CACHET côte à côte ----------
        #sign_title = Paragraph("<b>Signature & Cachet</b>", head)

        # contenu gauche : texte + signature + cachet alignés horizontalement
        left_items = [Paragraph("", P), Spacer(1, 6)]
        img_row = []
        if sign:
            img_row.append(sign)
        if stamp:
            img_row.append(stamp)
        if img_row:
            left_items.append(Table([img_row], style=[("VALIGN", (0,0), (-1,-1), "BOTTOM")]))

        sign_block = Table([[left_items]], colWidths=[16*cm])
        sign_block.setStyle(TableStyle([
            ("VALIGN", (0,0), (-1,-1), "TOP"),
        ]))


        # ---------- FOOTER avec QR (vers admin de l’objet) ----------
        site_url = getattr(settings, "SITE_URL", "http://127.0.0.1:8000")
        qrw = qr.QrCodeWidget(f"{site_url}/admin/core/versement/{self.pk}/change/")
        b = qrw.getBounds(); w, h = b[2]-b[0], b[3]-b[1]
        d = Drawing(2.5*cm, 2.5*cm, transform=[2.5*cm/w,0,0,2.5*cm/h,0,0]); d.add(qrw)

        def footer(canvas, _doc):
            canvas.saveState()
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(colors.grey)
            canvas.drawString(2*cm, 1.5*cm, f"Facture générée le {self.date_versement.strftime('%d/%m/%Y')}")
            renderPDF.draw(d, canvas, A4[0]-2*cm-2.5*cm, 1.2*cm)
            canvas.restoreState()

        # ---------- BUILD ----------
        story = [
            header_table, Spacer(1, 10),
            fac_infos, Spacer(1, 14),
            cp, Spacer(1, 16),
            Paragraph("<b>Détail du versement</b>", head),
            detail, Spacer(1, 18),
            Paragraph("<b>Récapitulatif</b>", head),
            recap, Spacer(1, 26),
            sign_title, Spacer(1, 6),
            sign_block,
        ]
        doc.build(story, onFirstPage=footer, onLaterPages=footer)

        filename = f"facture_{self.projet.nom}_{self.date_versement.strftime('%Y%m%d')}.pdf"
        self.facture_pdf.save(filename, ContentFile(buf.getvalue()), save=False)
        buf.close()
