from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.mixins import LoginRequiredMixin

from accounts.models import UserProfile
from .models import Watchlist, Portfolio
from api_services.binance_service import BinanceAPIService

import json


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


class WatchlistView(LoginRequiredMixin, View):
    """Vue pour afficher la watchlist et le portfolio (requiert connexion)"""

    login_url = '/accounts/login/'
    redirect_field_name = 'next'

    def get(self, request):
        # Profil garanti pour l'utilisateur connecté
        profile = _get_or_create_profile(request)

        # Récupérer la watchlist
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
                    'high': ticker.get('highPrice', '0'),
                    'low': ticker.get('lowPrice', '0'),
                })

        # Récupérer le portfolio
        portfolio_items = Portfolio.objects.filter(user_profile=profile)
        portfolio_data = []
        total_value = 0.0
        total_profit_loss = 0.0

        for item in portfolio_items:
            ticker = BinanceAPIService.get_24hr_ticker(item.symbol)
            if ticker:
                current_price = float(ticker.get('lastPrice', '0') or 0)
                current_value = item.current_value(current_price)
                profit_loss = item.profit_loss(current_price)
                profit_loss_pct = item.profit_loss_percent(current_price)

                portfolio_data.append({
                    'id': item.id,
                    'symbol': item.symbol,
                    'quantity': float(item.quantity),
                    'purchase_price': float(item.purchase_price),
                    'current_price': current_price,
                    'current_value': current_value,
                    'profit_loss': profit_loss,
                    'profit_loss_percent': profit_loss_pct,
                    'notes': item.notes,
                })

                total_value += current_value
                total_profit_loss += profit_loss

        context = {
            'profile': profile,
            'watchlist': watchlist_data,
            'portfolio': portfolio_data,
            'total_value': total_value,
            'total_profit_loss': total_profit_loss,
        }

        return render(request, 'watchlist/watchlist.html', context)


class AddToWatchlistView(LoginRequiredMixin, View):
    """Ajouter une paire à la watchlist (POST JSON)"""

    login_url = '/accounts/login/'
    redirect_field_name = 'next'

    # Tu utilises des requêtes JSON (fetch) → on garde csrf_exempt ici
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        try:
            profile = _get_or_create_profile(request)

            data = json.loads(request.body or '{}')
            symbol = (data.get('symbol') or '').upper().strip()

            if not symbol:
                return JsonResponse({'error': 'Symbole requis'}, status=400)

            # Déjà présent ?
            if Watchlist.objects.filter(user_profile=profile, symbol=symbol).exists():
                return JsonResponse({'error': 'Déjà dans la watchlist'}, status=400)

            Watchlist.objects.create(user_profile=profile, symbol=symbol)
            return JsonResponse({'success': True, 'message': 'Ajouté à la watchlist'})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON invalide'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class RemoveFromWatchlistView(LoginRequiredMixin, View):
    """Retirer une paire de la watchlist (POST)"""

    login_url = '/accounts/login/'
    redirect_field_name = 'next'

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, watchlist_id):
        try:
            profile = _get_or_create_profile(request)
            watchlist_item = get_object_or_404(Watchlist, id=watchlist_id, user_profile=profile)
            watchlist_item.delete()
            return JsonResponse({'success': True, 'message': 'Retiré de la watchlist'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class AddToPortfolioView(LoginRequiredMixin, View):
    """Ajouter un actif au portfolio (POST JSON)"""

    login_url = '/accounts/login/'
    redirect_field_name = 'next'

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        try:
            profile = _get_or_create_profile(request)

            data = json.loads(request.body or '{}')
            symbol = (data.get('symbol') or '').upper().strip()
            quantity = float(data.get('quantity') or 0)
            purchase_price = float(data.get('purchase_price') or 0)
            notes = data.get('notes') or ''

            if not symbol:
                return JsonResponse({'error': 'Symbole requis'}, status=400)
            if quantity <= 0 or purchase_price <= 0:
                return JsonResponse({'error': 'Quantité et prix doivent être > 0'}, status=400)

            Portfolio.objects.create(
                user_profile=profile,
                symbol=symbol,
                quantity=quantity,
                purchase_price=purchase_price,
                notes=notes
            )

            return JsonResponse({'success': True, 'message': 'Ajouté au portfolio'})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON invalide'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class RemoveFromPortfolioView(LoginRequiredMixin, View):
    """Retirer un actif du portfolio (POST)"""

    login_url = '/accounts/login/'
    redirect_field_name = 'next'

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, portfolio_id):
        try:
            profile = _get_or_create_profile(request)
            portfolio_item = get_object_or_404(Portfolio, id=portfolio_id, user_profile=profile)
            portfolio_item.delete()
            return JsonResponse({'success': True, 'message': 'Retiré du portfolio'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)