"""
Utilitaires pour le système Portfolio : enregistrement automatique de l'historique
"""
from .models import TradingAccount, WalletHistory
from decimal import Decimal
from datetime import datetime


def record_wallet_history(account):
    """
    Enregistre l'état actuel du wallet dans l'historique
    Appeler cette fonction après chaque modification du balance
    """
    WalletHistory.objects.create(
        account=account,
        balance=account.balance
    )


def initialize_account_history(account):
    """
    Initialise l'historique d'un compte avec le balance initial
    """
    # Vérifier si l'historique existe déjà
    if not WalletHistory.objects.filter(account=account).exists():
        WalletHistory.objects.create(
            account=account,
            balance=account.initial_balance
        )

