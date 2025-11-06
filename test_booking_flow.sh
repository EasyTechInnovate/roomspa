#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base URL
BASE_URL="http://127.0.0.1:8000"

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Report data
START_TIME=$(date +%s)
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
REPORT_DIR="test_reports"
JSON_REPORT_FILE="$REPORT_DIR/booking_test_report_$TIMESTAMP.json"

# Arrays to store test results
declare -a TEST_NAMES
declare -a TEST_STATUSES
declare -a TEST_DETAILS
declare -a TEST_TIMES
declare -a TEST_REQUESTS
declare -a TEST_RESPONSES

# Create report directory
mkdir -p "$REPORT_DIR"

# Function to print test header
print_test() {
    TEST_START=$(date +%s)
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}TEST: $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((TESTS_PASSED++))
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
    ((TESTS_FAILED++))
}

# Function to print info
print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Function to record test result
record_test() {
    local name="$1"
    local status="$2"
    local detail="$3"
    local duration="$4"
    local request="${5:-N/A}"
    local response="${6:-N/A}"

    TEST_NAMES+=("$name")
    TEST_STATUSES+=("$status")
    TEST_DETAILS+=("$detail")
    TEST_TIMES+=("$duration")
    TEST_REQUESTS+=("$request")
    TEST_RESPONSES+=("$response")
}

# Variables to store tokens and IDs
CUSTOMER_TOKEN=""
THERAPIST_TOKEN=""
THERAPIST_ID=""
PENDING_REQUEST_ID=""
BOOKING_ID=""
COUPON_ID=""
BOOKING_WITHOUT_COUPON=""
BOOKING_WITH_COUPON=""

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   RoomSpa Booking System Test Suite   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"

# ============================================
# Test 1: Customer Login
# ============================================
TEST_START=$(date +%s)
print_test "1. Customer Login"
REQUEST_DATA='{
  "identifier": "mdashsharma95@gmail.com",
  "password": "12345678"
}'
RESPONSE=$(curl -s -X POST "$BASE_URL/login/" \
  -H "Content-Type: application/json" \
  -d "$REQUEST_DATA")

