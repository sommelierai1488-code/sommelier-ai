# Руководство по миграции базы данных

Это руководство объясняет, как применить миграции для добавления новых таблиц в базу данных.

## Структура базы данных

После применения миграций база данных будет содержать следующие таблицы:

1. **products** - Каталог товаров (уже существует)
2. **users** - Пользователи системы
3. **sessions** - Сессии прохождения квиза
4. **session_quiz** - Ответы на вопросы квиза (1:1 с sessions)
5. **session_feedback** - Лайки/дизлайки товаров (N:1 к sessions и products)
6. **session_cart** - Корзина товаров в сессии (N:1 к sessions и products)

## Применение миграции

### Вариант 1: Применить миграцию к существующей БД

Если у вас уже есть база данных с таблицей products и данными:

```bash
python apply_migration.py
```

Этот скрипт:
- Применит миграцию из файла `migrations/001_add_session_tables.sql`
- Создаст все новые таблицы без удаления существующих данных
- Выведет список всех таблиц для проверки

### Вариант 2: Пересоздать всю БД с нуля

Если вы хотите пересоздать базу данных полностью:

```bash
python create_database.py
```

Этот скрипт:
- Создаст базу данных (если не существует)
- Применит полную схему из `schema.sql`
- Создаст все таблицы с нуля (удалит существующие данные!)

**⚠️ ВНИМАНИЕ:** Этот вариант удалит все существующие данные!

## Проверка структуры БД

После применения миграции проверьте структуру:

```bash
python check_database.py
```

## Структура файлов

```
backend/
├── schema.sql                           # Полная схема БД
├── migrations/
│   └── 001_add_session_tables.sql      # Миграция для новых таблиц
├── apply_migration.py                   # Скрипт применения миграций
├── create_database.py                   # Скрипт создания БД с нуля
└── MIGRATION_GUIDE.md                   # Это руководство
```

## Детали таблиц

### users
```sql
user_id (PK, SERIAL)
created_at (TIMESTAMP)
```

### sessions
```sql
session_id (PK, SERIAL)
user_id (FK -> users) или anon_id
status (completed / abandoned)
created_at, updated_at (TIMESTAMP)
```

### session_quiz (1:1 к sessions)
```sql
session_id (PK, FK -> sessions)
occasion, style, drink_type, taste
people_count, budget_bucket, budget_total
created_at (TIMESTAMP)
```

### session_feedback (N:1)
```sql
PRIMARY KEY (session_id, sku)
session_id (FK -> sessions)
sku (FK -> products)
action (like / dislike)
created_at (TIMESTAMP)
```

### session_cart (N:1)
```sql
PRIMARY KEY (session_id, sku)
session_id (FK -> sessions)
sku (FK -> products)
qty, price_at_add
added_at (TIMESTAMP)
```

## Индексы

Все таблицы имеют оптимизированные индексы для:
- Внешних ключей
- Часто используемых полей для фильтрации
- Временных меток

## Триггеры

- `trigger_sessions_updated_at` - автоматически обновляет `updated_at` в таблице `sessions`

## Ограничения (Constraints)

- Проверка статуса сессии: только 'completed' или 'abandoned'
- Проверка действия в feedback: только 'like' или 'dislike'
- Проверка количества в корзине: qty > 0
- Каскадное удаление для зависимых таблиц

## Поддержка

Если возникли проблемы:
1. Проверьте конфигурацию в `db_config.py`
2. Убедитесь, что PostgreSQL запущен
3. Проверьте права доступа к базе данных
