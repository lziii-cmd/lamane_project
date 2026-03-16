document.addEventListener('DOMContentLoaded', function () {
    function bindToggle(checkboxId, fieldId) {
        const checkbox = document.getElementById(checkboxId);
        const targetField = document.getElementById(fieldId);
        if (!checkbox || !targetField) return;

        const wrapper = targetField.closest('.form-row') || targetField.closest('.form-group');
        if (!wrapper) return;

        function toggleField() {
            wrapper.style.display = checkbox.checked ? '' : 'none';
        }

        checkbox.addEventListener('change', toggleField);
        toggleField(); // set initial state
    }

    bindToggle('id_a_piscine', 'id_volume_piscine');
    bindToggle('id_a_ascenseur', 'id_nb_ascenseurs');
    bindToggle('id_a_climatisation', 'id_nb_climatiseurs');
    bindToggle('id_a_panneau_solaire', 'id_puissance_panneaux');
});
