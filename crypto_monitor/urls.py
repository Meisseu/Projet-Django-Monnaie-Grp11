"""
URL configuration for crypto_monitor project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 🧩 Administration Django
    path('admin/', admin.site.urls),

    # 🌐 Pages principales
    path('', include(('landing.urls', 'landing'), namespace='landing')),
    path('home/', include(('home.urls', 'home'), namespace='home')),
    path('search/', include(('search.urls', 'search'), namespace='search')),
    path('pairs/', include(('pairs.urls', 'pairs'), namespace='pairs')),
    path('watchlist/', include(('watchlist.urls', 'watchlist'), namespace='watchlist')),

    # 👥 Authentification et profils utilisateurs
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
]

# 🔧 Gestion des fichiers statiques et médias en mode développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])