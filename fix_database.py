"""
fix_database.py — Répare la base de données LAMANE
Exécuter depuis le dossier lamane_project :
    python fix_database.py
"""
import sqlite3
import os
import shutil
from datetime import datetime

DB_PATH     = os.path.join(os.path.dirname(__file__), "db.sqlite3")
BACKUP_PATH = os.path.join(os.path.dirname(__file__), "db_enriched_backup.sqlite3")
TEMP_PATH   = os.path.join(os.path.dirname(__file__), "db_recovered.sqlite3")

# ─────────────────────────────────────────────────────────────────────────────
# 1. Dump the corrupted database
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("LAMANE — Réparation base de données")
print("=" * 60)

print("\n[1/4] Extraction des données depuis la base corrompue...")
try:
    src_conn = sqlite3.connect(DB_PATH)
    dump_lines = list(src_conn.iterdump())
    src_conn.close()
    print(f"      ✓ {len(dump_lines)} lignes SQL extraites")
    source_used = "corrupted"
except Exception as e:
    print(f"      ✗ Impossible de lire la base principale ({e})")
    print("      → Utilisation de la sauvegarde...")
    src_conn = sqlite3.connect(BACKUP_PATH)
    dump_lines = list(src_conn.iterdump())
    src_conn.close()
    print(f"      ✓ {len(dump_lines)} lignes SQL extraites depuis la sauvegarde")
    source_used = "backup"

# ─────────────────────────────────────────────────────────────────────────────
# 2. Create fresh database and replay the dump
# ─────────────────────────────────────────────────────────────────────────────
print("\n[2/4] Reconstruction d'une base propre...")
if os.path.exists(TEMP_PATH):
    os.remove(TEMP_PATH)

new_conn = sqlite3.connect(TEMP_PATH)
new_conn.execute("PRAGMA journal_mode=DELETE")
new_conn.execute("PRAGMA synchronous=FULL")

errors = 0
for line in dump_lines:
    try:
        new_conn.execute(line)
    except sqlite3.Error:
        # Some lines may fail (e.g. constraints during replay) — skip gracefully
        errors += 1

new_conn.commit()
print(f"      ✓ Base reconstruite ({errors} lignes ignorées lors du replay)")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Apply data fixes
# ─────────────────────────────────────────────────────────────────────────────
print("\n[3/4] Application des corrections...")
c = new_conn.cursor()

# Fix orphaned FK on core_versement.etape_id
try:
    c.execute("""
        UPDATE core_versement
        SET etape_id = NULL
        WHERE etape_id IS NOT NULL
          AND etape_id NOT IN (SELECT id FROM core_etapestandard)
    """)
    fixed_fk = c.rowcount
    new_conn.commit()
    print(f"      ✓ FK orphelines corrigées : {fixed_fk} enregistrement(s)")
except Exception as e:
    print(f"      ! core_versement FK fix : {e}")

# Add contrat_pdf column if missing
try:
    c.execute("PRAGMA table_info(core_contratsoustraitance)")
    cols = [row[1] for row in c.fetchall()]
    if "contrat_pdf" not in cols:
        c.execute(
            "ALTER TABLE core_contratsoustraitance "
            "ADD COLUMN contrat_pdf VARCHAR(100) NULL"
        )
        new_conn.commit()
        print("      ✓ Colonne contrat_pdf ajoutée")
    else:
        print("      ✓ Colonne contrat_pdf déjà présente")
except Exception as e:
    print(f"      ! contrat_pdf column : {e}")

# Mark migration 0009_contrat_pdf as applied
try:
    c.execute(
        "SELECT 1 FROM django_migrations WHERE app='core' AND name='0009_contrat_pdf'"
    )
    exists = c.fetchone()
    if not exists:
        c.execute(
            "INSERT INTO django_migrations (app, name, applied) "
            "VALUES ('core', '0009_contrat_pdf', ?)",
            (datetime.now().isoformat(),),
        )
        new_conn.commit()
        print("      ✓ Migration 0009_contrat_pdf enregistrée")
    else:
        print("      ✓ Migration 0009_contrat_pdf déjà enregistrée")
except Exception as e:
    print(f"      ! migration record : {e}")

# Final integrity check
c.execute("PRAGMA integrity_check")
integrity = c.fetchone()[0]
print(f"      Intégrité finale : {integrity}")

new_conn.close()

# ─────────────────────────────────────────────────────────────────────────────
# 4. Replace the database
# ─────────────────────────────────────────────────────────────────────────────
print("\n[4/4] Remplacement de la base de données...")
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
old_backup = DB_PATH + f".bak_{timestamp}"
shutil.copy2(DB_PATH, old_backup)
print(f"      Sauvegarde : {os.path.basename(old_backup)}")

shutil.copy2(TEMP_PATH, DB_PATH)
os.remove(TEMP_PATH)
print(f"      ✓ Base de données remplacée avec succès")

print("\n" + "=" * 60)
print("✓ Réparation terminée. Vous pouvez redémarrer le serveur.")
print("=" * 60)
