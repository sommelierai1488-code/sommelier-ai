"""
FastAPI application for AmWine recommendations
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

from .models import RecommendRequest, RecommendResponse, Offer
from .database import get_random_products, format_product_for_response
from .config import API_TITLE, API_VERSION, API_DESCRIPTION, DEFAULT_RECOMMENDATIONS_COUNT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION
)

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": API_TITLE,
        "version": API_VERSION
    }


@app.post("/offers/recommend", response_model=RecommendResponse)
async def recommend_offers(request: RecommendRequest):
    """
    Get product recommendations based on quiz results

    Args:
        request: Quiz results including occasion, style, preferences, etc.

    Returns:
        List of recommended products

    Note:
        Currently returns random products. ML-based filtering will be added later.
    """
    try:
        logger.info(f"Received recommendation request: occasion={request.occasion}, "
                   f"style={request.style}, people_count={request.people_count}")

        # Get random products from database
        # TODO: Implement ML-based filtering using request parameters
        products = get_random_products(limit=DEFAULT_RECOMMENDATIONS_COUNT)

        if not products:
            raise HTTPException(
                status_code=404,
                detail="No products found in database"
            )

        # Format products for response
        offers = [
            Offer(**format_product_for_response(product))
            for product in products
        ]

        logger.info(f"Returning {len(offers)} recommendations")

        return RecommendResponse(offers=offers)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing recommendation request: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring

    Returns:
        Service health status
    """
    return {
        "status": "healthy",
        "service": API_TITLE,
        "version": API_VERSION
    }
