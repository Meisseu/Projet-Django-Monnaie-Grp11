"""
Service pour interagir avec l'API Binance Spot
Documentation: https://binance-docs.github.io/apidocs/spot/en/
"""
import requests
from django.conf import settings
from typing import List, Dict, Optional


class BinanceAPIService:
    """Service pour récupérer les données de l'API Binance"""
    
    BASE_URL = settings.BINANCE_API_BASE_URL
    
    @staticmethod
    def get_24hr_ticker(symbol: Optional[str] = None) -> Dict:
        """
        Récupère les statistiques de prix sur 24h
        Endpoint: /api/v3/ticker/24hr
        """
        url = f"{BinanceAPIService.BASE_URL}/api/v3/ticker/24hr"
        params = {}
        if symbol:
            params['symbol'] = symbol
            
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur API Binance (24hr ticker): {e}")
            return {} if symbol else []
    
    @staticmethod
    def get_exchange_info() -> Dict:
        """
        Récupère les informations sur l'exchange
        Endpoint: /api/v3/exchangeInfo
        """
        url = f"{BinanceAPIService.BASE_URL}/api/v3/exchangeInfo"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur API Binance (exchange info): {e}")
            return {}
    
    @staticmethod
    def get_klines(symbol: str, interval: str = '1d', limit: int = 30) -> List:
        """
        Récupère les données de chandelier (klines/candlesticks)
        Endpoint: /api/v3/klines
        
        Intervals possibles: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
        """
        url = f"{BinanceAPIService.BASE_URL}/api/v3/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur API Binance (klines): {e}")
            return []
    
    @staticmethod
    def get_ticker_price(symbol: Optional[str] = None) -> Dict:
        """
        Récupère le prix actuel d'un symbole
        Endpoint: /api/v3/ticker/price
        """
        url = f"{BinanceAPIService.BASE_URL}/api/v3/ticker/price"
        params = {}
        if symbol:
            params['symbol'] = symbol
            
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur API Binance (ticker price): {e}")
            return {} if symbol else []
    
    @staticmethod
    def get_order_book(symbol: str, limit: int = 20) -> Dict:
        """
        Récupère le carnet d'ordres (depth)
        Endpoint: /api/v3/depth
        """
        url = f"{BinanceAPIService.BASE_URL}/api/v3/depth"
        params = {
            'symbol': symbol,
            'limit': limit
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur API Binance (order book): {e}")
            return {}
    
    @staticmethod
    def get_recent_trades(symbol: str, limit: int = 20) -> List:
        """
        Récupère les transactions récentes
        Endpoint: /api/v3/trades
        """
        url = f"{BinanceAPIService.BASE_URL}/api/v3/trades"
        params = {
            'symbol': symbol,
            'limit': limit
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur API Binance (recent trades): {e}")
            return []
    
    @staticmethod
    def get_popular_pairs() -> List[str]:
        """Retourne une liste des paires les plus populaires"""
        return [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT',
            'DOGEUSDT', 'SOLUSDT', 'MATICUSDT', 'DOTUSDT', 'LTCUSDT',
            'AVAXUSDT', 'LINKUSDT', 'UNIUSDT', 'ATOMUSDT', 'ETCUSDT'
        ]
    
    @staticmethod
    def format_price_change(price_change_percent: str) -> str:
        """Formate le pourcentage de changement de prix"""
        try:
            percent = float(price_change_percent)
            return f"{percent:+.2f}%"
        except (ValueError, TypeError):
            return "0.00%"
    
    @staticmethod
    def format_volume(volume: str) -> str:
        """Formate le volume en notation compacte"""
        try:
            vol = float(volume)
            if vol >= 1_000_000_000:
                return f"{vol / 1_000_000_000:.2f}B"
            elif vol >= 1_000_000:
                return f"{vol / 1_000_000:.2f}M"
            elif vol >= 1_000:
                return f"{vol / 1_000:.2f}K"
            else:
                return f"{vol:.2f}"
        except (ValueError, TypeError):
            return "0"

