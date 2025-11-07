from rest_framework import serializers
from .models import Booking, FCMToken, PendingRequests, Coupon
from therapist.models import Services as TherapistAddress

class PendingRequestsSerializer(serializers.ModelSerializer):
    services_with_pricing = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    customer_profile_picture = serializers.SerializerMethodField()
    therapist_profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = PendingRequests
        fields = [ 'id', 'customer_id', 'therapist_id', 'status', 'customer_name', 'services', 'services_with_pricing', 'total_amount', 'timeslot_from', 'timeslot_to', 'latitude', 'longitude', 'distance', 'customer_profile_picture', 'therapist_profile_picture', 'created_at']
        read_only_fields = ['id', 'created_at', 'services_with_pricing', 'total_amount', 'customer_profile_picture', 'therapist_profile_picture']

    def get_services_with_pricing(self, obj):
        try:
            import ast
            from therapist.models import Services as TherapistServices
            from django.contrib.auth import get_user_model

            User = get_user_model()
            therapist = User.objects.get(id=obj.therapist_id)
            therapist_services = TherapistServices.objects.filter(user=therapist).first()

            # Parse services string to dict
            if isinstance(obj.services, str):
                try:
                    requested_services = ast.literal_eval(obj.services)
                except:
                    requested_services = {}
            else:
                requested_services = obj.services or {}

            services_array = []
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

                    services_array.append({
                        'service_name': service_name,
                        'quantity': actual_quantity,
                        'price_per_unit': float(price_per_service),
                        'total_price': float(price_per_service) * actual_quantity
                    })

            return services_array
        except Exception as e:
            return []

    def get_total_amount(self, obj):
        services_pricing = self.get_services_with_pricing(obj)
        total = sum(service['total_price'] for service in services_pricing)
        return float(total)

    def get_customer_profile_picture(self, obj):
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            customer = User.objects.get(id=obj.customer_id)
            return customer.therapist_pictures.profile_picture
        except:
            return None

    def get_therapist_profile_picture(self, obj):
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            therapist = User.objects.get(id=obj.therapist_id)
            return therapist.therapist_pictures.profile_picture
        except:
            return None

class FCMTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMToken
        fields = ['token']

class BookingRequestSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    services = serializers.DictField()
    timeslot_from = serializers.DateTimeField()
    timeslot_to = serializers.DateTimeField()
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    distance = serializers.DecimalField(max_digits=9, decimal_places=6)
    coupon_code = serializers.CharField(max_length=50, required=False, allow_blank=True)

class BookingResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    action = serializers.ChoiceField(choices=['accept', 'reject'])

class BookingSerializer(serializers.ModelSerializer):
    source = serializers.SerializerMethodField()
    destination = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    therapist_name = serializers.SerializerMethodField()
    customer_id = serializers.SerializerMethodField()
    therapist_id = serializers.SerializerMethodField()
    customer_phone = serializers.SerializerMethodField()
    therapist_phone = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()
    therapist_email = serializers.SerializerMethodField()
    customer_profile_picture = serializers.SerializerMethodField()
    therapist_profile_picture = serializers.SerializerMethodField()
    coupon_info = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'customer_id', 'therapist_id', 'time_slot_from', 'time_slot_to', 'services',
            'subtotal', 'coupon_discount', 'total', 'status',
            'cancellation_reason', 'distance',
            'created_at', 'started_at', 'completed_at', 'cancelled_at',
            'customer_name', 'therapist_name', 'customer_phone', 'therapist_phone',
            'customer_email', 'therapist_email', 'customer_profile_picture', 'therapist_profile_picture',
            'coupon_info', 'source', 'destination'
        ]
        read_only_fields = ['id', 'created_at', 'source', 'destination', 'customer_name', 'therapist_name',
                           'customer_id', 'therapist_id', 'customer_phone', 'therapist_phone',
                           'customer_email', 'therapist_email', 'customer_profile_picture', 'therapist_profile_picture']

    def get_source(self, obj):
        try:
            ta = obj.therapist.therapist_address
            return {'latitude': ta.latitude, 'longitude': ta.longitude}
        except TherapistAddress.DoesNotExist:
            return {'latitude': None, 'longitude': None}

    def get_destination(self, obj):
        return {'latitude': obj.latitude, 'longitude': obj.longitude}

    def _get_name(self, user_obj):
        if not user_obj:
            return None
        return getattr(user_obj, 'name', None) or str(user_obj)

    def get_customer_name(self, obj):
        return self._get_name(obj.customer)

    def get_therapist_name(self, obj):
        return self._get_name(obj.therapist)

    def get_customer_id(self, obj):
        return obj.customer.id if obj.customer else None

    def get_therapist_id(self, obj):
        return obj.therapist.id if obj.therapist else None

    def get_customer_phone(self, obj):
        return obj.customer.phone_number if obj.customer else None

    def get_therapist_phone(self, obj):
        return obj.therapist.phone_number if obj.therapist else None

    def get_customer_email(self, obj):
        return obj.customer.email if obj.customer else None

    def get_therapist_email(self, obj):
        return obj.therapist.email if obj.therapist else None

    def get_customer_profile_picture(self, obj):
        if obj.customer:
            try:
                return obj.customer.therapist_pictures.profile_picture
            except:
                return None
        return None

    def get_therapist_profile_picture(self, obj):
        if obj.therapist:
            try:
                return obj.therapist.therapist_pictures.profile_picture
            except:
                return None
        return None

    def get_coupon_info(self, obj):
        if obj.coupon:
            return {
                'code': obj.coupon.code,
                'name': obj.coupon.name,
                'discount_type': obj.coupon.discount_type,
                'discount_value': obj.coupon.discount_value
            }
        return None

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['id', 'code', 'name', 'description', 'discount_type', 'discount_value',
                 'minimum_order_amount', 'maximum_discount_amount', 'is_active',
                 'valid_from', 'valid_until']
        read_only_fields = ['id']

class CouponValidationSerializer(serializers.Serializer):
    coupon_code = serializers.CharField(max_length=50)
    order_amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate_coupon_code(self, value):
        try:
            coupon = Coupon.objects.get(code=value.upper())
            if not coupon.is_valid():
                raise serializers.ValidationError("This coupon is not valid or has expired.")
            return value.upper()
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("Invalid coupon code.")

class ApplyCouponSerializer(serializers.Serializer):
    coupon_code = serializers.CharField(max_length=50)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    final_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)