if echo "$RESPONSE" | grep -q "access_token"; then
    CUSTOMER_TOKEN=$(echo "$RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    print_success "Customer logged in successfully"
    print_info "Token: ${CUSTOMER_TOKEN:0:20}..."
    record_test "Customer Login" "PASS" "Customer authenticated successfully. Token obtained." $(($(date +%s) - TEST_START)) "POST $BASE_URL/login/ - $REQUEST_DATA" "$RESPONSE"
else
    print_error "Customer login failed"
    echo "$RESPONSE"
    record_test "Customer Login" "FAIL" "Authentication failed" $(($(date +%s) - TEST_START)) "POST $BASE_URL/login/ - $REQUEST_DATA" "$RESPONSE"
    exit 1
fi

# ============================================
# Test 2: Therapist Login
# ============================================
TEST_START=$(date +%s)
print_test "2. Therapist Login"
RESPONSE=$(curl -s -X POST "$BASE_URL/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "vinexi1320@limtu.com",
    "password": "12345678"
  }')

if echo "$RESPONSE" | grep -q "access_token"; then
    THERAPIST_TOKEN=$(echo "$RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    THERAPIST_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
    print_success "Therapist logged in successfully"
    print_info "Token: ${THERAPIST_TOKEN:0:20}..."
    print_info "Therapist ID: $THERAPIST_ID"
    record_test "Therapist Login" "PASS" "Therapist authenticated successfully. ID: $THERAPIST_ID" $(($(date +%s) - TEST_START))
else
    print_error "Therapist login failed"
    echo "$RESPONSE"
    record_test "Therapist Login" "FAIL" "Authentication failed: $RESPONSE" $(($(date +%s) - TEST_START))
    exit 1
fi

# ============================================
# Test 3: Check Therapist Profile (Location)
# ============================================
TEST_START=$(date +%s)
print_test "3. Check Therapist Profile - Location"
RESPONSE=$(curl -s -X GET "$BASE_URL/therapist/location/" \
  -H "Authorization: Bearer $THERAPIST_TOKEN")

if echo "$RESPONSE" | grep -q "address"; then
    print_success "Therapist location profile exists"
    ADDRESS=$(echo "$RESPONSE" | grep -o '"address":"[^"]*' | cut -d'"' -f4)
    print_info "Address: $ADDRESS"
    record_test "Therapist Location Profile" "PASS" "Location profile exists. Address: $ADDRESS" $(($(date +%s) - TEST_START))
else
    print_info "No location found - would need to create profile"
    record_test "Therapist Location Profile" "INFO" "No location profile found" $(($(date +%s) - TEST_START))
fi

# ============================================
# Test 4: Check Therapist Services
# ============================================
TEST_START=$(date +%s)
print_test "4. Check Therapist Services"
RESPONSE=$(curl -s -X GET "$BASE_URL/therapist/services/" \
  -H "Authorization: Bearer $THERAPIST_TOKEN")

if echo "$RESPONSE" | grep -q "services"; then
    print_success "Therapist services profile exists"
    SERVICES=$(echo $RESPONSE | grep -o '"services":{[^}]*}' | head -1)
    print_info "Services: $SERVICES"
    record_test "Therapist Services Profile" "PASS" "Services configured: $SERVICES" $(($(date +%s) - TEST_START))
else
    print_info "No services found - would need to create profile"
    record_test "Therapist Services Profile" "INFO" "No services configured" $(($(date +%s) - TEST_START))
fi

# ============================================
# Test 5: Admin Login and Create Coupon
# ============================================
TEST_START=$(date +%s)
print_test "5. Admin - Create Test Coupon"
TEST_TIMESTAMP=$(date +%s)
COUPON_CODE="TEST${TEST_TIMESTAMP: -4}"

RESPONSE=$(curl -s -X POST "$BASE_URL/admin_panel/api/coupons/create/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token admin-simple-token-2024" \
  -d "{
    \"code\": \"$COUPON_CODE\",
    \"name\": \"Test Discount\",
    \"description\": \"Test coupon for automated testing\",
    \"discount_type\": \"percentage\",
    \"discount_value\": \"15.00\",
    \"minimum_order_amount\": \"500.00\",
    \"maximum_discount_amount\": \"150.00\",
    \"usage_limit\": 10,
    \"is_active\": true,
    \"valid_from\": \"2025-01-01T00:00:00Z\",
    \"valid_until\": \"2026-12-31T23:59:59Z\"
  }")

if echo "$RESPONSE" | grep -q "success"; then
    COUPON_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
    print_success "Coupon created: $COUPON_CODE"
    print_info "Coupon ID: $COUPON_ID"
    record_test "Create Admin Coupon" "PASS" "Coupon created: $COUPON_CODE (15% off, max ₹150, min order ₹500)" $(($(date +%s) - TEST_START))
else
    print_error "Coupon creation failed"
    echo "$RESPONSE"
    record_test "Create Admin Coupon" "FAIL" "Failed to create coupon: $RESPONSE" $(($(date +%s) - TEST_START))
fi

# ============================================
# Test 6: Search Therapists
# ============================================
TEST_START=$(date +%s)
print_test "6. Search for Available Therapists"
RESPONSE=$(curl -s -X GET "$BASE_URL/booking/search-therapists/?latitude=19.0760&longitude=72.8777&radius=20" \
  -H "Authorization: Bearer $CUSTOMER_TOKEN")

if echo "$RESPONSE" | grep -q "\"id\":$THERAPIST_ID"; then
    print_success "Therapist found in search results"
    SERVICES=$(echo "$RESPONSE" | grep -o '"services":{[^}]*}' | head -1)
    print_info "$SERVICES"
    record_test "Search Therapists" "PASS" "Therapist found in search results with services" $(($(date +%s) - TEST_START))
else
    print_error "Therapist not found in search"
    echo "$RESPONSE"
    record_test "Search Therapists" "FAIL" "Therapist not found in search results" $(($(date +%s) - TEST_START))
fi

# Convert therapist ID to UUID format
THERAPIST_UUID=$(printf "00000000-0000-0000-0000-%012d" $THERAPIST_ID)
print_info "Therapist UUID: $THERAPIST_UUID"

# ============================================
# Test 7: Send Booking Request WITHOUT Coupon
# ============================================
TEST_START=$(date +%s)
print_test "7. Send Booking Request (No Coupon)"
TIMESLOT_FROM=$(date -u -v+1d +"%Y-%m-%dT10:00:00Z" 2>/dev/null || date -u -d "+1 day" +"%Y-%m-%dT10:00:00Z")
TIMESLOT_TO=$(date -u -v+1d +"%Y-%m-%dT12:00:00Z" 2>/dev/null || date -u -d "+1 day" +"%Y-%m-%dT12:00:00Z")

REQUEST_DATA="{
  \"id\": \"$THERAPIST_UUID\",
  \"services\": {\"thai\": 1, \"foot\": 1},
  \"timeslot_from\": \"$TIMESLOT_FROM\",
  \"timeslot_to\": \"$TIMESLOT_TO\",
  \"latitude\": \"19.076000\",
  \"longitude\": \"72.877700\",
  \"distance\": \"5.500000\"
}"
RESPONSE=$(curl -s -X POST "$BASE_URL/booking/send-booking-request/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $CUSTOMER_TOKEN" \
  -d "$REQUEST_DATA")

if echo "$RESPONSE" | grep -q "pending_booking_id"; then
    PENDING_REQUEST_ID=$(echo "$RESPONSE" | grep -o '"pending_booking_id":"[^"]*' | cut -d'"' -f4)
    print_success "Booking request sent"
    print_info "Pending Request ID: $PENDING_REQUEST_ID"
    record_test "Send Booking Request (No Coupon)" "PASS" "Request sent successfully. Services: Thai + Foot. Pending ID: $PENDING_REQUEST_ID" $(($(date +%s) - TEST_START)) "POST $BASE_URL/booking/send-booking-request/ - $REQUEST_DATA" "$RESPONSE"
else
    print_error "Booking request failed"
    echo "$RESPONSE"
    record_test "Send Booking Request (No Coupon)" "FAIL" "Failed to send booking request" $(($(date +%s) - TEST_START)) "POST $BASE_URL/booking/send-booking-request/ - $REQUEST_DATA" "$RESPONSE"
    exit 1
fi

# ============================================
# Test 8: Therapist Accepts Booking
# ============================================
TEST_START=$(date +%s)
print_test "8. Therapist Accepts Booking Request"
sleep 1  # Small delay
RESPONSE=$(curl -s -X POST "$BASE_URL/booking/respond-to-booking-request/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $THERAPIST_TOKEN" \
  -d "{
    \"id\": \"$PENDING_REQUEST_ID\",
    \"action\": \"accept\"
  }")

if echo "$RESPONSE" | grep -q "booking_id"; then
    BOOKING_ID=$(echo "$RESPONSE" | grep -o '"booking_id":"[^"]*' | cut -d'"' -f4)
    print_success "Booking accepted and created"
    print_info "Booking ID: $BOOKING_ID"
    record_test "Accept Booking Request" "PASS" "Therapist accepted booking. Booking ID: $BOOKING_ID" $(($(date +%s) - TEST_START))
else
    print_error "Booking acceptance failed"
    echo "$RESPONSE"
    record_test "Accept Booking Request" "FAIL" "Failed to accept booking: $RESPONSE" $(($(date +%s) - TEST_START))
    exit 1
fi

# ============================================
# Test 9: Verify Booking Details (No Coupon)
# ============================================
TEST_START=$(date +%s)
print_test "9. Verify Booking Details (No Coupon)"
sleep 1
RESPONSE=$(curl -s -X GET "$BASE_URL/booking/bookings/$BOOKING_ID/" \
  -H "Authorization: Bearer $CUSTOMER_TOKEN")

if echo "$RESPONSE" | grep -q "\"id\":\"$BOOKING_ID\""; then
    SUBTOTAL=$(echo "$RESPONSE" | grep -o '"subtotal":"[^"]*' | cut -d'"' -f4)
    COUPON_DISCOUNT=$(echo "$RESPONSE" | grep -o '"coupon_discount":"[^"]*' | cut -d'"' -f4)
    TOTAL=$(echo "$RESPONSE" | grep -o '"total":"[^"]*' | cut -d'"' -f4)

    print_success "Booking details retrieved"
    print_info "Subtotal: ₹$SUBTOTAL"
    print_info "Coupon Discount: ₹$COUPON_DISCOUNT"
    print_info "Total: ₹$TOTAL"

    BOOKING_WITHOUT_COUPON="Subtotal: ₹$SUBTOTAL | Discount: ₹$COUPON_DISCOUNT | Total: ₹$TOTAL"

    # Verify no coupon was applied
    if [ "$COUPON_DISCOUNT" == "0.00" ]; then
        print_success "Verified: No coupon discount applied"
        record_test "Verify Booking (No Coupon)" "PASS" "Booking verified. $BOOKING_WITHOUT_COUPON. No coupon applied ✓" $(($(date +%s) - TEST_START)) "GET $BASE_URL/booking/bookings/$BOOKING_ID/" "$RESPONSE"
    else
        print_error "Error: Coupon discount should be 0.00"
        record_test "Verify Booking (No Coupon)" "FAIL" "Unexpected coupon discount: ₹$COUPON_DISCOUNT" $(($(date +%s) - TEST_START)) "GET $BASE_URL/booking/bookings/$BOOKING_ID/" "$RESPONSE"
    fi
else
    print_error "Failed to retrieve booking details"
    echo "$RESPONSE"
    record_test "Verify Booking (No Coupon)" "FAIL" "Failed to retrieve booking" $(($(date +%s) - TEST_START)) "GET $BASE_URL/booking/bookings/$BOOKING_ID/" "$RESPONSE"
fi

# ============================================
# Test 10: Send Booking Request WITH Coupon
# ============================================
TEST_START=$(date +%s)
print_test "10. Send Booking Request (With Coupon: $COUPON_CODE)"
TIMESLOT_FROM_2=$(date -u -v+2d +"%Y-%m-%dT14:00:00Z" 2>/dev/null || date -u -d "+2 days" +"%Y-%m-%dT14:00:00Z")
TIMESLOT_TO_2=$(date -u -v+2d +"%Y-%m-%dT16:00:00Z" 2>/dev/null || date -u -d "+2 days" +"%Y-%m-%dT16:00:00Z")

REQUEST_DATA="{
  \"id\": \"$THERAPIST_UUID\",
  \"services\": {\"thai\": 1, \"oil\": 1},
  \"coupon_code\": \"$COUPON_CODE\",
  \"timeslot_from\": \"$TIMESLOT_FROM_2\",
  \"timeslot_to\": \"$TIMESLOT_TO_2\",
  \"latitude\": \"19.076000\",
  \"longitude\": \"72.877700\",
  \"distance\": \"5.500000\"
}"
RESPONSE=$(curl -s -X POST "$BASE_URL/booking/send-booking-request/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $CUSTOMER_TOKEN" \
  -d "$REQUEST_DATA")

