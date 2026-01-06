from flask_dance.contrib.github import make_github_blueprint, github
from flask import redirect, url_for, session, request
from flask_login import login_user, logout_user, current_user, LoginManager
from backend.models import db, User
import os

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    import logging
    try:
        user = User.query.get(user_id)
        if user:
            logging.info(f"Loaded user {user_id} successfully")
        else:
            logging.warning(f"User {user_id} not found in DB")
        return user
    except Exception as e:
        logging.error(f"Error loading user {user_id}: {e}")
        return None

def setup_github_auth(app):
    client_id = os.environ.get("GITHUB_CLIENT_ID")
    client_secret = os.environ.get("GITHUB_CLIENT_SECRET")
    
    if client_id and client_secret:
        # Standard Blueprint logic
        github_bp = make_github_blueprint(
            client_id=client_id,
            client_secret=client_secret,
            scope="user:email,repo,workflow,read:org",
            redirect_to="index"
        )
        
        # Explicitly connect signal to THIS blueprint
        @oauth_authorized.connect_via(github_bp)
        def github_logged_in(blueprint, token):
            import logging
            logger = logging.getLogger(__name__)
            logger.info("SIGNAL RECEIVED: github_logged_in triggered!")
            
            try:
                resp = blueprint.session.get("/user")
                if not resp.ok:
                    logger.error(f"GitHub API Error: {resp.text}")
                    return False
                
                gh_user = resp.json()
                user_id = str(gh_user["id"])
                
                logger.info(f"Processing login for user: {gh_user.get('login')} (ID: {user_id})")
                
                user = User.query.get(user_id)
                if not user:
                    logger.info("Creating new user")
                    user = User(id=user_id)
                
                user.first_name = gh_user.get("name") or gh_user.get("login")
                user.email = gh_user.get("email")
                user.profile_image_url = gh_user.get("avatar_url")
                
                db.session.add(user)
                try:
                    db.session.commit()
                    logger.info("User saved to DB")
                except Exception as db_err:
                    logger.error(f"DB Commit Error: {db_err}")
                    db.session.rollback()
                
                login_user(user)
                session['github_token'] = token.get("access_token")
                logger.info("User logged in successfully")
                
                # Force session save
                session.modified = True
                
                return False
                
            except Exception as e:
                logger.error(f"LOGIN CRITICAL ERROR: {str(e)}", exc_info=True)
                db.session.rollback()
                return False

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
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        if blueprint.name != "github":
            return
        
        resp = blueprint.session.get("/user")
        if not resp.ok:
            logger.error(f"GitHub API Error: {resp.text}")
            return False
        
        gh_user = resp.json()
        user_id = str(gh_user["id"])
        
        logger.info(f"Processing login for user: {gh_user.get('login')} (ID: {user_id})")
        
        user = User.query.get(user_id)
        if not user:
            logger.info("Creating new user")
            user = User(id=user_id)
        
        user.first_name = gh_user.get("name") or gh_user.get("login")
        user.email = gh_user.get("email")
        user.profile_image_url = gh_user.get("avatar_url")
        
        db.session.add(user)
        db.session.commit()
        logger.info("User saved to DB")
        
        login_user(user)
        session['github_token'] = token.get("access_token")
        logger.info("User logged in successfully")
        
        return False
        
    except Exception as e:
        logger.error(f"LOGIN CRITICAL ERROR: {str(e)}", exc_info=True)
        db.session.rollback()
        return False
