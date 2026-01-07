import os
import shutil
import subprocess
import logging
import threading
from backend.models import User, db
from flask import session, jsonify, Blueprint
from flask_dance.contrib.github import github

logger = logging.getLogger(__name__)

workspace_bp = Blueprint('workspace_manager', __name__, url_prefix='/api/workspace')

class WorkspaceManager:
    def __init__(self, base_path="/workspace"):
        self.base_path = base_path
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path, exist_ok=True)
            
            os.makedirs(self.base_path, exist_ok=True)

    def get_user_workspace(self, user_id):
        path = os.path.join(self.base_path, str(user_id))
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        return path

    def sync_user_repos(self, user_id, token, app):
        """Starts background syncing of all user repos"""
        user = User.query.get(user_id)
        if user and user.sync_status == "syncing":
            return
            
        user.sync_status = "syncing"
        user.current_sync_repo = "Obteniendo lista de repositorios..."
        db.session.commit()
        
        thread = threading.Thread(target=self._sync_thread, args=(user_id, token, app))
        thread.start()

    def _sync_thread(self, user_id, token, app):
        with app.app_context():
            try:
                workspace_path = self.get_user_workspace(user_id)
                user = User.query.get(user_id)
                
                # Fetch repos using GitHub API (fetch ALL repos including private)
                import requests
                headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
                # Use visibility=all to get private and public repos
                resp = requests.get("https://api.github.com/user/repos?sort=updated&per_page=100&visibility=all", headers=headers)
                
                if not resp.ok:
                    logger.error(f"Failed to fetch repos for user {user_id}: {resp.text}")
                    user.sync_status = "error"
                    user.sync_error = "GitHub API failure"
                    db.session.commit()
                    return

                repos = resp.json()
                logger.info(f"Found {len(repos)} repos for user {user_id}")

                for repo in repos:
                    repo_name = repo['name']
                    repo_url = repo['clone_url']
                    
                    if repo_name == "CorreosPremium":
                        logger.warning(f"Skipping problematic repo {repo_name} by manual override")
                        continue

                    # Inject token into URL for private cloning
                    auth_url = repo_url.replace("https://", f"https://x-access-token:{token}@")
                    
                    target_path = os.path.join(workspace_path, repo_name)
                    
                    if not os.path.exists(target_path):
                        user.current_sync_repo = repo_name
                        db.session.commit()
                        logger.info(f"Cloning {repo_name} into {target_path}")
                        
                        # Clone using git command
                        try:
                            env = os.environ.copy()
                            env["GIT_TERMINAL_PROMPT"] = "0"
                            
                            subprocess.run(["git", "clone", "--depth", "1", auth_url, target_path], 
                                         capture_output=True, check=True, timeout=30, env=env)
                                         
                        except subprocess.TimeoutExpired:
                            logger.error(f"Timeout cloning {repo_name}")
                            if os.path.exists(target_path):
                                shutil.rmtree(target_path, ignore_errors=True)
                                
                        except subprocess.CalledProcessError as e:
                            logger.error(f"Error cloning {repo_name}: {e.stderr.decode()}")
                    else:
                        logger.info(f"Repo {repo_name} already exists, skipping clone.")

                user.sync_status = "completed"
                user.current_sync_repo = None
                db.session.commit()
                logger.info(f"Sync completed for user {user_id}")
                
            except Exception as e:
                logger.error(f"Critical error in sync thread for {user_id}: {str(e)}")
                user = User.query.get(user_id)
                if user:
                    user.sync_status = "error"
                    user.sync_error = str(e)
                    db.session.commit()

workspace_mgr = WorkspaceManager()

@workspace_bp.route('/sync-status')
def get_sync_status():
    from flask_login import current_user
    if not current_user.is_authenticated:
        return jsonify({"status": "error", "error": "Not authenticated"}), 401
    
    status_data = {
        "status": current_user.sync_status or "none",
        "current_repo": current_user.current_sync_repo,
        "error": current_user.sync_error
    }
    
    if current_user.sync_status == "completed":
        status_data["redirect"] = f"/?folder=/workspace/{current_user.id}"
        
    return jsonify(status_data)

@workspace_bp.route('/launch')
def launch_workspace():
    from flask_login import current_user
    if not current_user.is_authenticated:
        return jsonify({"success": False, "error": "Not authenticated"}), 401
        
    user_id = str(current_user.id)
    token = session.get('github_token') # Should be stored during login
    
    if not token and github.authorized:
        token = github.token.get('access_token')
        
    if not token:
        return jsonify({"success": False, "error": "Missing GitHub Token"}), 401
        
    from flask import current_app
    workspace_mgr.sync_user_repos(user_id, token, current_app._get_current_object())
    return jsonify({"success": True, "redirect": "/syncing"})
