from flask_restful import Resource
from sqlalchemy import select
from flask import url_for

from extensions import db
from models import Movie, Comment, User

class MovieListResource(Resource):
    def get(self):
        stmt = select(Movie)
        movies = [
            {"id": movie.id,
             "title": movie.title,
             "url": url_for("movie_detail", mid=movie.id, _external=True)}
            for movie in db.session.execute(stmt).scalars().all()]
        return movies

class CommentListResource(Resource):
    def get(self):
        stmt = select(Comment)
        comments = [
            {"movie_id": comment.movie_id,
             "id": comment.id,
             "text": comment.text,
             "created_at": comment.created_at.isoformat()}
            for comment in db.session.execute(stmt).scalars().all()]
        return comments

class UserListResource(Resource):
    def get(self):
        stmt = select(User)
        users = [
            {"id": user.id,
             "name": user.username,
             "email": user.email}
            for user in db.session.execute(stmt).scalars().all()]
        return users

def initialize_routes(api):
    api.add_resource(MovieListResource, '/api/movies')
    api.add_resource(CommentListResource, '/api/comments')
    api.add_resource(UserListResource, '/api/users')