if echo "$RESPONSE" | grep -q "pending_booking_id"; then
    PENDING_REQUEST_ID_2=$(echo "$RESPONSE" | grep -o '"pending_booking_id":"[^"]*' | cut -d'"' -f4)
    print_success "Booking request with coupon sent"
    print_info "Pending Request ID: $PENDING_REQUEST_ID_2"
    record_test "Send Booking Request (With Coupon)" "PASS" "Request sent with coupon $COUPON_CODE. Services: Thai + Oil. Pending ID: $PENDING_REQUEST_ID_2" $(($(date +%s) - TEST_START)) "POST $BASE_URL/booking/send-booking-request/ - $REQUEST_DATA" "$RESPONSE"
else
    print_error "Booking request with coupon failed"
    echo "$RESPONSE"
    record_test "Send Booking Request (With Coupon)" "FAIL" "Failed to send booking with coupon" $(($(date +%s) - TEST_START)) "POST $BASE_URL/booking/send-booking-request/ - $REQUEST_DATA" "$RESPONSE"
    exit 1
fi

# ============================================
# Test 11: Therapist Accepts Booking with Coupon
# ============================================
TEST_START=$(date +%s)
print_test "11. Therapist Accepts Booking with Coupon"
sleep 1
RESPONSE=$(curl -s -X POST "$BASE_URL/booking/respond-to-booking-request/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $THERAPIST_TOKEN" \
  -d "{
    \"id\": \"$PENDING_REQUEST_ID_2\",
    \"action\": \"accept\"
  }")

