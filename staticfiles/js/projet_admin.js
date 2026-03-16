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
// Hypothèses de nom pour le champ "nombre d'étages" côté Projet (ajuste si besoin)
const FLOORS_FIELD_NAMES = ["nombre_etages", "nb_etages", "nombre_detages", "nbEtages"];

// Libellés d'étapes standard attendus (recherche insensible à la casse / accents tolérés)
const STEP_NAMES = {
  SIGNATURE: "signature",
  FONDATION: "fondation",
  ELEVATION: "élévation",   // "elevation" accepté aussi
  PLANCHER: "plancher",
  TOITURE:  "toiture"
};

// Trouve le champ "nombre d'étages"
function findFloorsInput() {
  for (const n of FLOORS_FIELD_NAMES) {
    const el = document.querySelector(`[name="${n}"]`);
    if (el) return el;
  }
  return null;
}

// Trouve la table inline des phases (tabular inline)
function findPhasesInlineTable() {
  const tables = document.querySelectorAll("div.inline-group table");
  for (const t of tables) {
    if (t.querySelector('th[class*="field-etape_standard"]')) return t;
  }
  return null;
}

// Détecte le préfixe de l'inline formset (ex: "phaseversement_set-")
function detectInlinePrefix(table) {
  const any = table.querySelector("input, select, textarea");
  if (!any || !any.name) return null;
  const m = any.name.match(/^(.+?)-\d+-/);
  return m ? m[1] + "-" : null;
}

// Accès/MAJ TOTAL_FORMS
function getFormCounts(prefix) {
  const totalEl = document.querySelector(`input[name="${prefix}TOTAL_FORMS"]`);
  const initialEl = document.querySelector(`input[name="${prefix}INITIAL_FORMS"]`);
  return {
    totalEl,
    total: totalEl ? parseInt(totalEl.value || "0", 10) : 0,
    initial: initialEl ? parseInt(initialEl.value || "0", 10) : 0
  };
}
function incTotalForms(prefix) {
  const c = getFormCounts(prefix);
  if (c.totalEl) c.totalEl.value = String(c.total + 1);
}

// Ajoute une ligne en clonant la empty-form
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
  // tag pour pouvoir nettoyer les anciennes lignes auto sans toucher au manuel
  row.setAttribute("data-auto", "1");

  const addRow = table.querySelector("tr.add-row");
  if (addRow && addRow.parentNode) addRow.parentNode.insertBefore(row, addRow);
  else table.tBodies[0].appendChild(row);

  incTotalForms(prefix);
  return { row, index: idx };
}

// Cherche la value correspondant à un libellé (option du <select> etape_standard)
function findStepValue(selectEl, targetName) {
  if (!selectEl) return null;
  const norm = (s) => (s || "").normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase().trim();
  const tgt = norm(targetName);
  for (const opt of selectEl.options) {
    const txt = norm(opt.text);
    if (txt.includes(tgt)) return opt.value;
    // tolérer "elevation" si "élévation" n'est pas accentué
    if (tgt === "élévation" || tgt === "elevation") {
      if (txt.includes("elevation") || txt.includes("élévation")) return opt.value;
    }
  }
  return null;
}

// Récupère les step values depuis un select de référence
function getStepValues(table, prefix) {
  const probe = table.querySelector(`select[name^="${prefix}"][name$="-etape_standard"]`) || table.querySelector("tr.empty-form select");
  return {
    SIGNATURE: findStepValue(probe, STEP_NAMES.SIGNATURE),
    FONDATION: findStepValue(probe, STEP_NAMES.FONDATION),
    ELEVATION: findStepValue(probe, STEP_NAMES.ELEVATION),
    PLANCHER:  findStepValue(probe, STEP_NAMES.PLANCHER),
    TOITURE:   findStepValue(probe, STEP_NAMES.TOITURE)
  };
}

// Calcule le prochain "ordre" (max existant + 1) en ignorant les lignes auto supprimées
function nextOrdre(table, prefix) {
  const inputs = table.querySelectorAll(`input[name^="${prefix}"][name$="-ordre"]`);
  let max = 0;
  inputs.forEach(el => {
    const v = parseInt(el.value || "0", 10);
    if (!isNaN(v) && v > max) max = v;
  });
  return max + 1;
}

// Fixe les champs d'une ligne
function setRowFields(row, prefix, index, { etapeValue, niveau, ordre }) {
  const sel = row.querySelector(`select[name="${prefix}${index}-etape_standard"]`);
  if (sel && etapeValue != null) sel.value = etapeValue;

  const niv = row.querySelector(`input[name="${prefix}${index}-niveau"]`);
  if (niv && (niveau ?? null) !== null) niv.value = String(niveau);
  if (niv && (niveau === null || niveau === undefined)) niv.value = ""; // pas de niveau

  const ord = row.querySelector(`input[name="${prefix}${index}-ordre"]`);
  if (ord && typeof ordre === "number") ord.value = String(ordre);
  // On laisse l'utilisateur saisir "echeance" & "montant_prevu" manuellement.
}

