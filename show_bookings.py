#!/usr/bin/env python3
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Spa.settings')
django.setup()

from booking.models import Booking, PendingRequests
from django.contrib.auth import get_user_model
import json

User = get_user_model()

print("=" * 80)
print("BOOKING DATABASE SUMMARY")
print("=" * 80)

# Stats
total_bookings = Booking.objects.count()
total_pending = PendingRequests.objects.count()
total_users = User.objects.count()

print(f"\nTotal Bookings: {total_bookings}")
print(f"Total Pending Requests: {total_pending}")
print(f"Total Users: {total_users}")

# Status breakdown
print("\n" + "=" * 80)
print("BOOKING STATUS BREAKDOWN")
print("=" * 80)
for status_choice in Booking.STATUS_CHOICES:
    status_code = status_choice[0]
    count = Booking.objects.filter(status=status_code).count()
    if count > 0:
        print(f"{status_code}: {count}")

# Pending request status breakdown
print("\n" + "=" * 80)
print("PENDING REQUEST STATUS BREAKDOWN")
print("=" * 80)
pending_statuses = PendingRequests.objects.values_list('status', flat=True).distinct()
for status in pending_statuses:
    count = PendingRequests.objects.filter(status=status).count()
    print(f"{status}: {count}")

# Recent bookings
print("\n" + "=" * 80)
print("RECENT BOOKINGS (Last 10)")
print("=" * 80)

recent_bookings = Booking.objects.all().order_by('-created_at')[:10]

if recent_bookings.exists():
    for idx, b in enumerate(recent_bookings, 1):
        print(f"\n{idx}. Booking ID: {b.id}")
        print(f"   Customer: {b.customer.email if b.customer else 'N/A'} ({b.customer.name if hasattr(b.customer, 'name') else 'No name'})")
        print(f"   Therapist: {b.therapist.email if b.therapist else 'N/A'} ({b.therapist.name if hasattr(b.therapist, 'name') else 'No name'})")
        print(f"   Services: {b.services}")
        print(f"   Subtotal: ₹{b.subtotal}")
        if b.coupon:
            print(f"   Coupon: {b.coupon.code} (-₹{b.coupon_discount})")
        print(f"   Total: ₹{b.total}")
        print(f"   Status: {b.status}")
        print(f"   Time Slot: {b.time_slot_from} to {b.time_slot_to}")
        print(f"   Created: {b.created_at}")
else:
    print("No bookings found")

# Recent pending requests
print("\n" + "=" * 80)
print("RECENT PENDING REQUESTS (Last 10)")
print("=" * 80)

recent_pending = PendingRequests.objects.all().order_by('-created_at')[:10]

if recent_pending.exists():
    for idx, p in enumerate(recent_pending, 1):
        print(f"\n{idx}. Request ID: {p.id}")
        print(f"   Customer: {p.customer_name} (ID: {p.customer_id})")
        print(f"   Therapist ID: {p.therapist_id}")
        print(f"   Services: {p.services}")
        print(f"   Status: {p.status}")
        print(f"   Time Slot: {p.timeslot_from} to {p.timeslot_to}")
        print(f"   Created: {p.created_at}")
        if p.coupon_code:
            print(f"   Coupon: {p.coupon_code}")
else:
    print("No pending requests found")

print("\n" + "=" * 80)
