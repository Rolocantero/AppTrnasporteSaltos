from django.contrib import admin
from .models import CurrencyExchange, FareConfig, Driver, Passenger, RideRequest, Expense, CityLocation

@admin.register(CityLocation)
class CityLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude', 'is_active', 'display_order')
    list_editable = ('is_active', 'display_order')
    search_fields = ('name',)

@admin.register(CurrencyExchange)
class CurrencyExchangeAdmin(admin.ModelAdmin):
    list_display = ('pyg_per_brl', 'pyg_per_usd', 'updated_at')

@admin.register(FareConfig)
class FareConfigAdmin(admin.ModelAdmin):
    list_display = ('base_fare_pyg', 'price_per_km_pyg', 'price_per_min_pyg', 'app_commission_percent', 'is_active')

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'country', 'vehicle_model', 'license_plate', 'is_verified', 'is_online')
    list_filter = ('country', 'is_verified', 'is_online')
    search_fields = ('name', 'phone', 'document_id', 'license_plate')
    actions = ['approve_drivers', 'disapprove_drivers']

    @admin.action(description="Aprobar conductores seleccionados")
    def approve_drivers(self, request, queryset):
        queryset.update(is_verified=True)

    @admin.action(description="Desactivar verificación de conductores")
    def disapprove_drivers(self, request, queryset):
        queryset.update(is_verified=False)

@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone')
    search_fields = ('name', 'phone')

@admin.register(RideRequest)
class RideRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'passenger', 'driver', 'origin_address', 'destination_address', 'distance_km', 'total_fare_pyg', 'total_fare_brl', 'total_fare_usd', 'payment_method', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('origin_address', 'destination_address', 'passenger__name', 'driver__name')

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'category', 'amount_pyg', 'date')
    list_filter = ('category', 'date')
