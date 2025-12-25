from flask_dance.contrib.github import make_github_blueprint, github
from flask import redirect, url_for, session, request
from flask_login import login_user, logout_user, current_user, LoginManager
from BUNK3R_IA.models import db, User
import os

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

def setup_github_auth(app):
    github_bp = make_github_blueprint(
        client_id=os.environ.get("GITHUB_CLIENT_ID"),
        client_secret=os.environ.get("GITHUB_CLIENT_SECRET"),
        scope="user:email,repo"
    )
    app.register_blueprint(github_bp, url_prefix="/auth")
    login_manager.init_app(app)

    @app.route("/login")
    def login():
        return redirect(url_for("github.login"))

    @app.route("/logout")
    def logout():
        logout_user()
        return redirect(url_for("index"))

    return github_bp

def require_login(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("github.login"))
        return f(*args, **kwargs)
    return decorated_function

from flask_dance.consumer import oauth_authorized

@oauth_authorized.connect_via(None)
def github_logged_in(blueprint, token):
    if blueprint.name != "github":
        return
    
    resp = blueprint.session.get("/user")
    if not resp.ok:
        return False

    gh_user = resp.json()
    user_id = str(gh_user["id"])
    
    user = User.query.get(user_id)
    if not user:
        user = User(id=user_id)
    
    user.first_name = gh_user.get("name") or gh_user.get("login")
    user.email = gh_user.get("email")
    user.profile_image_url = gh_user.get("avatar_url")
    
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return False
