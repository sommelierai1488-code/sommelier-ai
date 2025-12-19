# AmWine Recommendation API

Rule-based рекомендательная система для подбора вина и алкогольных напитков на основе квиза.

## Описание

Система работает полностью на правилах (rule-based), без машинного обучения:

1. **Фильтрация по бюджету** - отбирает товары в нужном ценовом диапазоне
2. **Фильтрация по типу напитка** - использует категории продуктов
3. **Фильтрация по стилю вечера** - учитывает крепость (ABV)
4. **Подсчёт релевантности** - присваивает оценку каждому товару
5. **Разнообразие** - обеспечивает разных производителей и страны

## Установка

```bash
cd /home/project/backend/api
pip install -r requirements.txt
```

## Запуск

```bash
# Из директории backend/api
python main.py

# Или с uvicorn напрямую
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API будет доступно по адресу: `http://localhost:8000`

## Endpoints

### 1. GET `/` - Корневой endpoint
Информация об API

### 2. GET `/health` - Проверка здоровья
Проверяет подключение к БД

### 3. POST `/api/recommendations` - Получить рекомендации
Основной endpoint для получения рекомендаций на основе квиза

**Request Body:**
```json
{
  "occasion": "party",
  "style": "moderate",
  "drink_type": "wine_red",
  "people_count": 4,
  "budget": "medium"
}
```

**Response:**
```json
{
  "products": [
    {
      "sku": "12345678",
      "name": "Вино красное сухое Example 0.75л",
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
  ],
  "total_count": 10,
  "quiz_answers": {...},
  "estimated_total_price": 12999.90
}
```

### 4. GET `/api/products/{sku}` - Получить товар по SKU
Детали конкретного товара

### 5. GET `/api/filters` - Получить доступные фильтры
Все доступные значения для квиза

## Параметры квиза

### occasion (Повод)
- `party` - Вечеринка
- `romantic` - Романтический вечер
- `celebration` - Праздник
- `casual` - Обычный вечер
- `gift` - Подарок
- `business` - Деловая встреча

### style (Настрой вечера)
- `light` - Лёгко пообщаться (низкая крепость)
- `moderate` - Средний темп (средняя крепость)
- `intense` - Жёсткий разгон (высокая крепость)

### drink_type (Тип напитка)
- `wine_red` - Красное вино
- `wine_white` - Белое вино
- `wine_rose` - Розовое вино
- `sparkling` - Игристое/Шампанское
- `spirits` - Крепкие напитки
- `beer` - Пиво
- `mixed` - Микс

### budget (Бюджет)
- `low` - До 1000 руб
- `medium` - 1000-3000 руб
- `high` - 3000-7000 руб
- `premium` - От 7000 руб

### people_count (Количество людей)
Число от 1 до 50

## Логика рекомендаций

Система использует следующие правила:

### 1. Фильтрация по цене
Отбирает товары в диапазоне выбранного бюджета:
- `low`: 0-1000 руб
- `medium`: 1000-3000 руб
- `high`: 3000-7000 руб
- `premium`: 7000+ руб

### 2. Фильтрация по категории
На основе `drink_type` ищет товары в соответствующих категориях:
- Красное вино: категории содержат "красное", "red"
- Белое вино: "белое", "white"
- Игристое: "игристое", "шампанское", "sparkling"
- И т.д.

### 3. Фильтрация по крепости (ABV)
На основе `style` определяет подходящий диапазон крепости:

**Для вина:**
- `light`: 0-12%
- `moderate`: 11-14%
- `intense`: 13-20%

**Для крепких напитков:**
- `light`: 30-40%
- `moderate`: 35-45%
- `intense`: 40-70%

### 4. Подсчёт релевантности

Каждому товару присваивается оценка (0-1) на основе:

- **Цена (30%)**: товары ближе к середине бюджетного диапазона получают больше баллов
- **Крепость (20%)**: соответствие выбранному стилю
- **Категория (30%)**: точное попадание в нужную категорию
- **Рейтинг (10%)**: рейтинг товара от покупателей
- **Наличие (10%)**: товары в наличии

### 5. Разнообразие

Финальный список формируется с учётом разнообразия:
- Разные производители
- Разные страны
- Разные ценовые уровни внутри бюджета

## Примеры запросов

### cURL

```bash
# Получить рекомендации
curl -X POST "http://localhost:8000/api/recommendations" \
  -H "Content-Type: application/json" \
  -d '{
    "occasion": "party",
    "style": "moderate",
    "drink_type": "wine_red",
    "people_count": 4,
    "budget": "medium"
  }'

# Проверка здоровья
curl "http://localhost:8000/health"

# Получить доступные фильтры
curl "http://localhost:8000/api/filters"
```

### Python

```python
import requests

# Получить рекомендации
quiz_data = {
    "occasion": "party",
    "style": "moderate",
    "drink_type": "wine_red",
    "people_count": 4,
    "budget": "medium"
}

response = requests.post(
    "http://localhost:8000/api/recommendations",
    json=quiz_data
)

recommendations = response.json()
print(f"Найдено товаров: {recommendations['total_count']}")
print(f"Общая стоимость: {recommendations['estimated_total_price']} руб")

for product in recommendations['products']:
    print(f"{product['name']} - {product['price_current']} руб (score: {product['relevance_score']:.2f})")
```

### JavaScript/TypeScript

```javascript
// Получить рекомендации
const quizData = {
  occasion: "party",
  style: "moderate",
  drink_type: "wine_red",
  people_count: 4,
  budget: "medium"
};

fetch('http://localhost:8000/api/recommendations', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(quizData)
})
  .then(response => response.json())
  .then(data => {
    console.log(`Найдено товаров: ${data.total_count}`);
    console.log(`Общая стоимость: ${data.estimated_total_price} руб`);

    data.products.forEach(product => {
      console.log(`${product.name} - ${product.price_current} руб`);
    });
  });
```

## Документация API

После запуска сервера доступна интерактивная документация:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Структура файлов

```
api/
├── main.py              # FastAPI приложение и endpoints
├── models.py            # Pydantic модели данных
├── recommender.py       # Логика рекомендаций
├── requirements.txt     # Зависимости
├── __init__.py         # Пакет
└── README.md           # Документация
```

## Настройка

Подключение к БД настраивается через файл `backend/db_config.py` или переменные окружения:

```bash
export DB_NAME=amwine_products
export DB_USER=postgres
export DB_PASSWORD=postgres
export DB_HOST=localhost
export DB_PORT=5432
```

## Возможные улучшения

1. **Кэширование** - добавить Redis для кэширования результатов
2. **Логирование** - детальное логирование запросов
3. **Аналитика** - сбор статистики по рекомендациям
4. **A/B тестирование** - разные варианты правил
5. **Персонализация** - учёт истории покупок пользователя
6. **Сезонность** - учёт времени года и праздников

## Лицензия

Для внутреннего использования.
