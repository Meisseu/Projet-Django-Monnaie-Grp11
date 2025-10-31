"""
Vues pour la page Portfolio avec comptes multiples et graphiques
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Q, DecimalField
from django.db.models.functions import Coalesce
from datetime import datetime, timedelta
import json as json_lib

from accounts.models import UserProfile
from .models import TradingAccount, Trade, WalletHistory, Portfolio
from .portfolio_utils import initialize_account_history
from api_services.binance_service import BinanceAPIService


def _get_or_create_profile(request):
    """Récupère (ou crée) le UserProfile lié à l'utilisateur connecté"""
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


def _get_or_create_account(profile, account_type='trading'):
    """Récupère ou crée un compte de trading"""
    account, created = TradingAccount.objects.get_or_create(
        user_profile=profile,
        account_type=account_type,
        defaults={
            'balance': 10000.00,
            'initial_balance': 10000.00,
        }
    )
    # Initialiser l'historique si c'est un nouveau compte
    if created:
        initialize_account_history(account)
    return account


class PortfolioView(LoginRequiredMixin, View):
    """Page principale du Portfolio avec tous les comptes"""
    
    login_url = '/accounts/login/'
    redirect_field_name = 'next'
    
    def get(self, request):
        profile = _get_or_create_profile(request)
        
        # Créer les comptes s'ils n'existent pas
        finance_account = _get_or_create_account(profile, 'finance')
        trading_account = _get_or_create_account(profile, 'trading')
        margin_account = _get_or_create_account(profile, 'margin')
        
        accounts = [finance_account, trading_account, margin_account]
        
        # Calculer les totaux globaux
        total_balance = sum(float(acc.balance) for acc in accounts)
        total_initial = sum(float(acc.initial_balance) for acc in accounts)
        total_pnl = total_balance - total_initial
        total_pnl_percent = ((total_balance - total_initial) / total_initial * 100) if total_initial > 0 else 0
        
        # Compter les trades globaux
        total_trades = Trade.objects.filter(account__in=accounts).count()
        
        # Trades récents (derniers 10)
        recent_trades = Trade.objects.filter(account__in=accounts).select_related('account', 'related_trade')[:10]
        
        # Préparer les données pour les graphiques
        account_charts = {}
        for account in accounts:
            # Récupérer l'historique du wallet (derniers 30 jours)
            history = WalletHistory.objects.filter(
                account=account,
                timestamp__gte=datetime.now() - timedelta(days=30)
            ).order_by('timestamp')[:100]
            
            chart_data = {
                'labels': [h.timestamp.strftime('%d/%m %H:%M') for h in history],
                'balances': [float(h.balance) for h in history],
            }
            account_charts[account.account_type] = chart_data
        
        # Convertir en JSON pour le template
        account_charts_json = json_lib.dumps(account_charts)
        
        context = {
            'profile': profile,
            'accounts': accounts,
            'total_balance': total_balance,
            'total_initial': total_initial,
            'total_pnl': total_pnl,
            'total_pnl_percent': total_pnl_percent,
            'total_trades': total_trades,
            'recent_trades': recent_trades,
            'account_charts': account_charts_json,
        }
        
        return render(request, 'watchlist/portfolio.html', context)


