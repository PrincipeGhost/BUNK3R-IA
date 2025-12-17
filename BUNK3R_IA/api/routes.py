"""
BUNK3R_IA API Routes - Rutas de la API de IA
Extraídas del proyecto principal para funcionar de forma independiente
"""
import os
import io
import json
import zipfile
import logging
from datetime import datetime
from functools import wraps
from flask import Blueprint, request, jsonify, send_file

logger = logging.getLogger(__name__)

ai_bp = Blueprint('ai', __name__, url_prefix='/api')

def get_db_manager():
    """Get database manager (to be configured externally)"""
    from BUNK3R_IA.core.ai_service import db_manager
    return db_manager

def set_db_manager(manager):
    """Set database manager"""
    import BUNK3R_IA.core.ai_service as ai_service_module
    ai_service_module.db_manager = manager

ai_constructor_service = None

def get_ai_constructor():
    """Get or create AI Constructor Service instance"""
    global ai_constructor_service
    from BUNK3R_IA.core.ai_service import get_ai_service
    from BUNK3R_IA.core.ai_constructor import AIConstructorService
    
    if ai_constructor_service is None:
        db_manager = get_db_manager()
        if db_manager is None:
            raise ValueError("Database not available")
        ai_service = get_ai_service(db_manager)
        if ai_service is None:
            raise ValueError("AI service not available")
        ai_constructor_service = AIConstructorService(ai_service)
    return ai_constructor_service

def sanitize_constructor_response(result):
    """Sanitize AI Constructor response for JSON serialization"""
    if not isinstance(result, dict):
        return result
    
    def convert_value(v):
        if isinstance(v, datetime):
            return v.isoformat()
        elif isinstance(v, dict):
            return {k: convert_value(val) for k, val in v.items()}
        elif isinstance(v, list):
            return [convert_value(item) for item in v]
        elif hasattr(v, 'to_dict'):
            return convert_value(v.to_dict())
        elif hasattr(v, 'value'):
            return v.value
        return v
    
    return {k: convert_value(v) for k, v in result.items()}

def sanitize_error(e, context=''):
    """Sanitize error for safe display"""
    return f"Error in {context}: {str(e)[:100]}"

@ai_bp.route('/ai/chat', methods=['POST'])
def ai_chat():
    """Send message to AI and get response"""
    try:
        from BUNK3R_IA.core.ai_service import get_ai_service
        
        data = request.json
        user_id = data.get('user_id', 'anonymous')
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        ai = get_ai_service(get_db_manager())
        result = ai.chat(user_id, message)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        return jsonify({'success': False, 'error': 'Error processing message'}), 500

