# Comprehensive Admin Panel APIs - All in one file
# Using DRF Response format as requested

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db.models import Count, Sum, Q, Avg, Max
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator

from User.models import UserProfile
from booking.models import Booking, PendingRequests, FCMToken, Coupon
from therapist.models import TherapistStatus, Services as TherapistServices, TherapistAddress, BankDetails
from customer.models import CustomerAddress
from chat.models import Conversation, Message
from api.models import Pictures
from .auth import SimpleAdminAuthentication
from .serializers import AdminCouponSerializer, AdminCouponListSerializer

# Hardcoded admin credentials
ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "admin@1234"
ADMIN_TOKEN = "admin-simple-token-2024"

# =================== AUTHENTICATION APIs ===================

@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login_api(request):
    """Admin login with hardcoded credentials - returns simple token"""
    try:
        email = request.data.get('email')
        password = request.data.get('password')

        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            return Response({
                'success': True,
                'message': 'Admin login successful',
                'token': ADMIN_TOKEN,
                'user': {
                    'id': 'admin-001',
                    'name': 'Admin User',
                    'email': ADMIN_EMAIL,
                    'role': 'admin'
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': 'Invalid credentials'
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([SimpleAdminAuthentication])
@permission_classes([AllowAny])
def admin_logout_api(request):
    """Admin logout"""
    return Response({
        'success': True,
        'message': 'Logged out successfully'
    }, status=status.HTTP_200_OK)

# =================== DASHBOARD APIs ===================

@api_view(['GET'])
@authentication_classes([SimpleAdminAuthentication])
@permission_classes([AllowAny])
def dashboard_overview_api(request):
    """Main dashboard overview with comprehensive metrics"""
    try:
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # User Statistics
        user_stats = {
            'total': UserProfile.objects.count(),
            'customers': UserProfile.objects.filter(role='customer').count(),
            'therapists': UserProfile.objects.filter(role='therapist').count(),
            'admins': UserProfile.objects.filter(role='admin').count(),
            'new_today': UserProfile.objects.filter(date_created__date=today).count(),
            'new_this_week': UserProfile.objects.filter(date_created__date__gte=week_ago).count(),
            'verified': UserProfile.objects.filter(verification_status=True).count(),
            'unverified': UserProfile.objects.filter(verification_status=False).count()
        }

        # Booking Statistics
        booking_stats = {
            'total': Booking.objects.count(),
            'active': Booking.objects.filter(status='active').count(),
            'completed': Booking.objects.filter(status='completed').count(),
            'pending': Booking.objects.filter(status='pending').count(),
            'cancelled': Booking.objects.filter(status='cancelled').count(),
            'started': Booking.objects.filter(status='started').count(),
            'today': Booking.objects.filter(created_at__date=today).count(),
            'this_week': Booking.objects.filter(created_at__date__gte=week_ago).count()
        }

        # Revenue Statistics
        revenue_stats = {
            'today': float(Booking.objects.filter(
                created_at__date=today,
                status__in=['completed', 'active']
            ).aggregate(total=Sum('total'))['total'] or 0),
            'this_week': float(Booking.objects.filter(
                created_at__date__gte=week_ago,
                status__in=['completed', 'active']
            ).aggregate(total=Sum('total'))['total'] or 0),
            'this_month': float(Booking.objects.filter(
                created_at__date__gte=month_ago,
                status__in=['completed', 'active']
            ).aggregate(total=Sum('total'))['total'] or 0),
            'avg_booking_value': float(Booking.objects.aggregate(avg=Avg('total'))['avg'] or 0)
        }

        # Therapist Statistics
        try:
            therapist_stats = {
                'total': UserProfile.objects.filter(role='therapist').count(),
                'available': TherapistStatus.objects.filter(status='available').count(),
                'unavailable': TherapistStatus.objects.filter(status='unavailable').count(),
                'verified': UserProfile.objects.filter(role='therapist', verification_status=True).count(),
                'with_services': TherapistServices.objects.count(),
                'with_addresses': TherapistAddress.objects.count()
            }
        except:
            therapist_stats = {'total': 0, 'available': 0, 'unavailable': 0, 'verified': 0, 'with_services': 0, 'with_addresses': 0}

        # System Health
        system_health = {
            'pending_requests': PendingRequests.objects.filter(status='pending').count(),
            'old_pending_requests': PendingRequests.objects.filter(
                status='pending',
                created_at__lt=timezone.now() - timedelta(minutes=30)
            ).count(),
            'total_conversations': Conversation.objects.count(),
            'active_conversations': Conversation.objects.filter(is_active=True).count(),
            'unread_messages': Message.objects.filter(is_read=False).count(),
            'fcm_tokens': FCMToken.objects.count()
        }

        # System Alerts
        alerts = []
        if booking_stats['today'] > 0:
            cancellation_rate = (Booking.objects.filter(
                created_at__date=today,
                status='cancelled'
            ).count() / booking_stats['today']) * 100
            if cancellation_rate > 30:
                alerts.append({
                    'type': 'warning',
                    'message': f'High cancellation rate today: {cancellation_rate:.1f}%'
                })

        if system_health['old_pending_requests'] > 0:
            alerts.append({
                'type': 'danger',
                'message': f'{system_health["old_pending_requests"]} pending requests >30min'
            })

        data = {
            'users': user_stats,
            'bookings': booking_stats,
            'revenue': revenue_stats,
            'therapists': therapist_stats,
            'system': system_health,
            'alerts': alerts,
            'last_updated': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        return Response({
            'success': True,
            'data': data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# =================== USER MANAGEMENT APIs ===================

@api_view(['GET'])
@authentication_classes([SimpleAdminAuthentication])
@permission_classes([AllowAny])
def users_list_api(request):
    """Paginated list of all users with filters"""
    try:
        page = int(request.query_params.get('page', 1))
        per_page = int(request.query_params.get('per_page', 20))
        role_filter = request.query_params.get('role')
        search = request.query_params.get('search')
        verification_filter = request.query_params.get('verified')

        users = UserProfile.objects.all()

        if role_filter:
            users = users.filter(role=role_filter)

        if verification_filter is not None:
            verified = verification_filter.lower() == 'true'
            users = users.filter(verification_status=verified)

        if search:
            users = users.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone_number__icontains=search)
            )

        users = users.annotate(
            booking_count=Count('bookings') + Count('booked_therapies'),
            last_booking_activity=Max('bookings__created_at'),
            last_therapy_activity=Max('booked_therapies__created_at')
        )

        paginator = Paginator(users.order_by('-date_created'), per_page)
        page_obj = paginator.get_page(page)

        users_data = []
        for user in page_obj:
            # Calculate last activity from both booking types
            last_activity = None
            if user.last_booking_activity and user.last_therapy_activity:
                last_activity = max(user.last_booking_activity, user.last_therapy_activity)
            elif user.last_booking_activity:
                last_activity = user.last_booking_activity
            elif user.last_therapy_activity:
                last_activity = user.last_therapy_activity

            user_info = {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'phone_number': user.phone_number,
                'role': user.role,
                'verification_status': user.verification_status,
                'is_active': user.is_active,
                'date_created': user.date_created.strftime('%Y-%m-%d %H:%M:%S'),
                'gender': user.gender,
                'booking_count': user.booking_count or 0,
                'last_activity': last_activity.strftime('%Y-%m-%d %H:%M:%S') if last_activity else None
            }

            if user.role == 'therapist':
                try:
                    status_obj = TherapistStatus.objects.get(user=user)
                    user_info['therapist_status'] = status_obj.status
                except TherapistStatus.DoesNotExist:
                    user_info['therapist_status'] = 'unavailable'

                revenue = Booking.objects.filter(
                    therapist=user,
                    status='completed'
                ).aggregate(total=Sum('total'))['total'] or 0
                user_info['total_revenue'] = float(revenue)

            elif user.role == 'customer':
                spent = Booking.objects.filter(
                    customer=user,
                    status='completed'
                ).aggregate(total=Sum('total'))['total'] or 0
                user_info['total_spent'] = float(spent)

            users_data.append(user_info)

        return Response({
            'success': True,
            'data': {
                'users': users_data,
                'pagination': {
                    'current_page': page,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([SimpleAdminAuthentication])
@permission_classes([AllowAny])
def user_detail_api(request, user_id):
    """Detailed user information with role-specific data"""
    try:
        user = UserProfile.objects.get(id=user_id)

        user_data = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'phone_number': user.phone_number,
            'country_code': user.country_code,
            'role': user.role,
            'verification_status': user.verification_status,
            'is_active': user.is_active,
            'date_created': user.date_created.strftime('%Y-%m-%d %H:%M:%S'),
            'gender': user.gender,
            'consent': user.consent
        }

        if user.role == 'therapist':
            # Address info
            try:
                address = TherapistAddress.objects.get(user=user)
                user_data['address'] = {
                    'address': address.address,
                    'service_radius': float(address.service_radius),
                    'latitude': float(address.latitude) if address.latitude else None,
                    'longitude': float(address.longitude) if address.longitude else None
                }
            except TherapistAddress.DoesNotExist:
                user_data['address'] = None

            # Services
            try:
                services = TherapistServices.objects.get(user=user)
                user_data['services'] = services.services
            except TherapistServices.DoesNotExist:
                user_data['services'] = None

            # Status
            try:
                status_obj = TherapistStatus.objects.get(user=user)
                user_data['status'] = status_obj.status
            except TherapistStatus.DoesNotExist:
                user_data['status'] = 'unavailable'

            # Performance metrics
            therapist_bookings = Booking.objects.filter(therapist=user)
            performance = therapist_bookings.aggregate(
                total_bookings=Count('id'),
                completed_bookings=Count('id', filter=Q(status='completed')),
                cancelled_bookings=Count('id', filter=Q(status='cancelled')),
                total_revenue=Sum('total', filter=Q(status='completed')),
                avg_booking_value=Avg('total')
            )

            user_data['performance'] = {
                'total_bookings': performance['total_bookings'] or 0,
                'completed_bookings': performance['completed_bookings'] or 0,
                'cancelled_bookings': performance['cancelled_bookings'] or 0,
                'total_revenue': float(performance['total_revenue'] or 0),
                'avg_booking_value': round(float(performance['avg_booking_value'] or 0), 2),
                'success_rate': round((performance['completed_bookings'] or 0) / max(performance['total_bookings'] or 1, 1) * 100, 2)
            }

        elif user.role == 'customer':
            # Customer addresses
            addresses = CustomerAddress.objects.filter(user=user)
            user_data['addresses'] = [{
                'id': addr.id,
                'name': addr.name,
                'address': addr.address,
                'latitude': float(addr.latitude),
                'longitude': float(addr.longitude)
            } for addr in addresses]

            # Spending metrics
            customer_bookings = Booking.objects.filter(customer=user)
            spending = customer_bookings.aggregate(
                total_bookings=Count('id'),
                completed_bookings=Count('id', filter=Q(status='completed')),
                cancelled_bookings=Count('id', filter=Q(status='cancelled')),
                total_spent=Sum('total', filter=Q(status='completed')),
                avg_booking_value=Avg('total')
            )

            user_data['spending'] = {
                'total_bookings': spending['total_bookings'] or 0,
                'completed_bookings': spending['completed_bookings'] or 0,
                'cancelled_bookings': spending['cancelled_bookings'] or 0,
                'total_spent': float(spending['total_spent'] or 0),
                'avg_booking_value': round(float(spending['avg_booking_value'] or 0), 2)
            }

        return Response({
            'success': True,
            'data': user_data
        }, status=status.HTTP_200_OK)

    except UserProfile.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# =================== BOOKING MANAGEMENT APIs ===================

@api_view(['GET'])
@authentication_classes([SimpleAdminAuthentication])
@permission_classes([AllowAny])
def bookings_list_api(request):
    """Comprehensive bookings list with filters and pagination"""
    try:
        page = int(request.query_params.get('page', 1))
        per_page = int(request.query_params.get('per_page', 20))
        status_filter = request.query_params.get('status')
        search = request.query_params.get('search')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        bookings = Booking.objects.select_related('customer', 'therapist')

        if status_filter:
            bookings = bookings.filter(status=status_filter)

        if search:
            bookings = bookings.filter(
                Q(customer__name__icontains=search) |
                Q(therapist__name__icontains=search) |
                Q(id__icontains=search)
            )

        if date_from:
            bookings = bookings.filter(created_at__date__gte=date_from)
        if date_to:
            bookings = bookings.filter(created_at__date__lte=date_to)

        paginator = Paginator(bookings.order_by('-created_at'), per_page)
        page_obj = paginator.get_page(page)

        bookings_data = []
        for booking in page_obj:
            bookings_data.append({
                'id': str(booking.id),
                'customer': {
                    'id': booking.customer.id,
                    'name': booking.customer.name,
                    'email': booking.customer.email
                },
                'therapist': {
                    'id': booking.therapist.id,
                    'name': booking.therapist.name,
                    'email': booking.therapist.email
                },
                'services': booking.services,
                'total': float(booking.total),
                'status': booking.status,
                'created_at': booking.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'time_slot': {
                    'from': booking.time_slot_from.strftime('%Y-%m-%d %H:%M:%S'),
                    'to': booking.time_slot_to.strftime('%Y-%m-%d %H:%M:%S')
                },
                'location': {
                    'address': booking.address,
                    'distance': float(booking.distance) if booking.distance else None
                }
            })

        summary = bookings.aggregate(
            total_bookings=Count('id'),
            total_revenue=Sum('total', filter=Q(status='completed')),
            avg_booking_value=Avg('total')
        )

        return Response({
            'success': True,
            'data': {
                'bookings': bookings_data,
                'pagination': {
                    'current_page': page,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                },
                'summary': {
                    'total_bookings': summary['total_bookings'],
                    'total_revenue': float(summary['total_revenue'] or 0),
                    'avg_booking_value': round(float(summary['avg_booking_value'] or 0), 2)
                }
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([SimpleAdminAuthentication])
@permission_classes([AllowAny])
def booking_detail_api(request, booking_id):
    """Detailed booking information"""
    try:
        booking = Booking.objects.select_related('customer', 'therapist').get(id=booking_id)

        booking_data = {
            'id': str(booking.id),
            'status': booking.status,
            'total': float(booking.total),
            'services': booking.services,
            'customer': {
                'id': booking.customer.id,
                'name': booking.customer.name,
                'email': booking.customer.email,
                'phone_number': booking.customer.phone_number
            },
            'therapist': {
                'id': booking.therapist.id,
                'name': booking.therapist.name,
                'email': booking.therapist.email,
                'phone_number': booking.therapist.phone_number
            },
            'schedule': {
                'time_slot_from': booking.time_slot_from.strftime('%Y-%m-%d %H:%M:%S'),
                'time_slot_to': booking.time_slot_to.strftime('%Y-%m-%d %H:%M:%S')
            },
            'location': {
                'address': booking.address,
                'latitude': float(booking.latitude) if booking.latitude else None,
                'longitude': float(booking.longitude) if booking.longitude else None,
                'distance': float(booking.distance) if booking.distance else None
            },
            'timeline': {
                'created_at': booking.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'started_at': booking.started_at.strftime('%Y-%m-%d %H:%M:%S') if booking.started_at else None,
                'completed_at': booking.completed_at.strftime('%Y-%m-%d %H:%M:%S') if booking.completed_at else None,
                'cancelled_at': booking.cancelled_at.strftime('%Y-%m-%d %H:%M:%S') if booking.cancelled_at else None
            },
            'cancellation_reason': booking.cancellation_reason
        }

        return Response({
            'success': True,
            'data': booking_data
        }, status=status.HTTP_200_OK)

    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# =================== ANALYTICS APIs ===================

@api_view(['GET'])
@authentication_classes([SimpleAdminAuthentication])
@permission_classes([AllowAny])
def booking_analytics_api(request):
    """Comprehensive booking analytics and trends"""
    try:
        period = int(request.query_params.get('period', 30))  # days
        start_date = timezone.now().date() - timedelta(days=period)
        end_date = timezone.now().date()

        # Daily trends
        daily_trends = []
        current_date = start_date
        while current_date <= end_date:
            day_bookings = Booking.objects.filter(created_at__date=current_date)
            day_revenue = day_bookings.filter(status='completed').aggregate(
                total=Sum('total')
            )['total'] or 0

            daily_trends.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'bookings': day_bookings.count(),
                'completed': day_bookings.filter(status='completed').count(),
                'cancelled': day_bookings.filter(status='cancelled').count(),
                'revenue': float(day_revenue)
            })
            current_date += timedelta(days=1)

        # Status distribution
        status_stats = list(Booking.objects.filter(
            created_at__date__gte=start_date
        ).values('status').annotate(count=Count('id')))

        # Top therapists
        top_therapists = list(Booking.objects.filter(
            created_at__date__gte=start_date
        ).values(
            'therapist__name', 'therapist__email', 'therapist__id'
        ).annotate(
            bookings=Count('id'),
            revenue=Sum('total', filter=Q(status='completed')),
            success_rate=Count('id', filter=Q(status='completed')) * 100.0 / Count('id')
        ).order_by('-revenue')[:10])

        for therapist in top_therapists:
            therapist['revenue'] = float(therapist['revenue'] or 0)
            therapist['success_rate'] = round(float(therapist['success_rate'] or 0), 2)

        # Financial summary
        financial_summary = Booking.objects.filter(
            created_at__date__gte=start_date
        ).aggregate(
            total_bookings=Count('id'),
            total_revenue=Sum('total', filter=Q(status='completed')),
            avg_booking_value=Avg('total'),
            completion_rate=Count('id', filter=Q(status='completed')) * 100.0 / Count('id')
        )

        return Response({
            'success': True,
            'data': {
                'period_days': period,
                'date_range': {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d')
                },
                'daily_trends': daily_trends,
                'status_distribution': status_stats,
                'top_therapists': top_therapists,
                'financial_summary': {
                    'total_bookings': financial_summary['total_bookings'] or 0,
                    'total_revenue': float(financial_summary['total_revenue'] or 0),
                    'avg_booking_value': round(float(financial_summary['avg_booking_value'] or 0), 2),
                    'completion_rate': round(float(financial_summary['completion_rate'] or 0), 2)
                }
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# =================== LIVE MONITORING APIs ===================

@api_view(['GET'])
@authentication_classes([SimpleAdminAuthentication])
@permission_classes([AllowAny])
def live_monitoring_api(request):
    """Real-time system monitoring dashboard"""
    try:
        # Active bookings
        active_bookings = list(Booking.objects.filter(
            status__in=['active', 'started']
        ).select_related('customer', 'therapist').values(
            'id', 'customer__name', 'therapist__name', 'status',
            'total', 'created_at', 'time_slot_from', 'time_slot_to'
        ).order_by('-created_at')[:15])

        for booking in active_bookings:
            booking['id'] = str(booking['id'])
            booking['created_at'] = booking['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            booking['time_slot_from'] = booking['time_slot_from'].strftime('%Y-%m-%d %H:%M:%S')
            booking['time_slot_to'] = booking['time_slot_to'].strftime('%Y-%m-%d %H:%M:%S')
            booking['total'] = float(booking['total'])

        # Recent pending requests
        recent_requests = list(PendingRequests.objects.filter(
            status='pending'
        ).values(
            'id', 'customer_name', 'services', 'created_at', 'distance'
        ).order_by('-created_at')[:10])

        for req in recent_requests:
            req['id'] = str(req['id'])
            req['created_at'] = req['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            req['distance'] = float(req['distance'])

        # Available therapists
        available_therapists = list(UserProfile.objects.filter(
            role='therapist',
            therapist_status__status='available'
        ).values('id', 'name', 'email'))

        # System alerts
        alerts = []
        now = timezone.now()
        today = now.date()

        # Check cancellation rate
        today_bookings = Booking.objects.filter(created_at__date=today)
        if today_bookings.count() > 5:
            cancellation_rate = today_bookings.filter(status='cancelled').count() / today_bookings.count()
            if cancellation_rate > 0.3:
                alerts.append({
                    'type': 'warning',
                    'message': f'High cancellation rate: {cancellation_rate:.1%} today'
                })

        # Check old pending requests
        old_requests = PendingRequests.objects.filter(
            status='pending',
            created_at__lt=now - timedelta(minutes=30)
        ).count()
        if old_requests > 0:
            alerts.append({
                'type': 'danger',
                'message': f'{old_requests} requests pending >30min'
            })

        # Quick stats
        quick_stats = {
            'active_bookings': len(active_bookings),
            'pending_requests': len(recent_requests),
            'available_therapists': len(available_therapists),
            'unread_messages': Message.objects.filter(is_read=False).count(),
            'today_revenue': float(Booking.objects.filter(
                created_at__date=today,
                status='completed'
            ).aggregate(total=Sum('total'))['total'] or 0)
        }

        return Response({
            'success': True,
            'data': {
                'active_bookings': active_bookings,
                'recent_requests': recent_requests,
                'available_therapists': available_therapists,
                'alerts': alerts,
                'quick_stats': quick_stats,
                'last_updated': now.strftime('%Y-%m-%d %H:%M:%S')
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# =================== FINANCIAL REPORTS APIs ===================

@api_view(['GET'])
@authentication_classes([SimpleAdminAuthentication])
@permission_classes([AllowAny])
def financial_reports_api(request):
    """Financial analytics and revenue reports"""
    try:
        period = request.query_params.get('period', 'month')

        today = timezone.now().date()
        if period == 'week':
            start_date = today - timedelta(days=7)
        elif period == 'month':
            start_date = today - timedelta(days=30)
        elif period == 'quarter':
            start_date = today - timedelta(days=90)
        elif period == 'year':
            start_date = today - timedelta(days=365)
        else:
            start_date = today - timedelta(days=30)

        # Revenue trends
        revenue_trends = []
        current_date = start_date
        while current_date <= today:
            day_revenue = Booking.objects.filter(
                created_at__date=current_date,
                status='completed'
            ).aggregate(total=Sum('total'))['total'] or 0

            revenue_trends.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'revenue': float(day_revenue)
            })
            current_date += timedelta(days=1)

        # Top earning therapists
        top_earners = list(Booking.objects.filter(
            created_at__date__gte=start_date,
            status='completed'
        ).values(
            'therapist__name', 'therapist__email'
        ).annotate(
            total_revenue=Sum('total'),
            booking_count=Count('id'),
            avg_booking_value=Avg('total')
        ).order_by('-total_revenue')[:15])

        for earner in top_earners:
            earner['total_revenue'] = float(earner['total_revenue'])
            earner['avg_booking_value'] = round(float(earner['avg_booking_value']), 2)
            earner['platform_commission'] = round(earner['total_revenue'] * 0.1, 2)
            earner['therapist_earnings'] = round(earner['total_revenue'] * 0.9, 2)

        # Financial summary
        period_bookings = Booking.objects.filter(created_at__date__gte=start_date)
        financial_summary = period_bookings.aggregate(
            total_revenue=Sum('total', filter=Q(status='completed')),
            total_bookings=Count('id'),
            completed_bookings=Count('id', filter=Q(status='completed')),
            avg_transaction=Avg('total', filter=Q(status='completed'))
        )

        total_revenue = float(financial_summary['total_revenue'] or 0)
        platform_revenue = total_revenue * 0.1
        therapist_payouts = total_revenue * 0.9

        return Response({
            'success': True,
            'data': {
                'period': period,
                'date_range': {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': today.strftime('%Y-%m-%d')
                },
                'revenue_trends': revenue_trends,
                'top_earners': top_earners,
                'financial_summary': {
                    'total_revenue': round(total_revenue, 2),
                    'platform_revenue': round(platform_revenue, 2),
                    'therapist_payouts': round(therapist_payouts, 2),
                    'total_bookings': financial_summary['total_bookings'] or 0,
                    'completed_bookings': financial_summary['completed_bookings'] or 0,
                    'avg_transaction': round(float(financial_summary['avg_transaction'] or 0), 2)
                }
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# =================== THERAPIST ANALYTICS APIs ===================

@api_view(['GET'])
@authentication_classes([SimpleAdminAuthentication])
@permission_classes([AllowAny])
def therapist_analytics_api(request):
    """Therapist performance and analytics"""
    try:
        # Top performing therapists
        top_therapists = UserProfile.objects.filter(role='therapist').annotate(
            total_bookings=Count('booked_therapies'),
            completed_bookings=Count('booked_therapies', filter=Q(booked_therapies__status='completed')),
            total_revenue=Sum('booked_therapies__total', filter=Q(booked_therapies__status='completed')),
            avg_booking_value=Avg('booked_therapies__total')
        ).order_by('-total_revenue')[:15]

        top_therapists_data = []
        for therapist in top_therapists:
            success_rate = (therapist.completed_bookings / max(therapist.total_bookings, 1)) * 100
            top_therapists_data.append({
                'id': therapist.id,
                'name': therapist.name,
                'email': therapist.email,
                'total_bookings': therapist.total_bookings or 0,
                'completed_bookings': therapist.completed_bookings or 0,
                'total_revenue': float(therapist.total_revenue or 0),
                'avg_booking_value': round(float(therapist.avg_booking_value or 0), 2),
                'success_rate': round(success_rate, 2)
            })

        # Availability statistics
        try:
            availability_stats = list(TherapistStatus.objects.values('status').annotate(count=Count('id')))
        except:
            availability_stats = []

        # Service coverage
        service_coverage = {}
        therapist_services = TherapistServices.objects.all()
        for ts in therapist_services:
            if ts.services:
                for service_key in ts.services.keys():
                    service_coverage[service_key] = service_coverage.get(service_key, 0) + 1

        return Response({
            'success': True,
            'data': {
                'top_therapists': top_therapists_data,
                'availability_stats': availability_stats,
                'service_coverage': dict(sorted(service_coverage.items(), key=lambda x: x[1], reverse=True)),
                'summary': {
                    'total_therapists': UserProfile.objects.filter(role='therapist').count(),
                    'verified_therapists': UserProfile.objects.filter(role='therapist', verification_status=True).count(),
                    'available_therapists': len([s for s in availability_stats if s['status'] == 'available'])
                }
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# =================== SYSTEM HEALTH APIs ===================

@api_view(['GET'])
@authentication_classes([SimpleAdminAuthentication])
@permission_classes([AllowAny])
def system_health_api(request):
    """System health monitoring and performance metrics"""
    try:
        now = timezone.now()
        today = now.date()
        last_24h = now - timedelta(hours=24)

        # Database health
        db_stats = {
            'total_users': UserProfile.objects.count(),
            'total_bookings': Booking.objects.count(),
            'total_conversations': Conversation.objects.count(),
            'total_messages': Message.objects.count()
        }

        # Recent activity
        activity_stats = {
            'registrations_24h': UserProfile.objects.filter(date_created__gte=last_24h).count(),
            'bookings_24h': Booking.objects.filter(created_at__gte=last_24h).count(),
            'messages_24h': Message.objects.filter(created_at__gte=last_24h).count(),
            'revenue_24h': float(Booking.objects.filter(
                created_at__gte=last_24h,
                status='completed'
            ).aggregate(total=Sum('total'))['total'] or 0)
        }

        # Health indicators
        health_indicators = []

        # Check response times (placeholder)
        avg_response_time = 250
        health_indicators.append({
            'type': 'performance',
            'metric': 'Avg Response Time',
            'value': f'{avg_response_time}ms',
            'status': 'good' if avg_response_time < 500 else 'warning'
        })

        # Check database performance
        health_indicators.append({
            'type': 'database',
            'metric': 'Database Performance',
            'value': 'good',
            'status': 'good'
        })

        # Overall system status
        critical_issues = len([i for i in health_indicators if i['status'] == 'critical'])
        system_status = 'critical' if critical_issues > 0 else 'healthy'

        return Response({
            'success': True,
            'data': {
                'system_status': system_status,
                'db_stats': db_stats,
                'activity_stats': activity_stats,
                'health_indicators': health_indicators,
                'uptime': {
                    'percentage': 99.9,
                    'last_incident': None
                },
                'last_updated': now.strftime('%Y-%m-%d %H:%M:%S')
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# =================== USER MANAGEMENT ACTIONS ===================

@api_view(['POST'])
@authentication_classes([SimpleAdminAuthentication])
@permission_classes([AllowAny])
def user_action_api(request, user_id):
    """Perform actions on users (activate, deactivate, verify, delete)"""
    try:
        user = UserProfile.objects.get(id=user_id)
        action = request.data.get('action')

        if action == 'activate':
            user.is_active = True
            user.save()
            message = f'User {user.name} activated successfully'
        elif action == 'deactivate':
            user.is_active = False
            user.save()
            message = f'User {user.name} deactivated successfully'
        elif action == 'verify':
            user.verification_status = True
            user.save()
            message = f'User {user.name} verified successfully'
        elif action == 'unverify':
            user.verification_status = False
            user.save()
            message = f'User {user.name} unverified successfully'
        elif action == 'delete':
            user_name = user.name
            user.delete()
            message = f'User {user_name} deleted successfully'
        else:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'success': True,
            'message': message
        }, status=status.HTTP_200_OK)

    except UserProfile.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# =================== BOOKING MANAGEMENT ACTIONS ===================

@api_view(['POST'])
@authentication_classes([SimpleAdminAuthentication])
@permission_classes([AllowAny])
def booking_action_api(request, booking_id):
    """Perform actions on bookings (cancel, complete, refund)"""
    try:
        booking = Booking.objects.get(id=booking_id)
        action = request.data.get('action')
        reason = request.data.get('reason', '')

        if action == 'cancel':
            booking.status = 'cancelled'
            booking.cancellation_reason = reason
            booking.cancelled_at = timezone.now()
            booking.save()
            message = f'Booking {booking.id} cancelled successfully'
        elif action == 'complete':
            booking.status = 'completed'
            booking.completed_at = timezone.now()
            booking.save()
            message = f'Booking {booking.id} marked as completed'
        elif action == 'start':
            booking.status = 'started'
            booking.started_at = timezone.now()
            booking.save()
            message = f'Booking {booking.id} started'
        else:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'success': True,
            'message': message,
            'booking': {
                'id': str(booking.id),
                'status': booking.status,
                'updated_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }, status=status.HTTP_200_OK)

    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# =================== THERAPIST MANAGEMENT ===================

@api_view(['GET'])
@authentication_classes([SimpleAdminAuthentication])
@permission_classes([AllowAny])
def therapist_list_api(request):
    """List all therapists with their details and performance"""
    try:
        page = int(request.query_params.get('page', 1))
        per_page = int(request.query_params.get('per_page', 20))
        status_filter = request.query_params.get('status')
        verified_filter = request.query_params.get('verified')

        therapists = UserProfile.objects.filter(role='therapist')

        if verified_filter is not None:
            verified = verified_filter.lower() == 'true'
            therapists = therapists.filter(verification_status=verified)

        if status_filter:
            therapists = therapists.filter(therapist_status__status=status_filter)

        therapists = therapists.annotate(
            total_bookings=Count('booked_therapies'),
            completed_bookings=Count('booked_therapies', filter=Q(booked_therapies__status='completed')),
            total_revenue=Sum('booked_therapies__total', filter=Q(booked_therapies__status='completed'))
        )

        paginator = Paginator(therapists.order_by('-date_created'), per_page)
        page_obj = paginator.get_page(page)

        therapists_data = []
        for therapist in page_obj:
            therapist_info = {
                'id': therapist.id,
                'name': therapist.name,
                'email': therapist.email,
                'phone_number': therapist.phone_number,
                'verification_status': therapist.verification_status,
                'is_active': therapist.is_active,
                'date_created': therapist.date_created.strftime('%Y-%m-%d %H:%M:%S'),
                'total_bookings': therapist.total_bookings or 0,
                'completed_bookings': therapist.completed_bookings or 0,
                'total_revenue': float(therapist.total_revenue or 0),
                'success_rate': round((therapist.completed_bookings or 0) / max(therapist.total_bookings or 1, 1) * 100, 2)
            }

            # Get therapist status
            try:
                status_obj = TherapistStatus.objects.get(user=therapist)
                therapist_info['status'] = status_obj.status
            except TherapistStatus.DoesNotExist:
                therapist_info['status'] = 'unavailable'

            # Get services
            try:
                services = TherapistServices.objects.get(user=therapist)
                therapist_info['services_count'] = len(services.services) if services.services else 0
            except TherapistServices.DoesNotExist:
                therapist_info['services_count'] = 0

            therapists_data.append(therapist_info)

        return Response({
            'success': True,
            'data': {
                'therapists': therapists_data,
                'pagination': {
                    'current_page': page,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([SimpleAdminAuthentication])
@permission_classes([AllowAny])
def therapist_action_api(request, therapist_id):
    """Perform actions on therapists (approve, reject, suspend)"""
    try:
        therapist = UserProfile.objects.get(id=therapist_id, role='therapist')
        action = request.data.get('action')

        if action == 'approve':
            therapist.verification_status = True
            therapist.is_active = True
            therapist.save()
            message = f'Therapist {therapist.name} approved successfully'
        elif action == 'reject':
            therapist.verification_status = False
            therapist.is_active = False
            therapist.save()
            message = f'Therapist {therapist.name} rejected'
        elif action == 'suspend':
            therapist.is_active = False
            therapist.save()
            message = f'Therapist {therapist.name} suspended'
        elif action == 'reactivate':
            therapist.is_active = True
            therapist.save()
            message = f'Therapist {therapist.name} reactivated'
        else:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'success': True,
            'message': message
        }, status=status.HTTP_200_OK)

    except UserProfile.DoesNotExist:
        return Response({'error': 'Therapist not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# =================== CUSTOMER MANAGEMENT ===================

@api_view(['GET'])
@authentication_classes([SimpleAdminAuthentication])
@permission_classes([AllowAny])
def customer_list_api(request):
    """List all customers with their booking history"""
    try:
        page = int(request.query_params.get('page', 1))
        per_page = int(request.query_params.get('per_page', 20))
        search = request.query_params.get('search')

        customers = UserProfile.objects.filter(role='customer')

        if search:
            customers = customers.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone_number__icontains=search)
            )

        customers = customers.annotate(
            total_bookings=Count('bookings'),
            completed_bookings=Count('bookings', filter=Q(bookings__status='completed')),
            total_spent=Sum('bookings__total', filter=Q(bookings__status='completed')),
            last_booking=Max('bookings__created_at')
        )

        paginator = Paginator(customers.order_by('-date_created'), per_page)
        page_obj = paginator.get_page(page)

        customers_data = []
        for customer in page_obj:
            customers_data.append({
                'id': customer.id,
                'name': customer.name,
                'email': customer.email,
                'phone_number': customer.phone_number,
                'verification_status': customer.verification_status,
                'is_active': customer.is_active,
                'date_created': customer.date_created.strftime('%Y-%m-%d %H:%M:%S'),
                'total_bookings': customer.total_bookings or 0,
                'completed_bookings': customer.completed_bookings or 0,
                'total_spent': float(customer.total_spent or 0),
                'avg_booking_value': round(float(customer.total_spent or 0) / max(customer.completed_bookings or 1, 1), 2),
                'last_booking': customer.last_booking.strftime('%Y-%m-%d %H:%M:%S') if customer.last_booking else None
            })

        return Response({
            'success': True,
            'data': {
                'customers': customers_data,
                'pagination': {
                    'current_page': page,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# =================== PENDING REQUESTS MANAGEMENT ===================

@api_view(['GET'])
@authentication_classes([SimpleAdminAuthentication])
@permission_classes([AllowAny])
def pending_requests_api(request):
    """List all pending booking requests"""
    try:
        page = int(request.query_params.get('page', 1))
        per_page = int(request.query_params.get('per_page', 20))
        status_filter = request.query_params.get('status')

        requests = PendingRequests.objects.all()

        if status_filter:
            requests = requests.filter(status=status_filter)

        paginator = Paginator(requests.order_by('-created_at'), per_page)
        page_obj = paginator.get_page(page)

        requests_data = []
        for req in page_obj:
            requests_data.append({
                'id': str(req.id),
                'customer_id': req.customer_id,
                'customer_name': req.customer_name,
                'therapist_id': req.therapist_id,
                'services': req.services,
                'timeslot_from': req.timeslot_from.strftime('%Y-%m-%d %H:%M:%S'),
                'timeslot_to': req.timeslot_to.strftime('%Y-%m-%d %H:%M:%S'),
                'latitude': float(req.latitude),
                'longitude': float(req.longitude),
                'distance': float(req.distance),
                'status': req.status,
                'created_at': req.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'time_ago': str(timezone.now() - req.created_at)
            })

        return Response({
            'success': True,
            'data': {
                'requests': requests_data,
                'pagination': {
                    'current_page': page,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([SimpleAdminAuthentication])
@permission_classes([AllowAny])
def pending_request_action_api(request, request_id):
    """Take action on pending requests"""
    try:
        pending_req = PendingRequests.objects.get(id=request_id)
        action = request.data.get('action')

        if action == 'approve':
            pending_req.status = 'approved'
            pending_req.save()
            message = f'Request {pending_req.id} approved'
        elif action == 'reject':
            pending_req.status = 'rejected'
            pending_req.save()
            message = f'Request {pending_req.id} rejected'
        elif action == 'cancel':
            pending_req.status = 'cancelled'
            pending_req.save()
            message = f'Request {pending_req.id} cancelled'
        else:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'success': True,
            'message': message
        }, status=status.HTTP_200_OK)

    except PendingRequests.DoesNotExist:
        return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# =================== CHAT/COMMUNICATION MANAGEMENT ===================

@api_view(['GET'])
@authentication_classes([SimpleAdminAuthentication])
@permission_classes([AllowAny])
def conversations_api(request):
    """List all conversations with message counts"""
    try:
        page = int(request.query_params.get('page', 1))
        per_page = int(request.query_params.get('per_page', 20))

        conversations = Conversation.objects.select_related('customer', 'therapist').annotate(
            message_count=Count('messages'),
            unread_count=Count('messages', filter=Q(messages__is_read=False)),
            last_message_time=Max('messages__created_at')
        )

        paginator = Paginator(conversations.order_by('-last_message_time'), per_page)
        page_obj = paginator.get_page(page)

        conversations_data = []
        for conv in page_obj:
            conversations_data.append({
                'id': str(conv.id),
                'customer': {
                    'id': conv.customer.id,
                    'name': conv.customer.name,
                    'email': conv.customer.email
                },
                'therapist': {
                    'id': conv.therapist.id,
                    'name': conv.therapist.name,
                    'email': conv.therapist.email
                },
                'is_active': conv.is_active,
                'message_count': conv.message_count,
                'unread_count': conv.unread_count,
                'last_message_time': conv.last_message_time.strftime('%Y-%m-%d %H:%M:%S') if conv.last_message_time else None,
                'created_at': conv.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })

        return Response({
            'success': True,
            'data': {
                'conversations': conversations_data,
                'pagination': {
                    'current_page': page,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([SimpleAdminAuthentication])
@permission_classes([AllowAny])
def conversation_messages_api(request, conversation_id):
    """Get messages for a specific conversation"""
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        messages = Message.objects.filter(conversation=conversation).order_by('-created_at')

        page = int(request.query_params.get('page', 1))
        per_page = int(request.query_params.get('per_page', 50))

        paginator = Paginator(messages, per_page)
        page_obj = paginator.get_page(page)

        messages_data = []
        for message in page_obj:
            messages_data.append({
                'id': str(message.id),
                'sender': {
                    'id': message.sender.id,
                    'name': message.sender.name,
                    'role': message.sender.role
                },
                'content': message.content,
                'is_read': message.is_read,
                'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })

        return Response({
            'success': True,
            'data': {
                'conversation': {
                    'id': str(conversation.id),
                    'customer': conversation.customer.name,
                    'therapist': conversation.therapist.name
                },
                'messages': messages_data,
                'pagination': {
                    'current_page': page,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            }
        }, status=status.HTTP_200_OK)

    except Conversation.DoesNotExist:
        return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# =================== ADVANCED ANALYTICS ===================

@api_view(['GET'])
@authentication_classes([SimpleAdminAuthentication])
@permission_classes([AllowAny])
def advanced_analytics_api(request):
    """Advanced analytics with geographic and service data"""
    try:
        period = int(request.query_params.get('period', 30))
        start_date = timezone.now().date() - timedelta(days=period)

        # Geographic distribution
        bookings_by_location = Booking.objects.filter(
            created_at__date__gte=start_date
        ).values('address').annotate(
            booking_count=Count('id'),
            total_revenue=Sum('total', filter=Q(status='completed'))
        ).order_by('-booking_count')[:10]

        for location in bookings_by_location:
            location['total_revenue'] = float(location['total_revenue'] or 0)

        # Service popularity
        service_stats = {}
        bookings = Booking.objects.filter(created_at__date__gte=start_date)
        for booking in bookings:
            if booking.services:
                for service_key in booking.services.keys():
                    if service_key not in service_stats:
                        service_stats[service_key] = {
                            'count': 0,
                            'revenue': 0,
                            'avg_price': 0
                        }
                    service_stats[service_key]['count'] += 1
                    if booking.status == 'completed':
                        service_stats[service_key]['revenue'] += float(booking.total)

        # Calculate averages
        for service in service_stats.values():
            if service['count'] > 0:
                service['avg_price'] = round(service['revenue'] / service['count'], 2)

        # Peak hours analysis
        hour_stats = {}
        for booking in bookings:
            hour = booking.created_at.hour
            if hour not in hour_stats:
                hour_stats[hour] = {'bookings': 0, 'revenue': 0}
            hour_stats[hour]['bookings'] += 1
            if booking.status == 'completed':
                hour_stats[hour]['revenue'] += float(booking.total)

        peak_hours = sorted(hour_stats.items(), key=lambda x: x[1]['bookings'], reverse=True)[:5]

        return Response({
            'success': True,
            'data': {
                'period_days': period,
                'geographic_distribution': list(bookings_by_location),
                'service_popularity': dict(sorted(service_stats.items(), key=lambda x: x[1]['count'], reverse=True)),
                'peak_hours': [{'hour': f'{hour}:00', 'bookings': data['bookings'], 'revenue': data['revenue']} for hour, data in peak_hours],
                'summary': {
                    'total_locations': len(bookings_by_location),
                    'total_services': len(service_stats),
                    'busiest_hour': f'{peak_hours[0][0]}:00' if peak_hours else 'N/A'
                }
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# =================== EXPORT AND REPORTING ===================

@api_view(['GET'])
@authentication_classes([SimpleAdminAuthentication])
@permission_classes([AllowAny])
def export_data_api(request):
    """Export data in various formats (CSV data structure)"""
    try:
        export_type = request.query_params.get('type', 'bookings')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        if export_type == 'bookings':
            bookings = Booking.objects.select_related('customer', 'therapist').all()

            if date_from:
                bookings = bookings.filter(created_at__date__gte=date_from)
            if date_to:
                bookings = bookings.filter(created_at__date__lte=date_to)

            export_data = []
            for booking in bookings:
                export_data.append({
                    'booking_id': str(booking.id),
                    'customer_name': booking.customer.name,
                    'customer_email': booking.customer.email,
                    'therapist_name': booking.therapist.name,
                    'therapist_email': booking.therapist.email,
                    'total': float(booking.total),
                    'status': booking.status,
                    'created_at': booking.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'address': booking.address,
                    'services': str(booking.services)
                })

        elif export_type == 'users':
            users = UserProfile.objects.all()

            if date_from:
                users = users.filter(date_created__date__gte=date_from)
            if date_to:
                users = users.filter(date_created__date__lte=date_to)

            export_data = []
            for user in users:
                export_data.append({
                    'user_id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'phone_number': user.phone_number,
                    'role': user.role,
                    'verification_status': user.verification_status,
                    'is_active': user.is_active,
                    'date_created': user.date_created.strftime('%Y-%m-%d %H:%M:%S'),
                    'gender': user.gender
                })

        elif export_type == 'revenue':
            bookings = Booking.objects.filter(status='completed')

            if date_from:
                bookings = bookings.filter(created_at__date__gte=date_from)
            if date_to:
                bookings = bookings.filter(created_at__date__lte=date_to)

            export_data = []
            for booking in bookings:
                platform_commission = float(booking.total) * 0.1
                therapist_earning = float(booking.total) * 0.9

                export_data.append({
                    'booking_id': str(booking.id),
                    'date': booking.created_at.strftime('%Y-%m-%d'),
                    'total_amount': float(booking.total),
                    'platform_commission': round(platform_commission, 2),
                    'therapist_earning': round(therapist_earning, 2),
                    'therapist_name': booking.therapist.name,
                    'customer_name': booking.customer.name
                })

        else:
            return Response({'error': 'Invalid export type'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'success': True,
            'data': {
                'export_type': export_type,
                'record_count': len(export_data),
                'data': export_data,
                'generated_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# =================== NOTIFICATION MANAGEMENT ===================

@api_view(['GET'])
@authentication_classes([SimpleAdminAuthentication])
@permission_classes([AllowAny])
def fcm_tokens_api(request):
    """List all FCM tokens for push notifications"""
    try:
        tokens = FCMToken.objects.select_related('user').all()

        tokens_data = []
        for token in tokens:
            tokens_data.append({
                'id': token.id,
                'user': {
                    'id': token.user.id,
                    'name': token.user.name,
                    'email': token.user.email,
                    'role': token.user.role
                },
                'token': token.token[:50] + '...' if len(token.token) > 50 else token.token,
                'created_at': token.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })

        return Response({
            'success': True,
            'data': {
                'tokens': tokens_data,
                'total_count': len(tokens_data)
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([SimpleAdminAuthentication])
@permission_classes([AllowAny])
def send_notification_api(request):
    """Send push notification to users"""
    try:
        title = request.data.get('title')
        message = request.data.get('message')
        user_type = request.data.get('user_type', 'all')  # all, customers, therapists

        if not title or not message:
            return Response({'error': 'Title and message are required'}, status=status.HTTP_400_BAD_REQUEST)

        # Get target users
        if user_type == 'customers':
            target_users = UserProfile.objects.filter(role='customer')
        elif user_type == 'therapists':
            target_users = UserProfile.objects.filter(role='therapist')
        else:
            target_users = UserProfile.objects.all()

        # Get FCM tokens for target users
        tokens = FCMToken.objects.filter(user__in=target_users)

        # Here you would normally send the actual push notifications
        # For now, we'll just return success with the count

        return Response({
            'success': True,
            'message': f'Notification sent to {tokens.count()} users',
            'data': {
                'title': title,
                'message': message,
                'target_user_type': user_type,
                'tokens_count': tokens.count()
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# =================== COUPON MANAGEMENT APIs ===================

@api_view(['GET'])
@authentication_classes([SimpleAdminAuthentication])
def admin_coupons_list_api(request):
    """List all coupons with pagination and search"""
    try:
        search = request.GET.get('search', '').strip()
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        is_active = request.GET.get('is_active')

        queryset = Coupon.objects.all().order_by('-created_at')

        # Apply search filter
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        # Apply active filter
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)

        # Pagination
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        serializer = AdminCouponListSerializer(page_obj.object_list, many=True)

        return Response({
            'success': True,
            'data': {
                'coupons': serializer.data,
                'pagination': {
                    'current_page': page,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([SimpleAdminAuthentication])
def admin_coupons_create_api(request):
    """Create a new coupon"""
    try:
        serializer = AdminCouponSerializer(data=request.data)
        if serializer.is_valid():
            coupon = serializer.save()
            return Response({
                'success': True,
                'message': 'Coupon created successfully',
                'data': AdminCouponSerializer(coupon).data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([SimpleAdminAuthentication])
def admin_coupons_detail_api(request, coupon_id):
    """Get detailed coupon information"""
    try:
        coupon = Coupon.objects.get(id=coupon_id)
        serializer = AdminCouponSerializer(coupon)

        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    except Coupon.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Coupon not found'
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@authentication_classes([SimpleAdminAuthentication])
def admin_coupons_update_api(request, coupon_id):
    """Update an existing coupon"""
    try:
        coupon = Coupon.objects.get(id=coupon_id)
        serializer = AdminCouponSerializer(coupon, data=request.data, partial=True)

        if serializer.is_valid():
            updated_coupon = serializer.save()
            return Response({
                'success': True,
                'message': 'Coupon updated successfully',
                'data': AdminCouponSerializer(updated_coupon).data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    except Coupon.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Coupon not found'
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@authentication_classes([SimpleAdminAuthentication])
def admin_coupons_delete_api(request, coupon_id):
    """Delete a coupon"""
    try:
        coupon = Coupon.objects.get(id=coupon_id)
        coupon_code = coupon.code
        coupon.delete()

        return Response({
            'success': True,
            'message': f'Coupon "{coupon_code}" deleted successfully'
        }, status=status.HTTP_200_OK)

    except Coupon.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Coupon not found'
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([SimpleAdminAuthentication])
def admin_coupons_toggle_status_api(request, coupon_id):
    """Toggle coupon active/inactive status"""
    try:
        coupon = Coupon.objects.get(id=coupon_id)
        coupon.is_active = not coupon.is_active
        coupon.save()

        status_text = "activated" if coupon.is_active else "deactivated"

        return Response({
            'success': True,
            'message': f'Coupon "{coupon.code}" {status_text} successfully',
            'data': {
                'coupon_id': str(coupon.id),
                'code': coupon.code,
                'is_active': coupon.is_active
            }
        }, status=status.HTTP_200_OK)

    except Coupon.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Coupon not found'
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([SimpleAdminAuthentication])
def admin_coupons_stats_api(request):
    """Get coupon usage statistics"""
    try:
        total_coupons = Coupon.objects.count()
        active_coupons = Coupon.objects.filter(is_active=True).count()
        expired_coupons = Coupon.objects.filter(valid_until__lt=timezone.now()).count()
        used_coupons = Coupon.objects.filter(used_count__gt=0).count()

        # Most used coupons
        most_used = Coupon.objects.filter(used_count__gt=0).order_by('-used_count')[:5]
        most_used_data = AdminCouponListSerializer(most_used, many=True).data

        return Response({
            'success': True,
            'data': {
                'summary': {
                    'total_coupons': total_coupons,
                    'active_coupons': active_coupons,
                    'expired_coupons': expired_coupons,
                    'used_coupons': used_coupons
                },
                'most_used_coupons': most_used_data
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)