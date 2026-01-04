import os
import shutil
import logging
import subprocess
from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from pathlib import Path
from bunk3r_core.context_manager import ContextManager

logger = logging.getLogger(__name__)
repo_mgr_bp = Blueprint('repo_manager', __name__, url_prefix='/api/repo')

@repo_mgr_bp.route('/clone', methods=['POST'])
@login_required
def clone_repo():
    user_id = str(current_user.id)
    data = request.json
    repo_full_name = data.get('repo')
    token = data.get('token')
    
    if not repo_full_name or not token:
        return jsonify({'success': False, 'error': 'Missing repo name or token'}), 400
        
    repo_name = repo_full_name.split('/')[-1]
    context_mgr = ContextManager(user_id)
    workspace_path = context_mgr.user_workspace
    target_path = workspace_path / repo_name
    
    # Check if already exists
    if target_path.exists():
        # Update CWD and return
        context_mgr.update_cwd(str(target_path))
        return jsonify({
            'success': True, 
            'message': 'Repo already exists, workspace switched.',
            'path': str(target_path)
        })

    try:
        # Construct clone URL with token for auth
        clone_url = f"https://{token}@github.com/{repo_full_name}.git"
        
        # Clone repo
        result = subprocess.run(
            ['git', 'clone', '--depth', '1', clone_url, str(target_path)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            logger.error(f"Clone failed for {repo_full_name}: {result.stderr}")
            return jsonify({'success': False, 'error': f'Git Clone failed: {result.stderr}'}), 500
            
        # Update context
        context_mgr.update_cwd(str(target_path))
        context_mgr.update_intent(f"Analizando repositorio: {repo_full_name}", ["Explorar estructura", "Identificar tech stack"])
        
        return jsonify({
            'success': True,
            'message': 'Repository cloned successfully.',
            'path': str(target_path)
        })
        
    except Exception as e:
        logger.error(f"Repo clone error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@repo_mgr_bp.route('/status', methods=['GET'])
@login_required
def get_status():
    user_id = str(current_user.id)
    context_mgr = ContextManager(user_id)
    return jsonify({
        'success': True,
        'cwd': context_mgr.state["metadata"]["cwd"],
        'intent': context_mgr.state["history"]["logical_intent"]
    })