class AccountDetailView(LoginRequiredMixin, View):
    """Page détaillée d'un compte (Finance, Trading ou Marge)"""
    
    login_url = '/accounts/login/'
    redirect_field_name = 'next'
    
    def get(self, request, account_type=None):
        # Si account_type vient de kwargs (pages séparées)
        if account_type is None:
            account_type = request.resolver_match.kwargs.get('account_type', 'trading')
        
        profile = _get_or_create_profile(request)
        
        # Récupérer ou créer le compte
        account = _get_or_create_account(profile, account_type)
        
        # Récupérer tous les trades du compte
        trades = Trade.objects.filter(account=account).select_related('related_trade').order_by('-executed_at')
        
        # Calculer les statistiques
        total_trades = trades.count()
        buy_trades = trades.filter(side='buy').count()
        sell_trades = trades.filter(side='sell').count()
        
        # P&L total des trades fermés (avec related_trade)
        closed_trades = trades.filter(side='sell', related_trade__isnull=False)
        total_pnl_trades = sum(float(t.profit_loss or 0) for t in closed_trades if t.profit_loss)
        
        # Trades ouverts (achats sans vente liée)
        open_positions = trades.filter(
            side='buy',
            related_trade__isnull=True
        ).order_by('-executed_at')
        
        # Récupérer les prix actuels pour calculer le P&L non réalisé
        open_positions_data = []
        for position in open_positions:
            ticker = BinanceAPIService.get_24hr_ticker(position.symbol)
            if ticker:
                current_price = float(ticker.get('lastPrice', 0))
                unrealized_pnl = (current_price - float(position.price)) * float(position.quantity)
                unrealized_pnl_percent = ((current_price - float(position.price)) / float(position.price) * 100) if float(position.price) > 0 else 0
                
                open_positions_data.append({
                    'trade': position,
                    'current_price': current_price,
                    'unrealized_pnl': unrealized_pnl,
                    'unrealized_pnl_percent': unrealized_pnl_percent,
                })
        
        # Historique du wallet pour le graphique (derniers 30 jours)
        wallet_history = WalletHistory.objects.filter(
            account=account,
            timestamp__gte=datetime.now() - timedelta(days=30)
        ).order_by('timestamp')[:200]
        
        # Si pas d'historique, créer des points initiaux
        if not wallet_history.exists():
            chart_data = {
                'labels': [datetime.now().strftime('%d/%m %H:%M')],
                'balances': [float(account.initial_balance)],
            }
        else:
            chart_data = {
                'labels': [h.timestamp.strftime('%d/%m %H:%M') for h in wallet_history],
                'balances': [float(h.balance) for h in wallet_history],
            }
        
        # Convertir en JSON pour le template
        chart_data_json = json_lib.dumps(chart_data)
        
        # Calculer le P&L réel incluant les positions ouvertes
        # La valeur totale du compte = Balance disponible + Valeur actuelle des positions
        # Le borrowed_amount fait déjà partie de la valeur des positions, donc on ne le soustrait pas
        total_unrealized_pnl = sum(pos['unrealized_pnl'] for pos in open_positions_data)
        
        # Valeur totale actuelle des positions (au prix actuel)
        total_positions_value = sum(
            pos['current_price'] * float(pos['trade'].quantity) for pos in open_positions_data
        )
        
        # Valeur totale du compte = Balance disponible + Valeur des positions
        total_account_value = float(account.balance) + total_positions_value
        
        # P&L = Valeur totale actuelle - Capital initial
        account_pnl = total_account_value - float(account.initial_balance)
        
        # Calculer le pourcentage
        if float(account.initial_balance) > 0:
            account_pnl_percent = (account_pnl / float(account.initial_balance)) * 100
        else:
            account_pnl_percent = 0
        
        context = {
            'profile': profile,
            'account': account,
            'trades': trades[:50],  # Limiter à 50 trades pour l'affichage
            'total_trades': total_trades,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'total_pnl_trades': total_pnl_trades,
            'open_positions': open_positions_data,
            'total_unrealized_pnl': total_unrealized_pnl,
            'chart_data': chart_data_json,
            'account_pnl': account_pnl,
            'account_pnl_percent': account_pnl_percent,
        }
        
        return render(request, 'watchlist/account_detail.html', context)


class AccountBalanceView(LoginRequiredMixin, View):
    """API endpoint pour récupérer le solde d'un compte"""
    
    login_url = '/accounts/login/'
    
    def get(self, request, account_type=None):
        from django.http import JsonResponse
        
        # Si account_type vient de kwargs
        if account_type is None:
            account_type = request.resolver_match.kwargs.get('account_type', 'trading')
        
        profile = _get_or_create_profile(request)
        account = _get_or_create_account(profile, account_type)
        
        # Récupérer les positions ouvertes pour ce compte
        trades = Trade.objects.filter(
            account=account,
            side='buy',
            related_trade__isnull=True
        ).order_by('symbol')
        
        positions = []
        for trade in trades:
            portfolio_item = Portfolio.objects.filter(
                account=account,
                symbol=trade.symbol
            ).first()
            
            if portfolio_item:
                positions.append({
                    'symbol': trade.symbol,
                    'quantity': float(portfolio_item.quantity),
                    'purchase_price': float(portfolio_item.purchase_price),
                })
        
        return JsonResponse({
            'balance': float(account.balance),
            'account_type': account.account_type,
            'positions': positions,
        })


