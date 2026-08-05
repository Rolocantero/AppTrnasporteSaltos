from django.db import models

class CurrencyExchange(models.Model):
    pyg_per_brl = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=1400.00,
        verbose_name="1 Real (R$) en Guaraníes (₲)"
    )
    pyg_per_usd = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=7500.00,
        verbose_name="1 Dólar ($) en Guaraníes (₲)"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        verbose_name = "Tipo de Cambio (₲ / R$ / USD)"
        verbose_name_plural = "Tipo de Cambio (₲ / R$ / USD)"

    def __str__(self):
        return f"1 R$ = {self.pyg_per_brl} ₲ | 1 USD = {self.pyg_per_usd} ₲"


class FareConfig(models.Model):
    base_fare_pyg = models.IntegerField(default=20000, verbose_name="Tarifa Base (₲)")
    price_per_km_pyg = models.IntegerField(default=3500, verbose_name="Precio por Km (₲)")
    price_per_min_pyg = models.IntegerField(default=500, verbose_name="Precio por Minuto (₲)")
    app_commission_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=15.00, 
        verbose_name="Comisión App (%)"
    )
    is_active = models.BooleanField(default=True, verbose_name="Tarifa Activa")

    class Meta:
        verbose_name = "Configuración de Tarifa"
        verbose_name_plural = "Configuraciones de Tarifa"

    def __str__(self):
        return f"Base: ₲{self.base_fare_pyg} | ₲{self.price_per_km_pyg}/km | Comisión: {self.app_commission_percent}%"


class Driver(models.Model):
    COUNTRY_CHOICES = [
        ('PY', 'Paraguay'),
        ('BR', 'Brasil'),
    ]

    name = models.CharField(max_length=150, verbose_name="Nombre Completo")
    phone = models.CharField(max_length=30, verbose_name="Teléfono / WhatsApp")
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES, default='PY', verbose_name="País")
    document_id = models.CharField(max_length=50, verbose_name="Cédula / RG / CPF")
    
    vehicle_model = models.CharField(max_length=100, verbose_name="Modelo del Vehículo")
    vehicle_color = models.CharField(max_length=50, verbose_name="Color")
    license_plate = models.CharField(max_length=20, verbose_name="Chapa / Placa")

    pin_code = models.CharField(max_length=10, default="1234", verbose_name="PIN Acceso (4 dígitos)")
    total_km_driven = models.FloatField(default=0.0, verbose_name="Kilometraje Acumulado (km)")
    last_service_km = models.FloatField(default=0.0, verbose_name="Km del Último Mantenimiento")

    pix_key = models.CharField(max_length=100, blank=True, null=True, verbose_name="Chave PIX (Brasil)")
    bank_alias = models.CharField(max_length=100, blank=True, null=True, verbose_name="Alias Cta. Bancaria (Paraguay)")

    photo_ci = models.FileField(upload_to='drivers/ci/', null=True, blank=True, verbose_name="Foto Cédula / RG / CPF")
    photo_judicial = models.FileField(upload_to='drivers/judicial/', null=True, blank=True, verbose_name="Antecedentes Judiciales")
    photo_police = models.FileField(upload_to='drivers/police/', null=True, blank=True, verbose_name="Antecedentes Policiales")
    photo_license_plate = models.FileField(upload_to='drivers/plate/', null=True, blank=True, verbose_name="Foto de la Chapa / Placa")
    photo_vehicle = models.FileField(upload_to='drivers/vehicle/', null=True, blank=True, verbose_name="Foto del Vehículo")

    rating_sum = models.IntegerField(default=0, verbose_name="Suma de Estrellas")
    rating_count = models.IntegerField(default=0, verbose_name="Cantidad de Calificaciones")

    @property
    def rating_avg(self):
        if self.rating_count > 0:
            return round(self.rating_sum / self.rating_count, 1)
        return 5.0

    is_verified = models.BooleanField(default=True, verbose_name="Verificado por Admin")
    is_online = models.BooleanField(default=False, verbose_name="En Línea")
    
    current_lat = models.FloatField(null=True, blank=True, verbose_name="Latitud")
    current_lng = models.FloatField(null=True, blank=True, verbose_name="Longitud")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Conductor"
        verbose_name_plural = "Conductores"

    def __str__(self):
        return f"{self.name} ({self.vehicle_model} - {self.license_plate}) ⭐{self.rating_avg}"


