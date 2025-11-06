#!/usr/bin/env python3
"""
Test script to verify 2-minute auto-expiry for pending booking requests
"""
import os
import django
import sys
from datetime import timedelta

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Spa.settings')
django.setup()

from booking.models import PendingRequests
from django.utils import timezone

print("=" * 70)
print("PENDING REQUEST AUTO-EXPIRY TEST")
print("=" * 70)

# Create a test pending request
print("\n1. Creating a test pending request...")
test_request = PendingRequests.objects.create(
    customer_id="1",
    therapist_id="2",
    status='pending',
    customer_name="Test Customer",
    services="{'test': 1}",
    timeslot_from=timezone.now() + timedelta(hours=1),
    timeslot_to=timezone.now() + timedelta(hours=2),
    latitude=19.076,
    longitude=72.877,
    distance=5.5
)
print(f"   ✓ Created request ID: {test_request.id}")
print(f"   ✓ Status: {test_request.status}")
print(f"   ✓ Created at: {test_request.created_at}")

# Test 1: Fresh request should not be expired
print("\n2. Testing fresh request (just created)...")
print(f"   is_expired(): {test_request.is_expired()}")
if not test_request.is_expired():
    print("   ✓ PASS: Fresh request is not expired")
else:
    print("   ✗ FAIL: Fresh request should not be expired")

# Test 2: Simulate old request by manually setting created_at
print("\n3. Simulating request older than 2 minutes...")
test_request.created_at = timezone.now() - timedelta(minutes=3)
test_request.save()
test_request.refresh_from_db()

print(f"   Created at: {test_request.created_at}")
print(f"   Current time: {timezone.now()}")
print(f"   Age: {(timezone.now() - test_request.created_at).total_seconds()} seconds")
print(f"   is_expired(): {test_request.is_expired()}")

if test_request.is_expired():
    print("   ✓ PASS: Old request is expired")
else:
    print("   ✗ FAIL: Old request should be expired")

# Test 3: Auto-expire functionality
print("\n4. Testing auto_expire_if_needed()...")
result = test_request.auto_expire_if_needed()
test_request.refresh_from_db()

print(f"   auto_expire_if_needed() returned: {result}")
print(f"   Status after: {test_request.status}")

if result and test_request.status == 'expired':
    print("   ✓ PASS: Status changed to 'expired'")
else:
    print("   ✗ FAIL: Status should be 'expired'")

# Test 4: Already expired request shouldn't be re-expired
print("\n5. Testing already expired request...")
test_request.status = 'accepted'
test_request.save()
result = test_request.auto_expire_if_needed()

print(f"   Status: {test_request.status}")
print(f"   auto_expire_if_needed() returned: {result}")

if not result:
    print("   ✓ PASS: Non-pending requests don't get expired")
else:
    print("   ✗ FAIL: Non-pending requests shouldn't be expired")

# Cleanup
print("\n6. Cleaning up test data...")
test_request.delete()
print("   ✓ Test request deleted")

print("\n" + "=" * 70)
print("API USAGE FOR CUSTOMER APP")
print("=" * 70)
print("""
To get pending requests in customer app:

GET /booking/pending-requests/?role=customer
Headers:
  Authorization: Bearer <customer_token>

Response:
  - Only returns pending/accepted/rejected requests
  - Expired requests are automatically excluded
  - Requests older than 2 minutes are auto-expired

Example:
  curl -X GET "http://127.0.0.1:8000/booking/pending-requests/?role=customer" \\
    -H "Authorization: Bearer YOUR_CUSTOMER_TOKEN"
""")

print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)
