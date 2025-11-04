"""
MyCarExpenses Backend API
Простой REST API на Flask для управления расходами на автомобиль
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import jwt
import datetime
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
CORS(app)  # Разрешаем запросы с фронтенда

# Инициализация базы данных
def init_db():
    """Создание таблиц в БД"""
    conn = sqlite3.connect('mycarexpenses.db')
    cursor = conn.cursor()

    # Таблица пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL
        )
    """)

    # Таблица автомобилей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cars (
            car_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            year INTEGER,
            license_plate TEXT,
            fuel_type TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # Таблица расходов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            FOREIGN KEY (car_id) REFERENCES cars(car_id)
        )
    """)

    conn.commit()
    conn.close()

# Декоратор для проверки токена
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'message': 'Токен отсутствует'}), 401

        try:
            # Убираем "Bearer " если есть
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user_id = data['user_id']
        except:
            return jsonify({'message': 'Неверный токен'}), 401

        return f(current_user_id, *args, **kwargs)

    return decorated

# ============ АУТЕНТИФИКАЦИЯ ============

@app.route('/api/register', methods=['POST'])
def register():
    """Регистрация нового пользователя"""
    data = request.json

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'message': 'Все поля обязательны'}), 400

    conn = sqlite3.connect('mycarexpenses.db')
    cursor = conn.cursor()

    try:
        hashed_password = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (username, email, hashed_password) VALUES (?, ?, ?)",
            (username, email, hashed_password)
        )
        conn.commit()

        return jsonify({'message': 'Пользователь зарегистрирован'}), 201

    except sqlite3.IntegrityError:
        return jsonify({'message': 'Пользователь уже существует'}), 409

    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    """Вход пользователя"""
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email и пароль обязательны'}), 400

    conn = sqlite3.connect('mycarexpenses.db')
    cursor = conn.cursor()

    cursor.execute("SELECT user_id, username, hashed_password FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if not user or not check_password_hash(user[2], password):
        return jsonify({'message': 'Неверный email или пароль'}), 401

    # Генерация JWT токена
    token = jwt.encode({
        'user_id': user[0],
        'username': user[1],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({
        'token': token,
        'user': {
            'user_id': user[0],
            'username': user[1],
            'email': email
        }
    }), 200

# ============ АВТОМОБИЛИ ============

@app.route('/api/cars', methods=['GET'])
@token_required
def get_cars(current_user_id):
    """Получить все автомобили пользователя"""
    conn = sqlite3.connect('mycarexpenses.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT car_id, make, model, year, license_plate, fuel_type
        FROM cars WHERE user_id = ?
    """, (current_user_id,))

    cars = []
    for row in cursor.fetchall():
        cars.append({
            'car_id': row[0],
            'make': row[1],
            'model': row[2],
            'year': row[3],
            'license_plate': row[4],
            'fuel_type': row[5]
        })

    conn.close()
    return jsonify(cars), 200

@app.route('/api/cars', methods=['POST'])
@token_required
def add_car(current_user_id):
    """Добавить новый автомобиль"""
    data = request.json

    make = data.get('make')
    model = data.get('model')
    year = data.get('year')
    license_plate = data.get('license_plate')
    fuel_type = data.get('fuel_type')

    if not make or not model:
        return jsonify({'message': 'Марка и модель обязательны'}), 400

    conn = sqlite3.connect('mycarexpenses.db')
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO cars (user_id, make, model, year, license_plate, fuel_type)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (current_user_id, make, model, year, license_plate, fuel_type))

    car_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({'car_id': car_id, 'message': 'Автомобиль добавлен'}), 201

@app.route('/api/cars/<int:car_id>', methods=['DELETE'])
@token_required
def delete_car(current_user_id, car_id):
    """Удалить автомобиль"""
    conn = sqlite3.connect('mycarexpenses.db')
    cursor = conn.cursor()

    # Проверка принадлежности автомобиля пользователю
    cursor.execute("SELECT user_id FROM cars WHERE car_id = ?", (car_id,))
    result = cursor.fetchone()

    if not result or result[0] != current_user_id:
        conn.close()
        return jsonify({'message': 'Автомобиль не найден'}), 404

    cursor.execute("DELETE FROM cars WHERE car_id = ?", (car_id,))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Автомобиль удален'}), 200

# ============ РАСХОДЫ ============

