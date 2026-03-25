"""
seed_database.py — Données de test complètes pour LAMANE BTP
Schéma exact vérifié via PRAGMA table_info.

Usage :  python seed_database.py
"""
import sqlite3, os, sys, uuid, datetime, random

DB_PATH = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
if not os.path.exists(DB_PATH):
    print(f"[ERREUR] db.sqlite3 introuvable : {DB_PATH}"); sys.exit(1)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = OFF")
cur = conn.cursor()

def now():   return datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
def uid():   return uuid.uuid4().hex  # 32-char hex sans tirets (format Django)
def last_id(): return cur.lastrowid

def ins(table, **kw):
    cols = ', '.join(f'"{k}"' for k in kw)
    plc  = ', '.join('?' for _ in kw)
    try:
        cur.execute(f'INSERT OR IGNORE INTO "{table}" ({cols}) VALUES ({plc})', list(kw.values()))
        return cur.lastrowid
    except sqlite3.OperationalError as e:
        print(f"  [ERR ins {table}] {e}")
        return None

def gid(table, col, val):
    cur.execute(f'SELECT id FROM "{table}" WHERE "{col}"=?', (val,))
    r = cur.fetchone(); return r[0] if r else None

print("=== LAMANE BTP — Seed Database ===")

# ──────────────────────────────────────────────────────────────────────────────
# 0. NETTOYAGE
# ──────────────────────────────────────────────────────────────────────────────
print("\n[0] Nettoyage…")
for t in ['core_lignebonsortie','core_bonsortie','core_ligneachat','core_achat',
          'core_versement','core_situationmensuelle','core_contratsoustraitance',
          'core_soustraitant','core_marchetravaux','core_avancementchantier',
          'core_phaseversement','core_projetemploye','core_materiel',
          'core_categoriemateriel','core_employe','core_fournisseur',
          'core_projet','core_proprietaire','core_typeprojet','core_etapestandard',
          'core_caracteristique']:
    try: cur.execute(f'DELETE FROM "{t}"')
    except: pass
conn.commit()

# ──────────────────────────────────────────────────────────────────────────────
# 1. TYPES DE PROJETS  (id INT auto, nom, description)
# ──────────────────────────────────────────────────────────────────────────────
print("[1] Types de projets…")
types = [
    ("Villa individuelle",  "Maison individuelle ou villa privée"),
    ("Immeuble collectif",  "R+3 à R+10, résidentiel ou mixte"),
    ("Bâtiment commercial", "Commerce, bureau, centre commercial"),
    ("Équipement public",   "École, hôpital, mairie, mosquée"),
    ("Hôtel & Résidence",   "Complexe hôtelier, résidence touristique"),
]
for nom, desc in types:
    ins('core_typeprojet', nom=nom, description=desc)
conn.commit()
tp_villa = gid('core_typeprojet','nom','Villa individuelle')
tp_imm   = gid('core_typeprojet','nom','Immeuble collectif')
tp_com   = gid('core_typeprojet','nom','Bâtiment commercial')
tp_pub   = gid('core_typeprojet','nom','Équipement public')
tp_hotel = gid('core_typeprojet','nom','Hôtel & Résidence')

# ──────────────────────────────────────────────────────────────────────────────
# 2. PROPRIÉTAIRES  (id INT auto, est_moral, prenom, nom, telephone, email…)
# ──────────────────────────────────────────────────────────────────────────────
print("[2] Propriétaires…")
def ins_prop(prenom, nom, tel, email, sexe, est_moral=False, entreprise="", ninea=""):
    ins('core_proprietaire',
        est_moral=1 if est_moral else 0,
        entreprise=entreprise, ninea=ninea,
        prenom=prenom, nom=nom,
        numero_identite=None, sexe=sexe,
        telephone=tel, email=email, adresse="Dakar, Sénégal")
    return gid('core_proprietaire','nom',nom)

prop_moussa  = ins_prop("Moussa",     "Diallo",    "77 600 11 22", "moussa.diallo@gmail.com", "M")
prop_fatou   = ins_prop("Fatou",      "Ndiaye",    "76 512 33 44", "f.ndiaye@outlook.com",    "F")
prop_abdou   = ins_prop("Abdoulaye",  "Ba",        "70 345 66 77", "abdoulaye.ba@yahoo.fr",   "M")
prop_cheikh  = ins_prop("Cheikh",     "Mbaye",     "77 900 88 99", "cheikh.mbaye@lamane.sn",  "M")
prop_sochisen= ins_prop("SOCHISEN",   "SARL",      "33 869 10 20", "dg@sochisen.sn",          "M",
                        True, "SOCHISEN SARL", "SN-DKR-2018-B12-00123")
conn.commit()

# ──────────────────────────────────────────────────────────────────────────────
# 3. FOURNISSEURS  (UUID pk, BaseModel, est_moral, prenom/nom ou entreprise…)
# ──────────────────────────────────────────────────────────────────────────────
print("[3] Fournisseurs…")
def ins_four(prenom, nom, tel, email, adresse, ninea, est_moral=True, entreprise=""):
    fid = uid()
    ins('core_fournisseur',
        id=fid, date_creation=now(), date_modification=now(),
        est_moral=1 if est_moral else 0,
        entreprise=entreprise, ninea=ninea,
        prenom=prenom, nom=nom,
        numero_identite=f"NI-{ninea[:6]}",   # unique fake NI
        sexe="H", photo_identite="",
        telephone=tel, email=email, adresse=adresse)
    return fid