class Coupon(models.Model):
    code = models.CharField(max_length=30, unique=True, verbose_name="Código de Cupón")
    discount_percent = models.IntegerField(default=0, verbose_name="Descuento (%)")
    discount_flat_pyg = models.IntegerField(default=0, verbose_name="Descuento Fijo (₲)")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cupón de Descuento"
        verbose_name_plural = "Cupones de Descuento"

    def __str__(self):
        return f"{self.code} ({self.discount_percent}% / ₲{self.discount_flat_pyg})"


class Passenger(models.Model):
    name = models.CharField(max_length=150, verbose_name="Nombre Completo")
    phone = models.CharField(max_length=30, verbose_name="Teléfono / WhatsApp")

    class Meta:
        verbose_name = "Pasajero"
        verbose_name_plural = "Pasajeros"

    def __str__(self):
        return f"{self.name} ({self.phone})"


class RideRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Buscando Conductor'),
        ('ACCEPTED', 'Conductor En Camino'),
        ('IN_PROGRESS', 'En Viaje'),
        ('COMPLETED', 'Finalizado'),
        ('CANCELLED', 'Cancelado'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('CASH_PYG', 'Efectivo Guaraníes (₲)'),
        ('CASH_BRL', 'Efectivo Reales (R$)'),
        ('CASH_USD', 'Efectivo Dólares ($)'),
        ('PIX', 'PIX (Brasil)'),
        ('TRANSFER', 'Transferencia / Giro (Paraguay)'),
    ]

    passenger = models.ForeignKey(Passenger, on_delete=models.CASCADE, related_name='rides')
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name='rides')
    
    origin_address = models.CharField(max_length=255, verbose_name="Origen")
    origin_lat = models.FloatField(verbose_name="Latitud Origen")
    origin_lng = models.FloatField(verbose_name="Longitud Origen")

    destination_address = models.CharField(max_length=255, verbose_name="Destino")
    destination_lat = models.FloatField(verbose_name="Latitud Destino")
    destination_lng = models.FloatField(verbose_name="Longitud Destino")

    distance_km = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    estimated_minutes = models.IntegerField(default=0)

    total_fare_pyg = models.IntegerField(default=0, verbose_name="Total ₲")
    total_fare_brl = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, verbose_name="Total R$")
    total_fare_usd = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, verbose_name="Total USD $")
    app_commission_pyg = models.IntegerField(default=0, verbose_name="Comisión App ₲")

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='CASH_PYG')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    rating = models.IntegerField(null=True, blank=True, verbose_name="Calificación (1-5 estrellas)")
    rating_comment = models.TextField(null=True, blank=True, verbose_name="Comentario Pasajero")

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Solicitud de Viaje"
        verbose_name_plural = "Solicitudes de Viajes"

    def __str__(self):
        return f"Viaje #{self.id} | {self.origin_address} ➔ {self.destination_address}"


class Expense(models.Model):
    description = models.CharField(max_length=200, verbose_name="Descripción del Gasto")
    category = models.CharField(max_length=50, default="Operaciones", verbose_name="Categoría")
    amount_pyg = models.IntegerField(default=0, verbose_name="Monto en Guaraníes (₲)")
    date = models.DateField(auto_now_add=True, verbose_name="Fecha del Gasto")

    class Meta:
        verbose_name = "Gasto Operativo"
        verbose_name_plural = "Gastos Operativos"

    def __str__(self):
        return f"{self.description} ({self.category}): ₲ {self.amount_pyg}"


class CityLocation(models.Model):
    name = models.CharField(max_length=150, verbose_name="Nombre de la Ciudad / Punto")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="Latitud")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="Longitud")
    is_active = models.BooleanField(default=True, verbose_name="Activo en la App")
    display_order = models.IntegerField(default=0, verbose_name="Orden de visualización")

    class Meta:
        verbose_name = "Ciudad / Itinerario de Mapa"
        verbose_name_plural = "Ciudades e Itinerarios de Mapa"
        ordering = ['display_order', 'name']

    def __str__(self):
        return f"{self.name} ({self.latitude}, {self.longitude})"
