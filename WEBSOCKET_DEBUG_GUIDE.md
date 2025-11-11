# WebSocket Debugging Guide

## 🔍 Logging Added

Comprehensive logging has been added to all WebSocket components to help diagnose the production 500 error.

---

## 📋 What's Been Logged

### 1. **JWTAuthMiddleware** (`chat/middleware.py`)
- Connection attempts
- Token validation
- User authentication
- Token errors (expired, invalid, missing)

### 2. **ChatConsumer** (`chat/consumers.py`)
- Connection lifecycle (connect/disconnect)
- Authorization checks
- Message sending/receiving
- Database operations (conversation creation, message storage)
- Channel layer operations

### 3. **LocationConsumer** (`chat/consumers.py`)
- Connection lifecycle
- Authorization checks
- Location updates
- Channel layer operations

---

## 🚀 After Deployment - How to Debug

### Step 1: Check Logs for WebSocket Connections

```bash
# If using systemd
sudo journalctl -u your-service-name -f | grep -E '\[ChatConsumer\]|\[LocationConsumer\]|\[JWTAuthMiddleware\]'

# If using supervisor
tail -f /var/log/supervisor/your-app-stderr.log | grep -E '\[ChatConsumer\]|\[LocationConsumer\]|\[JWTAuthMiddleware\]'

# If using Docker
docker logs -f your-container-name | grep -E '\[ChatConsumer\]|\[LocationConsumer\]|\[JWTAuthMiddleware\]'

# Direct Django logs
tail -f /path/to/django.log | grep -E '\[ChatConsumer\]|\[LocationConsumer\]|\[JWTAuthMiddleware\]'
```

---

## 🔎 What to Look For

### When Testing `/ws/chat/1/2/?token=...`

**Expected Log Sequence (Success):**
```
[JWTAuthMiddleware] Processing connection for path: /ws/chat/1/2/
[JWTAuthMiddleware] Token found: eyJhbGciOiJIUzI1NiI...
[JWTAuthMiddleware] Decoded token payload, user_id: 1
[JWTAuthMiddleware] User found: 1 - user@example.com (role: customer)
[JWTAuthMiddleware] User authenticated: 1 (user@example.com)
[ChatConsumer] Connection attempt started
[ChatConsumer] User authenticated: True, User: <User object>
[ChatConsumer] Customer ID: 1, Therapist ID: 2
[ChatConsumer] Room group name: chat_1_2
[ChatConsumer] Added to channel group successfully
[ChatConsumer] Connection accepted for user 1 (role: customer)
[ChatConsumer] Getting/creating conversation for customer 1, therapist 2
[ChatConsumer] Found existing conversation: <uuid>
[ChatConsumer] Conversation loaded/created: <uuid>
```

**Common Error Patterns:**

1. **Authentication Error:**
```
[JWTAuthMiddleware] Invalid token: ...
[ChatConsumer] Connection rejected - user not authenticated
```
→ **Fix:** Check if token is valid and not expired

2. **Database Error:**
```
[ChatConsumer] Database error in get_or_create_conversation: ...
```
→ **Fix:** Check database connection, ensure migrations are run

3. **Redis Error:**
```
[ChatConsumer] Failed to add to channel group: ...
```
→ **Fix:** Check Redis connection at `srv804559.hstgr.cloud:6379`

4. **Authorization Error:**
```
[ChatConsumer] Authorization failed - customer 1 tried to access customer 2
```
→ **Fix:** Check user IDs in URL match authenticated user

---

## 🧪 Test Commands

### 1. Test with Node.js (from test directory)
```bash
cd /Users/manish/Developer/Freelance/RoomSpa/test
node websocket-test.js <jwt_token>
```

### 2. Test with diagnostics
```bash
cd /Users/manish/Developer/Freelance/RoomSpa/test
node websocket-diagnostic.js <jwt_token>
```

### 3. Get fresh token
```bash
curl -X POST https://spa.manishdashsharma.site/login/ \
  -H "Content-Type: application/json" \
  -d '{"identifier":"mdashsharma95@gmail.com","password":"12345678"}' \
  | jq -r '.access_token'
```

---

## 🐛 Common Issues & Solutions

### Issue 1: 500 Internal Server Error

**Symptoms:**
- WebSocket connection fails with HTTP 500
- `/ws/test/` works but `/ws/chat/` fails

**Debug Steps:**
1. Check logs for the exact error message
2. Look for database errors
3. Check Redis connection
4. Verify all migrations are applied

**Solutions:**
```bash
# Check Redis connection
redis-cli -h srv804559.hstgr.cloud -p 6379 -a npg_l9DMtmArvYW3 ping

# Run migrations
python manage.py migrate

# Check database connection
python manage.py dbshell
```

### Issue 2: Authentication Failures (4001)

**Symptoms:**
- Connection closed with code 4001
- Logs show "user not authenticated"

**Solutions:**
- Verify JWT token is not expired
- Check token is sent in query parameter: `?token=...`
- Ensure user exists in database

### Issue 3: Authorization Failures (4003)

**Symptoms:**
- Connection closed with code 4003
- Logs show authorization failed

**Solutions:**
- Ensure customer connects with their own ID
- Ensure therapist connects with their own ID
- Check user role matches URL parameters

### Issue 4: Database Errors

**Symptoms:**
- Logs show "Database error in get_or_create_conversation"
- Transaction errors

**Solutions:**
```bash
# Check database connection
python manage.py check --database default

# Ensure migrations are applied
python manage.py showmigrations
python manage.py migrate

# Check if users exist
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> User.objects.filter(id__in=[1, 2]).count()
```

---

## 📊 Log Levels

The logging uses standard Python logging levels:

- **INFO**: Normal operation (connection, disconnection, messages)
- **WARNING**: Unusual but handled (empty messages, auth failures)
- **ERROR**: Errors that need attention (database errors, Redis errors)

---

## 🔧 After Fixing

Once you deploy with logging and find the issue:

1. Look at the logs to identify the exact error
2. Fix the root cause
3. Test again with `node websocket-test.js <token>`
4. Verify all endpoints work:
   - `/ws/test/` ✅
   - `/ws/chat/1/2/?token=...` ✅
   - `/ws/location/1/2/?token=...` ✅

---

## 📞 Quick Reference

**Test Endpoints:**
```
wss://spa.manishdashsharma.site/ws/test/
wss://spa.manishdashsharma.site/ws/chat/{customer_id}/{therapist_id}/?token={jwt}
wss://spa.manishdashsharma.site/ws/location/{customer_id}/{therapist_id}/?token={jwt}
```

**Error Codes:**
- 1000: Normal closure
- 1006: Abnormal closure (connection lost)
- 1011: Internal server error
- 4000: Missing parameters
- 4001: Not authenticated
- 4003: Authorization failed

---

## 💡 Pro Tips

1. **Enable DEBUG logging** in production temporarily for detailed output
2. **Monitor in real-time** while testing: `tail -f logs | grep WebSocket`
3. **Test incrementally**: First test `/ws/test/`, then authenticated endpoints
4. **Check all dependencies**: Database, Redis, ASGI server running
5. **Verify environment**: Ensure production uses Redis, not InMemory channel layer