f_sdm     = ins_four("",  "SDM",      "33 823 14 00", "contact@sdm.sn",       "Route de Rufisque, Dakar",    "1234567A0", True, "Société Dakaroise des Matériaux")
f_cimaf   = ins_four("",  "CIMAF",    "33 889 55 00", "ventes@cimaf.sn",       "Zone ind. Mbao",              "2345678B1", True, "CIMAF Sénégal")
f_quinca  = ins_four("",  "QuincaE",  "33 824 60 00", "info@pointe.sn",        "Liberté 6, Dakar",            "3456789C2", True, "Quincaillerie Point E")
f_sococim = ins_four("",  "Sococim",  "33 939 90 00", "commercial@sococim.sn", "Zone ind. Rufisque",          "4567890D3", True, "Sococim Industries")
f_btpmat  = ins_four("",  "BTPMat",   "77 644 22 11", "vente@btpmaterials.sn", "Autoroute Thiaroye",          "5678901E4", True, "BTP Materials SA")
conn.commit()

# ──────────────────────────────────────────────────────────────────────────────
# 4. PROJETS  (UUID pk, statut: "En cours"|"Terminé"|"En attente"|"En pause")
# ──────────────────────────────────────────────────────────────────────────────
print("[4] Projets…")
def ins_proj(nom, statut, type_id, prop_id, loc, budget, debut, fin, etages=1, sup=0, desc=""):
    pid = uid()
    ins('core_projet',
        id=pid, nom=nom, statut=statut,
        type_projet_id=type_id, proprietaire_id=prop_id,
        localisation=loc, cout_estime_lamane=budget,
        date_debut=debut, date_fin=fin,
        description=desc or f"Projet {nom} — LAMANE BTP",
        superficie=sup, surface_batie=int(sup*0.6) if sup else 0,
        nombre_pieces=4, nombre_etages=etages,
        a_piscine=0, volume_piscine=0,
        a_ascenseur=1 if etages > 3 else 0, nombre_ascenseurs=1 if etages > 3 else 0,
        a_climatisation=1, nombre_clims=etages*2,
        a_panneaux_solaires=0, puissance_panneaux=0,
        date_creation=now(), date_modification=now())
    return pid

proj_almadies  = ins_proj("Villa Résidentielle Almadies",          "En cours",   tp_villa,  prop_moussa,   "Almadies, Dakar",                  95000000, "2025-02-01","2026-06-30", 2, 320)
proj_plateau   = ins_proj("Immeuble R+5 du Plateau",               "En cours",   tp_imm,    prop_sochisen, "Plateau, Dakar",                  480000000, "2024-09-15","2026-12-31", 6,1800)
proj_saly      = ins_proj("Villa Saly Portudal",                    "Terminé",    tp_villa,  prop_fatou,    "Saly Portudal, Mbour",              62000000, "2024-03-01","2025-02-28", 1, 220)
proj_parcelles = ins_proj("Centre Commercial Parcelles Assainies",  "En cours",   tp_com,    prop_cheikh,   "Parcelles Assainies, Dakar",        220000000, "2024-11-01","2026-09-30", 3,2400)
proj_guediawaye= ins_proj("École Primaire Guédiawaye",              "Terminé",    tp_pub,    prop_abdou,    "Guédiawaye, Dakar",                  38000000, "2023-11-01","2025-01-31", 1,1200)
proj_hotel     = ins_proj("Résidence Hôtelière Saly Beach",         "En cours",   tp_hotel,  prop_cheikh,   "Saly Portudal, Mbour",             680000000, "2025-04-01","2027-06-30", 4,4200)
conn.commit()
projets = [proj_almadies, proj_plateau, proj_saly, proj_parcelles, proj_guediawaye, proj_hotel]

# Caractéristiques
for p_id in projets:
    ins('core_caracteristique',
        projet_id=p_id,
        superficie_totale=random.randint(200,2000),
        surface_batie=random.randint(100,800),
        nombre_etages=random.randint(1,6),
        nombre_pieces=random.randint(4,20),
        piscine=0, ascenseur=0, groupe_electrogene=1,
        panneau_solaire=0, parking_souterrain=0,
        climatisation=1, acces_handicapes=0,
        performance_energetique="B")
conn.commit()

# ──────────────────────────────────────────────────────────────────────────────
# 5. ÉTAPES STANDARD  (id INT, nom, ordre, multi_niveau, groupe:"gros"|"second")
# ──────────────────────────────────────────────────────────────────────────────
print("[5] Étapes standard…")
etapes_std = [
    ("Terrassement & fondations", 1, "gros"),
    ("Gros œuvre / Structure",    2, "gros"),
    ("Maçonnerie",                3, "gros"),
    ("Charpente & couverture",    4, "gros"),
    ("Plomberie sanitaire",       5, "second"),
    ("Électricité",               6, "second"),
    ("Menuiserie bois",           7, "second"),
    ("Menuiserie aluminium",      8, "second"),
    ("Carrelage & faïence",       9, "second"),
    ("Peinture & finitions",     10, "second"),
    ("VRD & aménagement ext.",   11, "second"),
]
for nom, ordre, groupe in etapes_std:
    ins('core_etapestandard', nom=nom, ordre=ordre, multi_niveau=0, groupe=groupe)
