from django.urls import path
from . import views

app_name = 'pairs'

urlpatterns = [
    path('api/<str:symbol>/', views.PairDataAPIView.as_view(), name='api_data'),
    path('<str:symbol>/', views.PairDetailView.as_view(), name='detail'),
]

