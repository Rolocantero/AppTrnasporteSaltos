from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def passenger_view(request):
    file_path = BASE_DIR / 'frontend_passenger' / 'index.html'
    with open(file_path, 'r', encoding='utf-8') as f:
        return HttpResponse(f.read(), content_type='text/html')

def driver_view(request):
    file_path = BASE_DIR / 'frontend_driver' / 'index.html'
    with open(file_path, 'r', encoding='utf-8') as f:
        return HttpResponse(f.read(), content_type='text/html')

def dashboard_view(request):
    file_path = BASE_DIR / 'backend' / 'templates' / 'dashboard.html'
    with open(file_path, 'r', encoding='utf-8') as f:
        return HttpResponse(f.read(), content_type='text/html')

import json

def manifest_passenger_view(request):
    manifest = {
        "name": "ViajaYa Frontera - Pasajero",
        "short_name": "ViajaYa",
        "description": "Aplicación de transporte privado y viajes en la frontera Saltos del Guairá, Guaíra y Mundo Novo.",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#121824",
        "theme_color": "#00c853",
        "orientation": "portrait",
        "icons": [
            {
                "src": "https://cdn-icons-png.flaticon.com/512/3097/3097180.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "https://cdn-icons-png.flaticon.com/512/3097/3097180.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            }
        ]
    }
    return HttpResponse(json.dumps(manifest), content_type='application/json')

def manifest_driver_view(request):
    manifest = {
        "name": "ViajaYa Conductor",
        "short_name": "ChoferYa",
        "description": "Aplicación oficial para conductores de la red de transporte en frontera.",
        "start_url": "/driver/",
        "display": "standalone",
        "background_color": "#0f172a",
        "theme_color": "#ffab00",
        "orientation": "portrait",
        "icons": [
            {
                "src": "https://cdn-icons-png.flaticon.com/512/3097/3097180.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "https://cdn-icons-png.flaticon.com/512/3097/3097180.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            }
        ]
    }
    return HttpResponse(json.dumps(manifest), content_type='application/json')

def service_worker_view(request):
    sw_code = """
    self.addEventListener('install', (e) => self.skipWaiting());
    self.addEventListener('activate', (e) => self.clients.claim());
    self.addEventListener('fetch', (e) => {});
    """
    return HttpResponse(sw_code, content_type='application/javascript')

admin.site.site_header = "Panel de Control - Transporte Fronterizo (Saltos del Guairá)"
admin.site.site_title = "Admin Movilidad Frontera"
admin.site.index_title = "Gestión de Viajes, Conductores y Tarifas"
admin.site.site_url = '/dashboard/'

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', passenger_view, name='passenger_app'),
    path('driver/', driver_view, name='driver_app'),
    path('dashboard/', dashboard_view, name='dashboard_app'),
    path('manifest_passenger.json', manifest_passenger_view, name='manifest_passenger'),
    path('manifest_driver.json', manifest_driver_view, name='manifest_driver'),
    path('sw.js', service_worker_view, name='service_worker'),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