class MarginPositionView(LoginRequiredMixin, View):
    """API endpoint pour récupérer les informations de position margin en temps réel"""
    
    login_url = '/accounts/login/'
    
    def get(self, request, symbol=None):
        from django.http import JsonResponse
        from decimal import Decimal
        from .trading_views import calculate_liquidation_price, calculate_margin_ratio
        
        if not symbol:
            symbol = request.GET.get('symbol', '').upper().strip()
        
        if not symbol:
            return JsonResponse({
                'success': False,
                'error': 'Symbole manquant'
            }, status=400)
        
        profile = _get_or_create_profile(request)
        account = _get_or_create_account(profile, 'margin')
        
        # Récupérer les positions ouvertes pour ce symbole
        open_trades = Trade.objects.filter(
            account=account,
            symbol=symbol,
            side='buy',
            related_trade__isnull=True
        ).order_by('-executed_at')
        
        if not open_trades.exists():
            return JsonResponse({
                'success': True,
                'has_position': False,
            })
        
        # Calculer les totaux de la position
        total_quantity = sum(float(t.quantity) for t in open_trades)
        total_cost = sum(float(t.quantity * t.price) for t in open_trades)
        avg_entry_price = total_cost / total_quantity if total_quantity > 0 else Decimal('0')
        
        # Récupérer le prix actuel depuis Binance
        ticker = BinanceAPIService.get_24hr_ticker(symbol)
        if not ticker:
            return JsonResponse({
                'success': False,
                'error': 'Impossible de récupérer le prix actuel'
            }, status=500)
        
        current_price = Decimal(str(ticker.get('lastPrice', 0)))
        current_value = total_quantity * float(current_price)
        
        # Calculer le P&L non réalisé
        unrealized_pnl = (float(current_price) - float(avg_entry_price)) * total_quantity
        unrealized_pnl_percent = ((float(current_price) - float(avg_entry_price)) / float(avg_entry_price) * 100) if avg_entry_price > 0 else 0
        
        # Récupérer le levier depuis les notes du trade
        # Le levier est stocké dans les notes du trade au format "Levier: x5"
        leverage = 1
        for trade in open_trades:
            if trade.notes and 'Levier' in trade.notes:
                try:
                    # Extraire le levier depuis "Levier: x5" ou "x5"
                    notes_str = trade.notes.strip()
                    if 'x' in notes_str:
                        leverage_str = notes_str.split('x')[-1].strip().split()[0]
                        leverage = int(float(leverage_str))
                        break
                except:
                    pass
        
        # Calculer le prix de liquidation
        liquidation_price = None
        if leverage > 1:
            liquidation_price = calculate_liquidation_price(avg_entry_price, int(leverage), 'buy')
        
        # Calculer le margin risk (ratio de marge)
        total_borrowed = float(account.borrowed_amount)
        total_collateral = float(account.balance) + current_value
        margin_ratio = calculate_margin_ratio(account, Decimal(str(total_borrowed)), Decimal(str(total_collateral)))
        
        # Déterminer le niveau de risque
        if margin_ratio >= Decimal('80'):
            risk_level = 'high'
            risk_percent = float(margin_ratio)
            risk_message = f"Risque élevé ({risk_percent:.2f}%) - Liquidation imminente!"
        elif margin_ratio >= Decimal('60'):
            risk_level = 'medium'
            risk_percent = float(margin_ratio)
            risk_message = f"Risque moyen ({risk_percent:.2f}%) - Surveillez de près"
        else:
            risk_level = 'low'
            risk_percent = float(margin_ratio)
            risk_message = f"Risque faible ({risk_percent:.2f}%)"
        
        # Distance jusqu'à la liquidation (en %)
        distance_to_liquidation = None
        if liquidation_price and current_price > 0:
            distance_to_liquidation = ((float(current_price) - float(liquidation_price)) / float(current_price) * 100)
        
        return JsonResponse({
            'success': True,
            'has_position': True,
            'symbol': symbol,
            'quantity': total_quantity,
            'avg_entry_price': float(avg_entry_price),
            'current_price': float(current_price),
            'current_value': current_value,
            'unrealized_pnl': unrealized_pnl,
            'unrealized_pnl_percent': unrealized_pnl_percent,
            'leverage': float(leverage),
            'liquidation_price': float(liquidation_price) if liquidation_price else None,
            'distance_to_liquidation': distance_to_liquidation,
            'margin_ratio': float(margin_ratio),
            'total_borrowed': total_borrowed,
            'total_collateral': total_collateral,
            'account_balance': float(account.balance),
            'risk_level': risk_level,
            'risk_percent': risk_percent,
            'risk_message': risk_message,
        })

