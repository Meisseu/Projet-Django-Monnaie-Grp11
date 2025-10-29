from django.shortcuts import render, redirect
from django.views import View
from accounts.models import UserProfile
from api_services.binance_service import BinanceAPIService


class PairDetailView(View):
    """Page détaillée d'une paire de trading"""
    
    def get(self, request, symbol):
        # Vérifier si l'utilisateur a un profil
        if 'user_profile_id' not in request.session:
            return redirect('landing:index')
        
        profile = UserProfile.objects.get(id=request.session['user_profile_id'])
        
        # Récupérer les informations de la paire
        ticker_24h = BinanceAPIService.get_24hr_ticker(symbol.upper())
        
        if not ticker_24h:
            return render(request, 'pairs/not_found.html', {'symbol': symbol})
        
        # Récupérer le prix actuel
        current_price = BinanceAPIService.get_ticker_price(symbol.upper())
        
        # Récupérer les klines pour différentes périodes
        klines_1h = BinanceAPIService.get_klines(symbol.upper(), '1h', 24)
        klines_1d = BinanceAPIService.get_klines(symbol.upper(), '1d', 30)
        klines_1w = BinanceAPIService.get_klines(symbol.upper(), '1w', 52)
        
        # Formater les données pour les graphiques
        chart_data_1h = {
            'labels': [i for i in range(len(klines_1h))],
            'prices': [float(k[4]) for k in klines_1h],  # Prix de clôture
        }
        
        chart_data_1d = {
            'labels': [i for i in range(len(klines_1d))],
            'prices': [float(k[4]) for k in klines_1d],
        }
        
        chart_data_1w = {
            'labels': [i for i in range(len(klines_1w))],
            'prices': [float(k[4]) for k in klines_1w],
        }
        
        # Récupérer le carnet d'ordres
        order_book = BinanceAPIService.get_order_book(symbol.upper(), 10)
        
        # Récupérer les transactions récentes
        recent_trades = BinanceAPIService.get_recent_trades(symbol.upper(), 20)
        
        # Calculer les variations
        price_1h = float(klines_1h[-1][4]) if klines_1h else 0
        price_24h = float(klines_1d[-1][4]) if len(klines_1d) > 1 else price_1h
        price_7d = float(klines_1d[-7][4]) if len(klines_1d) > 7 else price_24h
        current = float(ticker_24h.get('lastPrice', 0))
        
        change_1h = ((current - price_1h) / price_1h * 100) if price_1h > 0 else 0
        change_7d = ((current - price_7d) / price_7d * 100) if price_7d > 0 else 0
        
        # Calculer ATH et ATL des 52 dernières semaines
        all_prices = [float(k[2]) for k in klines_1w]  # Prix high
        ath = max(all_prices) if all_prices else current
        
        all_lows = [float(k[3]) for k in klines_1w]  # Prix low
        atl = min(all_lows) if all_lows else current
        
        # Trouver des paires similaires (même quote currency)
        quote_currency = symbol[-4:] if len(symbol) > 4 else 'USDT'
        all_tickers = BinanceAPIService.get_24hr_ticker()
        similar_pairs = []
        
        for ticker in all_tickers:
            tick_symbol = ticker.get('symbol', '')
            if tick_symbol.endswith(quote_currency) and tick_symbol != symbol.upper():
                similar_pairs.append({
                    'symbol': tick_symbol,
                    'price': ticker.get('lastPrice', '0'),
                    'change': ticker.get('priceChangePercent', '0'),
                })
                if len(similar_pairs) >= 5:
                    break
        
        context = {
            'profile': profile,
            'symbol': symbol.upper(),
            'ticker': ticker_24h,
            'current_price': current_price,
            'change_1h': f"{change_1h:+.2f}",
            'change_24h': ticker_24h.get('priceChangePercent', '0'),
            'change_7d': f"{change_7d:+.2f}",
            'volume': BinanceAPIService.format_volume(ticker_24h.get('volume', '0')),
            'quote_volume': BinanceAPIService.format_volume(ticker_24h.get('quoteVolume', '0')),
            'high_24h': ticker_24h.get('highPrice', '0'),
            'low_24h': ticker_24h.get('lowPrice', '0'),
            'ath': ath,
            'atl': atl,
            'order_book': order_book,
            'recent_trades': recent_trades[:10],
            'chart_data_1h': chart_data_1h,
            'chart_data_1d': chart_data_1d,
            'chart_data_1w': chart_data_1w,
            'similar_pairs': similar_pairs,
        }
        
        return render(request, 'pairs/detail.html', context)

