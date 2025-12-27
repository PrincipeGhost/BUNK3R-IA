import os
import subprocess
import shlex
import logging
from flask import Blueprint, request, jsonify
from BUNK3R_IA.core.context_manager import ContextManager

logger = logging.getLogger(__name__)
terminal_bp = Blueprint('terminal', __name__, url_prefix='/api/terminal')
context_mgr = ContextManager()

@terminal_bp.route('/execute', methods=['POST'])
def execute_command():
    try:
        data = request.json
        command = data.get('command', '').strip()
        
        if not command:
            return jsonify({'success': False, 'error': 'No command provided'}), 400
            
        # Security: In a real sandbox this would be isolated. 
        # For now, we execute in the current environment but restrict dangerous calls if possible.
        # TODO: Move to E2B/Docker for full isolation.
        
        cwd = context_mgr.state["metadata"]["cwd"]
        
        # Handle 'cd' manually as it doesn't persist across subprocess calls
        if command.startswith('cd '):
            new_path = command[3:].strip()
            # Resolve relative paths
            if not os.path.isabs(new_path):
                new_path = os.path.normpath(os.path.join(cwd, new_path))
            
            if os.path.exists(new_path) and os.path.isdir(new_path):
                context_mgr.update_cwd(new_path)
                return jsonify({
                    'success': True,
                    'output': f'\x1b[1;34mCWD changed to: {new_path}\x1b[0m',
                    'cwd': new_path
                })
            else:
                return jsonify({'success': False, 'output': f'\x1b[1;31mError: Directory not found: {new_path}\x1b[0m'})

        # Execute command
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
        return jsonify({'success': False, 'output': '\x1b[1;31mError: Command timed out (30s limit)\x1b[0m'})
    except Exception as e:
        logger.error(f"Terminal execution error: {e}")
        return jsonify({'success': False, 'output': f'\x1b[1;31mSystem Error: {str(e)}\x1b[0m'})
