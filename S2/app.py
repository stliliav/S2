from flask import Flask
from flask_login import current_user

from config import Config
from extensions import db, login_manager
from models import create_db

from user.views import (
    UserSignUpView, UserSignInView, UserDetailView,
     EditUsernameView, EditEmailView, EditPasswordView, LogOutView
)

from movie.views import (
	RateView, MovieListView, MoviesDetailView,
	CreateMovieView, EditMovieView, DeleteMovieView
)

from comment.views import (
	CommentsDetailView,CreateCommentView,
	EditCommentView, DeleteCommentView
)

from resources import initialize_routes
from flask_restful import Api


app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager.init_app(app)
login_manager.login_view = 'signin'

create_db(app)

api = Api(app)
initialize_routes(api)

app.add_url_rule('/signup', view_func=UserSignUpView.as_view('signup', db))
app.add_url_rule("/signin", view_func=UserSignInView.as_view('signin', db))
app.add_url_rule('/movie/rating/<int:mid>', view_func=RateView.as_view('ratings', db))
app.add_url_rule('/', view_func=MovieListView.as_view('home', db))
app.add_url_rule('/movie/<int:mid>', view_func=MoviesDetailView.as_view('movie_detail', db))
app.add_url_rule('/comment/<int:cid>', view_func=CommentsDetailView.as_view('comment_detail', db))
app.add_url_rule('/user/<int:uid>', view_func=UserDetailView.as_view('user_detail', db))
app.add_url_rule('/movie/new', view_func=CreateMovieView.as_view('create_movie', db))
app.add_url_rule('/movie/edit/<int:mid>', view_func=EditMovieView.as_view('edit_movie', db))
app.add_url_rule('/movie/delete/<int:mid>', view_func=DeleteMovieView.as_view('delete_movie', db))
app.add_url_rule('/movie/<int:mid>/comment/new', view_func=CreateCommentView.as_view('create_comment', db))
app.add_url_rule('/comment/edit/<int:cid>', view_func=EditCommentView.as_view('edit_comment', db))
app.add_url_rule('/comment/delete/<int:cid>', view_func=DeleteCommentView.as_view('delete_comment', db))
app.add_url_rule('/user/name/<int:uid>', view_func=EditUsernameView.as_view('edit_username', db))
app.add_url_rule('/user/email/<int:uid>', view_func=EditEmailView.as_view('edit_email', db))
app.add_url_rule('/user/password/<int:uid>', view_func=EditPasswordView.as_view('edit_password', db))
app.add_url_rule('/logout', view_func=LogOutView.as_view('logout'))


if __name__ == '__main__':
	app.run(port=7777, debug=True, use_reloader=False)



