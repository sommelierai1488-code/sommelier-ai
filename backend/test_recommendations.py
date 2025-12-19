"""
Test script for optimized recommendation engine
"""
from api.recommender import ProductRecommender
from api.models import QuizAnswers, DrinkType, Occasion, Style, Budget


def print_products(products, title):
    """Print products in a nice format"""
    print("\n" + "=" * 80)
    print(f"{title}")
    print("=" * 80)

    if not products:
        print("No products found")
        return

    for i, product in enumerate(products, 1):
        print(f"\n{i}. {product.name}")
        print(f"   SKU: {product.sku}")
        print(f"   Price: {product.price_current:.2f} ₽")
        print(f"   Country: {product.country}")
        print(f"   Producer: {product.producer}")
        if product.abv_percent:
            print(f"   ABV: {product.abv_percent}%")
        if product.rating_value:
            print(f"   Rating: {product.rating_value:.1f}/5 ({product.rating_count} reviews)")
        if hasattr(product, 'relevance_score') and product.relevance_score > 0:
            print(f"   Relevance: {product.relevance_score:.3f}")


def test_recommendations():
    """Test personalized recommendations"""
    print("\n🍷 TESTING OPTIMIZED RECOMMENDATION ENGINE 🍷")

    recommender = ProductRecommender()

    # Test 1: Red wine for romantic dinner, moderate style, medium budget
    print("\n\n📋 TEST 1: Red Wine Recommendations")
    quiz1 = QuizAnswers(
        drink_type=DrinkType.WINE_RED,
        occasion=Occasion.ROMANTIC,
        style=Style.MODERATE,
        budget=Budget.MEDIUM,
        people_count=2
    )

    recommendations1 = recommender.get_recommendations(quiz1, limit=5)
    print_products(recommendations1, "Top 5 Red Wine Recommendations (Medium Budget)")

    # Test 2: Diverse recommendations
    print("\n\n📋 TEST 2: Diverse Red Wine Recommendations")
    diverse1 = recommender.get_diverse_recommendations(quiz1, limit=5)
    print_products(diverse1, "Top 5 Diverse Red Wine Recommendations")

    # Test 3: White wine for party, light style, low budget
    print("\n\n📋 TEST 3: White Wine Recommendations")
    quiz2 = QuizAnswers(
        drink_type=DrinkType.WINE_WHITE,
        occasion=Occasion.PARTY,
        style=Style.LIGHT,
        budget=Budget.LOW,
        people_count=6
    )

    recommendations2 = recommender.get_recommendations(quiz2, limit=5)
    print_products(recommendations2, "Top 5 White Wine Recommendations (Low Budget)")

    # Test 4: Similar products
    print("\n\n📋 TEST 4: Similar Products")
    if recommendations1:
        sku = recommendations1[0].sku
        similar = recommender.get_similar_products(sku, limit=4)
        print_products(similar, f"Products Similar to {recommendations1[0].name}")

    # Test 5: Trending products
    print("\n\n📋 TEST 5: Trending Products")
    trending = recommender.get_trending_products(drink_type=DrinkType.WINE_RED, limit=5)
    print_products(trending, "Top 5 Trending Red Wines")

    # Test 6: Spirits for gift, premium budget
    print("\n\n📋 TEST 6: Premium Spirits")
    quiz3 = QuizAnswers(
        drink_type=DrinkType.SPIRITS,
        occasion=Occasion.GIFT,
        style=Style.INTENSE,
        budget=Budget.PREMIUM,
        people_count=1
    )

    recommendations3 = recommender.get_recommendations(quiz3, limit=5)
    print_products(recommendations3, "Top 5 Premium Spirits")

    print("\n\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == '__main__':
    try:
        test_recommendations()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
