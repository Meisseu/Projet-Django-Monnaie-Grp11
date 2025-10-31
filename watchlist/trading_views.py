"""
Vues pour le trading (buy/sell) avec intégration au système Portfolio
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Sum, Q
from decimal import Decimal
import json

from accounts.models import UserProfile
from .models import TradingAccount, Trade, WalletHistory, Portfolio
from .portfolio_utils import record_wallet_history
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
    return account


def calculate_liquidation_price(entry_price, leverage, side='buy', maintenance_margin_rate=Decimal('0.10')):
    """
    Calcule le prix de liquidation selon la logique Binance Cross Margin
    
    Formule Binance :
    - Long: Liquidation = Entry Price * (1 - Maintenance Margin Rate - 1/Leverage)
    - Short: Liquidation = Entry Price * (1 + Maintenance Margin Rate + 1/Leverage)
    
    maintenance_margin_rate: 10% par défaut pour Cross Margin (peut varier selon la paire)
    """
    leverage_decimal = Decimal(str(leverage))
    
    if side == 'buy':
        # Long position
        # Liquidation = Entry * (1 - Maintenance Rate - 1/Leverage)
        factor = Decimal('1.0') - maintenance_margin_rate - (Decimal('1.0') / leverage_decimal)
        liquidation = entry_price * factor
    else:
        # Short position
        # Liquidation = Entry * (1 + Maintenance Rate + 1/Leverage)
        factor = Decimal('1.0') + maintenance_margin_rate + (Decimal('1.0') / leverage_decimal)
        liquidation = entry_price * factor
    
    return max(liquidation, Decimal('0'))  # Éviter les prix négatifs


def calculate_margin_ratio(account, total_borrowed, total_collateral):
    """
    Calcule le ratio de marge selon Binance
    
    Margin Ratio = Total Borrowed / Total Collateral * 100%
    
    Si le ratio dépasse 80%, liquidation risque d'arriver
    Si le ratio dépasse 100%, liquidation automatique
    """
    if total_collateral == 0:
        return Decimal('999')  # Ratio très élevé si pas de collateral
    
    ratio = (total_borrowed / total_collateral) * Decimal('100')
    return ratio


def check_margin_requirement(account, quantity, price, leverage=1, current_positions=None):
    """
    Vérifie si le compte a assez de marge selon la logique Binance
    
    Pour Cross Margin avec levier :
    1. Calculer la marge initiale requise (Valeur / Levier)
    2. Vérifier le balance disponible
    3. Calculer la marge de maintien (10% de la valeur totale des positions)
    4. Vérifier que le ratio de marge reste sous 80%
    """
    total_value = Decimal(str(quantity)) * Decimal(str(price))
    
    # Marge initiale requise
    required_initial_margin = total_value / Decimal(str(leverage))
    
    # Vérifier le balance disponible
    available_balance = account.balance
    
    # Si c'est un compte margin avec levier
    if account.account_type == 'margin' and leverage > 1:
        # Calculer le total des positions existantes + nouvelle position
        if current_positions is None:
            current_positions = Trade.objects.filter(
                account=account,
                side='buy',
                related_trade__isnull=True
            )
        
        total_positions_value = Decimal('0')
        for pos in current_positions:
            ticker = BinanceAPIService.get_24hr_ticker(pos.symbol)
            if ticker:
                current_price = Decimal(str(ticker.get('lastPrice', 0)))
                total_positions_value += Decimal(str(pos.quantity)) * current_price
        
        # Ajouter la nouvelle position
        total_positions_value += total_value
        
        # Ratio de maintien (10% pour Cross Margin)
        maintenance_margin_rate = Decimal('0.10')
        required_maintenance_margin = total_positions_value * maintenance_margin_rate
        
        # Montant emprunté après ce trade
        borrowed_after = total_value - required_initial_margin
        total_borrowed = account.borrowed_amount + borrowed_after
        
        # Collateral total (balance + valeur des positions)
        total_collateral = available_balance + total_positions_value
        
        # Vérifier le ratio de marge (doit être < 80% pour sécurité)
        margin_ratio = calculate_margin_ratio(account, total_borrowed, total_collateral)
        
        if margin_ratio > Decimal('80'):
            return False, f"Ratio de marge trop élevé ({margin_ratio:.2f}%). Risque de liquidation imminent!"
        
        # Vérifier qu'on a assez pour la marge initiale + marge de maintien
        if available_balance < required_initial_margin:
            return False, f"Marge initiale insuffisante. Requis: ${required_initial_margin:.2f}"
        
        # Vérifier qu'on peut couvrir la marge de maintien
        remaining_after_margin = available_balance - required_initial_margin
        if remaining_after_margin < required_maintenance_margin:
            return False, f"Marge de maintien insuffisante. Requis après marge: ${required_maintenance_margin:.2f}"
    else:
        # Trading spot ou finance : pas de marge, juste vérifier le solde
        if available_balance < required_initial_margin:
            return False, "Fonds insuffisants"
    
    return True, None


@method_decorator(csrf_exempt, name='dispatch')
class BuyTradeView(LoginRequiredMixin, View):
    """Vue pour exécuter un ordre d'achat"""
    
    login_url = '/accounts/login/'
    
    def post(self, request):
        try:
            profile = _get_or_create_profile(request)
            
            # Parser les données JSON
            data = json.loads(request.body)
            symbol = data.get('symbol', '').upper().strip()
            quantity = Decimal(str(data.get('quantity', 0)))
            price = Decimal(str(data.get('price', 0)))
            account_type = data.get('account_type', 'trading')  # trading, margin, finance
            leverage = int(data.get('leverage', 1))  # 1-5 pour margin
            
            if not symbol or quantity <= 0 or price <= 0:
                return JsonResponse({
                    'success': False,
                    'error': 'Données invalides'
                }, status=400)
            
            # Limiter le levier à x5 pour margin
            if account_type == 'margin':
                leverage = min(max(leverage, 1), 5)
            else:
                leverage = 1
            
            # Récupérer le compte approprié
            account = _get_or_create_account(profile, account_type)
            
            # Calculer le total
            total_value = quantity * price
            
            # Pour margin avec levier, vérifier les exigences de marge
            if account_type == 'margin' and leverage > 1:
                can_trade, error_msg = check_margin_requirement(account, quantity, price, leverage)
                if not can_trade:
                    return JsonResponse({
                        'success': False,
                        'error': error_msg
                    }, status=400)
                
                required_margin = total_value / Decimal(str(leverage))
                
                # Mettre à jour le montant emprunté
                borrowed_amount = total_value - required_margin
                account.borrowed_amount += borrowed_amount
            else:
                required_margin = total_value
            
            # Vérifier le solde
            if account.balance < required_margin:
                return JsonResponse({
                    'success': False,
                    'error': f'Fonds insuffisants. Solde: ${account.balance:.2f}, Requis: ${required_margin:.2f}'
                }, status=400)
            
            # Calculer les frais (0.1% par défaut)
            fee_rate = Decimal('0.001')
            fee = total_value * fee_rate
            
            # Calculer le prix de liquidation si margin
            liquidation_price = None
            if account_type == 'margin' and leverage > 1:
                liquidation_price = calculate_liquidation_price(price, leverage, 'buy')
            
            # Créer le trade
            trade = Trade.objects.create(
                account=account,
                symbol=symbol,
                side='buy',
                order_type='market',
                quantity=quantity,
                price=price,
                total=total_value,
                fee=fee_rate,
                notes=f"Levier: x{leverage}" if account_type == 'margin' and leverage > 1 else "",
            )
            
            # Mettre à jour le balance du compte
            account.remove_funds(required_margin)
            account.save()  # Sauvegarder aussi le borrowed_amount si margin
            
            # Enregistrer l'historique
            record_wallet_history(account)
            
            # Créer/MAJ le portfolio pour tracker les positions (lié au compte)
            portfolio_item, created = Portfolio.objects.get_or_create(
                account=account,
                symbol=symbol,
                defaults={
                    'user_profile': profile,
                    'quantity': quantity,
                    'purchase_price': price,
                }
            )
            
            if not created:
                # Mise à jour de la position existante (moyenne pondérée)
                total_qty = portfolio_item.quantity + quantity
                total_cost = (portfolio_item.quantity * portfolio_item.purchase_price) + total_value
                portfolio_item.quantity = total_qty
                portfolio_item.purchase_price = total_cost / total_qty
                portfolio_item.save()
            
            response_data = {
                'success': True,
                'message': f'Achat de {quantity} {symbol} effectué avec succès',
                'new_balance': float(account.balance),
                'trade_id': trade.id,
            }
            
            # Ajouter les informations de liquidation si margin
            if account_type == 'margin' and leverage > 1 and liquidation_price:
                response_data['liquidation_price'] = float(liquidation_price)
                response_data['leverage'] = leverage
                response_data['margin_warning'] = f"Attention: Prix de liquidation estimé: ${float(liquidation_price):.2f}"
            
            return JsonResponse(response_data)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'JSON invalide'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class SellTradeView(LoginRequiredMixin, View):
    """Vue pour exécuter un ordre de vente"""
    
    login_url = '/accounts/login/'
    
    def post(self, request):
        try:
            profile = _get_or_create_profile(request)
            
            # Parser les données JSON
            data = json.loads(request.body)
            symbol = data.get('symbol', '').upper().strip()
            quantity = Decimal(str(data.get('quantity', 0)))
            price = Decimal(str(data.get('price', 0)))
            account_type = data.get('account_type', 'trading')
            leverage = int(data.get('leverage', 1))
            
            if not symbol or quantity <= 0 or price <= 0:
                return JsonResponse({
                    'success': False,
                    'error': 'Données invalides'
                }, status=400)
            
            # Récupérer le compte
            account = _get_or_create_account(profile, account_type)
            
            # Vérifier qu'on a la quantité en portfolio (pour ce compte spécifique)
            portfolio_item = Portfolio.objects.filter(
                account=account,
                symbol=symbol
            ).first()
            
            if not portfolio_item or portfolio_item.quantity < quantity:
                return JsonResponse({
                    'success': False,
                    'error': f'Quantité insuffisante. Vous possédez: {portfolio_item.quantity if portfolio_item else 0} {symbol}'
                }, status=400)
            
            # Calculer le revenu
            total_value = quantity * price
            
            # Calculer les frais
            fee_rate = Decimal('0.001')
            fee = total_value * fee_rate
            net_revenue = total_value - fee
            
            # Trouver le trade d'entrée correspondant (FIFO)
            buy_trade = Trade.objects.filter(
                account=account,
                symbol=symbol,
                side='buy',
                related_trade__isnull=True
            ).order_by('executed_at').first()
            
            # Créer le trade de vente
            trade = Trade.objects.create(
                account=account,
                symbol=symbol,
                side='sell',
                order_type='market',
                quantity=quantity,
                price=price,
                total=total_value,
                fee=fee_rate,
                related_trade=buy_trade,
            )
            
            # Calculer le P&L si on a un trade d'entrée
            if buy_trade:
                pnl = trade.calculate_pnl()
                if pnl is not None:
                    trade.profit_loss = Decimal(str(pnl))
                    trade.profit_loss_percent = Decimal(str(((price - buy_trade.price) / buy_trade.price) * 100))
                    trade.save()
            
            # Mettre à jour le balance
            account.add_funds(net_revenue)
            
            # Mettre à jour le portfolio
            portfolio_item.quantity -= quantity
            if portfolio_item.quantity <= 0:
                portfolio_item.delete()
            else:
                portfolio_item.save()
            
            # Enregistrer l'historique
            record_wallet_history(account)
            
            return JsonResponse({
                'success': True,
                'message': f'Vente de {quantity} {symbol} effectuée avec succès',
                'new_balance': float(account.balance),
                'trade_id': trade.id,
                'pnl': float(trade.profit_loss) if trade.profit_loss else None,
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'JSON invalide'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

