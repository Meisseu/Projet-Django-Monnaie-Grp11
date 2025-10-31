from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from accounts.models import UserProfile
from api_services.binance_service import BinanceAPIService


def _get_or_create_profile(request):
    """
    Récupère (ou crée) le UserProfile lié à l'utilisateur connecté
    et synchronise son id dans la session (user_profile_id).
    """
    profile = UserProfile.objects.filter(user=request.user).first()
    if not profile:
        if not request.session.session_key:
            request.session.save()
        profile = UserProfile.objects.create(
            user=request.user,
            session_key=request.session.session_key or '',
            profile_type=request.session.get('profile_type', 'beginner'),
            market_preference=request.session.get('market_preference', 'crypto'),
        )
    request.session['user_profile_id'] = profile.id
    return profile


class PairDetailView(LoginRequiredMixin, View):
    """Page détaillée d'une paire de trading (connexion obligatoire)"""

    login_url = '/accounts/login/'
    redirect_field_name = 'next'

    def get(self, request, symbol):
        # Profil garanti pour l'utilisateur connecté
        profile = _get_or_create_profile(request)

        sym = (symbol or "").upper()

        # 24h ticker
        ticker_24h = BinanceAPIService.get_24hr_ticker(sym)
        if not ticker_24h:
            return render(request, 'pairs/not_found.html', {'symbol': sym})

        # Prix actuel
        current_price = BinanceAPIService.get_ticker_price(sym)

        # Kliness (peuvent être vides)
        klines_1h = BinanceAPIService.get_klines(sym, '1h', 24) or []
        klines_1d = BinanceAPIService.get_klines(sym, '1d', 30) or []
        klines_1w = BinanceAPIService.get_klines(sym, '1w', 52) or []

        # Helpers sécurisés
        def safe_close(k):  # kline item -> close price float
            try:
                return float(k[4])
            except Exception:
                return 0.0

        def list_close(kl):
            return [safe_close(k) for k in kl]

        # Données graphiques
        chart_data_1h = {
            'labels': list(range(len(klines_1h))),
            'prices': list_close(klines_1h),
        }
        chart_data_1d = {
            'labels': list(range(len(klines_1d))),
            'prices': list_close(klines_1d),
        }
        chart_data_1w = {
            'labels': list(range(len(klines_1w))),
            'prices': list_close(klines_1w),
        }

        # Carnet d'ordres & trades récents
        order_book = BinanceAPIService.get_order_book(sym, 10) or {}
        recent_trades = BinanceAPIService.get_recent_trades(sym, 20) or []

        # Variations 1h / 7j
        try:
            current = float(ticker_24h.get('lastPrice', 0) or 0)
        except Exception:
            current = 0.0

        price_1h = safe_close(klines_1h[-1]) if klines_1h else 0.0
        # Pour 24h on utilise directement le % du ticker (plus fiable côté Binance)
        if len(klines_1d) > 7:
            price_7d = safe_close(klines_1d[-7])
        else:
            price_7d = price_1h or current

        change_1h = ((current - price_1h) / price_1h * 100) if price_1h > 0 else 0.0
        change_24h = ticker_24h.get('priceChangePercent', '0')
        change_7d = ((current - price_7d) / price_7d * 100) if price_7d > 0 else 0.0

        # ATH / ATL sur 52 semaines (via klines 1w)
        def safe_high(k):
            try:
                return float(k[2])
            except Exception:
                return None

        def safe_low(k):
            try:
                return float(k[3])
            except Exception:
                return None

        highs = [h for h in (safe_high(k) for k in klines_1w) if h is not None]
        lows = [l for l in (safe_low(k) for k in klines_1w) if l is not None]

        ath = max(highs) if highs else current
        atl = min(lows) if lows else current

        # Paires similaires (même quote currency)
        # On détecte la quote via une liste de suffixes fréquents
        known_quotes = ['USDT', 'BUSD', 'USDC', 'DAI', 'BTC', 'ETH', 'BNB', 'EUR', 'GBP', 'AUD', 'CAD', 'JPY', 'TRY', 'BRL', 'RUB']
        quote_currency = None
        for q in sorted(known_quotes, key=len, reverse=True):
            if sym.endswith(q):
                quote_currency = q
                break
        if not quote_currency:
            # fallback sur 4 derniers caractères (ex. 'USDT')
            quote_currency = sym[-4:] if len(sym) >= 4 else 'USDT'

        all_tickers = BinanceAPIService.get_24hr_ticker() or []
        similar_pairs = []
        for t in all_tickers:
            tsym = t.get('symbol') or ''
            if tsym.endswith(quote_currency) and tsym != sym:
                similar_pairs.append({
                    'symbol': tsym,
                    'price': t.get('lastPrice', '0'),
                    'change': t.get('priceChangePercent', '0'),
                })
                if len(similar_pairs) >= 5:
                    break

        # Formatages pratiques
        volume_fmt = BinanceAPIService.format_volume(ticker_24h.get('volume', '0'))
        quote_volume_fmt = BinanceAPIService.format_volume(ticker_24h.get('quoteVolume', '0'))

        context = {
            'profile': profile,
            'symbol': sym,
            'ticker': ticker_24h,
            'current_price': current_price,
            'change_1h': f"{change_1h:+.2f}",
            'change_24h': change_24h,
            'change_7d': f"{change_7d:+.2f}",
            'volume': volume_fmt,
            'quote_volume': quote_volume_fmt,
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