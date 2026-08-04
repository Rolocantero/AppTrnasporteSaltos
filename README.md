# 🚗 Movilidad Fronteriza - App de Transporte (Saltos del Guairá & Frontera)

Plataforma de transporte estilo Bolt / Uber diseñada específicamente para la zona de **Saltos del Guairá (Paraguay)** y sus alrededores interurbanos y fronterizos:
- **Paraguay**: Saltos del Guairá, La Paloma, Puente Kyjhá, Katueté, San Alberto.
- **Brasil**: Guaíra (PR), Mundo Novo (MS).

---

## 🌟 Características Destacadas

1. **Bi-Moneda Dinámica (Guaraníes ₲ y Reales R$)**:
   - Muestra tarifas y cobros en ambas monedas con tasa de cambio configurable desde el panel de control.
2. **Métodos de Pago Adaptados**:
   - Efectivo (Cash en ₲ o R$).
   - PIX (clave para usuarios y conductores de Brasil).
   - Transferencia Bancaria / Giros Tigo (Paraguay).
3. **Control Total Administrativo (Django Admin & Dashboard)**:
   - Gestión de choferes, verificación de documentos (Cédula, CNH, Habilitación).
   - Monitoreo de viajes en vivo y recaudación de comisiones.
4. **Apps Web Móviles (PWA)**:
   - Pasajero y Conductor cuentan con interfaces móviles optimizadas con mapas interactivos (Leaflet / OpenStreetMap / Google Maps) sin necesidad de instalar archivos pesados.

---

## 📂 Estructura del Proyecto

```
AppTransporteSaltos/
├── README.md                      # Este archivo
├── requirements.txt               # Dependencias de Python / Django
├── backend/                       # Servidor API & Panel de Administración (Python Django)
│   ├── manage.py
│   ├── core/                      # Configuración Django (settings, urls, wsgi)
│   └── api/                       # Modelos, Vistas API y Admin
├── frontend_passenger/            # App Móvil (PWA) para el Pasajero
│   └── index.html                 # Interfaz interactiva de Pasajero con Mapa
└── frontend_driver/               # App Móvil (PWA) para el Conductor
    └── index.html                 # Interfaz interactiva de Conductor (Aceptar Viajes)
```

---

## 🚀 Cómo Ejecutar el Proyecto

### 1. Iniciar el Backend (Python Django)

Abre la terminal en la carpeta `backend`:

```bash
cd backend
python -m venv venv
# En Windows PowerShell:
.\venv\Scripts\activate

pip install -r ../requirements.txt

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser  # Crea tu usuario administrador
python manage.py runserver 0.0.0.0:8000
```

El Panel de Control Web estará disponible en: `http://localhost:8000/admin/`

### 2. Iniciar las Apps Móviles (Pasajero y Conductor)

Puedes abrir los archivos HTML directamente en el navegador del celular o la computadora:
- **App Pasajero**: `frontend_passenger/index.html`
- **App Conductor**: `frontend_driver/index.html`
