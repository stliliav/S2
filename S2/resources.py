from comment.api import CommentListResource
from movie.api import MovieListResource
from user.api import UserListResource


def initialize_routes(api):
    api.add_resource(MovieListResource, '/api/movies')
    api.add_resource(CommentListResource, '/api/comments')
    api.add_resource(UserListResource, '/api/users')