"""
Скрипт для заполнения БД демо-данными с несколькими пользователями
"""

import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

def seed_database():
    """Заполнение базы данных тестовыми данными"""

    conn = sqlite3.connect('mycarexpenses.db')
    cursor = conn.cursor()

    # Очистка существующих данных
    cursor.execute("DELETE FROM expenses")
    cursor.execute("DELETE FROM cars")
    cursor.execute("DELETE FROM users")

    print("=" * 70)
    print("СОЗДАНИЕ ТЕСТОВЫХ ПОЛЬЗОВАТЕЛЕЙ")
    print("=" * 70)
    print()

    # ========================================
    # ПОЛЬЗОВАТЕЛЬ 1: Daniil Hatouchyts (основной)
    # ========================================

    hashed_password = generate_password_hash("demo123")
    cursor.execute("""
        INSERT INTO users (username, email, hashed_password)
        VALUES (?, ?, ?)
    """, ("Daniil Hatouchyts", "hatouchyts.daniil@bsuir.by", hashed_password))

    user1_id = cursor.lastrowid
    print(f"✓ Пользователь 1: Daniil Hatouchyts")
    print(f"  Email: hatouchyts.daniil@bsuir.by")
    print(f"  Пароль: demo123")
    print(f"  ID: {user1_id}")
    print()

    # Автомобиль для пользователя 1
    cursor.execute("""
        INSERT INTO cars (user_id, make, model, year, license_plate, fuel_type)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user1_id, "VAZ", "07", 1988, "BSUIR1", "Бензин"))

    car1_id = cursor.lastrowid
    print(f"  Автомобиль: VAZ-07 1988 (BSUIR1)")
    print()

    # Расходы для пользователя 1 (за последние 6 месяцев)
    categories_expenses_1 = {
        "Топливо": [50, 55, 60, 52, 58, 50],
        "Ремонт": [0, 120, 0, 80, 0, 95],
        "Обслуживание": [0, 0, 75, 0, 65, 0],
        "Страховка": [0, 0, 0, 150, 0, 0],
        "Мойка": [15, 15, 20, 15, 20, 15],
        "Другое": [10, 5, 8, 12, 7, 10]
    }

    base_date = datetime(2024, 5, 1)
    expenses_count = 0

    for month_offset in range(6):
        current_date = base_date + timedelta(days=month_offset * 30)

        for category, amounts in categories_expenses_1.items():
            amount = amounts[month_offset]

            if amount > 0:
                date_str = current_date.strftime("%Y-%m-%d")

                descriptions = {
                    "Топливо": [
                        "Заправка на АЗС Белоруснефть",
                        "Полный бак 95",
                        "Заправка 20 литров",
                        "Дозаправка"
                    ],
                    "Ремонт": [
                        "Замена тормозных колодок",
                        "Ремонт подвески",
                        "Замена аккумулятора",
                        "Замена свечей"
                    ],
                    "Обслуживание": [
                        "ТО-1",
                        "Замена масла и фильтров",
                        "Техосмотр",
                        "Диагностика"
                    ],
                    "Страховка": ["Годовая страховка ОСАГО"],
                    "Мойка": ["Мойка кузова", "Мойка + химчистка салона", "Комплексная мойка"],
                    "Другое": ["Парковка", "Автомойка", "Ароматизатор", "Щетки стеклоочистителя"]
                }

                description = random.choice(descriptions[category])

                cursor.execute("""
                    INSERT INTO expenses (car_id, date, amount, category, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (car1_id, date_str, amount, category, description))

                expenses_count += 1

    print(f"  Добавлено расходов: {expenses_count}")
    print()

    # ========================================
    # ПОЛЬЗОВАТЕЛЬ 2: Ivan Petrov
    # ========================================

    hashed_password_2 = generate_password_hash("pass123")
    cursor.execute("""
        INSERT INTO users (username, email, hashed_password)
        VALUES (?, ?, ?)
    """, ("Ivan Petrov", "ivan.petrov@example.com", hashed_password_2))

    user2_id = cursor.lastrowid
    print(f"✓ Пользователь 2: Ivan Petrov")
    print(f"  Email: ivan.petrov@example.com")
    print(f"  Пароль: pass123")
    print(f"  ID: {user2_id}")
    print()

    # Два автомобиля для пользователя 2
    cursor.execute("""
        INSERT INTO cars (user_id, make, model, year, license_plate, fuel_type)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user2_id, "Toyota", "Camry", 2015, "1234AB-7", "Бензин"))

    car2_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO cars (user_id, make, model, year, license_plate, fuel_type)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user2_id, "Volkswagen", "Polo", 2018, "5678CD-7", "Дизель"))

    car3_id = cursor.lastrowid

    print(f"  Автомобиль 1: Toyota Camry 2015 (1234AB-7)")
    print(f"  Автомобиль 2: Volkswagen Polo 2018 (5678CD-7)")
    print()

    # Расходы для пользователя 2
    expenses_2_count = 0
    for i in range(20):
        days_ago = random.randint(1, 180)
        expense_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        car_id = random.choice([car2_id, car3_id])
        category = random.choice(["Топливо", "Ремонт", "Обслуживание", "Мойка", "Другое"])

        amount_ranges = {
            "Топливо": (40, 70),
            "Ремонт": (50, 200),
            "Обслуживание": (60, 120),
            "Мойка": (10, 25),
            "Другое": (5, 30)
        }

        amount = round(random.uniform(*amount_ranges[category]), 2)
        description = f"{category} - запись {i+1}"

        cursor.execute("""
            INSERT INTO expenses (car_id, date, amount, category, description)
            VALUES (?, ?, ?, ?, ?)
        """, (car_id, expense_date, amount, category, description))

        expenses_2_count += 1

    print(f"  Добавлено расходов: {expenses_2_count}")
    print()

    # ========================================
    # ПОЛЬЗОВАТЕЛЬ 3: Anna Sidorova
    # ========================================

    hashed_password_3 = generate_password_hash("anna2024")
    cursor.execute("""
        INSERT INTO users (username, email, hashed_password)
        VALUES (?, ?, ?)
    """, ("Anna Sidorova", "anna.sidorova@mail.ru", hashed_password_3))

    user3_id = cursor.lastrowid
    print(f"✓ Пользователь 3: Anna Sidorova")
    print(f"  Email: anna.sidorova@mail.ru")
    print(f"  Пароль: anna2024")
    print(f"  ID: {user3_id}")
    print()

    # Автомобиль для пользователя 3
    cursor.execute("""
        INSERT INTO cars (user_id, make, model, year, license_plate, fuel_type)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user3_id, "Mazda", "3", 2020, "9999EF-7", "Бензин"))

    car4_id = cursor.lastrowid
    print(f"  Автомобиль: Mazda 3 2020 (9999EF-7)")
    print()

    # Расходы для пользователя 3
    expenses_3_count = 0
    for i in range(15):
        days_ago = random.randint(1, 120)
        expense_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        category = random.choice(["Топливо", "Обслуживание", "Страховка", "Мойка"])

        amount_ranges = {
            "Топливо": (45, 65),
            "Обслуживание": (70, 150),
            "Страховка": (100, 200),
            "Мойка": (12, 20)
        }

        amount = round(random.uniform(*amount_ranges[category]), 2)
        description = f"{category} #{i+1}"

        cursor.execute("""
            INSERT INTO expenses (car_id, date, amount, category, description)
            VALUES (?, ?, ?, ?, ?)
        """, (car4_id, expense_date, amount, category, description))

        expenses_3_count += 1

    print(f"  Добавлено расходов: {expenses_3_count}")
    print()

    # ========================================
    # ПОЛЬЗОВАТЕЛЬ 4: Dmitry Kozlov
    # ========================================

    hashed_password_4 = generate_password_hash("test123")
    cursor.execute("""
        INSERT INTO users (username, email, hashed_password)
        VALUES (?, ?, ?)
    """, ("Dmitry Kozlov", "dmitry.kozlov@gmail.com", hashed_password_4))

    user4_id = cursor.lastrowid
    print(f"✓ Пользователь 4: Dmitry Kozlov")
    print(f"  Email: dmitry.kozlov@gmail.com")
    print(f"  Пароль: test123")
    print(f"  ID: {user4_id}")
    print()

    # Автомобиль для пользователя 4
    cursor.execute("""
        INSERT INTO cars (user_id, make, model, year, license_plate, fuel_type)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user4_id, "Audi", "A4", 2017, "0000XY-7", "Дизель"))

    car5_id = cursor.lastrowid
    print(f"  Автомобиль: Audi A4 2017 (0000XY-7)")
    print()

    # Расходы для пользователя 4
    expenses_4_count = 0
    for i in range(25):
        days_ago = random.randint(1, 150)
        expense_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        category = random.choice(["Топливо", "Ремонт", "Обслуживание", "Налоги", "Мойка", "Другое"])

        amount_ranges = {
            "Топливо": (50, 80),
            "Ремонт": (100, 300),
            "Обслуживание": (80, 180),
            "Налоги": (50, 150),
            "Мойка": (15, 30),
            "Другое": (10, 50)
        }

        amount = round(random.uniform(*amount_ranges[category]), 2)
        description = f"Расход: {category.lower()}"

        cursor.execute("""
            INSERT INTO expenses (car_id, date, amount, category, description)
            VALUES (?, ?, ?, ?, ?)
        """, (car5_id, expense_date, amount, category, description))

        expenses_4_count += 1

    print(f"  Добавлено расходов: {expenses_4_count}")
    print()

    conn.commit()
    conn.close()

    # Итоговая сводка
    print("=" * 70)
    print("БАЗА ДАННЫХ УСПЕШНО ЗАПОЛНЕНА!")
    print("=" * 70)
    print()
    print("ВСЕГО СОЗДАНО:")
    print(f"  • Пользователей: 4")
    print(f"  • Автомобилей: 5")
    print(f"  • Расходов: {expenses_count + expenses_2_count + expenses_3_count + expenses_4_count}")
    print()
    print("УЧЕТНЫЕ ДАННЫЕ ДЛЯ ВХОДА:")
    print("-" * 70)
    print("1. Email: hatouchyts.daniil@bsuir.by  | Пароль: demo123")
    print("2. Email: ivan.petrov@example.com     | Пароль: pass123")
    print("3. Email: anna.sidorova@mail.ru       | Пароль: anna2024")
    print("4. Email: dmitry.kozlov@gmail.com     | Пароль: test123")
    print("-" * 70)

if __name__ == "__main__":
    seed_database()
