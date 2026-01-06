import os
import shutil
import subprocess
import logging
import threading
from flask import session, jsonify, Blueprint
from flask_dance.contrib.github import github

logger = logging.getLogger(__name__)

workspace_bp = Blueprint('workspace_manager', __name__, url_prefix='/api/workspace')

class WorkspaceManager:
    def __init__(self, base_path="/workspace"):
        self.base_path = base_path
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path, exist_ok=True)
            
        self.sync_status = {} # {user_id: {"status": "syncing", "current_repo": ""}}

    def get_user_workspace(self, user_id):
        path = os.path.join(self.base_path, str(user_id))
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        return path

    def sync_user_repos(self, user_id, token):
        """Starts background syncing of all user repos"""
        if user_id in self.sync_status and self.sync_status[user_id]["status"] == "syncing":
            return
            
        self.sync_status[user_id] = {"status": "syncing", "current_repo": "Obteniendo lista de repositorios..."}
        
        thread = threading.Thread(target=self._sync_thread, args=(user_id, token))
        thread.start()

    def _sync_thread(self, user_id, token):
        try:
            workspace_path = self.get_user_workspace(user_id)
            
            # Fetch repos using GitHub API (via requests to ensure we have the token handle)
            import requests
            headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
            resp = requests.get("https://api.github.com/user/repos?sort=updated&per_page=100", headers=headers)
            
            if not resp.ok:
                logger.error(f"Failed to fetch repos for user {user_id}: {resp.text}")
                self.sync_status[user_id] = {"status": "error", "error": "GitHub API failure"}
                return

            repos = resp.json()
            logger.info(f"Found {len(repos)} repos for user {user_id}")

            for repo in repos:
                repo_name = repo['name']
                repo_url = repo['clone_url']
                # Inject token into URL for private cloning
                auth_url = repo_url.replace("https://", f"https://x-access-token:{token}@")
                
                if repo_name == "CorreosPremium":
                    logger.warning(f"Skipping problematic repo {repo_name} by manual override")
                    continue

                target_path = os.path.join(workspace_path, repo_name)
                
                if not os.path.exists(target_path):
                    self.sync_status[user_id]["current_repo"] = repo_name
                    logger.info(f"Cloning {repo_name} into {target_path}")
                    
                    # Clone using git command
                    try:
                        env = os.environ.copy()
                        env["GIT_TERMINAL_PROMPT"] = "0" # Disable prompt for password
                        
                        subprocess.run(["git", "clone", "--depth", "1", auth_url, target_path], 
                                     capture_output=True, check=True, timeout=30, env=env)
                                     
                    except subprocess.TimeoutExpired:
                        logger.error(f"Timeout cloning {repo_name}")
                        # Clean up partial clone
                        if os.path.exists(target_path):
                            shutil.rmtree(target_path, ignore_errors=True)
                            
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Error cloning {repo_name}: {e.stderr.decode()}")
                else:
                    logger.info(f"Repo {repo_name} already exists, skipping clone.")

            self.sync_status[user_id] = {"status": "completed"}
            logger.info(f"Sync completed for user {user_id}")
            
        except Exception as e:
            logger.error(f"Critical error in sync thread for {user_id}: {str(e)}")
            self.sync_status[user_id] = {"status": "error", "error": str(e)}

workspace_mgr = WorkspaceManager()

@workspace_bp.route('/sync-status')
def get_sync_status():
    from flask_login import current_user
    if not current_user.is_authenticated:
        return jsonify({"status": "error", "error": "Not authenticated"}), 401
    
    user_id = str(current_user.id)
    status = workspace_mgr.sync_status.get(user_id, {"status": "none"})
    
    # If completed, provide the IDE launch URL with folder param
    if status.get("status") == "completed":
        status["redirect"] = f"/?folder=/workspace/{user_id}"
        
    return jsonify(status)

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
        
    workspace_mgr.sync_user_repos(user_id, token)
    return jsonify({"success": True, "redirect": "/syncing"})
