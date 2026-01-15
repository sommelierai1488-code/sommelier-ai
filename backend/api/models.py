"""
Pydantic models for API request/response validation
"""
from pydantic import BaseModel, Field
from typing import List


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
