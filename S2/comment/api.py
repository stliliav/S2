from flask_restful import Resource
from extensions import db
from models import Comment
from sqlalchemy import select


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