@ai_bp.route('/ai/history', methods=['GET'])
def ai_history():
    """Get AI chat history"""
    try:
        from BUNK3R_IA.core.ai_service import get_ai_service
        
        user_id = request.args.get('user_id', 'anonymous')
        ai = get_ai_service(get_db_manager())
        history = ai.get_conversation_history(user_id)
        providers = ai.get_available_providers()
        
        return jsonify({
            'success': True,
            'history': history,
            'providers': providers
        })
    except Exception as e:
        logger.error(f"AI history error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai/clear', methods=['POST'])
def ai_clear():
    """Clear AI chat history"""
    try:
        from BUNK3R_IA.core.ai_service import get_ai_service
        
        data = request.json
        user_id = data.get('user_id', 'anonymous')
        ai = get_ai_service(get_db_manager())
        ai.clear_conversation(user_id)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"AI clear error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai/code-builder', methods=['POST'])
def ai_code_builder():
    """AI-powered code generation for web projects"""
    try:
        from BUNK3R_IA.core.ai_service import get_ai_service
        
        data = request.json
        user_id = data.get('user_id', 'anonymous')
        message = data.get('message', '').strip()
        current_files = data.get('currentFiles', {})
        project_name = data.get('projectName', 'Mi Proyecto')
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        ai = get_ai_service(get_db_manager())
        result = ai.generate_code(user_id, message, current_files, project_name)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI code builder error: {e}")
        return jsonify({'success': False, 'error': 'Error generating code'}), 500

@ai_bp.route('/ai-constructor/process', methods=['POST'])
def ai_constructor_process():
    """Process message through AI Constructor's 8-phase architecture"""
    try:
        data = request.json
        user_id = data.get('user_id', 'anonymous')
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        constructor = get_ai_constructor()
        result = constructor.process_message(user_id, message)
        sanitized_result = sanitize_constructor_response(result)
        
        return jsonify(sanitized_result)
    except ValueError as e:
        return jsonify({'success': False, 'error': sanitize_error(e, 'ai_constructor_process')}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': sanitize_error(e, 'ai_constructor_process')}), 500

@ai_bp.route('/ai-constructor/session', methods=['GET'])
def ai_constructor_session():
    """Get current AI Constructor session status"""
    try:
        user_id = request.args.get('user_id', 'anonymous')
        constructor = get_ai_constructor()
        session = constructor.get_session_status(user_id)
        
        if session:
            sanitized_session = sanitize_constructor_response(session)
            return jsonify({
                'success': True,
                'hasSession': True,
                'session': sanitized_session
            })
        else:
            return jsonify({
                'success': True,
                'hasSession': False,
                'session': None
            })
    except ValueError as e:
        return jsonify({'success': False, 'error': sanitize_error(e, 'ai_constructor_session')}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': sanitize_error(e, 'ai_constructor_session')}), 500

@ai_bp.route('/ai-constructor/reset', methods=['POST'])
def ai_constructor_reset():
    """Reset AI Constructor session"""
    try:
        data = request.json
        user_id = data.get('user_id', 'anonymous')
        constructor = get_ai_constructor()
        constructor.reset_session(user_id)
        
        return jsonify({'success': True, 'message': 'Session reset successfully'})
    except ValueError as e:
        return jsonify({'success': False, 'error': sanitize_error(e, 'ai_constructor_reset')}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': sanitize_error(e, 'ai_constructor_reset')}), 500

@ai_bp.route('/ai-constructor/files', methods=['GET'])
def ai_constructor_files():
    """Get files generated by AI Constructor"""
    try:
        user_id = request.args.get('user_id', 'anonymous')
        constructor = get_ai_constructor()
        files = constructor.get_generated_files(user_id)
        
        if files:
            sanitized_files = sanitize_constructor_response({'files': files})
            return jsonify({
                'success': True,
                'hasFiles': True,
                'files': sanitized_files.get('files', {}),
                'fileCount': len(files)
            })
        else:
            return jsonify({
                'success': True,
                'hasFiles': False,
                'files': {},
                'fileCount': 0
            })
    except ValueError as e:
        return jsonify({'success': False, 'error': sanitize_error(e, 'ai_constructor_files')}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': sanitize_error(e, 'ai_constructor_files')}), 500

@ai_bp.route('/ai-constructor/confirm', methods=['POST'])
def ai_constructor_confirm():
    """Confirm plan and continue execution"""
    try:
        data = request.json
        user_id = data.get('user_id', 'anonymous')
        confirmed = data.get('confirmed', True)
        
        constructor = get_ai_constructor()
        
        if confirmed:
            result = constructor.process_message(user_id, "confirmo el plan")
            sanitized_result = sanitize_constructor_response(result)
            return jsonify(sanitized_result)
        else:
            constructor.reset_session(user_id)
            return jsonify({'success': True, 'message': 'Session cancelled'})
    except ValueError as e:
        return jsonify({'success': False, 'error': sanitize_error(e, 'ai_constructor_confirm')}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': sanitize_error(e, 'ai_constructor_confirm')}), 500

@ai_bp.route('/ai-constructor/flow', methods=['GET'])
def ai_constructor_flow():
    """Get AI Constructor flow log for debugging"""
    try:
        from BUNK3R_IA.core.ai_flow_logger import flow_logger
        user_id = request.args.get('user_id', 'anonymous')
        
        flow = flow_logger.get_session_flow(user_id)
        if flow:
            return jsonify({
                'success': True,
                'flow': flow,
                'formatted': flow_logger.format_flow_for_display(user_id)
            })
        else:
            return jsonify({
                'success': True,
                'flow': None,
                'message': 'No hay sesión activa para este usuario'
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-constructor/flow/all', methods=['GET'])
def ai_constructor_flow_all():
    """Get all AI Constructor sessions summary"""
    try:
        from BUNK3R_IA.core.ai_flow_logger import flow_logger
        
        sessions = flow_logger.get_all_sessions_summary()
        recent = flow_logger.get_recent_interactions(50)
        
        return jsonify({
            'success': True,
            'sessions': sessions,
            'recent_interactions': recent,
            'total_sessions': len(sessions)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-constructor/flow/clear', methods=['POST'])
def ai_constructor_flow_clear():
    """Clear flow logs"""
    try:
        from BUNK3R_IA.core.ai_flow_logger import flow_logger
        
        data = request.json or {}
        user_id = data.get('user_id', 'anonymous')
        clear_all = data.get('clear_all', False)
        
        if clear_all:
            flow_logger.clear_all()
            return jsonify({'success': True, 'message': 'All flow logs cleared'})
        else:
            flow_logger.clear_session(user_id)
            return jsonify({'success': True, 'message': f'Flow log cleared for user {user_id}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-constructor/download-zip', methods=['GET'])
def ai_constructor_download_zip():
    """Download generated project as ZIP file"""
    try:
        global ai_constructor_service
        user_id = request.args.get('user_id', 'anonymous')
        
        if ai_constructor_service is None:
            return jsonify({'success': False, 'error': 'AI Constructor service not available'}), 500
        
        files = ai_constructor_service.get_generated_files(user_id)
        
        if not files:
            return jsonify({'success': False, 'error': 'No hay archivos generados para descargar'}), 404
        
        memory_file = io.BytesIO()
        
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for filename, content in files.items():
                safe_filename = os.path.normpath(filename).lstrip(os.sep)
                safe_filename = safe_filename.replace('..', '')
                if not safe_filename:
                    safe_filename = 'unnamed_file'
                zf.writestr(safe_filename, content)
        
        memory_file.seek(0)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f'bunkr_project_{timestamp}.zip'
        
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
    except Exception as e:
        logger.error(f"Error creating ZIP: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-toolkit/files/read', methods=['POST'])
def ai_toolkit_read_file():
    """Read file content using AI Toolkit"""
    try:
        from BUNK3R_IA.core.ai_toolkit import AIFileToolkit
        data = request.json
        path = data.get('path', '')
        max_lines = data.get('max_lines')
        
        if not path:
            return jsonify({'success': False, 'error': 'Path is required'}), 400
        
        toolkit = AIFileToolkit()
        result = toolkit.read_file(path, max_lines)
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI Toolkit read error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-toolkit/files/write', methods=['POST'])
def ai_toolkit_write_file():
    """Write file content using AI Toolkit"""
    try:
        from BUNK3R_IA.core.ai_toolkit import AIFileToolkit
        data = request.json
        path = data.get('path', '')
        content = data.get('content', '')
        
        if not path:
            return jsonify({'success': False, 'error': 'Path is required'}), 400
        
        toolkit = AIFileToolkit()
        result = toolkit.write_file(path, content)
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI Toolkit write error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-toolkit/files/edit', methods=['POST'])
def ai_toolkit_edit_file():
    """Edit file by replacing content using AI Toolkit"""
    try:
        from BUNK3R_IA.core.ai_toolkit import AIFileToolkit
        data = request.json
        path = data.get('path', '')
        old_content = data.get('old_content', '')
        new_content = data.get('new_content', '')
        
        if not path or not old_content:
            return jsonify({'success': False, 'error': 'Path and old_content are required'}), 400
        
        toolkit = AIFileToolkit()
        result = toolkit.edit_file(path, old_content, new_content)
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI Toolkit edit error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-toolkit/files/delete', methods=['POST'])
def ai_toolkit_delete_file():
    """Delete file using AI Toolkit - Requires explicit confirmation"""
    try:
        from BUNK3R_IA.core.ai_toolkit import AIFileToolkit
        data = request.json
        path = data.get('path', '')
        confirm = data.get('confirm', False)
        confirm_text = data.get('confirm_text', '')
        
        if not path:
            return jsonify({'success': False, 'error': 'Path is required'}), 400
        
        if not confirm or confirm_text != 'DELETE':
            return jsonify({
                'success': False, 
                'error': 'Deletion requires confirm=true AND confirm_text="DELETE"',
                'requires_confirmation': True,
                'path': path
            }), 400
        
        toolkit = AIFileToolkit()
        result = toolkit.delete_file(path, confirm=True)
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI Toolkit delete error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-toolkit/files/list', methods=['POST'])
def ai_toolkit_list_directory():
    """List directory contents using AI Toolkit"""
    try:
        from BUNK3R_IA.core.ai_toolkit import AIFileToolkit
        data = request.json or {}
        path = data.get('path', '.')
        recursive = data.get('recursive', False)
        max_depth = data.get('max_depth', 3)
        
        toolkit = AIFileToolkit()
        result = toolkit.list_directory(path, recursive, max_depth)
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI Toolkit list error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-toolkit/files/search', methods=['POST'])
def ai_toolkit_search_code():
    """Search code using AI Toolkit"""
    try:
        from BUNK3R_IA.core.ai_toolkit import AIFileToolkit
        data = request.json
        query = data.get('query', '')
        path = data.get('path', '.')
        file_pattern = data.get('file_pattern')
        
        if not query:
            return jsonify({'success': False, 'error': 'Query is required'}), 400
        
        toolkit = AIFileToolkit()
        result = toolkit.search_code(query, path, file_pattern)
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI Toolkit search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-toolkit/command/run', methods=['POST'])
def ai_toolkit_run_command():
    """Execute command using AI Toolkit"""
    try:
        from BUNK3R_IA.core.ai_toolkit import AICommandExecutor
        data = request.json
        command = data.get('command', '')
        timeout = data.get('timeout', 30)
        
        if not command:
            return jsonify({'success': False, 'error': 'Command is required'}), 400
        
        executor = AICommandExecutor()
        result = executor.run_command(command, timeout)
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI Toolkit command error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-toolkit/command/install', methods=['POST'])
def ai_toolkit_install_package():
    """Install package using AI Toolkit"""
    try:
        from BUNK3R_IA.core.ai_toolkit import AICommandExecutor
        data = request.json
        package = data.get('package', '')
        manager = data.get('manager', 'pip')
        
        if not package:
            return jsonify({'success': False, 'error': 'Package name is required'}), 400
        
        executor = AICommandExecutor()
        result = executor.install_package(package, manager)
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI Toolkit install error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-toolkit/command/script', methods=['POST'])
def ai_toolkit_run_script():
    """Run a script file using AI Toolkit"""
    try:
        from BUNK3R_IA.core.ai_toolkit import AICommandExecutor
        data = request.json
        script_path = data.get('script_path', '')
        interpreter = data.get('interpreter', 'python')
        
        if not script_path:
            return jsonify({'success': False, 'error': 'Script path is required'}), 400
        
        executor = AICommandExecutor()
        result = executor.run_script(script_path, interpreter)
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI Toolkit script error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-toolkit/errors/detect', methods=['POST'])
def ai_toolkit_detect_errors():
    """Detect errors in logs using AI Toolkit"""
    try:
        from BUNK3R_IA.core.ai_toolkit import AIErrorDetector
        data = request.json
        logs = data.get('logs', [])
        language = data.get('language', 'python')
        
        if not logs:
            return jsonify({'success': False, 'error': 'Logs are required'}), 400
        
        detector = AIErrorDetector()
        result = detector.detect_errors(logs, language)
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI Toolkit error detection: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-toolkit/errors/analyze', methods=['POST'])
def ai_toolkit_analyze_error():
    """Analyze error and suggest fix using AI Toolkit"""
    try:
        from BUNK3R_IA.core.ai_toolkit import AIErrorDetector
        data = request.json
        error = data.get('error', {})
        
        if not error:
            return jsonify({'success': False, 'error': 'Error data is required'}), 400
        
        detector = AIErrorDetector()
        analysis = detector.analyze_error(error)
        fix = detector.suggest_fix(error)
        
        return jsonify({
            'success': True,
            'analysis': analysis.get('analysis'),
            'fixes': fix.get('fixes', []),
            'auto_fixable': fix.get('auto_fixable', False)
        })
    except Exception as e:
        logger.error(f"AI Toolkit error analysis: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-toolkit/project/analyze', methods=['GET'])
def ai_toolkit_analyze_project():
    """Analyze project structure using AI Toolkit"""
    try:
        from BUNK3R_IA.core.ai_toolkit import AIProjectAnalyzer
        
        analyzer = AIProjectAnalyzer()
        result = analyzer.analyze_project()
        
        if result['success']:
            result['context'] = analyzer.generate_context()
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI Toolkit project analysis: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-core/process', methods=['POST'])
def ai_core_process_message():
    """Process user message and determine workflow"""
    try:
        from BUNK3R_IA.core.ai_core_engine import AICoreOrchestrator
        
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        orchestrator = AICoreOrchestrator()
        result = orchestrator.process_user_message(message)
        
        return jsonify({'success': True, **result})
    except Exception as e:
        logger.error(f"AI Core process: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-core/intent/classify', methods=['POST'])
def ai_core_classify_intent():
    """Classify user intent from message"""
    try:
        from BUNK3R_IA.core.ai_core_engine import AIDecisionEngine
        
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        engine = AIDecisionEngine()
        intent = engine.classify_intent(message)
        
        return jsonify({
            'success': True,
            'intent': {
                'type': intent.type.value,
                'confidence': intent.confidence,
                'keywords': intent.keywords,
                'target_file': intent.target_file,
                'target_function': intent.target_function,
            }
        })
    except Exception as e:
        logger.error(f"AI Core intent classify: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-core/workflow/decide', methods=['POST'])
def ai_core_decide_workflow():
    """Decide workflow based on intent"""
    try:
        from BUNK3R_IA.core.ai_core_engine import AIDecisionEngine, IntentType, Intent
        
        data = request.json
        intent_type = data.get('intent_type', 'ambiguous')
        
        engine = AIDecisionEngine()
        intent = Intent(
            type=IntentType(intent_type),
            confidence=1.0,
            keywords=[],
            original_message=''
        )
        workflow = engine.decide_workflow(intent)
        
        return jsonify({
            'success': True,
            'workflow': {
                'name': workflow.name,
                'steps': [s.value for s in workflow.steps],
                'total_steps': len(workflow.steps),
            }
        })
    except Exception as e:
        logger.error(f"AI Core workflow decide: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-core/validate', methods=['POST'])
def ai_core_validate_action():
    """Validate action before execution"""
    try:
        from BUNK3R_IA.core.ai_core_engine import PreExecutionValidator
        
        data = request.json
        action_type = data.get('action_type', 'edit')
        action_params = data.get('params', {})
        
        validator = PreExecutionValidator()
        result = validator.validate_before_action(action_type, **action_params)
        
        return jsonify({
            'success': True,
            'valid': result.valid,
            'checks': result.checks,
            'errors': result.errors,
            'warnings': result.warnings
        })
    except Exception as e:
        logger.error(f"AI Core validate: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-core/checkpoint/create', methods=['POST'])
def ai_core_create_checkpoint():
    """Create a checkpoint before making changes"""
    try:
        from BUNK3R_IA.core.ai_core_engine import RollbackManager
        
        data = request.json
        files = data.get('files', [])
        description = data.get('description', '')
        
        if not files:
            return jsonify({'success': False, 'error': 'Files list is required'}), 400
        
        manager = RollbackManager()
        checkpoint_id = manager.create_checkpoint(files, description)
        
        if checkpoint_id:
            return jsonify({
                'success': True,
                'checkpoint_id': checkpoint_id,
                'files_saved': len(files)
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to create checkpoint'}), 500
    except Exception as e:
        logger.error(f"AI Core checkpoint create: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-core/checkpoint/rollback', methods=['POST'])
def ai_core_rollback_checkpoint():
    """Rollback to a checkpoint"""
    try:
        from BUNK3R_IA.core.ai_core_engine import RollbackManager
        
        data = request.json
        checkpoint_id = data.get('checkpoint_id', '')
        
        if not checkpoint_id:
            return jsonify({'success': False, 'error': 'Checkpoint ID is required'}), 400
        
        manager = RollbackManager()
        result = manager.rollback_to_checkpoint(checkpoint_id)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI Core rollback: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-core/checkpoint/list', methods=['GET'])
def ai_core_list_checkpoints():
    """List available checkpoints"""
    try:
        from BUNK3R_IA.core.ai_core_engine import RollbackManager
        
        manager = RollbackManager()
        checkpoints = manager.get_checkpoints()
        
        return jsonify({
            'success': True,
            'checkpoints': checkpoints,
            'count': len(checkpoints)
        })
    except Exception as e:
        logger.error(f"AI Core list checkpoints: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-core/impact/analyze', methods=['POST'])
def ai_core_analyze_impact():
    """Analyze impact of changing a file"""
    try:
        from BUNK3R_IA.core.ai_core_engine import ChangeImpactAnalyzer
        
        data = request.json
        file_path = data.get('file_path', '')
        change_description = data.get('change_description', '')
        
        if not file_path:
            return jsonify({'success': False, 'error': 'File path is required'}), 400
        
        analyzer = ChangeImpactAnalyzer()
        impact = analyzer.analyze_impact(file_path, change_description)
        
        return jsonify({
            'success': True,
            'impact': {
                'importers': impact.importers,
                'usages': impact.usages,
                'tests': impact.tests,
                'breaking_changes': impact.breaking_changes,
                'risk_level': impact.risk_level
            }
        })
    except Exception as e:
        logger.error(f"AI Core impact analyze: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-core/workflow/status', methods=['GET'])
def ai_core_workflow_status():
    """Get workflow/server status"""
    try:
        from BUNK3R_IA.core.ai_core_engine import WorkflowManager
        
        name = request.args.get('name', 'main')
        
        manager = WorkflowManager()
        status = manager.get_workflow_status(name)
        
        return jsonify({'success': True, **status})
    except Exception as e:
        logger.error(f"AI Core workflow status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-core/workflow/health', methods=['GET'])
def ai_core_workflow_health():
    """Check server health"""
    try:
        from BUNK3R_IA.core.ai_core_engine import WorkflowManager
        
        port = request.args.get('port', 5000, type=int)
        path = request.args.get('path', '/')
        
        manager = WorkflowManager()
        health = manager.check_server_health(port, path)
        
        return jsonify({'success': True, **health})
    except Exception as e:
        logger.error(f"AI Core workflow health: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-core/tasks/create', methods=['POST'])
def ai_core_create_tasks():
    """Create a task list"""
    try:
        from BUNK3R_IA.core.ai_core_engine import TaskManager
        
        data = request.json
        tasks = data.get('tasks', [])
        
        if not tasks:
            return jsonify({'success': False, 'error': 'Tasks list is required'}), 400
        
        manager = TaskManager()
        created_tasks = manager.create_task_list(tasks)
        
        return jsonify({
            'success': True,
            'session_id': manager.session_id,
            'tasks_created': len(created_tasks)
        })
    except Exception as e:
        logger.error(f"AI Core create tasks: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-core/tasks/progress', methods=['GET'])
def ai_core_tasks_progress():
    """Get task progress"""
    try:
        from BUNK3R_IA.core.ai_core_engine import TaskManager
        
        manager = TaskManager()
        progress = manager.show_progress_to_user()
        
        return jsonify({'success': True, **progress})
    except Exception as e:
        logger.error(f"AI Core tasks progress: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/ai-core/status', methods=['GET'])
def ai_core_full_status():
    """Get full AI Core status"""
    try:
        from BUNK3R_IA.core.ai_core_engine import AICoreOrchestrator
        
        orchestrator = AICoreOrchestrator()
        status = orchestrator.get_full_status()
        
        return jsonify({'success': True, **status})
    except Exception as e:
        logger.error(f"AI Core full status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'service': 'BUNK3R_IA',
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    })


# ========================================
# NUEVOS ENDPOINTS (34.3, 34.4, 34.5, 34.17, 34.19)
# ========================================

@ai_bp.route('/ai-verifier/verify', methods=['POST'])
def ai_verify_code():
    """Verify code syntax and quality (34.5 OutputVerifier)"""
    try:
        from BUNK3R_IA.core.output_verifier import output_verifier
        
        data = request.json
        code = data.get('code', '')
        filename = data.get('filename')
        
        if not code:
            return jsonify({'success': False, 'error': 'Code is required'}), 400
        
        report = output_verifier.verify(code, filename)
        
        return jsonify({
            'success': True,
            **report.to_dict()
        })
    except Exception as e:
        logger.error(f"Code verification error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-verifier/quick', methods=['POST'])
def ai_verify_quick():
    """Quick syntax validation (34.5 OutputVerifier)"""
    try:
        from BUNK3R_IA.core.output_verifier import output_verifier
        
        data = request.json
        code = data.get('code', '')
        
        if not code:
            return jsonify({'success': False, 'error': 'Code is required'}), 400
        
        is_valid, message = output_verifier.quick_validate(code)
        
        return jsonify({
            'success': True,
            'is_valid': is_valid,
            'message': message
        })
    except Exception as e:
        logger.error(f"Quick verification error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-clarification/detect', methods=['POST'])
def ai_clarification_detect():
    """Detect ambiguity in request (34.3 ClarificationManager)"""
    try:
        from BUNK3R_IA.core.clarification_manager import clarification_manager
        
        data = request.json
        request_text = data.get('request', '')
        
        if not request_text:
            return jsonify({'success': False, 'error': 'Request text is required'}), 400
        
        ambiguity = clarification_manager.detect_ambiguity(request_text)
        
        return jsonify({
            'success': True,
            **ambiguity.to_dict()
        })
    except Exception as e:
        logger.error(f"Ambiguity detection error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-clarification/questions', methods=['POST'])
def ai_clarification_questions():
    """Generate clarification questions (34.3 ClarificationManager)"""
    try:
        from BUNK3R_IA.core.clarification_manager import clarification_manager
        
        data = request.json
        request_text = data.get('request', '')
        max_questions = data.get('max_questions', 3)
        
        if not request_text:
            return jsonify({'success': False, 'error': 'Request text is required'}), 400
        
        questions = clarification_manager.generate_questions(request_text, max_questions=max_questions)
        
        return jsonify({
            'success': True,
            'questions': [q.to_dict() for q in questions],
            'count': len(questions),
            'formatted': clarification_manager.format_questions_for_chat(questions)
        })
    except Exception as e:
        logger.error(f"Clarification questions error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-clarification/session', methods=['POST'])
def ai_clarification_session():
    """Create clarification session (34.3 ClarificationManager)"""
    try:
        from BUNK3R_IA.core.clarification_manager import clarification_manager
        import uuid
        
        data = request.json
        user_id = data.get('user_id', 'anonymous')
        request_text = data.get('request', '')
        
        if not request_text:
            return jsonify({'success': False, 'error': 'Request text is required'}), 400
        
        session_id = str(uuid.uuid4())[:8]
        session = clarification_manager.create_session(session_id, user_id, request_text)
        
        return jsonify({
            'success': True,
            **session.to_dict()
        })
    except Exception as e:
        logger.error(f"Clarification session error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-clarification/answer', methods=['POST'])
def ai_clarification_answer():
    """Submit answer to clarification question (34.3 ClarificationManager)"""
    try:
        from BUNK3R_IA.core.clarification_manager import clarification_manager
        
        data = request.json
        session_id = data.get('session_id', '')
        question_id = data.get('question_id', '')
        answer = data.get('answer', '')
        
        if not all([session_id, question_id, answer]):
            return jsonify({'success': False, 'error': 'session_id, question_id and answer are required'}), 400
        
        success, next_question = clarification_manager.submit_answer(session_id, question_id, answer)
        
        session = clarification_manager.get_session(session_id)
        
        return jsonify({
            'success': success,
            'completed': session.completed if session else False,
            'next_question': next_question.to_dict() if next_question else None,
            'enriched_request': clarification_manager.get_enriched_request(session_id) if session and session.completed else None
        })
    except Exception as e:
        logger.error(f"Clarification answer error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-plan/create', methods=['POST'])
def ai_plan_create():
    """Create execution plan (34.4 PlanPresenter)"""
    try:
        from BUNK3R_IA.core.plan_presenter import plan_presenter
        import uuid
        
        data = request.json
        title = data.get('title', 'Plan de Ejecución')
        description = data.get('description', '')
        tasks = data.get('tasks', [])
        context = data.get('context', {})
        
        if not tasks:
            return jsonify({'success': False, 'error': 'Tasks list is required'}), 400
        
        plan_id = str(uuid.uuid4())[:8]
        plan = plan_presenter.create_plan(plan_id, title, description, tasks, context)
        
        return jsonify({
            'success': True,
            **plan.to_dict()
        })
    except Exception as e:
        logger.error(f"Plan creation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-plan/format', methods=['GET'])
def ai_plan_format():
    """Get formatted plan (34.4 PlanPresenter)"""
    try:
        from BUNK3R_IA.core.plan_presenter import plan_presenter
        
        plan_id = request.args.get('plan_id', '')
        compact = request.args.get('compact', 'false').lower() == 'true'
        
        if not plan_id:
            return jsonify({'success': False, 'error': 'Plan ID is required'}), 400
        
        plan = plan_presenter.get_plan(plan_id)
        
        if not plan:
            return jsonify({'success': False, 'error': 'Plan not found'}), 404
        
        if compact:
            formatted = plan_presenter.format_plan_compact(plan)
        else:
            formatted = plan_presenter.format_plan_visual(plan)
        
        return jsonify({
            'success': True,
            'formatted': formatted,
            'plan': plan.to_dict()
        })
    except Exception as e:
        logger.error(f"Plan format error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-plan/confirm', methods=['POST'])
def ai_plan_confirm():
    """Confirm execution plan (34.4 PlanPresenter)"""
    try:
        from BUNK3R_IA.core.plan_presenter import plan_presenter
        
        data = request.json
        plan_id = data.get('plan_id', '')
        
        if not plan_id:
            return jsonify({'success': False, 'error': 'Plan ID is required'}), 400
        
        success, message = plan_presenter.confirm_plan(plan_id)
        
        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        logger.error(f"Plan confirm error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-plan/modify', methods=['POST'])
def ai_plan_modify():
    """Modify execution plan (34.4 PlanPresenter)"""
    try:
        from BUNK3R_IA.core.plan_presenter import plan_presenter
        
        data = request.json
        plan_id = data.get('plan_id', '')
        modification = data.get('modification', '')
        
        if not plan_id or not modification:
            return jsonify({'success': False, 'error': 'Plan ID and modification are required'}), 400
        
        success, plan = plan_presenter.modify_plan(plan_id, modification)
        
        if success and plan:
            return jsonify({
                'success': True,
                **plan.to_dict()
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to modify plan'}), 400
    except Exception as e:
        logger.error(f"Plan modify error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-plan/progress', methods=['GET'])
def ai_plan_progress():
    """Get plan execution progress (34.4 PlanPresenter)"""
    try:
        from BUNK3R_IA.core.plan_presenter import plan_presenter
        
        plan_id = request.args.get('plan_id', '')
        
        if not plan_id:
            return jsonify({'success': False, 'error': 'Plan ID is required'}), 400
        
        progress = plan_presenter.get_progress(plan_id)
        
        return jsonify({
            'success': True,
            **progress
        })
    except Exception as e:
        logger.error(f"Plan progress error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-retry/stats', methods=['GET'])
def ai_retry_stats():
    """Get retry system statistics (34.17 SmartRetrySystem)"""
    try:
        from BUNK3R_IA.core.smart_retry import smart_retry
        
        stats = smart_retry.get_failure_stats()
        
        return jsonify({
            'success': True,
            **stats
        })
    except Exception as e:
        logger.error(f"Retry stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-retry/reset', methods=['POST'])
def ai_retry_reset():
    """Reset retry system scores (34.17 SmartRetrySystem)"""
    try:
        from BUNK3R_IA.core.smart_retry import smart_retry
        
        data = request.json or {}
        reset_logs = data.get('reset_logs', False)
        
        smart_retry.reset_provider_scores()
        
        if reset_logs:
            smart_retry.clear_failure_log()
        
        return jsonify({
            'success': True,
            'message': 'Retry scores reset successfully'
        })
    except Exception as e:
        logger.error(f"Retry reset error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-validator/validate', methods=['POST'])
def ai_validator_validate():
    """Validate action before execution (34.19 PreExecutionValidator)"""
    try:
        from BUNK3R_IA.core.pre_execution_validator import pre_execution_validator, ActionType
        
        data = request.json
        action_type = data.get('action_type', '')
        action_data = data.get('data', {})
        
        if not action_type:
            return jsonify({'success': False, 'error': 'Action type is required'}), 400
        
        try:
            action = ActionType(action_type)
        except ValueError:
            return jsonify({'success': False, 'error': f'Invalid action type: {action_type}'}), 400
        
        result = pre_execution_validator.validate_action(action, action_data)
        
        return jsonify({
            'success': True,
            **result.to_dict()
        })
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-validator/batch', methods=['POST'])
def ai_validator_batch():
    """Validate batch of actions (34.19 PreExecutionValidator)"""
    try:
        from BUNK3R_IA.core.pre_execution_validator import pre_execution_validator, ActionType
        
        data = request.json
        actions = data.get('actions', [])
        
        if not actions:
            return jsonify({'success': False, 'error': 'Actions list is required'}), 400
        
        action_tuples = []
        for action in actions:
            try:
                action_type = ActionType(action.get('type', ''))
                action_data = action.get('data', {})
                action_tuples.append((action_type, action_data))
            except ValueError:
                continue
        
        result = pre_execution_validator.validate_batch(action_tuples)
        
        return jsonify({
            'success': True,
            **result.to_dict()
        })
    except Exception as e:
        logger.error(f"Batch validation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-validator/dependencies', methods=['POST'])
def ai_validator_dependencies():
    """Check code dependencies (34.19 PreExecutionValidator)"""
    try:
        from BUNK3R_IA.core.pre_execution_validator import pre_execution_validator
        
        data = request.json
        code = data.get('code', '')
        language = data.get('language', 'python')
        
        if not code:
            return jsonify({'success': False, 'error': 'Code is required'}), 400
        
        issues = pre_execution_validator.check_dependencies(code, language)
        
        return jsonify({
            'success': True,
            'issues': [i.to_dict() for i in issues],
            'count': len(issues)
        })
    except Exception as e:
        logger.error(f"Dependency check error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-constructor/generate', methods=['POST'])
def ai_constructor_generate():
    """Generate project with AI and return preview URL (Section 35)"""
    try:
        from BUNK3R_IA.core.live_preview import live_preview
        
        data = request.json
        prompt = data.get('prompt', '').strip()
        session_id = data.get('session_id')
        
        if not prompt:
            return jsonify({'success': False, 'error': 'Prompt is required'}), 400
        
        result = live_preview.generate_with_fallback(prompt, session_id)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI Constructor generate error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-constructor/projects', methods=['GET'])
def ai_constructor_list_projects():
    """List all generated projects (Section 35)"""
    try:
        from BUNK3R_IA.core.live_preview import live_preview
        
        projects = live_preview.list_projects()
        
        return jsonify({
            'success': True,
            'projects': projects,
            'count': len(projects)
        })
    except Exception as e:
        logger.error(f"List projects error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-constructor/projects/<session_id>', methods=['DELETE'])
def ai_constructor_delete_project(session_id):
    """Delete a generated project (Section 35)"""
    try:
        from BUNK3R_IA.core.live_preview import live_preview
        
        result = live_preview.delete_project(session_id)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Delete project error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# LLM Phase Integrator Routes (34.7)
# ============================================

@ai_bp.route('/ai-llm/phase', methods=['POST'])
def ai_llm_execute_phase():
    """Execute a specific phase of the constructor with LLM (34.7)"""
    try:
        from BUNK3R_IA.core.llm_phase_integrator import llm_integrator, ConstructorPhase
        
        data = request.json
        phase_num = data.get('phase', 1)
        input_data = data.get('input_data', {})
        user_id = data.get('user_id', 'anonymous')
        
        try:
            phase = ConstructorPhase(phase_num)
        except ValueError:
            return jsonify({'success': False, 'error': f'Invalid phase: {phase_num}'}), 400
        
        result = llm_integrator.execute_phase(phase, input_data, user_id)
        
        return jsonify({
            'success': True,
            **result.to_dict()
        })
    except Exception as e:
        logger.error(f"LLM phase execution error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-llm/pipeline', methods=['POST'])
def ai_llm_run_pipeline():
    """Run the full 8-phase pipeline with LLM (34.7)"""
    try:
        from BUNK3R_IA.core.llm_phase_integrator import llm_integrator
        
        data = request.json
        user_request = data.get('request', '').strip()
        user_id = data.get('user_id', 'anonymous')
        skip_clarification = data.get('skip_clarification', False)
        
        if not user_request:
            return jsonify({'success': False, 'error': 'Request is required'}), 400
        
        results = llm_integrator.run_full_pipeline(
            user_request, 
            user_id, 
            skip_clarification
        )
        
        serialized = {}
        for key, value in results.items():
            if hasattr(value, 'to_dict'):
                serialized[key] = value.to_dict()
            else:
                serialized[key] = value
        
        return jsonify({
            'success': True,
            'results': serialized
        })
    except Exception as e:
        logger.error(f"LLM pipeline error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-llm/execute-plan', methods=['POST'])
def ai_llm_execute_plan():
    """Execute an approved plan (phases 6-8) with LLM (34.7)"""
    try:
        from BUNK3R_IA.core.llm_phase_integrator import llm_integrator
        
        data = request.json
        plan_data = data.get('plan', {})
        original_request = data.get('original_request', '')
        user_id = data.get('user_id', 'anonymous')
        
        if not plan_data:
            return jsonify({'success': False, 'error': 'Plan data is required'}), 400
        
        result = llm_integrator.execute_plan(plan_data, original_request, user_id)
        
        return jsonify({
            'success': True,
            **result
        })
    except Exception as e:
        logger.error(f"LLM execute plan error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-llm/phases', methods=['GET'])
def ai_llm_list_phases():
    """List all available phases (34.7)"""
    try:
        from BUNK3R_IA.core.llm_phase_integrator import ConstructorPhase
        
        phases = [
            {
                'number': phase.value,
                'name': phase.name,
                'description': {
                    1: 'Análisis de Intención - Detecta qué quiere el usuario',
                    2: 'Investigación - Busca mejores prácticas y patrones',
                    3: 'Clarificación - Genera preguntas si hay ambigüedad',
                    4: 'Construcción de Prompt - Crea el prompt maestro',
                    5: 'Presentación de Plan - Genera plan de ejecución',
                    6: 'Ejecución - Genera el código',
                    7: 'Verificación - Valida el código generado',
                    8: 'Entrega - Prepara el resultado final'
                }.get(phase.value, '')
            }
            for phase in ConstructorPhase
        ]
        
        return jsonify({
            'success': True,
            'phases': phases,
            'count': len(phases)
        })
    except Exception as e:
        logger.error(f"List phases error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai/chat/stream', methods=['GET'])
def ai_chat_stream():
    """
    Stream chat responses using Server-Sent Events (SSE)
    Implements 34.15 - Sistema de streaming de respuestas
    
    Query params:
        - user_id: User identifier
        - message: The message to send
        - provider: Preferred AI provider (optional)
    """
    from flask import Response, stream_with_context
    
    try:
        from BUNK3R_IA.core.streaming_service import get_streaming_service
        
        user_id = request.args.get('user_id', 'anonymous')
        message = request.args.get('message', '').strip()
        preferred_provider = request.args.get('provider')
        
        if not message:
            def error_stream():
                yield 'data: {"type": "error", "data": "Message is required"}\n\n'
            return Response(
                stream_with_context(error_stream()),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'X-Accel-Buffering': 'no',
                    'Access-Control-Allow-Origin': '*'
                }
            )
        
        streaming_service = get_streaming_service()
        
        def generate():
            try:
                for event in streaming_service.stream_chat(
                    user_id=user_id,
                    message=message,
                    preferred_provider=preferred_provider
                ):
                    yield event.to_sse()
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield f'data: {{"type": "error", "data": "{str(e)}"}}\n\n'
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no',
                'Access-Control-Allow-Origin': '*'
            }
        )
        
    except Exception as e:
        logger.error(f"Stream init error: {e}")
        def error_stream():
            yield f'data: {{"type": "error", "data": "{str(e)}"}}\n\n'
        return Response(
            stream_with_context(error_stream()),
            mimetype='text/event-stream'
        )


@ai_bp.route('/ai/chat/stream', methods=['POST'])
def ai_chat_stream_post():
    """
    Stream chat responses using Server-Sent Events (SSE) - POST version
    Implements 34.15 - Sistema de streaming de respuestas
    """
    from flask import Response, stream_with_context
    
    try:
        from BUNK3R_IA.core.streaming_service import get_streaming_service
        
        data = request.json or {}
        user_id = data.get('user_id', 'anonymous')
        message = data.get('message', '').strip()
        preferred_provider = data.get('provider')
        system_prompt = data.get('system_prompt')
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        streaming_service = get_streaming_service()
        
        def generate():
            try:
                for event in streaming_service.stream_chat(
                    user_id=user_id,
                    message=message,
                    system_prompt=system_prompt,
                    preferred_provider=preferred_provider
                ):
                    yield event.to_sse()
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield f'data: {{"type": "error", "data": "{str(e)}"}}\n\n'
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no',
                'Access-Control-Allow-Origin': '*'
            }
        )
        
    except Exception as e:
        logger.error(f"Stream POST init error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai/streaming/providers', methods=['GET'])
def ai_streaming_providers():
    """Get list of available streaming providers (34.15)"""
    try:
        from BUNK3R_IA.core.streaming_service import get_streaming_service
        
        service = get_streaming_service()
        providers = service.get_available_providers()
        
        return jsonify({
            'success': True,
            'providers': providers,
            'count': len(providers),
            'streaming_enabled': len(providers) > 0
        })
    except Exception as e:
        logger.error(f"Streaming providers error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai/streaming/clear', methods=['POST'])
def ai_streaming_clear():
    """Clear streaming conversation history (34.15)"""
    try:
        from BUNK3R_IA.core.streaming_service import get_streaming_service
        
        data = request.json or {}
        user_id = data.get('user_id', 'anonymous')
        
        service = get_streaming_service()
        service.clear_conversation(user_id)
        
        return jsonify({
            'success': True,
            'message': 'Conversation cleared'
        })
    except Exception as e:
        logger.error(f"Streaming clear error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-search/query', methods=['POST'])
def ai_search_query():
    """Realizar búsqueda web (34.A.1)"""
    try:
        from BUNK3R_IA.core.web_search_service import web_search_service, SearchType, ContentFilter
        
        data = request.json or {}
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'success': False, 'error': 'Query is required'}), 400
        
        search_type_str = data.get('search_type', 'search')
        search_type = SearchType(search_type_str) if search_type_str in [st.value for st in SearchType] else SearchType.GENERAL
        
        filter_strs = data.get('filters', ['all'])
        filters = []
        for f in filter_strs:
            try:
                filters.append(ContentFilter(f))
            except ValueError:
                filters.append(ContentFilter.ALL)
        
        num_results = min(data.get('num_results', 10), 100)
        use_cache = data.get('use_cache', True)
        
        response = web_search_service.search_sync(
            query=query,
            search_type=search_type,
            filters=filters,
            num_results=num_results,
            use_cache=use_cache
        )
        
        return jsonify({
            'success': True,
            **response.to_dict()
        })
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-search/code-examples', methods=['POST'])
def ai_search_code_examples():
    """Buscar ejemplos de código (34.A.1)"""
    try:
        from BUNK3R_IA.core.web_search_service import web_search_service, ContentFilter
        
        data = request.json or {}
        technology = data.get('technology', '').strip()
        task = data.get('task', '').strip()
        language = data.get('language', 'python')
        
        if not technology or not task:
            return jsonify({'success': False, 'error': 'Technology and task are required'}), 400
        
        query = f"{technology} {task} {language} example code"
        response = web_search_service.search_sync(
            query=query,
            filters=[ContentFilter.GITHUB, ContentFilter.STACKOVERFLOW]
        )
        
        return jsonify({
            'success': True,
            **response.to_dict()
        })
    except Exception as e:
        logger.error(f"Code examples search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-search/documentation', methods=['POST'])
def ai_search_documentation():
    """Buscar documentación (34.A.1)"""
    try:
        from BUNK3R_IA.core.web_search_service import web_search_service, ContentFilter
        
        data = request.json or {}
        library = data.get('library', '').strip()
        topic = data.get('topic', '').strip()
        
        if not library:
            return jsonify({'success': False, 'error': 'Library is required'}), 400
        
        query = f"{library} {topic} documentation"
        response = web_search_service.search_sync(
            query=query,
            filters=[ContentFilter.DOCUMENTATION, ContentFilter.OFFICIAL]
        )
        
        return jsonify({
            'success': True,
            **response.to_dict()
        })
    except Exception as e:
        logger.error(f"Documentation search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-search/error-solution', methods=['POST'])
def ai_search_error_solution():
    """Buscar solución para errores (34.A.1)"""
    try:
        from BUNK3R_IA.core.web_search_service import web_search_service, ContentFilter
        
        data = request.json or {}
        error_message = data.get('error_message', '').strip()
        technology = data.get('technology', '')
        
        if not error_message:
            return jsonify({'success': False, 'error': 'Error message is required'}), 400
        
        error_clean = error_message[:200]
        query = f"{technology} {error_clean}"
        response = web_search_service.search_sync(
            query=query,
            filters=[ContentFilter.STACKOVERFLOW]
        )
        
        return jsonify({
            'success': True,
            **response.to_dict()
        })
    except Exception as e:
        logger.error(f"Error solution search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-search/stats', methods=['GET'])
def ai_search_stats():
    """Obtener estadísticas del servicio de búsqueda (34.A.1)"""
    try:
        from BUNK3R_IA.core.web_search_service import web_search_service
        
        stats = web_search_service.get_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Search stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai-search/cache/clear', methods=['POST'])
def ai_search_cache_clear():
    """Limpiar cache de búsquedas (34.A.1)"""
    try:
        from BUNK3R_IA.core.web_search_service import web_search_service
        
        web_search_service.clear_cache()
        
        return jsonify({
            'success': True,
            'message': 'Search cache cleared'
        })
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
