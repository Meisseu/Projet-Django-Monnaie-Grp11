from django.db import models
from accounts.models import UserProfile
from decimal import Decimal


class Watchlist(models.Model):
    """Liste de surveillance des paires de trading"""
    
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='watchlist_items')
    symbol = models.CharField(max_length=20)  # ex: BTCUSDT
    added_at = models.DateTimeField(auto_now_add=True)
    order = models.IntegerField(default=0)  # Pour permettre le réordonnancement
    
    class Meta:
        verbose_name = "Élément de watchlist"
        verbose_name_plural = "Watchlist"
        ordering = ['order', '-added_at']
        unique_together = ['user_profile', 'symbol']
    
    def __str__(self):
        return f"{self.symbol} - {self.user_profile.session_key}"


class Portfolio(models.Model):
    """Portefeuille de simulation d'actifs - Lié à un compte de trading spécifique"""
    
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='portfolio_items')
    account = models.ForeignKey('TradingAccount', on_delete=models.CASCADE, related_name='portfolio_positions', null=True, blank=True)
    symbol = models.CharField(max_length=20)
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    purchase_price = models.DecimalField(max_digits=20, decimal_places=8)
    purchase_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Élément de portfolio"
        verbose_name_plural = "Portfolio"
        ordering = ['-purchase_date']
        unique_together = ['account', 'symbol']  # Un portfolio par compte et par symbole
        indexes = [
            models.Index(fields=['account', 'symbol']),
            models.Index(fields=['user_profile', 'symbol']),
        ]
    
    def __str__(self):
        return f"{self.symbol} x{self.quantity} - {self.user_profile.session_key}"
    
    def current_value(self, current_price):
        """Calcule la valeur actuelle de la position"""
        return float(self.quantity) * float(current_price)
    
    def profit_loss(self, current_price):
        """Calcule le gain ou la perte"""
        return (float(current_price) - float(self.purchase_price)) * float(self.quantity)
    
    def profit_loss_percent(self, current_price):
        """Calcule le pourcentage de gain ou perte"""
        if float(self.purchase_price) == 0:
            return 0
        return ((float(current_price) - float(self.purchase_price)) / float(self.purchase_price)) * 100


class TradingBalance(models.Model):
    """Solde fictif pour le paper trading"""
    
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='trading_balance')
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('10000.00'))  # Capital initial de 10,000 USD
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Solde de trading"
        verbose_name_plural = "Soldes de trading"
    
    def __str__(self):
        return f"Balance: ${self.balance} - {self.user_profile.session_key}"
    
    def can_buy(self, amount):
        """Vérifie si l'utilisateur a assez de fonds"""
        return self.balance >= Decimal(str(amount))
    
    def add_funds(self, amount):
        """Ajoute des fonds (lors d'une vente)"""
        self.balance += Decimal(str(amount))
        self.save()
    
    def remove_funds(self, amount):
        """Retire des fonds (lors d'un achat)"""
        if self.can_buy(amount):
            self.balance -= Decimal(str(amount))
            self.save()
            return True
        return False


class TradingAccount(models.Model):
    """Compte de trading avec différents types (Finance, Trading, Marge)"""
    
    ACCOUNT_TYPES = [
        ('finance', 'Finance'),
        ('trading', 'Trading Spot'),
        ('margin', 'Marge'),
    ]
    
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='trading_accounts')
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='trading')
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('10000.00'))
    initial_balance = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('10000.00'))
    # Pour margin trading
    max_leverage = models.IntegerField(default=5)  # Levier maximum (x5)
    borrowed_amount = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0.00'))  # Montant emprunté
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Compte de trading"
        verbose_name_plural = "Comptes de trading"
        unique_together = ['user_profile', 'account_type']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_account_type_display()} - ${self.balance} - {self.user_profile.user.username if self.user_profile.user else 'Anon'}"
    
    def get_total_pnl(self):
        """Calcule le P&L total du compte"""
        return float(self.balance) - float(self.initial_balance)
    
    def get_total_pnl_percent(self):
        """Calcule le P&L en pourcentage"""
        if float(self.initial_balance) == 0:
            return 0
        return ((float(self.balance) - float(self.initial_balance)) / float(self.initial_balance)) * 100
    
    def can_buy(self, amount):
        """Vérifie si le compte a assez de fonds"""
        return self.balance >= Decimal(str(amount))
    
    def add_funds(self, amount):
        """Ajoute des fonds au compte"""
        self.balance += Decimal(str(amount))
        self.save()
    
    def remove_funds(self, amount):
        """Retire des fonds du compte"""
        if self.can_buy(amount):
            self.balance -= Decimal(str(amount))
            self.save()
            return True
        return False


class Trade(models.Model):
    """Historique des trades avec P&L"""
    
    SIDE_CHOICES = [
        ('buy', 'Achat'),
        ('sell', 'Vente'),
    ]
    
    ORDER_TYPE_CHOICES = [
        ('market', 'Marché'),
        ('limit', 'Limite'),
        ('stop', 'Stop Loss'),
        ('stop_limit', 'Stop Limit'),
    ]
    
    account = models.ForeignKey(TradingAccount, on_delete=models.CASCADE, related_name='trades')
    symbol = models.CharField(max_length=20)  # ex: BTCUSDT
    side = models.CharField(max_length=4, choices=SIDE_CHOICES)  # buy ou sell
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, default='market')
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    price = models.DecimalField(max_digits=20, decimal_places=8)
    total = models.DecimalField(max_digits=20, decimal_places=2)  # quantity * price
    fee = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.001'))  # 0.1% par défaut
    executed_at = models.DateTimeField(auto_now_add=True)
    
    # P&L calculé (pour les trades fermés)
    profit_loss = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    profit_loss_percent = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    # Lien vers le trade d'entrée (pour calculer P&L à la vente)
    related_trade = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='closing_trades')
    
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Trade"
        verbose_name_plural = "Trades"
        ordering = ['-executed_at']
        indexes = [
            models.Index(fields=['account', '-executed_at']),
            models.Index(fields=['symbol', '-executed_at']),
        ]
    
    def __str__(self):
        return f"{self.side.upper()} {self.symbol} x{self.quantity} @ ${self.price} - {self.account.get_account_type_display()}"
    
    def calculate_pnl(self, current_price=None):
        """Calcule le P&L si c'est une vente avec trade d'entrée lié"""
        if self.side == 'sell' and self.related_trade:
            entry_price = float(self.related_trade.price)
            exit_price = float(self.price)
            quantity = float(self.quantity)
            
            # P&L = (Prix sortie - Prix entrée) * Quantité
            pnl = (exit_price - entry_price) * quantity
            
            # Soustraire les frais
            fee_entry = float(self.related_trade.total) * float(self.related_trade.fee)
            fee_exit = float(self.total) * float(self.fee)
            pnl -= (fee_entry + fee_exit)
            
            return pnl
        return None


class WalletHistory(models.Model):
    """Historique de l'évolution du wallet pour les graphiques"""
    
    account = models.ForeignKey(TradingAccount, on_delete=models.CASCADE, related_name='wallet_history')
    balance = models.DecimalField(max_digits=20, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Historique du wallet"
        verbose_name_plural = "Historiques des wallets"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['account', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.account.get_account_type_display()}: ${self.balance} - {self.timestamp}"