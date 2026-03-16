(function($) {
  $(document).ready(function () {
    // Patch du clic sur le "+" pour forcer le focus et overlay
    $('body').on('click', '.related-widget-wrapper-link', function (event) {
      const url = $(this).attr('href');
      const name = 'django_related_popup_' + Date.now();
      const win = window.open(url, name, 'height=500,width=800,resizable=yes,scrollbars=yes');
      if (win) {
        win.focus(); // ✅ Forcer le focus
      }

      if ($('#popup-overlay').length === 0) {
        $('body').append(`
          <div id="popup-overlay"
               style="position:fixed;
                      top:0; left:0;
                      width:100vw;
                      height:100vh;
                      background:rgba(0,0,0,0.25);
                      z-index:9999;"></div>
        `);
      }

      // Bloquer le comportement par défaut de Django
      event.preventDefault();
      return false;
    });

    // Nettoyage de l'overlay après fermeture
    const dismissOriginal = window.dismissAddRelatedObjectPopup;

    window.dismissAddRelatedObjectPopup = function (win, newId, newRepr) {
      $('#popup-overlay').remove();
      return dismissOriginal(win, newId, newRepr);
    };
  });
})(django.jQuery);
