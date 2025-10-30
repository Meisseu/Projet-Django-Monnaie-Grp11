# accounts/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Page de connexion
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),

    # Page de déconnexion
    path('logout/', views.SafeLogoutView.as_view(), name='logout'),

    # Page d’inscription
    path('signup/', views.SignupView.as_view(), name='signup'),
]
