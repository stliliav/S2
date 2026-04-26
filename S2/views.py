import os
from flask import render_template, flash, redirect, url_for, abort, request, current_app
from flask_login import login_user, login_required, current_user, logout_user
from flask.views import MethodView
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import select, func

from models import User, Profile, Movie, Comment, Genres, Image, Rating
from forms import SignUpForm, SignInForm, MovieForm, CommentForm, UsernameForm, UserEmailForm, PasswordForm

from extensions import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)

class UserSignUpView(MethodView):
    init_every_request = False

    def __init__(self, engine):
        self.engine = engine

    def get(self):
        form = SignUpForm()
        return render_template('user/signup.html', form=form)

    def post(self):
        form = SignUpForm()
        if form.validate_on_submit():
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            user.profile = Profile(name = form.name.data, age = form.age.data)
            self.engine.session.add(user)
            self.engine.session.commit()
            flash("You successfully signed up! Please, log in now", "success")
            return redirect(url_for('signin'))
        return render_template('user/signup.html', form=form)

class UserSignInView(MethodView):
    init_every_request = False

    def __init__(self, engine):
        self.engine = engine

    def get(self):
        form = SignInForm()
        return render_template('user/signin.html', form = form)

    def post(self):
        form = SignInForm()
        if form.validate_on_submit():
            stmt = select(User).where(User.username == form.username.data)
            user = self.engine.session.execute(stmt).scalar_one_or_none()
            if user and check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash("Successfully logged in!", "success")
                return redirect(url_for('home'))
            else:
                flash("Invalid username or password", "danger")
        return render_template('user/signin.html', form = form)

#________________________________________________________________________
class RateView(MethodView):
    decorators = [login_required]
    init_every_request = False

    def __init__(self, engine):
        self.engine = engine

    def get(self, mid):
        return redirect(url_for('movie_detail', mid=mid))

    def post(self, mid):
        choice = request.form.get('rates')
        if not choice:
            return redirect(url_for('movie_detail', mid=mid))

        stmt = select(Rating).where(Rating.user_id == current_user.id, Rating.movie_id == mid)
        existing_rating = self.engine.session.execute(stmt).scalar_one_or_none()

        if existing_rating:
            existing_rating.value = int(choice)
            flash('Your rate is updated!', 'info')
        else:
            new_rate = Rating(
                value=int(choice),
                user_id=current_user.id,
                movie_id=mid
            )
            self.engine.session.add(new_rate)
            flash('Rate is saved! We appreciate your opinion!', 'success')

        self.engine.session.commit()
        self.update_movie_average(mid)

        return redirect(url_for('movie_detail', mid=mid))

    def update_movie_average(self, mid):
        avg_rating = self.engine.session.query(func.avg(Rating.value)).filter(Rating.movie_id == mid).scalar()
        movie = self.engine.session.get(Movie, mid)
        if movie:
            movie.rate = round(float(avg_rating), 1) if avg_rating else 0.0
            self.engine.session.commit()

class MovieListView(MethodView):
    init_every_request = False

    def __init__(self, engine):
        self.engine = engine

    def get(self):
        stmt = select(Movie).order_by(Movie.id.desc())
        movies = self.engine.session.execute(stmt).scalars().all()
        return render_template('movie/home.html', movies=movies)

class MoviesDetailView(MethodView):
    init_every_request = False

    def __init__(self, engine):
        self.engine = engine

    def get(self, mid):
        movie = self.engine.session.get(Movie, mid) or abort(404)
        has_voted = False
        form = MovieForm(obj=movie)
        if current_user.is_authenticated:
            stmt = select(Rating).where(Rating.user_id == current_user.id, Rating.movie_id == mid)
            has_voted = self.engine.session.execute(stmt).scalar_one_or_none() is not None
        return render_template("movie/movie_detail.html", movie=movie, has_voted=has_voted, form = form)

class CommentsDetailView(MethodView):
    init_every_request = False

    def __init__(self, engine):
        self.engine = engine
    def get(self, cid):
        comment = self.engine.session.get(Comment, cid) or abort(404)
        form = CommentForm(obj=comment)
        return render_template("comment/comment_form.html", cid = comment.id, form=form)

