// static/js/proprietaire_admin.js

document.addEventListener('DOMContentLoaded', function () {
    const checkboxEntreprise = document.getElementById('id_est_moral');
    const blockEntreprise = document.querySelector('.form-row.field-entreprise, .form-row.field-ninea');
    const blockPersonne = document.querySelectorAll('.form-row.field-prenom, .form-row.field-nom, .form-row.field-numero_identite, .form-row.field-sexe');

    function toggleChamps() {
        const isEntreprise = checkboxEntreprise.checked;

        // Affiche ou masque les champs entreprise
        document.querySelector('.form-row.field-entreprise').style.display = isEntreprise ? 'block' : 'none';
        document.querySelector('.form-row.field-ninea').style.display = isEntreprise ? 'block' : 'none';

        // Affiche ou masque les champs personne physique
        document.querySelector('.form-row.field-prenom').style.display = isEntreprise ? 'none' : 'block';
        document.querySelector('.form-row.field-nom').style.display = isEntreprise ? 'none' : 'block';
        document.querySelector('.form-row.field-numero_identite').style.display = isEntreprise ? 'none' : 'block';
        document.querySelector('.form-row.field-sexe').style.display = isEntreprise ? 'none' : 'block';
    }

    if (checkboxEntreprise) {
        checkboxEntreprise.addEventListener('change', toggleChamps);
        toggleChamps(); // appel initial
    }
});
