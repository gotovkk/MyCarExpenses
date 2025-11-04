/**
 * MyCarExpenses - Приложение для учета расходов на автомобиль
 * ВЕРСИЯ С ПОДКЛЮЧЕНИЕМ К FLASK BACKEND API + DEBUGGING
 */

// ========================================
// КОНФИГУРАЦИЯ API
// ========================================

const API_BASE_URL = 'http://localhost:5000/api';

// ========================================
// СОСТОЯНИЕ ПРИЛОЖЕНИЯ
// ========================================

const appState = {
    currentUser: null,
    currentPage: 'login',
    token: null,
    cars: [],
    expenses: [],
    editingExpenseId: null,
    confirmCallback: null,
    charts: {},
    loading: false,
    error: null,
    categories: ['Топливо', 'Ремонт', 'Обслуживание', 'Страховка', 'Налоги', 'Мойка', 'Другое'],
    maintenance: {
        nextServiceDate: '25.10.2025',
        lastTireChange: '05.05.2024',
        lastOilChange: '01.09.2023'
    }
};

// ========================================
// API ЗАПРОСЫ
// ========================================

class ApiClient {
    static async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;

        console.log('🔵 API Request:', {
            url,
            method: options.method || 'GET',
            body: options.body ? JSON.parse(options.body) : null
        });

        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (appState.token) {
            headers['Authorization'] = `Bearer ${appState.token}`;
            console.log('🔑 Token attached:', appState.token.substring(0, 20) + '...');
        }

        try {
            appState.loading = true;
            const response = await fetch(url, {
                ...options,
                headers
            });

            console.log('📥 Response status:', response.status, response.statusText);

            if (!response.ok) {
                const error = await response.json();
                console.error('❌ API Error:', error);
                throw new Error(error.message || `HTTP ${response.status}`);
            }

            const data = await response.json();
            console.log('✅ API Success:', data);

            appState.loading = false;
            return data;
        } catch (error) {
            appState.loading = false;
            appState.error = error.message;
            console.error('💥 Request failed:', error);
            throw error;
        }
    }

    static async register(username, email, password) {
        console.log('📝 Registering user:', email);
        return this.request('/register', {
            method: 'POST',
            body: JSON.stringify({ username, email, password })
        });
    }

    static async login(email, password) {
        console.log('🔐 Logging in:', email);
        const response = await this.request('/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });

        if (response.token) {
            appState.token = response.token;
            appState.currentUser = response.user;
            localStorage.setItem('token', response.token);
            localStorage.setItem('user', JSON.stringify(response.user));
            console.log('✅ Login successful, token saved');
        }

        return response;
    }

    static async getCars() {
        console.log('🚗 Fetching cars...');
        return this.request('/cars');
    }

    static async addCar(carData) {
        console.log('➕ Adding car:', carData);
        return this.request('/cars', {
            method: 'POST',
            body: JSON.stringify(carData)
        });
    }

    static async deleteCar(carId) {
        console.log('🗑️ Deleting car:', carId);
        return this.request(`/cars/${carId}`, {
            method: 'DELETE'
        });
    }

    static async getExpenses(filters = {}) {
        console.log('💰 Fetching expenses with filters:', filters);
        const params = new URLSearchParams();
        if (filters.car_id) params.append('car_id', filters.car_id);
        if (filters.start_date) params.append('start_date', filters.start_date);
        if (filters.end_date) params.append('end_date', filters.end_date);
        if (filters.category) params.append('category', filters.category);

        const query = params.toString() ? `?${params.toString()}` : '';
        return this.request(`/expenses${query}`);
    }

    static async addExpense(expenseData) {
        console.log('➕ Adding expense:', expenseData);
        return this.request('/expenses', {
            method: 'POST',
            body: JSON.stringify(expenseData)
        });
    }

    static async updateExpense(expenseId, expenseData) {
        console.log('✏️ Updating expense:', expenseId, expenseData);
        return this.request(`/expenses/${expenseId}`, {
            method: 'PUT',
            body: JSON.stringify(expenseData)
        });
    }

    static async deleteExpense(expenseId) {
        console.log('🗑️ Deleting expense:', expenseId);
        return this.request(`/expenses/${expenseId}`, {
            method: 'DELETE'
        });
    }

    static async getSummary(filters = {}) {
        console.log('📊 Fetching summary with filters:', filters);
        const params = new URLSearchParams();
        if (filters.car_id) params.append('car_id', filters.car_id);
        if (filters.start_date) params.append('start_date', filters.start_date);
        if (filters.end_date) params.append('end_date', filters.end_date);

        const query = params.toString() ? `?${params.toString()}` : '';
        return this.request(`/analytics/summary${query}`);
    }
}

