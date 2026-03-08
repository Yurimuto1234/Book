from flask import render_template, flash, redirect, url_for, Response, abort
from app import app
from app.forms import LoginForm, RegistrationForm, AddBookForm
from flask_login import current_user, login_user
import sqlalchemy as sa
from app import db
from app.models import User, Book
from flask_login import logout_user, login_required
from flask import request
from urllib.parse import urlsplit

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = AddBookForm()
    if form.validate_on_submit():
        cover_data = None
        cover_mimetype = None
        f = form.cover.data
        if f and f.filename:
            cover_data = f.read()
            cover_mimetype = f.mimetype or 'image/jpeg'

        book = Book(
            title=form.title.data,
            author=form.author.data,
            genre=form.genre.data or None,
            year=form.year.data,
            description=form.description.data or None,
            cover_data=cover_data,
            cover_mimetype=cover_mimetype,
            added_by=current_user.id
        )
        db.session.add(book)
        db.session.commit()
        flash('Book added successfully!')
        return redirect(url_for('index'))

    books = db.session.scalars(sa.select(Book).order_by(Book.timestamp.desc())).all()
    return render_template('index.html', title='Book Catalog', books=books, form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

# @app.route('/add_book', methods=['GET', 'POST'])
# @login_required
# def add_book():
#     form = AddBookForm()
#     if form.validate_on_submit():
#         cover_data = None
#         cover_mimetype = None
#         f = form.cover.data
#         if f and f.filename:
#             cover_data = f.read()
#             cover_mimetype = f.mimetype or 'image/jpeg'

#         book = Book(
#             title=form.title.data,
#             author=form.author.data,
#             genre=form.genre.data or None,
#             year=form.year.data,
#             description=form.description.data or None,
#             cover_data=cover_data,
#             cover_mimetype=cover_mimetype,
#             added_by=current_user.id
#         )
#         db.session.add(book)
#         db.session.commit()
#         flash('Book added successfully!')
#         return redirect(url_for('index'))
#     return render_template('add_book.html', title='Add Book', form=form)

@app.route('/book/<int:book_id>/cover')
@login_required
def book_cover(book_id):
    book = db.session.get(Book, book_id)
    if book is None or not book.cover_data:
        abort(404)
    return Response(book.cover_data, mimetype=book.cover_mimetype or 'image/jpeg')