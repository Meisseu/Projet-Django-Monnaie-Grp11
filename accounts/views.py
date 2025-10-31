from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.views import LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from accounts.models import UserProfile
from accounts.forms import CustomUserCreationForm, ProfileUpdateForm


class AuthView(View):
    """Page d'authentification avec choix entre connexion et inscription"""
    
    def get(self, request):
        # Si déjà connecté, rediriger vers home
        if request.user.is_authenticated:
            return redirect('home:index')
        
        return render(request, 'registration/auth.html')


class SignupView(View):
    """Vue d'inscription avec sélection de profil intégrée"""
    
    def get(self, request):
        # Si déjà connecté, rediriger vers home
        if request.user.is_authenticated:
            return redirect('home:index')
        
        form = CustomUserCreationForm()
        return render(request, 'registration/signup.html', {'form': form})

    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        
        if not form.is_valid():
            # Ré-afficher le formulaire avec les erreurs
            return render(request, 'registration/signup.html', {'form': form})

        # Crée l'utilisateur Django ET son profil (via form.save())
        user = form.save()
        
        # Connecter l'utilisateur automatiquement
        login(request, user)

        # S'assurer d'avoir une session
        if not request.session.session_key:
            request.session.save()

        # Récupérer le profil créé
        profile = UserProfile.objects.get(user=user)
        
        # Mettre à jour la session key du profil
        profile.session_key = request.session.session_key or ''
        profile.save()

        # Synchroniser la session
        request.session['user_profile_id'] = profile.id
        request.session['profile_type'] = profile.profile_type
        request.session['market_preference'] = profile.market_preference

        messages.success(request, f"Bienvenue {user.username} ! Votre compte a été créé avec succès.")

        # Respecter la redirection 'next' si présente
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url:
            return redirect(next_url)
        
        return redirect('home:index')


class SafeLogoutView(LogoutView):
    """
    Déconnexion propre : ne supprime pas le UserProfile.
    """
    def dispatch(self, request, *args, **kwargs):
        messages.info(request, "Déconnexion réussie.")
        return super().dispatch(request, *args, **kwargs)


class ProfileConfigView(LoginRequiredMixin, View):
    """Vue pour configurer/modifier le profil utilisateur"""
    
    login_url = '/accounts/login/'
    redirect_field_name = 'next'
    
    def get(self, request):
        # Récupérer ou créer le profil
        profile = UserProfile.objects.filter(user=request.user).first()
        
        if not profile:
            # Créer un profil par défaut si inexistant
            if not request.session.session_key:
                request.session.save()
            profile = UserProfile.objects.create(
                user=request.user,
                session_key=request.session.session_key or '',
                profile_type='beginner',
                market_preference='crypto'
            )
        
        form = ProfileUpdateForm(instance=profile)
        return render(request, 'registration/profile_config.html', {
            'form': form,
            'profile': profile
        })
    
    def post(self, request):
        profile = UserProfile.objects.filter(user=request.user).first()
        
        if not profile:
            messages.error(request, "Erreur : profil introuvable.")
            return redirect('home:index')
        
        form = ProfileUpdateForm(request.POST, instance=profile)
        
        if form.is_valid():
            profile = form.save()
            
            # Mettre à jour la session
            request.session['user_profile_id'] = profile.id
            request.session['profile_type'] = profile.profile_type
            request.session['market_preference'] = profile.market_preference
            
            messages.success(request, "Votre profil a été mis à jour avec succès !")
            
            # Rediriger vers 'next' ou home
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url:
                return redirect(next_url)
            
            return redirect('home:index')
        
        return render(request, 'registration/profile_config.html', {
            'form': form,
            'profile': profile
        })