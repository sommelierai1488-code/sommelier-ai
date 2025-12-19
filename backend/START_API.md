# Быстрый старт рекомендательной системы

## Запуск API

### Вариант 1: Запуск из директории api

```bash
cd /home/project/backend/api
python3 main.py
```

### Вариант 2: Запуск с uvicorn

```bash
cd /home/project/backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

API будет доступно по адресу: **http://localhost:8000**

## Проверка работы

### 1. Проверка здоровья
```bash
curl http://localhost:8000/health
```

### 2. Получение рекомендаций

```bash
curl -X POST "http://localhost:8000/api/recommendations" \
  -H "Content-Type: application/json" \
  -d '{
    "occasion": "party",
    "style": "moderate",
    "drink_type": "wine_red",
    "people_count": 4,
    "budget": "medium"
  }'
```

### 3. Интерактивная документация

Откройте в браузере:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Примеры запросов для разных сценариев

### Вечеринка - Красное вино - Средний бюджет
```json
{
  "occasion": "party",
  "style": "moderate",
  "drink_type": "wine_red",
  "people_count": 4,
  "budget": "medium"
}
```

**Результат:** ~19,750 руб, 10 товаров, средняя крепость 13-14%

### Романтический вечер - Игристое - Высокий бюджет
```json
{
  "occasion": "romantic",
  "style": "light",
  "drink_type": "sparkling",
  "people_count": 2,
  "budget": "high"
}
```

**Результат:** ~49,692 руб, 10 товаров премиум шампанского

### Праздник - Микс - Премиум бюджет
```json
{
  "occasion": "celebration",
  "style": "intense",
  "drink_type": "mixed",
  "people_count": 10,
  "budget": "premium"
}
```

**Результат:** ~152,557 руб, топовые вина из Италии и Чили

## Доступные параметры

### occasion (Повод)
- `party` - Вечеринка
- `romantic` - Романтический вечер
- `celebration` - Праздник
- `casual` - Обычный вечер
- `gift` - Подарок
- `business` - Деловая встреча

### style (Настрой)
- `light` - Лёгкий (низкая крепость)
- `moderate` - Средний
- `intense` - Интенсивный (высокая крепость)

### drink_type (Тип напитка)
- `wine_red` - Красное вино
- `wine_white` - Белое вино
- `wine_rose` - Розовое вино
- `sparkling` - Игристое/Шампанское
- `spirits` - Крепкие напитки
- `beer` - Пиво
- `mixed` - Микс

### budget (Бюджет)
- `low` - До 1,000 руб
- `medium` - 1,000-3,000 руб
- `high` - 3,000-7,000 руб
- `premium` - От 7,000 руб

### people_count
Число от 1 до 50

## Структура ответа

```json
{
  "products": [
    {
      "sku": "24480051",
      "name": "Вино Santa Cristina, Toscana IGT 0.75 л",
      "price_current": 1999.99,
      "country": "Италия",
      "producer": "Cantinе Santa Cristina Spa",
      "volume_l": 0.75,
      "abv_percent": 13.0,
      "category_path": "Главная > Каталог > Вино",
      "image_urls": [...],
      "rating_value": 4.5,
      "rating_count": 120,
      "relevance_score": 0.70
    }
  ],
  "total_count": 10,
  "quiz_answers": {...},
  "estimated_total_price": 19750.92
}
```

## Тестирование

Запустить автоматические тесты:

```bash
cd /home/project/backend
python3 api/test_api.py
```

## Что дальше?

1. Интегрируйте API в ваше приложение
2. Добавьте кэширование для ускорения
3. Настройте CORS для вашего домена
4. Добавьте аналитику запросов
5. Реализуйте персонализацию на основе истории

## Поддержка

Документация API: `/home/project/backend/api/README.md`
Примеры SQL запросов: `/home/project/backend/queries_examples.sql`
