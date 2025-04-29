from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Transaction Model
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Primary key for the transaction
    amount = db.Column(db.Float, nullable=False)  # Amount for the transaction (income/expense)
    transaction_type = db.Column(db.String(10), nullable=False)  # 'Income' or 'Expense'
    category = db.Column(db.String(100))  # Category of the transaction (e.g., food, shopping, etc.)
    description = db.Column(db.String(200))  # Description of the transaction (optional)
    date = db.Column(db.DateTime, default=datetime.utcnow)  # Automatically set to current time
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Foreign key linking to the User table




@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = User(username=request.form['username'], password=request.form['password'])
        db.session.add(user)
        db.session.commit()
        flash('Registered successfully. Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.password == request.form['password']:
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Fetch all transactions for the current user
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()

    # Initialize variables for calculating totals
    total_income = 0
    total_expenses = 0
    
    # Loop through the transactions and calculate income and expenses separately
    for t in transactions:
        if t.transaction_type == 'income':
            total_income += t.amount
        elif t.transaction_type == 'expense':
            total_expenses += t.amount

    # Calculate the current balance
    current_balance = total_income - total_expenses

    # Fetch the most recent 5 transactions
    recent_transactions = transactions[-5:]  # Last 5 transactions, adjust if needed

    # Render the dashboard template and pass the necessary data
    return render_template('dashboard.html', 
                           total_income=total_income, 
                           total_expenses=total_expenses, 
                           current_balance=current_balance,
                           recent_transactions=recent_transactions)


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        # Ensure form field names match model column names
        transaction = Transaction(
            amount=float(request.form['amount']),
            transaction_type=request.form['transaction_type'],  
            description=request.form['description'],
            category=request.form['category'],
            user_id=current_user.id
        )
        db.session.add(transaction)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('transaction_form.html')


@app.route('/charts')
@login_required
def charts():
    transactions = Transaction.query.filter_by(user_id=current_user.id, transaction_type='expense').all()

    categories = {}
    
    for t in transactions:
        categories[t.category] = categories.get(t.category, 0) + t.amount
    
    print("Categories data:", categories)

    bar_data = {
        'x': list(categories.keys()),  # Categories
        'y': list(categories.values()),  # Spending amounts
        'type': 'bar'  # Type of chart: bar
    }

    pie_data = {
        'labels': list(categories.keys()),  # Categories
        'values': list(categories.values()),  # Spending amounts
        'type': 'pie'  # Type of chart: pie
    }

    return render_template('charts.html', bar_data=bar_data, pie_data=pie_data)



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
