# API Documentation

REST API для мобильного приложения AmWine - рекомендации алкогольных напитков.

## Base URL

```
http://your-server-ip:8000
```

## Endpoints Overview

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/sessions/start` | Создать новую сессию |
| POST | `/sessions/{session_id}/quiz` | Сохранить ответы квиза |
| POST | `/offers/recommend` | Получить рекомендации товаров |
| POST | `/session/events` | Записать события (лайки/дизлайки) батчем |
| POST | `/sessions/{session_id}/cart` | Добавить товар в корзину |
| GET | `/sessions/{session_id}/cart` | Получить корзину |
| DELETE | `/sessions/{session_id}/cart/{sku}` | Удалить товар из корзины |
| POST | `/sessions/{session_id}/complete` | Завершить сессию |

---

## Recommended Flow (Рекомендуемый порядок вызовов)

```
1. Welcome Screen → "Start"
   └─> POST /sessions/start

2. Quiz Completed → "Перейти к подбору напитков"
   ├─> POST /sessions/{session_id}/quiz
   └─> POST /offers/recommend

3. User Swipes Products (like/dislike/none)
   └─> POST /session/events (batch, flush on background)

4. User Adds to Cart → "Забронировать заказ"
   └─> POST /sessions/{session_id}/cart

5. User Views Cart
   └─> GET /sessions/{session_id}/cart

6. User Confirms Booking
   └─> POST /sessions/{session_id}/complete
