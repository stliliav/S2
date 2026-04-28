import os
from flask import render_template, flash, redirect, url_for, abort, request, current_app
from flask_login import login_required, current_user
from flask.views import MethodView
from werkzeug.utils import secure_filename
from sqlalchemy import select, func

from models import Movie, Genres, Image, Rating
from movie.forms import MovieForm


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
