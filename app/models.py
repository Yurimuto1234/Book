from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db, login
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))

    posts: so.WriteOnlyMapped['Post'] = so.relationship(back_populates='author')
    books: so.WriteOnlyMapped['Book'] = so.relationship(back_populates='added_by_user')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))


class Book(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(200), nullable=False)
    author: so.Mapped[str] = so.mapped_column(sa.String(200), nullable=False)
    genre: so.Mapped[Optional[str]] = so.mapped_column(sa.String(64))
    year: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer)
    description: so.Mapped[Optional[str]] = so.mapped_column(sa.String(500))
    cover_data: so.Mapped[Optional[bytes]] = so.mapped_column(sa.LargeBinary)
    cover_mimetype: so.Mapped[Optional[str]] = so.mapped_column(sa.String(32))
    timestamp: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))
    added_by: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)

    added_by_user: so.Mapped[User] = so.relationship(back_populates='books')

    def __repr__(self):
        return '<Book {} by {}>'.format(self.title, self.author)


class Post(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(300))
    timestamp: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)

    author: so.Mapped[User] = so.relationship(back_populates='posts')