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
    
    @staticmethod
    def format_price(price: str) -> str:
        """Formate un prix crypto avec le bon nombre de décimales"""
        try:
            p = float(price)
            
            if p == 0:
                return "0.00"
            
            # Grands prix (>= 1000)
            if p >= 1000:
                return f"{p:,.2f}"
            
            # Prix normaux (>= 1)
            elif p >= 1:
                return f"{p:.2f}"
            
            # Petits prix - on garde 4 chiffres significatifs
            else:
                # Compter les zéros après la virgule
                price_str = f"{p:.20f}".rstrip('0')
                decimal_part = price_str.split('.')[1] if '.' in price_str else ''
                
                leading_zeros = 0
                for char in decimal_part:
                    if char == '0':
                        leading_zeros += 1
                    else:
                        break
                
                # 4 chiffres significatifs après le premier chiffre non-zéro
                decimals_needed = min(leading_zeros + 4, 12)
                return f"{p:.{decimals_needed}f}"
                
        except (ValueError, TypeError):
            return str(price)

