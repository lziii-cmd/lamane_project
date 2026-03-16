// static/js/proprietaire_admin.js
(function () {
  // petit log pour confirmer le chargement
  console.log("proprietaire_admin.js loaded");

  const qs  = (sel, root=document) => root.querySelector(sel);
  const show = (el, on) => { if (el) el.style.display = on ? "" : "none"; };

  // compatible Django admin: .form-row (Django <4) ou .form-group (Django 4/5)
  function getRow(fieldName) {
    return qs(`.form-row.field-${fieldName}, .form-group.field-${fieldName}`);
  }

  function setup() {
    const estMoral = qs("#id_est_moral");
    if (!estMoral) return;

    // lignes "Entreprise"
    const rowEntreprise = getRow("entreprise");
    const rowNinea      = getRow("ninea");

    // lignes "Personne Physique"
    const rowPrenom     = getRow("prenom");
    const rowNom        = getRow("nom");
    const rowSexe       = getRow("sexe");
    const rowNumId      = getRow("numero_identite");
    const rowPhoto      = getRow("photo_identite"); // ignoré si non présent

    // fieldsets (bandeaux titres) : on remonte depuis une ligne de chaque groupe
    const fsEntreprise  = rowEntreprise ? rowEntreprise.closest("fieldset") : null;
    const fsPersonne    = rowPrenom ? rowPrenom.closest("fieldset") : null;

    function toggle() {
      const isEntreprise = !!estMoral.checked;

      // afficher/masquer lignes
      show(rowEntreprise, isEntreprise);
      show(rowNinea,      isEntreprise);

      show(rowPrenom,     !isEntreprise);
      show(rowNom,        !isEntreprise);
      show(rowSexe,       !isEntreprise);
      show(rowNumId,      !isEntreprise);
      show(rowPhoto,      !isEntreprise);

      // afficher/masquer les bandeaux (fieldsets entiers)
      show(fsEntreprise, isEntreprise);
      show(fsPersonne,   !isEntreprise);
    }

    // état initial + écoute du toggle
    toggle();
    estMoral.addEventListener("change", toggle);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setup);
  } else {
    setup();
  }
})();
