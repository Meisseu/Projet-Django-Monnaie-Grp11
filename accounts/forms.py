"""
Formulaires personnalisés pour l'authentification et les profils utilisateurs
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from accounts.models import UserProfile


class CustomUserCreationForm(UserCreationForm):
    """Formulaire d'inscription avec sélection de profil et préférences"""
    
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'votre@email.com'
        })
    )
    
    profile_type = forms.ChoiceField(
        choices=UserProfile.PROFILE_CHOICES,
        required=True,
        label="Type de profil",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    market_preference = forms.ChoiceField(
        choices=UserProfile.MARKET_CHOICES,
        required=True,
        label="Marché préféré",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'profile_type', 'market_preference')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom d\'utilisateur'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajouter les classes Bootstrap aux champs de mot de passe
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Mot de passe'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmer le mot de passe'
        })
        
        # Personnaliser les labels
        self.fields['username'].label = "Nom d'utilisateur"
        self.fields['password1'].label = "Mot de passe"
        self.fields['password2'].label = "Confirmer le mot de passe"
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            
            # Créer automatiquement le UserProfile avec les préférences
            UserProfile.objects.create(
                user=user,
                profile_type=self.cleaned_data['profile_type'],
                market_preference=self.cleaned_data['market_preference'],
                session_key=''  # Sera rempli lors de la première connexion
            )
        
        return user


class ProfileUpdateForm(forms.ModelForm):
    """Formulaire pour mettre à jour le profil utilisateur"""
    
    class Meta:
        model = UserProfile
        fields = ('profile_type', 'market_preference')
        widgets = {
            'profile_type': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
            'market_preference': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
        }
        labels = {
            'profile_type': 'Type de profil',
            'market_preference': 'Marché préféré',
        }

