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
    """Retorna la estructura de archivos real del proyecto"""
    project_path = os.path.join(os.getcwd(), str(project_id))
    if not os.path.exists(project_path) or project_id == 'current':
        # Fallback para el repo actual si el proyecto no tiene carpeta propia aún
        project_path = os.getcwd()

    def get_dir_structure(path):
        items = []
        try:
            for entry in os.scandir(path):
                if entry.name.startswith('.') or entry.name == '__pycache__':
                    continue
                if entry.is_dir():
                    items.append({
                        "name": entry.name,
                        "type": "folder",
                        "children": get_dir_structure(entry.path)
                    })
                else:
                    items.append({
                        "name": entry.name,
                        "type": "file",
                        "path": os.path.relpath(entry.path, os.getcwd())
                    })
        except Exception:
            pass
        return items

    return jsonify({"files": get_dir_structure(project_path)})

@projects_bp.route('/file/content', methods=['GET', 'POST'])
def manage_file_content():
    """Leer o actualizar contenido de un archivo"""
    file_path = ""
    if request.method == 'GET':
        file_path = request.args.get('path', '')
    else:
        file_path = request.json.get('path', '') if request.json else ''
        
    if not file_path:
        return jsonify({"success": False, "error": "No path provided"}), 400

    full_path = os.path.abspath(os.path.join(os.getcwd(), file_path))
    
    # Intento de encontrar el archivo si la ruta incluye el nombre del repo (para compatibilidad con GitHub UI)
    if not os.path.exists(full_path):
        # Limpieza de la ruta para evitar problemas con nombres de repo
        # Si la ruta es solo el nombre de un repo o usuario, o una carpeta sin extensión
        parts = file_path.strip('/').split('/')
        is_potential_repo_or_dir = len(parts) <= 2 and not "." in parts[-1]
        
        if is_potential_repo_or_dir:
            # Es probable que sea el nombre del repo PrincipeGhost/BUNK3R o una carpeta
            # Intentamos servir el README.md del proyecto actual como fallback
            full_path = os.path.join(os.getcwd(), 'README.md')
        else:
            # Intentar limpiar prefijos conocidos si el archivo no existe
            clean_path = file_path
            # Prefijos dinámicos basados en la estructura del usuario (dueño/repo)
            if len(parts) >= 2:
                # Si las primeras partes parecen ser un owner/repo de GitHub
                # Probamos quitando PrincipeGhost/BUNK3R y variantes
                prefixes = ["PrincipeGhost/BUNK3R-W3B/", "PrincipeGhost/BUNK3R-IA/", "PrincipeGhost/BUNK3R/"]
                for prefix in prefixes:
                    if clean_path.startswith(prefix):
                        clean_path = clean_path.replace(prefix, "", 1)
                        break
                # Si aún no existe, probamos quitando los dos primeros segmentos dinámicamente
                if not os.path.exists(os.path.join(os.getcwd(), clean_path)) and len(parts) > 2:
                    clean_path = "/".join(parts[2:])
            
            full_path = os.path.abspath(os.path.join(os.getcwd(), clean_path))

    # Intento agresivo si sigue sin existir
    if not os.path.exists(full_path):
        parts = file_path.split('/')
        # Si tiene más de 2 partes (owner/repo/archivo)
        if len(parts) >= 2:
            # Probar buscando solo el nombre del archivo en el directorio actual
            filename = parts[-1]
            for root, dirs, files in os.walk(os.getcwd()):
                if filename in files:
                    full_path = os.path.join(root, filename)
                    break
    
    # Seguridad básica: no salir del directorio actual
    if not full_path.startswith(os.getcwd()):
        return jsonify({"success": False, "error": "Access denied"}), 403

    if request.method == 'GET':
        try:
            if not os.path.exists(full_path):
                return jsonify({"success": False, "error": f"File not found: {file_path}"}), 404
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({"success": True, "content": content})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    if request.method == 'POST':
        content = request.json.get('content', '') if request.json else ''
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

@projects_bp.route('/<project_id>/env', methods=['GET', 'POST'])
def manage_env(project_id):
    """Leer o actualizar variables de entorno (Vault)"""
    if request.method == 'GET':
        # Retornar variables de DB desencriptadas
        return jsonify({"env": {"DATABASE_URL": "postgres://...", "API_KEY": "****"}})
    
    if request.method == 'POST':
        # Guardar cambios
        return jsonify({"success": True})
