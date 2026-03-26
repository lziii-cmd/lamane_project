"""
Reusable pagination helper for LAMANE list views.

Usage in a view:
    from core.pagination import paginate_queryset

    def my_list_view(request):
        qs = MyModel.objects.all()
        # ... apply filters ...
        page_obj = paginate_queryset(request, qs, per_page=20)
        return render(request, 'template.html', {'page_obj': page_obj, ...})

In the template:
    {% for item in page_obj %}
      ... render item ...
    {% endfor %}
    {% include "lamane/includes/pagination.html" %}

The pagination template automatically:
  - Shows page numbers with ellipsis for large sets
  - Preserves all existing GET parameters (search, filters, etc.)
  - Matches the dark/light theme via CSS variables
  - Is responsive (stacks on mobile)

Views that need pagination (iterate over page_obj instead of raw queryset):
  - projets_list_view        -> template: projets_list.html       (iterates: projets_data)
  - achats_list_view         -> template: achats_list.html        (iterates: achats)
  - versements_view          -> template: versements_list.html    (iterates: versements)
  - bons_sortie_list_view    -> template: bons_sortie.html        (iterates: bons)
  - materiaux_list_view      -> template: materiaux_list.html     (iterates: materiaux)
  - fournisseurs_view        -> template: fournisseurs.html       (iterates: fournisseurs)
  - clients_view             -> template: clients_list.html       (iterates: clients)
  - sous_traitants_view      -> template: sous_traitants.html     (iterates: sous_traitants)
  - rh_view                  -> template: rh.html                 (iterates: employes)
  - marches_view             -> template: marches.html            (iterates: marches)
  - comptabilite_journal_view -> template: (inline)               (iterates: ecritures)
  - documents_btp_view       -> template: (inline)                (iterates: documents)
  - bordereaux_view          -> template: (inline)                (iterates: bordereaux)
  - dgd_list_view            -> template: (inline)                (iterates: dgds)
"""

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def paginate_queryset(request, queryset, per_page=20):
    """
    Paginate a queryset and return the page object.

    Args:
        request: The Django HttpRequest (reads 'page' from GET params).
        queryset: A Django QuerySet or list to paginate.
        per_page: Number of items per page (default: 20).

    Returns:
        A Page object that can be iterated in templates.
        The Page object also carries .paginator, .number, .has_previous,
        .has_next, etc. for the pagination template to use.
    """
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    return page_obj