conn.commit()

def etape_id(nom): return gid('core_etapestandard','nom',nom)

# ──────────────────────────────────────────────────────────────────────────────
# 6. PHASES VERSEMENT  (libelle, projet_id, echeance, etape_standard_id,
#                       montant_prevu, niveau, ordre)
# ──────────────────────────────────────────────────────────────────────────────
print("[6] Phases versement…")
phases_def = {
    proj_almadies:   [
        ("Acompte démarrage",    "2025-02-01", 28500000, 1),
        ("Situation travaux 1",  "2025-05-01", 23750000, 2),
        ("Situation travaux 2",  "2025-09-01", 23750000, 3),
        ("Solde final",          "2026-06-30", 19000000, 4),
    ],
    proj_plateau:    [
        ("Acompte démarrage",    "2024-09-20",144000000, 1),
        ("Situation travaux 1",  "2025-01-10",120000000, 2),
        ("Situation travaux 2",  "2025-05-01",120000000, 3),
        ("Solde final",          "2026-12-31", 96000000, 4),
    ],
    proj_saly:       [
        ("Acompte démarrage",    "2024-03-10", 18600000, 1),
        ("Situation travaux 1",  "2024-07-20", 15500000, 2),
        ("Situation travaux 2",  "2024-11-15", 15500000, 3),
        ("Solde final",          "2025-02-01", 12400000, 4),
    ],
    proj_parcelles:  [
        ("Acompte démarrage",    "2024-11-10", 66000000, 1),
        ("Situation travaux 1",  "2025-02-20", 55000000, 2),
        ("Situation travaux 2",  "2025-06-01", 55000000, 3),
        ("Solde final",          "2026-09-30", 44000000, 4),
    ],
    proj_guediawaye: [
        ("Acompte démarrage",    "2023-11-10", 11400000, 1),
        ("Situation travaux 1",  "2024-04-05",  9500000, 2),
        ("Situation travaux 2",  "2024-08-15",  9500000, 3),
        ("Solde final",          "2025-01-20",  7600000, 4),
    ],
    proj_hotel:      [
        ("Acompte démarrage",    "2025-04-10",204000000, 1),
        ("Situation travaux 1",  "2025-10-01",170000000, 2),
        ("Situation travaux 2",  "2026-04-01",170000000, 3),
        ("Solde final",          "2027-06-30",136000000, 4),
    ],
}

phase_ids = {}  # (proj_id, ordre) → phase_id
for proj_id, phases in phases_def.items():
    for libelle, echeance, montant, ordre in phases:
        std_id = etape_id("Gros œuvre / Structure") if ordre == 1 else None
        ins('core_phaseversement',
            libelle=libelle, projet_id=proj_id,
            echeance=echeance, etape_standard_id=std_id,
            montant_prevu=montant, niveau=1, ordre=ordre)
        cur.execute("SELECT id FROM core_phaseversement WHERE projet_id=? AND ordre=?",
                    (proj_id, ordre))
        r = cur.fetchone()
        if r: phase_ids[(proj_id, ordre)] = r[0]
conn.commit()

# ──────────────────────────────────────────────────────────────────────────────
# 7. EMPLOYÉS  (id INT, nom, prenom, date_naissance, sexe, telephone, poste…)
# ──────────────────────────────────────────────────────────────────────────────
print("[7] Employés…")
def ins_emp(prenom, nom, tel, poste, date_emb, sexe="M", matricule=None):
    mat = matricule or f"EMP-{random.randint(1000,9999)}"
    ins('core_employe',
        nom=nom, prenom=prenom,
        date_naissance="1985-01-01",
        sexe=sexe, numero_identite=f"CNI-{mat}",
        telephone=tel, email=f"{prenom.lower()}.{nom.lower()}@lamane.sn",
        photo_identite="", matricule=mat,
        poste=poste, date_embauche=date_emb,
        adresse="Dakar, Sénégal", actif=1)
    return gid('core_employe','matricule',mat)

emp_ibou   = ins_emp("Ibrahima", "Sarr",   "77 711 22 33", "Conducteur de travaux",  "2022-03-01", "M", "EMP-0001")
emp_aminata= ins_emp("Aminata",  "Sy",     "76 822 44 55", "Comptable",               "2022-06-15", "F", "EMP-0002")
emp_modou  = ins_emp("Modou",    "Fall",   "70 933 66 77", "Chef chantier",           "2021-11-01", "M", "EMP-0003")
emp_adja   = ins_emp("Adja",     "Diallo", "77 044 88 99", "Ingénieur BTP",           "2023-01-15", "F", "EMP-0004")
emp_seydou = ins_emp("Seydou",   "Thiaw",  "76 155 99 00", "Technicien métreur",      "2023-07-01", "M", "EMP-0005")
emp_oumar  = ins_emp("Oumar",    "Mbaye",  "77 266 11 22", "Chef chantier",           "2024-02-01", "M", "EMP-0006")
conn.commit()

