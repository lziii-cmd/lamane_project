# Generated migration — BonSortie, LigneBonSortie + bon_entree_pdf sur Achat
import uuid
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_nouveaux_modeles_btp'),
    ]

    operations = [

        # ── BonSortie ──────────────────────────────────────────────────────
        migrations.CreateModel(
            name='BonSortie',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('reference', models.CharField(blank=True, help_text='Auto-générée (ex: BS-2025-001)', max_length=30, unique=True, verbose_name='Référence')),
                ('date_sortie', models.DateField(default=django.utils.timezone.now, verbose_name='Date de sortie')),
                ('responsable', models.CharField(blank=True, max_length=100, verbose_name='Responsable de la sortie')),
                ('observations', models.TextField(blank=True, verbose_name='Observations')),
                ('bon_pdf', models.FileField(blank=True, null=True, upload_to='bons_sortie/', verbose_name='Bon de sortie PDF')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('projet', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='bons_sortie',
                    to='core.projet',
                    verbose_name='Projet / Chantier',
                )),
            ],
            options={
                'verbose_name': 'Bon de sortie',
                'verbose_name_plural': 'Bons de sortie',
                'ordering': ['-date_sortie'],
            },
        ),

        # ── LigneBonSortie ─────────────────────────────────────────────────
        migrations.CreateModel(
            name='LigneBonSortie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantite', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Quantité')),
                ('commentaire', models.CharField(blank=True, max_length=200, verbose_name='Commentaire')),
                ('bon', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='lignes',
                    to='core.bonsortie',
                    verbose_name='Bon de sortie',
                )),
                ('materiel', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='sorties',
                    to='core.materiel',
                    verbose_name='Matériau',
                )),
            ],
            options={
                'verbose_name': 'Ligne bon de sortie',
                'verbose_name_plural': 'Lignes bon de sortie',
            },
        ),

        # ── bon_entree_pdf sur Achat ────────────────────────────────────────
        migrations.AddField(
            model_name='achat',
            name='bon_entree_pdf',
            field=models.FileField(
                blank=True, null=True,
                upload_to='bons_entree/',
                verbose_name="Bon d'entrée PDF"
            ),
        ),
    ]
