import os
import subprocess
import logging
from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user, login_required
from pathlib import Path

logger = logging.getLogger(__name__)
git_bp = Blueprint('git', __name__, url_prefix='/api/git')

def get_repo_path(repo_name):
    user_id = str(current_user.id)
    workspaces_dir = current_app.config.get('WORKSPACES_DIR', 'backend/workspaces')
    path = Path(workspaces_dir) / user_id / 'repos' / repo_name
    return path if path.exists() else None

def run_git_command(repo_path, args):
    try:
        result = subprocess.run(
            ['git'] + args,
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=15
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        logger.error(f"Git execution error: {e}")
        return {"success": False, "error": str(e)}

@git_bp.route('/status', methods=['GET'])
@login_required
def git_status():
    repo_name = request.args.get('repo')
    if not repo_name:
        return jsonify({"success": False, "error": "No repository specified"}), 400
    
    repo_path = get_repo_path(repo_name)
    if not repo_path:
        return jsonify({"success": False, "error": "Repository not found"}), 404
    
    # Get status porcelain for easy parsing
    res = run_git_command(repo_path, ['status', '--porcelain'])
    if not res["success"]:
        return jsonify(res)
    
    lines = res["stdout"].strip().split('\n')
    changes = []
    for line in lines:
        if not line: continue
        status = line[:2]
        file_path = line[3:]
        changes.append({
            "status": status,
            "path": file_path
        })
    
    # Get current branch
    branch_res = run_git_command(repo_path, ['rev-parse', '--abbrev-ref', 'HEAD'])
    branch = branch_res["stdout"].strip() if branch_res["success"] else "unknown"
    
    return jsonify({
        "success": True, 
        "changes": changes,
        "branch": branch
    })

@git_bp.route('/stage', methods=['POST'])
@login_required
def git_stage():
    data = request.json
    repo_name = data.get('repo')
    file_path = data.get('path')
    
    repo_path = get_repo_path(repo_name)
    if not repo_path: return jsonify({"success": False, "error": "Repo not found"}), 404
    
    res = run_git_command(repo_path, ['add', file_path])
    return jsonify(res)

@git_bp.route('/unstage', methods=['POST'])
@login_required
def git_unstage():
    data = request.json
    repo_name = data.get('repo')
    file_path = data.get('path')
    
    repo_path = get_repo_path(repo_name)
    if not repo_path: return jsonify({"success": False, "error": "Repo not found"}), 404
    
    res = run_git_command(repo_path, ['reset', 'HEAD', file_path])
    return jsonify(res)

@git_bp.route('/commit', methods=['POST'])
@login_required
def git_commit():
    data = request.json
    repo_name = data.get('repo')
    message = data.get('message')
    
    if not message:
        return jsonify({"success": False, "error": "Commit message is required"}), 400
        
    repo_path = get_repo_path(repo_name)
    if not repo_path: return jsonify({"success": False, "error": "Repo not found"}), 404
    
    # Ensure config exists for commit
    run_git_command(repo_path, ['config', 'user.email', 'bunk3r@ai.local'])
    run_git_command(repo_path, ['config', 'user.name', 'BUNK3R AI'])
    
    res = run_git_command(repo_path, ['commit', '-m', message])
    return jsonify(res)

@git_bp.route('/push', methods=['POST'])
@login_required
def git_push():
    data = request.json
    repo_name = data.get('repo')
    
    repo_path = get_repo_path(repo_name)
    if not repo_path: return jsonify({"success": False, "error": "Repo not found"}), 404
    
    # We might need to inject the token here if not using SSH
    # For now, try simple push
    res = run_git_command(repo_path, ['push', 'origin', 'HEAD'])
    return jsonify(res)