// ========================================
// ПРИЛОЖЕНИЕ
// ========================================

class App {
    constructor() {
        console.log('🚀 App initialization...');
        this.state = appState;
        this.init();
    }

    init() {
        const savedToken = localStorage.getItem('token');
        const savedUser = localStorage.getItem('user');

        console.log('🔍 Checking saved session:', {
            hasToken: !!savedToken,
            hasUser: !!savedUser
        });

        if (savedToken && savedUser) {
            this.state.token = savedToken;
            this.state.currentUser = JSON.parse(savedUser);
            console.log('✅ Session restored:', this.state.currentUser);
            this.setupEventListeners();
            this.navigateTo('dashboard');
            this.loadData();
        } else {
            console.log('ℹ️ No saved session, showing login page');
            this.setupEventListeners();
            this.navigateTo('login');
        }
    }

    setupEventListeners() {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const page = e.currentTarget.getAttribute('data-page');
                this.navigateTo(page);
            });
        });

        const expenseForm = document.getElementById('expense-form');
        if (expenseForm) {
            expenseForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveExpense();
            });
        }

        const carForm = document.getElementById('car-form');
        if (carForm) {
            carForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveCar();
            });
        }
    }

    async loadData() {
        console.log('📦 Loading user data...');
        try {
            const [cars, expenses] = await Promise.all([
                ApiClient.getCars(),
                ApiClient.getExpenses()
            ]);

            this.state.cars = cars;
            this.state.expenses = expenses;
            console.log('✅ Data loaded:', {
                cars: cars.length,
                expenses: expenses.length
            });
        } catch (error) {
            console.error('❌ Failed to load data:', error);
        }
    }

    navigateTo(page) {
        console.log('🧭 Navigating to:', page);
        this.state.currentPage = page;
        const app = document.getElementById('app');
        const bottomNav = document.getElementById('bottom-nav');

        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('data-page') === page) {
                item.classList.add('active');
            }
        });

        if (page === 'login') {
            bottomNav.classList.add('hidden');
        } else {
            bottomNav.classList.remove('hidden');
        }

        switch (page) {
            case 'login':
                this.renderLoginPage();
                break;
            case 'dashboard':
                this.renderDashboard();
                break;
            case 'analytics':
                this.renderAnalytics();
                break;
            case 'cars':
                this.renderCars();
                break;
            case 'profile':
                this.renderProfile();
                break;
        }
    }

    renderLoginPage() {
        const app = document.getElementById('app');
        app.innerHTML = `
            <div class="login-container">
                <div class="login-card">
                    <div class="login-header">
                        <h1>MyCarExpenses</h1>
                        <p>Трекер расходов на автомобиль</p>
                    </div>
                    <form class="login-form" onsubmit="app.handleLogin(event)">
                        <div class="form-group">
                            <label for="login-email">Email</label>
                            <input type="email" id="login-email" value="hatouchyts.daniil@bsuir.by" required>
                        </div>
                        <div class="form-group">
                            <label for="login-password">Пароль</label>
                            <input type="password" id="login-password" value="demo123" required>
                        </div>
                        <button type="submit" class="btn btn-primary btn-full">Войти</button>
                    </form>
                    <div class="login-footer">
                        <p>Нет аккаунта? <a href="#" onclick="app.showRegisterForm(event)">Зарегистрироваться</a></p>
                        <p style="margin-top: 10px; font-size: 12px; color: #999;">
                            Откройте консоль (F12) для просмотра логов
                        </p>
                    </div>
                </div>
            </div>
        `;
    }

    async handleLogin(event) {
        event.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;

        console.log('🔐 Attempting login...');
        try {
            await ApiClient.login(email, password);
            await this.loadData();
            this.navigateTo('dashboard');
        } catch (error) {
            console.error('❌ Login failed:', error);
            alert('Ошибка входа: ' + error.message + '\n\nПроверьте консоль (F12) для деталей');
        }
    }

    showRegisterForm(event) {
        event.preventDefault();
        const app = document.getElementById('app');
        app.innerHTML = `
            <div class="login-container">
                <div class="login-card">
                    <div class="login-header">
                        <h1>Регистрация</h1>
                        <p>Создайте новый аккаунт</p>
                    </div>
                    <form class="login-form" onsubmit="app.handleRegister(event)">
                        <div class="form-group">
                            <label for="reg-username">Имя пользователя</label>
                            <input type="text" id="reg-username" required>
                        </div>
                        <div class="form-group">
                            <label for="reg-email">Email</label>
                            <input type="email" id="reg-email" required>
                        </div>
                        <div class="form-group">
                            <label for="reg-password">Пароль</label>
                            <input type="password" id="reg-password" required>
                        </div>
                        <button type="submit" class="btn btn-primary btn-full">Зарегистрироваться</button>
                    </form>
                    <div class="login-footer">
                        <p><a href="#" onclick="app.navigateTo('login')">Вернуться к входу</a></p>
                    </div>
                </div>
            </div>
        `;
    }

    async handleRegister(event) {
        event.preventDefault();
        const username = document.getElementById('reg-username').value;
        const email = document.getElementById('reg-email').value;
        const password = document.getElementById('reg-password').value;

        try {
            await ApiClient.register(username, email, password);
            alert('Регистрация успешна! Пожалуйста, войдите.');
            this.navigateTo('login');
        } catch (error) {
            alert('Ошибка регистрации: ' + error.message);
        }
    }

    async renderDashboard() {
        const currentMonth = new Date().toLocaleDateString('ru-RU', { month: 'long' });
        const currentMonthStart = new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0];
        const currentMonthEnd = new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).toISOString().split('T')[0];

        try {
            const summary = await ApiClient.getSummary({
                start_date: currentMonthStart,
                end_date: currentMonthEnd
            });

            const app = document.getElementById('app');
            app.innerHTML = `
                <div class="page-container">
                    <div class="page-header">
                        <h1>MyCarExpenses</h1>
                        <p>Трекер расходов на автомобиль</p>
                    </div>

                    <div class="total-expenses">
                        <h2>Общие расходы</h2>
                        <div class="amount">${this.formatCurrency(summary.total_amount)}</div>
                    </div>

                    <button class="btn btn-primary btn-full mb-3" onclick="app.openExpenseModal()">
                        Добавить расход
                    </button>

                    <div class="stats-section">
                        <div class="section-header">
                            <h3 class="section-title">Статистика за ${currentMonth}</h3>
                        </div>
                        <div class="chart-container">
                            <canvas id="category-chart"></canvas>
                        </div>
                        ${this.renderCategoryBreakdown(summary.by_category)}
                    </div>

                    <div class="maintenance-card">
                        <h3>Плановое ТО</h3>
                        <p>Следующее: ${this.state.maintenance.nextServiceDate}</p>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">Последние расходы</h3>
                        </div>
                        <div class="expenses-list">
                            ${this.renderRecentExpenses(this.state.expenses.slice(-5).reverse())}
                        </div>
                    </div>
                </div>
            `;

            setTimeout(() => this.renderPieChart('category-chart', summary.by_category), 100);
        } catch (error) {
            console.error('Ошибка загрузки dashboard:', error);
        }
    }

    renderCategoryBreakdown(categoryData) {
        if (!categoryData || Object.keys(categoryData).length === 0) {
            return '<div class="empty-state"><p>Нет расходов</p></div>';
        }

        const items = Object.entries(categoryData)
            .sort(([_, a], [__, b]) => b - a)
            .map(([category, amount]) => `
                <div class="category-item">
                    <div class="category-info">
                        <div class="category-icon">${this.getCategoryIcon(category)}</div>
                        <div class="category-name">${category}</div>
                    </div>
                    <div class="category-amount">${this.formatCurrency(amount)}</div>
                </div>
            `).join('');

        return `<div class="category-list">${items}</div>`;
    }

    renderRecentExpenses(expenses) {
        if (expenses.length === 0) {
            return '<div class="empty-state"><p>Нет расходов</p></div>';
        }

        return expenses.map(expense => `
            <div class="expense-item">
                <div class="expense-info">
                    <div class="expense-category">${this.getCategoryIcon(expense.category)} ${expense.category}</div>
                    <div class="expense-description">${expense.description || 'Без описания'}</div>
                    <div class="expense-date">${this.formatDate(expense.date)}</div>
                </div>
                <div class="expense-amount">${this.formatCurrency(expense.amount)}</div>
                <div class="expense-actions">
                    <button class="btn-icon" onclick="app.editExpense(${expense.expense_id})">✎</button>
                    <button class="btn-icon" onclick="app.deleteExpense(${expense.expense_id})">✕</button>
                </div>
            </div>
        `).join('');
    }

    async renderAnalytics() {
        try {
            const summary = await ApiClient.getSummary();

            const app = document.getElementById('app');
            app.innerHTML = `
                <div class="analytics-container">
                    <div class="page-header">
                        <h1>Аналитика</h1>
                        <p>Анализ расходов</p>
                    </div>

                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="label">Всего расходов</div>
                            <div class="value">${this.formatCurrency(summary.total_amount)}</div>
                        </div>
                        <div class="stat-card">
                            <div class="label">Всего операций</div>
                            <div class="value">${summary.total_count}</div>
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">Расходы по категориям</h3>
                        </div>
                        <div class="chart-container" style="height: 300px;">
                            <canvas id="category-pie-chart"></canvas>
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">Детали по категориям</h3>
                        </div>
                        ${this.renderCategoryBreakdown(summary.by_category)}
                    </div>
                </div>
            `;

            setTimeout(() => this.renderPieChart('category-pie-chart', summary.by_category), 100);
        } catch (error) {
            console.error('Ошибка загрузки аналитики:', error);
        }
    }

    async renderCars() {
        const app = document.getElementById('app');
        app.innerHTML = `
            <div class="page-container">
                <div class="page-header">
                    <h1>Мои автомобили</h1>
                    <p>Управление автомобилями</p>
                </div>

                <div id="cars-list">
                    <div class="loading">Загрузка...</div>
                </div>

                <button class="btn btn-primary btn-full" onclick="app.openCarModal()">
                    Добавить новый автомобиль
                </button>
            </div>
        `;

        try {
            const carsList = document.getElementById('cars-list');
            if (this.state.cars.length === 0) {
                carsList.innerHTML = '<div class="empty-state"><p>Нет автомобилей</p></div>';
            } else {
                carsList.innerHTML = this.state.cars.map(car => this.renderCarCard(car)).join('');
            }
        } catch (error) {
            console.error('Ошибка загрузки автомобилей:', error);
        }
    }

    renderCarCard(car) {
        return `
            <div class="car-card">
                <div class="car-image">🚗</div>
                <div class="car-details">
                    <h2 class="car-name">${car.make}-${car.model}</h2>
                    <div class="car-info">
                        <div class="info-item">
                            <div class="info-label">Год</div>
                            <div class="info-value">${car.year || 'N/A'}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Номер</div>
                            <div class="info-value">${car.license_plate || 'N/A'}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Топливо</div>
                            <div class="info-value">${car.fuel_type || 'N/A'}</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderProfile() {
        const user = this.state.currentUser;

        const app = document.getElementById('app');
        app.innerHTML = `
            <div class="page-container">
                <div class="profile-header">
                    <div class="profile-avatar">🚗💰</div>
                    <div class="profile-name">${user.username}</div>
                    <div class="profile-email">${user.email}</div>
                </div>

                <div class="menu-list">
                    <div class="menu-item" onclick="app.openCarModal()">
                        <div class="menu-item-content">
                            <div class="menu-icon">🚗</div>
                            <div>Добавить новый автомобиль</div>
                        </div>
                    </div>
                    <div class="menu-item" onclick="app.exportData()">
                        <div class="menu-item-content">
                            <div class="menu-icon">📥</div>
                            <div>Экспорт данных</div>
                        </div>
                    </div>
                </div>

                <button class="btn btn-danger btn-full" onclick="app.logout()">
                    Выйти из аккаунта
                </button>
            </div>
        `;
    }

    logout() {
        console.log('👋 Logging out...');
        this.state.currentUser = null;
        this.state.token = null;
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        this.navigateTo('login');
    }

    exportData() {
        console.log('📥 Exporting data...');
        let csv = 'Дата,Категория,Сумма,Описание\n';

        this.state.expenses.forEach(expense => {
            csv += `${this.formatDate(expense.date)},${expense.category},${expense.amount},"${expense.description || ''}"\n`;
        });

        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', 'my_car_expenses.csv');
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    openExpenseModal(expenseId = null) {
        const modal = document.getElementById('expense-modal');
        const form = document.getElementById('expense-form');
        const title = document.getElementById('modal-title');
        const carSelect = document.getElementById('expense-car');

        carSelect.innerHTML = this.state.cars.map(car => 
            `<option value="${car.car_id}">${car.make} ${car.model}</option>`
        ).join('');

        if (expenseId) {
            this.state.editingExpenseId = expenseId;
            title.textContent = 'Редактировать расход';
            const expense = this.state.expenses.find(e => e.expense_id === expenseId);

            document.getElementById('expense-date').value = expense.date;
            document.getElementById('expense-amount').value = expense.amount;
            document.getElementById('expense-category').value = expense.category;
            document.getElementById('expense-description').value = expense.description || '';
            document.getElementById('expense-car').value = expense.car_id;
        } else {
            this.state.editingExpenseId = null;
            title.textContent = 'Добавить расход';
            form.reset();
            document.getElementById('expense-date').value = new Date().toISOString().split('T')[0];
            if (this.state.cars.length > 0) {
                carSelect.value = this.state.cars[0].car_id;
            }
        }

        modal.classList.remove('hidden');
    }

    closeExpenseModal() {
        document.getElementById('expense-modal').classList.add('hidden');
        this.state.editingExpenseId = null;
    }

    async saveExpense() {
        const date = document.getElementById('expense-date').value;
        const amount = parseFloat(document.getElementById('expense-amount').value);
        const category = document.getElementById('expense-category').value;
        const description = document.getElementById('expense-description').value;
        const carId = parseInt(document.getElementById('expense-car').value);

        if (!date || !amount || !category || !carId) {
            alert('Пожалуйста, заполните все обязательные поля');
            return;
        }

        try {
            if (this.state.editingExpenseId) {
                await ApiClient.updateExpense(this.state.editingExpenseId, {
                    date, amount, category, description
                });
            } else {
                await ApiClient.addExpense({
                    car_id: carId,
                    date,
                    amount,
                    category,
                    description
                });
            }

            await this.loadData();
            this.closeExpenseModal();
            this.navigateTo(this.state.currentPage);
        } catch (error) {
            alert('Ошибка: ' + error.message);
        }
    }

    editExpense(expenseId) {
        this.openExpenseModal(expenseId);
    }

    async deleteExpense(expenseId) {
        if (confirm('Вы уверены?')) {
            try {
                await ApiClient.deleteExpense(expenseId);
                await this.loadData();
                this.navigateTo(this.state.currentPage);
            } catch (error) {
                alert('Ошибка: ' + error.message);
            }
        }
    }

    openCarModal() {
        const modal = document.getElementById('car-modal');
        const form = document.getElementById('car-form');
        form.reset();
        modal.classList.remove('hidden');
    }

    closeCarModal() {
        document.getElementById('car-modal').classList.add('hidden');
    }

    async saveCar() {
        const make = document.getElementById('car-make').value;
        const model = document.getElementById('car-model').value;
        const year = parseInt(document.getElementById('car-year').value) || null;
        const licensePlate = document.getElementById('car-plate').value;
        const fuelType = document.getElementById('car-fuel').value;

        if (!make || !model) {
            alert('Пожалуйста, заполните обязательные поля');
            return;
        }

        try {
            await ApiClient.addCar({
                make,
                model,
                year,
                license_plate: licensePlate,
                fuel_type: fuelType
            });

            await this.loadData();
            this.closeCarModal();
            this.navigateTo('cars');
        } catch (error) {
            alert('Ошибка: ' + error.message);
        }
    }

    renderPieChart(canvasId, categoryData) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        if (this.state.charts[canvasId]) {
            this.state.charts[canvasId].destroy();
        }

        const colors = ['#1FB8CD', '#FFC185', '#B4413C', '#ECEBD5', '#5D878F', '#DB4545', '#D2BA4C'];
        const labels = Object.keys(categoryData).filter(cat => categoryData[cat] > 0);
        const data = labels.map(cat => categoryData[cat]);

        this.state.charts[canvasId] = new Chart(canvas, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { padding: 15, font: { size: 12 } }
                    }
                }
            }
        });
    }

    formatCurrency(amount) {
        return `${amount.toFixed(2)} BYN`;
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    }

    getCategoryIcon(category) {
        const icons = {
            'Топливо': '⛽',
            'Ремонт': '🔧',
            'Обслуживание': '🛠️',
            'Страховка': '🛡️',
            'Налоги': '📄',
            'Мойка': '💧',
            'Другое': '📦'
        };
        return icons[category] || '📦';
    }
}

console.log('🚀 MyCarExpenses app starting...');
console.log('📍 API Base URL:', API_BASE_URL);
const app = new App();
