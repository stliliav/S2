from flask_restful import Resource
from sqlalchemy import select

from extensions import db
from models import User

class UserListResource(Resource):
    def get(self):
        stmt = select(User)
        users = [
            {"id": user.id,
             "name": user.username,
             "email": user.email}
            for user in db.session.execute(stmt).scalars().all()]
        return users