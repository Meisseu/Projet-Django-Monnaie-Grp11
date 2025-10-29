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
    """Portefeuille de simulation d'actifs"""
    
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='portfolio_items')
    symbol = models.CharField(max_length=20)
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    purchase_price = models.DecimalField(max_digits=20, decimal_places=8)
    purchase_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Élément de portfolio"
        verbose_name_plural = "Portfolio"
        ordering = ['-purchase_date']
    
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