# Affectations
for emp in [emp_ibou, emp_modou, emp_adja]:
    for proj in [proj_almadies, proj_plateau]:
        ins('core_projetemploye',
            projet_id=proj, employe_id=emp,
            role="Cadre technique", date_affectation="2025-01-15",
            date_fin=None, contrat="CDI", observation="", actif=1)
for emp in [emp_seydou, emp_oumar]:
    ins('core_projetemploye',
        projet_id=proj_saly, employe_id=emp,
        role="Technicien", date_affectation="2024-03-01",
        date_fin="2025-02-28", contrat="CDD", observation="", actif=0)
conn.commit()

# ──────────────────────────────────────────────────────────────────────────────
# 8. CATÉGORIES + MATÉRIAUX  (catégorie: id INT; matériel: UUID)
# ──────────────────────────────────────────────────────────────────────────────
print("[8] Catégories et matériaux…")
cats = ["Gros œuvre","Menuiserie","Électricité","Plomberie","Finition","Outillage"]
for c in cats:
    ins('core_categoriemateriel', date_creation=now(), date_modification=now(), nom=c)
conn.commit()

def cat(nom): return gid('core_categoriemateriel','nom',nom)

materiaux = [
    # (nom, unite, categorie)
    ("Ciment CEM II/B-L 42.5 (sac 50kg)",    "sac",    "Gros œuvre"),
    ("Fer à béton HA8 (barre 12m)",           "barre",  "Gros œuvre"),
    ("Fer à béton HA10 (barre 12m)",          "barre",  "Gros œuvre"),
    ("Fer à béton HA12 (barre 12m)",          "barre",  "Gros œuvre"),
    ("Fer à béton HA14 (barre 12m)",          "barre",  "Gros œuvre"),
    ("Sable de mer lavé",                      "m³",     "Gros œuvre"),
    ("Gravier 15/25",                          "m³",     "Gros œuvre"),
    ("Parpaing creux 15cm",                    "unité",  "Gros œuvre"),
    ("Brique creuse 10cm",                     "unité",  "Gros œuvre"),
    ("Carrelage grès cérame 60×60",            "m²",     "Finition"),
    ("Faïence murale 30×60",                   "m²",     "Finition"),
    ("Peinture façade (seau 25L)",             "seau",   "Finition"),
    ("Peinture intérieure (seau 20L)",         "seau",   "Finition"),
    ("Câble électrique 2.5mm² (100m)",         "bobine", "Électricité"),
    ("Câble électrique 1.5mm² (100m)",         "bobine", "Électricité"),
    ("Tuyau PVC assainissement 110mm (6m)",    "barre",  "Plomberie"),
    ("Tuyau PVC pression 63mm (6m)",           "barre",  "Plomberie"),
    ("Porte aluminium 90×210",                 "unité",  "Menuiserie"),
    ("Fenêtre aluminium 120×140",              "unité",  "Menuiserie"),
    ("Porte bois isoplane 80×210",             "unité",  "Menuiserie"),
]
mat_ids = {}  # nom court → uuid
for nom, unite, cat_nom in materiaux:
    mid = uid()
    ins('core_materiel', id=mid, date_creation=now(), date_modification=now(),
        nom=nom, unite=unite, categorie_id=cat(cat_nom))
    mat_ids[nom] = mid
conn.commit()

def m(nom): return mat_ids.get(nom)

CIM  = m("Ciment CEM II/B-L 42.5 (sac 50kg)")
FER8 = m("Fer à béton HA8 (barre 12m)")
FER10= m("Fer à béton HA10 (barre 12m)")
FER12= m("Fer à béton HA12 (barre 12m)")
FER14= m("Fer à béton HA14 (barre 12m)")
SAB  = m("Sable de mer lavé")
GRV  = m("Gravier 15/25")
PAR  = m("Parpaing creux 15cm")
CAR  = m("Carrelage grès cérame 60×60")
FAI  = m("Faïence murale 30×60")
PEXT = m("Peinture façade (seau 25L)")
PINT = m("Peinture intérieure (seau 20L)")
CAB25= m("Câble électrique 2.5mm² (100m)")
CAB15= m("Câble électrique 1.5mm² (100m)")
TUY  = m("Tuyau PVC assainissement 110mm (6m)")
PORAL= m("Porte aluminium 90×210")
FENAL= m("Fenêtre aluminium 120×140")
PORBO= m("Porte bois isoplane 80×210")

