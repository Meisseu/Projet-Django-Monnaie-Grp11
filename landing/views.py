from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages

from accounts.models import UserProfile


class LandingView(View):
    """Page d'atterrissage - Sélection du profil (publique)"""

    def get(self, request):
        # Si l'utilisateur est connecté ET qu'il a déjà un profil, on garde la landing accessible,
        # mais on s'assure de synchroniser l'id en session pour le reste du site.
        if request.user.is_authenticated:
            profile = UserProfile.objects.filter(user=request.user).first()
            if profile:
                request.session['user_profile_id'] = profile.id
                request.session['profile_type'] = profile.profile_type
                request.session['market_preference'] = profile.market_preference
        return render(request, 'landing/index.html')

    def post(self, request):
        profile_type = (request.POST.get('profile_type') or '').strip() or 'beginner'
        market_preference = (request.POST.get('market_preference') or '').strip() or 'crypto'

        # S'assurer d'avoir une session
        if not request.session.session_key:
            request.session.save()

        if request.user.is_authenticated:
            # Utilisateur connecté : on met à jour ou crée son profil persistant
            profile = UserProfile.objects.filter(user=request.user).first()
            if profile:
                profile.profile_type = profile_type
                profile.market_preference = market_preference
                profile.session_key = request.session.session_key or ''
                profile.save()
            else:
                profile = UserProfile.objects.create(
                    user=request.user,
                    session_key=request.session.session_key or '',
                    profile_type=profile_type,
                    market_preference=market_preference,
                )
            # Sync session
            request.session['user_profile_id'] = profile.id
            request.session['profile_type'] = profile_type
            request.session['market_preference'] = market_preference
            messages.success(request, "Préférences mises à jour.")
            return redirect('home:index')

        # Utilisateur anonyme : on réutilise le profil de session si possible
        profile = None
        upid = request.session.get('user_profile_id')
        if upid:
            try:
                candidate = get_object_or_404(UserProfile, id=upid)
                if candidate.user is None:
                    profile = candidate
            except Exception:
                profile = None

        if profile:
            # Mettre à jour le profil de session existant
            profile.profile_type = profile_type
            profile.market_preference = market_preference
            profile.session_key = request.session.session_key or ''
            profile.save()
        else:
            # Créer un nouveau profil anonyme basé sur la session
            profile = UserProfile.create(
                session_key=request.session.session_key or '',
                profile_type=profile_type,
                market_preference=market_preference
            ) if hasattr(UserProfile, 'create') else UserProfile.objects.create(
                session_key=request.session.session_key or '',
                profile_type=profile_type,
                market_preference=market_preference
            )

        # Sync session
        request.session['user_profile_id'] = profile.id
        request.session['profile_type'] = profile_type
        request.session['market_preference'] = market_preference

        # Pour un anonyme, aller sur /home/ déclenchera la redirection vers /accounts/login/
        # grâce au LoginRequiredMixin. Ça garde un flow simple : choisir → se connecter.
        return redirect('home:index')
