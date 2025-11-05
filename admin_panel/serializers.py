from rest_framework import serializers
from booking.models import Coupon

class AdminCouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'name', 'description', 'discount_type', 'discount_value',
            'minimum_order_amount', 'maximum_discount_amount', 'usage_limit', 'used_count',
            'is_active', 'valid_from', 'valid_until', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'used_count', 'created_at', 'updated_at']

    def validate_code(self, value):
        # Convert to uppercase and validate uniqueness
        value = value.upper().strip()
        if self.instance:
            # For updates, exclude current instance from uniqueness check
            if Coupon.objects.filter(code=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("A coupon with this code already exists.")
        else:
            # For creation, check if code already exists
            if Coupon.objects.filter(code=value).exists():
                raise serializers.ValidationError("A coupon with this code already exists.")
        return value

    def validate(self, data):
        # Validate that valid_from is before valid_until
        if 'valid_from' in data and 'valid_until' in data:
            if data['valid_from'] >= data['valid_until']:
                raise serializers.ValidationError("Valid from date must be before valid until date.")

        # Validate discount value based on type
        if 'discount_type' in data and 'discount_value' in data:
            if data['discount_type'] == 'percentage' and data['discount_value'] > 100:
                raise serializers.ValidationError("Percentage discount cannot be more than 100%.")
            if data['discount_value'] <= 0:
                raise serializers.ValidationError("Discount value must be greater than 0.")

        return data

class AdminCouponListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing coupons"""
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'name', 'discount_type', 'discount_value',
            'minimum_order_amount', 'usage_limit', 'used_count',
            'is_active', 'valid_from', 'valid_until', 'created_at'
        ]