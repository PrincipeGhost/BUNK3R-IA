from tracking.ai_service import get_ai_service
from tracking.ai_constructor import AIConstructorService

ai_constructor_service = None

def get_ai_constructor():
    """Get or create AI Constructor Service instance"""
    global ai_constructor_service
    if ai_constructor_service is None:
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

@app.route('/api/ai/chat', methods=['POST'])
@require_telegram_auth
def ai_chat():
    """Send message to AI and get response"""
    try:
        user_id = str(request.telegram_user.get('id'))
        data = request.json
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        ai = get_ai_service(db_manager)
        result = ai.chat(user_id, message)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        return jsonify({'success': False, 'error': 'Error processing message'}), 500

@app.route('/api/ai/history', methods=['GET'])
@require_telegram_auth
def ai_history():
    """Get AI chat history"""
    try:
        user_id = str(request.telegram_user.get('id'))
        ai = get_ai_service(db_manager)
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

@app.route('/api/ai/clear', methods=['POST'])
@require_telegram_auth
def ai_clear():
    """Clear AI chat history"""
    try:
        user_id = str(request.telegram_user.get('id'))
        ai = get_ai_service(db_manager)
        ai.clear_conversation(user_id)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"AI clear error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== CODE BUILDER API ====================

@app.route('/api/ai/code-builder', methods=['POST'])
@require_telegram_auth
def ai_code_builder():
    """AI-powered code generation for web projects"""
    try:
        user_id = str(request.telegram_user.get('id'))
        data = request.json
        message = data.get('message', '').strip()
        current_files = data.get('currentFiles', {})
        project_name = data.get('projectName', 'Mi Proyecto')
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        ai = get_ai_service(db_manager)
        result = ai.generate_code(user_id, message, current_files, project_name)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI code builder error: {e}")
        return jsonify({'success': False, 'error': 'Error generating code'}), 500

@app.route('/api/code-builder/projects', methods=['GET'])
@require_telegram_auth
def get_code_projects():
    """Get user's saved code projects"""
    try:
        user_id = str(request.telegram_user.get('id'))
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, name, files, created_at, updated_at
                    FROM code_builder_projects
                    WHERE user_id = %s
                    ORDER BY updated_at DESC
                    LIMIT 20
                """, (user_id,))
                projects = cur.fetchall()
                
        return jsonify({'success': True, 'projects': projects})
    except Exception as e:
        logger.error(f"Error getting projects: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/code-builder/projects', methods=['POST'])
@require_telegram_auth
def save_code_project():
    """Save a code project"""
    try:
        user_id = str(request.telegram_user.get('id'))
        data = request.json
        project_id = data.get('projectId')
        name = data.get('name', 'Mi Proyecto')
        files = data.get('files', {})
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                if project_id:
                    cur.execute("""
                        UPDATE code_builder_projects
                        SET name = %s, files = %s, updated_at = NOW()
                        WHERE id = %s AND user_id = %s
                        RETURNING id
                    """, (name, json.dumps(files), project_id, user_id))
                    result = cur.fetchone()
                    if not result:
                        project_id = None
                
                if not project_id:
                    cur.execute("""
                        INSERT INTO code_builder_projects (user_id, name, files, created_at, updated_at)
                        VALUES (%s, %s, %s, NOW(), NOW())
                        RETURNING id
                    """, (user_id, name, json.dumps(files)))
                    project_id = cur.fetchone()[0]
                
                conn.commit()
        
        return jsonify({'success': True, 'projectId': project_id})
    except Exception as e:
        logger.error(f"Error saving project: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/code-builder/projects/<project_id>', methods=['DELETE'])
@require_telegram_auth
def delete_code_project(project_id):
    """Delete a code project"""
    try:
        user_id = str(request.telegram_user.get('id'))
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM code_builder_projects
                    WHERE id = %s AND user_id = %s
                """, (project_id, user_id))
                conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== END CODE BUILDER SECTION ====================


# ==================== AI CONSTRUCTOR SECTION ====================