# ──────────────────────────────────────────────────────────────────────────────
# 9. ACHATS + LIGNES  (achat: UUID, no commentaire column)
# ──────────────────────────────────────────────────────────────────────────────
print("[9] Achats…")
achats = [
    ("2025-02-15", proj_almadies, f_cimaf,  "virement", "FAC-2025-0112", False,
        [(CIM,300,7500),(FER10,80,6500),(FER12,60,9200)]),
    ("2025-03-01", proj_almadies, f_quinca, "espèces",  "FCT-2025-0089", False,
        [(SAB,20,28000),(GRV,15,35000),(PAR,500,350)]),
    ("2025-03-20", proj_plateau,  f_sdm,    "virement", "SDM-25-0456",   True,
        [(CIM,800,7400),(FER8,200,4150),(FER10,150,6400),(FER12,120,9100)]),
    ("2025-04-10", proj_plateau,  f_quinca, "chèque",   "QE-2025-0234",  False,
        [(CAR,500,13800),(FAI,300,8300),(PINT,40,17500)]),
    ("2025-01-10", proj_saly,     f_cimaf,  "virement", "FAC-2025-0023", False,
        [(CIM,200,7500),(SAB,10,28000),(GRV,8,35000)]),
    ("2025-02-28", proj_saly,     f_sdm,    "espèces",  "SDM-25-0167",   False,
        [(CAR,200,14000),(PEXT,12,32000),(PINT,8,18000)]),
    ("2025-04-05", proj_parcelles,f_sdm,    "virement", "SDM-25-0512",   True,
        [(FER10,300,6450),(FER14,200,12400),(CIM,1200,7400)]),
    ("2025-05-12", proj_parcelles,f_quinca, "virement", "QE-2025-0311",  False,
        [(CAB25,30,45000),(CAB15,25,28000),(TUY,50,8500)]),
    ("2024-12-05", proj_guediawaye,f_cimaf, "virement", "FAC-2024-0891", False,
        [(CIM,400,7500),(PAR,2000,350),(FER8,100,4200)]),
    ("2025-01-20", proj_guediawaye,f_sdm,   "chèque",   "SDM-25-0098",   False,
        [(CAR,300,14000),(FAI,200,8500),(PEXT,20,32000)]),
    ("2025-05-01", proj_hotel,    f_sdm,    "virement", "SDM-25-0589",   True,
        [(CIM,2000,7300),(FER10,500,6400),(FER12,400,9100),(FER14,300,12300)]),
    ("2025-06-15", proj_hotel,    f_quinca, "virement", "QE-2025-0445",  True,
        [(PORAL,40,184000),(FENAL,80,143000),(PORBO,30,64000)]),
]

for date_a, proj_id, four_id, mode, num_fact, tva, lignes in achats:
    if not all(m_id for m_id, _, _ in lignes): continue
    aid = uid()
    total_ht  = sum(q*p for _,q,p in lignes)
    total_tva = round(total_ht*0.18,2) if tva else 0
    total_ttc = round(total_ht+total_tva,2)
    ins('core_achat',
        id=aid, date_creation=now(), date_modification=now(),
        date_achat=date_a, mode_paiement=mode,
        numero_facture=num_fact, fichier_facture="",
        tva_active=1 if tva else 0,
        total_ht=total_ht, total_tva=total_tva, total_ttc=total_ttc,
        fournisseur_id=four_id, projet_id=proj_id, bon_entree_pdf="")
    for m_id, qte, prix in lignes:
        ins('core_ligneachat',
            date_creation=now(), date_modification=now(),
            quantite=qte, prix_unitaire=prix, commentaire="",
            achat_id=aid, materiel_id=m_id)
conn.commit()
print(f"  {len(achats)} achats créés.")

# ──────────────────────────────────────────────────────────────────────────────
# 10. BONS DE SORTIE + LIGNES
# ──────────────────────────────────────────────────────────────────────────────
print("[10] Bons de sortie…")
bons = [
    ("BS-2025-001","2025-02-20",proj_almadies,  "Ibrahima Sarr",
        [(CIM,50,"Fondations villa"),(FER10,20,"Armatures semelles")]),
    ("BS-2025-002","2025-03-05",proj_almadies,  "Ibrahima Sarr",
        [(SAB,8,"Béton de propreté"),(GRV,6,"Béton fondations")]),
    ("BS-2025-003","2025-03-25",proj_plateau,   "Modou Fall",
        [(CIM,200,"Voile béton RDC"),(FER10,40,"Voiles"),(FER12,30,"Poteaux RDC")]),
    ("BS-2025-004","2025-04-15",proj_plateau,   "Modou Fall",
        [(PAR,1000,"Maçonnerie R+1"),(CIM,80,"Mortier hourdage")]),
    ("BS-2025-005","2025-01-15",proj_saly,       "Seydou Thiaw",
        [(CIM,100,"Dalles"),(FER8,30,"Treillis dalle")]),
    ("BS-2025-006","2025-05-20",proj_parcelles, "Oumar Mbaye",
        [(FER10,80,"Poteaux R+1"),(FER14,50,"Poutres principales")]),
    ("BS-2025-007","2025-06-01",proj_hotel,     "Ibrahima Sarr",
        [(CIM,500,"Radier général"),(FER10,120,"Armatures radier")]),
    ("BS-2025-008","2025-06-20",proj_hotel,     "Adja Diallo",
        [(CAB25,10,"Colonnes montantes"),(CAB15,8,"Circuits prise")]),
]
for ref, date_s, proj_id, resp, lignes in bons:
    bid = uid()
    ins('core_bonsortie',
        id=bid, reference=ref, date_sortie=date_s,
        projet_id=proj_id, responsable=resp,
        observations="", bon_pdf="",
        date_creation=now(), date_modification=now())
    for m_id, qte, cmt in lignes:
        if m_id:
            ins('core_lignebonsortie', bon_id=bid, materiel_id=m_id,
                quantite=qte, commentaire=cmt)
conn.commit()
print(f"  {len(bons)} bons de sortie créés.")

