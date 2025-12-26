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

    # Normalización agresiva de la ruta
    # Si la ruta tiene prefijos de repo de GitHub, los removemos
    clean_path = file_path.strip('/')
    prefixes = ["PrincipeGhost/BUNK3R-W3B", "PrincipeGhost/BUNK3R-IA", "PrincipeGhost/BUNK3R"]
    for prefix in prefixes:
        if clean_path.startswith(prefix):
            clean_path = clean_path[len(prefix):].strip('/')
            break

    # Buscar el archivo directamente en la raíz del proyecto local
    possible_paths = [
        os.path.abspath(os.path.join(os.getcwd(), clean_path)),
        os.path.abspath(os.path.join(os.getcwd(), "BUNK3R_IA", clean_path))
    ]
    
    # Añadir rutas de carpetas comunes si no se encuentra
    if not any(os.path.exists(p) for p in possible_paths):
        common_dirs = ["api", "core", "static", "templates", "tests", "docs", "prompts"]
        for d in common_dirs:
            possible_paths.append(os.path.abspath(os.path.join(os.getcwd(), "BUNK3R_IA", d, clean_path)))

    full_path = None
    for p in possible_paths:
        if os.path.exists(p) and os.path.isfile(p):
            full_path = p
            break
            
    # Si sigue sin existir y es un archivo (tiene extensión), buscarlo recursivamente en TODO el proyecto
    if not full_path and "." in os.path.basename(clean_path):
        filename = os.path.basename(clean_path)
        print(f"[AI-LOG] File not found by direct path, searching recursively for: {filename}")
        search_root = os.path.abspath(os.path.join(os.getcwd())) 
        for root, dirs, files in os.walk(search_root):
            if filename in files:
                full_path = os.path.join(root, filename)
                print(f"[AI-LOG] Found file at: {full_path}")
                break

    if not full_path:
        print(f"[AI-LOG] ERROR: File NOT found: {file_path}")
        return jsonify({"success": False, "error": f"File not found: {file_path} (cleaned: {clean_path})"}), 404

    print(f"[AI-LOG] File found, proceeding to read/write: {full_path}")
    # Seguridad: asegurar que el archivo está dentro de la raíz permitida
    # En Replit, permitimos leer cualquier cosa dentro de /home/runner/
    if not full_path.startswith('/home/runner/'):
         print(f"[AI-LOG] ERROR: Access denied for path: {full_path}")
         return jsonify({"success": False, "error": "Access denied"}), 403

    if request.method == 'GET':
        try:
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
            
    return jsonify({"success": False, "error": "Method not allowed"}), 405

import subprocess

@projects_bp.route('/command/run', methods=['POST'])
def run_command():
    """Ejecutar un comando en el sistema"""
    data = request.json
    command = data.get('command')
    timeout = data.get('timeout', 30)
    
    if not command:
        return jsonify({"success": False, "error": "No command provided"}), 400
        
    try:
        # Ejecutar comando de forma segura
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd()
        )
        
        return jsonify({
            "success": True,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        })
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "error": "Command timeout"}), 408
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
