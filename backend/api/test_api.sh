#!/bin/bash
# Test script for AmWine Recommendations API

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_URL="http://localhost:8000"

echo -e "${YELLOW}Testing AmWine Recommendations API${NC}"
echo "=================================="
echo ""

# Test 1: Health check
echo -e "${YELLOW}Test 1: Health check (GET /)${NC}"
response=$(curl -s -w "\n%{http_code}" "$API_URL/")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 200 ]; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    echo "Response: $body"
else
    echo -e "${RED}✗ Health check failed (HTTP $http_code)${NC}"
fi
echo ""

# Test 2: Recommendations endpoint
echo -e "${YELLOW}Test 2: Get recommendations (POST /offers/recommend)${NC}"
response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/offers/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "occasion": "🎉 Вечеринка",
    "style": "🌤 Легко и мягко",
    "drink_types": ["🍷 Вино / игристое", "🍺 Пиво / сидр"],
    "tastes": ["🍑 Фруктовое / ароматное", "🍬 Сладковатое"],
    "people_count": 6,
    "budget": "💰 1000–3000 ₽"
  }')

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 200 ]; then
    echo -e "${GREEN}✓ Recommendations request successful${NC}"
    # Pretty print JSON response
    echo "$body" | python -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "${RED}✗ Recommendations request failed (HTTP $http_code)${NC}"
    echo "Response: $body"
fi
echo ""

echo "=================================="
echo -e "${YELLOW}Tests completed${NC}"