@app.route('/api/expenses', methods=['GET'])
@token_required
def get_expenses(current_user_id):
    """Получить все расходы пользователя"""
    car_id = request.args.get('car_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category = request.args.get('category')

    conn = sqlite3.connect('mycarexpenses.db')
    cursor = conn.cursor()

    # Базовый запрос с проверкой прав доступа
    query = """
        SELECT e.expense_id, e.car_id, e.date, e.amount, e.category, e.description
        FROM expenses e
        JOIN cars c ON e.car_id = c.car_id
        WHERE c.user_id = ?
    """
    params = [current_user_id]

    # Добавляем фильтры
    if car_id:
        query += " AND e.car_id = ?"
        params.append(car_id)
    if start_date:
        query += " AND e.date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND e.date <= ?"
        params.append(end_date)
    if category:
        query += " AND e.category = ?"
        params.append(category)

    query += " ORDER BY e.date DESC"

    cursor.execute(query, params)

    expenses = []
    for row in cursor.fetchall():
        expenses.append({
            'expense_id': row[0],
            'car_id': row[1],
            'date': row[2],
            'amount': row[3],
            'category': row[4],
            'description': row[5]
        })

    conn.close()
    return jsonify(expenses), 200

@app.route('/api/expenses', methods=['POST'])
@token_required
def add_expense(current_user_id):
    """Добавить новый расход"""
    data = request.json

    car_id = data.get('car_id')
    date = data.get('date')
    amount = data.get('amount')
    category = data.get('category')
    description = data.get('description', '')

    if not car_id or not date or not amount or not category:
        return jsonify({'message': 'Обязательные поля: car_id, date, amount, category'}), 400

    conn = sqlite3.connect('mycarexpenses.db')
    cursor = conn.cursor()

    # Проверка принадлежности автомобиля пользователю
    cursor.execute("SELECT user_id FROM cars WHERE car_id = ?", (car_id,))
    result = cursor.fetchone()

    if not result or result[0] != current_user_id:
        conn.close()
        return jsonify({'message': 'Автомобиль не найден'}), 404

    cursor.execute("""
        INSERT INTO expenses (car_id, date, amount, category, description)
        VALUES (?, ?, ?, ?, ?)
    """, (car_id, date, amount, category, description))

    expense_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({'expense_id': expense_id, 'message': 'Расход добавлен'}), 201

@app.route('/api/expenses/<int:expense_id>', methods=['PUT'])
@token_required
def update_expense(current_user_id, expense_id):
    """Обновить расход"""
    data = request.json

    conn = sqlite3.connect('mycarexpenses.db')
    cursor = conn.cursor()

    # Проверка прав доступа
    cursor.execute("""
        SELECT e.expense_id FROM expenses e
        JOIN cars c ON e.car_id = c.car_id
        WHERE e.expense_id = ? AND c.user_id = ?
    """, (expense_id, current_user_id))

    if not cursor.fetchone():
        conn.close()
        return jsonify({'message': 'Расход не найден'}), 404

    # Обновление полей
    updates = []
    params = []

    if 'date' in data:
        updates.append("date = ?")
        params.append(data['date'])
    if 'amount' in data:
        updates.append("amount = ?")
        params.append(data['amount'])
    if 'category' in data:
        updates.append("category = ?")
        params.append(data['category'])
    if 'description' in data:
        updates.append("description = ?")
        params.append(data['description'])

    if not updates:
        conn.close()
        return jsonify({'message': 'Нет данных для обновления'}), 400

    params.append(expense_id)
    query = f"UPDATE expenses SET {', '.join(updates)} WHERE expense_id = ?"

    cursor.execute(query, params)
    conn.commit()
    conn.close()

    return jsonify({'message': 'Расход обновлен'}), 200

@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
@token_required
def delete_expense(current_user_id, expense_id):
    """Удалить расход"""
    conn = sqlite3.connect('mycarexpenses.db')
    cursor = conn.cursor()

    # Проверка прав доступа
    cursor.execute("""
        SELECT e.expense_id FROM expenses e
        JOIN cars c ON e.car_id = c.car_id
        WHERE e.expense_id = ? AND c.user_id = ?
    """, (expense_id, current_user_id))

    if not cursor.fetchone():
        conn.close()
        return jsonify({'message': 'Расход не найден'}), 404

    cursor.execute("DELETE FROM expenses WHERE expense_id = ?", (expense_id,))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Расход удален'}), 200

# ============ АНАЛИТИКА ============

@app.route('/api/analytics/summary', methods=['GET'])
@token_required
def get_summary(current_user_id):
    """Получить сводную статистику"""
    car_id = request.args.get('car_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    conn = sqlite3.connect('mycarexpenses.db')
    cursor = conn.cursor()

    # Общая сумма расходов
    query = """
        SELECT SUM(e.amount), COUNT(e.expense_id)
        FROM expenses e
        JOIN cars c ON e.car_id = c.car_id
        WHERE c.user_id = ?
    """
    params = [current_user_id]

    if car_id:
        query += " AND e.car_id = ?"
        params.append(car_id)
    if start_date:
        query += " AND e.date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND e.date <= ?"
        params.append(end_date)

    cursor.execute(query, params)
    total, count = cursor.fetchone()

    # Расходы по категориям
    query_cat = """
        SELECT e.category, SUM(e.amount)
        FROM expenses e
        JOIN cars c ON e.car_id = c.car_id
        WHERE c.user_id = ?
    """
    params_cat = [current_user_id]

    if car_id:
        query_cat += " AND e.car_id = ?"
        params_cat.append(car_id)
    if start_date:
        query_cat += " AND e.date >= ?"
        params_cat.append(start_date)
    if end_date:
        query_cat += " AND e.date <= ?"
        params_cat.append(end_date)

    query_cat += " GROUP BY e.category"

    cursor.execute(query_cat, params_cat)
    categories = {}
    for row in cursor.fetchall():
        categories[row[0]] = row[1]

    conn.close()

    return jsonify({
        'total_amount': total or 0,
        'total_count': count or 0,
        'by_category': categories
    }), 200

# ============ ЗАПУСК ============

if __name__ == '__main__':
    init_db()
    print("База данных инициализирована")
    print("Сервер запущен на http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