# ──────────────────────────────────────────────────────────────────────────────
# 11. VERSEMENTS  (id INT auto, phase_id REQUIRED, etape_id nullable)
#   type_versement: 'chèque'|'virement bancaire'|'virement om'|'wave'|'espèces'
# ──────────────────────────────────────────────────────────────────────────────
print("[11] Versements…")
versements = [
    (proj_almadies,   1, 28500000, "2025-02-01", "virement bancaire", "Acompte démarrage villa Almadies",  "RE-ALM-001"),
    (proj_almadies,   2, 23750000, "2025-04-15", "chèque",            "Situation 1 villa Almadies",        "RE-ALM-002"),
    (proj_plateau,    1,144000000, "2024-09-20", "virement bancaire", "Acompte immeuble Plateau",          "RE-PLA-001"),
    (proj_plateau,    2,120000000, "2025-01-10", "virement bancaire", "Situation 1 immeuble Plateau",      "RE-PLA-002"),
    (proj_plateau,    3,120000000, "2025-05-01", "virement bancaire", "Situation 2 immeuble Plateau",      "RE-PLA-003"),
    (proj_saly,       1, 18600000, "2024-03-10", "virement bancaire", "Acompte villa Saly",                "RE-SAL-001"),
    (proj_saly,       2, 15500000, "2024-07-20", "chèque",            "Situation 1 villa Saly",            "RE-SAL-002"),
    (proj_saly,       3, 15500000, "2024-11-15", "espèces",           "Situation 2 villa Saly",            "RE-SAL-003"),
    (proj_saly,       4, 12400000, "2025-02-01", "virement bancaire", "Solde villa Saly",                  "RE-SAL-004"),
    (proj_parcelles,  1, 66000000, "2024-11-10", "virement bancaire", "Acompte centre commercial",         "RE-PAR-001"),
    (proj_parcelles,  2, 55000000, "2025-02-20", "virement bancaire", "Situation 1 centre commercial",     "RE-PAR-002"),
    (proj_guediawaye, 1, 11400000, "2023-11-10", "virement bancaire", "Acompte école Guédiawaye",          "RE-GUE-001"),
    (proj_guediawaye, 2,  9500000, "2024-04-05", "chèque",            "Situation 1 école",                 "RE-GUE-002"),
    (proj_guediawaye, 3,  9500000, "2024-08-15", "virement bancaire", "Situation 2 école",                 "RE-GUE-003"),
    (proj_guediawaye, 4,  7600000, "2025-01-20", "virement bancaire", "Solde école Guédiawaye",            "RE-GUE-004"),
    (proj_hotel,      1,204000000, "2025-04-10", "virement bancaire", "Acompte résidence hôtelière",       "RE-HOT-001"),
    (proj_hotel,      2,170000000, "2025-07-01", "virement bancaire", "Situation 1 hôtel Saly Beach",      "RE-HOT-002"),
]

for proj_id, phase_ordre, montant, date_v, type_v, libelle, ref_pmt in versements:
    ph_id = phase_ids.get((proj_id, phase_ordre))
    if ph_id:
        ins('core_versement',
            projet_id=proj_id, phase_id=ph_id, etape_id=None,
            montant=montant, date_versement=date_v,
            type_versement=type_v, libelle=libelle,
            numero_facture=ref_pmt.replace("RE-","FAC-"),
            reference_paiement=ref_pmt,
            fichier_justificatif="", facture_pdf="")
conn.commit()
print(f"  {len(versements)} versements créés.")

# ──────────────────────────────────────────────────────────────────────────────
# 12. MARCHÉS DE TRAVAUX
# ──────────────────────────────────────────────────────────────────────────────
print("[12] Marchés de travaux…")
marches = [
    (proj_plateau,    "MT-2024-001","Construction immeuble R+5 — Lot unique",
     480000000,96000000,5.0,0.05,10.0,"2024-09-10","2024-09-15",480,"signe",None,None),
    (proj_parcelles,  "MT-2024-002","Construction centre commercial",
     220000000,44000000,5.0,0.05,10.0,"2024-10-25","2024-11-01",700,"signe",None,None),
    (proj_saly,       "MT-2024-003","Construction villa Saly",
     62000000, 12400000,5.0,0.05,10.0,"2024-02-20","2024-03-01",365,"reception_definitive","2025-02-10","2025-03-01"),
    (proj_guediawaye, "MT-2023-001","Construction école primaire",
     38000000,  7600000,5.0,0.05,10.0,"2023-10-20","2023-11-01",450,"reception_definitive","2025-01-15","2025-02-28"),
    (proj_hotel,      "MT-2025-001","Résidence hôtelière — Tous corps d'état",
     680000000,136000000,5.0,0.05,10.0,"2025-03-25","2025-04-01",820,"signe",None,None),
]
for (p,num,obj,mont,avance,ret,pen,plaf,dt_sign,dt_os,delai,stat,dt_rp,dt_rd) in marches:
    ins('core_marchetravaux',
        projet_id=p, numero_marche=num, objet=obj,
        montant_marche=mont, montant_avance_demarrage=avance,
        taux_retenue_garantie=ret, penalite_journaliere_pct=pen,
        plafond_penalites_pct=plaf, date_signature=dt_sign,
        date_ordre_service=dt_os, delai_execution_jours=delai, statut=stat,
        date_reception_provisoire=dt_rp, date_reception_definitive=dt_rd,
        observations="", date_creation=now(), date_modification=now())
