from flask import render_template, flash, redirect, url_for, Response, abort
from app import app
from app.forms import LoginForm, RegistrationForm, AddBookForm, ReviewForm
from flask_login import current_user, login_user
import sqlalchemy as sa
from app import db
from app.models import User, Book, Review
from flask_login import logout_user, login_required
from flask import request
from urllib.parse import urlsplit
from functools import wraps


# ── Decorators ────────────────────────────────────────────────────────────────

def admin_required(f):
    """Restrict a route to admin users only."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


# ── Error handlers ─────────────────────────────────────────────────────────────

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403


# ── Public / customer routes ───────────────────────────────────────────────────

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = AddBookForm()

    # Only admins may submit the add-book form
    if form.validate_on_submit():
        if not current_user.is_admin:
            abort(403)

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
    top_books = sorted(
    [b for b in books if b.avg_rating is not None],
    key=lambda b: b.avg_rating,
    reverse=True)[:5]
    return render_template(url_for('index'), title='Home', books=books, top_books=top_books, form=form)


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
        user = User(username=form.username.data, email=form.email.data, role='customer')
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/book/<int:book_id>/cover')
@login_required
def book_cover(book_id):
    book = db.session.get(Book, book_id)
    if book is None or not book.cover_data:
        abort(404)
    return Response(book.cover_data, mimetype=book.cover_mimetype or 'image/jpeg')


@app.route('/book/<int:book_id>', methods=['GET', 'POST'])
@login_required
def book_detail(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        abort(404)

    # Check if the current user has already reviewed this book
    existing_review = db.session.scalar(
        sa.select(Review).where(
            Review.book_id == book_id,
            Review.user_id == current_user.id
        )
    )

    form = ReviewForm()
    if form.validate_on_submit():
        if existing_review:
            flash('You have already reviewed this book.')
            return redirect(url_for('book_detail', book_id=book_id))

        review = Review(
            body=form.body.data,
            rating=int(form.rating.data),
            user_id=current_user.id,
            book_id=book_id
        )
        db.session.add(review)
        db.session.commit()
        flash('Your review has been posted!')
        return redirect(url_for('book_detail', book_id=book_id))

    reviews = db.session.scalars(
        sa.select(Review)
        .where(Review.book_id == book_id)
        .order_by(Review.timestamp.desc())
    ).all()

    return render_template(
        'book_detail.html',
        title=book.title,
        book=book,
        reviews=reviews,
        existing_review=existing_review,
        form=form
    )

@app.route('/review/<int:review_id>/delete', methods=['POST'])
@login_required
def delete_review(review_id):
    review = db.session.get(Review, review_id)
    if review is None:
        abort(404)
    if review.user_id != current_user.id:
        abort(403)
    book_id = review.book_id
    db.session.delete(review)
    db.session.commit()
    flash('Your review has been deleted.')
    return redirect(url_for('book_detail', book_id=book_id))

# ── Admin routes ───────────────────────────────────────────────────────────────

@app.route('/admin/users')
@admin_required
def admin_users():
    users = db.session.scalars(sa.select(User).order_by(User.username)).all()
    return render_template('admin_users.html', title='Manage Users', users=users)


@app.route('/admin/users/<int:user_id>/set-role', methods=['POST'])
@admin_required
def admin_set_role(user_id):
    target = db.session.get(User, user_id)
    if target is None:
        abort(404)

    # Prevent an admin from accidentally demoting themselves
    if target.id == current_user.id:
        flash('You cannot change your own role.', 'error')
        return redirect(url_for('admin_users'))

    new_role = request.form.get('role')
    if new_role not in ('admin', 'customer'):
        flash('Invalid role.', 'error')
        return redirect(url_for('admin_users'))

    target.role = new_role
    db.session.commit()
    flash(f'{target.username} is now a{"n" if new_role == "admin" else ""} {new_role}.', 'success')
    return redirect(url_for('admin_users'))


@app.route('/book/<int:book_id>/delete', methods=['POST'])
@admin_required
def delete_book(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        abort(404)
    title = book.title
    db.session.delete(book)
    db.session.commit()
    flash(f'"{title}" has been deleted.')
    return redirect(url_for('index'))

@app.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    return render_template('user.html', user = user)

@app.route('/about')
def about():
    return render_template('about.html', title = 'About')