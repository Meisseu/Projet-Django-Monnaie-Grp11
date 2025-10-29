from django.urls import path
from . import views

app_name = 'pairs'

urlpatterns = [
    path('<str:symbol>/', views.PairDetailView.as_view(), name='detail'),
]

