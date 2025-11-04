# MyCarExpenses Backend API

Простой REST API на Flask для управления расходами на автомобиль.

## Установка и запуск

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Запуск сервера

```bash
python app.py
```

Сервер запустится на `http://localhost:5000`

## API Endpoints

### Аутентификация

#### Регистрация
```http
POST /api/register
Content-Type: application/json

{
  "username": "daniil",
  "email": "hatouchyts.daniil@bsuir.by",
  "password": "password123"
}
```

#### Вход
```http
POST /api/login
Content-Type: application/json

{
  "email": "hatouchyts.daniil@bsuir.by",
  "password": "password123"
}
```

Ответ:
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "user_id": 1,
    "username": "daniil",
    "email": "hatouchyts.daniil@bsuir.by"
  }
}
```

### Автомобили

#### Получить все автомобили
```http
GET /api/cars
Authorization: Bearer <token>
```

#### Добавить автомобиль
```http
POST /api/cars
Authorization: Bearer <token>
Content-Type: application/json

{
  "make": "VAZ",
  "model": "07",
  "year": 1988,
  "license_plate": "BSUIR1",
  "fuel_type": "Бензин"
}
```

#### Удалить автомобиль
```http
DELETE /api/cars/<car_id>
Authorization: Bearer <token>
```

### Расходы

#### Получить расходы
```http
GET /api/expenses?car_id=1&start_date=2024-09-01&end_date=2024-09-30&category=Топливо
Authorization: Bearer <token>
```

Параметры (все необязательные):
- `car_id` - фильтр по автомобилю
- `start_date` - начальная дата (YYYY-MM-DD)
- `end_date` - конечная дата (YYYY-MM-DD)
- `category` - категория расходов

#### Добавить расход
```http
POST /api/expenses
Authorization: Bearer <token>
Content-Type: application/json

{
  "car_id": 1,
  "date": "2024-11-04",
  "amount": 50.00,
  "category": "Топливо",
  "description": "Заправка"
}
```

Категории:
- Топливо
- Ремонт
- Обслуживание
- Страховка
- Налоги
- Мойка
- Другое

#### Обновить расход
```http
PUT /api/expenses/<expense_id>
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": 55.00,
  "description": "Заправка полный бак"
}
```

#### Удалить расход
```http
DELETE /api/expenses/<expense_id>
Authorization: Bearer <token>
```

### Аналитика

#### Получить сводную статистику
```http
GET /api/analytics/summary?car_id=1&start_date=2024-09-01&end_date=2024-09-30
Authorization: Bearer <token>
```

Ответ:
```json
{
  "total_amount": 325.50,
  "total_count": 12,
  "by_category": {
    "Топливо": 180.30,
    "Ремонт": 80.00,
    "Обслуживание": 65.20
  }
}
```

## База данных

Используется SQLite (`mycarexpenses.db`). База данных создается автоматически при первом запуске.

### Структура таблиц

**users**
- user_id (INTEGER, PRIMARY KEY)
- username (TEXT, UNIQUE)
- email (TEXT, UNIQUE)
- hashed_password (TEXT)

**cars**
- car_id (INTEGER, PRIMARY KEY)
- user_id (INTEGER, FOREIGN KEY)
- make (TEXT)
- model (TEXT)
- year (INTEGER)
- license_plate (TEXT)
- fuel_type (TEXT)

**expenses**
- expense_id (INTEGER, PRIMARY KEY)
- car_id (INTEGER, FOREIGN KEY)
- date (TEXT)
- amount (REAL)
- category (TEXT)
- description (TEXT)

## Безопасность

- Пароли хешируются с помощью Werkzeug
- Аутентификация через JWT токены
- Токены действительны 7 дней
- CORS включен для работы с фронтендом

## Примечания

- Для продакшена замените `SECRET_KEY` на надежный ключ
- Настройте CORS для конкретных доменов
- Добавьте SSL сертификаты (HTTPS)
- Рассмотрите использование PostgreSQL вместо SQLite

## Тестирование

Можно использовать curl, Postman или httpie для тестирования API.

Пример с curl:

```bash
# Регистрация
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"daniil","email":"test@bsuir.by","password":"pass123"}'

# Вход
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@bsuir.by","password":"pass123"}'

# Добавить автомобиль (замените <TOKEN> на полученный токен)
curl -X POST http://localhost:5000/api/cars \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"make":"VAZ","model":"07","year":1988,"license_plate":"BSUIR1"}'
```
