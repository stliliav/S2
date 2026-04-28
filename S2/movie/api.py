from flask_restful import Resource
from sqlalchemy import select
from flask import url_for

from extensions import db
from models import Movie

class MovieListResource(Resource):
    def get(self):
        stmt = select(Movie)
        movies = [
            {"id": movie.id,
             "title": movie.title,
             "url": url_for("movie_detail", mid=movie.id, _external=True)}
            for movie in db.session.execute(stmt).scalars().all()]
        return movies
