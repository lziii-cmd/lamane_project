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
