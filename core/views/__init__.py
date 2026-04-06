# core/views/__init__.py
"""
Package de vues LAMANE BTP — réexporte toutes les vues pour compatibilité URL.
"""
from core.views._helpers import set_global_filter  # noqa
from core.views.auth import *          # noqa
from core.views.dashboard import *     # noqa
from core.views.projets import *       # noqa
from core.views.finances import *      # noqa
from core.views.chantiers import *     # noqa
from core.views.marches import *       # noqa
from core.views.sous_traitants import *  # noqa
from core.views.rh import *            # noqa
from core.views.stock import *         # noqa
from core.views.comptabilite import *  # noqa
from core.views.tresorerie import *    # noqa
from core.views.documents import *     # noqa
from core.views.config import *        # noqa
from core.views.vitrine import *       # noqa