```

---

## Detailed Endpoints

### 1. Start Session

Создание новой сессии при начале работы с приложением.

**Endpoint:** `POST /sessions/start`

**Request Body:**
```json
{
  "user_id": null
}
```

**Response:**
```json
{
  "session_id": 1,
  "status": "in_progress",
  "created_at": "2024-01-15T10:30:00"
}
```

**Когда вызывать:**
- При нажатии "Start" на Welcome Screen
- Или при первом появлении QuizView

---

### 2. Save Quiz Answers

Сохранение (UPSERT) ответов квиза для сессии.

**Endpoint:** `POST /sessions/{session_id}/quiz`

**Request Body:**
```json
{
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
```

**Response:**
```json
{
  "success": true,
  "session_id": 1,
  "message": "Quiz answers saved successfully"
}
```

**Когда вызывать:**
- Сразу после нажатия "Перейти к подбору напитков"
- ПЕРЕД вызовом `/offers/recommend`

**Важно:**
- Поддерживает UPSERT - если пользователь вернется и изменит ответы, они обновятся
- `drink_types` и `tastes` - массивы (multi-select)

---

### 3. Get Recommendations

Получение рекомендованных товаров на основе квиза.

**Endpoint:** `POST /offers/recommend`

**Request Body:**
```json
{
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
```

**Response:**
```json
{
  "offers": [
    {
      "id": "121633",
      "description": "Riga Black Balsam 0.5л",
      "image": "https://example.com/image.jpg",
      "url": "https://example.com/product/121633",
      "price_raw": "999 ₽"
    },
    {
      "id": "121634",
      "description": "Product Name",
      "image": "https://example.com/image2.jpg",
      "url": "https://example.com/product/121634",
      "price_raw": "1499 ₽"
    }
  ]
}
```

**Когда вызывать:**
- После сохранения квиза
- При переходе к экрану со свайпами

**Note:**
- Сейчас возвращает случайные товары
- ML-фильтрация будет добавлена позже

---

### 4. Record Session Events (Batch)

Пакетная запись событий взаимодействия пользователя с товарами (лайки, дизлайки).

**Endpoint:** `POST /session/events`

**Request Body:**
```json
{
  "session_id": 1,
  "events": [
    {"sku": "121633", "action": "like"},
    {"sku": "121634", "action": "dislike"},
    {"sku": "121635", "action": "none"}
  ]
}
```

**Response:**
```json
{
  "success": true,
  "inserted_count": 3,
  "message": "Successfully inserted 3 events"
}
```

**Когда вызывать:**

**Рекомендуемый паттерн:**
1. Локально складывайте события в очередь `pendingEvents`
2. Отправляйте батчем:
   - Каждые N событий (например, 5-10 свайпов)
   - При уходе в background (flush)
   - Fire-and-forget (не блокируйте UI)

**Action types:**
- `"like"` - пользователь лайкнул товар
- `"dislike"` - пользователь дизлайкнул товар
- `"none"` - нейтральное взаимодействие (показ без реакции)

---

### 5. Add to Cart

Добавление товара в корзину или обновление количества (UPSERT).

**Endpoint:** `POST /sessions/{session_id}/cart`

**Request Body:**
```json
{
  "sku": "121633",
  "qty": 2,
  "price_at_add": 999.0
}
```

**Response:**
```json
{
  "success": true,
  "message": "Item added to cart successfully"
}
```

**Когда вызывать:**
- При нажатии "Забронировать заказ"
- При изменении количества товара в корзине

**Важно:**
- Поддерживает UPSERT по `(session_id, sku)`
- Если товар уже в корзине - обновляется `qty` и `price_at_add`

---

### 6. Get Cart

Получение содержимого корзины для сессии.

**Endpoint:** `GET /sessions/{session_id}/cart`

**Response:**
```json
{
  "session_id": 1,
  "items": [
    {
      "sku": "121633",
      "qty": 2,
      "price_at_add": 999.0
    },
    {
      "sku": "121634",
      "qty": 1,
      "price_at_add": 1499.0
    }
  ],
  "total_items": 3,
  "total_price": 3497.0
}
```

**Когда вызывать:**
- При открытии экрана корзины
- После добавления товара для обновления UI

---

### 7. Remove from Cart

Удаление товара из корзины.

**Endpoint:** `DELETE /sessions/{session_id}/cart/{sku}`

**Response:**
```json
{
  "success": true,
  "message": "Item removed from cart successfully"
}
```

**Когда вызывать:**
- При удалении товара из корзины пользователем

---

### 8. Complete Session

Завершение сессии (установка статуса `completed`).

**Endpoint:** `POST /sessions/{session_id}/complete`

**Response:**
```json
{
  "success": true,
  "session_id": 1,
  "status": "completed",
  "message": "Session completed successfully"
}
```

**Когда вызывать:**
- При подтверждении брони
- При завершении заказа

---

## Health Check Endpoints

### Health Check
```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "AmWine Recommendations API",
  "version": "1.0.0"
}
```

### Root
```
GET /
```

**Response:**
```json
{
  "status": "ok",
  "service": "AmWine Recommendations API",
  "version": "1.0.0"
}
```

---

## Error Responses

Все endpoints возвращают стандартные HTTP статус-коды:

**Success:**
- `200 OK` - успешный запрос

**Client Errors:**
- `400 Bad Request` - неверные данные в запросе
- `404 Not Found` - ресурс не найден

**Server Errors:**
- `500 Internal Server Error` - ошибка на сервере

**Error Format:**
```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Interactive API Documentation

После запуска сервера доступна интерактивная документация:

- **Swagger UI:** `http://your-server-ip:8000/docs`
- **ReDoc:** `http://your-server-ip:8000/redoc`

---

## Database Schema

### Tables

1. **users** - пользователи (анонимные или зарегистрированные)
2. **sessions** - сессии пользователей (статус: in_progress, completed, abandoned)
3. **session_quiz** - ответы на квиз (1:1 с sessions)
4. **session_events** - события взаимодействия с товарами (река событий)
5. **session_cart** - финальная корзина
6. **products** - каталог товаров (только для чтения)

### Session Lifecycle

```
in_progress → completed
            ↘ abandoned (если не завершена)
```

---

## Implementation Notes for Mobile App

### 1. Session Management
```swift
// При старте приложения
let session = await startSession()
UserDefaults.standard.set(session.session_id, forKey: "session_id")
```

### 2. Event Queue Pattern
```swift
class EventQueue {
    private var pendingEvents: [SessionEvent] = []
    private let batchSize = 10

    func addEvent(sku: String, action: String) {
        pendingEvents.append(SessionEvent(sku: sku, action: action))

        if pendingEvents.count >= batchSize {
            flush()
        }
    }

    func flush() {
        // Send batch to API
        API.sendEvents(sessionId: currentSessionId, events: pendingEvents)
        pendingEvents.removeAll()
    }
}

// В SceneDelegate/AppDelegate
func sceneDidEnterBackground(_ scene: UIScene) {
    EventQueue.shared.flush()
}
```

### 3. Error Handling
```swift
do {
    let result = try await API.addToCart(...)
} catch {
    // Show user-friendly error
    showError("Не удалось добавить товар в корзину")
}
```

---

## Setup & Running

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Create database:
```bash
cd backend/db
python create_database.py
```

3. Run API server:
```bash
cd backend/api
uvicorn main:app --host 0.0.0.0 --port 8000
```

4. Access API:
```
http://your-server-ip:8000
```
