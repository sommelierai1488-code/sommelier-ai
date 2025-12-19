"""
FastAPI application for wine/spirits recommendation system
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import List
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models import QuizAnswers, RecommendationResponse, Product
from api.recommender import ProductRecommender


# Initialize FastAPI app
app = FastAPI(
    title="AmWine Recommendation API",
    description="Quiz-based product recommendation system for wine and spirits",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - Quiz page"""
    html_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        recommender = ProductRecommender()
        recommender.connect()
        recommender.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.post("/api/recommendations", response_model=RecommendationResponse)
async def get_recommendations(quiz: QuizAnswers):
    """
    Get product recommendations based on quiz answers

    Args:
        quiz: User's quiz answers including occasion, style, drink type, people count, and budget

    Returns:
        Top 10 recommended products with relevance scores

    Example request:
        ```json
        {
            "occasion": "party",
            "style": "moderate",
            "drink_type": "wine_red",
            "people_count": 4,
            "budget": "medium"
        }
        ```
    """
    try:
        # Initialize recommender
        recommender = ProductRecommender()

        # Get recommendations
        products = recommender.get_diverse_recommendations(quiz, limit=10)

        # Calculate total price
        total_price = sum(p.price_current for p in products)

        # Build response
        response = RecommendationResponse(
            products=products,
            total_count=len(products),
            quiz_answers=quiz,
            estimated_total_price=total_price
        )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating recommendations: {str(e)}"
        )


@app.get("/api/products/{sku}", response_model=Product)
async def get_product(sku: str):
    """
    Get product details by SKU

    Args:
        sku: Product SKU

    Returns:
        Product details
    """
    try:
        recommender = ProductRecommender()
        recommender.connect()

        query = """
            SELECT
                sku, name, price_current, country, producer,
                volume_l, abv_percent, category_path, image_urls,
                rating_value, rating_count
            FROM products
            WHERE sku = %s
        """

        recommender.cursor.execute(query, (sku,))
        product = recommender.cursor.fetchone()

        recommender.close()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        return Product(
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
            rating_count=product.get('rating_count')
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching product: {str(e)}"
        )


@app.get("/api/filters")
async def get_available_filters():
    """
    Get available filter options for the quiz

    Returns:
        Dictionary with all available options
    """
    from api.models import Occasion, Style, DrinkType, Budget

    return {
        "occasions": [e.value for e in Occasion],
        "styles": [e.value for e in Style],
        "drink_types": [e.value for e in DrinkType],
        "budgets": [e.value for e in Budget],
        "people_count_range": {
            "min": 1,
            "max": 50
        }
    }


@app.get("/api/similar/{sku}", response_model=List[Product])
async def get_similar_products(sku: str, limit: int = 6):
    """
    Get similar products based on a product SKU

    Args:
        sku: Product SKU to find similar products for
        limit: Maximum number of similar products to return (default: 6)

    Returns:
        List of similar products
    """
    try:
        recommender = ProductRecommender()
        similar_products = recommender.get_similar_products(sku, limit=limit)

        if not similar_products:
            raise HTTPException(status_code=404, detail="No similar products found")

        return similar_products

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error finding similar products: {str(e)}"
        )


@app.get("/api/trending", response_model=List[Product])
async def get_trending_products(drink_type: str = None, limit: int = 10):
    """
    Get trending/popular products

    Args:
        drink_type: Optional drink type filter (wine_red, wine_white, etc.)
        limit: Maximum number of products to return (default: 10)

    Returns:
        List of trending products
    """
    try:
        from api.models import DrinkType

        # Convert drink_type string to enum if provided
        drink_type_enum = None
        if drink_type:
            try:
                drink_type_enum = DrinkType(drink_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid drink_type. Must be one of: {[e.value for e in DrinkType]}"
                )

        recommender = ProductRecommender()
        trending_products = recommender.get_trending_products(
            drink_type=drink_type_enum,
            limit=limit
        )

        return trending_products

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching trending products: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
