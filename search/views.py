from django.shortcuts import render, redirect
from django.views import View
from accounts.models import UserProfile
from api_services.binance_service import BinanceAPIService


class SearchView(View):
    """Page de recherche avec filtres"""
    
    def get(self, request):
        # Vérifier si l'utilisateur a un profil
        if 'user_profile_id' not in request.session:
            return redirect('landing:index')
        
        profile = UserProfile.objects.get(id=request.session['user_profile_id'])
        
        # Récupérer les paramètres de recherche
        search_query = request.GET.get('q', '').upper()
        currency_type = request.GET.get('type', 'all')
        min_price = request.GET.get('min_price', '')
        max_price = request.GET.get('max_price', '')
        min_volume = request.GET.get('min_volume', '')
        price_change = request.GET.get('price_change', '')
        view_mode = request.GET.get('view', 'cards')  # cards ou table
        
        # Récupérer tous les tickers
        all_tickers = BinanceAPIService.get_24hr_ticker()
        
        # Filtrer les résultats
        results = []
        for ticker in all_tickers:
            symbol = ticker.get('symbol', '')
            
            # Filtrer par recherche
            if search_query and search_query not in symbol:
                continue
            
            # Filtrer par type de monnaie
            if currency_type == 'crypto':
                if not (symbol.endswith('USDT') or symbol.endswith('BUSD') or symbol.endswith('BTC')):
                    continue
            elif currency_type == 'stablecoin':
                if not any(stable in symbol for stable in ['USDT', 'USDC', 'BUSD', 'DAI']):
                    continue
            elif currency_type == 'fiat':
                if not any(fiat in symbol for fiat in ['EUR', 'GBP', 'AUD', 'CAD', 'JPY']):
                    continue
            
            try:
                price = float(ticker.get('lastPrice', 0))
                volume = float(ticker.get('volume', 0))
                change = float(ticker.get('priceChangePercent', 0))
                
                # Filtrer par prix
                if min_price and price < float(min_price):
                    continue
                if max_price and price > float(max_price):
                    continue
                
                # Filtrer par volume
                if min_volume and volume < float(min_volume):
                    continue
                
                # Filtrer par variation de prix
                if price_change:
                    if price_change == 'positive' and change <= 0:
                        continue
                    elif price_change == 'negative' and change >= 0:
                        continue
                
                results.append({
                    'symbol': symbol,
                    'price': BinanceAPIService.format_price(ticker.get('lastPrice', '0')),
                    'change': ticker.get('priceChangePercent', '0'),
                    'volume': BinanceAPIService.format_volume(ticker.get('volume', '0')),
                    'volume_raw': volume,  # Pour le tri
                    'high': BinanceAPIService.format_price(ticker.get('highPrice', '0')),
                    'low': BinanceAPIService.format_price(ticker.get('lowPrice', '0')),
                    'quote_volume': BinanceAPIService.format_volume(ticker.get('quoteVolume', '0')),
                })
            except (ValueError, TypeError):
                continue
        
        # Trier par volume décroissant en utilisant le volume brut
        results.sort(key=lambda x: x.get('volume_raw', 0), reverse=True)
        
        # Limiter les résultats
        results = results[:100]
        
        context = {
            'profile': profile,
            'results': results,
            'search_query': search_query,
            'currency_type': currency_type,
            'min_price': min_price,
            'max_price': max_price,
            'min_volume': min_volume,
            'price_change': price_change,
            'view_mode': view_mode,
            'total_results': len(results),
        }
        
        return render(request, 'search/index.html', context)

