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
        
        # Validation
        if not profile_type or not market_preference:
            return render(request, 'landing/index.html', {
                'error': 'Veuillez sélectionner un profil et un marché'
            })
        
        # Créer un nouveau profil utilisateur basé sur la session
        if not request.session.session_key:
            request.session.create()
        
        # Forcer la sauvegarde de la session
        request.session.modified = True
        
        # Supprimer l'ancien profil si existant
        if 'user_profile_id' in request.session:
            try:
                old_profile = UserProfile.objects.get(id=request.session['user_profile_id'])
                old_profile.delete()
            except UserProfile.DoesNotExist:
                pass
        
        try:
            # Supprimer les anciens profils avec cette session_key (nettoyage)
            UserProfile.objects.filter(session_key=request.session.session_key).delete()
            
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
            request.session.modified = True
            
            print(f"[OK] Profil cree avec succes: ID={profile.id}, Type={profile_type}, Marche={market_preference}")
            
            return redirect('home:index')
            
        except Exception as e:
            print(f"[ERREUR] Erreur lors de la creation du profil: {e}")
            return render(request, 'landing/index.html', {
                'error': f'Erreur: {str(e)}'
            })