class UserDetailView(MethodView):
    init_every_request = False

    def __init__(self, engine):
        self.engine = engine
    def get(self, uid):
        if not current_user.is_authenticated:
            return redirect(url_for("signin"))
        if uid != current_user.id:
            return redirect(url_for("signin"))
        stmt = select(User).where(User.id == uid)
        user = self.engine.session.execute(stmt).scalar_one_or_none()
        if user is None:
            return redirect(url_for("signup"))
        return render_template("profile/user_detail.html", user=user)

#__________________________________________________________________________________
#crud для фильмов

class CreateMovieView(MethodView):
    decorators = [login_required]
    init_every_request = False

    def __init__(self, engine):
        self.engine = engine

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
                    genre = self.engine.session.execute(stmt).scalar_one_or_none()

                    if not genre:
                        genre = Genres(name=i)
                        self.engine.session.add(genre)
                    movie.genres.append(genre)
            self.engine.session.add(movie)
            self.engine.session.flush()

            f = form.img.data
            filename = secure_filename(f.filename)

            save_dir = os.path.join(current_app.root_path, 'static', 'images')
            os.makedirs(save_dir, exist_ok=True)

            file_path = os.path.join(save_dir, filename)
            f.save(file_path)

            image_record = Image(movie_id=movie.id, image_path=f'images/{filename}')
            self.engine.session.add(image_record)
            self.engine.session.commit()
            flash('Movie created!', 'success')
            return redirect(url_for('home'))
        return render_template('movie/movie_form.html', form=form, title="New movie")


class EditMovieView(MethodView):
    decorators = [login_required]

    init_every_request = False

    def __init__(self, engine):
        self.engine = engine
    def get(self, mid):
        movie = self.engine.session.get(Movie, mid) or abort(404)
        if movie.profile_id != current_user.profile.id:
            abort(403)

        form = MovieForm(obj=movie)
        if movie.genres:
            form.genres.data = ", ".join([s.name for s in movie.genres])
        return render_template('movie/movie_form.html', form=form, title="Edit movie info")

    def post(self, mid):
        movie = self.engine.session.get(Movie, mid) or abort(404)
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
                    genre = self.engine.session.execute(stmt).scalar_one_or_none()

                    if not genre:
                        genre = Genres(name=i)
                        self.engine.session.add(genre)
                    movie.genres.append(genre)

            new_file = form.img.data

            if new_file and hasattr(new_file, 'filename') and new_file.filename != '':
                if movie.image:
                    old_path = os.path.join(current_app.root_path, 'static', movie.image.image_path)
                    if os.path.exists(old_path):
                        os.remove(old_path)

                    self.engine.session.delete(movie.image)
                    self.engine.session.flush()

                filename = secure_filename(new_file.filename)
                save_dir = os.path.join(current_app.root_path, 'static', 'images')
                os.makedirs(save_dir, exist_ok=True)

                new_file.save(os.path.join(save_dir, filename))

                image_record = Image(movie_id=movie.id, image_path=f'images/{filename}')
                self.engine.session.add(image_record)

            self.engine.session.commit()
            flash('Movie updated!', 'success')
            return redirect(url_for('movie_detail', mid=movie.id))

        return render_template('movie/movie_form.html', form=form, title="Edit movie info")


class DeleteMovieView(MethodView):
    decorators = [login_required]
    init_every_request = False

    def __init__(self, engine):
        self.engine = engine
    def post(self, mid):
        movie = self.engine.session.get(Movie, mid) or abort(404)
        if movie.profile_id != current_user.profile.id:
            abort(403)
        self.engine.session.delete(movie)
        self.engine.session.commit()
        flash('Movie deleted', 'warning')
        return redirect(url_for('home'))

#__________________________________________________________________________________
#crud для коментов

class CreateCommentView(MethodView):
    decorators = [login_required]
    init_every_request = False

    def __init__(self, engine):
        self.engine = engine
    def get(self, mid):
        movie = self.engine.session.get(Movie, mid) or abort(404)
        form = CommentForm()
        return render_template('comment/comment_form.html', form=form, title="New comment")

    def post(self, mid):
        form = CommentForm()
        movie = self.engine.session.get(Movie, mid) or abort(404)
        if form.validate_on_submit():
            self.engine.session.add(Comment(text = form.text.data, profile=current_user.profile, movie_id = mid))
            self.engine.session.commit()
            flash('Comment posted!', 'success')
            return redirect(url_for('movie_detail', mid=mid))
        return render_template('comment/comment_form.html', movie = movie, form=form, title="New comment")

