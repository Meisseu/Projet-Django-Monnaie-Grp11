from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from accounts.models import UserProfile
from watchlist.models import Watchlist
from api_services.binance_service import BinanceAPIService


class HomeView(View):
    """Page d'accueil avec carrousel et watchlist"""
    
    def get(self, request):
        # Vérifier si l'utilisateur a un profil
        if 'user_profile_id' not in request.session:
            return redirect('landing:index')
        
        profile = get_object_or_404(UserProfile, id=request.session['user_profile_id'])
        
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

