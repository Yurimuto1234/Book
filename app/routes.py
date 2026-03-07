from flask import render_template, flash, redirect, url_for, current_app
from app import app
from app.forms import LoginForm, RegistrationForm, AddBookForm
from flask_login import current_user, login_user
import sqlalchemy as sa
from app import db
from app.models import User, Book
from flask_login import logout_user, login_required
from flask import request
from urllib.parse import urlsplit
import os
import uuid
from werkzeug.utils import secure_filename

def save_cover(file_storage):
    """Save an uploaded cover image and return the filename."""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    ext = file_storage.filename.rsplit('.', 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    file_storage.save(os.path.join(upload_folder, filename))
    return filename

@app.route('/')
@app.route('/index')
@login_required
def index():
    books = db.session.scalars(sa.select(Book).order_by(Book.timestamp.desc())).all()
    return render_template('index.html', title='Book Catalog', books=books)

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

@app.route('/add_book', methods=['GET', 'POST'])
@login_required
def add_book():
    form = AddBookForm()
    if form.validate_on_submit():
        cover_filename = None
        if form.cover.data and form.cover.data.filename:
            cover_filename = save_cover(form.cover.data)

        book = Book(
            title=form.title.data,
            author=form.author.data,
            genre=form.genre.data or None,
            year=form.year.data,
            description=form.description.data or None,
            cover_filename=cover_filename,
            added_by=current_user.id
        )
        db.session.add(book)
        db.session.commit()
        flash('Book added successfully!')
        return redirect(url_for('index'))
    return render_template('add_book.html', title='Add Book', form=form)