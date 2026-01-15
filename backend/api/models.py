"""
Pydantic models for API request/response validation
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class RecommendRequest(BaseModel):
    """Request model for recommendations"""
    occasion: str = Field(..., description="Повод для покупки")
    style: str = Field(..., description="Стиль напитка")
    drink_types: List[str] = Field(..., description="Типы алкоголя (multi-select)")
    tastes: List[str] = Field(..., description="Вкусовые предпочтения (multi-select)")
    people_count: int = Field(..., ge=1, le=10, description="Количество людей (1-10)")
    budget: str = Field(..., description="Бюджет")

    class Config:
        json_schema_extra = {
            "example": {
                "occasion": "🎉 Вечеринка",
                "style": "🌤 Легко и мягко",
                "drink_types": [
                    "🍷 Вино / игристое",
                    "🍺 Пиво / сидр"
                ],
                "tastes": [
                    "🍑 Фруктовое / ароматное",
                    "🍬 Сладковатое"
                ],
                "people_count": 6,
                "budget": "💰 1000–3000 ₽"
            }
        }


class Offer(BaseModel):
    """Single product offer"""
    id: str = Field(..., description="Product SKU")
    description: str = Field(..., description="Product name")
    image: str = Field(..., description="Product image URL")
    url: str = Field(..., description="Product page URL")
    price_raw: str = Field(..., description="Formatted price string")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "121633",
                "description": "Riga Black Balsam 0.5л",
                "image": "https://example.com/image.jpg",
                "url": "https://example.com/product/121633",
                "price_raw": "999 ₽"
            }
        }


class RecommendResponse(BaseModel):
    """Response model for recommendations"""
    offers: List[Offer] = Field(..., description="List of recommended products")

    class Config:
        json_schema_extra = {
            "example": {
                "offers": [
                    {
                        "id": "121633",
                        "description": "Riga Black Balsam 0.5л",
                        "image": "https://example.com/image.jpg",
                        "url": "https://example.com/product/121633",
                        "price_raw": "999 ₽"
                    }
                ]
            }
        }


class SessionEvent(BaseModel):
    """Single session event (user interaction with product)"""
    sku: str = Field(..., description="Product SKU")
    action: Literal['like', 'dislike', 'none'] = Field(..., description="User action: like, dislike, or none")

    class Config:
        json_schema_extra = {
            "example": {
                "sku": "121633",
                "action": "like"
            }
        }


class BatchSessionEventsRequest(BaseModel):
    """Request model for batch session events"""
    session_id: int = Field(..., description="Session ID")
    events: List[SessionEvent] = Field(..., description="List of session events")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": 1,
                "events": [
                    {"sku": "121633", "action": "like"},
                    {"sku": "121634", "action": "dislike"},
                    {"sku": "121635", "action": "none"}
                ]
            }
        }


class BatchSessionEventsResponse(BaseModel):
    """Response model for batch session events"""
    success: bool = Field(..., description="Whether the operation was successful")
    inserted_count: int = Field(..., description="Number of events inserted")
    message: str = Field(..., description="Response message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "inserted_count": 3,
                "message": "Successfully inserted 3 events"
            }
        }


# ============================================
# SESSION MANAGEMENT MODELS
# ============================================

class SessionStartRequest(BaseModel):
    """Request model for starting a new session"""
    user_id: Optional[int] = Field(None, description="User ID (optional, for anonymous users)")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": None
            }
        }


class SessionStartResponse(BaseModel):
    """Response model for session start"""
    session_id: int = Field(..., description="Created session ID")
    status: str = Field(..., description="Session status")
    created_at: str = Field(..., description="Session creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": 1,
                "status": "in_progress",
                "created_at": "2024-01-15T10:30:00"
            }
        }


class SessionQuizRequest(BaseModel):
    """Request model for saving quiz answers"""
    occasion: str = Field(..., description="Повод для покупки")
    style: str = Field(..., description="Стиль напитка")
    drink_types: List[str] = Field(..., description="Типы алкоголя (multi-select)")
    tastes: List[str] = Field(..., description="Вкусовые предпочтения (multi-select)")
    people_count: int = Field(..., ge=1, le=10, description="Количество людей (1-10)")
    budget: str = Field(..., description="Бюджет")

    class Config:
        json_schema_extra = {
            "example": {
                "occasion": "🎉 Вечеринка",
                "style": "🌤 Легко и мягко",
                "drink_types": ["🍷 Вино / игристое", "🍺 Пиво / сидр"],
                "tastes": ["🍑 Фруктовое / ароматное", "🍬 Сладковатое"],
                "people_count": 6,
                "budget": "💰 1000–3000 ₽"
            }
        }


class SessionQuizResponse(BaseModel):
    """Response model for quiz save"""
    success: bool = Field(..., description="Whether the operation was successful")
    session_id: int = Field(..., description="Session ID")
    message: str = Field(..., description="Response message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "session_id": 1,
                "message": "Quiz answers saved successfully"
            }
        }


# ============================================
# CART MANAGEMENT MODELS
# ============================================

class CartItem(BaseModel):
    """Single cart item"""
    sku: str = Field(..., description="Product SKU")
    qty: int = Field(..., ge=1, description="Quantity (minimum 1)")
    price_at_add: float = Field(..., description="Price at the time of adding to cart")

    class Config:
        json_schema_extra = {
            "example": {
                "sku": "121633",
                "qty": 2,
                "price_at_add": 999.0
            }
        }


class AddToCartRequest(BaseModel):
    """Request model for adding/updating item in cart"""
    sku: str = Field(..., description="Product SKU")
    qty: int = Field(..., ge=1, description="Quantity (minimum 1)")
    price_at_add: float = Field(..., description="Price at the time of adding to cart")

    class Config:
        json_schema_extra = {
            "example": {
                "sku": "121633",
                "qty": 2,
                "price_at_add": 999.0
            }
        }


class AddToCartResponse(BaseModel):
    """Response model for add to cart"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Item added to cart successfully"
            }
        }


class GetCartResponse(BaseModel):
    """Response model for getting cart"""
    session_id: int = Field(..., description="Session ID")
    items: List[CartItem] = Field(..., description="Cart items")
    total_items: int = Field(..., description="Total number of items")
    total_price: float = Field(..., description="Total cart price")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": 1,
                "items": [
                    {"sku": "121633", "qty": 2, "price_at_add": 999.0},
                    {"sku": "121634", "qty": 1, "price_at_add": 1499.0}
                ],
                "total_items": 3,
                "total_price": 3497.0
            }
        }


class SessionCompleteResponse(BaseModel):
    """Response model for session completion"""
    success: bool = Field(..., description="Whether the operation was successful")
    session_id: int = Field(..., description="Session ID")
    status: str = Field(..., description="Session status")
    message: str = Field(..., description="Response message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "session_id": 1,
                "status": "completed",
                "message": "Session completed successfully"
            }
        }
