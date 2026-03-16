# scripts/load_categories_materiels.py
from core.models.categorie_materiel import CategorieMateriel

categories = [
    "Ciment",
    "Béton et Agrégats",
    "Ferraillage",
    "Électricité",
    "Plomberie",
    "Menuiserie",
    "Peinture et Finitions",
    "Isolation",
    "Étanchéité",
    "Revêtement sol et mur",
    "Charpente",
    "Serrurerie",
    "Outils et consommables",
    "Énergie solaire",
]

created_count = 0

for nom in categories:
    obj, created = CategorieMateriel.objects.get_or_create(nom=nom)
    if created:
        created_count += 1

print(f"✅ {created_count} catégories créées (ou déjà existantes ignorées).")
