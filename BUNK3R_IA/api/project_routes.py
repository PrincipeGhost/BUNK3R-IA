from flask import Blueprint, jsonify, request, current_app
import os
from BUNK3R_IA.core.database.manager import manager
from BUNK3R_IA.core.workers.queue_manager import queue_manager

projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')

@projects_bp.route('/', methods=['GET'])
def list_projects():
    """Listar proyectos para un usuario"""
    from flask_login import current_user
    user_id = current_user.id if current_user.is_authenticated else "user_123"
    conn = manager.get_user_db(user_id)
    if not conn:
        return jsonify({"projects": []})
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects ORDER BY created_at DESC")
    projects = [dict(row) for row in cursor.fetchall()]
    return jsonify({"projects": projects})

@projects_bp.route('/create', methods=['POST'])
def create_project():
    """Crear un nuevo proyecto y lanzar tarea de autoconfiguración"""
    data = request.json
    user_id = "user_123"
    name = data.get('name')
    project_id = data.get('project_id', name.lower().replace(' ', '-'))
    
    try:
        # Registrar en DB
        manager.register_project(user_id, project_id, name)
        
        # Encolar tarea de inicialización (ej: crear repo)
        queue_manager.enqueue_task(
            task_type='create_github_repo',
            payload={'repo_name': f"bunk3r-{project_id}"},
            user_id=user_id,
            project_id=project_id
        )
        
        return jsonify({"success": True, "project_id": project_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@projects_bp.route('/<project_id>/files', methods=['GET'])
def get_project_files(project_id):
    """Retorna la estructura de archivos del proyecto"""
    # En un caso real, esto leería del directorio físico del proyecto.
    # Simularemos una estructura para el ejemplo si no existe carpeta real aún.
    
    # Path base ficticio o real
    # project_path = os.path.join(current_app.config['PROJECTS_DIR'], project_id)
    
    # Mock response por ahora hasta conectar con filesystem real
    structure = [
        {"name": "src", "type": "folder", "children": [
            {"name": "app.py", "type": "file"},
            {"name": "utils.py", "type": "file"}
        ]},
        {"name": "tests", "type": "folder", "children": []},
        {"name": "README.md", "type": "file"},
        {"name": ".env", "type": "file", "protected": True}
    ]
    return jsonify({"files": structure})

@projects_bp.route('/<project_id>/env', methods=['GET', 'POST'])
def manage_env(project_id):
    """Leer o actualizar variables de entorno (Vault)"""
    if request.method == 'GET':
        # Retornar variables de DB desencriptadas
        return jsonify({"env": {"DATABASE_URL": "postgres://...", "API_KEY": "****"}})
    
    if request.method == 'POST':
        # Guardar cambios
        return jsonify({"success": True})