conn.commit()
print(f"  {len(marches)} marchés créés.")

# ──────────────────────────────────────────────────────────────────────────────
# 13. AVANCEMENTS CHANTIER
# ──────────────────────────────────────────────────────────────────────────────
print("[13] Avancements chantier…")
def add_avc(proj_id, start_y, start_m, data):
    for i,(tp,tf,tpl,ouv,enc) in enumerate(data):
        m2 = start_m + i
        y2 = start_y + (m2-1)//12
        m2 = ((m2-1)%12)+1
        ins('core_avancementchantier',
            projet_id=proj_id, periode=f"{y2}-{m2:02d}-01",
            taux_physique=tp, taux_financier=tf, taux_planifie=tpl,
            effectif_ouvriers=ouv, effectif_encadrement=enc,
            observations=f"Avancement mois {i+1}", incidents="", mesures_correctives="",
            date_creation=now(), date_modification=now())

add_avc(proj_almadies,  2025,2, [(5,10,10,8,2),(15,20,20,12,3),(28,30,30,15,3),(42,35,40,18,4),(55,45,50,18,4)])
add_avc(proj_plateau,   2024,9, [(3,8,8,20,5),(10,16,15,28,6),(18,24,22,32,7),(28,30,30,35,7),(38,38,38,38,8),(47,44,46,40,8),(55,50,54,42,9),(62,56,62,40,9)])
add_avc(proj_saly,      2024,3, [(8,15,12,6,2),(20,28,25,8,2),(38,40,40,10,2),(55,50,55,10,2),(70,65,68,8,2),(84,80,82,6,2),(95,90,95,4,1),(100,100,100,2,1)])
add_avc(proj_parcelles, 2024,11,[(4,8,8,25,6),(12,16,16,32,7),(22,24,25,38,8),(33,32,33,40,9),(42,40,42,42,9),(52,48,50,44,10)])
add_avc(proj_guediawaye,2023,11,[(8,12,10,15,4),(20,24,22,18,4),(35,36,35,20,5),(50,48,50,20,5),(65,62,65,18,4),(78,75,78,16,4),(90,88,90,10,3),(100,100,100,5,2)])
add_avc(proj_hotel,     2025,4, [(2,5,5,30,8),(8,12,10,45,10),(15,18,18,55,12)])
conn.commit()
print("  Avancements créés.")

# ──────────────────────────────────────────────────────────────────────────────
# 14. SOUS-TRAITANTS + CONTRATS
# ──────────────────────────────────────────────────────────────────────────────
print("[14] Sous-traitants et contrats…")
sts = [
    ("Électricité Générale Dakar (EGD)",    "electricite_cfa",    "1122334A5","77 500 11 22","egd@egd.sn",         "Liberté 5"),
    ("Plomberie Sanitaire SARL",            "plomberie_sanitaire","2233445B6","76 611 33 44","ps@pssarl.sn",       "Thiaroye"),
    ("Menuiserie Aluminium Sénégal (MAS)",  "menuiserie_alu",     "3344556C7","77 722 55 66","mas@mas-dakar.sn",   "Parcelles"),
    ("Carrelage & Faïence Pro",             "carrelage_faience",  "4455667D8","70 833 77 88","cfpro@cfpro.sn",     "Rufisque"),
    ("Peinture Bâtiment Expert (PBE)",      "peinture_revetement","5566778E9","77 944 99 00","pbe@pbe.sn",         "Yoff"),
    ("Climatisation & Ventilation Afrique", "climatisation",      "6677889F0","33 801 22 33","cva@cva.sn",         "Zone ind."),
]
st_ids = {}
for nom, spec, ninea, tel, email, adr in sts:
    ins('core_soustraitant',
        nom=nom, specialite=spec, ninea=ninea,
        telephone=tel, email=email, adresse=adr,
        contact_nom="", actif=1,
        date_creation=now(), date_modification=now())
    st_ids[nom] = gid('core_soustraitant','ninea',ninea)
conn.commit()

def st(n): return st_ids.get(n)

