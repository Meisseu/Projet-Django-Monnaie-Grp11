from django.contrib import admin
from .models import Watchlist, Portfolio


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

