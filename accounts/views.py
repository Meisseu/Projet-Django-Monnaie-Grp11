from django.shortcuts import redirect
from django.views import View
from .models import UserProfile
from watchlist.models import Watchlist, Portfolio


class LogoutView(View):
    """Vue pour déconnexion - efface la session et redirige vers la landing page"""
    
    def get(self, request):
        # Supprimer le profil de la session
        if 'user_profile_id' in request.session:
            profile_id = request.session['user_profile_id']
            
            # Supprimer la watchlist et le portfolio associés
            try:
                profile = UserProfile.objects.get(id=profile_id)
                Watchlist.objects.filter(user_profile=profile).delete()
                Portfolio.objects.filter(user_profile=profile).delete()
                profile.delete()
            except UserProfile.DoesNotExist:
                pass
            
            # Vider la session
            request.session.flush()
        
        return redirect('landing:index')

