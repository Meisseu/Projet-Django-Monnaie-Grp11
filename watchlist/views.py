from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from accounts.models import UserProfile
from .models import Watchlist, Portfolio
from api_services.binance_service import BinanceAPIService
import json


class WatchlistView(View):
    """Vue pour afficher la watchlist et le portfolio"""
    
    def get(self, request):
        # Vérifier si l'utilisateur a un profil
        if 'user_profile_id' not in request.session:
            return redirect('landing:index')
        
        profile = get_object_or_404(UserProfile, id=request.session['user_profile_id'])
        
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
        total_value = 0
        total_profit_loss = 0
        
        for item in portfolio_items:
            ticker = BinanceAPIService.get_24hr_ticker(item.symbol)
            if ticker:
                current_price = float(ticker.get('lastPrice', '0'))
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


class AddToWatchlistView(View):
    """Ajouter une paire à la watchlist"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        if 'user_profile_id' not in request.session:
            return JsonResponse({'error': 'Non authentifié'}, status=401)
        
        try:
            data = json.loads(request.body)
            symbol = data.get('symbol', '').upper()
            
            profile = UserProfile.objects.get(id=request.session['user_profile_id'])
            
            # Vérifier si déjà dans la watchlist
            if Watchlist.objects.filter(user_profile=profile, symbol=symbol).exists():
                return JsonResponse({'error': 'Déjà dans la watchlist'}, status=400)
            
            # Ajouter à la watchlist
            Watchlist.objects.create(user_profile=profile, symbol=symbol)
            
            return JsonResponse({'success': True, 'message': 'Ajouté à la watchlist'})
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class RemoveFromWatchlistView(View):
    """Retirer une paire de la watchlist"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request, watchlist_id):
        if 'user_profile_id' not in request.session:
            return JsonResponse({'error': 'Non authentifié'}, status=401)
        
        try:
            profile = UserProfile.objects.get(id=request.session['user_profile_id'])
            watchlist_item = get_object_or_404(Watchlist, id=watchlist_id, user_profile=profile)
            watchlist_item.delete()
            
            return JsonResponse({'success': True, 'message': 'Retiré de la watchlist'})
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class AddToPortfolioView(View):
    """Ajouter un actif au portfolio"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        if 'user_profile_id' not in request.session:
            return JsonResponse({'error': 'Non authentifié'}, status=401)
        
        try:
            data = json.loads(request.body)
            symbol = data.get('symbol', '').upper()
            quantity = float(data.get('quantity', 0))
            purchase_price = float(data.get('purchase_price', 0))
            notes = data.get('notes', '')
            
            if quantity <= 0 or purchase_price <= 0:
                return JsonResponse({'error': 'Quantité et prix invalides'}, status=400)
            
            profile = UserProfile.objects.get(id=request.session['user_profile_id'])
            
            Portfolio.objects.create(
                user_profile=profile,
                symbol=symbol,
                quantity=quantity,
                purchase_price=purchase_price,
                notes=notes
            )
            
            return JsonResponse({'success': True, 'message': 'Ajouté au portfolio'})
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class RemoveFromPortfolioView(View):
    """Retirer un actif du portfolio"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request, portfolio_id):
        if 'user_profile_id' not in request.session:
            return JsonResponse({'error': 'Non authentifié'}, status=401)
        
        try:
            profile = UserProfile.objects.get(id=request.session['user_profile_id'])
            portfolio_item = get_object_or_404(Portfolio, id=portfolio_id, user_profile=profile)
            portfolio_item.delete()
            
            return JsonResponse({'success': True, 'message': 'Retiré du portfolio'})
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

