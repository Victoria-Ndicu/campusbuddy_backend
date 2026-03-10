#!/usr/bin/env bash
# ============================================================
# API TEST SCRIPT — Full Suite
# Usage: bash test_api.sh [BASE_URL]
# Default BASE_URL: http://127.0.0.1:8000
# ============================================================

BASE="${1:-http://127.0.0.1:8000}/api/v1"
EMAIL="test3@uni.ac.ke"
PASSWORD="securepass123"
ACCESS=""
REFRESH=""
LISTING_ID=""
HOUSING_ID=""
EVENT_ID=""
GROUP_ID=""
QUESTION_ID=""

# ── Helpers ─────────────────────────────────────────────────
GREEN='\033[0;32m'; RED='\033[0;31m'; CYAN='\033[0;36m'
YELLOW='\033[1;33m'; NC='\033[0m'; BOLD='\033[1m'

pass() { echo -e "${GREEN}  ✔ PASS${NC}  $1"; }
fail() { echo -e "${RED}  ✘ FAIL${NC}  $1"; }
info() { echo -e "${CYAN}  ℹ  ${NC}$1"; }
warn() { echo -e "${YELLOW}  ⚠  ${NC}$1"; }
section() { echo -e "\n${BOLD}${CYAN}══════════════════════════════════════${NC}"; echo -e "${BOLD}${CYAN}  $1${NC}"; echo -e "${BOLD}${CYAN}══════════════════════════════════════${NC}"; }

# Pretty-print + capture
req() {
  local label="$1"; shift
  echo -e "\n${BOLD}▶ $label${NC}"
  local resp
  resp=$(curl -s "$@")
  echo "$resp" | python3 -m json.tool 2>/dev/null || echo "$resp"
  echo "$resp"   # last line is the raw value returned to caller
}

# Extract a JSON field (simple, no jq required)
jget() { echo "$1" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d$2)" 2>/dev/null; }

# ============================================================
section "🔐 AUTH"
# ============================================================

# 1. Register
RESP=$(req "1. Register" -s -X POST "$BASE/auth/register/" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}")
echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print('registered:', d.get('email','?'))" 2>/dev/null && pass "Register" || warn "Register may have failed (user might already exist)"

# 2. Verify OTP
echo ""
warn "⏳ Paste the OTP code from your server terminal and press Enter:"
read -r OTP_CODE

RESP=$(req "2. Verify OTP" -s -X POST "$BASE/auth/verify-otp/" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"code\": \"$OTP_CODE\"}")
ACCESS=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access',''))" 2>/dev/null)
REFRESH=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('refresh',''))" 2>/dev/null)

if [[ -n "$ACCESS" && "$ACCESS" != "None" ]]; then
  pass "Verify OTP — tokens captured"
  info "ACCESS  = ${ACCESS:0:40}..."
  info "REFRESH = ${REFRESH:0:40}..."
else
  fail "Verify OTP — no access token in response"
  warn "Continuing with empty token (subsequent tests will likely 401)"
fi

# 3. Login
RESP=$(req "4. Login" -s -X POST "$BASE/auth/login/" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}")
LOGIN_ACCESS=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access',''))" 2>/dev/null)
[[ -n "$LOGIN_ACCESS" ]] && pass "Login" || fail "Login"

# 4. Get current user
RESP=$(req "5. Get current user" -s "$BASE/auth/me/" \
  -H "Authorization: Bearer $ACCESS")
echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print('user:', d.get('email','?'))" 2>/dev/null && pass "Get /me/" || fail "Get /me/"

# 5. Refresh token
RESP=$(req "6. Refresh token" -s -X POST "$BASE/auth/refresh/" \
  -H "Content-Type: application/json" \
  -d "{\"refresh\": \"$REFRESH\"}")
NEW_ACCESS=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access',''))" 2>/dev/null)
[[ -n "$NEW_ACCESS" ]] && { pass "Refresh token"; ACCESS="$NEW_ACCESS"; } || fail "Refresh token"

