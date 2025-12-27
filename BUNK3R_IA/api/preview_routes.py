
from flask import Blueprint, send_from_directory, abort, current_app
from flask_login import current_user, login_required
import os
from BUNK3R_IA.core.context_manager import ContextManager

preview_bp = Blueprint('preview', __name__)

@preview_bp.route('/api/preview/<user_id>/', defaults={'filename': 'index.html'})
@preview_bp.route('/api/preview/<user_id>/<path:filename>')
@login_required
def serve_preview_file(user_id, filename):
    """
    Serves static files from a user's jailed workspace.
    Enforces security via ContextManager.
    """
    # Security: Ensure requesting user matches target user or is admin (if we had admins)
    if current_user.id != user_id:
        abort(403, "Access denied to this workspace.")

    # Get the user's workspace path securely
    try:
        # We use a temporary context manager just to resolve the path securely
        ctx = ContextManager(user_id)
        workspace_root = ctx.root_dir
        
        # Ensure the file exists within the jail
        safe_path = os.path.normpath(os.path.join(workspace_root, filename))
        
        if not safe_path.startswith(workspace_root):
            abort(403, "Path traversal detected.")
            
        if not os.path.exists(safe_path):
            return abort(404, f"File not found: {filename}")

        # Serve the file
        return send_from_directory(workspace_root, filename)

    except Exception as e:
        current_app.logger.error(f"Preview Error: {str(e)}")
        return abort(500, "Internal Server Error during preview.")
