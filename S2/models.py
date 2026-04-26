from typing import List
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, DateTime, func
from sqlalchemy.orm import mapped_column, Mapped, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

from extensions import db

movies_genres = db.Table(
    'movies_genres',
    db.Column('post_id', db.Integer, db.ForeignKey('movies.id')),
    db.Column('genre_id', db.Integer, db.ForeignKey('genres.id'))
)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    username: Mapped[str] = mapped_column(db.String(100))
    email: Mapped[str] = mapped_column(db.String(100), nullable = True)
    password_hash: Mapped[str] = mapped_column(db.String(100), nullable = True)
    profile: Mapped["Profile"] = relationship(back_populates="user", uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        if self.password_hash:
            return check_password_hash(str(self.password_hash), password)

class Profile(db.Model):
    __tablename__ = 'profiles'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    user: Mapped["User"] = relationship(back_populates="profile", uselist = False)
    name: Mapped[str] = mapped_column(db.String(100))
    age: Mapped[int] = mapped_column(db.Integer)
    movies: Mapped[List["Movie"]] = relationship(back_populates="profile")

class Movie(db.Model):
    __tablename__ = 'movies'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    title: Mapped[str] = mapped_column(db.String(100))
    profile_id: Mapped[int] = mapped_column(ForeignKey('profiles.id'))
    profile: Mapped["Profile"] = relationship(back_populates="movies", uselist = False)
    comments: Mapped[List["Comment"]] = relationship(lazy = 'dynamic', back_populates = "movies", cascade="all, delete-orphan")
    genres: Mapped[List["Genres"]] = relationship(secondary = movies_genres, back_populates = "movies")
    year: Mapped[int] = mapped_column(db.Integer)
    country: Mapped[str] = mapped_column(db.String(50))
    image: Mapped["Image"] = relationship(backref="movie", uselist=False, cascade="all, delete-orphan")
    rate: Mapped[float] = mapped_column(db.Float, default=0.0)
    ratings_list: Mapped[List["Rating"]] = relationship(back_populates="movie", cascade="all, delete-orphan")


class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(db.Integer, primary_key= True)
    text: Mapped[str] = mapped_column(db.String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    profile_id: Mapped[int] = mapped_column(ForeignKey('profiles.id'))
    profile: Mapped["Profile"] = relationship( uselist = False)
    movie_id: Mapped[int] = mapped_column(ForeignKey('movies.id'))
    movies: Mapped["Movie"] = relationship(back_populates = 'comments', uselist = False)

class Genres(db.Model):
    __tablename__ = "genres"
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(50), unique=True)
    movies: Mapped[List["Movie"]] = relationship(secondary= movies_genres, back_populates="genres")


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey('movies.id'))
    #будет чт то типо "images/photo1.jpg"
    image_path = db.Column(db.String(100), nullable=False)


class Rating(db.Model):
    __tablename__ = 'ratings'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    value: Mapped[int] = mapped_column(db.Integer)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    movie_id: Mapped[int] = mapped_column(ForeignKey('movies.id'))
    movie: Mapped["Movie"] = relationship(back_populates="ratings_list")

def create_db(app):
    with app.app_context():
        db.create_all()