// Supprime les anciennes lignes auto-générées pour régénérer proprement
function removeOldAutoRows(table) {
  const autos = table.querySelectorAll('tr[data-auto="1"]');
  autos.forEach(tr => {
    // marquer pour suppression via DELETE si Django a déjà initialisé — sinon retirer du DOM
    const del = tr.querySelector('input[name$="-DELETE"]');
    if (del) {
      del.checked = true;
      tr.style.display = "none";
    } else {
      tr.remove();
      // NB: on ne décrémente pas TOTAL_FORMS car Django tolère des "trous" à l'envoi.
    }
  });
}

// Génère la séquence demandée selon N (N >= 0)
function generateSequence(N, steps) {
  // steps = {SIGNATURE, FONDATION, ELEVATION, PLANCHER, TOITURE}
  // On construit un tableau d'objets {etapeKey, niveau} (niveau null si non multi-niveau)
  const seq = [];

  if (steps.SIGNATURE) seq.push({ etapeKey: "SIGNATURE", niveau: null });
  if (steps.FONDATION) seq.push({ etapeKey: "FONDATION", niveau: null });

  // Elevation/Plancher par niveaux:
  // - pour tous les niveaux 0..N-1 : ELEVATION R+level puis PLANCHER R+level (si PLANCHER existe)
  // - enfin ELEVATION R+N puis TOITURE (si TOITURE existe)
  if (N >= 0 && steps.ELEVATION) {
    for (let level = 0; level < N; level++) {
      seq.push({ etapeKey: "ELEVATION", niveau: level });
      if (steps.PLANCHER) seq.push({ etapeKey: "PLANCHER", niveau: level });
    }
    // dernier niveau
    seq.push({ etapeKey: "ELEVATION", niveau: N });

    if (N === 0) {
      // Cas RDC seul : PLANCHER R+0 si possible, sinon TOITURE
      if (steps.PLANCHER) {
        seq.push({ etapeKey: "PLANCHER", niveau: 0 });
      } else if (steps.TOITURE) {
        seq.push({ etapeKey: "TOITURE", niveau: null });
      }
    } else {
      // Étages > 0 : on finit par TOITURE si dispo
      if (steps.TOITURE) seq.push({ etapeKey: "TOITURE", niveau: null });
    }
  }

  return seq;
}

// Point d'entrée
(function initPhasageAuto() {
  const floorsInput = findFloorsInput();
  const table = findPhasesInlineTable();
  if (!floorsInput || !table) return;
  const prefix = detectInlinePrefix(table);
  if (!prefix) return;

  const stepValues = getStepValues(table, prefix);

  // Si pas d'Élévation dans le catalogue, on s'arrête (rien n'est imposé)
  if (!stepValues.ELEVATION) return;

  const apply = () => {
    const N = parseInt(floorsInput.value || ""); // N peut être 0, 1, 2…
    if (isNaN(N) || N < 0) return;

    // Nettoyer anciens auto
    removeOldAutoRows(table);

    // Construire la séquence
    const seq = generateSequence(N, stepValues);
    let ordre = nextOrdre(table, prefix);

    // Injecter
    for (const item of seq) {
      const add = addInlineRow(table, prefix);
      if (!add) break;
      setRowFields(add.row, prefix, add.index, {
        etapeValue: stepValues[item.etapeKey],
        niveau: item.niveau,
        ordre
      });
      ordre += 1;
    }
  };

  // première application si déjà rempli
  apply();
  floorsInput.addEventListener("change", apply);
})();


