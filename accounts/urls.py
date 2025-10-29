from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('logout/', views.LogoutView.as_view(), name='logout'),
]

