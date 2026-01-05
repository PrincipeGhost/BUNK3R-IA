from flask_dance.contrib.github import make_github_blueprint, github
from flask import redirect, url_for, session, request
from flask_login import login_user, logout_user, current_user, LoginManager
from backend.models import db, User
import os

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

def setup_github_auth(app):
    client_id = os.environ.get("GITHUB_CLIENT_ID")
    client_secret = os.environ.get("GITHUB_CLIENT_SECRET")
    
    if client_id and client_secret:
        # Custom Blueprint logic to FORCE redirect_uri
        github_bp = make_github_blueprint(
            client_id=client_id,
            client_secret=client_secret,
            scope="user:email,repo,workflow,read:org",
            redirect_to="index"
        )
        
        # MONKEY PATCH: Forcing the redirect_uri to be HTTPS string
        # This bypasses Flask's url_for generation entirely
        original_login = github_bp.view_functions['login']
        
        def secure_login():
            # Force HTTPS redirect_uri in the session/oauth flow
            from flask import url_for, redirect
            from flask_dance.contrib.github import github
            
            # Manually construct the authorization URL with the correct redirect_uri
            redirect_uri = "https://bunk3r-ia.onrender.com/auth/github/authorized"
            return redirect(github.session.authorization_url(
                "https://github.com/login/oauth/authorize",
                redirect_uri=redirect_uri
            )[0])

        # Replace the login view with our secure version
        github_bp.view_functions['login'] = secure_login
        
        app.register_blueprint(github_bp, url_prefix="/auth")
    
    login_manager.init_app(app)

    @app.route("/auth/token")
    @require_login
    def auth_token():
        # Securely return the OAuth token to the authenticated user's frontend
        if not github.authorized:
            return {"error": "Not authorized with GitHub"}, 401
        
        token = github.token
        return {"token": token.get("access_token"), "scope": token.get("scope")}

    @app.route("/login")
    def login_route():
        if not os.environ.get("GITHUB_CLIENT_ID"):
            return "Error: GITHUB_CLIENT_ID no configurado en variables de entorno (.env)", 401
        return redirect(url_for("github.login"))

    @app.route("/logout")
    def logout():
        logout_user()
        return redirect(url_for("index"))

def require_login(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("login_route"))
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
    session['github_token'] = token.get("access_token")
    return False
