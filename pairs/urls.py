# pairs/urls.py
from django.urls import path
from .views import PairDetailView, PairAPIView

app_name = 'pairs'

urlpatterns = [
    path('<str:symbol>/', PairDetailView.as_view(), name='detail'),
    path('api/<str:symbol>/', PairAPIView.as_view(), name='api'),
]
