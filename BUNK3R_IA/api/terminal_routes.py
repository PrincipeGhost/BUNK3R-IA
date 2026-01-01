import os
import subprocess
import shlex
import logging
from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from BUNK3R_IA.core.legacy_v1_archive.context_manager import ContextManager

logger = logging.getLogger(__name__)
terminal_bp = Blueprint('terminal', __name__, url_prefix='/api/terminal')

@terminal_bp.route('/execute', methods=['POST'])
@login_required
def execute_command():
    user_id = str(current_user.id)
    context_mgr = ContextManager(user_id)
    
    try:
        data = request.json
        command = data.get('command', '').strip()
        
        if not command:
            return jsonify({'success': False, 'error': 'No command provided'}), 400
            
        cwd = context_mgr.state["metadata"]["cwd"]
        
        # Handle 'cd' manually as it doesn't persist across subprocess calls
        if command.startswith('cd '):
            new_inner_path = command[3:].strip()
            # Resolve relative paths
            if not os.path.isabs(new_inner_path):
                new_full_path = os.path.normpath(os.path.join(cwd, new_inner_path))
            else:
                new_full_path = os.path.normpath(new_inner_path)
            
            if os.path.exists(new_full_path) and os.path.isdir(new_full_path):
                if context_mgr.update_cwd(new_full_path):
                    return jsonify({
                        'success': True,
                        'output': f'\x1b[1;34mCWD cambiado a: {new_full_path}\x1b[0m',
                        'cwd': new_full_path
                    })
                else:
                    return jsonify({'success': False, 'output': f'\x1b[1;31mError de Seguridad: No puedes salir de tu Sandbox\x1b[0m'})
            else:
                return jsonify({'success': False, 'output': f'\x1b[1;31mError: Directorio no encontrado: {new_inner_path}\x1b[0m'})

        # Execute command - Enforce CWD is within jail
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30
        )
        
        output = result.stdout + result.stderr
        status = "success" if result.returncode == 0 else "failed"
        
        # Save to context
        context_mgr.add_command(command, status, output)
        
        return jsonify({
            'success': True,
            'output': output,
            'returncode': result.returncode,
            'cwd': cwd
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'output': '\x1b[1;31mError: Tiempo de ejecución agotado (30s)\x1b[0m'})
    except Exception as e:
        logger.error(f"Terminal execution error for user {user_id}: {e}")
        return jsonify({'success': False, 'output': f'\x1b[1;31mError del Sistema: {str(e)}\x1b[0m'})
