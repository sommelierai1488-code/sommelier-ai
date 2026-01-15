# AmWine Backend

Бэкенд для системы рекомендаций вин AmWine Sommelier AI.

## Структура проекта

```
backend/
├── api/              # API endpoints (в разработке)
├── ml/
│   └── recsys/      # ML модели рекомендательной системы (в разработке)
├── db/              # База данных
│   ├── schema.sql           # Схема БД
│   ├── create_database.py   # Скрипт создания БД
│   ├── db_config.py         # Конфигурация подключения к БД
│   ├── update_products.py   # Скрипт обновления товаров
│   └── migrations/          # Миграции БД
├── .env             # Переменные окружения
└── requirements.txt # Python зависимости
```

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Настройте переменные окружения в `.env`:
```bash
DB_NAME=amwine_products
DB_USER=postgres
DB_HOST=localhost
DB_PORT=5432
DB_PASSWORD=postgres
```

## Работа с базой данных

### Создание базы данных

```bash
cd db
python create_database.py
```

### Обновление товаров

```bash
cd db
python update_products.py /path/to/products.json
```

## База данных

PostgreSQL база данных со следующими таблицами:
- `products` - товары (вина)
- `users` - пользователи
- `sessions` - сессии квизов
- `session_quiz` - ответы на вопросы квиза
- `session_feedback` - лайки/дизлайки товаров
- `session_cart` - корзина товаров