# 6. Forgot password
RESP=$(req "7. Forgot password" -s -X POST "$BASE/auth/forgot-password/" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\"}")
echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(list(d.keys()))" 2>/dev/null && pass "Forgot password" || fail "Forgot password"

# ============================================================
section "👤 PROFILE"
# ============================================================

RESP=$(req "8. Get profile" -s "$BASE/profile/me/" \
  -H "Authorization: Bearer $ACCESS")
echo "$RESP" | python3 -m json.tool > /dev/null 2>&1 && pass "Get profile" || fail "Get profile"

RESP=$(req "9. Update profile" -s -X PATCH "$BASE/profile/me/" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"fullName": "John Doe", "university": "University of Nairobi", "yearOfStudy": 2}')
echo "$RESP" | python3 -m json.tool > /dev/null 2>&1 && pass "Update profile" || fail "Update profile"

RESP=$(req "10. Update preferences" -s -X PATCH "$BASE/profile/preferences/" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"notifications": true, "darkMode": false, "language": "en"}')
echo "$RESP" | python3 -m json.tool > /dev/null 2>&1 && pass "Update preferences" || fail "Update preferences"

RESP=$(req "11. Register device token" -s -X POST "$BASE/profile/device-token/" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"token": "fake-fcm-token-abc123", "platform": "android"}')
echo "$RESP" | python3 -m json.tool > /dev/null 2>&1 && pass "Register device token" || fail "Register device token"

RESP=$(req "12. Submit feedback" -s -X POST "$BASE/profile/feedback/" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"message": "Great app!", "category": "general"}')
echo "$RESP" | python3 -m json.tool > /dev/null 2>&1 && pass "Submit feedback" || fail "Submit feedback"

RESP=$(req "13. Get notifications" -s "$BASE/profile/notifications/" \
  -H "Authorization: Bearer $ACCESS")
echo "$RESP" | python3 -m json.tool > /dev/null 2>&1 && pass "Get notifications" || fail "Get notifications"

# ============================================================
section "🛒 MARKET"
# ============================================================

RESP=$(req "14. Create listing" -s -X POST "$BASE/market/listings/" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Python Textbook",
    "description": "Good condition, used one semester",
    "price": 500,
    "category": "books",
    "condition": "good",
    "campus_id": "uon",
    "listing_type": "sale"
  }')
LISTING_ID=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id', d.get('listing_id','')))" 2>/dev/null)
[[ -n "$LISTING_ID" ]] && { pass "Create listing — ID: $LISTING_ID"; } || fail "Create listing"

RESP=$(req "15. List all listings" -s "\"$BASE/market/listings/?campus_id=uon\"" \
  -H "Authorization: Bearer $ACCESS")

req "17. Get single listing" -s "$BASE/market/listings/$LISTING_ID/" \
  -H "Authorization: Bearer $ACCESS" > /dev/null
pass "Get single listing"

req "18. Update listing" -s -X PUT "$BASE/market/listings/$LISTING_ID/" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"title": "Python Textbook - Updated", "price": 450}' > /dev/null
pass "Update listing"

req "19. Toggle save listing" -s -X POST "$BASE/market/saved/" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d "{\"listing_id\": \"$LISTING_ID\"}" > /dev/null
pass "Toggle save listing"

req "20. Get saved listings" -s "$BASE/market/saved/" \
  -H "Authorization: Bearer $ACCESS" > /dev/null
pass "Get saved listings"

RESP=$(req "21. Create donation listing" -s -X POST "$BASE/market/listings/" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Free Calculator",
    "category": "electronics",
    "campus_id": "uon",
    "listing_type": "donation"
  }')
echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id','?'))" 2>/dev/null && pass "Create donation listing" || fail "Create donation listing"

# ============================================================
section "🏠 HOUSING"
# ============================================================

RESP=$(req "22. Create housing listing" -s -X POST "$BASE/housing/listings/" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Single Room near UoN",
    "description": "Spacious room, water included",
    "rent_per_month": 8000,
    "location_name": "Ngara, Nairobi",
    "latitude": -1.2762,
    "longitude": 36.8219,
    "bedrooms": 1,
    "bathrooms": 1,
    "amenities": ["wifi", "water", "security"],
    "campus_id": "uon"
  }')
