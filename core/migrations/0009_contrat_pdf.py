# Migration — add contrat_pdf field to ContratSousTraitance
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_alter_avancementchantier_effectif_encadrement_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='contratsoustraitance',
            name='contrat_pdf',
            field=models.FileField(
                blank=True, null=True,
                upload_to='contrats_sous_traitance/',
                verbose_name='Contrat PDF'
            ),
        ),
    ]
