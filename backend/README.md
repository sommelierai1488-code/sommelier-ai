# AmWine Products Database

Этот проект предназначен для загрузки данных о товарах из JSON файла в PostgreSQL базу данных.

## Структура проекта

```
backend/
├── schema.sql              # SQL схема для создания таблицы
├── db_config.py           # Конфигурация подключения к БД
├── create_database.py     # Скрипт для создания БД и таблиц
├── load_data.py           # Скрипт для загрузки данных из JSON
├── requirements.txt       # Зависимости Python
├── .env.example          # Пример файла конфигурации
└── README.md             # Документация
```

## Требования

- Python 3.7+
- PostgreSQL 12+

## Установка

### 1. Установите PostgreSQL

Убедитесь, что PostgreSQL установлен и запущен на вашей системе.

```bash
# Для Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Для macOS (с Homebrew)
brew install postgresql
brew services start postgresql
```

### 2. Создайте виртуальное окружение и установите зависимости

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Для Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Настройте переменные окружения (опционально)

Скопируйте `.env.example` в `.env` и измените параметры при необходимости:

```bash
cp .env.example .env
```

Отредактируйте `.env` файл:

```
DB_NAME=amwine_products
DB_USER=postgres
DB_PASSWORD=ваш_пароль
DB_HOST=localhost
DB_PORT=5432
```

Если вы не создадите `.env` файл, будут использованы значения по умолчанию.

## Использование

### Шаг 1: Создание базы данных и таблиц

```bash
python create_database.py
```

Этот скрипт:
- Создаст базу данных `amwine_products` (если её нет)
- Создаст таблицу `products` с необходимой структурой
- Создаст индексы для оптимизации запросов

### Шаг 2: Загрузка данных из JSON

```bash
python load_data.py
```

По умолчанию скрипт загружает данные из `/home/testuser/amwine_products.json`.

Вы также можете указать свой путь к JSON файлу:

```bash
python load_data.py /path/to/your/products.json
```

Скрипт:
- Прочитает JSON файл
- Исключит поля `raw_html`, `"Гастрономические сочетания"`, `"Затрудняетесь с выбором?"`
- Загрузит данные в БД с показом прогресса
- При конфликте по ключу `sku` обновит существующую запись

## Структура таблицы

Таблица `products` содержит следующие поля:

- `sku` (VARCHAR) - PRIMARY KEY
- `source` (VARCHAR)
- `product_url` (TEXT)
- `site_product_id` (VARCHAR)
- `name` (TEXT)
- `category_path` (TEXT)
- `brand` (VARCHAR)
- `producer` (VARCHAR)
- `country` (VARCHAR)
- `price_current` (DECIMAL)
- `price_old` (DECIMAL)
- `availability_status` (VARCHAR)
- `volume_l` (DECIMAL)
- `abv_percent` (DECIMAL)
- `rating_value` (DECIMAL)
- `rating_count` (INTEGER)
- `image_urls` (JSONB)
- `listing_stats` (JSONB)
- `attrs_json` (JSONB)
- `attrs_norm_json` (JSONB)
- `texts_json` (JSONB) - без полей "Гастрономические сочетания" и "Затрудняетесь с выбором?"
- `new_attr_keys` (JSONB)
- `dedup_key` (VARCHAR)
- `all_product_urls` (JSONB)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

## Примеры запросов

### Получить все товары из России

```sql
SELECT * FROM products WHERE country = 'Россия';
```

### Найти товары по производителю

```sql
SELECT name, price_current, country
FROM products
WHERE producer = 'Кубань-вино';
```

### Поиск по атрибутам (JSONB)

```sql
SELECT name, price_current, attrs_json->>'Цвет' as color
FROM products
WHERE attrs_json->>'Цвет' = 'Белое';
```

### Получить среднюю цену по странам

```sql
SELECT country, AVG(price_current) as avg_price, COUNT(*) as count
FROM products
GROUP BY country
ORDER BY avg_price DESC;
```

## Исключенные поля

При загрузке данных автоматически исключаются следующие поля:

1. `raw_html` (верхнего уровня) - содержит HTML разметку
2. `"Гастрономические сочетания"` (из texts_json)
3. `"Затрудняетесь с выбором?"` (из texts_json)

## Устранение неполадок

### Ошибка подключения к PostgreSQL

Убедитесь, что:
- PostgreSQL запущен
- Указаны правильные учетные данные в `.env` или используются значения по умолчанию
- PostgreSQL принимает подключения на указанном порту

### Ошибка "database already exists"

Это нормально - скрипт пропустит создание БД и перейдет к созданию таблиц.

### Ошибки при загрузке данных

Скрипт продолжит работу при ошибках отдельных записей и покажет итоговую статистику.

## Обслуживание базы данных

### Пересоздание таблицы

```bash
# Подключитесь к БД
psql -U postgres -d amwine_products

# Выполните
DROP TABLE IF EXISTS products CASCADE;

# Затем запустите скрипт создания снова
python create_database.py
```

### Очистка данных

```sql
TRUNCATE TABLE products;
```

## Лицензия

Этот проект создан для внутреннего использования.
