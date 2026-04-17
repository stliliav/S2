import os
from werkzeug.utils import secure_filename
from datetime import datetime
from typing import List

from flask import Flask, render_template, flash, redirect, url_for, abort, request
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from flask.views import MethodView
from flask_wtf import FlaskForm, form

from sqlalchemy import ForeignKey, DateTime, func, select
from sqlalchemy.orm import mapped_column, Mapped, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, SubmitField, FileField, IntegerField
from wtforms.validators import DataRequired, EqualTo, ValidationError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.secret_key = 'rhfiwehfwhfwehfnoehfwef'
api = Api(app)
db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'signin'

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

@login.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    age = StringField('Age', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat the password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Sign up')

    def validate_username(self, field):
        stmt = select(User).where(User.username == field.data)
        if db.session.execute(stmt).scalar_one_or_none():
            raise ValidationError('Username already exists')

class SignInForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign in')

    def validate_username(self, field):
        stmt = select(User).where(User.username == field.data)

class UserSignUpView(MethodView):
    def get(self):
        form = SignUpForm()
        return render_template('user/signup.html', form=form)

    def post(self):
        form = SignUpForm()
        if form.validate_on_submit():
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            user.profile = Profile(name = form.name.data, age = form.age.data)
            db.session.add(user)
            db.session.commit()
            flash("You successfully signed up! Please, log in now", "success")
            return redirect(url_for('signin'))
        return render_template('user/signup.html', form=form)
app.add_url_rule('/signup', view_func=UserSignUpView.as_view('signup'))

class UserSignInView(MethodView):
    def get(self):
        form = SignInForm()
        return render_template('user/signin.html', form = form)
    def post(self):
        form = SignInForm()
        if form.validate_on_submit():
            stmt = select(User).where(User.username == form.username.data)
            user = db.session.execute(stmt).scalar_one_or_none()
            if user and check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash("Successfully logged in!", "success")
                return redirect(url_for('home'))
            else:
                flash("Invalid username or password", "danger")
        return render_template('user/signin.html', form = form)
app.add_url_rule("/signin", view_func=UserSignInView.as_view('signin'))

#________________________________________________________________________
class RateView(MethodView):
    decorators = [login_required]

    def get(self, mid):
        return redirect(url_for('movie_detail', mid=mid))

    def post(self, mid):
        choice = request.form.get('rates')
        if not choice:
            return redirect(url_for('movie_detail', mid=mid))

        stmt = select(Rating).where(Rating.user_id == current_user.id, Rating.movie_id == mid)
        existing_rating = db.session.execute(stmt).scalar_one_or_none()

        if existing_rating:
            existing_rating.value = int(choice)
            flash('Your rate is updated!', 'info')
        else:
            new_rate = Rating(
                value=int(choice),
                user_id=current_user.id,
                movie_id=mid
            )
            db.session.add(new_rate)
            flash('Rate is saved! We appreciate your opinion!', 'success')

        db.session.commit()
        self.update_movie_average(mid)

        return redirect(url_for('movie_detail', mid=mid))

    def update_movie_average(self, mid):
        avg_rating = db.session.query(func.avg(Rating.value)).filter(Rating.movie_id == mid).scalar()
        movie = db.session.get(Movie, mid)
        if movie:
            movie.rate = round(float(avg_rating), 1) if avg_rating else 0.0
            db.session.commit()
app.add_url_rule('/movie/rating/<int:mid>', view_func=RateView.as_view('ratings'))

class MovieListView(MethodView):
    def get(self):
        stmt = select(Movie).order_by(Movie.id.desc())
        movies = db.session.execute(stmt).scalars().all()
        return render_template('movie/home.html', movies=movies)
app.add_url_rule('/', view_func=MovieListView.as_view('home'))

class MoviesDetailView(MethodView):
    def get(self, mid):
        movie = db.session.get(Movie, mid) or abort(404)
        has_voted = False
        form = MovieForm(obj=movie)
        if current_user.is_authenticated:
            stmt = select(Rating).where(Rating.user_id == current_user.id, Rating.movie_id == mid)
            has_voted = db.session.execute(stmt).scalar_one_or_none() is not None
        return render_template("movie/movie_detail.html", movie=movie, has_voted=has_voted, form = form)
app.add_url_rule('/movie/<int:mid>', view_func=MoviesDetailView.as_view('movie_detail'))

class CommentsDetailView(MethodView):
    def get(self, cid):
        comment = db.session.get(Comment, cid) or abort(404)
        form = CommentForm(obj=comment)
        return render_template("comment/comment_form.html", cid = comment.id, form=form)
app.add_url_rule('/comment/<int:cid>', view_func=CommentsDetailView.as_view('comment_detail'))

class UserDetailView(MethodView):
    def get(self, uid):
        if not current_user.is_authenticated:
            return redirect(url_for("signin"))
        if uid != current_user.id:
            return redirect(url_for("signin"))
        stmt = select(User).where(User.id == uid)
        user = db.session.execute(stmt).scalar_one_or_none()
        if user is None:
            return redirect(url_for("signup"))
        return render_template("profile/user_detail.html", user=user)
app.add_url_rule('/user/<int:uid>', view_func=UserDetailView.as_view('user_detail'))

# class ProfileListView(MethodView):
#     def get(self):
#         stmt = select(Profile).order_by(Profile.age.desc())
#         profiles = db.session.execute(stmt).scalars().all()
#         return render_template('profile_list.html', profiles=profiles)
# app.add_url_rule('/profiles', view_func=ProfileListView.as_view('profile_list'))

class LogOutView(MethodView):
    def get(self):
        logout_user()
        flash("You have been logged out!", "success")
        return redirect(url_for('home'))
app.add_url_rule('/logout', view_func=LogOutView.as_view('logout'))


#______________________________________________________________________
#crud для изменения списка рпубликованных фильмов

class MovieForm(FlaskForm):
    title = StringField('Movie name', validators=[DataRequired()])
    genres = StringField('Genres', validators=[DataRequired()])
    year = IntegerField('Year of publishing', validators=[DataRequired()])
    country = StringField('Country', validators=[DataRequired()])
    img = FileField('Image')
    submit = SubmitField('Save movie')


class CreateMovieView(MethodView):
    decorators = [login_required]

    def get(self):
        form = MovieForm()
        return render_template('movie/movie_form.html', form=form, title="New movie")

    def post(self):
        form = MovieForm()
        if form.validate_on_submit():
            movie = Movie(title=form.title.data, profile=current_user.profile, year = form.year.data, country = form.country.data)
            raw_genres = form.genres.data
            if raw_genres:
                genre_names = [s.strip() for s in raw_genres.split(',')]
                for i in genre_names:
                    if not i:
                        continue
                    stmt = select(Genres).where(Genres.name == i)
                    genre = db.session.execute(stmt).scalar_one_or_none()

                    if not genre:
                        genre = Genres(name=i)
                        db.session.add(genre)
                    movie.genres.append(genre)
            db.session.add(movie)
            db.session.flush()

            f = form.img.data
            filename = secure_filename(f.filename)

            save_dir = os.path.join(app.root_path, 'static', 'images')
            os.makedirs(save_dir, exist_ok=True)

            file_path = os.path.join(save_dir, filename)
            f.save(file_path)

            image_record = Image(movie_id=movie.id, image_path=f'images/{filename}')
            db.session.add(image_record)
            db.session.commit()
            flash('Movie created!', 'success')
            return redirect(url_for('home'))
        return render_template('movie/movie_form.html', form=form, title="New movie")
app.add_url_rule('/movie/new', view_func=CreateMovieView.as_view('create_movie'))


class EditMovieView(MethodView):
    decorators = [login_required]
    def get(self, mid):
        movie = db.session.get(Movie, mid) or abort(404)
        if movie.profile_id != current_user.profile.id:
            abort(403)

        form = MovieForm(obj=movie)
        if movie.genres:
            form.genres.data = ", ".join([s.name for s in movie.genres])
        return render_template('movie/movie_form.html', form=form, title="Edit movie info")

    def post(self, mid):
        movie = db.session.get(Movie, mid) or abort(404)
        if movie.profile_id != current_user.profile.id:
            abort(403)
        form = MovieForm()
        if form.validate_on_submit():
            movie.title = form.title.data
            movie.year = form.year.data
            movie.country = form.country.data
            movie.genres.clear()
            raw_genres = form.genres.data
            if raw_genres:
                genre_names = [s.strip() for s in raw_genres.split(',')]
                for i in genre_names:
                    if not i:
                        continue

                    stmt = select(Genres).where(Genres.name == i)
                    genre = db.session.execute(stmt).scalar_one_or_none()

                    if not genre:
                        genre = Genres(name=i)
                        db.session.add(genre)
                    movie.genres.append(genre)

            new_file = form.img.data

            if new_file and hasattr(new_file, 'filename') and new_file.filename != '':
                if movie.image:
                    old_path = os.path.join(app.root_path, 'static', movie.image.image_path)
                    if os.path.exists(old_path):
                        os.remove(old_path)

                    db.session.delete(movie.image)
                    db.session.flush()

                filename = secure_filename(new_file.filename)
                save_dir = os.path.join(app.root_path, 'static', 'images')
                os.makedirs(save_dir, exist_ok=True)

                new_file.save(os.path.join(save_dir, filename))

                image_record = Image(movie_id=movie.id, image_path=f'images/{filename}')
                db.session.add(image_record)

            db.session.commit()
            flash('Movie updated!', 'success')
            return redirect(url_for('movie_detail', mid=movie.id))

        return render_template('movie/movie_form.html', form=form, title="Edit movie info")
app.add_url_rule('/movie/edit/<int:mid>', view_func=EditMovieView.as_view('edit_movie'))


class DeleteMovieView(MethodView):
    decorators = [login_required]
    def post(self, mid):
        movie = db.session.get(Movie, mid) or abort(404)
        if movie.profile_id != current_user.profile.id:
            abort(403)
        db.session.delete(movie)
        db.session.commit()
        flash('Movie deleted', 'warning')
        return redirect(url_for('home'))
app.add_url_rule('/movie/delete/<int:mid>', view_func=DeleteMovieView.as_view('delete_movie'))

#__________________________________________________________________________________
#crud для коментов

class CommentForm(FlaskForm):
    text = StringField('Input your comment', validators=[DataRequired()])
    submit = SubmitField('Post')

class CreateCommentView(MethodView):
    decorators = [login_required]
    def get(self, mid):
        movie = db.session.get(Movie, mid) or abort(404)
        form = CommentForm()
        return render_template('comment/comment_form.html', form=form, title="New comment")

    def post(self, mid):
        form = CommentForm()
        movie = db.session.get(Movie, mid) or abort(404)
        if form.validate_on_submit():
            db.session.add(Comment(text = form.text.data, profile=current_user.profile, movie_id = mid))
            db.session.commit()
            flash('Comment posted!', 'success')
            return redirect(url_for('movie_detail', mid=mid))
        return render_template('comment/comment_form.html', movie = movie, form=form, title="New comment")
app.add_url_rule('/movie/<int:mid>/comment/new', view_func=CreateCommentView.as_view('create_comment'))

class EditCommentView(MethodView):
    decorators = [login_required]
    def get(self, cid):
        comment = db.session.get(Comment, cid) or abort(404)
        form = CommentForm(obj=comment)
        if comment.profile_id != current_user.profile.id:
            abort(403)
        return render_template('comment/comment_info.html', form=form, title="Edit comment", cid = comment.id, mid = comment.movie_id)

    def post(self, cid):
        comment = db.session.get(Comment, cid) or abort(404)
        if comment.profile_id != current_user.profile.id:
            abort(403)
        mid = comment.movie_id
        form = CommentForm()
        if form.validate_on_submit():
            comment.text = form.text.data
            db.session.commit()
            return redirect(url_for('movie_detail', mid=mid))
        return render_template('comment/comment_info.html', form=form, title="Edit comment", cid = comment.id, mid = comment.movie_id)
app.add_url_rule('/comment/edit/<int:cid>', view_func=EditCommentView.as_view('edit_comment'))

class DeleteCommentView(MethodView):
    decorators = [login_required]
    def post(self, cid):
        comment = db.session.get(Comment, cid) or abort(404)
        mid = comment.movie_id
        if comment.profile_id != current_user.profile.id:
            abort(403)
        db.session.delete(comment)
        db.session.commit()
        flash('Comment deleted', 'warning')
        return redirect(url_for('movie_detail', mid = mid))
app.add_url_rule('/comment/delete/<int:cid>', view_func=DeleteCommentView.as_view('delete_comment'))

#__________________________________________________________________________________________________
#апдейт учетной записи
class UsernameForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    submit = SubmitField('Set new username')

    def validate_username(self, field):
        stmt = select(User).where(User.username == field.data)
        if db.session.execute(stmt).scalar_one_or_none():
            raise ValidationError('Username already exists')


class UserEmailForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    submit = SubmitField('Set new email')
    def validate_email(self, field):
        if db.session.execute(select(User).where(User.email == field.data)).scalar_one_or_none():
            raise ValidationError('Email already exists')

class PasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat your password', validators=[DataRequired(), EqualTo('password', message = 'Passwords must match')])
    submit = SubmitField('Change password')

class EditUsernameView(MethodView):
    decorators = [login_required]
    def get(self, uid):
        stmt = select(User).where(User.id == uid)
        user = db.session.execute(stmt).scalar_one_or_none()
        if user.profile.id != current_user.profile.id:
            abort(403)
        return render_template('profile/name_form.html', form=UsernameForm(obj=user), title="Edit username")

    def post(self,uid):
        stmt = select(User).where(User.id == uid)
        user = db.session.execute(stmt).scalar_one_or_none()
        if user.profile.id != current_user.profile.id:
            abort(403)
        form = UsernameForm()
        if form.validate_on_submit():
            user.username = form.username.data
            db.session.commit()
            return redirect(url_for('profile/user_detail', user = current_user))
        return render_template('profile/name_form.html', form=form, title="Edit username")
app.add_url_rule('/user/name/<int:uid>', view_func=EditUsernameView.as_view('edit_username'))

class EditEmailView(MethodView):
    decorators = [login_required]
    def get(self, uid):
        uid = current_user.id
        user = db.session.get(User, uid) or abort(404)
        if user.profile.id != current_user.profile.id:
            abort(403)
        return render_template('profile/email_form.html', form=UserEmailForm(obj=user), title="Edit email")

    def post(self, uid):
        #uid = current_user.id
        user = db.session.get(Comment, uid) or abort(404)
        if user.profile.id != current_user.profile.id:
            abort(403)
        form = UserEmailForm()
        if form.validate_on_submit():
            user.email = form.email.data
            db.session.commit()
            return redirect(url_for('profile/user_detail', user = current_user))
        return render_template('profile/email_form.html', form=form, title="Edit email")
app.add_url_rule('/user/email/<int:uid>', view_func=EditEmailView.as_view('edit_email'))

class EditPasswordView(MethodView):
    decorators = [login_required]
    def get(self, uid):
        # uid = current_user.id
        user = db.session.get(User, uid) or abort(404)
        if user.profile.id != current_user.profile.id:
            abort(403)
        return render_template('profile/password_form.html', form=PasswordForm(obj=user), title="Edit password")

    def post(self, uid):
        uid = current_user.id
        user = db.session.get(Comment, uid) or abort(404)
        if user.profile.id != current_user.profile.id:
            abort(403)
        form = PasswordForm()
        if form.validate_on_submit():
            user.set_password(form.password.data)
            db.session.commit()
            return redirect(url_for('profile/user_detail', user = current_user))
        return render_template('profile/password_form.html', form=form, title="Edit password")
app.add_url_rule('/user/password/<int:uid>', view_func=EditPasswordView.as_view('edit_password'))

#_____________________________________________ResourceAPI_______________________________________________________________
class MovieListResource(Resource):
	def get(self):
		with app.app_context():
			stmt = select(Movie)
			movies = [
				{"id": movie.id,
				 "title": movie.title,
				 "url": app.url_for("movie_detail", mid=movie.id, movie=movie, _external=True)}
				for movie in db.session.execute(stmt).scalars().all()]
			return movies
api.add_resource(MovieListResource, '/api/movies')

class CommentListResource(Resource):
	def get(self):
		with app.app_context():
			stmt = select(Comment)
			comments = [
				{"movie_id": comment.movie_id,
				 "id": comment.id,
				 "text": comment.text}
				for comment in db.session.execute(stmt).scalars().all()]
			return comments
api.add_resource(CommentListResource, '/api/comments')

class UserListResource(Resource):
	def get(self):
		with app.app_context():
			stmt = select(User)
			users = [
				{"id": user.id,
				 "name": user.username,
                 "email": user.email}
				for user in db.session.execute(stmt).scalars().all()]
			return users
api.add_resource(UserListResource, '/api/users')


def create_db():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    create_db()
    app.run(port= 7777, debug=True, use_reloader=False)

