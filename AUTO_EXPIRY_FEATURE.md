# Auto-Expiry Feature for Pending Booking Requests

## Overview
Pending booking requests that are not accepted by therapists within **2 minutes** are automatically marked as "expired" and visible to both customer and therapist.

## Problem Solved
- Previously: Pending requests stayed visible to customers indefinitely, even if therapist never responded
- Now: After 2 minutes, requests are automatically marked as "expired" so both customer and therapist know the request timed out

## Implementation Details

### 1. Model Changes (`booking/models.py`)

Added two methods to `PendingRequests` model:

```python
def is_expired(self):
    """Check if request is older than 2 minutes and still pending"""
    from datetime import timedelta
    if self.status != 'pending':
        return False
    expiry_time = self.created_at + timedelta(minutes=2)
    return timezone.now() > expiry_time

def auto_expire_if_needed(self):
    """Automatically mark as expired if older than 2 minutes"""
    if self.is_expired():
        self.status = 'expired'
        self.save()
        return True
    return False
```

### 2. View Changes (`booking/views.py`)

#### Updated `pending_requests_list` endpoint:
- Automatically detects user role from authentication (customer vs therapist)
- Automatically expires old pending requests (bulk update)
- Both customers and therapists can see expired requests

```python
# Auto-expire old pending requests
from datetime import timedelta
two_minutes_ago = timezone.now() - timedelta(minutes=2)
old_pending = qs.filter(status='pending', created_at__lt=two_minutes_ago)
old_pending.update(status='expired')
```

#### Updated `respond_to_booking_request`:
- Checks if request is expired before allowing therapist to accept
- Returns 410 GONE status if expired

```python
# Check if request has expired
if pending_request.is_expired():
    pending_request.status = 'expired'
    pending_request.save()
    return Response({
        'error': 'Request has expired',
        'message': 'This booking request expired because it was not accepted within 2 minutes.'
    }, status=status.HTTP_410_GONE)
```

## Status Values

- **`pending`**: Request sent, waiting for therapist response
- **`accepted`**: Therapist accepted, booking created
- **`rejected`**: Therapist rejected the request
- **`expired`**: Request older than 2 minutes, not responded (auto-set)
- **`cancelled`**: Manually cancelled

## API Usage

### For Customer App - View Pending Requests

```bash
GET /booking/pending-requests/
Authorization: Bearer <customer_token>
```

**Behavior:**
- Automatically detects you're a customer from your authentication token
- Returns all requests including `pending`, `accepted`, `rejected`, `expired`
- Auto-expires requests older than 2 minutes
- Customer can see which requests expired (weren't accepted in time)

**Response Example:**
```json
[
  {
    "id": "uuid",
    "status": "pending",
    "customer_name": "John",
    "services": "{'thai': 1}",
    "created_at": "2025-11-06T09:05:00Z"
  }
]
```

### For Therapist App - View Pending Requests

```bash
GET /booking/pending-requests/
Authorization: Bearer <therapist_token>
```

**Behavior:**
- Automatically detects you're a therapist from your authentication token
- Shows all requests including expired ones
- Same as customer view - both can see expired requests

### For Therapist - Accept Request

```bash
POST /booking/respond-to-booking-request/
Authorization: Bearer <therapist_token>
Content-Type: application/json

{
  "id": "request_uuid",
  "action": "accept"
}
```

**Responses:**
- **200 OK**: Request accepted, booking created
- **410 GONE**: Request expired (older than 2 minutes)
- **409 CONFLICT**: Request already responded to

## Testing

Run the test script to verify functionality:

```bash
python3 test_expiry.py
```

### Test Results:
✅ Fresh requests (< 2 minutes) remain visible
✅ Old requests (> 2 minutes) auto-expire
✅ Expired requests visible to both customers and therapists
✅ Therapists cannot accept expired requests
✅ Non-pending requests don't get expired

## Examples

### Example 1: Fresh Request (Visible)
```
Customer sends request at 10:00:00
Customer checks at 10:01:30
→ Status: pending
→ Visible: YES
```

### Example 2: Expired Request (Visible)
```
Customer sends request at 10:00:00
Customer checks at 10:02:30
→ Status: expired (auto-set)
→ Visible: YES (customer can see it expired)
```

### Example 3: Therapist Accepts in Time
```
Customer sends request at 10:00:00
Therapist accepts at 10:01:00
→ Status: accepted
→ Booking created ✓
```

### Example 4: Therapist Accepts Too Late
```
Customer sends request at 10:00:00
Therapist tries to accept at 10:03:00
→ Status: expired (auto-set)
→ Response: 410 GONE
→ Error: "Request has expired"
```

## Benefits

1. **Better UX**: Customers can see which requests expired and weren't accepted in time
2. **Clear Status**: Both parties know when a request expires (marked as "expired")
3. **Automatic**: No manual intervention needed
4. **Configurable**: 2-minute timeout can be changed if needed

## Configuration

To change the expiry timeout, update the timedelta value in:
- `booking/models.py` → `is_expired()` method
- `booking/views.py` → `pending_requests_list` view

Current: `timedelta(minutes=2)`

## Migration

No database migration required! The feature uses existing fields:
- `status` field (existing)
- `created_at` field (existing)

Just restart your server to apply changes.
