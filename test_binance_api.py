"""
Script de test pour l'API Binance
Execute ce script pour vérifier que l'API fonctionne correctement
"""

import requests
import json
from datetime import datetime

print("=" * 80)
print("TEST DE L'API BINANCE")
print("=" * 80)
print()

# URL de base de l'API Binance
BASE_URL = "https://api.binance.com"

# Test 1: Ping de l'API
print("📡 Test 1: Connexion à l'API Binance...")
try:
    response = requests.get(f"{BASE_URL}/api/v3/ping", timeout=5)
    if response.status_code == 200:
        print("✅ SUCCÈS: Connexion établie avec l'API Binance")
    else:
        print(f"❌ ERREUR: Code de statut {response.status_code}")
except Exception as e:
    print(f"❌ ERREUR: {e}")

print()

# Test 2: Heure du serveur
print("⏰ Test 2: Récupération de l'heure du serveur...")
try:
    response = requests.get(f"{BASE_URL}/api/v3/time", timeout=5)
    if response.status_code == 200:
        data = response.json()
        server_time = datetime.fromtimestamp(data['serverTime'] / 1000)
        print(f"✅ SUCCÈS: Heure du serveur: {server_time}")
    else:
        print(f"❌ ERREUR: Code de statut {response.status_code}")
except Exception as e:
    print(f"❌ ERREUR: {e}")

print()

# Test 3: Prix actuel du Bitcoin
print("💰 Test 3: Récupération du prix du Bitcoin (BTC/USDT)...")
try:
    response = requests.get(f"{BASE_URL}/api/v3/ticker/price", 
                          params={'symbol': 'BTCUSDT'}, 
                          timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCÈS: BTC/USDT = ${float(data['price']):,.2f}")
    else:
        print(f"❌ ERREUR: Code de statut {response.status_code}")
except Exception as e:
    print(f"❌ ERREUR: {e}")

print()

# Test 4: Statistiques 24h pour plusieurs paires
print("📊 Test 4: Statistiques 24h des principales paires...")
symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
try:
    for symbol in symbols:
        response = requests.get(f"{BASE_URL}/api/v3/ticker/24hr", 
                              params={'symbol': symbol}, 
                              timeout=5)
        if response.status_code == 200:
            data = response.json()
            price = float(data['lastPrice'])
            change = float(data['priceChangePercent'])
            volume = float(data['volume'])
            
            # Formatage de la couleur selon la variation
            color = "🟢" if change >= 0 else "🔴"
            
            print(f"{color} {symbol:10} | Prix: ${price:>12,.2f} | "
                  f"Variation: {change:>+7.2f}% | Volume: {volume:>15,.0f}")
        else:
            print(f"❌ {symbol}: Erreur {response.status_code}")
except Exception as e:
    print(f"❌ ERREUR: {e}")

print()

# Test 5: Klines (données de graphique)
print("📈 Test 5: Récupération des données de graphique (Klines)...")
try:
    response = requests.get(f"{BASE_URL}/api/v3/klines", 
                          params={
                              'symbol': 'BTCUSDT',
                              'interval': '1h',
                              'limit': 5
                          }, 
                          timeout=5)
    if response.status_code == 200:
        klines = response.json()
        print(f"✅ SUCCÈS: {len(klines)} bougies horaires récupérées")
        print("\n   Dernières 5 heures du BTC/USDT:")
        print("   " + "-" * 70)
        print(f"   {'Heure':<20} | {'Open':<12} | {'High':<12} | {'Low':<12} | {'Close':<12}")
        print("   " + "-" * 70)
        
        for kline in klines:
            timestamp = datetime.fromtimestamp(kline[0] / 1000)
            open_price = float(kline[1])
            high_price = float(kline[2])
            low_price = float(kline[3])
            close_price = float(kline[4])
            
            print(f"   {timestamp.strftime('%Y-%m-%d %H:%M'):<20} | "
                  f"${open_price:<11,.2f} | ${high_price:<11,.2f} | "
                  f"${low_price:<11,.2f} | ${close_price:<11,.2f}")
    else:
        print(f"❌ ERREUR: Code de statut {response.status_code}")
except Exception as e:
    print(f"❌ ERREUR: {e}")

print()

# Test 6: Carnet d'ordres
print("📚 Test 6: Récupération du carnet d'ordres...")
try:
    response = requests.get(f"{BASE_URL}/api/v3/depth", 
                          params={
                              'symbol': 'BTCUSDT',
                              'limit': 5
                          }, 
                          timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCÈS: Carnet d'ordres récupéré")
        print(f"\n   Top 5 des ordres d'achat (bids):")
        for bid in data['bids'][:5]:
            print(f"   Prix: ${float(bid[0]):>12,.2f} | Quantité: {float(bid[1]):>10.5f} BTC")
        
        print(f"\n   Top 5 des ordres de vente (asks):")
        for ask in data['asks'][:5]:
            print(f"   Prix: ${float(ask[0]):>12,.2f} | Quantité: {float(ask[1]):>10.5f} BTC")
    else:
        print(f"❌ ERREUR: Code de statut {response.status_code}")
except Exception as e:
    print(f"❌ ERREUR: {e}")

print()

# Test 7: Nombre de paires disponibles
print("🌐 Test 7: Vérification des paires disponibles...")
try:
    response = requests.get(f"{BASE_URL}/api/v3/exchangeInfo", timeout=10)
    if response.status_code == 200:
        data = response.json()
        total_symbols = len(data['symbols'])
        
        # Compter les paires par type
        usdt_pairs = sum(1 for s in data['symbols'] if s['symbol'].endswith('USDT'))
        btc_pairs = sum(1 for s in data['symbols'] if s['symbol'].endswith('BTC'))
        
        print(f"✅ SUCCÈS: {total_symbols} paires de trading disponibles")
        print(f"   - Paires USDT: {usdt_pairs}")
        print(f"   - Paires BTC: {btc_pairs}")
        print(f"   - Autres: {total_symbols - usdt_pairs - btc_pairs}")
    else:
        print(f"❌ ERREUR: Code de statut {response.status_code}")
except Exception as e:
    print(f"❌ ERREUR: {e}")

print()
print("=" * 80)
print("TESTS TERMINÉS")
print("=" * 80)
print()
print("📝 Conclusion:")
print("   Si tous les tests affichent ✅, l'API Binance fonctionne correctement")
print("   et votre projet Django pourra récupérer les données sans problème.")
print()
print("🚀 Vous pouvez maintenant lancer votre application Django avec:")
print("   python manage.py runserver")
print()