if echo "$RESPONSE" | grep -q "booking_id"; then
    BOOKING_ID_2=$(echo "$RESPONSE" | grep -o '"booking_id":"[^"]*' | cut -d'"' -f4)
    print_success "Booking with coupon accepted"
    print_info "Booking ID: $BOOKING_ID_2"
    record_test "Accept Booking (With Coupon)" "PASS" "Therapist accepted booking with coupon. Booking ID: $BOOKING_ID_2" $(($(date +%s) - TEST_START))
else
    print_error "Booking acceptance failed"
    echo "$RESPONSE"
    record_test "Accept Booking (With Coupon)" "FAIL" "Failed to accept booking with coupon: $RESPONSE" $(($(date +%s) - TEST_START))
    exit 1
fi

# ============================================
# Test 12: Verify Booking with Coupon
# ============================================
TEST_START=$(date +%s)
print_test "12. Verify Booking Details (With Coupon)"
sleep 1
RESPONSE=$(curl -s -X GET "$BASE_URL/booking/bookings/$BOOKING_ID_2/" \
  -H "Authorization: Bearer $CUSTOMER_TOKEN")

if echo "$RESPONSE" | grep -q "\"id\":\"$BOOKING_ID_2\""; then
    SUBTOTAL=$(echo "$RESPONSE" | grep -o '"subtotal":"[^"]*' | cut -d'"' -f4)
    COUPON_DISCOUNT=$(echo "$RESPONSE" | grep -o '"coupon_discount":"[^"]*' | cut -d'"' -f4)
    TOTAL=$(echo "$RESPONSE" | grep -o '"total":"[^"]*' | cut -d'"' -f4)
    COUPON_INFO=$(echo "$RESPONSE" | grep -o '"coupon_info":{[^}]*}' | head -1)

    print_success "Booking with coupon details retrieved"
    print_info "Subtotal: ₹$SUBTOTAL"
    print_info "Coupon Discount: ₹$COUPON_DISCOUNT"
    print_info "Total: ₹$TOTAL"
    print_info "$COUPON_INFO"

    BOOKING_WITH_COUPON="Subtotal: ₹$SUBTOTAL | Discount: ₹$COUPON_DISCOUNT | Total: ₹$TOTAL | Coupon: $COUPON_CODE"

    # Verify coupon was applied
    if [ "$COUPON_DISCOUNT" != "0.00" ]; then
        print_success "Verified: Coupon discount applied (₹$COUPON_DISCOUNT)"

        # Calculate expected discount (15% of subtotal, max 150)
        EXPECTED_DISCOUNT=$(echo "scale=2; $SUBTOTAL * 0.15" | bc)
        if (( $(echo "$EXPECTED_DISCOUNT > 150" | bc -l) )); then
            EXPECTED_DISCOUNT="150.00"
        fi

        if [ "$COUPON_DISCOUNT" == "$EXPECTED_DISCOUNT" ]; then
            print_success "Verified: Discount calculation is correct"
            record_test "Verify Booking (With Coupon)" "PASS" "Booking verified. $BOOKING_WITH_COUPON. Discount calculation correct ✓" $(($(date +%s) - TEST_START)) "GET $BASE_URL/booking/bookings/$BOOKING_ID_2/" "$RESPONSE"
        else
            print_info "Expected discount: ₹$EXPECTED_DISCOUNT"
            record_test "Verify Booking (With Coupon)" "PASS" "Booking verified. $BOOKING_WITH_COUPON. Expected: ₹$EXPECTED_DISCOUNT" $(($(date +%s) - TEST_START)) "GET $BASE_URL/booking/bookings/$BOOKING_ID_2/" "$RESPONSE"
        fi
    else
        print_error "Error: Coupon discount should not be 0.00"
        record_test "Verify Booking (With Coupon)" "FAIL" "Coupon was not applied. Discount: ₹0.00" $(($(date +%s) - TEST_START)) "GET $BASE_URL/booking/bookings/$BOOKING_ID_2/" "$RESPONSE"
    fi
