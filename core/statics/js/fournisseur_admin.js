// static/js/fournisseur_admin.js
document.addEventListener("DOMContentLoaded", function () {
    function toggleFournisseurFields() {
        const checkbox = document.querySelector("#id_est_moral");
        const entrepriseFields = document.querySelectorAll(
            "#id_entreprise, #id_ninea"
        );
        const personneFields = document.querySelectorAll(
            "#id_prenom, #id_nom, #id_numero_identite, #id_sexe"
        );

        if (checkbox.checked) {
            entrepriseFields.forEach((el) => el.closest(".form-row").style.display = "");
            personneFields.forEach((el) => el.closest(".form-row").style.display = "none");
        } else {
            entrepriseFields.forEach((el) => el.closest(".form-row").style.display = "none");
            personneFields.forEach((el) => el.closest(".form-row").style.display = "");
        }
    }

    const checkbox = document.querySelector("#id_est_moral");
    if (checkbox) {
        checkbox.addEventListener("change", toggleFournisseurFields);
        toggleFournisseurFields();
    }
});
