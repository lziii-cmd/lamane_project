// static/js/projet_admin.js

document.addEventListener('DOMContentLoaded', function () {
  // Champs dynamiques selon a_piscine
  const checkboxPiscine = document.querySelector('#id_a_piscine');
  const blocPiscine = document.querySelector('.form-row.field-volume_piscine');

  // Champs dynamiques selon a_ascenseur
  const checkboxAscenseur = document.querySelector('#id_a_ascenseur');
  const blocAscenseur = document.querySelector('.form-row.field-nombre_ascenseurs');

  // Champs dynamiques selon a_climatisation
  const checkboxClim = document.querySelector('#id_a_climatisation');
  const blocClim = document.querySelector('.form-row.field-nombre_clims');

  // Champs dynamiques selon a_panneaux_solaires
  const checkboxPanneaux = document.querySelector('#id_a_panneaux_solaires');
  const blocPanneaux = document.querySelector('.form-row.field-puissance_panneaux');

  function toggleBloc(checkbox, bloc) {
    if (checkbox && bloc) {
      if (checkbox.checked) {
        bloc.style.display = '';
      } else {
        bloc.style.display = 'none';
      }
    }
  }

  function bindToggle(checkbox, bloc) {
    if (checkbox && bloc) {
      toggleBloc(checkbox, bloc);
      checkbox.addEventListener('change', function () {
        toggleBloc(checkbox, bloc);
      });
    }
  }

  bindToggle(checkboxPiscine, blocPiscine);
  bindToggle(checkboxAscenseur, blocAscenseur);
  bindToggle(checkboxClim, blocClim);
  bindToggle(checkboxPanneaux, blocPanneaux);
});

// === Lamane :: Phasage semi-automatique (Élévation/Plancher par niveaux) ===
const FLOORS_FIELD_NAMES = ["nombre_etages", "nb_etages", "nombre_detages", "nbEtages"];
const STEP_NAMES = {
  SIGNATURE: "signature",
  FONDATION: "fondation",
  ELEVATION: "élévation", // "elevation" accepté aussi
  PLANCHER:  "plancher",
  TOITURE:   "toiture",
};

// -------- utilitaires DOM --------
function findFloorsInput() {
  for (const n of FLOORS_FIELD_NAMES) {
    const el = document.querySelector(`[name="${n}"]`);
    if (el) return el;
  }
  return null;
}

// Trouve la table de l’inline PhaseVersement (robuste)
function findPhasesInlineTable() {
  // via management form (TOTAL_FORMS)
  const mgmt = document.querySelector('input[name$="TOTAL_FORMS"][name*="phaseversement"]');
  if (mgmt) {
    const group = mgmt.closest("div.inline-group") || document;
    const t = group.querySelector("table");
    if (t) return t;
  }
  // via empty-form (quand présente)
  const emptySel = document.querySelector('tr.empty-form select[name$="-etape_standard"]');
  if (emptySel) return emptySel.closest("table");

  // via une ligne déjà visible
  const anySel = document.querySelector('select[name$="-etape_standard"]');
  if (anySel) return anySel.closest("table");

  // fallback
  return document.querySelector("div.inline-group table") || null;
}

// Préfixe du formset (ex: "phaseversement_set-")
function detectInlinePrefix(table) {
  const any = table && table.querySelector("input, select, textarea");
  if (any && any.name) {
    const m = any.name.match(/^(.+?)-\d+-/);
    if (m) return m[1] + "-";
  }
  const mgmt = document.querySelector('input[name$="TOTAL_FORMS"][name*="phaseversement"]');
  if (mgmt && mgmt.name) {
    const m2 = mgmt.name.match(/^(.+?)TOTAL_FORMS$/);
    if (m2) return m2[1];
  }
  return null;
}

