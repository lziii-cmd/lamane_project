"""
Management command: genere tous les PDFs manquants
(bons d'entree achats, contrats sous-traitance, factures versement).
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Genere les PDFs manquants pour achats, contrats ST et versements"

    def handle(self, *args, **options):
        from core.models import Achat, Versement, ContratSousTraitance

        # ── 1. Bons d'entree achats ─────────────────────────────────────
        achats = Achat.objects.filter(bon_entree_pdf="")
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"Achats sans bon d'entree PDF: {achats.count()}")
        ok, err = 0, 0
        for a in achats:
            try:
                a.generate_bon_entree_pdf()
                ok += 1
            except Exception as e:
                err += 1
                self.stderr.write(f"  ERREUR achat {a.pk}: {e}")
        self.stdout.write(self.style.SUCCESS(f"  Generes: {ok}, Erreurs: {err}"))

        # ── 2. Contrats sous-traitance ──────────────────────────────────
        contrats = ContratSousTraitance.objects.filter(contrat_pdf="")
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"Contrats ST sans PDF: {contrats.count()}")
        ok, err = 0, 0
        for c in contrats:
            try:
                c.generate_contrat_pdf()
                c.save()
                ok += 1
            except Exception as e:
                err += 1
                self.stderr.write(f"  ERREUR contrat {c.pk}: {e}")
        self.stdout.write(self.style.SUCCESS(f"  Generes: {ok}, Erreurs: {err}"))

        # ── 3. Factures versements ──────────────────────────────────────
        versements = Versement.objects.filter(facture_pdf="")
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"Versements sans facture PDF: {versements.count()}")
        ok, err = 0, 0
        for v in versements:
            try:
                v.generate_facture_pdf()
                v.save(update_fields=["facture_pdf"])
                ok += 1
            except Exception as e:
                err += 1
                self.stderr.write(f"  ERREUR versement {v.pk}: {e}")
        self.stdout.write(self.style.SUCCESS(f"  Generes: {ok}, Erreurs: {err}"))

        self.stdout.write(self.style.SUCCESS(f"\n{'='*60}\nTermine!"))
