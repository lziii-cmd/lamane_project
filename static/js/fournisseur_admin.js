// static/js/fournisseur_admin.js
(function () {
  console.log("fournisseur_admin.js loaded");

  // utilitaires
  const qs  = (s, r=document) => r.querySelector(s);
  const show = (el, on) => { if (el) el.style.display = on ? "" : "none"; };

  // récupère la "row" d'un champ admin: compatible form-row / form-group
  function getRow(fieldName) {
    return qs(`.form-row.field-${fieldName}, .form-group.field-${fieldName}`);
  }

  function setup() {
    const estMoral = qs("#id_est_moral");
    if (!estMoral) return;

    // lignes "Entreprise"
    const rowEntreprise = getRow("entreprise");
    const rowNinea      = getRow("ninea");

    // lignes "Personne physique"
    const rowPrenom     = getRow("prenom");
    const rowNom        = getRow("nom");
    const rowSexe       = getRow("sexe");
    const rowNumId      = getRow("numero_identite");
    const rowPhoto      = getRow("photo_identite"); // ignore si non présent

    // fieldsets (bandeaux) : on remonte du premier champ de chaque groupe
    const fsEntreprise  = rowEntreprise ? rowEntreprise.closest("fieldset") : null;
    const fsPersonne    = rowPrenom ? rowPrenom.closest("fieldset") : null;

    function toggle() {
      const isMoral = !!estMoral.checked;

      // afficher / masquer lignes
      show(rowEntreprise, isMoral);
      show(rowNinea,      isMoral);

      show(rowPrenom,     !isMoral);
      show(rowNom,        !isMoral);
      show(rowSexe,       !isMoral);
      show(rowNumId,      !isMoral);
      show(rowPhoto,      !isMoral);

      // afficher / masquer bandeaux (fieldsets)
      show(fsEntreprise, isMoral);
      show(fsPersonne,   !isMoral);
    }

    toggle(); // init
    estMoral.addEventListener("change", toggle);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setup);
  } else {
    setup();
  }
})();
