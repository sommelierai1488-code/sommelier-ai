"""
FastAPI application for AmWine recommendations
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

from .models import (
    RecommendRequest, RecommendResponse, Offer,
    BatchSessionEventsRequest, BatchSessionEventsResponse,
    SessionStartRequest, SessionStartResponse,
    SessionQuizRequest, SessionQuizResponse,
    AddToCartRequest, AddToCartResponse,
    GetCartResponse, SessionCompleteResponse
)
from .database import (
    get_random_products, format_product_for_response,
    insert_session_events_batch,
    create_session, save_quiz_answers,
    add_to_cart, get_cart, remove_from_cart,
    complete_session
)
from .config import API_TITLE, API_VERSION, API_DESCRIPTION, DEFAULT_RECOMMENDATIONS_COUNT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tags metadata for Swagger documentation
tags_metadata = [
    {
        "name": "Session Management",
        "description": "Управление сессиями пользователей: создание, сохранение квиза, завершение."
    },
    {
        "name": "Recommendations",
        "description": "Получение рекомендаций товаров на основе ответов квиза."
    },
    {
        "name": "Events",
        "description": "Отслеживание событий взаимодействия пользователя с товарами (лайки/дизлайки)."
    },
    {
        "name": "Cart",
        "description": "Управление корзиной: добавление, просмотр, удаление товаров."
    },
    {
        "name": "Health",
        "description": "Проверка состояния сервиса."
    }
]

# Create FastAPI app
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    openapi_tags=tags_metadata
)

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": API_TITLE,
        "version": API_VERSION
    }


@app.post("/offers/recommend", response_model=RecommendResponse, tags=["Recommendations"])
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


@app.get("/health", tags=["Health"])
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


@app.post("/session/events", response_model=BatchSessionEventsResponse, tags=["Events"])
async def create_session_events(request: BatchSessionEventsRequest):
    """
    Create session events in batch (user interactions with products)

    Args:
        request: Session ID and list of events (sku + action)

    Returns:
        Success status and number of inserted events

    Note:
        This endpoint records all user interactions with products (like, dislike, none)
        in a single batch operation for better performance.
    """
    try:
        logger.info(f"Received batch session events request: session_id={request.session_id}, "
                   f"events_count={len(request.events)}")

        if not request.events:
            return BatchSessionEventsResponse(
                success=True,
                inserted_count=0,
                message="No events to insert"
            )

        # Convert Pydantic models to dict format for database function
        events_data = [
            {"sku": event.sku, "action": event.action}
            for event in request.events
        ]

        # Insert events in batch
        inserted_count = insert_session_events_batch(request.session_id, events_data)

        logger.info(f"Successfully inserted {inserted_count} events for session {request.session_id}")

        return BatchSessionEventsResponse(
            success=True,
            inserted_count=inserted_count,
            message=f"Successfully inserted {inserted_count} events"
        )

    except Exception as e:
        logger.error(f"Error inserting session events: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to insert session events: {str(e)}"
        )


# ============================================
# SESSION MANAGEMENT ENDPOINTS
# ============================================

@app.post("/sessions/start", response_model=SessionStartResponse, tags=["Session Management"])
async def start_session(request: SessionStartRequest):
    """
    Start a new session

    Args:
        request: Optional user_id (can be None for anonymous users)

    Returns:
        Session ID, status, and creation timestamp

    Note:
        Call this endpoint when user starts the quiz (Welcome -> Start)
    """
    try:
        logger.info(f"Starting new session with user_id={request.user_id}")

        result = create_session(request.user_id)

        logger.info(f"Created session {result['session_id']}")

        return SessionStartResponse(**result)

    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create session: {str(e)}"
        )


@app.post("/sessions/{session_id}/quiz", response_model=SessionQuizResponse, tags=["Session Management"])
async def save_session_quiz(session_id: int, request: SessionQuizRequest):
    """
    Save quiz answers for a session (UPSERT)

    Args:
        session_id: Session ID
        request: Quiz answers (occasion, style, drink_types, tastes, people_count, budget)

    Returns:
        Success status and message

    Note:
        Call this endpoint when user completes the quiz and clicks
        "Перейти к подбору напитков" (before calling /offers/recommend)
    """
    try:
        logger.info(f"Saving quiz answers for session {session_id}")

        save_quiz_answers(
            session_id=session_id,
            occasion=request.occasion,
            style=request.style,
            drink_types=request.drink_types,
            tastes=request.tastes,
            people_count=request.people_count,
            budget=request.budget
        )

        logger.info(f"Quiz answers saved for session {session_id}")

        return SessionQuizResponse(
            success=True,
            session_id=session_id,
            message="Quiz answers saved successfully"
        )

    except Exception as e:
        logger.error(f"Error saving quiz answers: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save quiz answers: {str(e)}"
        )


@app.post("/sessions/{session_id}/complete", response_model=SessionCompleteResponse, tags=["Session Management"])
async def complete_session_endpoint(session_id: int):
    """
    Mark session as completed

    Args:
        session_id: Session ID

    Returns:
        Success status and session info

    Note:
        Call this endpoint when user completes booking/order
    """
    try:
        logger.info(f"Completing session {session_id}")

        result = complete_session(session_id)

        logger.info(f"Session {session_id} marked as {result['status']}")

        return SessionCompleteResponse(
            success=True,
            session_id=result['session_id'],
            status=result['status'],
            message="Session completed successfully"
        )

    except Exception as e:
        logger.error(f"Error completing session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to complete session: {str(e)}"
        )


# ============================================
# CART MANAGEMENT ENDPOINTS
# ============================================

@app.post("/sessions/{session_id}/cart", response_model=AddToCartResponse, tags=["Cart"])
async def add_item_to_cart(session_id: int, request: AddToCartRequest):
    """
    Add or update item in cart (UPSERT)

    Args:
        session_id: Session ID
        request: Item details (sku, qty, price_at_add)

    Returns:
        Success status and message

    Note:
        Use this endpoint to add items to cart or update quantity.
        Call when user clicks "Забронировать заказ"
    """
    try:
        logger.info(f"Adding item to cart: session={session_id}, sku={request.sku}, qty={request.qty}")

        add_to_cart(
            session_id=session_id,
            sku=request.sku,
            qty=request.qty,
            price_at_add=request.price_at_add
        )

        logger.info(f"Item added to cart for session {session_id}")

        return AddToCartResponse(
            success=True,
            message="Item added to cart successfully"
        )

    except Exception as e:
        logger.error(f"Error adding to cart: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add item to cart: {str(e)}"
        )


@app.get("/sessions/{session_id}/cart", response_model=GetCartResponse, tags=["Cart"])
async def get_session_cart(session_id: int):
    """
    Get cart for a session

    Args:
        session_id: Session ID

    Returns:
        Cart items, total items count, and total price

    Note:
        Use this endpoint to retrieve cart contents
    """
    try:
        logger.info(f"Getting cart for session {session_id}")

        cart_data = get_cart(session_id)

        logger.info(f"Retrieved {cart_data['total_items']} items from cart for session {session_id}")

        return GetCartResponse(**cart_data)

    except Exception as e:
        logger.error(f"Error getting cart: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cart: {str(e)}"
        )


@app.delete("/sessions/{session_id}/cart/{sku}", tags=["Cart"])
async def remove_item_from_cart(session_id: int, sku: str):
    """
    Remove item from cart

    Args:
        session_id: Session ID
        sku: Product SKU to remove

    Returns:
        Success status and message

    Note:
        Use this endpoint to remove items from cart
    """
    try:
        logger.info(f"Removing item from cart: session={session_id}, sku={sku}")

        remove_from_cart(session_id, sku)

        logger.info(f"Item removed from cart for session {session_id}")

        return {
            "success": True,
            "message": "Item removed from cart successfully"
        }

    except Exception as e:
        logger.error(f"Error removing from cart: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove item from cart: {str(e)}"
        )
