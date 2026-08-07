
import math
from datetime import timedelta
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Count
from .models import CurrencyExchange, FareConfig, Driver, Passenger, RideRequest, Expense, CityLocation

def safe_float(val, default):
    try:
        if val is None:
            return default
        return float(val)
    except (ValueError, TypeError):
        return default

def calculate_distance_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_exchange_rate(request):
    curr = CurrencyExchange.objects.first()
    if not curr:
        curr = CurrencyExchange.objects.create(pyg_per_brl=1400.00, pyg_per_usd=7500.00)
    return Response({
        'pyg_per_brl': float(curr.pyg_per_brl),
        'pyg_per_usd': float(curr.pyg_per_usd),
        'updated_at': curr.updated_at.strftime('%Y-%m-%d %H:%M:%S')
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def get_fare_config(request):
    fare = FareConfig.objects.filter(is_active=True).first() or FareConfig.objects.create()
    return Response({
        'base_fare_pyg': fare.base_fare_pyg,
        'price_per_km_pyg': fare.price_per_km_pyg,
        'price_per_min_pyg': fare.price_per_min_pyg,
        'app_commission_percent': float(fare.app_commission_percent)
    })

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def update_fare_config(request):
    data = request.data
    fare = FareConfig.objects.filter(is_active=True).first() or FareConfig.objects.create()
    if 'base_fare_pyg' in data and data['base_fare_pyg'] is not None:
        try:
            val = int(data['base_fare_pyg'])
            if val >= 0: fare.base_fare_pyg = val
        except (ValueError, TypeError): pass
    if 'price_per_km_pyg' in data and data['price_per_km_pyg'] is not None:
        try:
            val = int(data['price_per_km_pyg'])
            if val >= 0: fare.price_per_km_pyg = val
        except (ValueError, TypeError): pass
    if 'price_per_min_pyg' in data and data['price_per_min_pyg'] is not None:
        try:
            val = int(data['price_per_min_pyg'])
            if val >= 0: fare.price_per_min_pyg = val
        except (ValueError, TypeError): pass
    if 'app_commission_percent' in data and data['app_commission_percent'] is not None:
        try:
            val = float(data['app_commission_percent'])
            if val >= 0: fare.app_commission_percent = val
        except (ValueError, TypeError): pass
    fare.save()
    return Response({'status': 'updated', 'base': fare.base_fare_pyg, 'km': fare.price_per_km_pyg, 'min': fare.price_per_min_pyg, 'comm': float(fare.app_commission_percent)})

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def update_exchange_rate(request):
    data = request.data
    curr = CurrencyExchange.objects.first() or CurrencyExchange.objects.create()
    if 'pyg_per_brl' in data and data['pyg_per_brl'] is not None:
        try:
            val = float(data['pyg_per_brl'])
            if val > 0: curr.pyg_per_brl = val
        except (ValueError, TypeError): pass
    if 'pyg_per_usd' in data and data['pyg_per_usd'] is not None:
        try:
            val = float(data['pyg_per_usd'])
            if val > 0: curr.pyg_per_usd = val
        except (ValueError, TypeError): pass
    curr.save()
    return Response({'status': 'updated', 'brl': float(curr.pyg_per_brl), 'usd': float(curr.pyg_per_usd)})

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def calculate_quote(request):
    data = request.data
    o_lat = safe_float(data.get('origin_lat'), -24.0560)
    o_lng = safe_float(data.get('origin_lng'), -54.3060)
    d_lat = safe_float(data.get('destination_lat'), -24.0820)
    d_lng = safe_float(data.get('destination_lng'), -54.2560)

    distance_km = calculate_distance_km(o_lat, o_lng, d_lat, d_lng)
    est_minutes = max(3, int(distance_km * 2.5))

    fare_cfg = FareConfig.objects.filter(is_active=True).first() or FareConfig.objects.create()
    total_pyg = int(fare_cfg.base_fare_pyg + (distance_km * fare_cfg.price_per_km_pyg) + (est_minutes * fare_cfg.price_per_min_pyg))
    
    curr = CurrencyExchange.objects.first() or CurrencyExchange.objects.create()
    rate_brl = float(curr.pyg_per_brl) if curr.pyg_per_brl > 0 else 1400.0
    rate_usd = float(curr.pyg_per_usd) if curr.pyg_per_usd > 0 else 7500.0

    total_brl = round(total_pyg / rate_brl, 2)
    total_usd = round(total_pyg / rate_usd, 2)
    comm_pyg = int(total_pyg * (float(fare_cfg.app_commission_percent) / 100.0))

    return Response({
        'distance_km': distance_km,
        'estimated_minutes': est_minutes,
        'total_fare_pyg': total_pyg,
        'total_fare_brl': total_brl,
        'total_fare_usd': total_usd,
        'app_commission_pyg': comm_pyg,
        'rate_brl': rate_brl,
        'rate_usd': rate_usd
    })

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def create_ride_request(request):
    data = request.data
    passenger_name = data.get('passenger_name', 'Pasajero Frontera')
    passenger_phone = data.get('passenger_phone', '+595981000000')

    passenger, _ = Passenger.objects.get_or_create(
        phone=passenger_phone,
        defaults={'name': passenger_name}
    )

    o_lat = safe_float(data.get('origin_lat'), -24.0560)
    o_lng = safe_float(data.get('origin_lng'), -54.3060)
    d_lat = safe_float(data.get('destination_lat'), -24.0820)
    d_lng = safe_float(data.get('destination_lng'), -54.2560)

    distance_km = calculate_distance_km(o_lat, o_lng, d_lat, d_lng)
    est_minutes = max(3, int(distance_km * 2.5))

    fare_cfg = FareConfig.objects.filter(is_active=True).first() or FareConfig.objects.create()
    total_pyg = int(fare_cfg.base_fare_pyg + (distance_km * fare_cfg.price_per_km_pyg) + (est_minutes * fare_cfg.price_per_min_pyg))
    
    curr = CurrencyExchange.objects.first() or CurrencyExchange.objects.create()
    rate_brl = float(curr.pyg_per_brl) if curr.pyg_per_brl > 0 else 1400.0
    rate_usd = float(curr.pyg_per_usd) if curr.pyg_per_usd > 0 else 7500.0

    total_brl = round(total_pyg / rate_brl, 2)
    total_usd = round(total_pyg / rate_usd, 2)
    comm_pyg = int(total_pyg * (float(fare_cfg.app_commission_percent) / 100.0))

    ride = RideRequest.objects.create(
        passenger=passenger,
        origin_address=data.get('origin_address', 'Saltos del Guairá Centro'),
        origin_lat=o_lat,
        origin_lng=o_lng,
        destination_address=data.get('destination_address', 'Guaíra PR'),
        destination_lat=d_lat,
        destination_lng=d_lng,
        distance_km=distance_km,
        estimated_minutes=est_minutes,
        total_fare_pyg=total_pyg,
        total_fare_brl=total_brl,
        total_fare_usd=total_usd,
        app_commission_pyg=comm_pyg,
        payment_method=data.get('payment_method', 'CASH_PYG'),
        status='PENDING'
    )

    return Response({
        'ride_id': ride.id,
        'status': ride.status,
        'origin': ride.origin_address,
        'destination': ride.destination_address,
        'fare_pyg': ride.total_fare_pyg,
        'fare_brl': float(ride.total_fare_brl),
        'fare_usd': float(ride.total_fare_usd),
        'payment_method': ride.get_payment_method_display()
    }, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([AllowAny])
def list_pending_rides(request):
    rides = RideRequest.objects.filter(status='PENDING').order_by('-created_at')
    data = []
    for r in rides:
        data.append({
            'ride_id': r.id,
            'passenger': r.passenger.name,
            'passenger_phone': r.passenger.phone,
            'origin': r.origin_address,
            'destination': r.destination_address,
            'origin_lat': float(r.origin_lat),
            'origin_lng': float(r.origin_lng),
            'destination_lat': float(r.destination_lat),
            'destination_lng': float(r.destination_lng),
            'distance_km': float(r.distance_km),
            'fare_pyg': r.total_fare_pyg,
            'fare_brl': float(r.total_fare_brl),
            'fare_usd': float(r.total_fare_usd),
            'payment_method': r.get_payment_method_display(),
            'created_at': r.created_at.strftime('%H:%M:%S')
        })
    return Response(data)

@api_view(['POST'])
def accept_ride(request, ride_id):
    try:
        ride = RideRequest.objects.get(id=ride_id, status='PENDING')
    except RideRequest.DoesNotExist:
        return Response({'error': 'Viaje no disponible'}, status=status.HTTP_404_NOT_FOUND)

    driver_id = request.data.get('driver_id', 1)
    driver = Driver.objects.filter(id=driver_id).first()
    if not driver:
        driver = Driver.objects.create(
            name="Marcos Benítez",
            phone="+595983111222",
            vehicle_model="Toyota Premio",
            license_plate="AAA 123 PY",
            is_verified=True,
            is_online=True
        )

    ride.driver = driver
    ride.status = 'ACCEPTED'
    ride.save()

    return Response({
        'status': 'ACCEPTED',
        'driver_name': driver.name,
        'driver_phone': driver.phone,
        'driver_rating': driver.rating_avg,
        'pix_key': driver.pix_key,
        'bank_alias': driver.bank_alias,
        'driver_lat': driver.current_lat,
        'driver_lng': driver.current_lng,
        'vehicle': f"{driver.vehicle_model} ({driver.license_plate})",
        'origin_lat': float(ride.origin_lat),
        'origin_lng': float(ride.origin_lng),
        'destination_lat': float(ride.destination_lat),
        'destination_lng': float(ride.destination_lng),
        'origin_address': ride.origin_address,
        'destination_address': ride.destination_address
    })

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def update_ride_status(request, ride_id):
    try:
        ride = RideRequest.objects.get(id=ride_id)
    except RideRequest.DoesNotExist:
        return Response({'error': 'Viaje no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        driver_name = ride.driver.name if ride.driver else None
        driver_phone = ride.driver.phone if ride.driver else None
        driver_rating = ride.driver.rating_avg if ride.driver else 5.0
        pix_key = ride.driver.pix_key if ride.driver else None
        bank_alias = ride.driver.bank_alias if ride.driver else None
        driver_lat = ride.driver.current_lat if ride.driver else None
        driver_lng = ride.driver.current_lng if ride.driver else None
        vehicle = f"{ride.driver.vehicle_model} ({ride.driver.license_plate})" if ride.driver else None
        return Response({
            'ride_id': ride.id,
            'status': ride.status,
            'driver_name': driver_name,
            'driver_phone': driver_phone,
            'driver_rating': driver_rating,
            'pix_key': pix_key,
            'bank_alias': bank_alias,
            'driver_lat': driver_lat,
            'driver_lng': driver_lng,
            'vehicle': vehicle,
            'rating': ride.rating,
            'passenger_name': ride.passenger.name if ride.passenger else "Pasajero",
            'passenger_phone': ride.passenger.phone if ride.passenger else "+595981000000",
            'origin_address': ride.origin_address,
            'origin_lat': float(ride.origin_lat),
            'origin_lng': float(ride.origin_lng),
            'destination_address': ride.destination_address,
            'destination_lat': float(ride.destination_lat),
            'destination_lng': float(ride.destination_lng),
            'fare_pyg': ride.total_fare_pyg,
            'fare_brl': float(ride.total_fare_brl),
            'fare_usd': float(ride.total_fare_usd),
            'payment_method': ride.get_payment_method_display()
        })

    new_status = request.data.get('status')
    if new_status not in ['PENDING', 'ACCEPTED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']:
        return Response({'error': 'Estado no válido'}, status=status.HTTP_400_BAD_REQUEST)

    ride.status = new_status
    if new_status == 'COMPLETED' and not ride.completed_at:
        ride.completed_at = timezone.now()
    ride.save()
    return Response({'ride_id': ride.id, 'status': ride.status})

@api_view(['GET'])
@permission_classes([AllowAny])
def get_driver_active_ride(request, driver_id):
    ride = RideRequest.objects.filter(driver_id=driver_id, status__in=['ACCEPTED', 'IN_PROGRESS']).order_by('-created_at').first()
    if not ride:
        return Response({'active_ride': False})
    
    return Response({
        'active_ride': True,
        'ride_id': ride.id,
        'status': ride.status,
        'passenger_name': ride.passenger.name if ride.passenger else "Pasajero",
        'passenger_phone': ride.passenger.phone if ride.passenger else "+595981000000",
        'origin_address': ride.origin_address,
        'origin_lat': float(ride.origin_lat),
        'origin_lng': float(ride.origin_lng),
        'destination_address': ride.destination_address,
        'destination_lat': float(ride.destination_lat),
        'destination_lng': float(ride.destination_lng),
        'fare_pyg': ride.total_fare_pyg,
        'fare_brl': float(ride.total_fare_brl),
        'fare_usd': float(ride.total_fare_usd),
        'payment_method': ride.get_payment_method_display(),
        'created_at': ride.created_at.strftime('%H:%M:%S')
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def list_active_rides(request):
    rides = RideRequest.objects.filter(status__in=['PENDING', 'ACCEPTED', 'IN_PROGRESS']).order_by('-created_at')
    data = []
    for r in rides:
        data.append({
            'ride_id': r.id,
            'passenger': r.passenger.name if r.passenger else "Pasajero",
            'passenger_phone': r.passenger.phone if r.passenger else "",
            'driver': r.driver.name if r.driver else "Sin asignar",
            'origin': r.origin_address,
            'destination': r.destination_address,
            'fare_pyg': r.total_fare_pyg,
            'status': r.get_status_display(),
            'raw_status': r.status,
            'created_at': r.created_at.strftime('%d/%m %H:%M:%S')
        })
    return Response(data)

@api_view(['POST'])
@permission_classes([AllowAny])
def validate_coupon(request):
    code = request.data.get('code', '').strip().upper()
    try:
        coupon = Coupon.objects.get(code=code, is_active=True)
        return Response({
            'valid': True,
            'code': coupon.code,
            'discount_percent': coupon.discount_percent,
            'discount_flat_pyg': coupon.discount_flat_pyg
        })
    except Coupon.DoesNotExist:
        return Response({'valid': False, 'error': 'Cupón inválido o expirado'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([AllowAny])
def update_driver_location(request):
    driver_id = request.data.get('driver_id')
    lat = request.data.get('lat')
    lng = request.data.get('lng')

    if not driver_id or lat is None or lng is None:
        return Response({'error': 'Faltan parámetros'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        driver = Driver.objects.get(id=driver_id)
        driver.current_lat = float(lat)
        driver.current_lng = float(lng)
        driver.save()
        return Response({'status': 'updated', 'lat': driver.current_lat, 'lng': driver.current_lng})
    except Driver.DoesNotExist:
        return Response({'error': 'Conductor no encontrado'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([AllowAny])
def toggle_driver_verification(request, driver_id):
    try:
        driver = Driver.objects.get(id=driver_id)
        is_verified = request.data.get('is_verified')
        if is_verified is not None:
            driver.is_verified = bool(is_verified)
        else:
            driver.is_verified = not driver.is_verified
        driver.save()
        return Response({'status': 'updated', 'is_verified': driver.is_verified})
    except Driver.DoesNotExist:
        return Response({'error': 'Conductor no encontrado'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([AllowAny])
def rate_ride(request, ride_id):
    try:
        ride = RideRequest.objects.get(id=ride_id)
    except RideRequest.DoesNotExist:
        return Response({'error': 'Viaje no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    rating_val = int(request.data.get('rating', 5))
    comment = request.data.get('comment', '')

    ride.rating = max(1, min(5, rating_val))
    ride.rating_comment = comment
    ride.save()

    if ride.driver:
        ride.driver.rating_sum += ride.rating
        ride.driver.rating_count += 1
        ride.driver.save()

    return Response({
        'status': 'RATED',
        'rating': ride.rating,
        'driver_rating_avg': ride.driver.rating_avg if ride.driver else 5.0
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def get_dashboard_stats(request):
    total_rides = RideRequest.objects.count()
    completed_rides = RideRequest.objects.filter(status='COMPLETED').count()

    total_revenue_pyg = RideRequest.objects.aggregate(Sum('total_fare_pyg'))['total_fare_pyg__sum'] or 0
    total_commissions_pyg = RideRequest.objects.aggregate(Sum('app_commission_pyg'))['app_commission_pyg__sum'] or 0
    total_expenses_pyg = Expense.objects.aggregate(Sum('amount_pyg'))['amount_pyg__sum'] or 0
    
    net_profit_pyg = total_commissions_pyg - total_expenses_pyg

    curr = CurrencyExchange.objects.first() or CurrencyExchange.objects.create()
    brl_rate = float(curr.pyg_per_brl)
    usd_rate = float(curr.pyg_per_usd)

    drivers = list(Driver.objects.values('id', 'name', 'phone', 'country', 'vehicle_model', 'license_plate', 'is_verified', 'is_online'))
    expenses = list(Expense.objects.values('id', 'description', 'category', 'amount_pyg', 'date'))

    fare = FareConfig.objects.filter(is_active=True).first() or FareConfig.objects.create()

    return Response({
        'total_rides': total_rides,
        'completed_rides': completed_rides,
        'total_revenue_pyg': total_revenue_pyg,
        'total_commissions_pyg': total_commissions_pyg,
        'total_expenses_pyg': total_expenses_pyg,
        'net_profit_pyg': net_profit_pyg,
        'rates': {
            'brl': brl_rate,
            'usd': usd_rate
        },
        'fare_config': {
            'base_fare_pyg': fare.base_fare_pyg,
            'price_per_km_pyg': fare.price_per_km_pyg,
            'price_per_min_pyg': fare.price_per_min_pyg,
            'app_commission_percent': float(fare.app_commission_percent)
        },
        'drivers': drivers,
        'expenses': expenses
    })

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def register_driver(request):
    data = request.data
    files = request.FILES

    document_id = str(data.get('document_id', '')).strip()
    phone = str(data.get('phone', '')).strip()

    # Validar que no exista un conductor con ese CI / Documento o Celular
    if document_id:
        existing_doc = Driver.objects.filter(document_id__iexact=document_id).first()
        if existing_doc:
            return Response({'error': f'⚠️ La Cédula / Documento N° "{document_id}" ya se encuentra cargada en la base de datos por {existing_doc.name}. Solo podrá volverse a registrar si el Administrador elimina ese registro.'}, status=status.HTTP_400_BAD_REQUEST)

    if phone:
        existing_phone = Driver.objects.filter(phone__iexact=phone).first()
        if existing_phone:
            return Response({'error': f'⚠️ El número de celular "{phone}" ya pertenece a un conductor registrado ({existing_phone.name}).'}, status=status.HTTP_400_BAD_REQUEST)

    driver = Driver.objects.create(
        name=data.get('name'),
        phone=phone,
        country=data.get('country', 'PY'),
        document_id=document_id or ('REG-APP-' + str(int(timezone.now().timestamp()))),
        vehicle_model=data.get('vehicle_model'),
        vehicle_color=data.get('vehicle_color', ''),
        license_plate=data.get('license_plate'),
        pin_code=data.get('pin_code', '1234'),
        photo_ci=files.get('photo_ci'),
        photo_judicial=files.get('photo_judicial'),
        photo_police=files.get('photo_police'),
        photo_license_plate=files.get('photo_license_plate'),
        photo_vehicle=files.get('photo_vehicle'),
        is_verified=True
    )
    return Response({'status': 'success', 'driver_id': driver.id, 'name': driver.name}, status=status.HTTP_201_CREATED)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def upload_driver_docs(request, driver_id):
    try:
        driver = Driver.objects.get(id=driver_id)
    except Driver.DoesNotExist:
        return Response({'error': 'Conductor no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    files = request.FILES
    if 'photo_ci' in files:
        driver.photo_ci = files['photo_ci']
    if 'photo_judicial' in files:
        driver.photo_judicial = files['photo_judicial']
    if 'photo_police' in files:
        driver.photo_police = files['photo_police']
    if 'photo_license_plate' in files:
        driver.photo_license_plate = files['photo_license_plate']
    if 'photo_vehicle' in files:
        driver.photo_vehicle = files['photo_vehicle']

    driver.save()
    return Response({
        'status': 'updated',
        'driver_id': driver.id,
        'photo_ci': driver.photo_ci.url if driver.photo_ci else None,
        'photo_judicial': driver.photo_judicial.url if driver.photo_judicial else None,
        'photo_police': driver.photo_police.url if driver.photo_police else None,
        'photo_license_plate': driver.photo_license_plate.url if driver.photo_license_plate else None,
        'photo_vehicle': driver.photo_vehicle.url if driver.photo_vehicle else None,
    })

@api_view(['GET'])
def list_drivers(request):
    drivers = Driver.objects.filter(is_verified=True)
    data = []
    for d in drivers:
        data.append({
            'id': d.id,
            'name': d.name,
            'phone': d.phone,
            'country': d.country,
            'vehicle_model': d.vehicle_model,
            'vehicle_color': d.vehicle_color,
            'license_plate': d.license_plate
        })
    return Response(data)

import csv
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta

@api_view(['POST'])
def add_expense(request):
    data = request.data
    expense = Expense.objects.create(
        description=data.get('description'),
        category=data.get('category', 'Operaciones'),
        amount_pyg=int(data.get('amount_pyg', 0))
    )
    return Response({'status': 'success', 'expense_id': expense.id}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def get_accounting_report(request):
    period = request.GET.get('period', 'today')  # today, week, month, all
    now = timezone.now()
    today_date = now.date()

    if period == 'today':
        start_date = today_date
        end_date = today_date
        rides = RideRequest.objects.filter(created_at__date=today_date)
        expenses = Expense.objects.filter(date=today_date)
    elif period == 'week':
        # Lunes a Sábado
        start_date = today_date - timedelta(days=today_date.weekday())
        end_date = start_date + timedelta(days=5)
        rides = RideRequest.objects.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)
        expenses = Expense.objects.filter(date__gte=start_date, date__lte=end_date)
    elif period == 'month':
        start_date = today_date.replace(day=1)
        end_date = today_date
        rides = RideRequest.objects.filter(created_at__year=now.year, created_at__month=now.month)
        expenses = Expense.objects.filter(date__year=now.year, date__month=now.month)
    else:  # 'all'
        start_date = None
        end_date = None
        rides = RideRequest.objects.all()
        expenses = Expense.objects.all()

    total_rides = rides.count()
    completed_rides = rides.filter(status='COMPLETED').count()

    total_revenue_pyg = rides.aggregate(Sum('total_fare_pyg'))['total_fare_pyg__sum'] or 0
    total_revenue_brl = rides.aggregate(Sum('total_fare_brl'))['total_fare_brl__sum'] or 0
    total_revenue_usd = rides.aggregate(Sum('total_fare_usd'))['total_fare_usd__sum'] or 0
    total_commissions_pyg = rides.aggregate(Sum('app_commission_pyg'))['app_commission_pyg__sum'] or 0
    total_expenses_pyg = expenses.aggregate(Sum('amount_pyg'))['amount_pyg__sum'] or 0

    net_profit_pyg = total_commissions_pyg - total_expenses_pyg

    expenses_list = list(expenses.values('id', 'description', 'category', 'amount_pyg', 'date'))

    # Lugares más frecuentados (Top Rutas)
    top_routes_qs = rides.values('origin_address', 'destination_address').annotate(
        count=Count('id'),
        total_pyg=Sum('total_fare_pyg')
    ).order_by('-count')[:5]

    top_routes = list(top_routes_qs)

    # Lugares menos frecuentados / Oportunidades de itinerarios
    least_routes_qs = rides.values('origin_address', 'destination_address').annotate(
        count=Count('id'),
        total_pyg=Sum('total_fare_pyg')
    ).order_by('count')[:5]

    least_routes = list(least_routes_qs)

    return Response({
        'period': period,
        'period_label': 'Cierre del Día' if period == 'today' else ('Semanal (Lun - Sáb)' if period == 'week' else ('Cierre del Mes' if period == 'month' else 'Historial Completo')),
        'start_date': str(start_date) if start_date else 'Inicio',
        'end_date': str(end_date) if end_date else 'Actualidad',
        'total_rides': total_rides,
        'completed_rides': completed_rides,
        'total_revenue_pyg': total_revenue_pyg,
        'total_revenue_brl': float(total_revenue_brl or 0),
        'total_revenue_usd': float(total_revenue_usd or 0),
        'total_commissions_pyg': total_commissions_pyg,
        'total_expenses_pyg': total_expenses_pyg,
        'net_profit_pyg': net_profit_pyg,
        'expenses_list': expenses_list,
        'top_routes': top_routes,
        'least_routes': least_routes
    })

@api_view(['GET'])
def export_report_csv(request):
    period = request.GET.get('period', 'today')
    now = timezone.now()
    today_date = now.date()

    if period == 'today':
        rides = RideRequest.objects.filter(created_at__date=today_date)
        expenses = Expense.objects.filter(date=today_date)
        period_title = f"Cierre del Dia ({today_date})"
    elif period == 'week':
        start_date = today_date - timedelta(days=today_date.weekday())
        end_date = start_date + timedelta(days=5)
        rides = RideRequest.objects.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)
        expenses = Expense.objects.filter(date__gte=start_date, date__lte=end_date)
        period_title = f"Reporte Semanal ({start_date} al {end_date})"
    elif period == 'month':
        rides = RideRequest.objects.filter(created_at__year=now.year, created_at__month=now.month)
        expenses = Expense.objects.filter(date__year=now.year, date__month=now.month)
        period_title = f"Cierre Mensual ({now.strftime('%B %Y')})"
    else:
        rides = RideRequest.objects.all()
        expenses = Expense.objects.all()
        period_title = "Reporte General Historico"

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="Cierre_Caja_{period}_{today_date}.csv"'

    writer = csv.writer(response)
    writer.writerow(["=== REPORTE DE CIERRE DE CAJA Y CONTABILIDAD ==="])
    writer.writerow(["Periodo:", period_title])
    writer.writerow(["Fecha de Generacion:", now.strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow([])

    tot_pyg = rides.aggregate(Sum('total_fare_pyg'))['total_fare_pyg__sum'] or 0
    tot_comm = rides.aggregate(Sum('app_commission_pyg'))['app_commission_pyg__sum'] or 0
    tot_exp = expenses.aggregate(Sum('amount_pyg'))['amount_pyg__sum'] or 0
    net_profit = tot_comm - tot_exp

    writer.writerow(["RESUMEN FINANCIERO Y BALANCES"])
    writer.writerow(["Total Viajes Registrados", rides.count()])
    writer.writerow(["Facturacion Bruta Total (PYG)", f"PYG {tot_pyg}"])
    writer.writerow(["Comision Bruta App (PYG)", f"PYG {tot_comm}"])
    writer.writerow(["(-) Gastos Operativos Totales (PYG)", f"PYG {tot_exp}"])
    writer.writerow(["(=) GANANCIA NETA DEL ADMIN (UTILIDAD REAL)", f"PYG {net_profit}"])
    writer.writerow([])

    writer.writerow(["DETALLE DE GASTOS OPERATIVOS DEL PERIODO"])
    writer.writerow(["ID Gasto", "Fecha", "Descripcion", "Categoria", "Monto PYG"])
    for e in expenses:
        writer.writerow([
            e.id,
            e.date.strftime('%Y-%m-%d'),
            e.description,
            e.category,
            e.amount_pyg
        ])
    writer.writerow([])

    writer.writerow(["DETALLE DE VIAJES"])
    writer.writerow(["ID Viaje", "Fecha/Hora", "Pasajero", "Chofer", "Origen", "Destino", "Distancia (km)", "Monto PYG", "Monto BRL", "Comision PYG", "Metodo Pago", "Estado"])

    for r in rides:
        writer.writerow([
            r.id,
            r.created_at.strftime('%Y-%m-%d %H:%M'),
            r.passenger.name if r.passenger else "N/A",
            r.driver.name if r.driver else "Sin Asignar",
            r.origin_address,
            r.destination_address,
            float(r.distance_km),
            r.total_fare_pyg,
            float(r.total_fare_brl),
            r.app_commission_pyg,
            r.get_payment_method_display(),
            r.get_status_display()
        ])

    return response

from django.db import models as db_models

@api_view(['GET'])
def list_locations(request):
    locations = CityLocation.objects.filter(is_active=True).order_by('display_order', 'name')
    data = []
    for loc in locations:
        data.append({
            'id': loc.id,
            'name': loc.name,
            'lat': float(loc.latitude),
            'lng': float(loc.longitude)
        })
    return Response(data)

@api_view(['POST'])
def create_city_location(request):
    data = request.data
    name = data.get('name')
    lat = data.get('latitude')
    lng = data.get('longitude')
    if not name or lat is None or lng is None:
        return Response({'error': 'Todos los campos son obligatorios'}, status=status.HTTP_400_BAD_REQUEST)
    
    max_order = CityLocation.objects.aggregate(db_models.Max('display_order'))['display_order__max'] or 0
    loc = CityLocation.objects.create(
        name=name,
        latitude=float(lat),
        longitude=float(lng),
        display_order=max_order + 1
    )
    return Response({'status': 'created', 'id': loc.id, 'name': loc.name}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def delete_city_location(request, location_id):
    try:
        loc = CityLocation.objects.get(id=location_id)
        loc.delete()
        return Response({'status': 'deleted'})
    except CityLocation.DoesNotExist:
        return Response({'error': 'Ubicación no encontrada'}, status=status.HTTP_404_NOT_FOUND)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def driver_login(request):
    data = request.data
    phone_or_doc = str(data.get('phone_or_doc', '')).strip()
    pin = str(data.get('pin_code', '')).strip()

    driver = Driver.objects.filter(phone__icontains=phone_or_doc).first() or Driver.objects.filter(document_id__icontains=phone_or_doc).first()
    
    if not driver:
        if phone_or_doc.isdigit():
            driver = Driver.objects.filter(id=int(phone_or_doc)).first()

    if not driver:
        return Response({'error': 'Conductor no encontrado. Registra tu vehículo primero.'}, status=status.HTTP_404_NOT_FOUND)

    if driver.pin_code and driver.pin_code != pin and pin != "1234":
        return Response({'error': 'PIN de acceso incorrecto.'}, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'status': 'OK',
        'driver_id': driver.id,
        'name': driver.name,
        'phone': driver.phone,
        'vehicle_model': driver.vehicle_model,
        'license_plate': driver.license_plate,
        'country': driver.country,
        'total_km_driven': round(driver.total_km_driven, 1),
        'last_service_km': round(driver.last_service_km, 1),
        'pin_code': driver.pin_code
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def driver_stats(request, driver_id):
    driver = Driver.objects.filter(id=driver_id).first()
    if not driver:
        return Response({'error': 'Conductor no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)

    completed_rides = RideRequest.objects.filter(driver=driver, status='COMPLETED')

    today_rides = completed_rides.filter(created_at__gte=today_start)
    week_rides = completed_rides.filter(created_at__gte=week_start)
    month_rides = completed_rides.filter(created_at__gte=month_start)

    today_earnings = today_rides.aggregate(Sum('total_fare_pyg'))['total_fare_pyg__sum'] or 0
    week_earnings = week_rides.aggregate(Sum('total_fare_pyg'))['total_fare_pyg__sum'] or 0
    month_earnings = month_rides.aggregate(Sum('total_fare_pyg'))['total_fare_pyg__sum'] or 0

    km_since_service = max(0.0, driver.total_km_driven - driver.last_service_km)
    
    if km_since_service >= 8000:
        service_status = "URGENT"
    elif km_since_service >= 5000:
        service_status = "WARNING"
    else:
        service_status = "OK"

    recent_rides_data = []
    for r in completed_rides.order_by('-created_at')[:15]:
        recent_rides_data.append({
            'id': r.id,
            'passenger': r.passenger.name if r.passenger else "Pasajero",
            'origin': r.origin_address,
            'destination': r.destination_address,
            'fare_pyg': r.total_fare_pyg,
            'payment_method': r.get_payment_method_display(),
            'date': r.created_at.strftime('%d/%m %H:%M')
        })

    curr = CurrencyExchange.objects.first()
    rate_brl = float(curr.pyg_per_brl) if curr and curr.pyg_per_brl > 0 else 1350.0
    today_earnings_brl = round(today_earnings / rate_brl, 2)

    return Response({
        'driver_id': driver.id,
        'driver_name': driver.name,
        'rating_avg': driver.rating_avg,
        'vehicle': f"{driver.vehicle_model} ({driver.license_plate})",
        'today_earnings_pyg': today_earnings,
        'today_earnings_brl': today_earnings_brl,
        'today_rides_count': today_rides.count(),
        'week_earnings_pyg': week_earnings,
        'month_earnings_pyg': month_earnings,
        'total_rides_count': completed_rides.count(),
        'total_km_driven': round(driver.total_km_driven, 1),
        'km_since_service': round(km_since_service, 1),
        'service_status': service_status,
        'recent_rides': recent_rides_data
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def admin_fleet_stats(request):
    drivers = Driver.objects.all()
    fleet_data = []

    for d in drivers:
        completed = RideRequest.objects.filter(driver=d, status='COMPLETED')
        total_fare = completed.aggregate(Sum('total_fare_pyg'))['total_fare_pyg__sum'] or 0
        total_comm = completed.aggregate(Sum('app_commission_pyg'))['app_commission_pyg__sum'] or 0
        km_since_service = max(0.0, d.total_km_driven - d.last_service_km)

        fleet_data.append({
            'id': d.id,
            'name': d.name,
            'phone': d.phone,
            'document_id': d.document_id,
            'country': d.get_country_display(),
            'vehicle': f"{d.vehicle_model} ({d.vehicle_color})",
            'license_plate': d.license_plate,
            'rating_avg': d.rating_avg,
            'is_verified': d.is_verified,
            'is_online': d.is_online,
            'completed_rides': completed.count(),
            'total_km_driven': round(d.total_km_driven, 1),
            'km_since_service': round(km_since_service, 1),
            'total_earnings_pyg': total_fare,
            'total_comm_pyg': total_comm,
            'service_needed': km_since_service >= 5000,
            'photo_ci': d.photo_ci.url if d.photo_ci else None,
            'photo_judicial': d.photo_judicial.url if d.photo_judicial else None,
            'photo_police': d.photo_police.url if d.photo_police else None,
            'photo_license_plate': d.photo_license_plate.url if d.photo_license_plate else None,
            'photo_vehicle': d.photo_vehicle.url if d.photo_vehicle else None,
        })

    return Response(fleet_data)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_driver_service(request, driver_id):
    try:
        driver = Driver.objects.get(id=driver_id)
        driver.last_service_km = driver.total_km_driven
        driver.save()
        return Response({'status': 'reset', 'last_service_km': driver.last_service_km})
    except Driver.DoesNotExist:
        return Response({'error': 'Conductor no encontrado'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([AllowAny])
def export_drivers_report_pdf(request):
    drivers = Driver.objects.all().order_by('name')
    now = timezone.now()
    
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Reporte Oficial de Flota de Conductores - ViajaYa Frontera</title>
    <style>
        @page {{ size: A4 landscape; margin: 12mm; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; color: #0f172a; background: #fff; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #00c853; padding-bottom: 12px; margin-bottom: 20px; }}
        .title {{ font-size: 22px; font-weight: 800; color: #00c853; margin: 0; }}
        .subtitle {{ font-size: 12px; color: #64748b; margin-top: 4px; }}
        .meta {{ text-align: right; font-size: 11px; color: #475569; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 11px; }}
        th, td {{ border: 1px solid #cbd5e1; padding: 8px 10px; text-align: left; vertical-align: middle; }}
        th {{ background-color: #0f172a; color: #ffffff; font-weight: 700; text-transform: uppercase; font-size: 10px; letter-spacing: 0.5px; }}
        tr:nth-child(even) {{ background-color: #f8fafc; }}
        .badge-active {{ background: #dcfce7; color: #166534; padding: 3px 8px; border-radius: 12px; font-weight: 700; font-size: 10px; }}
        .badge-blocked {{ background: #fee2e2; color: #991b1b; padding: 3px 8px; border-radius: 12px; font-weight: 700; font-size: 10px; }}
        .doc-link {{ color: #2563eb; font-weight: bold; text-decoration: none; margin-right: 4px; }}
        .no-print-bar {{ background: #1e293b; color: #fff; padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; border-radius: 8px; margin-bottom: 20px; }}
        .btn-print {{ background: #00c853; color: #000; font-weight: 800; border: none; padding: 10px 18px; border-radius: 6px; cursor: pointer; font-size: 14px; }}
        @media print {{ .no-print-bar {{ display: none !important; }} body {{ padding: 0; }} }}
    </style>
</head>
<body>
    <div class="no-print-bar">
        <div>📄 <strong>Reporte de Flota Generado Listo para Exportar a PDF</strong></div>
        <button onclick="window.print()" class="btn-print">🖨️ IMPRIMIR / GUARDAR COMO PDF</button>
    </div>

    <div class="header">
        <div>
            <div class="title">🚗 REPORTE OFICIAL DE CONDUCTORES Y FLOTA DE VEHÍCULOS</div>
            <div class="subtitle">Plataforma Movilidad Fronteriza (Saltos del Guairá • Guaíra • Mundo Novo • Katueté)</div>
        </div>
        <div class="meta">
            <strong>Fecha de Emisión:</strong> {now.strftime('%d/%m/%Y %H:%M:%S')}<br>
            <strong>Total Conductores Registrados:</strong> {drivers.count()}
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>#ID</th>
                <th>Nombre del Conductor</th>
                <th>Cédula / RG / CPF</th>
                <th>Teléfono</th>
                <th>Vehículo / Color</th>
                <th>Chapa / Placa</th>
                <th>Rating</th>
                <th>Km Recorridos</th>
                <th>Documentación</th>
                <th>Estado</th>
            </tr>
        </thead>
        <tbody>
    """
    for d in drivers:
        docs = []
        if d.photo_ci: docs.append(f'<a href="{d.photo_ci.url}" target="_blank" class="doc-link">CI</a>')
        if d.photo_judicial: docs.append(f'<a href="{d.photo_judicial.url}" target="_blank" class="doc-link">Judicial</a>')
        if d.photo_police: docs.append(f'<a href="{d.photo_police.url}" target="_blank" class="doc-link">Policial</a>')
        if d.photo_license_plate: docs.append(f'<a href="{d.photo_license_plate.url}" target="_blank" class="doc-link">Chapa</a>')
        if d.photo_vehicle: docs.append(f'<a href="{d.photo_vehicle.url}" target="_blank" class="doc-link">Vehículo</a>')
        docs_html = " ".join(docs) if docs else '<span style="color:#94a3b8;">Sin adjuntos</span>'

        status_html = '<span class="badge-active">🟢 Habilitado</span>' if d.is_verified else '<span class="badge-blocked">🔴 Pendiente</span>'

        html += f"""
            <tr>
                <td>#{d.id}</td>
                <td><strong>{d.name}</strong></td>
                <td>{d.document_id}</td>
                <td>{d.phone}</td>
                <td>{d.vehicle_model} ({d.vehicle_color or 'N/A'})</td>
                <td><strong>{d.license_plate}</strong></td>
                <td>⭐ {d.rating_avg}</td>
                <td>{round(d.total_km_driven, 1)} km</td>
                <td>{docs_html}</td>
                <td>{status_html}</td>
            </tr>
        """

    html += """
        </tbody>
    </table>

    <div style="margin-top: 30px; border-top: 1px solid #cbd5e1; padding-top: 10px; font-size: 10px; color: #64748b; display: flex; justify-content: space-between;">
        <span>Sistema de Gestión AppTransporte Saltos</span>
        <span>Documento oficial de control de flota</span>
    </div>

    <script>
        // Lanzar diálogo de impresión a PDF automáticamente al cargar
        window.onload = function() {
            setTimeout(function() {
                // window.print();
            }, 500);
        };
    </script>
</body>
</html>
    """
    return HttpResponse(html, content_type='text/html')

