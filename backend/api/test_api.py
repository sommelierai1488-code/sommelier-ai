"""
Test script for recommendation API
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models import QuizAnswers, Occasion, Style, DrinkType, Budget
from api.recommender import ProductRecommender


def test_recommender():
    """Test the recommendation engine"""
    print("=" * 60)
    print("Testing Recommendation Engine")
    print("=" * 60)

    # Test case 1: Party with moderate style, red wine
    print("\nTest Case 1: Party - Moderate - Red Wine - 4 people - Medium budget")
    print("-" * 60)

    quiz1 = QuizAnswers(
        occasion=Occasion.PARTY,
        style=Style.MODERATE,
        drink_type=DrinkType.WINE_RED,
        people_count=4,
        budget=Budget.MEDIUM
    )

    recommender = ProductRecommender()
    products1 = recommender.get_diverse_recommendations(quiz1, limit=10)

    print(f"Found {len(products1)} products")
    print(f"\nTop 5 recommendations:")
    for i, product in enumerate(products1[:5], 1):
        print(f"\n{i}. {product.name}")
        print(f"   SKU: {product.sku}")
        print(f"   Price: {product.price_current} руб")
        print(f"   Country: {product.country}")
        print(f"   Producer: {product.producer}")
        print(f"   ABV: {product.abv_percent}%")
        print(f"   Relevance Score: {product.relevance_score:.2f}")

    total_price1 = sum(p.price_current for p in products1)
    print(f"\nTotal price for all 10 products: {total_price1:.2f} руб")

    # Test case 2: Romantic evening with light style, sparkling
    print("\n" + "=" * 60)
    print("\nTest Case 2: Romantic - Light - Sparkling - 2 people - High budget")
    print("-" * 60)

    quiz2 = QuizAnswers(
        occasion=Occasion.ROMANTIC,
        style=Style.LIGHT,
        drink_type=DrinkType.SPARKLING,
        people_count=2,
        budget=Budget.HIGH
    )

    products2 = recommender.get_diverse_recommendations(quiz2, limit=10)

    print(f"Found {len(products2)} products")
    print(f"\nTop 5 recommendations:")
    for i, product in enumerate(products2[:5], 1):
        print(f"\n{i}. {product.name}")
        print(f"   Price: {product.price_current} руб")
        print(f"   Country: {product.country}")
        print(f"   ABV: {product.abv_percent}%")
        print(f"   Relevance Score: {product.relevance_score:.2f}")

    total_price2 = sum(p.price_current for p in products2)
    print(f"\nTotal price for all 10 products: {total_price2:.2f} руб")

    # Test case 3: Celebration with intense style, mixed
    print("\n" + "=" * 60)
    print("\nTest Case 3: Celebration - Intense - Mixed - 10 people - Premium budget")
    print("-" * 60)

    quiz3 = QuizAnswers(
        occasion=Occasion.CELEBRATION,
        style=Style.INTENSE,
        drink_type=DrinkType.MIXED,
        people_count=10,
        budget=Budget.PREMIUM
    )

    products3 = recommender.get_diverse_recommendations(quiz3, limit=10)

    print(f"Found {len(products3)} products")
    print(f"\nTop 5 recommendations:")
    for i, product in enumerate(products3[:5], 1):
        print(f"\n{i}. {product.name}")
        print(f"   Price: {product.price_current} руб")
        print(f"   Country: {product.country}")
        print(f"   Category: {product.category_path}")
        print(f"   Relevance Score: {product.relevance_score:.2f}")

    total_price3 = sum(p.price_current for p in products3)
    print(f"\nTotal price for all 10 products: {total_price3:.2f} руб")

    print("\n" + "=" * 60)
    print("Testing completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_recommender()
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