// comptage / ajout de ligne
function getFormCounts(prefix) {
  const totalEl = document.querySelector(`input[name="${prefix}TOTAL_FORMS"]`);
  const initialEl = document.querySelector(`input[name="${prefix}INITIAL_FORMS"]`);
  return {
    totalEl,
    total: totalEl ? parseInt(totalEl.value || "0", 10) : 0,
    initial: initialEl ? parseInt(initialEl.value || "0", 10) : 0,
  };
}
function incTotalForms(prefix) {
  const c = getFormCounts(prefix);
  if (c.totalEl) c.totalEl.value = String(c.total + 1);
}
function addInlineRow(table, prefix) {
  const empty = table.querySelector("tr.empty-form");
  if (!empty) return null;
  const idx = getFormCounts(prefix).total;
  const html = empty.outerHTML.replace(/__prefix__/g, idx);
  const temp = document.createElement("tbody");
  temp.innerHTML = html;
  const row = temp.querySelector("tr");
  row.classList.remove("empty-form");
  row.style.display = "";
  row.setAttribute("data-auto", "1"); // tag auto

  const addRow = table.querySelector("tr.add-row");
  if (addRow && addRow.parentNode) addRow.parentNode.insertBefore(row, addRow);
  else table.tBodies[0].appendChild(row);

  incTotalForms(prefix);
  return { row, index: idx };
}

// recherche d’options d’étape standard
const norm = (s) => (s || "").normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase().trim();
function findStepValue(selectEl, targetName) {
  if (!selectEl) return null;
  const tgt = norm(targetName);
  for (const opt of selectEl.options) {
    const txt = norm(opt.text);
    if (txt.includes(tgt)) return opt.value;
    if ((tgt === "élévation" || tgt === "elevation") && (txt.includes("elevation") || txt.includes("élévation"))) {
      return opt.value;
    }
  }
  return null;
}
function getStepValues(table, prefix) {
  const probe =
    table.querySelector(`select[name^="${prefix}"][name$="-etape_standard"]`) ||
    table.querySelector('tr.empty-form select[name$="-etape_standard"]');
  return {
    SIGNATURE: findStepValue(probe, STEP_NAMES.SIGNATURE),
    FONDATION: findStepValue(probe, STEP_NAMES.FONDATION),
    ELEVATION: findStepValue(probe, STEP_NAMES.ELEVATION),
    PLANCHER:  findStepValue(probe, STEP_NAMES.PLANCHER),
    TOITURE:   findStepValue(probe, STEP_NAMES.TOITURE),
  };
}

// ordre
function nextOrdre(table, prefix) {
  const inputs = table.querySelectorAll(`input[name^="${prefix}"][name$="-ordre"]`);
  let max = 0;
  inputs.forEach((el) => {
    const v = parseInt(el.value || "0", 10);
    if (!isNaN(v) && v > max) max = v;
  });
  return max + 1;
}

// affectation champs ligne
function setRowFields(row, prefix, index, { etapeValue, niveau, ordre }) {
  const sel = row.querySelector(`select[name="${prefix}${index}-etape_standard"]`);
  if (sel && etapeValue != null) sel.value = etapeValue;
  const niv = row.querySelector(`input[name="${prefix}${index}-niveau"]`);
  if (niv) niv.value = (niveau ?? "") === "" ? "" : String(niveau);
  const ord = row.querySelector(`input[name="${prefix}${index}-ordre"]`);
  if (ord && typeof ordre === "number") ord.value = String(ordre);
  // on laisse l’utilisateur saisir echeance & montant_prevu manuellement
}

// nettoyage des anciennes lignes auto
function removeOldAutoRows(table) {
  const autos = table.querySelectorAll('tr[data-auto="1"]');
  autos.forEach((tr) => {
    const del = tr.querySelector('input[name$="-DELETE"]');
    if (del) {
      del.checked = true;
      tr.style.display = "none";
    } else {
      tr.remove();
    }
  });
}

// --------- helpers ajoutés pour fiabilité ---------

// 1) Réutiliser une première ligne vide existante (évite une ligne orpheline "Ordre = 1")
function findFirstBlankRow(table, prefix) {
  const rows = table.querySelectorAll('tbody tr');
  for (const tr of rows) {
    if (tr.classList.contains('empty-form') || tr.classList.contains('add-row')) continue;
    if (tr.getAttribute('data-auto') === '1') continue;

    const sel = tr.querySelector(`select[name^="${prefix}"][name$="-etape_standard"]`);
    const niv = tr.querySelector(`input[name^="${prefix}"][name$="-niveau"]`);
    const ord = tr.querySelector(`input[name^="${prefix}"][name$="-ordre"]`);

    const isBlank = sel && (!sel.value || sel.value === '')
                 && (!niv || !niv.value)
                 && (!ord || !ord.value);
    if (isBlank) return tr;
  }
  return null;
}