class EditCommentView(MethodView):

    decorators = [login_required]
    init_every_request = False

    def __init__(self, engine):
        self.engine = engine
    def get(self, cid):
        comment = self.engine.session.get(Comment, cid) or abort(404)
        form = CommentForm(obj=comment)
        if comment.profile_id != current_user.profile.id:
            abort(403)
        return render_template('comment/comment_info.html', form=form, title="Edit comment", cid = comment.id, mid = comment.movie_id)

    def post(self, cid):
        comment = self.engine.session.get(Comment, cid) or abort(404)
        if comment.profile_id != current_user.profile.id:
            abort(403)
        mid = comment.movie_id
        form = CommentForm()
        if form.validate_on_submit():
            comment.text = form.text.data
            self.engine.session.commit()
            return redirect(url_for('movie_detail', mid=mid))
        return render_template('comment/comment_info.html', form=form, title="Edit comment", cid = comment.id, mid = comment.movie_id)

class DeleteCommentView(MethodView):
    decorators = [login_required]
    init_every_request = False

    def __init__(self, engine):
        self.engine = engine
    def post(self, cid):
        comment = self.engine.session.get(Comment, cid) or abort(404)
        mid = comment.movie_id
        if comment.profile_id != current_user.profile.id:
            abort(403)
        self.engine.session.delete(comment)
        self.engine.session.commit()
        flash('Comment deleted', 'warning')
        return redirect(url_for('movie_detail', mid = mid))

#__________________________________________________________________________________________________
#апдейт учетной записи

class EditUsernameView(MethodView):
    decorators = [login_required]
    init_every_request = False

    def __init__(self, engine):
        self.engine = engine
    def get(self, uid):
        stmt = select(User).where(User.id == uid)
        user = self.engine.session.execute(stmt).scalar_one_or_none()
        if user.profile.id != current_user.profile.id:
            abort(403)
        return render_template('profile/name_form.html', form=UsernameForm(obj=user), title="Edit username")

    def post(self,uid):
        stmt = select(User).where(User.id == uid)
        user = self.engine.session.execute(stmt).scalar_one_or_none()
        if user.profile.id != current_user.profile.id:
            abort(403)
        form = UsernameForm()
        if form.validate_on_submit():
            user.username = form.username.data
            self.engine.session.commit()
            return redirect(url_for('profile/user_detail', user = current_user))
        return render_template('profile/name_form.html', form=form, title="Edit username")

class EditEmailView(MethodView):
    decorators = [login_required]
    init_every_request = False

    def __init__(self, engine):
        self.engine = engine

    def get(self, uid):
        uid = current_user.id
        user = self.engine.session.get(User, uid) or abort(404)
        if user.profile.id != current_user.profile.id:
            abort(403)
        return render_template('profile/email_form.html', form=UserEmailForm(obj=user), title="Edit email")

    def post(self, uid):
        #uid = current_user.id
        user = self.engine.session.get(Comment, uid) or abort(404)
        if user.profile.id != current_user.profile.id:
            abort(403)
        form = UserEmailForm()
        if form.validate_on_submit():
            user.email = form.email.data
            self.engine.session.commit()
            return redirect(url_for('profile/user_detail', user = current_user))
        return render_template('profile/email_form.html', form=form, title="Edit email")

class EditPasswordView(MethodView):
    decorators = [login_required]
    init_every_request = False

    def __init__(self, engine):
        self.engine = engine
    def get(self, uid):
        # uid = current_user.id
        user = self.engine.session.get(User, uid) or abort(404)
        if user.profile.id != current_user.profile.id:
            abort(403)
        return render_template('profile/password_form.html', form=PasswordForm(obj=user), title="Edit password")

    def post(self, uid):
        uid = current_user.id
        user = self.engine.session.get(Comment, uid) or abort(404)
        if user.profile.id != current_user.profile.id:
            abort(403)
        form = PasswordForm()
        if form.validate_on_submit():
            user.set_password(form.password.data)
            self.engine.session.commit()
            return redirect(url_for('profile/user_detail', user = current_user))
        return render_template('profile/password_form.html', form=form, title="Edit password")

class LogOutView(MethodView):
    def get(self):
        logout_user()
        flash("You have been logged out!", "success")
        return redirect(url_for('home'))
