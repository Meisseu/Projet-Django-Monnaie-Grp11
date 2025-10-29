from django.urls import path
from . import views

app_name = 'watchlist'

urlpatterns = [
    path('', views.WatchlistView.as_view(), name='index'),
    path('add/', views.AddToWatchlistView.as_view(), name='add'),
    path('remove/<int:watchlist_id>/', views.RemoveFromWatchlistView.as_view(), name='remove'),
    path('portfolio/add/', views.AddToPortfolioView.as_view(), name='portfolio_add'),
    path('portfolio/remove/<int:portfolio_id>/', views.RemoveFromPortfolioView.as_view(), name='portfolio_remove'),
    # Trading endpoints
    path('trading/buy/', views.BuyTokenView.as_view(), name='buy_token'),
    path('trading/sell/', views.SellTokenView.as_view(), name='sell_token'),
    path('trading/balance/', views.GetTradingBalanceView.as_view(), name='trading_balance'),
]

