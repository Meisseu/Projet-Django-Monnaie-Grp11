"""
ASGI config for crypto_monitor project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crypto_monitor.settings')

application = get_asgi_application()