// core/statics/js/phasage_generator.js
(function () {
  /**
   * Hypothèses de nom de champ pour “nombre d’étages” côté Projet.
   * Ajuste ici si ton champ s'appelle autrement (ex: "etages_nb").
   */
  var CANDIDATE_FIELD_NAMES = [
    "nb_etages",
    "nombre_etages",
    "nombre_detages",
    "nbEtages"
  ];

  /**
   * Trouve l'input du nombre d'étages dans le formulaire principal Projet
   */
  function findFloorsInput() {
    for (var i = 0; i < CANDIDATE_FIELD_NAMES.length; i++) {
      var name = CANDIDATE_FIELD_NAMES[i];
      var el = document.querySelector('[name="' + name + '"]');
      if (el) return el;
    }
    return null;
  }

  /**
   * Récupère l'inline table des phases (Django admin tabular inline).
   * On vise le group fieldset qui contient les lignes PhaseVersement.
   */
  function findPhasesInlineTable() {
    // Le group est généralement un div avec id qui finit par '-group' basé sur le related_name
    // Ici on cible par table qui contient un header de colonne "etape_standard" (name suffix)
    var tables = document.querySelectorAll("div.inline-group table");
    for (var i = 0; i < tables.length; i++) {
      if (tables[i].querySelector('th[class*="field-etape_standard"]')) {
        return tables[i];
      }
    }
    return null;
  }

  /**
   * Renvoie le prefix de l’inline (ex: "phaseversement_set-") à partir des inputs existants
   */
  function detectInlinePrefix(table) {
    var anyInput = table.querySelector("input, select, textarea");
    if (!anyInput || !anyInput.name) return null;
    var m = anyInput.name.match(/^(.+?)-\d+-/); // capture "prefix-<index>-field"
    return m ? m[1] + "-" : null; // inclut déjà le tiret final
  }

  /**
   * Compte le nombre de lignes actuelles (TOTAL_FORMS)
   */
  function getFormCounts(prefix) {
    var totalEl = document.querySelector('input[name="' + prefix + 'TOTAL_FORMS"]');
    var initialEl = document.querySelector('input[name="' + prefix + 'INITIAL_FORMS"]');
    var total = totalEl ? parseInt(totalEl.value, 10) : 0;
    var initial = initialEl ? parseInt(initialEl.value, 10) : 0;
    return { total: total, initial: initial, totalEl: totalEl };
  }

  /**
   * Ajoute une ligne à l’inline en clonant la “empty-form” de Django
   */
  function addInlineRow(table, prefix) {
    var empty = table.querySelector("tr.empty-form");
    if (!empty) return null;
    var counts = getFormCounts(prefix);
    var index = counts.total; // nouvel index

    var html = empty.outerHTML.replace(/__prefix__/g, index);
    var temp = document.createElement("tbody");
    temp.innerHTML = html;
    var newRow = temp.querySelector("tr");
    newRow.classList.remove("empty-form");
    newRow.style.display = ""; // s'assurer que la ligne est visible

    // insérer avant la ligne "add-row" si présente, sinon à la fin
    var addRow = table.querySelector("tr.add-row");
    if (addRow) {
      addRow.parentNode.insertBefore(newRow, addRow);
    } else {
      table.tBodies[0].appendChild(newRow);
    }

    // incrémente TOTAL_FORMS
    counts.totalEl.value = counts.total + 1;

    return newRow;
  }

  /**
   * Cherche la valeur de l'option "Élévation" dans le select etape_standard (si existe)
   */
  function findElevationValue(selectEl) {
    if (!selectEl) return null;
    var options = selectEl.options;
    for (var i = 0; i < options.length; i++) {
      var txt = (options[i].text || "").toLowerCase();
      if (txt.indexOf("élévation") !== -1 || txt.indexOf("elevation") !== -1) {
        return options[i].value;
      }
    }
    return null;
  }

  /**
   * Remplit une ligne avec: Étape=Élévation, Niveau, Ordre (à la suite)
   * Ne force ni la date ni le montant, l'utilisateur les saisit.
   */
  function fillElevationRow(row, prefix, index, elevationValue, ordre) {
    var sel = row.querySelector('select[name="' + prefix + index + '-etape_standard"]');
    if (sel && elevationValue !== null) {
      sel.value = elevationValue;
    }
    var niveauInput = row.querySelector('input[name="' + prefix + index + '-niveau"]');
    if (niveauInput) {
      // niveau est déjà calculé par l'appelant
    }
    var ordreInput = row.querySelector('input[name="' + prefix + index + '-ordre"]');
    if (ordreInput && typeof ordre === "number") {
      ordreInput.value = ordre;
    }
  }

  /**
   * Calcule le prochain ordre (max existant + 1)
   */
  function getNextOrdre(table, prefix) {
    var inputs = table.querySelectorAll('input[name^="' + prefix + '"][name$="-ordre"]');
    var max = 0;
    inputs.forEach(function (el) {
      var v = parseInt(el.value, 10);
      if (!isNaN(v) && v > max) max = v;
    });
    return max + 1;
  }

  /**
   * Point d’entrée: quand le champ “nombre d’étages” change,
   * on insère les lignes Élévation R+0..R+(N-1).
   */
  function bind() {
    var floorsInput = findFloorsInput();
    if (!floorsInput) return;

    var table = findPhasesInlineTable();
    if (!table) return;

    var prefix = detectInlinePrefix(table);
    if (!prefix) return;

    floorsInput.addEventListener("change", function () {
      var n = parseInt(floorsInput.value, 10);
      if (isNaN(n) || n <= 0) return;

      // détecte la valeur “Élévation” dans un select existant (ou dans la empty-form)
      var probeSelect = table.querySelector('select[name^="' + prefix + '"][name$="-etape_standard"]')
                        || table.querySelector("tr.empty-form select");
      var elevationValue = findElevationValue(probeSelect);
      if (elevationValue === null) {
        // si l'étape Élévation n’est pas dans le select, on ne fait rien
        return;
      }

      // point de départ pour l’ordre
      var ordre = getNextOrdre(table, prefix);

      // crée R+0 à R+(n-1)
      for (var level = 0; level < n; level++) {
        var newRow = addInlineRow(table, prefix);
        if (!newRow) break;

        var counts = getFormCounts(prefix);
        var index = counts.total - 1; // dernière ligne ajoutée

        // Remplit étape & ordre
        fillElevationRow(newRow, prefix, index, elevationValue, ordre);

        // Pose le niveau (0 => R+0, 1 => R+1…)
        var niv = newRow.querySelector('input[name="' + prefix + index + '-niveau"]');
        if (niv) niv.value = level;

        ordre += 1;
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bind);
  } else {
    bind();
  }
})();
