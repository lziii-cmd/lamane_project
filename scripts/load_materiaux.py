# scripts/load_materiaux.py
from core.models import CategorieMateriel, Materiel
from uuid import uuid4

donnees = {
    "Béton et Agrégats": [
        ("Sable lavé", "m³"),
        ("Gravier concassé 10/14", "m³"),
        ("Béton prêt à l’emploi", "m³"),
        ("Sable de rivière", "m³"),
        ("Gravier roulé 5/15", "m³"),
        ("Béton dosé 350kg", "m³"),
        ("Sable stabilisé", "m³"),
        ("Grave ciment", "m³"),
        ("Béton de propreté", "m³"),
        ("Granulat recyclé", "m³"),
    ],
    "Charpente": [
        ("Poutre en bois 5x15", "m"),
        ("Chevron 4x6", "m"),
        ("Planche 2x20", "m"),
        ("Liteau bois", "m"),
        ("Panne bois", "m"),
        ("Contreplaqué marine", "m²"),
        ("Solive métallique", "m"),
        ("Poutre lamellé-collé", "m"),
        ("Fermette", "unité"),
        ("Tasseau 3x4", "m"),
    ],
    "Ciment": [
        ("Ciment CPJ 45", "sac"),
        ("Ciment CPA 55", "sac"),
        ("Ciment blanc", "sac"),
        ("Ciment prompt", "sac"),
        ("Ciment sulfate résistant", "sac"),
        ("Ciment hydrophobe", "sac"),
        ("Ciment expansif", "sac"),
        ("Ciment à prise rapide", "sac"),
        ("Ciment à faible chaleur", "sac"),
        ("Ciment pouzzolanique", "sac"),
    ],
    "Ferraillage": [
        ("Fer torsadé Ø8", "barre"),
        ("Fer torsadé Ø10", "barre"),
        ("Fer torsadé Ø12", "barre"),
        ("Fer torsadé Ø14", "barre"),
        ("Treillis soudé ST25", "feuille"),
        ("Étrier acier", "unité"),
        ("Fil anneau", "kg"),
        ("Tiges filetées", "m"),
        ("Cadres préfabriqués", "unité"),
        ("Armature en attente", "m"),
    ],
    "Isolation": [
        ("Laine de roche", "m²"),
        ("Polystyrène extrudé", "m²"),
        ("Mousse polyuréthane", "m²"),
        ("Fibre de bois", "m²"),
        ("Liège expansé", "m²"),
        ("Isolant mince multicouche", "m²"),
        ("Bande résiliente", "m"),
        ("Film polyane", "m²"),
        ("Feutre bitumeux", "m²"),
        ("Isolant acoustique", "m²"),
    ],
    "Menuiserie": [
        ("Porte bois intérieur", "unité"),
        ("Fenêtre aluminium", "unité"),
        ("Volet roulant", "unité"),
        ("Tablette fenêtre", "m"),
        ("Châssis fixe alu", "unité"),
        ("Cadre bois massif", "m"),
        ("Coulissant aluminium", "unité"),
        ("Placard mélaminé", "m²"),
        ("Plinthe bois", "m"),
        ("Appui fenêtre béton", "unité"),
    ],
    "Outils et consommables": [
        ("Truelle", "unité"),
        ("Marteau", "unité"),
        ("Pelle ronde", "unité"),
        ("Disque diamant", "unité"),
        ("Gants de chantier", "paire"),
        ("Casque de sécurité", "unité"),
        ("Seau de maçon", "unité"),
        ("Cordeau traceur", "unité"),
        ("Lame cutter", "lot"),
        ("Échafaudage roulant", "unité"),
    ],
    "Peinture et Finitions": [
        ("Peinture acrylique blanche", "pot"),
        ("Sous-couche mur", "pot"),
        ("Enduit lissage", "sac"),
        ("Peinture satinée", "pot"),
        ("Laque glycéro", "pot"),
        ("Peinture façade", "pot"),
        ("Colle carrelage", "sac"),
        ("Joint carrelage", "sac"),
        ("Vernis bois", "litre"),
        ("Primaire d’accrochage", "litre"),
    ],
    "Plomberie": [
        ("Tube PVC Ø100", "m"),
        ("Tube PER rouge Ø16", "m"),
        ("Tube multicouche Ø20", "m"),
        ("Coudes PVC Ø100", "unité"),
        ("Siphon évier", "unité"),
        ("Flexible inox", "m"),
        ("Robinet simple", "unité"),
        ("Mitigeur douche", "unité"),
        ("Réduction PVC", "unité"),
        ("Joint plat", "lot"),
    ],
    "Revêtement sol et mur": [
        ("Carrelage grès cérame 60x60", "m²"),
        ("Faïence murale 25x40", "m²"),
        ("Parquet stratifié", "m²"),
        ("Plinthe assortie", "m"),
        ("Colle carrelage", "sac"),
        ("Sous-couche parquet", "m²"),
        ("Sol vinyle rouleau", "m²"),
        ("Lame PVC clipsable", "m²"),
        ("Mortier de ragréage", "sac"),
        ("Peinture sol garage", "pot"),
    ],
    "Serrurerie": [
        ("Serrure encastrée", "unité"),
        ("Poignée porte alu", "paire"),
        ("Charnière acier", "paire"),
        ("Verrou", "unité"),
        ("Gond à vis", "paire"),
        ("Loquet à bascule", "unité"),
        ("Fer plat 40x5", "m"),
        ("Tube carré 40x40", "m"),
        ("Cornière acier", "m"),
        ("Crémone de fenêtre", "unité"),
    ],
    "Électricité": [
        ("Câble 3G1.5mm²", "m"),
        ("Goulotte 40x40", "m"),
        ("Interrupteur va-et-vient", "unité"),
        ("Prise 2P+T", "unité"),
        ("Boîte d’encastrement", "unité"),
        ("Tableau divisionnaire", "unité"),
        ("Disjoncteur 10A", "unité"),
        ("Gaine ICTA Ø20", "m"),
        ("Spot LED encastrable", "unité"),
        ("Domino électrique", "lot"),
    ],
    "Énergie solaire": [
        ("Panneau 400Wc", "unité"),
        ("Batterie 200Ah", "unité"),
        ("Onduleur hybride 5kW", "unité"),
        ("Régulateur MPPT", "unité"),
        ("Support panneau alu", "unité"),
        ("Câble solaire 6mm²", "m"),
        ("Connecteur MC4", "paire"),
        ("Boîte DC", "unité"),
        ("Fusible DC", "unité"),
        ("Structure triangulaire", "unité"),
    ],
    "Étanchéité": [
        ("Membrane EPDM", "m²"),
        ("Bitume modifié", "rouleau"),
        ("Résine d’étanchéité", "pot"),
        ("Bande d’arase", "m"),
        ("Primaire d’accrochage", "litre"),
        ("Enduit bitumineux", "litre"),
        ("Feutre géotextile", "m²"),
        ("Joint mastic PU", "cartouche"),
        ("Colle étanche", "tube"),
        ("Drain agricole", "m"),
    ],
}

def run():
    total = 0
    for nom_categorie, materiaux in donnees.items():
        try:
            categorie = CategorieMateriel.objects.get(nom=nom_categorie)
        except CategorieMateriel.DoesNotExist:
            print(f"❌ Catégorie inconnue : {nom_categorie}")
            continue
        for nom, unite in materiaux:
            obj, created = Materiel.objects.get_or_create(
                nom=nom,
                defaults={"unite": unite, "categorie": categorie}
            )
            if created:
                print(f"✅ {nom} créé.")
                total += 1
    print(f"🎯 Total : {total} nouveaux matériaux ajoutés.")

# Exécution automatique dans le shell
run()
   