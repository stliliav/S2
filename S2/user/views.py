from flask import render_template, flash, redirect, url_for, abort
from flask_login import login_user, login_required, current_user, logout_user
from flask.views import MethodView
from werkzeug.security import check_password_hash
from sqlalchemy import select

from models import User, Profile, Comment
from user.forms import SignUpForm, SignInForm, UsernameForm, UserEmailForm, PasswordForm


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
            return redirect(url_for('user_detail', uid=user.id))
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
        user = self.engine.session.get(User, uid) or abort(404)
        if user.profile.id != current_user.profile.id:
            abort(403)
        form = UserEmailForm()
        if form.validate_on_submit():
            user.email = form.email.data
            self.engine.session.commit()
            return redirect(url_for('user_detail', uid=user.id))
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
        user = self.engine.session.get(User, uid) or abort(404)
        if user.profile.id != current_user.profile.id:
            abort(403)
        form = PasswordForm()
        if form.validate_on_submit():
            user.set_password(form.password.data)
            self.engine.session.commit()
            return redirect(url_for('user_detail', uid=user.id))
        return render_template('profile/password_form.html', form=form, title="Edit password")

class LogOutView(MethodView):
    def get(self):
        logout_user()
        flash("You have been logged out!", "success")
        return redirect(url_for('home'))
