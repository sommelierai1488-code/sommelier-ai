# AmWine Sommelier AI - Рекомендательная система

Интеллектуальная система подбора вина и алкогольных напитков на основе квиза. Проект использует rule-based подход (без машинного обучения) для персонализированных рекомендаций.

## О проекте

AmWine Sommelier AI помогает пользователям подобрать идеальные напитки для любого события, учитывая:
- Повод (вечеринка, романтический ужин, подарок и т.д.)
- Настрой вечера (легкий, умеренный, активный)
- Тип напитка (вино, игристое, крепкие напитки)
- Бюджет (от эконом до премиум)
- Количество гостей

Система работает на основе правил (rule-based system), используя фильтрацию по характеристикам продуктов и расчет релевантности для каждой рекомендации.

## Основные возможности

- **Квиз-система**: простой опросник из 5 вопросов
- **Умная фильтрация**: по цене, категории, крепости (ABV)
- **Расчет релевантности**: оценка каждого товара по нескольким параметрам
- **Разнообразие**: рекомендации от разных производителей и стран
- **REST API**: FastAPI backend с документацией Swagger
- **Веб-интерфейс**: встроенная HTML страница с квизом
- **База данных PostgreSQL**: оптимизированная структура с индексами

## Технологический стек

- **Backend**: Python 3.7+, FastAPI
- **База данных**: PostgreSQL 12+
- **ORM**: psycopg2 (прямые SQL запросы)
- **API Documentation**: Swagger UI, ReDoc
- **Deployment**: Uvicorn ASGI server

## Структура проекта

```
.
├── README.md                           # Главная документация
└── backend/                           # Backend приложение
    ├── api/                           # FastAPI приложение
    │   ├── main.py                   # Endpoints и роуты
    │   ├── models.py                 # Pydantic модели
    │   ├── recommender.py            # Логика рекомендаций
    │   ├── templates/                # HTML шаблоны
    │   │   └── index.html           # Квиз страница
    │   ├── requirements.txt          # API зависимости
    │   └── README.md                # API документация
    ├── migrations/                    # SQL миграции
    │   ├── 001_add_session_tables.sql
    │   └── 002_schema_updates.sql
    ├── schema.sql                     # Основная схема БД
    ├── db_config.py                  # Конфигурация БД
    ├── create_database.py            # Создание БД и таблиц
    ├── load_data.py                  # Загрузка данных из JSON
    ├── update_products.py            # Обновление данных
    ├── optimize_db.py                # Оптимизация индексов
    ├── check_database.py             # Проверка данных
    ├── test_recommendations.py       # Тесты рекомендаций
    ├── setup_all.py                  # Полная настройка проекта
    ├── requirements.txt              # Backend зависимости
    ├── .env.example                  # Пример конфигурации
    └── README.md                     # Backend документация
```

## Быстрый старт

### Предварительные требования

- Python 3.7+
- PostgreSQL 12+
- pip (package installer)

### 1. Клонирование репозитория

```bash
git clone https://github.com/sommelierai1488-code/sommelier-ai.git
cd sommelier-ai
```

