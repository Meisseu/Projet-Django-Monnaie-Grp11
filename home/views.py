from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from accounts.models import UserProfile
from watchlist.models import Watchlist
from api_services.binance_service import BinanceAPIService


class HomeView(LoginRequiredMixin, View):
    """
    Page d'accueil avec carrousel et watchlist.
    - Exige l'authentification
    - S'assure qu'un UserProfile existe et est stocké en session
    """
    login_url = '/accounts/login/'
    redirect_field_name = 'next'

    def _get_or_create_profile(self, request):
        """
        1) Si l'utilisateur est connecté, on récupère (ou crée) le UserProfile lié au user.
        2) Sinon (théoriquement impossible ici car LoginRequiredMixin), on tente la session.
        3) On synchronise request.session['user_profile_id'].
        """
        profile = None

        # Cas standard: user connecté (grâce à LoginRequiredMixin)
        if request.user.is_authenticated:
            profile = UserProfile.objects.filter(user=request.user).first()
            if not profile:
                # Créer un profil pour ce user
                if not request.session.session_key:
                    request.session.save()
                profile = UserProfile.objects.create(
                    user=request.user,
                    session_key=request.session.session_key or '',
                    profile_type=request.session.get('profile_type', 'beginner'),
                    market_preference=request.session.get('market_preference', 'crypto'),
                )

        # Fallback : si on a un profil en session (rare ici, mais on garde la compatibilité)
        if not profile and request.session.get('user_profile_id'):
            profile = get_object_or_404(UserProfile, id=request.session['user_profile_id'])

        # Si aucun profil trouvé/créé, on peut rediriger vers la landing (au cas où)
        if not profile:
            return None

        # Synchroniser l’ID du profil en session
        request.session['user_profile_id'] = profile.id
        return profile

    def get(self, request):
        # Assurer un profil et l'enregistrer en session
        profile = self._get_or_create_profile(request)
        if profile is None:
            # Dernier recours: on renvoie vers la landing (ou signup) si vraiment pas de profil
            return redirect('landing:index')

        # Récupérer les paires populaires pour le carrousel
        popular_pairs = BinanceAPIService.get_popular_pairs()
        carousel_data = []

        for symbol in popular_pairs[:10]:  # Top 10 pour le carrousel
            ticker = BinanceAPIService.get_24hr_ticker(symbol)
            if ticker:
                # Récupérer les mini klines pour le graphique
                klines = BinanceAPIService.get_klines(symbol, '1h', 24)
                prices = [float(k[4]) for k in klines] if klines else []  # Prix de clôture

                carousel_data.append({
                    'symbol': symbol,
                    'price': ticker.get('lastPrice', '0'),
                    'change': ticker.get('priceChangePercent', '0'),
                    'volume': BinanceAPIService.format_volume(ticker.get('volume', '0')),
                    'high': ticker.get('highPrice', '0'),
                    'low': ticker.get('lowPrice', '0'),
                    'prices': prices,
                })

        # Récupérer la watchlist de l'utilisateur
        watchlist_items = Watchlist.objects.filter(user_profile=profile)
        watchlist_data = []

        for item in watchlist_items:
            ticker = BinanceAPIService.get_24hr_ticker(item.symbol)
            if ticker:
                watchlist_data.append({
                    'id': item.id,
                    'symbol': item.symbol,
                    'price': ticker.get('lastPrice', '0'),
                    'change': ticker.get('priceChangePercent', '0'),
                    'volume': BinanceAPIService.format_volume(ticker.get('volume', '0')),
                })

        context = {
            'profile': profile,
            'carousel_items': carousel_data,
            'watchlist': watchlist_data,
        }

        return render(request, 'home/index.html', context)