@app.route('/api/ai-constructor/process', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_constructor_process():
    """Process message through AI Constructor's 8-phase architecture (OWNER ONLY)"""
    try:
        user_id = str(request.telegram_user.get('id'))
        data = request.json
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

@app.route('/api/ai-constructor/session', methods=['GET'])
@require_telegram_auth
@require_owner
def ai_constructor_session():
    """Get current AI Constructor session status (OWNER ONLY)"""
    try:
        user_id = str(request.telegram_user.get('id'))
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

@app.route('/api/ai-constructor/reset', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_constructor_reset():
    """Reset AI Constructor session (OWNER ONLY)"""
    try:
        user_id = str(request.telegram_user.get('id'))
        constructor = get_ai_constructor()
        constructor.reset_session(user_id)
        
        return jsonify({'success': True, 'message': 'Session reset successfully'})
    except ValueError as e:
        return jsonify({'success': False, 'error': sanitize_error(e, 'ai_constructor_reset')}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': sanitize_error(e, 'ai_constructor_reset')}), 500

@app.route('/api/ai-constructor/files', methods=['GET'])
@require_telegram_auth
@require_owner
def ai_constructor_files():
    """Get files generated by AI Constructor"""
    try:
        user_id = str(request.telegram_user.get('id'))
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

@app.route('/api/ai-constructor/confirm', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_constructor_confirm():
    """Confirm plan and continue execution"""
    try:
        user_id = str(request.telegram_user.get('id'))
        data = request.json
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

@app.route('/api/ai-constructor/flow', methods=['GET'])
@require_telegram_auth
@require_owner
def ai_constructor_flow():
    """Get AI Constructor flow log for debugging"""
    try:
        from tracking.ai_flow_logger import flow_logger
        user_id = str(request.telegram_user.get('id'))
        
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

@app.route('/api/ai-constructor/flow/all', methods=['GET'])
@require_telegram_auth
@require_owner
def ai_constructor_flow_all():
    """Get all AI Constructor sessions summary (OWNER ONLY)"""
    try:
        from tracking.ai_flow_logger import flow_logger
        
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

@app.route('/api/ai-constructor/flow/clear', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_constructor_flow_clear():
    """Clear flow logs (OWNER ONLY)"""
    try:
        from tracking.ai_flow_logger import flow_logger
        user_id = str(request.telegram_user.get('id'))
        
        data = request.json or {}
        clear_all = data.get('clear_all', False)
        
        if clear_all:
            flow_logger.clear_all()
            return jsonify({'success': True, 'message': 'All flow logs cleared'})
        else:
            flow_logger.clear_session(user_id)
            return jsonify({'success': True, 'message': f'Flow log cleared for user {user_id}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== AI CONSTRUCTOR DOWNLOAD ZIP ====================

@app.route('/api/ai-constructor/download-zip', methods=['GET'])
@require_telegram_auth
@require_owner
def ai_constructor_download_zip():
    """Download generated project as ZIP file (OWNER ONLY)"""
    import zipfile
    import io
    from flask import send_file
    
    try:
        user_id = str(request.telegram_user.get('id'))
        
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

@app.route('/api/ai-constructor/download-disk-zip', methods=['GET'])
@require_telegram_auth
@require_owner
def ai_constructor_download_disk_zip():
    """Download ai_generated folder as ZIP file (OWNER ONLY)"""
    import zipfile
    import io
    from flask import send_file
    
    try:
        ai_generated_path = os.path.join(os.getcwd(), 'ai_generated')
        
        if not os.path.exists(ai_generated_path):
            return jsonify({'success': False, 'error': 'No hay archivos generados en disco'}), 404
        
        memory_file = io.BytesIO()
        
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(ai_generated_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
                
                for file in files:
                    if file.startswith('.'):
                        continue
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, ai_generated_path)
                    zf.write(file_path, arcname)
        
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
        logger.error(f"Error creating disk ZIP: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== END AI CONSTRUCTOR SECTION ====================


# ==================== AI TOOLKIT SECTION ====================

@app.route('/api/ai-toolkit/files/read', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_toolkit_read_file():
    """Read file content using AI Toolkit (OWNER ONLY)"""
    try:
        from tracking.ai_toolkit import AIFileToolkit
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

@app.route('/api/ai-toolkit/files/write', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_toolkit_write_file():
    """Write file content using AI Toolkit (OWNER ONLY)"""
    try:
        from tracking.ai_toolkit import AIFileToolkit
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

@app.route('/api/ai-toolkit/files/edit', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_toolkit_edit_file():
    """Edit file by replacing content using AI Toolkit (OWNER ONLY)"""
    try:
        from tracking.ai_toolkit import AIFileToolkit
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

@app.route('/api/ai-toolkit/files/delete', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_toolkit_delete_file():
    """Delete file using AI Toolkit (OWNER ONLY) - Requires explicit confirmation"""
    try:
        from tracking.ai_toolkit import AIFileToolkit
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

@app.route('/api/ai-toolkit/files/list', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_toolkit_list_directory():
    """List directory contents using AI Toolkit (OWNER ONLY)"""
    try:
        from tracking.ai_toolkit import AIFileToolkit
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

@app.route('/api/ai-toolkit/files/search', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_toolkit_search_code():
    """Search code using AI Toolkit (OWNER ONLY)"""
    try:
        from tracking.ai_toolkit import AIFileToolkit
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

@app.route('/api/ai-toolkit/command/run', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_toolkit_run_command():
    """Execute command using AI Toolkit (OWNER ONLY)"""
    try:
        from tracking.ai_toolkit import AICommandExecutor
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

@app.route('/api/ai-toolkit/command/install', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_toolkit_install_package():
    """Install package using AI Toolkit (OWNER ONLY)"""
    try:
        from tracking.ai_toolkit import AICommandExecutor
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

@app.route('/api/ai-toolkit/command/script', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_toolkit_run_script():
    """Run a script file using AI Toolkit (OWNER ONLY)"""
    try:
        from tracking.ai_toolkit import AICommandExecutor
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

@app.route('/api/ai-toolkit/errors/detect', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_toolkit_detect_errors():
    """Detect errors in logs using AI Toolkit (OWNER ONLY)"""
    try:
        from tracking.ai_toolkit import AIErrorDetector
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

@app.route('/api/ai-toolkit/errors/analyze', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_toolkit_analyze_error():
    """Analyze error and suggest fix using AI Toolkit (OWNER ONLY)"""
    try:
        from tracking.ai_toolkit import AIErrorDetector
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

@app.route('/api/ai-toolkit/project/analyze', methods=['GET'])
@require_telegram_auth
@require_owner
def ai_toolkit_analyze_project():
    """Analyze project structure using AI Toolkit (OWNER ONLY)"""
    try:
        from tracking.ai_toolkit import AIProjectAnalyzer
        
        analyzer = AIProjectAnalyzer()
        result = analyzer.analyze_project()
        
        if result['success']:
            result['context'] = analyzer.generate_context()
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI Toolkit project analysis: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== AI WEB SEARCH SECTION (Phase 34.A.1) ====================

@app.route('/api/ai-toolkit/search/web', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_toolkit_web_search():
    """
    Perform web search using Serper API (OWNER ONLY).
    
    FASE 34.A.1 - Búsqueda en Vivo
    
    Request body:
    {
        "query": "flask authentication tutorial",
        "filter": "docs|tutorials|stackoverflow|github|npm|pypi" (optional),
        "num_results": 5 (optional, max 10),
        "use_cache": true (optional)
    }
    """
    try:
        from tracking.ai_toolkit import AIWebSearch
        
        data = request.json or {}
        query = data.get('query', '')
        filter_type = data.get('filter')
        num_results = data.get('num_results', 5)
        use_cache = data.get('use_cache', True)
        
        if not query:
            return jsonify({'success': False, 'error': 'Query is required'}), 400
        
        searcher = AIWebSearch()
        
        if not searcher.is_configured:
            return jsonify({
                'success': False,
                'error': 'Serper API key not configured. Add SERPER_API_KEY to environment variables.',
                'results': []
            }), 503
        
        result = searcher.search(query, filter_type, num_results, use_cache)
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI Web Search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-toolkit/search/documentation', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_toolkit_search_documentation():
    """Search for documentation on a topic (OWNER ONLY)"""
    try:
        from tracking.ai_toolkit import AIWebSearch
        
        data = request.json or {}
        topic = data.get('topic', '')
        language = data.get('language', 'python')
        
        if not topic:
            return jsonify({'success': False, 'error': 'Topic is required'}), 400
        
        searcher = AIWebSearch()
        result = searcher.search_documentation(topic, language)
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI Documentation Search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-toolkit/search/tutorial', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_toolkit_search_tutorial():
    """Search for tutorials on a topic (OWNER ONLY)"""
    try:
        from tracking.ai_toolkit import AIWebSearch
        
        data = request.json or {}
        topic = data.get('topic', '')
        
        if not topic:
            return jsonify({'success': False, 'error': 'Topic is required'}), 400
        
        searcher = AIWebSearch()
        result = searcher.search_tutorial(topic)
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI Tutorial Search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-toolkit/search/stackoverflow', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_toolkit_search_stackoverflow():
    """Search Stack Overflow for answers (OWNER ONLY)"""
    try:
        from tracking.ai_toolkit import AIWebSearch
        
        data = request.json or {}
        question = data.get('question', '')
        
        if not question:
            return jsonify({'success': False, 'error': 'Question is required'}), 400
        
        searcher = AIWebSearch()
        result = searcher.search_stackoverflow(question)
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI StackOverflow Search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-toolkit/search/github', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_toolkit_search_github():
    """Search GitHub for code examples (OWNER ONLY)"""
    try:
        from tracking.ai_toolkit import AIWebSearch
        
        data = request.json or {}
        topic = data.get('topic', '')
        language = data.get('language', 'python')
        
        if not topic:
            return jsonify({'success': False, 'error': 'Topic is required'}), 400
        
        searcher = AIWebSearch()
        result = searcher.search_github_examples(topic, language)
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI GitHub Search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-toolkit/search/package', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_toolkit_search_package():
    """Search for package information (OWNER ONLY)"""
    try:
        from tracking.ai_toolkit import AIWebSearch
        
        data = request.json or {}
        package_name = data.get('package_name', '')
        registry = data.get('registry', 'pypi')
        
        if not package_name:
            return jsonify({'success': False, 'error': 'Package name is required'}), 400
        
        searcher = AIWebSearch()
        result = searcher.search_package(package_name, registry)
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI Package Search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-toolkit/search/cache', methods=['GET'])
@require_telegram_auth
@require_owner
def ai_toolkit_search_cache_stats():
    """Get web search cache statistics (OWNER ONLY)"""
    try:
        from tracking.ai_toolkit import AIWebSearch
        
        searcher = AIWebSearch()
        stats = searcher.get_cache_stats()
        stats['is_configured'] = searcher.is_configured
        
        return jsonify({'success': True, **stats})
    except Exception as e:
        logger.error(f"AI Search Cache Stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-toolkit/search/cache/clear', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_toolkit_search_cache_clear():
    """Clear web search cache (OWNER ONLY)"""
    try:
        from tracking.ai_toolkit import AIWebSearch
        
        searcher = AIWebSearch()
        searcher.clear_cache()
        
        return jsonify({'success': True, 'message': 'Search cache cleared'})
    except Exception as e:
        logger.error(f"AI Search Cache Clear error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== AI SCRAPER API (Phase 34.A.3) ====================

@app.route('/api/ai-toolkit/scraper/fetch', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_toolkit_scraper_fetch():
    """
    Scrape any URL using ScraperAPI with anti-bot bypass (OWNER ONLY).
    
    FASE 34.A.3 - Web Scraping Avanzado
    
    Request body:
    {
        "url": "https://example.com/page",
        "render_js": false (optional - enables JavaScript rendering),
        "country_code": "us" (optional - geolocation),
        "premium": false (optional - premium proxies),
        "use_cache": true (optional)
    }
    """
    try:
        from tracking.ai_toolkit import AIScraperAPI
        
        data = request.json or {}
        url = data.get('url', '')
        render_js = data.get('render_js', False)
        country_code = data.get('country_code')
        premium = data.get('premium', False)
        use_cache = data.get('use_cache', True)
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400
        
        scraper = AIScraperAPI()
        
        if not scraper.is_configured:
            return jsonify({
                'success': False,
                'error': 'ScraperAPI key not configured. Add SCRAPERAPI_KEY to environment variables.',
                'content': ''
            }), 503
        
        result = scraper.scrape(url, render_js, country_code, premium, use_cache=use_cache)
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI ScraperAPI fetch error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-toolkit/scraper/structured', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_toolkit_scraper_structured():
    """Scrape URL and return structured data (OWNER ONLY)"""
    try:
        from tracking.ai_toolkit import AIScraperAPI
        
        data = request.json or {}
        url = data.get('url', '')
        render_js = data.get('render_js', True)
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400
        
        scraper = AIScraperAPI()
        
        if not scraper.is_configured:
            return jsonify({
                'success': False,
                'error': 'ScraperAPI key not configured. Add SCRAPERAPI_KEY to environment variables.',
                'content': ''
            }), 503
        
        result = scraper.scrape_structured(url, render_js)
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI ScraperAPI structured error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-toolkit/scraper/ai-format', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_toolkit_scraper_ai_format():
    """Scrape URL and format for AI consumption (OWNER ONLY)"""
    try:
        from tracking.ai_toolkit import AIScraperAPI
        
        data = request.json or {}
        url = data.get('url', '')
        max_tokens = data.get('max_tokens', 4000)
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400
        
        scraper = AIScraperAPI()
        
        if not scraper.is_configured:
            return jsonify({
                'success': False,
                'error': 'ScraperAPI key not configured. Add SCRAPERAPI_KEY to environment variables.',
                'content': ''
            }), 503
        
        result = scraper.scrape_for_ai(url, max_tokens)
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI ScraperAPI AI format error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-toolkit/scraper/stats', methods=['GET'])
@require_telegram_auth
@require_owner
def ai_toolkit_scraper_stats():
    """Get ScraperAPI statistics (OWNER ONLY)"""
    try:
        from tracking.ai_toolkit import AIScraperAPI
        
        scraper = AIScraperAPI()
        stats = scraper.get_stats()
        
        return jsonify({'success': True, **stats})
    except Exception as e:
        logger.error(f"AI ScraperAPI stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-toolkit/scraper/cache/clear', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_toolkit_scraper_cache_clear():
    """Clear ScraperAPI cache (OWNER ONLY)"""
    try:
        from tracking.ai_toolkit import AIScraperAPI
        
        scraper = AIScraperAPI()
        scraper.clear_cache()
        
        return jsonify({'success': True, 'message': 'ScraperAPI cache cleared'})
    except Exception as e:
        logger.error(f"AI ScraperAPI cache clear error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== AI DOCUMENTATION SCRAPER (Phase 34.A.2) ====================

@app.route('/api/ai-toolkit/docs/fetch', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_toolkit_fetch_documentation():
    """
    Fetch and parse documentation from allowed domains (OWNER ONLY).
    
    FASE 34.A.2 - Web Scraping para documentación
    
    Request body:
    {
        "url": "https://docs.python.org/3/library/..."
    }
    
    Allowed domains: docs.python.org, flask.palletsprojects.com, developer.mozilla.org, 
                     reactjs.org, vuejs.org, nodejs.org, docs.djangoproject.com, 
                     fastapi.tiangolo.com, expressjs.com, tailwindcss.com, getbootstrap.com
    """
    try:
        from tracking.ai_toolkit import AIDocumentationScraper
        
        data = request.json or {}
        url = data.get('url', '')
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400
        
        scraper = AIDocumentationScraper()
        result = scraper.fetch_documentation(url)
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI Documentation Fetch error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== END AI TOOLKIT SECTION ====================


# ==================== AI CORE ENGINE SECTION (Phases 34.16-34.23) ====================

@app.route('/api/ai-core/process', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_core_process_message():
    """Process user message and determine workflow (OWNER ONLY)"""
    try:
        from tracking.ai_core_engine import AICoreOrchestrator
        
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

@app.route('/api/ai-core/intent/classify', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_core_classify_intent():
    """Classify user intent from message (OWNER ONLY)"""
    try:
        from tracking.ai_core_engine import AIDecisionEngine
        
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

@app.route('/api/ai-core/workflow/decide', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_core_decide_workflow():
    """Decide workflow based on intent (OWNER ONLY)"""
    try:
        from tracking.ai_core_engine import AIDecisionEngine, IntentType, Intent
        
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

@app.route('/api/ai-core/validate', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_core_validate_action():
    """Validate action before execution (OWNER ONLY)"""
    try:
        from tracking.ai_core_engine import PreExecutionValidator
        
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

@app.route('/api/ai-core/checkpoint/create', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_core_create_checkpoint():
    """Create a checkpoint before making changes (OWNER ONLY)"""
    try:
        from tracking.ai_core_engine import RollbackManager
        
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

@app.route('/api/ai-core/checkpoint/rollback', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_core_rollback_checkpoint():
    """Rollback to a checkpoint (OWNER ONLY)"""
    try:
        from tracking.ai_core_engine import RollbackManager
        
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

@app.route('/api/ai-core/checkpoint/list', methods=['GET'])
@require_telegram_auth
@require_owner
def ai_core_list_checkpoints():
    """List available checkpoints (OWNER ONLY)"""
    try:
        from tracking.ai_core_engine import RollbackManager
        
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

@app.route('/api/ai-core/impact/analyze', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_core_analyze_impact():
    """Analyze impact of changing a file (OWNER ONLY)"""
    try:
        from tracking.ai_core_engine import ChangeImpactAnalyzer
        
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

@app.route('/api/ai-core/workflow/status', methods=['GET'])
@require_telegram_auth
@require_owner
def ai_core_workflow_status():
    """Get workflow/server status (OWNER ONLY)"""
    try:
        from tracking.ai_core_engine import WorkflowManager
        
        name = request.args.get('name', 'main')
        
        manager = WorkflowManager()
        status = manager.get_workflow_status(name)
        
        return jsonify({'success': True, **status})
    except Exception as e:
        logger.error(f"AI Core workflow status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-core/workflow/health', methods=['GET'])
@require_telegram_auth
@require_owner
def ai_core_workflow_health():
    """Check server health (OWNER ONLY)"""
    try:
        from tracking.ai_core_engine import WorkflowManager
        
        port = request.args.get('port', 5000, type=int)
        path = request.args.get('path', '/')
        
        manager = WorkflowManager()
        health = manager.check_server_health(port, path)
        
        return jsonify({'success': True, **health})
    except Exception as e:
        logger.error(f"AI Core workflow health: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-core/tasks/create', methods=['POST'])
@require_telegram_auth
@require_owner
def ai_core_create_tasks():
    """Create a task list (OWNER ONLY)"""
    try:
        from tracking.ai_core_engine import TaskManager
        
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

@app.route('/api/ai-core/tasks/progress', methods=['GET'])
@require_telegram_auth
@require_owner
def ai_core_tasks_progress():
    """Get task progress (OWNER ONLY)"""
    try:
        from tracking.ai_core_engine import TaskManager
        
        manager = TaskManager()
        progress = manager.show_progress_to_user()
        
        return jsonify({'success': True, **progress})
    except Exception as e:
        logger.error(f"AI Core tasks progress: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-core/status', methods=['GET'])
@require_telegram_auth
@require_owner
def ai_core_full_status():
    """Get full AI Core status (OWNER ONLY)"""
    try:
        from tracking.ai_core_engine import AICoreOrchestrator
        
        orchestrator = AICoreOrchestrator()
        status = orchestrator.get_full_status()
        
        return jsonify({'success': True, **status})
    except Exception as e:
        logger.error(f"AI Core full status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== END AI CORE ENGINE SECTION ====================


# ==================== END AI CHAT SECTION ====================


# ==================== WORKSPACE SECTION ====================

def validate_workspace_path(file_path):
    """Validate and secure workspace file path - returns (valid, full_path, error)"""
    if not file_path:
        return False, None, 'Path required'
    
    blocked_patterns = ['.env', '.git', '__pycache__', 'node_modules', '.replit', 
                       '.cache', '.upm', '.config', 'venv', '.local', '.nix']
    
    for blocked in blocked_patterns:
        if blocked in file_path.lower():
            return False, None, f'Access to {blocked} is not allowed'
    
    if '..' in file_path or file_path.startswith('/') or file_path.startswith('~'):