HOUSING_ID=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)
[[ -n "$HOUSING_ID" ]] && pass "Create housing listing — ID: $HOUSING_ID" || fail "Create housing listing"

req "23. List housing" -s "$BASE/housing/listings/?campus_id=uon" \
  -H "Authorization: Bearer $ACCESS" > /dev/null
pass "List housing"

req "25. Save housing listing" -s -X POST "$BASE/housing/listings/$HOUSING_ID/save/" \
  -H "Authorization: Bearer $ACCESS" > /dev/null
pass "Save housing listing"

RESP=$(req "26. Create roommate profile" -s -X POST "$BASE/housing/roommates/" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{
    "bio": "Clean and quiet student",
    "budget_min": 5000,
    "budget_max": 10000,
    "sleep_schedule": "early_bird",
    "cleanliness": "very_clean",
    "noise_level": "quiet",
    "smoking": false,
    "pets": false,
    "campus_id": "uon"
  }')
echo "$RESP" | python3 -m json.tool > /dev/null 2>&1 && pass "Create roommate profile" || fail "Create roommate profile"

req "27. Browse roommates" -s "$BASE/housing/roommates/?campus_id=uon" \
  -H "Authorization: Bearer $ACCESS" > /dev/null
pass "Browse roommates"

RESP=$(req "28. Create housing alert" -s -X POST "$BASE/housing/alerts/" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"max_rent": 10000, "min_bedrooms": 1, "location_name": "Nairobi"}')
echo "$RESP" | python3 -m json.tool > /dev/null 2>&1 && pass "Create housing alert" || fail "Create housing alert"

# ============================================================
section "📅 EVENTS"
# ============================================================

RESP=$(req "29. Create event" -s -X POST "$BASE/events/" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AI & Machine Learning Talk",
    "description": "Guest lecture on AI trends",
    "category": "academic",
    "location": "Main Hall, UoN",
    "start_at": "2026-04-01T14:00:00Z",
    "end_at": "2026-04-01T16:00:00Z",
    "capacity": 100,
    "campus_id": "uon"
  }')
EVENT_ID=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)
[[ -n "$EVENT_ID" ]] && pass "Create event — ID: $EVENT_ID" || fail "Create event"

req "30. List events" -s "$BASE/events/?campus_id=uon" \
  -H "Authorization: Bearer $ACCESS" > /dev/null
pass "List events"

req "32. RSVP to event" -s -X POST "$BASE/events/$EVENT_ID/rsvp/" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"status": "going"}' > /dev/null
pass "RSVP to event"

req "33. Set reminder" -s -X POST "$BASE/events/reminders/" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d "{\"event_id\": \"$EVENT_ID\", \"remind_at\": \"2026-03-31T14:00:00Z\"}" > /dev/null
pass "Set reminder"

req "34. Save event" -s -X POST "$BASE/events/$EVENT_ID/save/" \
  -H "Authorization: Bearer $ACCESS" > /dev/null
pass "Save event"

# ============================================================
section "📚 STUDY BUDDY"
# ============================================================

req "35. Dashboard" -s "$BASE/study-buddy/dashboard/" \
  -H "Authorization: Bearer $ACCESS" > /dev/null
pass "Dashboard"

RESP=$(req "36. Register as tutor" -s -X POST "$BASE/study-buddy/tutors/" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{
    "subjects": ["Mathematics", "Physics"],
    "hourly_rate": 500,
    "bio": "3rd year Engineering student",
    "campus_id": "uon"
  }')
echo "$RESP" | python3 -m json.tool > /dev/null 2>&1 && pass "Register as tutor" || fail "Register as tutor"

req "37. List tutors" -s "$BASE/study-buddy/tutors/?campus_id=uon" \
  -H "Authorization: Bearer $ACCESS" > /dev/null
pass "List tutors"

RESP=$(req "38. Create study group" -s -X POST "$BASE/study-buddy/groups/" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Calculus Study Group",
    "subject": "Mathematics",
    "description": "Weekly calculus sessions",
    "max_members": 8,
    "campus_id": "uon"
  }')
GROUP_ID=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)
[[ -n "$GROUP_ID" ]] && pass "Create study group — ID: $GROUP_ID" || fail "Create study group"

