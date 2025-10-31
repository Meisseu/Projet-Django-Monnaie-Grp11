# watchlist/urls.py
from django.urls import path
from . import views
from . import portfolio_views
from . import trading_views

app_name = 'watchlist'

urlpatterns = [
    # Watchlist classique
    path('', views.WatchlistView.as_view(), name='index'),
    path('add/', views.AddToWatchlistView.as_view(), name='add'),
    path('remove/<int:watchlist_id>/', views.RemoveFromWatchlistView.as_view(), name='remove'),
    
    # Portfolio classique (ancien système)
    path('portfolio/add/', views.AddToPortfolioView.as_view(), name='portfolio_add'),
    path('portfolio/remove/<int:portfolio_id>/', views.RemoveFromPortfolioView.as_view(), name='portfolio_remove'),
    
    # Nouveau Portfolio avec comptes multiples
    path('portfolio/', portfolio_views.PortfolioView.as_view(), name='portfolio'),
    path('portfolio/<str:account_type>/', portfolio_views.AccountDetailView.as_view(), name='account_detail'),
    path('portfolio/<str:account_type>/balance/', portfolio_views.AccountBalanceView.as_view(), name='account_balance'),
    
    # Pages Portfolio séparées pour chaque type de compte
    path('portfolio-finance/', portfolio_views.AccountDetailView.as_view(), {'account_type': 'finance'}, name='portfolio_finance'),
    path('portfolio-trading/', portfolio_views.AccountDetailView.as_view(), {'account_type': 'trading'}, name='portfolio_trading'),
    path('portfolio-margin/', portfolio_views.AccountDetailView.as_view(), {'account_type': 'margin'}, name='portfolio_margin'),
    
    # Trading (buy/sell)
    path('trading/buy/', trading_views.BuyTradeView.as_view(), name='trading_buy'),
    path('trading/sell/', trading_views.SellTradeView.as_view(), name='trading_sell'),
    
    # Position Margin (informations en temps réel)
    path('trading/margin-position/<str:symbol>/', portfolio_views.MarginPositionView.as_view(), name='margin_position'),
]
