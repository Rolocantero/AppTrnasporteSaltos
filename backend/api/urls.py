from django.urls import path
from . import views

urlpatterns = [
    path('currency/', views.get_exchange_rate, name='get_exchange_rate'),
    path('currency/update/', views.update_exchange_rate, name='update_exchange_rate'),
    path('fare/', views.get_fare_config, name='get_fare_config'),
    path('fare/update/', views.update_fare_config, name='update_fare_config'),
    path('quote/', views.calculate_quote, name='calculate_quote'),
    path('rides/create/', views.create_ride_request, name='create_ride_request'),
    path('rides/pending/', views.list_pending_rides, name='list_pending_rides'),
    path('rides/<int:ride_id>/accept/', views.accept_ride, name='accept_ride'),
    path('rides/<int:ride_id>/status/', views.update_ride_status, name='update_ride_status'),
    path('dashboard/stats/', views.get_dashboard_stats, name='get_dashboard_stats'),
    path('drivers/create/', views.register_driver, name='register_driver'),
    path('drivers/list/', views.list_drivers, name='list_drivers'),
    path('expenses/create/', views.add_expense, name='add_expense'),
    path('reports/summary/', views.get_accounting_report, name='get_accounting_report'),
    path('reports/export/csv/', views.export_report_csv, name='export_report_csv'),
    path('locations/', views.list_locations, name='list_locations'),
    path('locations/create/', views.create_city_location, name='create_city_location'),
    path('locations/<int:location_id>/delete/', views.delete_city_location, name='delete_city_location'),
]
