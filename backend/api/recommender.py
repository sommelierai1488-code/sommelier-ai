"""
Recommendation engine for wine and spirits
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Tuple, Optional
import sys
import os
import math

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_config import DB_CONFIG
from api.models import QuizAnswers, Product, Occasion, Style, DrinkType, Budget


class ProductRecommender:
    """Recommendation engine based on quiz answers"""

    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self):
        """Connect to database"""
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)

    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def get_budget_range(self, budget: Budget) -> Tuple[float, float]:
        """Get price range for budget category"""
        budget_ranges = {
            Budget.LOW: (0, 1000),
            Budget.MEDIUM: (1000, 3000),
            Budget.HIGH: (3000, 7000),
            Budget.PREMIUM: (7000, 100000)
        }
        return budget_ranges.get(budget, (0, 100000))

    def get_category_filters(self, drink_type: DrinkType) -> List[str]:
        """Get category filters based on drink type"""
        category_map = {
            DrinkType.WINE_RED: ["красное", "red"],
            DrinkType.WINE_WHITE: ["белое", "white"],
            DrinkType.WINE_ROSE: ["розовое", "rose", "розе"],
            DrinkType.SPARKLING: ["игристое", "шампанское", "sparkling", "champagne"],
            DrinkType.SPIRITS: ["крепкие", "виски", "коньяк", "водка", "джин", "ром", "whisky", "cognac", "vodka"],
            DrinkType.BEER: ["пиво", "beer"],
            DrinkType.MIXED: []  # No specific filter for mixed
        }
        return category_map.get(drink_type, [])

    def get_abv_range(self, style: Style, drink_type: DrinkType) -> Tuple[float, float]:
        """Get ABV (alcohol by volume) range based on style and drink type"""

        # For spirits, higher ABV
        if drink_type == DrinkType.SPIRITS:
            if style == Style.LIGHT:
                return (30, 40)
            elif style == Style.MODERATE:
                return (35, 45)
            else:  # INTENSE
                return (40, 70)

        # For wines and sparkling
        if style == Style.LIGHT:
            return (0, 12)
        elif style == Style.MODERATE:
            return (11, 14)
        else:  # INTENSE
            return (13, 20)

    def calculate_relevance_score(
        self,
        product: Dict[str, Any],
        quiz: QuizAnswers,
        min_price: float,
        max_price: float
    ) -> float:
        """
        Calculate relevance score for a product based on quiz answers
        Score is between 0 and 1

        Optimized version with better weighting and popularity boost
        """
        score = 0.0
        max_score = 0.0

        # Price relevance (25% weight) - reduced from 30%
        price_weight = 0.25
        max_score += price_weight

        price = float(product.get('price_current', 0)) if product.get('price_current') else 0
        price_range = max_price - min_price
        if price_range > 0 and price > 0:
            # Prefer slightly cheaper items (20% below middle)
            budget_target = (min_price + max_price) / 2 * 0.8
            price_diff = abs(price - budget_target)
            price_score = 1 - (price_diff / (price_range / 2))
            score += max(0, min(1, price_score)) * price_weight

        # ABV relevance (20% weight)
        abv_weight = 0.2
        max_score += abv_weight

        abv = float(product.get('abv_percent')) if product.get('abv_percent') else None
        if abv:
            min_abv, max_abv = self.get_abv_range(quiz.style, quiz.drink_type)
            if min_abv <= abv <= max_abv:
                score += abv_weight
            else:
                # Partial score with softer penalty
                if abv < min_abv:
                    diff = min_abv - abv
                elif abv > max_abv:
                    diff = abv - max_abv
                else:
                    diff = 0

                partial_score = max(0, 1 - (diff / 7))  # 7% tolerance (increased)
                score += partial_score * abv_weight

        # Category match (25% weight) - reduced from 30%
        category_weight = 0.25
        max_score += category_weight

        category = (product.get('category_path') or '').lower()
        filters = self.get_category_filters(quiz.drink_type)

        if filters:
            if any(f in category for f in filters):
                score += category_weight
        else:
            # For mixed type, give partial score
            score += category_weight * 0.5

        # Rating relevance (15% weight) - increased from 10%
        rating_weight = 0.15
        max_score += rating_weight

        rating = float(product.get('rating_value')) if product.get('rating_value') else None
        rating_count = product.get('rating_count') or 0

        if rating and rating > 0:
            # Normalize rating with Wilson score for confidence
            # Products with more reviews get slight boost
            confidence_boost = min(1.0, (rating_count / 50) * 0.2)  # max 20% boost at 50+ reviews
            rating_score = (rating / 5) + confidence_boost
            score += min(1.0, rating_score) * rating_weight
        elif rating_count == 0:
            # New products without ratings get average score
            score += 0.4 * rating_weight

        # Availability (10% weight)
        availability_weight = 0.1
        max_score += availability_weight

        if product.get('availability_status') == 'in_stock':
            score += availability_weight

        # Popularity boost (5% weight) - NEW
        popularity_weight = 0.05
        max_score += popularity_weight

        if rating_count and rating_count > 0:
            # Logarithmic scale for popularity
            popularity_score = min(1.0, math.log(rating_count + 1) / math.log(100))
            score += popularity_score * popularity_weight

        # Normalize score to 0-1 range
        return score / max_score if max_score > 0 else 0

    def get_recommendations(
        self,
        quiz: QuizAnswers,
        limit: int = 10
    ) -> List[Product]:
        """
        Get product recommendations based on quiz answers

        Args:
            quiz: Quiz answers from user
            limit: Maximum number of recommendations to return

        Returns:
            List of recommended products
        """
        try:
            self.connect()

            # Get budget range
            min_price, max_price = self.get_budget_range(quiz.budget)

            # Build query
            query_parts = []
            params = {}

            # Base query
            base_query = """
                SELECT
                    sku, name, price_current, country, producer,
                    volume_l, abv_percent, category_path, image_urls,
                    rating_value, rating_count, availability_status
                FROM products
                WHERE 1=1
            """
            query_parts.append(base_query)

            # Filter by price
            query_parts.append("AND price_current BETWEEN %(min_price)s AND %(max_price)s")
            params['min_price'] = min_price
            params['max_price'] = max_price

            # Filter by availability
            query_parts.append("AND availability_status = 'in_stock'")

            # Filter by drink type using attrs_json->>'Цвет' for wines
            if quiz.drink_type != DrinkType.MIXED:
                if quiz.drink_type == DrinkType.WINE_RED:
                    query_parts.append("AND attrs_json->>'Цвет' = %(color_red)s")
                    params['color_red'] = 'Красное'
                elif quiz.drink_type == DrinkType.WINE_WHITE:
                    query_parts.append("AND (attrs_json->>'Цвет' = %(color_white1)s OR attrs_json->>'Цвет' = %(color_white2)s)")
                    params['color_white1'] = 'Белое'
                    params['color_white2'] = 'Белый'
                elif quiz.drink_type == DrinkType.WINE_ROSE:
                    query_parts.append("AND attrs_json->>'Цвет' = %(color_rose)s")
                    params['color_rose'] = 'Розовое'
                elif quiz.drink_type == DrinkType.SPARKLING:
                    # Use category path for sparkling
                    query_parts.append("AND (LOWER(category_path) LIKE %(sparkling_1)s OR LOWER(category_path) LIKE %(sparkling_2)s)")
                    params['sparkling_1'] = '%игрист%'
                    params['sparkling_2'] = '%шампан%'
                elif quiz.drink_type in [DrinkType.SPIRITS, DrinkType.BEER]:
                    # Use category path for spirits and beer
                    category_filters = self.get_category_filters(quiz.drink_type)
                    if category_filters:
                        category_conditions = []
                        for i, cat_filter in enumerate(category_filters):
                            param_name = f'cat_filter_{i}'
                            category_conditions.append(f"LOWER(category_path) LIKE %(cat_filter_{i})s")
                            params[param_name] = f'%{cat_filter.lower()}%'
                        query_parts.append(f"AND ({' OR '.join(category_conditions)})")

            # Filter by ABV range
            min_abv, max_abv = self.get_abv_range(quiz.style, quiz.drink_type)
            query_parts.append("AND (abv_percent BETWEEN %(min_abv)s AND %(max_abv)s OR abv_percent IS NULL)")
            params['min_abv'] = min_abv
            params['max_abv'] = max_abv

            # Order by relevance factors (initial sort)
            # Prioritize: rating * rating_count (popularity), then price
            query_parts.append("""
                ORDER BY
                    (COALESCE(rating_value, 3.5) * COALESCE(NULLIF(rating_count, 0), 1)) DESC,
                    price_current ASC
                LIMIT %(fetch_limit)s
            """)
            # Fetch more than needed for re-ranking
            params['fetch_limit'] = limit * 5

            # Execute query
            full_query = '\n'.join(query_parts)
            self.cursor.execute(full_query, params)
            products = self.cursor.fetchall()

            # Calculate relevance scores
            scored_products = []
            for product in products:
                score = self.calculate_relevance_score(
                    product,
                    quiz,
                    min_price,
                    max_price
                )

                # Create Product model
                product_obj = Product(
                    sku=product['sku'],
                    name=product['name'],
                    price_current=float(product['price_current']) if product['price_current'] else 0,
                    country=product.get('country'),
                    producer=product.get('producer'),
                    volume_l=float(product['volume_l']) if product.get('volume_l') else None,
                    abv_percent=float(product['abv_percent']) if product.get('abv_percent') else None,
                    category_path=product.get('category_path'),
                    image_urls=product.get('image_urls', []),
                    rating_value=float(product['rating_value']) if product.get('rating_value') else None,
                    rating_count=product.get('rating_count'),
                    relevance_score=score
                )
                scored_products.append(product_obj)

            # Sort by relevance score and return top N
            scored_products.sort(key=lambda p: p.relevance_score, reverse=True)

            return scored_products[:limit]

        finally:
            self.close()

    def get_diverse_recommendations(
        self,
        quiz: QuizAnswers,
        limit: int = 10
    ) -> List[Product]:
        """
        Get diverse recommendations (different producers, countries, price ranges)
        This ensures variety in the recommendations with better distribution
        """
        all_recommendations = self.get_recommendations(quiz, limit * 3)

        if not all_recommendations:
            return []

        # Ensure diversity across multiple dimensions
        diverse_products = []
        used_producers = {}  # producer -> count
        used_countries = {}  # country -> count
        used_price_ranges = {}  # price_range -> count

        def get_price_range(price):
            """Categorize price into ranges"""
            if price < 500:
                return "budget"
            elif price < 1500:
                return "mid-low"
            elif price < 3000:
                return "mid-high"
            else:
                return "premium"

        def calculate_diversity_penalty(product):
            """Calculate penalty for overused dimensions"""
            penalty = 0
            producer_count = used_producers.get(product.producer, 0)
            country_count = used_countries.get(product.country, 0)
            price_range_count = used_price_ranges.get(get_price_range(product.price_current), 0)

            # Exponential penalty for repeated dimensions
            penalty += producer_count * 0.15
            penalty += country_count * 0.10
            penalty += price_range_count * 0.05

            return penalty

        # Greedy selection with diversity penalty
        remaining = all_recommendations.copy()

        while len(diverse_products) < limit and remaining:
            # Find best product considering diversity
            best_product = None
            best_score = -float('inf')

            for product in remaining:
                diversity_penalty = calculate_diversity_penalty(product)
                adjusted_score = product.relevance_score - diversity_penalty

                if adjusted_score > best_score:
                    best_score = adjusted_score
                    best_product = product

            if best_product:
                diverse_products.append(best_product)
                remaining.remove(best_product)

                # Update diversity tracking
                used_producers[best_product.producer] = used_producers.get(best_product.producer, 0) + 1
                if best_product.country:
                    used_countries[best_product.country] = used_countries.get(best_product.country, 0) + 1
                price_range = get_price_range(best_product.price_current)
                used_price_ranges[price_range] = used_price_ranges.get(price_range, 0) + 1
            else:
                break

        return diverse_products

    def get_similar_products(
        self,
        sku: str,
        limit: int = 6
    ) -> List[Product]:
        """
        Get similar products based on attributes (grape variety, country, producer, style)
        Useful for "you might also like" recommendations
        """
        try:
            self.connect()

            # First, get the source product
            self.cursor.execute("""
                SELECT
                    sku, name, price_current, country, producer,
                    volume_l, abv_percent, category_path, image_urls,
                    rating_value, rating_count, availability_status,
                    attrs_json, brand
                FROM products
                WHERE sku = %s
            """, (sku,))

            source_product = self.cursor.fetchone()
            if not source_product:
                return []

            # Extract key attributes
            source_attrs = source_product.get('attrs_json', {}) or {}
            source_grape = source_attrs.get('Сорт винограда', '')
            source_color = source_attrs.get('Цвет', '')
            source_sugar = source_attrs.get('Содержание сахара', '')
            source_country = source_product.get('country')
            source_producer = source_product.get('producer')
            source_price = float(source_product.get('price_current', 0))

            # Build similarity query
            query = """
                SELECT
                    sku, name, price_current, country, producer,
                    volume_l, abv_percent, category_path, image_urls,
                    rating_value, rating_count, availability_status,
                    attrs_json,
                    -- Similarity scoring
                    (
                        CASE WHEN attrs_json->>'Сорт винограда' = %(grape)s THEN 3 ELSE 0 END +
                        CASE WHEN attrs_json->>'Цвет' = %(color)s THEN 2 ELSE 0 END +
                        CASE WHEN attrs_json->>'Содержание сахара' = %(sugar)s THEN 1 ELSE 0 END +
                        CASE WHEN country = %(country)s THEN 2 ELSE 0 END +
                        CASE WHEN producer = %(producer)s THEN 1 ELSE 0 END +
                        CASE WHEN ABS(price_current - %(price)s) < 500 THEN 1 ELSE 0 END
                    ) as similarity_score
                FROM products
                WHERE sku != %(sku)s
                    AND availability_status = 'in_stock'
                    AND (
                        attrs_json->>'Сорт винограда' = %(grape)s
                        OR attrs_json->>'Цвет' = %(color)s
                        OR country = %(country)s
                        OR producer = %(producer)s
                    )
                ORDER BY
                    similarity_score DESC,
                    COALESCE(rating_value, 0) DESC,
                    ABS(price_current - %(price)s) ASC
                LIMIT %(limit)s
            """

            self.cursor.execute(query, {
                'sku': sku,
                'grape': source_grape,
                'color': source_color,
                'sugar': source_sugar,
                'country': source_country,
                'producer': source_producer,
                'price': source_price,
                'limit': limit
            })

            products = self.cursor.fetchall()

            # Convert to Product models
            similar_products = []
            for product in products:
                product_obj = Product(
                    sku=product['sku'],
                    name=product['name'],
                    price_current=float(product['price_current']) if product['price_current'] else 0,
                    country=product.get('country'),
                    producer=product.get('producer'),
                    volume_l=float(product['volume_l']) if product.get('volume_l') else None,
                    abv_percent=float(product['abv_percent']) if product.get('abv_percent') else None,
                    category_path=product.get('category_path'),
                    image_urls=product.get('image_urls', []),
                    rating_value=float(product['rating_value']) if product.get('rating_value') else None,
                    rating_count=product.get('rating_count'),
                    relevance_score=0.0  # Not used for similar products
                )
                similar_products.append(product_obj)

            return similar_products

        finally:
            self.close()

    def get_trending_products(
        self,
        drink_type: Optional[DrinkType] = None,
        limit: int = 10
    ) -> List[Product]:
        """
        Get trending/popular products based on ratings and popularity
        Can be filtered by drink type
        """
        try:
            self.connect()

            # Build query for trending products
            query_parts = ["""
                SELECT
                    sku, name, price_current, country, producer,
                    volume_l, abv_percent, category_path, image_urls,
                    rating_value, rating_count, availability_status,
                    -- Trending score: rating * log(review_count) for popularity
                    (COALESCE(rating_value, 3.0) * LOG(COALESCE(NULLIF(rating_count, 0), 1) + 10)) as trending_score
                FROM products
                WHERE availability_status = 'in_stock'
                    AND rating_count > 0
            """]

            params = {'limit': limit}

            # Filter by drink type if specified
            if drink_type and drink_type != DrinkType.MIXED:
                if drink_type == DrinkType.WINE_RED:
                    query_parts.append("AND attrs_json->>'Цвет' = 'Красное'")
                elif drink_type == DrinkType.WINE_WHITE:
                    query_parts.append("AND (attrs_json->>'Цвет' = 'Белое' OR attrs_json->>'Цвет' = 'Белый')")
                elif drink_type == DrinkType.WINE_ROSE:
                    query_parts.append("AND attrs_json->>'Цвет' = 'Розовое'")
                elif drink_type == DrinkType.SPARKLING:
                    query_parts.append("AND (LOWER(category_path) LIKE '%игрист%' OR LOWER(category_path) LIKE '%шампан%')")

            query_parts.append("""
                ORDER BY trending_score DESC
                LIMIT %(limit)s
            """)

            full_query = '\n'.join(query_parts)
            self.cursor.execute(full_query, params)
            products = self.cursor.fetchall()

            # Convert to Product models
            trending_products = []
            for product in products:
                product_obj = Product(
                    sku=product['sku'],
                    name=product['name'],
                    price_current=float(product['price_current']) if product['price_current'] else 0,
                    country=product.get('country'),
                    producer=product.get('producer'),
                    volume_l=float(product['volume_l']) if product.get('volume_l') else None,
                    abv_percent=float(product['abv_percent']) if product.get('abv_percent') else None,
                    category_path=product.get('category_path'),
                    image_urls=product.get('image_urls', []),
                    rating_value=float(product['rating_value']) if product.get('rating_value') else None,
                    rating_count=product.get('rating_count'),
                    relevance_score=0.0  # Not used for trending
                )
                trending_products.append(product_obj)

            return trending_products

        finally:
            self.close()
