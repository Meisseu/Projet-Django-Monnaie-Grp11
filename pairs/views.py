from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from accounts.models import UserProfile
from api_services.binance_service import BinanceAPIService
from watchlist.models import TradingBalance, Portfolio
from datetime import datetime


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
        
        # Récupérer les informations de trading
        trading_balance, created = TradingBalance.objects.get_or_create(
            user_profile=profile
        )
        
        # Calculer la quantité totale détenue pour ce symbole
        portfolio_items = Portfolio.objects.filter(
            user_profile=profile,
            symbol=symbol.upper()
        )
        total_quantity = sum(float(item.quantity) for item in portfolio_items)
        avg_purchase_price = 0
        if portfolio_items.exists():
            total_cost = sum(float(item.quantity) * float(item.purchase_price) for item in portfolio_items)
            avg_purchase_price = total_cost / total_quantity if total_quantity > 0 else 0
        
        context = {
            'profile': profile,
            'symbol': symbol.upper(),
            'ticker': ticker_24h,
            'current_price': current_price,
            'current_price_formatted': BinanceAPIService.format_price(current_price.get('price', '0')),
            'change_1h': f"{change_1h:+.2f}",
            'change_24h': ticker_24h.get('priceChangePercent', '0'),
            'change_7d': f"{change_7d:+.2f}",
            'volume': BinanceAPIService.format_volume(ticker_24h.get('volume', '0')),
            'quote_volume': BinanceAPIService.format_volume(ticker_24h.get('quoteVolume', '0')),
            'high_24h': ticker_24h.get('highPrice', '0'),
            'low_24h': ticker_24h.get('lowPrice', '0'),
            'high_24h_formatted': BinanceAPIService.format_price(ticker_24h.get('highPrice', '0')),
            'low_24h_formatted': BinanceAPIService.format_price(ticker_24h.get('lowPrice', '0')),
            'ath': ath,
            'atl': atl,
            'ath_formatted': BinanceAPIService.format_price(str(ath)),
            'atl_formatted': BinanceAPIService.format_price(str(atl)),
            'order_book': order_book,
            'recent_trades': recent_trades[:10],
            'chart_data_1h': chart_data_1h,
            'chart_data_1d': chart_data_1d,
            'chart_data_1w': chart_data_1w,
            'similar_pairs': similar_pairs,
            # Trading info
            'trading_balance': float(trading_balance.balance),
            'held_quantity': total_quantity,
            'avg_purchase_price': avg_purchase_price,
        }
        
        return render(request, 'pairs/detail.html', context)


class PairDataAPIView(View):
    """API pour récupérer les données en temps réel d'une paire"""
    
    def get(self, request, symbol):
        data_type = request.GET.get('type', 'all')
        
        response_data = {}
        
        # Carnet d'ordres
        if data_type in ['all', 'orderbook']:
            order_book = BinanceAPIService.get_order_book(symbol.upper(), 8)
            response_data['order_book'] = {
                'bids': order_book.get('bids', [])[:8],
                'asks': order_book.get('asks', [])[:8],
            }
        
        # Transactions récentes
        if data_type in ['all', 'trades']:
            recent_trades = BinanceAPIService.get_recent_trades(symbol.upper(), 15)
            trades_formatted = []
            for trade in recent_trades:
                trade_time = datetime.fromtimestamp(trade['time'] / 1000)
                trades_formatted.append({
                    'price': BinanceAPIService.format_price(trade['price']),
                    'qty': trade['qty'],
                    'time': trade_time.strftime('%H:%M:%S'),
                })
            response_data['recent_trades'] = trades_formatted
        
        # Prix actuel et statistiques
        if data_type in ['all', 'ticker']:
            ticker = BinanceAPIService.get_24hr_ticker(symbol.upper())
            current_price = BinanceAPIService.get_ticker_price(symbol.upper())
            if ticker and current_price:
                response_data['ticker'] = {
                    'price': BinanceAPIService.format_price(current_price.get('price', '0')),
                    'change_24h': ticker.get('priceChangePercent', '0'),
                    'high_24h': BinanceAPIService.format_price(ticker.get('highPrice', '0')),
                    'low_24h': BinanceAPIService.format_price(ticker.get('lowPrice', '0')),
                    'volume': BinanceAPIService.format_volume(ticker.get('volume', '0')),
                }
        
        return JsonResponse(response_data)

