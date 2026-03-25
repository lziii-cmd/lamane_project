# Generated migration — Nouveaux modèles BTP / Finance / Comptabilité
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_etapestandard_groupe'),
    ]

    operations = [
        # ── MarcheTravaux ──────────────────────────────────────────────────
        migrations.CreateModel(
            name='MarcheTravaux',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_marche', models.CharField(max_length=50, unique=True, verbose_name='N° Marché')),
                ('objet', models.TextField(blank=True, verbose_name='Objet du marché')),
                ('montant_marche', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=16, verbose_name='Montant du marché (FCFA HT)')),
                ('montant_avance_demarrage', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text="Avance versée au démarrage (généralement 20-30% du marché).", max_digits=14, verbose_name='Avance de démarrage (FCFA)')),
                ('taux_retenue_garantie', models.DecimalField(decimal_places=2, default=Decimal('5.00'), help_text='Prélevée sur chaque situation de travaux (standard : 5%).', max_digits=5, verbose_name='Taux retenue de garantie (%)')),
                ('penalite_journaliere_pct', models.DecimalField(decimal_places=4, default=Decimal('0.0500'), help_text='% du montant du marché par jour de retard (norme CCAG : 0,05%).', max_digits=5, verbose_name='Pénalité journalière (%)')),
                ('plafond_penalites_pct', models.DecimalField(decimal_places=2, default=Decimal('10.00'), help_text='Plafond des pénalités exprimé en % du montant du marché.', max_digits=5, verbose_name='Plafond pénalités (%)')),
                ('date_signature', models.DateField(blank=True, null=True, verbose_name='Date de signature')),
                ('date_ordre_service', models.DateField(blank=True, null=True, verbose_name="Date ordre de service")),
                ('delai_execution_jours', models.PositiveIntegerField(default=365, verbose_name="Délai d'exécution (jours calendaires)")),
                ('statut', models.CharField(choices=[('en_attente', 'En attente de signature'), ('signe', 'Signé'), ('en_cours', "En cours d'exécution"), ('reception_provisoire', 'Réception provisoire'), ('reception_definitive', 'Réception définitive'), ('resilie', 'Résilié')], default='en_attente', max_length=30, verbose_name='Statut')),
                ('date_reception_provisoire', models.DateField(blank=True, null=True, verbose_name='Date réception provisoire')),
                ('date_reception_definitive', models.DateField(blank=True, null=True, verbose_name='Date réception définitive')),
                ('observations', models.TextField(blank=True, verbose_name='Observations')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('projet', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='marche', to='core.projet', verbose_name='Projet')),
            ],
            options={'verbose_name': 'Marché de travaux', 'verbose_name_plural': 'Marchés de travaux', 'ordering': ['-date_signature']},
        ),

        # ── AvancementChantier ──────────────────────────────────────────────
        migrations.CreateModel(
            name='AvancementChantier',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('periode', models.DateField(help_text='Date représentant le mois concerné (toujours le 1er du mois).', verbose_name='Période (1er du mois)')),
                ('taux_physique', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='Avancement physique (%)')),
                ('taux_financier', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='Avancement financier (%)')),
                ('taux_planifie', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='Avancement planifié (%)')),
                ('effectif_ouvriers', models.PositiveIntegerField(default=0, verbose_name='Effectif ouvriers')),
                ('effectif_encadrement', models.PositiveIntegerField(default=0, verbose_name='Effectif encadrement')),
                ('observations', models.TextField(blank=True, verbose_name='Observations techniques')),
                ('incidents', models.TextField(blank=True, verbose_name='Incidents / Non-conformités')),
                ('mesures_correctives', models.TextField(blank=True, verbose_name='Mesures correctives')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('projet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='avancements', to='core.projet', verbose_name='Projet')),
            ],
            options={'verbose_name': 'Avancement chantier', 'verbose_name_plural': 'Avancements chantier', 'ordering': ['projet', '-periode'], 'unique_together': {('projet', 'periode')}},
        ),

        # ── SousTraitant ──────────────────────────────────────────────────
        migrations.CreateModel(
            name='SousTraitant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=200, unique=True, verbose_name='Raison sociale / Nom')),
                ('specialite', models.CharField(choices=[('gros_oeuvre', 'Gros œuvre'), ('charpente_couverture', 'Charpente / Couverture'), ('plomberie_sanitaire', 'Plomberie / Sanitaire'), ('electricite_cfa', 'Électricité / CFA'), ('menuiserie_bois', 'Menuiserie Bois'), ('menuiserie_alu', 'Menuiserie Aluminium'), ('carrelage_faience', 'Carrelage / Faïence'), ('peinture_revetement', 'Peinture / Revêtement'), ('climatisation', 'Climatisation / Ventilation'), ('ascenseur', 'Ascenseur / Élévation'), ('piscine', 'Piscine / Traitement de l\'eau'), ('panneaux_solaires', 'Énergie Solaire'), ('vrd', 'VRD / Terrassement'), ('domotique', 'Domotique / Smart Building'), ('autre', 'Autre')], default='autre', max_length=30, verbose_name='Spécialité principale')),
                ('ninea', models.CharField(blank=True, max_length=20, verbose_name='NINEA')),
                ('telephone', models.CharField(blank=True, max_length=20, verbose_name='Téléphone')),
                ('email', models.EmailField(blank=True, verbose_name='Email')),
                ('adresse', models.CharField(blank=True, max_length=255, verbose_name='Adresse')),
                ('contact_nom', models.CharField(blank=True, max_length=100, verbose_name='Nom du contact')),
                ('actif', models.BooleanField(default=True, verbose_name='Actif')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'Sous-traitant', 'verbose_name_plural': 'Sous-traitants', 'ordering': ['nom']},
        ),

        # ── ContratSousTraitance ──────────────────────────────────────────
        migrations.CreateModel(
            name='ContratSousTraitance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lot', models.CharField(help_text='Ex : Lot 3 - Plomberie sanitaire RDC+R+1', max_length=200, verbose_name='Lot / Désignation')),
                ('montant', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=14, verbose_name='Montant du contrat (FCFA)')),
                ('montant_paye', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=14, verbose_name='Montant déjà payé (FCFA)')),
                ('date_debut', models.DateField(blank=True, null=True, verbose_name='Date de début')),
                ('date_fin_prevue', models.DateField(blank=True, null=True, verbose_name='Date de fin prévue')),
                ('date_fin_reelle', models.DateField(blank=True, null=True, verbose_name='Date de fin réelle')),
                ('statut', models.CharField(choices=[('en_cours', 'En cours'), ('termine', 'Terminé'), ('suspendu', 'Suspendu'), ('resilie', 'Résilié')], default='en_cours', max_length=20, verbose_name='Statut')),
                ('observations', models.TextField(blank=True, verbose_name='Observations')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('projet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contrats_sous_traitance', to='core.projet', verbose_name='Projet')),
                ('sous_traitant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='contrats', to='core.soustraitant', verbose_name='Sous-traitant')),
            ],
            options={'verbose_name': 'Contrat de sous-traitance', 'verbose_name_plural': 'Contrats de sous-traitance', 'ordering': ['projet', 'sous_traitant']},
        ),

        # ── SituationMensuelle ────────────────────────────────────────────
        migrations.CreateModel(
            name='SituationMensuelle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_situation', models.PositiveIntegerField(default=1, help_text='Numéro séquentiel de la situation (Situation N°1, N°2, etc.).', verbose_name='N° Situation')),
                ('periode', models.DateField(help_text='Mois de situation (toujours le 1er du mois).', verbose_name='Période (1er du mois)')),
                ('montant_brut_cumule', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=16, verbose_name='Montant brut cumulé HT (FCFA)')),
                ('taux_avancement', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name="Taux d'avancement (%)")),
                ('retenue_garantie', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=14, verbose_name='Retenue de garantie (FCFA)')),
                ('montant_net_cumule', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=16, verbose_name='Montant net cumulé HT (FCFA)')),
                ('montant_precedentes_situations', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=16, verbose_name='Montant situations précédentes (FCFA)')),
                ('montant_a_payer', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=16, verbose_name='Montant à payer cette situation (FCFA)')),
                ('statut', models.CharField(choices=[('brouillon', 'Brouillon'), ('soumise', "Soumise au maître d'ouvrage"), ('validee', 'Validée'), ('rejetee', 'Rejetée'), ('payee', 'Payée')], default='brouillon', max_length=20, verbose_name='Statut')),
                ('date_soumission', models.DateField(blank=True, null=True, verbose_name='Date de soumission')),
                ('date_validation', models.DateField(blank=True, null=True, verbose_name='Date de validation')),
                ('observations', models.TextField(blank=True, verbose_name='Observations / Réserves')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('projet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='situations_mensuelles', to='core.projet', verbose_name='Projet')),
            ],
            options={'verbose_name': 'Situation mensuelle', 'verbose_name_plural': 'Situations mensuelles', 'ordering': ['projet', 'numero_situation'], 'unique_together': {('projet', 'numero_situation')}},
        ),
    ]