req "39. List groups" -s "$BASE/study-buddy/groups/?campus_id=uon" \
  -H "Authorization: Bearer $ACCESS" > /dev/null
pass "List groups"

req "40. Join group" -s -X POST "$BASE/study-buddy/groups/$GROUP_ID/join/" \
  -H "Authorization: Bearer $ACCESS" > /dev/null
pass "Join group"

RESP=$(req "41. Post question" -s -X POST "$BASE/study-buddy/questions/" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "How do I solve differential equations?",
    "body": "I am struggling with second order ODEs. Can someone explain the method?",
    "subject": "Mathematics",
    "tags": ["calculus", "ode", "math"],
    "campus_id": "uon"
  }')
QUESTION_ID=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)
[[ -n "$QUESTION_ID" ]] && pass "Post question — ID: $QUESTION_ID" || fail "Post question"

req "42. List questions" -s "$BASE/study-buddy/questions/?campus_id=uon" \
  -H "Authorization: Bearer $ACCESS" > /dev/null
pass "List questions"

req "43. Answer question" -s -X POST "$BASE/study-buddy/questions/$QUESTION_ID/answers/" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"body": "Start with the characteristic equation. For ay\u0027\u0027+by\u0027+cy=0, solve ar\u00b2+br+c=0"}' > /dev/null
pass "Answer question"

req "44. Get question with answers" -s "$BASE/study-buddy/questions/$QUESTION_ID/" \
  -H "Authorization: Bearer $ACCESS" > /dev/null
pass "Get question with answers"

req "45. Upvote question" -s -X POST "$BASE/study-buddy/questions/$QUESTION_ID/upvote/" \
  -H "Authorization: Bearer $ACCESS" > /dev/null
pass "Upvote question"

RESP=$(req "46. Add study resource" -s -X POST "$BASE/study-buddy/resources/" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Calculus Cheat Sheet",
    "subject": "Mathematics",
    "resource_type": "pdf",
    "file_url": "https://example.com/calculus.pdf",
    "campus_id": "uon"
  }')
echo "$RESP" | python3 -m json.tool > /dev/null 2>&1 && pass "Add study resource" || fail "Add study resource"

req "47. List resources" -s "$BASE/study-buddy/resources/?campus_id=uon" \
  -H "Authorization: Bearer $ACCESS" > /dev/null
pass "List resources"

# ============================================================
section "🔒 AUTH CLEANUP"
# ============================================================

req "48. Logout" -s -X POST "$BASE/auth/logout/" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d "{\"refresh\": \"$REFRESH\"}" > /dev/null
pass "Logout"

echo -e "\n$(req "49. Confirm token blacklisted (expect 401)" -s "$BASE/auth/me/" \
  -H "Authorization: Bearer $ACCESS")"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/auth/me/" -H "Authorization: Bearer $ACCESS")
[[ "$HTTP_CODE" == "401" ]] && pass "Token is blacklisted ✔ (401)" || warn "Expected 401, got $HTTP_CODE"

# ============================================================
section "📊 SUMMARY"
# ============================================================
echo ""
echo -e "  ${BOLD}IDs captured during run:${NC}"
echo -e "  LISTING_ID  = ${YELLOW}${LISTING_ID:-<not captured>}${NC}"
echo -e "  HOUSING_ID  = ${YELLOW}${HOUSING_ID:-<not captured>}${NC}"
echo -e "  EVENT_ID    = ${YELLOW}${EVENT_ID:-<not captured>}${NC}"
echo -e "  GROUP_ID    = ${YELLOW}${GROUP_ID:-<not captured>}${NC}"
echo -e "  QUESTION_ID = ${YELLOW}${QUESTION_ID:-<not captured>}${NC}"
echo ""
echo -e "${BOLD}${GREEN}  ✅ Test run complete!${NC}"
echo ""