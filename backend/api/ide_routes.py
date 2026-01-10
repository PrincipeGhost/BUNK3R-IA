"""
BUNK3R-IA: IDE API Routes
Rutas simplificadas para el nuevo IDE Premium
"""
import os
import logging
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from pathlib import Path
from core.singularity import singularity
from core.ai_service import get_ai_service
from core.repo_indexer import RepoIndexer
from backend.api.github_sync import GitHubSyncService
from backend.models import db, GitHubRepo

logger = logging.getLogger(__name__)

ide_bp = Blueprint('ide', __name__, url_prefix='/api/ide')

def get_user_id():
    """Obtiene el ID del usuario actual"""
    if current_user.is_authenticated:
        return str(current_user.id)
    # Soporte para token en cabecera si es necesario para llamadas desde Node
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        # Aquí se podría validar un token JWT si lo implementamos
        pass
    return request.headers.get('X-User-ID', 'demo_user')

def get_base_path(user_id):
    """Retorna la ruta base del workspace del usuario"""
    return Path(f"/workspace/{user_id}")

@ide_bp.route('/chat', methods=['POST'])
def ide_chat():
    """Chat unificado con Singularity - Reemplaza al AI Constructor"""
    try:
        data = request.json
        user_id = get_user_id()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'success': False, 'error': 'Mensaje requerido'}), 400
        
        # Obtener contexto del repositorio activo
        active_repo = data.get('active_repo')
        repo_context = ""
        
        if active_repo:
            repo_path = get_base_path(user_id) / active_repo
            if repo_path.exists():
                indexer = RepoIndexer(repo_path)
                index_result = indexer.index_repo()
                if index_result["success"]:
                    index = index_result["index"]
                    repo_context = f"""
CONTEXTO DEL REPOSITORIO ACTIVO:
- Carpeta: {active_repo}
- Lenguajes: {', '.join(index['languages'].keys())}
- Archivos: {index['file_count']}
- Estructura: {', '.join([f['path'] for f in index['structure'][:15] if f['type'] == 'file'])}
"""
        
        # System prompt mejorado con contexto de repos
        system_prompt = f"""# MODO BUNK3R: ARQUITECTO DE CODIGO
Eres BUNK3R-IA, el cerebro operativo de este IDE. Tienes acceso directo al sistema de archivos del usuario.

{repo_context}

## CAPACIDADES DE ACCIÓN:
Puedes manipular el código usando herramientas. Si el usuario pide crear, editar o borrar algo, HAZLO directamente.
Herramientas disponibles: `read_file`, `write_file`, `list_dir`, `run_command`, `web_search`.

Usa siempre el formato: <TOOL>{{"name": "nombre", "args": {{...}}}}</TOOL>
"""
        
        # Llamar a Singularity
        ai_service = get_ai_service()
        result = ai_service.chat(
            user_id=user_id,
            message=message,
            system_prompt=system_prompt
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error en IDE chat: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ide_bp.route('/workspace', methods=['GET'])
def get_workspace():
    """Lista archivos del workspace del usuario"""
    try:
        user_id = get_user_id()
        workspace_path = get_base_path(user_id)
        
        if not workspace_path.exists():
            return jsonify({'success': True, 'repos': [], 'path': str(workspace_path)})
        
        repos = []
        for repo_dir in workspace_path.iterdir():
            if repo_dir.is_dir():
                repos.append({
                    "name": repo_dir.name,
                    "path": str(repo_dir),
                    "is_git": (repo_dir / '.git').exists()
                })
        
        return jsonify({'success': True, 'repos': repos})
    except Exception as e:
        logger.error(f"Error obteniendo workspace: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ide_bp.route('/file', methods=['GET'])
def read_file_route():
    """Lee un archivo específico"""
    try:
        user_id = get_user_id()
        file_path = request.args.get('path')
        
        if not file_path:
            return jsonify({'success': False, 'error': 'Path requerido'}), 400
        
        full_path = get_base_path(user_id) / file_path
        
        if not full_path.exists() or not full_path.is_file():
            return jsonify({'success': False, 'error': f'Archivo no encontrado: {file_path}'}), 404
        
        content = full_path.read_text(encoding='utf-8', errors='ignore')
        return jsonify({'success': True, 'content': content, 'path': file_path})
    except Exception as e:
        logger.error(f"Error leyendo archivo: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ide_bp.route('/file', methods=['POST'])
def write_file_route():
    """Guarda o edita un archivo"""
    try:
        user_id = get_user_id()
        data = request.json
        file_path = data.get('path')
        content = data.get('content', '')
        
        if not file_path:
            return jsonify({'success': False, 'error': 'Path requerido'}), 400
        
        full_path = get_base_path(user_id) / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding='utf-8')
        
        return jsonify({'success': True, 'path': file_path, 'message': 'Archivo guardado'})
    except Exception as e:
        logger.error(f"Error guardando archivo: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ide_bp.route('/repos', methods=['GET'])
def list_repos():
    """Lista repositorios sincronizados"""
    try:
        user_id = get_user_id()
        repos = GitHubRepo.query.filter_by(user_id=user_id).all()
        return jsonify({
            'success': True,
            'repos': [{
                'name': r.repo_name.split('/')[-1],
                'full_name': r.repo_name,
                'local_path': r.local_path,
                'last_synced': r.last_synced.isoformat() if r.last_synced else None,
                'status': r.sync_status
            } for r in repos]
        })
    except Exception as e:
        logger.error(f"Error listando repos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ide_bp.route('/repo/index', methods=['POST'])
def index_repo():
    """Indexa un repositorio específico"""
    try:
        user_id = get_user_id()
        data = request.json
        repo_name = data.get('repo')
        
        if not repo_name:
            return jsonify({'success': False, 'error': 'Nombre de repo requerido'}), 400
        
        repo_path = get_base_path(user_id) / repo_name
        if not repo_path.exists():
            return jsonify({'success': False, 'error': 'Repositorio no encontrado'}), 404
        
        indexer = RepoIndexer(repo_path)
        result = indexer.index_repo()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error indexando repo: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ide_bp.route('/repo/search', methods=['POST'])
def search_in_repo():
    """Busca en un repositorio"""
    try:
        user_id = get_user_id()
        data = request.json
        repo_name = data.get('repo')
        query = data.get('query', '')
        
        if not repo_name or not query:
            return jsonify({'success': False, 'error': 'Repo y query requeridos'}), 400
        
        repo_path = get_base_path(user_id) / repo_name
        if not repo_path.exists():
            return jsonify({'success': False, 'error': f'Repositorio no encontrado: {repo_name}'}), 404
        
        indexer = RepoIndexer(repo_path)
        results = indexer.search_in_repo(query)
        return jsonify({'success': True, 'query': query, 'results': results})
    except Exception as e:
        logger.error(f"Error buscando en repo: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
