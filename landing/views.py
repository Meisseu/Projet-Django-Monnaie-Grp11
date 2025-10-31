from django.shortcuts import render, redirect
from django.views import View

from accounts.models import UserProfile


class LandingView(View):
    """Page d'atterrissage - Page d'accueil publique avec Connexion/Inscription"""

    def get(self, request):
        # Si l'utilisateur est déjà connecté, rediriger vers la page d'accueil
        if request.user.is_authenticated:
            return redirect('home:index')
        
        return render(request, 'landing/index.html')