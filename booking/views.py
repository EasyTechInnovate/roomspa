import math
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from User.permissions import IsCustomer, IsTherapist
from rest_framework.permissions import IsAuthenticated
from therapist.models import Services as TherapistServices, TherapistAddress, TherapistStatus
from .models import Booking, FCMToken, PendingRequests, Coupon
from .serializers import FCMTokenSerializer, BookingRequestSerializer, BookingResponseSerializer, BookingSerializer, PendingRequestsSerializer, CouponValidationSerializer, ApplyCouponSerializer
from .firebase_utils import send_push_notification
from decimal import Decimal
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.shortcuts import get_object_or_404

User = get_user_model()

@api_view(['GET'])
@permission_classes([IsCustomer])
def search_therapists_view(request):
    lat = request.query_params.get('latitude')
    lon = request.query_params.get('longitude')
    services_param = request.query_params.get('services')
    radius = request.query_params.get('radius', '10') 
    
    if not lat or not lon:
        return Response({'error': 'Missing latitude or longitude'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user_lat = float(lat)
        user_lon = float(lon)
        search_radius = float(radius)
    except ValueError:
        return Response({'error': 'Invalid coordinates or radius'}, status=status.HTTP_400_BAD_REQUEST)
    
    service_list = []
    if services_param:
        service_list = [s.strip() for s in services_param.split(',') if s.strip()]
    
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371 
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
    
    addresses = TherapistAddress.objects.filter(
        user__therapist_status__status='available'
    )
    results = []
    
    for addr in addresses:
        if addr.latitude is None or addr.longitude is None:
            continue
        
        distance = haversine(user_lat, user_lon, float(addr.latitude), float(addr.longitude))
        
        if distance <= search_radius:
            therapist = addr.user
            status_obj = TherapistStatus.objects.filter(user=therapist).first()
            if not status_obj or status_obj.status != 'available':
                continue
            
            serv_obj = TherapistServices.objects.filter(user=therapist).first()
            
            if service_list and serv_obj:
                therapist_services = serv_obj.services or {}
                has_matching_service = any(service in therapist_services for service in service_list)
                if not has_matching_service:
                    continue
            
            data = {
                'id': therapist.id,
                'name': therapist.name, 
                'email': therapist.email,
                'address': {
                    'address':addr.address,
                    'coordinates':{
                        'latitude': addr.latitude,
                        'longitude': addr.longitude
                    }
                },
                'distance': round(distance, 2),
                'services': serv_obj.services if serv_obj else {},
            }
            results.append(data)
    
    results.sort(key=lambda x: x['distance'])
    return Response(results, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_fcm_token(request):
    serializer = FCMTokenSerializer(data=request.data)
    if serializer.is_valid():
        token, created = FCMToken.objects.get_or_create(
            user=request.user,
            defaults={'token': serializer.validated_data['token']}
        )
        if not created:
            token.token = serializer.validated_data['token']
            token.save()
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsCustomer])
def send_booking_request(request):
    serializer = BookingRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    try:
        therapist = User.objects.get(id=data['id'])
    except User.DoesNotExist:
        return Response({'error': 'Therapist not found'}, status=status.HTTP_404_NOT_FOUND)
    
    customer_id = str(request.user.id)
    therapist_id = str(therapist.id)
    services = str(data['services'])
    coupon_code = data.get('coupon_code', '').strip() or None
    timeslot_from = data['timeslot_from']
    timeslot_to = data['timeslot_to']
    latitude = data['latitude']
    longitude = data['longitude']
    distance = data['distance']

    already = PendingRequests.objects.filter(
        customer_id=customer_id,
        therapist_id=therapist_id,
        services=services,
        timeslot_from=timeslot_from,
        timeslot_to=timeslot_to,
        latitude=latitude,
        longitude=longitude,
        distance=distance,
        status='pending',
    ).first()

    if already:
        return Response(
            {
                'status': 'already_exists',
                'pending_booking_id': str(already.id),
                'message': 'A pending booking request with these exact details already exists.'
            },
            status=status.HTTP_200_OK
        )

    pending = PendingRequests.objects.create(
        customer_id=customer_id,
        therapist_id=therapist_id,
        status='pending',
        customer_name=getattr(request.user, 'name', None) or str(request.user),
        services=services,
        coupon_code=coupon_code,
        timeslot_from=timeslot_from,
        timeslot_to=timeslot_to,
        latitude=latitude,
        longitude=longitude,
        distance=distance
    )
    
    try:
        fcm_token = FCMToken.objects.get(user=therapist)
        customer_name = getattr(request.user, 'name', None) or str(request.user)
        send_push_notification(
            fcm_token.token,
            "New Booking Request",
            f"New request from {customer_name} for {services}",
            {"type": "booking_request", "request_id": str(pending.id)}
        )
    except FCMToken.DoesNotExist:
        pass
    
    return Response(
        {
            'status': 'sent',
            'pending_booking_id': str(pending.id)
        },
        status=status.HTTP_200_OK
    )

@api_view(['POST'])
@permission_classes([IsTherapist])
def respond_to_booking_request(request):
    serializer = BookingResponseSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    request_id = data['id']
    action = data['action']

    try:
        pending_request = PendingRequests.objects.get(
            id=request_id,
            therapist_id=request.user.id,
            status='pending'
        )
    except PendingRequests.DoesNotExist:
        return Response({
            'error': 'Request not found or already responded',
            'message': 'You have already responded to this booking request.'
        }, status=status.HTTP_409_CONFLICT)

    # Check if request has expired (older than 2 minutes)
    if pending_request.is_expired():
        pending_request.status = 'expired'
        pending_request.save()
        return Response({
            'error': 'Request has expired',
            'message': 'This booking request expired because it was not accepted within 2 minutes.'
        }, status=status.HTTP_410_GONE)
    
    try:
        customer = User.objects.get(id=pending_request.customer_id)
    except User.DoesNotExist:
        pending_request.status = 'rejected'
        pending_request.save()
        return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if action == 'reject':
        pending_request.status = 'rejected'
        pending_request.save()
        
        try:
            fcm_token = FCMToken.objects.get(user=customer)
            send_push_notification(
                fcm_token.token,
                "Booking Request Declined",
                "Your therapist is currently busy",
                {"type": "booking_rejected", "request_id": str(pending_request.id)}
            )
        except FCMToken.DoesNotExist:
            pass
        
        return Response({
            'accepted': False,
            'message': 'Therapist is currently busy.'
        }, status=status.HTTP_200_OK)
    
    elif action == 'accept':
        # Calculate actual total from therapist's service prices
        total_amount = Decimal('0.00')
        try:
            import ast
            from therapist.models import Services as TherapistServices

            therapist_services = TherapistServices.objects.filter(user=request.user).first()

            # Parse services string to dict
            if isinstance(pending_request.services, str):
                try:
                    requested_services = ast.literal_eval(pending_request.services)
                except:
                    requested_services = {}
            else:
                requested_services = pending_request.services or {}

            # Calculate total from therapist's pricing
            if therapist_services and therapist_services.services:
                for service_name, quantity in requested_services.items():
                    # Try to find price by exact match first
                    price_per_service = therapist_services.services.get(service_name, 0)

                    # If not found, try alternative formats
                    if price_per_service == 0:
                        # Convert spaces to underscores: "4 hands oil" -> "4_hands_oil"
                        alt_name = service_name.replace(' ', '_')
                        price_per_service = therapist_services.services.get(alt_name, 0)

                        # Try other common variations
                        if price_per_service == 0:
                            alt_name = service_name.replace('_', ' ')
                            price_per_service = therapist_services.services.get(alt_name, 0)

                    # Set default quantity to 1 if it's 0 (assuming they want the service)
                    actual_quantity = int(quantity) if quantity and int(quantity) > 0 else 1
                    total_amount += Decimal(str(price_per_service)) * Decimal(str(actual_quantity))
        except:
            total_amount = Decimal('0.00')

        # Handle coupon application
        coupon = None
        coupon_discount = Decimal('0.00')
        subtotal = total_amount

        if pending_request.coupon_code:
            try:
                coupon = Coupon.objects.get(code=pending_request.coupon_code.upper())
                if coupon.is_valid() and coupon.can_apply_to_amount(subtotal):
                    coupon_discount = coupon.calculate_discount(subtotal)
                    total_amount = subtotal - coupon_discount
                    # Increment usage count
                    coupon.used_count += 1
                    coupon.save()
            except Coupon.DoesNotExist:
                pass  # Invalid coupon, proceed without discount

        booking = Booking.objects.create(
            customer=customer,
            therapist=request.user,
            time_slot_from=pending_request.timeslot_from,
            time_slot_to=pending_request.timeslot_to,
            services=pending_request.services,
            subtotal=subtotal,
            coupon=coupon,
            coupon_discount=coupon_discount,
            total=total_amount,
            latitude=pending_request.latitude,
            longitude=pending_request.longitude,
            distance=pending_request.distance,
            status='active'
        )
        
        pending_request.status = 'accepted'
        pending_request.save()
        
        try:
            fcm_token = FCMToken.objects.get(user=customer)
            send_push_notification(
                fcm_token.token,
                "Booking Confirmed",
                "Your booking request has been accepted",
                {"type": "booking_accepted", "booking_id": str(booking.id)}
            )
        except FCMToken.DoesNotExist:
            pass
        
        return Response({
            'accepted': True,
            'message': 'Your booking has been placed.',
            'booking_id': booking.id
        }, status=status.HTTP_201_CREATED)
    
    else:
        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def list_bookings(request):
    therapist_id      = request.data.get('therapist')
    customer_id       = request.data.get('customer')
    status            = request.data.get('status')
    ts_from_raw       = request.data.get('time_slot_from')
    ts_to_raw         = request.data.get('time_slot_to')
    distance_max      = request.data.get('distance')

    qs = Booking.objects.all()

    if therapist_id:
        qs = qs.filter(therapist_id=therapist_id)
    if customer_id:
        qs = qs.filter(customer_id=customer_id)
    if status:
        qs = qs.filter(status=status)

    if ts_from_raw:
        dt_from = parse_datetime(ts_from_raw)
        if dt_from is None:
            return Response(
                {"error": "Invalid datetime format for time_slot_from"},
                status=400
            )
        if timezone.is_naive(dt_from):
            dt_from = timezone.make_aware(dt_from, timezone=timezone.get_current_timezone())
        qs = qs.filter(time_slot_from=dt_from)

    if ts_to_raw:
        dt_to = parse_datetime(ts_to_raw)
        if dt_to is None:
            return Response(
                {"error": "Invalid datetime format for time_slot_to"},
                status=400
            )
        if timezone.is_naive(dt_to):
            dt_to = timezone.make_aware(dt_to, timezone=timezone.get_current_timezone())
        qs = qs.filter(time_slot_to=dt_to)

    if distance_max:
        try:
            dist_val = float(distance_max)
        except (TypeError, ValueError):
            return Response({"error": "Invalid numeric value for distance"}, status=400)
        qs = qs.filter(distance__lte=dist_val)

    serializer = BookingSerializer(qs, many=True)
    return Response(serializer.data, status=200)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_booking_status(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    
    if request.user != booking.customer and request.user != booking.therapist:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    if booking.status == 'completed' or booking.status == 'cancelled':
        return Response({'error': f'Cannot update status of {booking.status} booking'}, status=status.HTTP_400_BAD_REQUEST)
    
    new_status = request.data.get('status')
    if not new_status:
        return Response({'error': 'Status field is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    valid_statuses = [choice[0] for choice in Booking.STATUS_CHOICES]
    if new_status not in valid_statuses:
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
    
    booking.status = new_status
    
    current_time = timezone.now()
    if new_status == 'started':
        booking.started_at = current_time
    elif new_status == 'completed':
        booking.completed_at = current_time
    elif new_status == 'cancelled':
        booking.cancelled_at = current_time
        booking.cancellation_reason = request.data.get('cancellation_reason', '')
    
    booking.save()
    
    return Response({
        'message': 'Booking status updated successfully',
        'booking_id': booking.id,
        'status': booking.status
    }, status=status.HTTP_200_OK)

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def pending_requests_list(request):
    if request.method == 'PATCH':
        req_id = request.data.get('id')
        pending = get_object_or_404(
            PendingRequests,
            id=req_id,
            therapist_id=request.user.id
        )
        if pending.status != 'pending':
            return Response(
                {'error': 'Only pending requests can be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        pending.status = 'cancelled'
        pending.save()
        serializer = PendingRequestsSerializer(pending)
        return Response(serializer.data, status=status.HTTP_200_OK)

    req_id = request.query_params.get('id')
    status_filter = request.query_params.get('status')

    if req_id:
        pending = get_object_or_404(PendingRequests, id=req_id)
        # Auto-expire if needed
        pending.auto_expire_if_needed()
        serializer = PendingRequestsSerializer(pending)
        return Response(serializer.data)

    # Automatically detect role from authenticated user
    user_role = getattr(request.user, 'role', 'therapist')

    # Filter by role: therapist or customer
    if user_role == 'customer':
        qs = PendingRequests.objects.filter(customer_id=str(request.user.id))
    else:
        qs = PendingRequests.objects.filter(therapist_id=str(request.user.id))

    # Auto-expire old pending requests
    from datetime import timedelta
    two_minutes_ago = timezone.now() - timedelta(minutes=2)
    old_pending = qs.filter(status='pending', created_at__lt=two_minutes_ago)
    old_pending.update(status='expired')

    # Apply status filter if provided
    if status_filter:
        qs = qs.filter(status=status_filter)

    serializer = PendingRequestsSerializer(qs, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def booking_detail_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.user != booking.customer and request.user != booking.therapist:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    serializer = BookingSerializer(booking)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsTherapist])
def therapist_analytics(request):
    from datetime import timedelta
    from django.db.models import Sum
    from decimal import Decimal

    therapist_id = request.query_params.get('therapist_id', str(request.user.id))

    # Ensure therapist can only see their own analytics
    if str(request.user.id) != str(therapist_id):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    now = timezone.now()

    # Date ranges
    last_7_days = now - timedelta(days=7)
    last_30_days = now - timedelta(days=30)
    last_365_days = now - timedelta(days=365)

    # Base queryset for completed bookings
    base_qs = Booking.objects.filter(
        therapist_id=therapist_id,
        status='completed'
    )

    # Analytics for different periods
    def get_period_analytics(start_date):
        period_bookings = base_qs.filter(completed_at__gte=start_date)
        total_revenue = period_bookings.aggregate(
            revenue=Sum('total')
        )['revenue'] or Decimal('0.00')
        total_orders = period_bookings.count()

        return {
            'total_revenue': float(total_revenue),
            'total_orders': total_orders,
            'average_order_value': float(total_revenue / total_orders) if total_orders > 0 else 0.0
        }

    # Weekly revenue breakdown (last 7 days)
    weekly_revenue = []
    for i in range(7):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        day_bookings = base_qs.filter(
            completed_at__gte=day_start,
            completed_at__lt=day_end
        )

        day_revenue = day_bookings.aggregate(revenue=Sum('total'))['revenue'] or Decimal('0.00')
        day_orders = day_bookings.count()

        weekly_revenue.append({
            'date': day_start.strftime('%Y-%m-%d'),
            'day_name': day_start.strftime('%A'),
            'revenue': float(day_revenue),
            'orders': day_orders
        })

    # Recent orders (last 10 completed bookings)
    recent_orders = base_qs.order_by('-completed_at')[:10]
    recent_orders_data = []

    for booking in recent_orders:
        recent_orders_data.append({
            'id': str(booking.id),
            'customer_name': getattr(booking.customer, 'name', None) or str(booking.customer),
            'services': booking.services,
            'total_amount': float(booking.total),
            'completed_at': booking.completed_at.isoformat() if booking.completed_at else None,
            'duration': str(booking.time_slot_to - booking.time_slot_from) if booking.time_slot_to and booking.time_slot_from else None
        })

    # Service popularity (from completed bookings)
    service_stats = {}
    for booking in base_qs.filter(completed_at__gte=last_30_days):
        if isinstance(booking.services, dict):
            services = booking.services
        elif isinstance(booking.services, str):
            try:
                import ast
                services = ast.literal_eval(booking.services)
            except:
                services = {}
        else:
            services = {}

        for service_name, quantity in services.items():
            if service_name not in service_stats:
                service_stats[service_name] = {'count': 0, 'revenue': 0.0}
            service_stats[service_name]['count'] += int(quantity) if quantity else 1

    # Convert service stats to list
    popular_services = []
    for service, stats in service_stats.items():
        popular_services.append({
            'service_name': service,
            'booking_count': stats['count']
        })
    popular_services = sorted(popular_services, key=lambda x: x['booking_count'], reverse=True)[:5]

    # Monthly trends (last 12 months)
    monthly_trends = []
    for i in range(12):
        month_start = (now.replace(day=1) - timedelta(days=32*i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = (month_start + timedelta(days=32)).replace(day=1)

        month_bookings = base_qs.filter(
            completed_at__gte=month_start,
            completed_at__lt=next_month
        )

        month_revenue = month_bookings.aggregate(revenue=Sum('total'))['revenue'] or Decimal('0.00')
        month_orders = month_bookings.count()

        monthly_trends.append({
            'month': month_start.strftime('%Y-%m'),
            'month_name': month_start.strftime('%B %Y'),
            'revenue': float(month_revenue),
            'orders': month_orders
        })

    # Reverse to show oldest to newest
    monthly_trends.reverse()

    return Response({
        'therapist_id': therapist_id,
        'generated_at': now.isoformat(),

        # Period analytics
        'last_7_days': get_period_analytics(last_7_days),
        'last_30_days': get_period_analytics(last_30_days),
        'last_365_days': get_period_analytics(last_365_days),

        # Weekly breakdown
        'weekly_revenue_breakdown': weekly_revenue,

        # Recent activity
        'recent_orders': recent_orders_data,

        # Service insights
        'popular_services': popular_services,

        # Trends
        'monthly_trends': monthly_trends,

        # Summary stats
        'total_lifetime_revenue': float(base_qs.aggregate(revenue=Sum('total'))['revenue'] or Decimal('0.00')),
        'total_lifetime_orders': base_qs.count(),
        'total_pending_requests': PendingRequests.objects.filter(
            therapist_id=therapist_id,
            status='pending'
        ).count()

    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_coupon(request):
    serializer = CouponValidationSerializer(data=request.data)
    if serializer.is_valid():
        coupon_code = serializer.validated_data['coupon_code']
        order_amount = serializer.validated_data['order_amount']

        try:
            coupon = Coupon.objects.get(code=coupon_code)

            if not coupon.is_valid():
                return Response({
                    'success': False,
                    'message': 'This coupon is not valid or has expired.'
                }, status=status.HTTP_400_BAD_REQUEST)

            if not coupon.can_apply_to_amount(order_amount):
                return Response({
                    'success': False,
                    'message': f'Minimum order amount is ₹{coupon.minimum_order_amount}'
                }, status=status.HTTP_400_BAD_REQUEST)

            discount_amount = coupon.calculate_discount(order_amount)
            final_total = order_amount - discount_amount

            return Response({
                'success': True,
                'coupon': {
                    'code': coupon.code,
                    'name': coupon.name,
                    'description': coupon.description,
                    'discount_type': coupon.discount_type,
                    'discount_value': coupon.discount_value
                },
                'original_amount': order_amount,
                'discount_amount': discount_amount,
                'final_total': final_total
            }, status=status.HTTP_200_OK)

        except Coupon.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid coupon code.'
            }, status=status.HTTP_400_BAD_REQUEST)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_coupon(request):
    serializer = ApplyCouponSerializer(data=request.data)
    if serializer.is_valid():
        coupon_code = serializer.validated_data['coupon_code']
        subtotal = serializer.validated_data['subtotal']

        try:
            coupon = Coupon.objects.get(code=coupon_code)

            if not coupon.is_valid():
                return Response({
                    'success': False,
                    'message': 'This coupon is not valid or has expired.'
                }, status=status.HTTP_400_BAD_REQUEST)

            if not coupon.can_apply_to_amount(subtotal):
                return Response({
                    'success': False,
                    'message': f'Minimum order amount is ₹{coupon.minimum_order_amount}'
                }, status=status.HTTP_400_BAD_REQUEST)

            discount_amount = coupon.calculate_discount(subtotal)
            final_total = subtotal - discount_amount

            response_data = serializer.data
            response_data.update({
                'discount_amount': discount_amount,
                'final_total': final_total,
                'success': True,
                'message': 'Coupon applied successfully'
            })

            return Response(response_data, status=status.HTTP_200_OK)

        except Coupon.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid coupon code.'
            }, status=status.HTTP_400_BAD_REQUEST)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)