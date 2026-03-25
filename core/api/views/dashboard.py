from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from core.models import Projet

class DashboardStatsView(APIView):
    def get(self, request):
        today = timezone.now().date()
        start_month = today.replace(day=1)
        end_week = today + timedelta(days=7)

        projets = Projet.objects.all()
        total = projets.count()
        en_cours = projets.filter(statut='en cours').count()
        livres_ce_mois = projets.filter(statut='livré', date_fin__range=(start_month, today)).count()
        demarrant_semaine = projets.filter(date_debut__range=(today, end_week)).count()

        projets_livres = projets.exclude(date_debut=None).exclude(date_fin=None).filter(statut='livré')
        if projets_livres.exists():
            duree_moyenne = round(
                sum([(p.date_fin - p.date_debut).days for p in projets_livres]) / projets_livres.count()
            )
        else:
            duree_moyenne = 0

        data = {
            "total_projets": total,
            "projets_en_cours": en_cours,
            "projets_a_demarer_cette_semaine": demarrant_semaine,
            "projets_termines_ce_mois": livres_ce_mois,
            "duree_moyenne_projets": duree_moyenne,
        }
        return Response(data, status=status.HTTP_200_OK)
