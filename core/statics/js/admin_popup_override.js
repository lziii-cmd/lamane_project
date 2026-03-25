(function($) {
  $(document).ready(function () {
    $('body').on('click', '.related-widget-wrapper-link', function (event) {
      event.preventDefault();

      const url = $(this).attr('href');
      const win = window.open(url, 'popup_' + Date.now(), 'height=500,width=900,resizable=yes,scrollbars=yes');

      // Attendre un peu pour forcer le focus (certains navigateurs sont stricts)
      setTimeout(() => {
        if (win) win.focus();
      }, 200);

      // Désactive la page principale avec un overlay
      if ($('#popup-overlay').length === 0) {
        $('body').append(`
          <div id="popup-overlay"
               style="position:fixed;
                      top:0;left:0;
                      width:100vw;
                      height:100vh;
                      background:rgba(0,0,0,0.25);
                      z-index:9999;"></div>
        `);
      }
    });

    // Remplacer la fonction de fermeture de Django
    const dismissOriginal = window.dismissAddRelatedObjectPopup;
    window.dismissAddRelatedObjectPopup = function (win, newId, newRepr) {
      $('#popup-overlay').remove();
      return dismissOriginal(win, newId, newRepr);
    };
  });
})(django.jQuery);
