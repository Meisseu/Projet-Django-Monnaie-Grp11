# pairs/urls.py
from django.urls import path
from .views import PairDetailView

app_name = 'pairs'

urlpatterns = [
    path('<str:symbol>/', PairDetailView.as_view(), name='detail'),
]