contrats = [
    (proj_plateau,  "Électricité Générale Dakar (EGD)",  "Lot 4 — Électricité CFA R+5",         28000000,14000000,"2025-02-01","2026-08-31",None,"en_cours"),
    (proj_plateau,  "Plomberie Sanitaire SARL",           "Lot 5 — Plomberie sanitaire R+5",     22000000,11000000,"2025-03-01","2026-09-30",None,"en_cours"),
    (proj_plateau,  "Menuiserie Aluminium Sénégal (MAS)", "Lot 6 — Menuiserie aluminium",        35000000,0,       "2025-06-01","2026-11-30",None,"en_cours"),
    (proj_saly,     "Carrelage & Faïence Pro",             "Lot 3 — Carrelage villa",              8500000, 8500000,"2024-09-01","2025-01-31","2025-02-10","termine"),
    (proj_saly,     "Peinture Bâtiment Expert (PBE)",      "Lot 4 — Peinture villa",               6200000, 6200000,"2024-11-01","2025-02-28","2025-03-05","termine"),
    (proj_parcelles,"Climatisation & Ventilation Afrique","Lot 5 — Climatisation commerces",     42000000,12600000,"2025-03-01","2026-07-31",None,"en_cours"),
    (proj_hotel,    "Électricité Générale Dakar (EGD)",   "Lot 3 — Électricité hôtel",           55000000,0,       "2025-07-01","2027-03-31",None,"en_cours"),
    (proj_hotel,    "Climatisation & Ventilation Afrique","Lot 7 — Climatisation chambres",      78000000,0,       "2025-08-01","2027-04-30",None,"en_cours"),
]
for (p_id, st_nom, lot, mont, paye, ddeb, dfin_p, dfin_r, stat) in contrats:
    s_id = st(st_nom)
    if s_id:
        ins('core_contratsoustraitance',
            projet_id=p_id, sous_traitant_id=s_id,
            lot=lot, montant=mont, montant_paye=paye,
            date_debut=ddeb, date_fin_prevue=dfin_p, date_fin_reelle=dfin_r,
            statut=stat, observations="", contrat_pdf="",
            date_creation=now(), date_modification=now())
conn.commit()
print(f"  {len(sts)} sous-traitants, {len(contrats)} contrats.")

# ──────────────────────────────────────────────────────────────────────────────
# 15. SITUATIONS MENSUELLES
# ──────────────────────────────────────────────────────────────────────────────
print("[15] Situations mensuelles…")
def add_situations(proj_id, situations):
    for i,(periode,brut,taux,statut,dt_soum,dt_val) in enumerate(situations):
        retenue = round(brut*0.05,2)
        net_cum = round(brut-retenue,2)
        prec    = 0 if i==0 else round(situations[i-1][1]*0.95,2)
        a_payer = round(net_cum-prec,2)
        ins('core_situationmensuelle',
            projet_id=proj_id, numero_situation=i+1,
            periode=periode, montant_brut_cumule=brut,
            taux_avancement=taux, retenue_garantie=retenue,
            montant_net_cumule=net_cum,
            montant_precedentes_situations=prec,
            montant_a_payer=a_payer, statut=statut,
            date_soumission=dt_soum, date_validation=dt_val,
            observations="", date_creation=now(), date_modification=now())

add_situations(proj_plateau,[
    ("2024-11-01", 48000000,10,"payee",   "2024-11-10","2024-11-20"),
    ("2024-12-01",115200000,24,"payee",   "2024-12-08","2024-12-20"),
    ("2025-01-01",182400000,38,"payee",   "2025-01-08","2025-01-20"),
    ("2025-02-01",240000000,50,"payee",   "2025-02-07","2025-02-18"),
    ("2025-03-01",288000000,60,"validee", "2025-03-10","2025-03-22"),
    ("2025-04-01",326400000,68,"soumise", "2025-04-08",None),
])
add_situations(proj_saly,[
    ("2024-05-01", 12400000,20,"payee","2024-05-10","2024-05-20"),
    ("2024-08-01", 31000000,50,"payee","2024-08-08","2024-08-18"),
    ("2024-11-01", 49600000,80,"payee","2024-11-06","2024-11-15"),
    ("2025-01-01", 62000000,100,"payee","2025-01-05","2025-01-12"),
])
add_situations(proj_guediawaye,[
    ("2024-02-01",  7600000,20,"payee","2024-02-10","2024-02-18"),
    ("2024-06-01", 19000000,50,"payee","2024-06-08","2024-06-16"),
    ("2024-10-01", 30400000,80,"payee","2024-10-07","2024-10-16"),
    ("2025-01-01", 38000000,100,"payee","2025-01-05","2025-01-12"),
])
add_situations(proj_parcelles,[
    ("2025-01-01", 22000000,10,"payee",  "2025-01-10","2025-01-20"),
    ("2025-03-01", 52800000,24,"payee",  "2025-03-08","2025-03-18"),
    ("2025-05-01", 88000000,40,"soumise","2025-05-08",None),
])
conn.commit()
print("  Situations mensuelles créées.")

# ──────────────────────────────────────────────────────────────────────────────
conn.execute("PRAGMA foreign_keys = ON")
conn.commit()
conn.close()

print()
print("=" * 55)
print("✅  BASE DE DONNÉES COMPLÈTEMENT PEUPLÉE !")
print("=" * 55)
rows = [
    ("Types de projets",        len(types)),
    ("Propriétaires",           5),
    ("Fournisseurs",            5),
    ("Projets",                 6),
    ("Étapes standard",         len(etapes_std)),
    ("Phases versement",        sum(len(v) for v in phases_def.values())),
    ("Employés",                6),
    ("Catégories matériaux",    len(cats)),
    ("Matériaux",               len(materiaux)),
    ("Achats",                  len(achats)),
    ("Bons de sortie",          len(bons)),
    ("Versements",              len(versements)),
    ("Marchés de travaux",      len(marches)),
    ("Sous-traitants",          len(sts)),
    ("Contrats sous-traitance", len(contrats)),
]
for nom, n in rows:
    print(f"  {nom:<35} {n:>3}")
print("\nRelancez le serveur Django — tout est prêt !")
