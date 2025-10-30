from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.views import LogoutView
from django.contrib import messages

from accounts.models import UserProfile


class SignupView(View):
    def get(self, request):
        return render(request, 'registration/signup.html', {'form': UserCreationForm()})

    def post(self, request):
        form = UserCreationForm(request.POST)
        if not form.is_valid():
            # Ré-afficher le formulaire avec les erreurs
            return render(request, 'registration/signup.html', {'form': form})

        # Crée l'utilisateur Django
        user = form.save()
        login(request, user)

        # On s'assure d'avoir une session
        if not request.session.session_key:
            request.session.save()

        # Essayer de récupérer un profil de session existant (anonyme)
        upid = request.session.get('user_profile_id')
        profile = None
        if upid:
            try:
                candidate = UserProfile.objects.get(id=upid)
                # On NE rattache que s'il n'est pas déjà lié à un autre user
                if candidate.user is None:
                    profile = candidate
            except UserProfile.DoesNotExist:
                profile = None

        # Créer le profil s'il n'existe pas
        if profile is None:
            profile = UserProfile.objects.filter(user=user).first()
        if profile is None:
            profile = UserProfile.objects.create(
                user=user,
                session_key=request.session.session_key or '',
                profile_type=request.session.get('profile_type', 'beginner'),
                market_preference=request.session.get('market_preference', 'crypto'),
            )
        else:
            # Mettre à jour et lier au user
            profile.user = user
            profile.session_key = request.session.session_key or ''
            # On conserve profile_type / market_preference si déjà saisis via la landing
            if request.session.get('profile_type'):
                profile.profile_type = request.session['profile_type']
            if request.session.get('market_preference'):
                profile.market_preference = request.session['market_preference']
            profile.save()

        # Synchroniser la session
        request.session['user_profile_id'] = profile.id
        request.session['profile_type'] = profile.profile_type
        request.session['market_preference'] = profile.market_preference

        messages.success(request, "Inscription réussie, bienvenue !")

        # Respecter la redirection 'next' si présente
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('home:index')


class SafeLogoutView(LogoutView):
    """
    Déconnexion propre : ne supprime pas le UserProfile.
    (Tu avais une version simple – on garde, avec un message.)
    """
    def dispatch(self, request, *args, **kwargs):
        messages.info(request, "Déconnexion réussie.")
        return super().dispatch(request, *args, **kwargs)
