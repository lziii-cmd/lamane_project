from datetime import date
from django.db.models import Count
from rest_framework.decorators import api_view
from rest_framework.response import Response
from core.models.projet import Projet

@api_view(['GET'])
def dashboard_stats(request):
    today = date.today()

    # Projets livrés (avec date de fin connue)
    projets_livres = Projet.objects.filter(date_fin__isnull=False)

    # Projets en cours : démarrés et pas encore livrés
    projets_en_cours = Projet.objects.filter(
        date_debut__lte=today,
    ).filter(
        date_fin__isnull=True
    )

    # Projets à démarrer cette semaine
    projets_semaine = Projet.objects.filter(
        date_debut__week=today.isocalendar()[1],
        date_debut__year=today.year
    )

    # Projets terminés ce mois-ci
    projets_termines_ce_mois = projets_livres.filter(
        date_fin__month=today.month,
        date_fin__year=today.year
    )

    # Durée moyenne des projets livrés
    durees = [
        (p.date_fin - p.date_debut).days
        for p in projets_livres
        if p.date_debut and p.date_fin
    ]
    moyenne_duree = sum(durees) / len(durees) if durees else 0

    data = {
        "total_projets": Projet.objects.count(),
        "projets_en_cours": projets_en_cours.count(),
        "projets_a_demarer_cette_semaine": projets_semaine.count(),
        "projets_termines_ce_mois": projets_termines_ce_mois.count(),
        "duree_moyenne_projets": round(moyenne_duree, 1),
    }

    return Response(data)
