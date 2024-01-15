from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import requests
from models import db, Book, Member, Transaction  
from views import some_function

flask_app = Flask(__name__)
flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
db.init_app(flask_app)
db = SQLAlchemy(flask_app)


# Create tables
with flask_app.app_context():
    db.create_all()

# Routes
@flask_app.route('/')
def index():
    books = Book.query.all()
    members = Member.query.all()
    transactions = Transaction.query.all()
    return render_template('template/index.html', books=books, members=members, transactions=transactions)

# CRUD Operations for Books
@flask_app.route('/add_book', methods=['POST'])
def add_book():
    title = request.form['title']
    author = request.form['author']
    stock = request.form['stock']

    new_book = Book(title=title, author=author, stock=stock)
    db.session.add(new_book)
    db.session.commit()

    return redirect(url_for('index'))

@flask_app.route('/update_book/<int:id>', methods=['POST'])
def update_book(id):
    book = Book.query.get(id)
    book.title = request.form['title']
    book.author = request.form['author']
    book.stock = request.form['stock']

    db.session.commit()

    return redirect(url_for('index'))

@flask_app.route('/delete_book/<int:id>')
def delete_book(id):
    book = Book.query.get(id)
    db.session.delete(book)
    db.session.commit()

    return redirect(url_for('index'))

# CRUD Operations for Members
@flask_app.route('/add_member', methods=['POST'])
def add_member():
    name = request.form['name']

    new_member = Member(name=name)
    db.session.add(new_member)
    db.session.commit()

    return redirect(url_for('index'))

@flask_app.route('/update_member/<int:id>', methods=['POST'])
def update_member(id):
    member = Member.query.get(id)
    member.name = request.form['name']

    db.session.commit()

    return redirect(url_for('index'))

@flask_app.route('/delete_member/<int:id>')
def delete_member(id):
    member = Member.query.get(id)
    db.session.delete(member)
    db.session.commit()

    return redirect(url_for('index'))

# Book Issue and Return
@flask_app.route('/issue_book', methods=['POST'])
def issue_book():
    book_id = request.form['book_id']
    member_id = request.form['member_id']

    book = Book.query.get(book_id)
    member = Member.query.get(member_id)

    if book.stock > 0 and member.outstanding_debt <= 500:
        transaction = Transaction(book_id=book_id, member_id=member_id)
        db.session.add(transaction)

        # Decrease book stock
        book.stock -= 1

        db.session.commit()

    return redirect(url_for('index'))

@flask_app.route('/return_book/<int:id>', methods=['POST'])
def return_book(id):
    transaction = Transaction.query.get(id)

    # Check if the book is returned on time and charge a fee if necessary
    if not transaction.return_date:
        transaction.return_date = db.func.current_date()

        # Charge a fee if the return is late
        days_late = (transaction.return_date - transaction.date_issued).days
        if days_late > 0:
            transaction.fee = days_late * 5  # Charge Rs.5 per day late fee

    db.session.commit()

    return redirect(url_for('index'))

# Search for a book by name and author
@flask_app.route('/search', methods=['POST'])
def search():
    search_term = request.form['search_term']

    books = Book.query.filter(
        (Book.title.like(f"%{search_term}%")) | (Book.author.like(f"%{search_term}%"))
    ).all()

    return render_template('index.html', books=books)

# Data Import from Frappe API
@flask_app.route('/import_books', methods=['POST'])
def import_books():
    search_term = request.form['search_term']
    num_books = int(request.form['num_books'])

    api_url = 'https://frappeapi.example.com/books'
    params = {'search': search_term, 'limit': num_books}
    response = requests.get(api_url, params=params)
    books_data = response.json()

    for book_data in books_data:
        new_book = Book(
            title=book_data['title'],
            author=book_data['authors'],
            stock=book_data['quantity']
        )
        db.session.add(new_book)

    db.session.commit()

    return redirect(url_for('index'))

flask_app.register_blueprint(some_function)


if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', port=5000)
