# core/models/achat.py
import uuid
from decimal import Decimal
from django.db import models
from core.models.projet import Projet
from core.models.fournisseur import Fournisseur

class Achat(models.Model):

    MODE_PAIEMENT_CHOICES = [
        ("espèces", "Espèces"),
        ("virement", "Virement"),
        ("chèque", "Chèque"),
        ("autre", "Autre"),
    ]


    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
        help_text="Identifiant unique global (UUID4)"
    )
    date_creation = models.DateTimeField(auto_now_add=True, help_text="Date de création de l’objet")
    date_modification = models.DateTimeField(auto_now=True, help_text="Date de dernière modification")
    
    date_achat = models.DateField(verbose_name="Date d’achat")
    projet = models.ForeignKey(
        Projet, on_delete=models.CASCADE, related_name="achats"
    )
#    fournisseur = models.CharField("Fournisseur", max_length=255, blank=True)
    fournisseur = models.ForeignKey(
        Fournisseur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Fournisseur",
        related_name="achats"
    )

    #mode_paiement = models.CharField("Mode de paiement", max_length=100)
    mode_paiement = models.CharField(max_length=50, choices=MODE_PAIEMENT_CHOICES)

    numero_facture = models.CharField("N° Facture", max_length=100, blank=True)
    fichier_facture = models.FileField(
        upload_to="achats/factures", verbose_name="Scan Facture", null=True, blank=True
    )
    bon_entree_pdf = models.FileField(
        upload_to="bons_entree/", verbose_name="Bon d'entrée PDF",
        blank=True, null=True
    )

    tva_active = models.BooleanField("TVA active ?", default=False)

    total_ht = models.DecimalField("Total HT", max_digits=12, decimal_places=2, default=0)
    total_tva = models.DecimalField("Montant TVA", max_digits=12, decimal_places=2, default=0)
    total_ttc = models.DecimalField("Total TTC", max_digits=12, decimal_places=2, default=0)

    # ── Suivi échéance fournisseur ──────────────────────────────────────────
    STATUT_PAIEMENT_CHOICES = [
        ("paye", "Payé"),
        ("en_attente", "En attente"),
        ("en_retard", "En retard"),
    ]
    echeance_paiement = models.DateField(
        "Échéance de paiement", null=True, blank=True,
        help_text="Date limite de paiement au fournisseur.",
    )
    statut_paiement = models.CharField(
        "Statut paiement fournisseur", max_length=20,
        choices=STATUT_PAIEMENT_CHOICES, default="paye",
    )

    class Meta:
        verbose_name = "Achat"
        verbose_name_plural = "Achats"
        ordering = ["-date_achat"]

    def __str__(self):
        return f"Achat du {self.date_achat} - {self.projet.nom}"

    def calcul_totaux(self):
        total_ht = sum(l.quantite * l.prix_unitaire for l in self.lignes.all())
        self.total_ht = total_ht
        self.total_tva = total_ht * Decimal("0.18") if self.tva_active else Decimal("0.00")
        self.total_ttc = self.total_ht + self.total_tva

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # save to create ID
        self.calcul_totaux()
        super().save(*args, **kwargs)

    def generate_bon_entree_pdf(self):
        """Génère le bon d'entrée matériaux (appelé après création des lignes)."""
        try:
            from io import BytesIO
            from django.core.files.base import ContentFile
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.units import cm
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_RIGHT, TA_CENTER
        except ImportError:
            return

        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
            leftMargin=2*cm, rightMargin=2*cm,
            topMargin=1.5*cm, bottomMargin=2*cm)
        S = getSampleStyleSheet()
        P = S["BodyText"]; P.fontSize = 10
        right = ParagraphStyle("right", parent=P, alignment=TA_RIGHT)
        head  = ParagraphStyle("head", parent=S["Heading2"],
                                textColor=colors.HexColor("#2f6f8f"), spaceAfter=8)
        center = ParagraphStyle("center", parent=P, alignment=TA_CENTER)

        header = Table(
            [[Paragraph("<b><font color='white' size=14>BON D'ENTRÉE MATÉRIAUX</font></b>", right)]],
            colWidths=[16*cm]
        )
        header.setStyle(TableStyle([
            ("BACKGROUND", (0,0),(-1,-1), colors.HexColor("#1a7a4a")),
            ("VALIGN", (0,0),(-1,-1), "MIDDLE"),
            ("BOTTOMPADDING",(0,0),(-1,-1), 14),
            ("TOPPADDING",(0,0),(-1,-1), 14),
        ]))

        fournisseur_nom = "—"
        if self.fournisseur:
            fournisseur_nom = (self.fournisseur.entreprise
                               if self.fournisseur.est_moral
                               else f"{self.fournisseur.prenom} {self.fournisseur.nom}").strip()

        infos = Table([
            [Paragraph(f"<b>Référence :</b> BE-{self.date_achat.strftime('%Y%m%d')}-{str(self.id)[:6].upper()}", P),
             Paragraph(f"<b>Date :</b> {self.date_achat.strftime('%d/%m/%Y')}", right)],
            [Paragraph(f"<b>Projet :</b> {self.projet.nom}", P),
             Paragraph(f"<b>Fournisseur :</b> {fournisseur_nom}", right)],
            [Paragraph(f"<b>N° Facture :</b> {self.numero_facture or '—'}", P),
             Paragraph(f"<b>Mode paiement :</b> {self.mode_paiement}", right)],
        ], colWidths=[8*cm, 8*cm])
        infos.setStyle(TableStyle([
            ("LINEBELOW", (0,0),(-1,-1), 0.5, colors.HexColor("#e5e7eb")),
            ("TOPPADDING", (0,0),(-1,-1), 6),
            ("BOTTOMPADDING", (0,0),(-1,-1), 6),
        ]))

        rows = [["Matériau", "Unité", "Qté", "P.U. HT (XOF)", "Total HT (XOF)"]]
        for lg in self.lignes.select_related("materiel").all():
            rows.append([
                lg.materiel.nom,
                lg.materiel.unite or "—",
                str(lg.quantite),
                f"{float(lg.prix_unitaire):,.0f}".replace(",", " "),
                f"{float(lg.total_ligne):,.0f}".replace(",", " "),
            ])
        rows.append(["", "", "", "Total HT",
                     f"{float(self.total_ht):,.0f}".replace(",", " ")])
        if self.tva_active:
            rows.append(["", "", "", "TVA 18%",
                         f"{float(self.total_tva):,.0f}".replace(",", " ")])
        rows.append(["", "", "", "TOTAL TTC",
                     f"{float(self.total_ttc):,.0f}".replace(",", " ")])

        table = Table(rows, colWidths=[5*cm, 2.5*cm, 2.5*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0),(-1,0), colors.HexColor("#e9f2f7")),
            ("TEXTCOLOR", (0,0),(-1,0), colors.HexColor("#1a7a4a")),
            ("FONTNAME", (0,0),(-1,0), "Helvetica-Bold"),
            ("GRID", (0,0),(-1,-len(rows)+len(rows)-3), 0.5, colors.HexColor("#e5e7eb")),
            ("ROWBACKGROUNDS", (0,1),(-1,-4), [colors.whitesmoke, colors.white]),
            ("FONTNAME", (3,-1),(-1,-1), "Helvetica-Bold"),
            ("BACKGROUND", (3,-1),(-1,-1), colors.HexColor("#e9f7ee")),
            ("ALIGN", (2,0),(-1,-1), "RIGHT"),
            ("TOPPADDING", (0,0),(-1,-1), 6),
            ("BOTTOMPADDING", (0,0),(-1,-1), 6),
        ]))

        story = [header, Spacer(1,12), infos, Spacer(1,16),
                 Paragraph("<b>Matériaux reçus</b>", head), table]
        doc.build(story)

        fname = f"bon_entree_{self.date_achat.strftime('%Y%m%d')}_{str(self.id)[:8]}.pdf"
        self.bon_entree_pdf.save(fname, ContentFile(buf.getvalue()), save=False)
        buf.close()
        models.Model.save(self, update_fields=["bon_entree_pdf"])