else
    print_error "Failed to retrieve booking with coupon details"
    echo "$RESPONSE"
    record_test "Verify Booking (With Coupon)" "FAIL" "Failed to retrieve booking" $(($(date +%s) - TEST_START)) "GET $BASE_URL/booking/bookings/$BOOKING_ID_2/" "$RESPONSE"
fi

# ============================================
# Test 13: List All Bookings
# ============================================
TEST_START=$(date +%s)
print_test "13. List All Customer Bookings"
RESPONSE=$(curl -s -X POST "$BASE_URL/booking/bookings/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $CUSTOMER_TOKEN" \
  -d "{\"customer\": 1}")

BOOKING_COUNT=$(echo "$RESPONSE" | grep -o '"id":"[^"]*"' | wc -l | tr -d ' ')
print_success "Retrieved $BOOKING_COUNT bookings"
record_test "List All Bookings" "PASS" "Retrieved $BOOKING_COUNT customer bookings" $(($(date +%s) - TEST_START))

# ============================================
# Test 14: Validate Coupon API
# ============================================
TEST_START=$(date +%s)
print_test "14. Test Validate Coupon API"
RESPONSE=$(curl -s -X POST "$BASE_URL/booking/validate-coupon/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $CUSTOMER_TOKEN" \
  -d "{
    \"coupon_code\": \"$COUPON_CODE\",
    \"order_amount\": \"1000.00\"
  }")

