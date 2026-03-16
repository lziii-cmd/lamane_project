# core/signals/versement_signals.py
import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models.versement import Versement
from django.core.files.base import ContentFile
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

def generate_facture_pdf(versement):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"Facture de Versement", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Numéro : {versement.numero_facture}", styles['Normal']))
    elements.append(Paragraph(f"Projet : {versement.projet.nom}", styles['Normal']))
    elements.append(Paragraph(f"Client : {versement.proprietaire}", styles['Normal']))
    elements.append(Paragraph(f"Montant : {versement.montant} FCFA", styles['Normal']))
    elements.append(Paragraph(f"Date : {versement.date_versement}", styles['Normal']))
    elements.append(Paragraph(f"Type : {versement.type_versement}", styles['Normal']))
    if versement.phase:
        elements.append(Paragraph(f"Phase : {versement.phase.nom}", styles['Normal']))

    doc.build(elements)
    pdf_content = buffer.getvalue()
    buffer.close()
    return pdf_content

@receiver(post_save, sender=Versement)
def generate_facture_after_versement(sender, instance, created, **kwargs):
    if created and not instance.facture_pdf:
        latest_number = Versement.objects.count()
        year = instance.date_versement.year
        numero = f"FV-{str(latest_number).zfill(4)}-{year}"
        instance.numero_facture = numero

        content = generate_facture_pdf(instance)
        filename = f"{numero}.pdf"
        instance.facture_pdf.save(filename, ContentFile(content), save=True)
