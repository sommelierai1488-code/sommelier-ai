"""
Pydantic models for quiz-based recommendation system
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class Occasion(str, Enum):
    """Повод для покупки"""
    PARTY = "party"  # Вечеринка
    ROMANTIC = "romantic"  # Романтический вечер
    CELEBRATION = "celebration"  # Праздник
    CASUAL = "casual"  # Обычный вечер
    GIFT = "gift"  # Подарок
    BUSINESS = "business"  # Деловая встреча


class Style(str, Enum):
    """Настрой вечера"""
    LIGHT = "light"  # Лёгко пообщаться
    MODERATE = "moderate"  # Средний темп
    INTENSE = "intense"  # Жёсткий разгон


class DrinkType(str, Enum):
    """Тип напитка в приоритете"""
    WINE_RED = "wine_red"  # Красное вино
    WINE_WHITE = "wine_white"  # Белое вино
    WINE_ROSE = "wine_rose"  # Розовое вино
    SPARKLING = "sparkling"  # Игристое/Шампанское
    SPIRITS = "spirits"  # Крепкие напитки
    BEER = "beer"  # Пиво
    MIXED = "mixed"  # Микс


class Budget(str, Enum):
    """Бюджет на покупку"""
    LOW = "low"  # До 1000 руб
    MEDIUM = "medium"  # 1000-3000 руб
    HIGH = "high"  # 3000-7000 руб
    PREMIUM = "premium"  # От 7000 руб


class QuizAnswers(BaseModel):
    """Ответы пользователя на квиз"""
    occasion: Occasion = Field(..., description="Повод для покупки")
    style: Style = Field(..., description="Настрой вечера")
    drink_type: DrinkType = Field(..., description="Тип напитка в приоритете")
    people_count: int = Field(..., ge=1, le=50, description="Количество человек")
    budget: Budget = Field(..., description="Бюджетная категория")

    class Config:
        json_schema_extra = {
            "example": {
                "occasion": "party",
                "style": "moderate",
                "drink_type": "wine_red",
                "people_count": 4,
                "budget": "medium"
            }
        }


class Product(BaseModel):
    """Модель продукта для ответа"""
    sku: str
    name: str
    price_current: float
    country: Optional[str] = None
    producer: Optional[str] = None
    volume_l: Optional[float] = None
    abv_percent: Optional[float] = None
    category_path: Optional[str] = None
    image_urls: Optional[List[str]] = None
    rating_value: Optional[float] = None
    rating_count: Optional[int] = None
    relevance_score: float = Field(default=0.0, description="Оценка релевантности")

    class Config:
        json_schema_extra = {
            "example": {
                "sku": "12345678",
                "name": "Вино красное сухое Chateau Example 0.75л",
                "price_current": 1499.99,
                "country": "Франция",
                "producer": "Chateau Example",
                "volume_l": 0.75,
                "abv_percent": 13.5,
                "category_path": "Главная > Вино > Красное вино",
                "image_urls": ["https://example.com/image.jpg"],
                "rating_value": 4.5,
                "rating_count": 120,
                "relevance_score": 0.95
            }
        }


class RecommendationResponse(BaseModel):
    """Ответ с рекомендациями"""
    products: List[Product] = Field(..., description="Список рекомендованных продуктов")
    total_count: int = Field(..., description="Общее количество найденных продуктов")
    quiz_answers: QuizAnswers = Field(..., description="Параметры квиза")
    estimated_total_price: float = Field(..., description="Примерная общая стоимость")

    class Config:
        json_schema_extra = {
            "example": {
                "products": [],
                "total_count": 10,
                "quiz_answers": {
                    "occasion": "party",
                    "style": "moderate",
                    "drink_type": "wine_red",
                    "people_count": 4,
                    "budget": "medium"
                },
                "estimated_total_price": 12999.90
            }
        }
