"""
Recommendation engine for wine and spirits
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Tuple, Optional
import sys
import os
import math
import uuid
import statistics
from collections import Counter
from typing import Union

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_config import DB_CONFIG
from api.models import QuizAnswers, Product, Occasion, Style, DrinkType, Budget


DEFAULT_WEIGHTS = {
    "price": 0.25,
    "abv": 0.2,
    "category": 0.2,
    "rating": 0.2,
    "popularity": 0.05,
    "behavior": 0.1
}

DIVERSITY_PENALTIES = {
    "producer": 0.15,
    "country": 0.1,
    "price_range": 0.05
}

TARGET_CART_ITEMS = 6  # heuristic target size, not tied to people_count

SessionId = Union[str, uuid.UUID]
UserId = Union[int, str, uuid.UUID]


class ProductRecommender:
    """Recommendation engine based on quiz answers"""

    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self):
        """Connect to database"""
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)

    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def get_budget_range(self, budget: Budget) -> Tuple[float, float]:
        """Get price range for budget bucket (interpreted as total session budget band)."""
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

    def _to_product_model(self, product: Dict[str, Any], score: float = 0.0) -> Product:
        return Product(
            sku=product['sku'],
            name=product['name'],
            price_current=float(product['price_current']) if product.get('price_current') else 0,
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

    def _fetch_session_quiz(self, session_id: SessionId) -> Optional[Dict[str, Any]]:
        self.cursor.execute(
            """
            select session_id, occasion, style, drink_type, taste, people_count, budget_bucket
            from session_quiz
            where session_id = %(session_id)s
            """,
            {"session_id": session_id}
        )
        return self.cursor.fetchone()

    def _hydrate_quiz_answers(self, quiz_row: Dict[str, Any]) -> QuizAnswers:
        return QuizAnswers(
            occasion=Occasion(quiz_row["occasion"]),
            style=Style(quiz_row["style"]),
            drink_type=DrinkType(quiz_row["drink_type"]),
            people_count=int(quiz_row["people_count"]),
            budget=Budget(quiz_row["budget_bucket"]),
        )

    def _fetch_liked(self, session_id: SessionId) -> List[Dict[str, Any]]:
        """Fetch liked products with attributes for session."""
        self.cursor.execute(
            """
            select p.*, se.action
            from session_events se
            join products p on p.sku = se.sku
            where se.session_id = %(session_id)s and se.action = 'like'
            """,
            {"session_id": session_id}
        )
        return self.cursor.fetchall() or []

    def _build_preferences(self, liked_products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simple preference profile inferred from likes."""
        countries = Counter()
        producers = Counter()
        colors = Counter()
        grapes = Counter()
        sugars = Counter()
        prices = []
        abvs = []

        for product in liked_products:
            if product.get("country"):
                countries[product["country"]] += 1
            if product.get("producer"):
                producers[product["producer"]] += 1
            attrs = product.get("attrs_json") or {}
            color = attrs.get("Цвет")
            grape = attrs.get("Сорт винограда")
            sugar = attrs.get("Содержание сахара")
            if color:
                colors[color] += 1
            if grape:
                grapes[grape] += 1
            if sugar:
                sugars[sugar] += 1
            if product.get("price_current") is not None:
                try:
                    prices.append(float(product["price_current"]))
                except (TypeError, ValueError):
                    pass
            if product.get("abv_percent") is not None:
                try:
                    abvs.append(float(product["abv_percent"]))
                except (TypeError, ValueError):
                    pass

        def top_keys(counter: Counter, n: int = 2) -> set:
            return {item for item, _ in counter.most_common(n)}

        preferences = {
            "top_countries": top_keys(countries),
            "top_producers": top_keys(producers),
            "colors": top_keys(colors),
            "grapes": top_keys(grapes),
            "sugars": top_keys(sugars),
            "price_median": statistics.median(prices) if prices else None,
            "abv_median": statistics.median(abvs) if abvs else None,
        }
        return preferences

    def _fetch_candidates(
        self,
        session_id: SessionId,
        quiz: QuizAnswers,
        abv_range: Tuple[float, float],
        fetch_limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch candidate products excluding already shown (including disliked)."""
        # candidate pool is computed dynamically from products
        # minus shown sku from session_events
        # no persistent pool storage by design (mvp)
        filters = []
        params: Dict[str, Any] = {
            "session_id": session_id,
            "min_abv": abv_range[0],
            "max_abv": abv_range[1],
            "limit": fetch_limit
        }

        filters.append("p.availability_status = 'in_stock'")
        filters.append("p.price_current is not null")
        filters.append("p.price_current > 0")
        filters.append("(p.abv_percent between %(min_abv)s and %(max_abv)s or p.abv_percent is null)")
        filters.append(
            "not exists (select 1 from session_events se where se.session_id = %(session_id)s and se.sku = p.sku)"
        )

        if quiz.drink_type != DrinkType.MIXED:
            if quiz.drink_type == DrinkType.WINE_RED:
                filters.append("p.attrs_json->>'Цвет' = %(color_red)s")
                params["color_red"] = "Красное"
            elif quiz.drink_type == DrinkType.WINE_WHITE:
                filters.append("(p.attrs_json->>'Цвет' = %(color_white1)s or p.attrs_json->>'Цвет' = %(color_white2)s)")
                params["color_white1"] = "Белое"
                params["color_white2"] = "Белый"
            elif quiz.drink_type == DrinkType.WINE_ROSE:
                filters.append("p.attrs_json->>'Цвет' = %(color_rose)s")
                params["color_rose"] = "Розовое"
            elif quiz.drink_type == DrinkType.SPARKLING:
                filters.append("(lower(p.category_path) like %(sparkling_1)s or lower(p.category_path) like %(sparkling_2)s)")
                params["sparkling_1"] = "%игрист%"
                params["sparkling_2"] = "%шампан%"
            elif quiz.drink_type in [DrinkType.SPIRITS, DrinkType.BEER]:
                category_filters = self.get_category_filters(quiz.drink_type)
                if category_filters:
                    category_conditions = []
                    for i, cat_filter in enumerate(category_filters):
                        param_name = f"cat_filter_{i}"
                        category_conditions.append(f"lower(p.category_path) like %({param_name})s")
                        params[param_name] = f"%{cat_filter.lower()}%"
                    filters.append("(" + " or ".join(category_conditions) + ")")

        # Index note: session_events(session_id, sku), session_cart(session_id), products(availability_status, price_current, attrs_json gin).
        where_clause = " and ".join(filters)
        query = f"""
            select
                p.sku, p.name, p.price_current, p.country, p.producer,
                p.volume_l, p.abv_percent, p.category_path, p.image_urls,
                p.rating_value, p.rating_count, p.availability_status, p.attrs_json
            from products p
            where {where_clause}
            order by coalesce(p.rating_value, 3.5) desc,
                     coalesce(p.rating_count, 0) desc,
                     p.price_current asc
            limit %(limit)s
        """
        self.cursor.execute(query, params)
        return self.cursor.fetchall() or []

    def _calculate_session_score(
        self,
        product: Dict[str, Any],
        quiz: QuizAnswers,
        weights: Dict[str, float],
        price_target: float,
        target_window: float,
        abv_range: Tuple[float, float],
        category_filters: List[str],
        preferences: Dict[str, Any]
    ) -> float:
        score = 0.0
        total_weight = 0.0

        price_weight = weights.get("price", 0)
        total_weight += price_weight
        price = float(product.get("price_current", 0) or 0)
        if price > 0 and price_weight > 0:
            denom = max(price_target * 0.5, target_window, 1)
            price_score = 1 - min(1, abs(price - price_target) / denom)
            score += price_score * price_weight

        abv_weight = weights.get("abv", 0)
        total_weight += abv_weight
        abv = float(product.get("abv_percent")) if product.get("abv_percent") is not None else None
        if abv is not None and abv_weight > 0:
            min_abv, max_abv = abv_range
            if min_abv <= abv <= max_abv:
                score += abv_weight
            else:
                diff = min(abs(abv - min_abv), abs(abv - max_abv))
                partial_score = max(0, 1 - (diff / 7))
                score += partial_score * abv_weight

        category_weight = weights.get("category", 0)
        total_weight += category_weight
        category_path = (product.get("category_path") or "").lower()
        attrs = product.get("attrs_json") or {}
        if quiz.drink_type in {DrinkType.WINE_RED, DrinkType.WINE_WHITE, DrinkType.WINE_ROSE}:
            expected_color = {
                DrinkType.WINE_RED: "Красное",
                DrinkType.WINE_WHITE: "Белое",
                DrinkType.WINE_ROSE: "Розовое"
            }
            if attrs.get("Цвет") == expected_color.get(quiz.drink_type):
                score += category_weight
            elif category_filters and any(token in category_path for token in category_filters):
                score += category_weight * 0.5
        else:
            if category_filters:
                if any(token in category_path for token in category_filters):
                    score += category_weight
            else:
                score += category_weight * 0.5

        rating_weight = weights.get("rating", 0)
        total_weight += rating_weight
        rating = float(product.get("rating_value")) if product.get("rating_value") else None
        rating_count = product.get("rating_count") or 0
        if rating and rating_weight > 0:
            confidence_boost = min(1.0, (rating_count / 50) * 0.2)
            rating_score = min(1.0, (rating / 5) + confidence_boost)
            score += rating_score * rating_weight
        elif rating_weight > 0:
            score += 0.4 * rating_weight

        popularity_weight = weights.get("popularity", 0)
        total_weight += popularity_weight
        if rating_count and popularity_weight > 0:
            popularity_score = min(1.0, math.log(rating_count + 1) / math.log(100))
            score += popularity_score * popularity_weight

        behavior_weight = weights.get("behavior", 0)
        total_weight += behavior_weight
        if behavior_weight > 0:
            behavior_score = 0.0
            if product.get("country") and product["country"] in preferences.get("top_countries", set()):
                behavior_score += 0.3
            if product.get("producer") and product["producer"] in preferences.get("top_producers", set()):
                behavior_score += 0.2
            attrs = product.get("attrs_json") or {}
            if attrs.get("Цвет") in preferences.get("colors", set()):
                behavior_score += 0.15
            if attrs.get("Сорт винограда") in preferences.get("grapes", set()):
                behavior_score += 0.1
            if attrs.get("Содержание сахара") in preferences.get("sugars", set()):
                behavior_score += 0.05
            median_price = preferences.get("price_median")
            if median_price:
                denom = max(median_price * 0.5, 300)
                behavior_score += max(0, 1 - min(1, abs(price - median_price) / denom)) * 0.2
            median_abv = preferences.get("abv_median")
            if median_abv is not None:
                behavior_score += max(0, 1 - min(1, abs((abv or 0) - median_abv) / 5)) * 0.1
            score += min(1.0, behavior_score) * behavior_weight

        return score / total_weight if total_weight > 0 else 0

    def _diversity_select(self, products: List[Product], limit: int, penalty_scale: float = 1.0) -> List[Product]:
        """Greedy selection with diversity penalties by producer/country/price range."""
        if not products:
            return []
        diverse_products: List[Product] = []
        used_producers: Dict[str, int] = {}
        used_countries: Dict[str, int] = {}
        used_price_ranges: Dict[str, int] = {}

        def price_range(price: float) -> str:
            if price < 500:
                return "budget"
            if price < 1500:
                return "mid-low"
            if price < 3000:
                return "mid-high"
            return "premium"

        remaining = products.copy()
        while len(diverse_products) < limit and remaining:
            best_product = None
            best_score = -float("inf")
            for candidate in remaining:
                penalty = 0.0
                penalty += used_producers.get(candidate.producer, 0) * DIVERSITY_PENALTIES["producer"] * penalty_scale
                if candidate.country:
                    penalty += used_countries.get(candidate.country, 0) * DIVERSITY_PENALTIES["country"] * penalty_scale
                pr = price_range(candidate.price_current)
                penalty += used_price_ranges.get(pr, 0) * DIVERSITY_PENALTIES["price_range"] * penalty_scale
                adjusted = candidate.relevance_score - penalty
                if adjusted > best_score:
                    best_score = adjusted
                    best_product = candidate
            if best_product:
                diverse_products.append(best_product)
                remaining.remove(best_product)
                used_producers[best_product.producer] = used_producers.get(best_product.producer, 0) + 1
                if best_product.country:
                    used_countries[best_product.country] = used_countries.get(best_product.country, 0) + 1
                chosen_range = price_range(best_product.price_current)
                used_price_ranges[chosen_range] = used_price_ranges.get(chosen_range, 0) + 1
            else:
                break
        return diverse_products

    def _log_impressions(self, session_id: SessionId, skus: List[str]) -> None:
        if not skus:
            return
        events = [{"session_id": session_id, "sku": sku} for sku in skus]
        self.cursor.executemany(
            """
            insert into session_events (session_id, sku, action, created_at)
            values (%(session_id)s, %(sku)s, null, now())
            on conflict (session_id, sku)
            do nothing
            """,
            events
        )

    def _get_cart_totals(self, session_id: SessionId) -> Dict[str, float]:
        self.cursor.execute(
            """
            select coalesce(sum(qty * price_at_add), 0) as cart_total,
                   count(distinct sku) as distinct_items
            from session_cart
            where session_id = %(session_id)s
            """,
            {"session_id": session_id}
        )
        row = self.cursor.fetchone() or {"cart_total": 0, "distinct_items": 0}
        cart_total = float(row.get("cart_total") or 0)
        distinct_items = int(row.get("distinct_items") or 0)
        return {"cart_total": cart_total, "distinct_items": distinct_items}

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
        Deprecated legacy stateless recommendations based on quiz answers.
        Prefer get_feed for stateful flow.

        Args:
            quiz: Quiz answers from user
            limit: Maximum number of recommendations to return

        Returns:
            List of recommended products
        """
        try:
            self.connect()

            min_price, max_price = self.get_budget_range(quiz.budget)

            query_parts = []
            params = {}

            base_query = """
                select
                    sku, name, price_current, country, producer,
                    volume_l, abv_percent, category_path, image_urls,
                    rating_value, rating_count, availability_status
                from products
                where 1=1
            """
            query_parts.append(base_query)

            query_parts.append("and price_current between %(min_price)s and %(max_price)s")
            params["min_price"] = min_price
            params["max_price"] = max_price

            query_parts.append("and availability_status = 'in_stock'")

            if quiz.drink_type != DrinkType.MIXED:
                if quiz.drink_type == DrinkType.WINE_RED:
                    query_parts.append("and attrs_json->>'Цвет' = %(color_red)s")
                    params["color_red"] = "Красное"
                elif quiz.drink_type == DrinkType.WINE_WHITE:
                    query_parts.append("and (attrs_json->>'Цвет' = %(color_white1)s or attrs_json->>'Цвет' = %(color_white2)s)")
                    params["color_white1"] = "Белое"
                    params["color_white2"] = "Белый"
                elif quiz.drink_type == DrinkType.WINE_ROSE:
                    query_parts.append("and attrs_json->>'Цвет' = %(color_rose)s")
                    params["color_rose"] = "Розовое"
                elif quiz.drink_type == DrinkType.SPARKLING:
                    query_parts.append("and (lower(category_path) like %(sparkling_1)s or lower(category_path) like %(sparkling_2)s)")
                    params["sparkling_1"] = "%игрист%"
                    params["sparkling_2"] = "%шампан%"
                elif quiz.drink_type in [DrinkType.SPIRITS, DrinkType.BEER]:
                    category_filters = self.get_category_filters(quiz.drink_type)
                    if category_filters:
                        category_conditions = []
                        for i, cat_filter in enumerate(category_filters):
                            param_name = f"cat_filter_{i}"
                            category_conditions.append(f"lower(category_path) like %({param_name})s")
                            params[param_name] = f"%{cat_filter.lower()}%"
                        query_parts.append(f"and ({' or '.join(category_conditions)})")

            min_abv, max_abv = self.get_abv_range(quiz.style, quiz.drink_type)
            query_parts.append("and (abv_percent between %(min_abv)s and %(max_abv)s or abv_percent is null)")
            params["min_abv"] = min_abv
            params["max_abv"] = max_abv

            query_parts.append("""
                order by
                    (coalesce(rating_value, 3.5) * coalesce(nullif(rating_count, 0), 1)) desc,
                    price_current asc
                limit %(fetch_limit)s
            """)
            params["fetch_limit"] = limit * 5

            full_query = "\n".join(query_parts)
            self.cursor.execute(full_query, params)
            products = self.cursor.fetchall()

            scored_products = []
            for product in products:
                score = self.calculate_relevance_score(
                    product,
                    quiz,
                    min_price,
                    max_price
                )

                product_obj = Product(
                    sku=product["sku"],
                    name=product["name"],
                    price_current=float(product["price_current"]) if product["price_current"] else 0,
                    country=product.get("country"),
                    producer=product.get("producer"),
                    volume_l=float(product["volume_l"]) if product.get("volume_l") else None,
                    abv_percent=float(product["abv_percent"]) if product.get("abv_percent") else None,
                    category_path=product.get("category_path"),
                    image_urls=product.get("image_urls", []),
                    rating_value=float(product["rating_value"]) if product.get("rating_value") else None,
                    rating_count=product.get("rating_count"),
                    relevance_score=score
                )
                scored_products.append(product_obj)

            scored_products.sort(key=lambda p: p.relevance_score, reverse=True)
            return scored_products[:limit]

        finally:
            self.close()

    def create_session(self, user_id: Optional[UserId] = None) -> SessionId:
        """
        Create a session for recsys flow with status in_progress.
        """
        try:
            self.connect()
            self.cursor.execute(
                """
                insert into sessions (user_id, status)
                values (%(user_id)s, 'in_progress')
                returning session_id
                """,
                {"user_id": user_id}
            )
            session_id = self.cursor.fetchone()["session_id"]
            self.conn.commit()
            return session_id
        except Exception:
            if self.conn:
                self.conn.rollback()
            raise
        finally:
            self.close()

    def upsert_quiz(self, session_id: SessionId, quiz: QuizAnswers) -> None:
        """Persist quiz answers for the session."""
        try:
            self.connect()
            params = {
                "session_id": session_id,
                "occasion": quiz.occasion.value,
                "style": quiz.style.value,
                "drink_type": quiz.drink_type.value,
                "taste": None,
                "people_count": quiz.people_count,
                "budget_bucket": quiz.budget.value,
            }
            self.cursor.execute(
                """
                insert into session_quiz (session_id, occasion, style, drink_type, taste, people_count, budget_bucket, created_at)
                values (%(session_id)s, %(occasion)s, %(style)s, %(drink_type)s, %(taste)s, %(people_count)s, %(budget_bucket)s, now())
                on conflict (session_id) do update
                set occasion = excluded.occasion,
                    style = excluded.style,
                    drink_type = excluded.drink_type,
                    taste = excluded.taste,
                    people_count = excluded.people_count,
                    budget_bucket = excluded.budget_bucket
                """,
                params
            )
            self.cursor.execute(
                "update sessions set updated_at = now() where session_id = %(session_id)s",
                {"session_id": session_id}
            )
            self.conn.commit()
        except Exception:
            if self.conn:
                self.conn.rollback()
            raise
        finally:
            self.close()

    def get_feed(
        self,
        session_id: SessionId,
        page_size: int = 10,
        weights_override: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Stateful feed with impressions logging and budget/cart context.
        """
        try:
            self.connect()
            quiz_row = self._fetch_session_quiz(session_id)
            if not quiz_row:
                raise ValueError("quiz answers not found for session")
            quiz = self._hydrate_quiz_answers(quiz_row)

            weights = {**DEFAULT_WEIGHTS}
            if weights_override:
                weights.update(weights_override)

            min_price, max_price = self.get_budget_range(quiz.budget)
            budget_target_total = ((min_price + max_price) / 2) * 0.9
            target_window = max(budget_target_total * 0.1, 300)
            n_target_items = TARGET_CART_ITEMS
            cart_totals = self._get_cart_totals(session_id)
            if cart_totals["cart_total"] == 0 and cart_totals["distinct_items"] == 0:
                price_target = budget_target_total * 0.85
            else:
                budget_left = max(0.0, budget_target_total - cart_totals["cart_total"])
                remaining_slots = max(1, TARGET_CART_ITEMS - cart_totals["distinct_items"])
                price_target = max(300.0, budget_left / remaining_slots)

            abv_range = self.get_abv_range(quiz.style, quiz.drink_type)
            category_filters = self.get_category_filters(quiz.drink_type)
            fetch_multiplier = 8
            penalty_scale = 1.0
            if quiz.people_count >= 4:
                fetch_multiplier = int(math.ceil(fetch_multiplier * 1.2))
                penalty_scale = 1.2
            fetch_limit = page_size * fetch_multiplier

            liked_products = self._fetch_liked(session_id)
            preferences = self._build_preferences(liked_products)

            candidates = self._fetch_candidates(
                session_id=session_id,
                quiz=quiz,
                abv_range=abv_range,
                fetch_limit=fetch_limit
            )

            scored_products: List[Product] = []
            for candidate in candidates:
                relevance = self._calculate_session_score(
                    candidate,
                    quiz,
                    weights,
                    price_target,
                    target_window,
                    abv_range,
                    category_filters,
                    preferences
                )
                scored_products.append(self._to_product_model(candidate, relevance))

            scored_products.sort(key=lambda p: p.relevance_score, reverse=True)
            selected = self._diversity_select(scored_products, page_size, penalty_scale=penalty_scale)

            self._log_impressions(session_id, [p.sku for p in selected])

            budget_progress = cart_totals["cart_total"] / budget_target_total if budget_target_total > 0 else 0

            self.conn.commit()
            return {
                "items": selected,
                "budget_target_total": budget_target_total,
                "cart_total": cart_totals["cart_total"],
                "budget_progress": budget_progress,
                "n_target_items": n_target_items,
                "cart_items_count": cart_totals["distinct_items"],
                "can_stop": True
            }
        except Exception:
            if self.conn:
                self.conn.rollback()
            raise
        finally:
            self.close()

    def record_reaction(self, session_id: SessionId, sku: str, action: str) -> None:
        """Record like/dislike for a SKU in session_events."""
        if action not in ["like", "dislike"]:
            raise ValueError("action must be 'like' or 'dislike'")
        try:
            self.connect()
            self.cursor.execute(
                """
                insert into session_events (session_id, sku, action, created_at)
                values (%(session_id)s, %(sku)s, %(action)s, now())
                on conflict (session_id, sku)
                do update set action = excluded.action,
                              created_at = session_events.created_at
                """,
                {"session_id": session_id, "sku": sku, "action": action}
            )
            self.cursor.execute(
                "update sessions set updated_at = now() where session_id = %(session_id)s",
                {"session_id": session_id}
            )
            self.conn.commit()
        except Exception:
            if self.conn:
                self.conn.rollback()
            raise
        finally:
            self.close()

    def add_to_cart(self, session_id: SessionId, sku: str, qty_delta: int = 1) -> None:
        """Add or increment SKU in session_cart and update timestamp."""
        if qty_delta == 0:
            return
        if qty_delta < 0:
            raise ValueError("qty_delta must be positive")
        try:
            self.connect()
            self.cursor.execute(
                "select price_current from products where sku = %(sku)s",
                {"sku": sku}
            )
            product_row = self.cursor.fetchone()
            if not product_row or product_row.get("price_current") is None:
                raise ValueError("product price not found")
            price_at_add = float(product_row["price_current"])

            self.cursor.execute(
                """
                insert into session_cart (session_id, sku, qty, price_at_add, added_at)
                values (%(session_id)s, %(sku)s, %(qty)s, %(price_at_add)s, now())
                on conflict (session_id, sku)
                do update set qty = greatest(1, session_cart.qty + excluded.qty),
                              added_at = excluded.added_at
                """,
                {
                    "session_id": session_id,
                    "sku": sku,
                    "qty": qty_delta,
                    "price_at_add": price_at_add
                }
            )
            self.cursor.execute(
                "update sessions set updated_at = now() where session_id = %(session_id)s",
                {"session_id": session_id}
            )
            self.conn.commit()
        except Exception:
            if self.conn:
                self.conn.rollback()
            raise
        finally:
            self.close()

    def get_cart_summary(self, session_id: SessionId) -> Dict[str, Any]:
        """Return cart lines and totals."""
        try:
            self.connect()
            self.cursor.execute(
                """
                select sku, qty, price_at_add, added_at
                from session_cart
                where session_id = %(session_id)s
                """,
                {"session_id": session_id}
            )
            lines = self.cursor.fetchall() or []
            totals = self._get_cart_totals(session_id)
            return {
                "items": lines,
                "cart_total": totals["cart_total"],
                "cart_items_count": totals["distinct_items"]
            }
        except Exception:
            if self.conn:
                self.conn.rollback()
            raise
        finally:
            self.close()

    def stop_session(self, session_id: SessionId) -> None:
        """Mark session as completed."""
        try:
            self.connect()
            self.cursor.execute(
                "update sessions set status = 'completed', updated_at = now() where session_id = %(session_id)s",
                {"session_id": session_id}
            )
            self.conn.commit()
        except Exception:
            if self.conn:
                self.conn.rollback()
            raise
        finally:
            self.close()

    # Minimal usage example (manual run):
    # rec = ProductRecommender()
    # sid = rec.create_session()
    # rec.upsert_quiz(sid, QuizAnswers(occasion=Occasion.PARTY, style=Style.MODERATE, drink_type=DrinkType.WINE_RED, people_count=4, budget=Budget.MEDIUM))
    # feed = rec.get_feed(sid, page_size=5)
    # if feed["items"]:
    #     rec.record_reaction(sid, feed["items"][0].sku, "like")
    #     rec.add_to_cart(sid, feed["items"][0].sku, 1)
    # cart = rec.get_cart_summary(sid)
    # rec.stop_session(sid)

    def get_diverse_recommendations(
        self,
        quiz: QuizAnswers,
        limit: int = 10
    ) -> List[Product]:
        """
        Deprecated legacy diverse recommendations.
        Prefer get_feed for stateful flow.
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
            self.cursor.execute(
                """
                select
                    sku, name, price_current, country, producer,
                    volume_l, abv_percent, category_path, image_urls,
                    rating_value, rating_count, availability_status,
                    attrs_json, brand
                from products
                where sku = %s
                """,
                (sku,)
            )

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
                select
                    sku, name, price_current, country, producer,
                    volume_l, abv_percent, category_path, image_urls,
                    rating_value, rating_count, availability_status,
                    attrs_json,
                    -- similarity scoring
                    (
                        case when attrs_json->>'Сорт винограда' = %(grape)s then 3 else 0 end +
                        case when attrs_json->>'Цвет' = %(color)s then 2 else 0 end +
                        case when attrs_json->>'Содержание сахара' = %(sugar)s then 1 else 0 end +
                        case when country = %(country)s then 2 else 0 end +
                        case when producer = %(producer)s then 1 else 0 end +
                        case when abs(price_current - %(price)s) < 500 then 1 else 0 end
                    ) as similarity_score
                from products
                where sku != %(sku)s
                    and availability_status = 'in_stock'
                    and (
                        attrs_json->>'Сорт винограда' = %(grape)s
                        or attrs_json->>'Цвет' = %(color)s
                        or country = %(country)s
                        or producer = %(producer)s
                    )
                order by
                    similarity_score desc,
                    coalesce(rating_value, 0) desc,
                    abs(price_current - %(price)s) asc
                limit %(limit)s
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
                select
                    sku, name, price_current, country, producer,
                    volume_l, abv_percent, category_path, image_urls,
                    rating_value, rating_count, availability_status,
                    -- trending score: rating * log(review_count) for popularity
                    (coalesce(rating_value, 3.0) * log(coalesce(nullif(rating_count, 0), 1) + 10)) as trending_score
                from products
                where availability_status = 'in_stock'
                    and rating_count > 0
            """]

            params = {'limit': limit}

            # Filter by drink type if specified
            if drink_type and drink_type != DrinkType.MIXED:
                if drink_type == DrinkType.WINE_RED:
                    query_parts.append("and attrs_json->>'Цвет' = 'Красное'")
                elif drink_type == DrinkType.WINE_WHITE:
                    query_parts.append("and (attrs_json->>'Цвет' = 'Белое' or attrs_json->>'Цвет' = 'Белый')")
                elif drink_type == DrinkType.WINE_ROSE:
                    query_parts.append("and attrs_json->>'Цвет' = 'Розовое'")
                elif drink_type == DrinkType.SPARKLING:
                    query_parts.append("and (lower(category_path) like '%игрист%' or lower(category_path) like '%шампан%')")

            query_parts.append("""
                order by trending_score desc
                limit %(limit)s
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
