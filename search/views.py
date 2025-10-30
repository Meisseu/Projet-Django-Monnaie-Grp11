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


class SearchView(LoginRequiredMixin, View):
    """Page de recherche avec filtres (connexion obligatoire)"""

    login_url = '/accounts/login/'
    redirect_field_name = 'next'

    def get(self, request):
        # Profil garanti pour l'utilisateur connecté
        profile = _get_or_create_profile(request)

        # Récupérer les paramètres de recherche
        search_query = (request.GET.get('q') or '').upper().strip()
        currency_type = request.GET.get('type', 'all')
        min_price = request.GET.get('min_price', '').strip()
        max_price = request.GET.get('max_price', '').strip()
        min_volume = request.GET.get('min_volume', '').strip()
        price_change = request.GET.get('price_change', '').strip()  # 'positive' | 'negative' | ''
        view_mode = request.GET.get('view', 'cards')  # 'cards' ou 'table'

        # Convertisseurs sécurisés
        def to_float(val, default=None):
            try:
                return float(val)
            except (TypeError, ValueError):
                return default

        min_price_f = to_float(min_price)
        max_price_f = to_float(max_price)
        min_volume_f = to_float(min_volume)

        # Récupérer tous les tickers (liste de dicts)
        all_tickers = BinanceAPIService.get_24hr_ticker() or []

        results = []
        for ticker in all_tickers:
            symbol = ticker.get('symbol', '') or ''
            if not symbol:
                continue

            # Filtrer par texte
            if search_query and search_query not in symbol:
                continue

            # Filtrer par type
            if currency_type == 'crypto':
                if not (symbol.endswith('USDT') or symbol.endswith('BUSD') or symbol.endswith('BTC')):
                    continue
            elif currency_type == 'stablecoin':
                if not any(stable in symbol for stable in ['USDT', 'USDC', 'BUSD', 'DAI']):
                    continue
            elif currency_type == 'fiat':
                if not any(fiat in symbol for fiat in ['EUR', 'GBP', 'AUD', 'CAD', 'JPY']):
                    continue

            # Valeurs numériques
            price = to_float(ticker.get('lastPrice'), 0.0)
            base_volume = to_float(ticker.get('volume'), 0.0)            # volume base asset
            quote_volume = to_float(ticker.get('quoteVolume'), 0.0)      # volume quote asset (souvent plus pertinent)
            change_pct = to_float(ticker.get('priceChangePercent'), 0.0)

            # Filtres numériques
            if min_price_f is not None and price < min_price_f:
                continue
            if max_price_f is not None and price > max_price_f:
                continue
            if min_volume_f is not None and (quote_volume or 0) < min_volume_f:
                # On utilise par défaut le quote_volume pour filtrer
                continue
            if price_change == 'positive' and (change_pct or 0) <= 0:
                continue
            if price_change == 'negative' and (change_pct or 0) >= 0:
                continue

            results.append({
                'symbol': symbol,
                'price': ticker.get('lastPrice', '0'),
                'change': ticker.get('priceChangePercent', '0'),
                'volume': BinanceAPIService.format_volume(ticker.get('volume', '0')),
                'high': ticker.get('highPrice', '0'),
                'low': ticker.get('lowPrice', '0'),
                'quote_volume': BinanceAPIService.format_volume(ticker.get('quoteVolume', '0')),
                # champs numériques pour tri fiable
                '_volume_num': quote_volume if quote_volume is not None else (base_volume or 0.0),
            })

        # Tri par volume (numérique) décroissant
        results.sort(key=lambda x: x.get('_volume_num', 0.0), reverse=True)

        # Limite des résultats
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
