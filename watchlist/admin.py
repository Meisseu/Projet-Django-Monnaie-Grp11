from django.contrib import admin
from .models import Watchlist, Portfolio, TradingBalance, TradingAccount, Trade, WalletHistory


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'user_profile', 'added_at', 'order']
    list_filter = ['added_at']
    search_fields = ['symbol', 'user_profile__session_key']


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'quantity', 'purchase_price', 'user_profile', 'purchase_date']
    list_filter = ['purchase_date']
    search_fields = ['symbol', 'user_profile__session_key']


@admin.register(TradingBalance)
class TradingBalanceAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'balance', 'created_at', 'updated_at']
    list_filter = ['created_at']
    search_fields = ['user_profile__session_key']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TradingAccount)
class TradingAccountAdmin(admin.ModelAdmin):
    list_display = ['account_type', 'user_profile', 'balance', 'initial_balance', 'get_total_pnl', 'created_at']
    list_filter = ['account_type', 'created_at']
    search_fields = ['user_profile__user__username', 'user_profile__session_key']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_total_pnl(self, obj):
        return f"${obj.get_total_pnl():.2f} ({obj.get_total_pnl_percent():.2f}%)"
    get_total_pnl.short_description = 'P&L Total'


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'side', 'account', 'quantity', 'price', 'total', 'profit_loss', 'executed_at']
    list_filter = ['side', 'order_type', 'executed_at', 'account__account_type']
    search_fields = ['symbol', 'account__user_profile__user__username']
    readonly_fields = ['executed_at']
    date_hierarchy = 'executed_at'
    
    fieldsets = (
        ('Trade', {
            'fields': ('account', 'symbol', 'side', 'order_type')
        }),
        ('Détails', {
            'fields': ('quantity', 'price', 'total', 'fee')
        }),
        ('P&L', {
            'fields': ('related_trade', 'profit_loss', 'profit_loss_percent')
        }),
        ('Autres', {
            'fields': ('executed_at', 'notes')
        }),
    )


@admin.register(WalletHistory)
class WalletHistoryAdmin(admin.ModelAdmin):
    list_display = ['account', 'balance', 'timestamp']
    list_filter = ['timestamp', 'account__account_type']
    search_fields = ['account__user_profile__user__username']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'

