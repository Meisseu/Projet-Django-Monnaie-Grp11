from django.shortcuts import render, redirect
from django.views import View
from accounts.models import UserProfile


class LandingView(View):
    """Page d'atterrissage - Sélection du profil"""
    
    def get(self, request):
        return render(request, 'landing/index.html')
    
    def post(self, request):
        profile_type = request.POST.get('profile_type')
        market_preference = request.POST.get('market_preference')
        
        # Créer un nouveau profil utilisateur basé sur la session
        if not request.session.session_key:
            request.session.create()
        
        # Supprimer l'ancien profil si existant
        if 'user_profile_id' in request.session:
            try:
                old_profile = UserProfile.objects.get(id=request.session['user_profile_id'])
                old_profile.delete()
            except UserProfile.DoesNotExist:
                pass
        
        # Créer le nouveau profil
        profile = UserProfile.objects.create(
            session_key=request.session.session_key,
            profile_type=profile_type,
            market_preference=market_preference
        )
        
        # Sauvegarder dans la session
        request.session['user_profile_id'] = profile.id
        request.session['profile_type'] = profile_type
        request.session['market_preference'] = market_preference
        
        return redirect('home:index')

