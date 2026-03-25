"""
apply_migrations.py — Applique les migrations manquantes (0006→0009) directement
sur la base SQLite, sans avoir besoin de Django ou d'un venv.

Utilisation (dans le dossier du projet, là où se trouve db.sqlite3) :
    python apply_migrations.py
"""
import sqlite3, os, sys, datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'db.sqlite3')

if not os.path.exists(DB_PATH):
    print(f"[ERREUR] db.sqlite3 introuvable ici : {DB_PATH}")
    sys.exit(1)

conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()

# ── Helpers ──────────────────────────────────────────────────────────────────

def tables():
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return {r[0] for r in cur.fetchall()}

def columns(table):
    cur.execute(f"PRAGMA table_info({table})")
    return {r[1] for r in cur.fetchall()}

def migration_applied(name):
    try:
        cur.execute("SELECT 1 FROM django_migrations WHERE app='core' AND name=?", (name,))
        return cur.fetchone() is not None
    except Exception:
        return False

def mark_applied(name):
    now = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
    cur.execute(
        "INSERT OR IGNORE INTO django_migrations (app, name, applied) VALUES ('core', ?, ?)",
        (name, now)
    )

def run(sql):
    try:
        cur.executescript(sql)
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"  [AVERTISSEMENT SQL] {e}")

# ── 0006 — Nouveaux modèles BTP ───────────────────────────────────────────────
print("=== Migration 0006 ===")
t = tables()

if 'core_marchetravaux' not in t:
    print("  Création core_marchetravaux …")
    run("""
    CREATE TABLE "core_marchetravaux" (
        "id"                          integer NOT NULL PRIMARY KEY AUTOINCREMENT,
        "numero_marche"               varchar(50)  NOT NULL UNIQUE,
        "objet"                       text         NOT NULL,
        "montant_marche"              decimal(16,2) NOT NULL,
        "montant_avance_demarrage"    decimal(14,2) NOT NULL,
        "taux_retenue_garantie"       decimal(5,2)  NOT NULL,
        "penalite_journaliere_pct"    decimal(5,4)  NOT NULL,
        "plafond_penalites_pct"       decimal(5,2)  NOT NULL,
        "date_signature"              date,
        "date_ordre_service"          date,
        "delai_execution_jours"       integer unsigned NOT NULL,
        "statut"                      varchar(30) NOT NULL,
        "date_reception_provisoire"   date,
        "date_reception_definitive"   date,
        "observations"                text NOT NULL,
        "date_creation"               datetime NOT NULL,
        "date_modification"           datetime NOT NULL,
        "projet_id"                   integer NOT NULL UNIQUE
                                      REFERENCES "core_projet" ("id")
                                      DEFERRABLE INITIALLY DEFERRED
    );
    """)
else:
    print("  core_marchetravaux déjà présente.")

if 'core_avancementchantier' not in t:
    print("  Création core_avancementchantier …")
    run("""
    CREATE TABLE "core_avancementchantier" (
        "id"                   integer NOT NULL PRIMARY KEY AUTOINCREMENT,
        "periode"              date    NOT NULL,
        "taux_physique"        decimal(5,2) NOT NULL,
        "taux_financier"       decimal(5,2) NOT NULL,
        "taux_planifie"        decimal(5,2) NOT NULL,
        "effectif_ouvriers"    integer unsigned NOT NULL,
        "effectif_encadrement" integer unsigned NOT NULL,
        "observations"         text NOT NULL,
        "incidents"            text NOT NULL,
        "mesures_correctives"  text NOT NULL,
        "date_creation"        datetime NOT NULL,
        "date_modification"    datetime NOT NULL,
        "projet_id"            integer NOT NULL
                               REFERENCES "core_projet" ("id")
                               DEFERRABLE INITIALLY DEFERRED,
        UNIQUE ("projet_id", "periode")
    );
    CREATE INDEX "core_avancementchantier_projet_id_idx"
        ON "core_avancementchantier" ("projet_id");
    """)
else:
    print("  core_avancementchantier déjà présente.")

if 'core_soustraitant' not in t:
    print("  Création core_soustraitant …")
    run("""
    CREATE TABLE "core_soustraitant" (
        "id"               integer NOT NULL PRIMARY KEY AUTOINCREMENT,
        "nom"              varchar(200) NOT NULL UNIQUE,
        "specialite"       varchar(30)  NOT NULL,
        "ninea"            varchar(20)  NOT NULL,
        "telephone"        varchar(20)  NOT NULL,
        "email"            varchar(254) NOT NULL,
        "adresse"          varchar(255) NOT NULL,
        "contact_nom"      varchar(100) NOT NULL,
        "actif"            bool         NOT NULL,
        "date_creation"    datetime     NOT NULL,
        "date_modification" datetime    NOT NULL
    );
    """)
else:
    print("  core_soustraitant déjà présente.")

if 'core_contratsoustraitance' not in t:
    print("  Création core_contratsoustraitance …")
    run("""
    CREATE TABLE "core_contratsoustraitance" (
        "id"                  integer NOT NULL PRIMARY KEY AUTOINCREMENT,
        "lot"                 varchar(200)  NOT NULL,
        "montant"             decimal(14,2) NOT NULL,
        "montant_paye"        decimal(14,2) NOT NULL,
        "date_debut"          date,
        "date_fin_prevue"     date,
        "date_fin_reelle"     date,
        "statut"              varchar(20) NOT NULL,
        "observations"        text NOT NULL,
        "date_creation"       datetime NOT NULL,
        "date_modification"   datetime NOT NULL,
        "projet_id"           integer NOT NULL
                              REFERENCES "core_projet" ("id")
                              DEFERRABLE INITIALLY DEFERRED,
        "sous_traitant_id"    integer NOT NULL
                              REFERENCES "core_soustraitant" ("id")
                              DEFERRABLE INITIALLY DEFERRED
    );
    CREATE INDEX "core_contratsoustraitance_projet_id_idx"
        ON "core_contratsoustraitance" ("projet_id");
    CREATE INDEX "core_contratsoustraitance_st_id_idx"
        ON "core_contratsoustraitance" ("sous_traitant_id");
    """)
