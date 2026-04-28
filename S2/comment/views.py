from flask import render_template, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from flask.views import MethodView
from models import Movie, Comment
from comment.forms import CommentForm

class CommentsDetailView(MethodView):
    init_every_request = False

    def __init__(self, engine):
        self.engine = engine
    def get(self, cid):
        comment = self.engine.session.get(Comment, cid) or abort(404)
        form = CommentForm(obj=comment)
        return render_template("comment/comment_form.html", cid = comment.id, form=form)

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