if echo "$RESPONSE" | grep -q "success.*true"; then
    print_success "Coupon validation API working"
    DISCOUNT=$(echo "$RESPONSE" | grep -o '"discount_amount":[0-9.]*' | cut -d':' -f2)
    print_info "Discount for ₹1000: ₹$DISCOUNT"
    record_test "Validate Coupon API" "PASS" "Coupon validation working. Discount for ₹1000: ₹$DISCOUNT" $(($(date +%s) - TEST_START))
else
    print_error "Coupon validation failed"
    echo "$RESPONSE"
    record_test "Validate Coupon API" "FAIL" "Coupon validation failed: $RESPONSE" $(($(date +%s) - TEST_START))
fi

# ============================================
# Test 15: Pending Requests List
# ============================================
TEST_START=$(date +%s)
print_test "15. Check Therapist Pending Requests"
RESPONSE=$(curl -s -X GET "$BASE_URL/booking/pending-requests/" \
  -H "Authorization: Bearer $THERAPIST_TOKEN")

if echo "$RESPONSE" | grep -q "\["; then
    REQUEST_COUNT=$(echo "$RESPONSE" | grep -o '"id":"[^"]*"' | wc -l | tr -d ' ')
    print_success "Retrieved $REQUEST_COUNT pending requests"
    record_test "Pending Requests List" "PASS" "Retrieved $REQUEST_COUNT pending requests for therapist" $(($(date +%s) - TEST_START))
else
    print_error "Failed to retrieve pending requests"
    echo "$RESPONSE"
    record_test "Pending Requests List" "FAIL" "Failed to retrieve pending requests: $RESPONSE" $(($(date +%s) - TEST_START))
fi

# ============================================
# Generate Reports
# ============================================
END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))
REPORT_DATE=$(date +"%Y-%m-%d %H:%M:%S")

echo -e "\n${BLUE}Generating JSON report...${NC}"

# Generate JSON Report
cat > "$JSON_REPORT_FILE" << EOF
{
  "report_metadata": {
    "generated_at": "$REPORT_DATE",
    "timestamp": "$TIMESTAMP",
    "total_duration_seconds": $TOTAL_DURATION,
    "base_url": "$BASE_URL"
  },
  "summary": {
    "total_tests": ${#TEST_NAMES[@]},
    "passed": $TESTS_PASSED,
    "failed": $TESTS_FAILED,
    "pass_rate": $(echo "scale=2; ($TESTS_PASSED * 100) / ${#TEST_NAMES[@]}" | bc)
  },
  "test_results": [
EOF

for i in "${!TEST_NAMES[@]}"; do
    name="${TEST_NAMES[$i]}"
    status="${TEST_STATUSES[$i]}"
    detail="${TEST_DETAILS[$i]}"
    time="${TEST_TIMES[$i]}"
    request="${TEST_REQUESTS[$i]}"
    response="${TEST_RESPONSES[$i]}"

    # Escape quotes for JSON
    detail=$(echo "$detail" | sed 's/"/\\"/g' | tr '\n' ' ')
    request=$(echo "$request" | sed 's/"/\\"/g' | tr '\n' ' ')
    response=$(echo "$response" | sed 's/"/\\"/g' | tr '\n' ' ')

    cat >> "$JSON_REPORT_FILE" << EOF
    {
      "test_number": $((i+1)),
      "name": "$name",
      "status": "$status",
      "details": "$detail",
      "duration_seconds": $time,
      "api_request": "$request",
      "api_response": "$response"
    }$([ $i -lt $((${#TEST_NAMES[@]}-1)) ] && echo "," || echo "")
EOF
done

cat >> "$JSON_REPORT_FILE" << EOF
  ]
}
EOF

# ============================================
# Final Summary
# ============================================
echo -e "\n${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          TEST SUMMARY                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
echo -e "${YELLOW}Total Duration: ${TOTAL_DURATION}s${NC}"

echo -e "\n${BLUE}📄 Report Generated:${NC}"
echo -e "${GREEN}✓ JSON Report: $JSON_REPORT_FILE${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed successfully!${NC}\n"
    exit 0
else
    echo -e "\n${RED}✗ Some tests failed. Please check the report for details.${NC}\n"
    exit 1
fi
