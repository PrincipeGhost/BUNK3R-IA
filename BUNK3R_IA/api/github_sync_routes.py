"""
BUNK3R-IA: GitHub Sync Routes
Rutas para sincronización automática de repositorios
"""
import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from BUNK3R_IA.api.github_sync import GitHubSyncService
from BUNK3R_IA.models import db, GitHubRepo, GlobalSetting
from datetime import datetime

logger = logging.getLogger(__name__)

github_sync_bp = Blueprint('github_sync', __name__, url_prefix='/api/github')

def get_user_id():
    """Obtiene el ID del usuario actual"""
    if current_user.is_authenticated:
        return str(current_user.id)
    return request.headers.get('X-User-ID', 'demo_user')

@github_sync_bp.route('/token', methods=['POST'])
def save_token():
    """Guarda el token de GitHub y dispara auto-sync"""
    try:
        data = request.json
        token = data.get('token', '').strip()
        
        if not token:
            return jsonify({'success': False, 'error': 'Token requerido'}), 400
        
        user_id = get_user_id()
        
        # Crear servicio de sync
        sync_service = GitHubSyncService(user_id, token)
        
        # Verificar token primero
        verification = sync_service.verify_token()
        if not verification["success"]:
            return jsonify(verification), 401
        
        # Guardar token en configuración global (encriptado en producción)
        GlobalSetting.set(f'github_token_{user_id}', token)
        
        # Iniciar sincronización automática
        logger.info(f"🔄 Iniciando auto-sync para {user_id}")
        sync_result = sync_service.sync_all_repos()
        
        if sync_result["success"]:
            # Guardar repos en la base de datos
            for repo_info in sync_result["sync_results"]["repos"]:
                if repo_info["success"]:
                    repo_record = GitHubRepo.query.filter_by(
                        user_id=user_id,
                        repo_name=repo_info.get("repo_name", "")
                    ).first()
                    
                    if not repo_record:
                        repo_record = GitHubRepo(
                            user_id=user_id,
                            repo_name=repo_info["repo_name"],
                            local_path=repo_info["local_path"]
                        )
                        db.session.add(repo_record)
                    
                    repo_record.last_synced = datetime.utcnow()
                    repo_record.sync_status = 'ready'
            
            db.session.commit()
        
        return jsonify({
            'success': True,
            'username': verification.get("username"),
            'sync_results': sync_result.get("sync_results"),
            'message': f'✅ {sync_result["sync_results"]["cloned"] + sync_result["sync_results"]["updated"]} repositorios sincronizados'
        })
        
    except Exception as e:
        logger.error(f"Error guardando token y sincronizando: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@github_sync_bp.route('/sync', methods=['POST'])
def manual_sync():
    """Sincronización manual de repositorios"""
    try:
        user_id = get_user_id()
        
        # Obtener token guardado
        token = GlobalSetting.get(f'github_token_{user_id}')
        if not token:
            return jsonify({'success': False, 'error': 'No hay token de GitHub configurado'}), 400
        
        sync_service = GitHubSyncService(user_id, token)
        sync_result = sync_service.sync_all_repos()
        
        if sync_result["success"]:
            # Actualizar base de datos
            for repo_info in sync_result["sync_results"]["repos"]:
                if repo_info["success"]:
                    repo_record = GitHubRepo.query.filter_by(
                        user_id=user_id,
                        repo_name=repo_info["repo_name"]
                    ).first()
                    
                    if repo_record:
                        repo_record.last_synced = datetime.utcnow()
                        repo_record.sync_status = 'ready'
            
            db.session.commit()
        
        return jsonify(sync_result)
        
    except Exception as e:
        logger.error(f"Error en sincronización manual: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@github_sync_bp.route('/sync/status', methods=['GET'])
def sync_status():
    """Estado de la sincronización"""
    try:
        user_id = get_user_id()
        
        repos = GitHubRepo.query.filter_by(user_id=user_id).all()
        
        total = len(repos)
        ready = sum(1 for r in repos if r.sync_status == 'ready')
        syncing = sum(1 for r in repos if r.sync_status == 'syncing')
        error = sum(1 for r in repos if r.sync_status == 'error')
        
        return jsonify({
            'success': True,
            'total': total,
            'ready': ready,
            'syncing': syncing,
            'error': error,
            'has_token': GlobalSetting.get(f'github_token_{user_id}') is not None
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de sync: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