### 2. Установка PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**macOS (Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**Windows:**
Скачайте и установите с [официального сайта](https://www.postgresql.org/download/windows/)

### 3. Настройка окружения

```bash
cd backend

# Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt
```

### 4. Конфигурация базы данных

Создайте файл `.env` в директории `backend/`:

```bash
cp .env.example .env
```

Отредактируйте `.env`:
```env
DB_NAME=amwine_products
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_HOST=localhost
DB_PORT=5432
```

### 5. Инициализация базы данных

```bash
# Создать БД и таблицы
python create_database.py

# Загрузить данные (если есть JSON файл)
python load_data.py /path/to/products.json
```

### 6. Запуск API сервера

```bash
cd api
python main.py

# Или с uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API будет доступно по адресу: **http://localhost:8000**

- Квиз страница: http://localhost:8000
- Swagger документация: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

## API Endpoints

### POST /api/recommendations
Получить рекомендации на основе квиза

**Запрос:**
```json
{
  "occasion": "party",
  "style": "moderate",
  "drink_type": "wine_red",
  "people_count": 4,
  "budget": "medium"
}
```

**Ответ:**
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

### GET /api/products/{sku}
Получить информацию о конкретном продукте

### GET /api/similar/{sku}
Найти похожие продукты

### GET /api/trending
Получить популярные/трендовые продукты

### GET /api/filters
Получить доступные опции для квиза

### GET /health
Проверка работоспособности API и подключения к БД

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

### people_count
Целое число от 1 до 50

## Алгоритм рекомендаций

Система использует многоступенчатый подход:

### 1. Фильтрация по бюджету
Товары отбираются в пределах выбранного ценового диапазона

### 2. Фильтрация по категории
На основе типа напитка система ищет соответствующие категории в базе данных

### 3. Фильтрация по крепости (ABV)
Выбор напитков с подходящей крепостью в зависимости от настроя вечера

### 4. Расчет релевантности
Каждому товару присваивается оценка (0-1) на основе:
- **Цена (30%)**: близость к оптимальной цене в бюджете
- **Крепость (20%)**: соответствие выбранному стилю
- **Категория (30%)**: точность категории
- **Рейтинг (10%)**: оценки покупателей
- **Наличие (10%)**: в наличии/под заказ

### 5. Обеспечение разнообразия
Финальный список формируется с учетом:
- Разных производителей
- Разных стран происхождения
- Разных ценовых точек внутри бюджета

## Работа с данными

### Загрузка данных из JSON

```bash
python load_data.py /path/to/products.json
```

Поддерживаемая структура JSON:
```json
{
  "sku": "string",
  "name": "string",
  "price_current": number,
  "country": "string",
  "producer": "string",
  "category_path": "string",
  "abv_percent": number,
  "volume_l": number,
  "rating_value": number,
  "rating_count": number,
  ...
}
```

### Обновление продуктов

```bash
python update_products.py /path/to/updated_products.json
```

### Оптимизация БД

```bash
python optimize_db.py
```

### Проверка данных

```bash
python check_database.py
```

## Тестирование

### Тест рекомендаций

```bash
python test_recommendations.py
```

### Тест API

```bash
cd api
python test_api.py
```

### Примеры запросов

**cURL:**
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

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/recommendations",
    json={
        "occasion": "party",
        "style": "moderate",
        "drink_type": "wine_red",
        "people_count": 4,
        "budget": "medium"
    }
)

print(response.json())
```

## Структура базы данных

### Таблица products

| Поле | Тип | Описание |
|------|-----|----------|
| sku | VARCHAR | Primary key, артикул |
| name | TEXT | Название продукта |
| price_current | DECIMAL | Текущая цена |
| price_old | DECIMAL | Старая цена |
| country | VARCHAR | Страна производства |
| producer | VARCHAR | Производитель |
| brand | VARCHAR | Бренд |
| category_path | TEXT | Путь категории |
| volume_l | DECIMAL | Объем в литрах |
| abv_percent | DECIMAL | Крепость в % |
| rating_value | DECIMAL | Рейтинг (0-5) |
| rating_count | INTEGER | Количество оценок |
| availability_status | VARCHAR | Статус наличия |
| image_urls | JSONB | Массив URL изображений |
| attrs_json | JSONB | Атрибуты продукта |
| texts_json | JSONB | Текстовые описания |
| created_at | TIMESTAMP | Дата создания |
| updated_at | TIMESTAMP | Дата обновления |

### Индексы

Для оптимизации запросов созданы индексы на:
- `category_path` (GIN для текстового поиска)
- `price_current`
- `country`
- `producer`
- `abv_percent`
- `rating_value`

## Развертывание

### Docker (будущая функциональность)

```dockerfile
# Пример Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Systemd Service

Пример файла `sommelier-api.service`:
```ini
[Unit]
Description=AmWine Sommelier API
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/sommelier-ai/backend/api
Environment="PATH=/opt/sommelier-ai/backend/venv/bin"
ExecStart=/opt/sommelier-ai/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

## Устранение неполадок

### Ошибка подключения к PostgreSQL

Проверьте:
- Запущен ли PostgreSQL: `sudo systemctl status postgresql`
- Правильные ли учетные данные в `.env`
- Доступен ли PostgreSQL на указанном порту

### Ошибка "database already exists"

Это нормально - скрипт пропустит создание и перейдет к таблицам

### Пустые рекомендации

Убедитесь что:
- В БД есть данные: `python check_database.py`
- Параметры квиза соответствуют имеющимся товарам
- Бюджет не слишком ограничен

## Возможные улучшения

- [ ] Frontend React/Vue приложение
- [ ] Кэширование с Redis
- [ ] Поддержка множественных языков
- [ ] История рекомендаций пользователя
- [ ] A/B тестирование правил
- [ ] Машинное обучение для персонализации
- [ ] Интеграция с системами оплаты
- [ ] Mobile приложение
- [ ] Учет сезонности и праздников
- [ ] Социальные функции (отзывы, рейтинги)

## Документация

Подробная документация доступна в:
- `backend/README.md` - Backend и база данных
- `backend/api/README.md` - API endpoints
- `backend/HOW_TO_UPDATE_DB.md` - Обновление БД
- `backend/MIGRATION_GUIDE.md` - Миграции
- `backend/START_API.md` - Запуск API

## Лицензия

Этот проект создан для образовательных целей.

## Контакты

Для вопросов и предложений создавайте [issues](https://github.com/sommelierai1488-code/sommelier-ai/issues) в репозитории.

## Благодарности

Проект разработан как демонстрация rule-based рекомендательной системы для e-commerce платформы алкогольных напитков.
