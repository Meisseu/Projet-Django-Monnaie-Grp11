from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    """Profil utilisateur étendu"""

    PROFILE_CHOICES = [
        ('beginner', 'Investisseur débutant'),
        ('trader', 'Trader confirmé'),
        ('analyst', 'Analyste'),
    ]

    MARKET_CHOICES = [
        ('crypto', 'Cryptomonnaies'),
        ('fiat', 'Devises FIAT'),
        ('commodities', 'Matières premières tokenisées'),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile', null=True, blank=True
    )
    # ❗️ session_key: plus unique, plus permissif
    session_key = models.CharField(max_length=64, blank=True, default='', db_index=True)

    profile_type = models.CharField(max_length=20, choices=PROFILE_CHOICES, default='beginner')
    market_preference = models.CharField(max_length=20, choices=MARKET_CHOICES, default='crypto')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        label = self.user.username if self.user else (self.session_key or 'anonymous')
        return f"Profile {label} - {self.get_profile_type_display()}"

    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"
        # Optionnel: un tri par défaut
        ordering = ['-created_at']