// 2) S'assurer que la empty-form est disponible (sinon simuler un "Ajouter...")
function ensureEmptyFormReady(table, done) {
  const hasEmpty = !!table.querySelector('tr.empty-form');
  if (hasEmpty) return done();

  const addLink = table.querySelector('tr.add-row a');
  if (addLink) {
    addLink.click();          // initialise une première ligne
    setTimeout(done, 30);     // laisse le DOM insérer la ligne
  } else {
    done(); // on tente quand même
  }
}

// séquence attendue selon N (N >= 0)
function generateSequence(N, steps) {
  const seq = [];
  if (steps.SIGNATURE) seq.push({ etapeKey: "SIGNATURE", niveau: null });
  if (steps.FONDATION) seq.push({ etapeKey: "FONDATION", niveau: null });

  if (steps.ELEVATION) {
    // niveaux 0..N-1 : ELEVATION + PLANCHER
    for (let level = 0; level < N; level++) {
      seq.push({ etapeKey: "ELEVATION", niveau: level });
      if (steps.PLANCHER) seq.push({ etapeKey: "PLANCHER", niveau: level });
    }
    // dernier niveau : ELEVATION N
    seq.push({ etapeKey: "ELEVATION", niveau: N });

    if (N === 0) {
      // RDC seul : Plancher R+0 si dispo, sinon Toiture
      if (steps.PLANCHER) seq.push({ etapeKey: "PLANCHER", niveau: 0 });
      else if (steps.TOITURE) seq.push({ etapeKey: "TOITURE", niveau: null });
    } else {
      // étages > 0 : terminer par Toiture si dispo
      if (steps.TOITURE) seq.push({ etapeKey: "TOITURE", niveau: null });
    }
  }
  return seq;
}

// -------- point d’entrée avec retry --------
(function initPhasageAuto() {
  const floorsInput = findFloorsInput();
  const table = findPhasesInlineTable();

  if (!floorsInput || !table) {
    // l’inline peut ne pas être encore monté : retente
    setTimeout(initPhasageAuto, 300);
    return;
  }

  const prefix = detectInlinePrefix(table);
  if (!prefix) {
    setTimeout(initPhasageAuto, 300);
    return;
  }

  const stepValues = getStepValues(table, prefix);
  // si "Élévation" n’existe pas dans le catalogue, on ne force rien
  if (!stepValues.ELEVATION) return;

  // --- apply : version corrigée (réutilise une ligne vide + "prime" la empty-form) ---
  const apply = () => {
    const Nraw = (floorsInput.value || '').trim();
    const N = parseInt(Nraw, 10);
    if (isNaN(N) || N < 0) return;

    ensureEmptyFormReady(table, () => {
      // re-détecte au cas où une première ligne vient d'être créée
      const _prefix = detectInlinePrefix(table) || prefix;
      const _steps  = getStepValues(table, _prefix);
      if (!_steps || !_steps.ELEVATION) return;

      // nettoie les anciennes lignes auto
      removeOldAutoRows(table);

      const seq = generateSequence(N, _steps);
      let ordre = nextOrdre(table, _prefix);

      // 1) réutiliser une 1ʳᵉ ligne vide si présente
      let reusedFirst = false;
      const blank = findFirstBlankRow(table, _prefix);
      if (blank && seq.length > 0) {
        blank.setAttribute('data-auto', '1');
        const any = blank.querySelector('input, select, textarea');
        const m = any && any.name.match(/^.+-(\d+)-/);
        const idx = m ? parseInt(m[1], 10) : 0;

        setRowFields(blank, _prefix, idx, {
          etapeValue: _steps[seq[0].etapeKey],
          niveau:     seq[0].niveau,
          ordre
        });
        ordre += 1;
        reusedFirst = true;
      }

      // 2) insérer le reste
      for (let i = reusedFirst ? 1 : 0; i < seq.length; i++) {
        const add = addInlineRow(table, _prefix);
        if (!add) break;
        setRowFields(add.row, _prefix, add.index, {
          etapeValue: _steps[seq[i].etapeKey],
          niveau:     seq[i].niveau,
          ordre
        });
        ordre += 1;
      }
    });
  };

  // premier passage & écoute des changements
  apply();
  floorsInput.addEventListener("change", apply);
})();