else:
    print("  core_contratsoustraitance déjà présente.")

if 'core_situationmensuelle' not in t:
    print("  Création core_situationmensuelle …")
    run("""
    CREATE TABLE "core_situationmensuelle" (
        "id"                          integer NOT NULL PRIMARY KEY AUTOINCREMENT,
        "numero_situation"            integer unsigned NOT NULL,
        "periode"                     date    NOT NULL,
        "montant_brut_cumule"         decimal(16,2) NOT NULL,
        "taux_avancement"             decimal(5,2)  NOT NULL,
        "retenue_garantie"            decimal(14,2) NOT NULL,
        "montant_net_cumule"          decimal(16,2) NOT NULL,
        "montant_precedentes_situations" decimal(16,2) NOT NULL,
        "montant_a_payer"             decimal(16,2) NOT NULL,
        "statut"                      varchar(20) NOT NULL,
        "date_soumission"             date,
        "date_validation"             date,
        "observations"                text NOT NULL,
        "date_creation"               datetime NOT NULL,
        "date_modification"           datetime NOT NULL,
        "projet_id"                   integer NOT NULL
                                      REFERENCES "core_projet" ("id")
                                      DEFERRABLE INITIALLY DEFERRED,
        UNIQUE ("projet_id", "numero_situation")
    );
    CREATE INDEX "core_situationmensuelle_projet_id_idx"
        ON "core_situationmensuelle" ("projet_id");
    """)
else:
    print("  core_situationmensuelle déjà présente.")

mark_applied('0006_nouveaux_modeles_btp')
conn.commit()

# ── 0007 — BonSortie, LigneBonSortie, bon_entree_pdf ─────────────────────────
print("=== Migration 0007 ===")
t = tables()

if 'core_bonsortie' not in t:
    print("  Création core_bonsortie …")
    run("""
    CREATE TABLE "core_bonsortie" (
        "id"                varchar(32)  NOT NULL PRIMARY KEY,
        "reference"         varchar(30)  NOT NULL UNIQUE,
        "date_sortie"       date         NOT NULL,
        "responsable"       varchar(100) NOT NULL,
        "observations"      text         NOT NULL,
        "bon_pdf"           varchar(100),
        "date_creation"     datetime     NOT NULL,
        "date_modification" datetime     NOT NULL,
        "projet_id"         integer      NOT NULL
                            REFERENCES "core_projet" ("id")
                            DEFERRABLE INITIALLY DEFERRED
    );
    CREATE INDEX "core_bonsortie_projet_id_idx"
        ON "core_bonsortie" ("projet_id");
    """)
else:
    print("  core_bonsortie déjà présente.")

if 'core_lignebonsortie' not in t:
    print("  Création core_lignebonsortie …")
    run("""
    CREATE TABLE "core_lignebonsortie" (
        "id"          integer NOT NULL PRIMARY KEY AUTOINCREMENT,
        "quantite"    decimal(10,2) NOT NULL,
        "commentaire" varchar(200)  NOT NULL,
        "bon_id"      varchar(32)   NOT NULL
                      REFERENCES "core_bonsortie" ("id")
                      DEFERRABLE INITIALLY DEFERRED,
        "materiel_id" integer NOT NULL
                      REFERENCES "core_materiel" ("id")
                      DEFERRABLE INITIALLY DEFERRED
    );
    CREATE INDEX "core_lignebonsortie_bon_id_idx"
        ON "core_lignebonsortie" ("bon_id");
    CREATE INDEX "core_lignebonsortie_materiel_id_idx"
        ON "core_lignebonsortie" ("materiel_id");
    """)
else:
    print("  core_lignebonsortie déjà présente.")

# Add bon_entree_pdf column to core_achat if missing
if 'bon_entree_pdf' not in columns('core_achat'):
    print("  Ajout colonne bon_entree_pdf sur core_achat …")
    run('ALTER TABLE "core_achat" ADD COLUMN "bon_entree_pdf" varchar(100);')
else:
    print("  core_achat.bon_entree_pdf déjà présente.")

mark_applied('0007_bonsortie_lignebon')
conn.commit()

# ── 0008 — AlterField (aucun changement structurel SQLite nécessaire) ─────────
print("=== Migration 0008 ===")
mark_applied('0008_alter_avancementchantier_effectif_encadrement_and_more')
conn.commit()
print("  Marquée comme appliquée (pas de changement SQLite).")

# ── 0009 — contrat_pdf sur ContratSousTraitance ───────────────────────────────
print("=== Migration 0009 ===")
if 'contrat_pdf' not in columns('core_contratsoustraitance'):
    print("  Ajout colonne contrat_pdf sur core_contratsoustraitance …")
    run('ALTER TABLE "core_contratsoustraitance" ADD COLUMN "contrat_pdf" varchar(100);')
else:
    print("  core_contratsoustraitance.contrat_pdf déjà présente.")
mark_applied('0009_contrat_pdf')
conn.commit()

conn.close()
print()
print("✅ Terminé ! Toutes les migrations sont appliquées.")
print("   Vous pouvez relancer le serveur Django.")
