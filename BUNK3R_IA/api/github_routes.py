from flask import Blueprint, jsonify, request
import requests
from BUNK3R_IA.core.database.manager import manager

github_bp = Blueprint('github', __name__, url_prefix='/api/github')

# URL de API GitHub
GITHUB_API_URL = "https://api.github.com"

def get_github_token(user_id):
    """
    Recupera el token cifrado de la BD.
    (Simplificado: en este momento lo leemos de user_properties o similar.
    Como no tenemos tabla de secrets aun, usaremos la tabla 'users' o 'projects' si fuera por proyecto.
    Idealmente: Tabla 'user_secrets'. Por ahora, mock o extensión de User DB).
    """
    # TODO: Implementar lectura real de token cifrado.
    # Por ahora, aceptamos que el frontend lo envíe o lo buscamos en una variable mock.
    return None 

@github_bp.route('/repos', methods=['GET'])
def list_repos():
    """Lista los repositorios del usuario authenticated"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing GitHub Token"}), 401
    
    token = auth_header.replace("Bearer ", "")
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        # Paginación básica o fetch all
        response = requests.get(f"{GITHUB_API_URL}/user/repos?sort=updated&per_page=100", headers=headers)
        if response.status_code == 200:
            repos = response.json()
            # Simplificar data para el frontend
            simplified_repos = [{
                'id': r['id'],
                'name': r['name'],
                'full_name': r['full_name'],
                'private': r['private'],
                'html_url': r['html_url'],
                'description': r['description'],
                'language': r['language'],
                'updated_at': r['updated_at']
            } for r in repos]
            return jsonify({"repos": simplified_repos})
        else:
            return jsonify({"error": "Failed to fetch repos from GitHub", "details": response.text}), response.status_code
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@github_bp.route('/create', methods=['POST'])
def create_repo():
    """Crea un nuevo repositorio"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing GitHub Token"}), 401
        
    token = auth_header.replace("Bearer ", "")
    data = request.json
    repo_name = data.get('name')
    private = data.get('private', True)
    description = data.get('description', 'Created by BUNK3R-IA')
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    payload = {
        "name": repo_name,
        "private": private,
        "description": description,
        "auto_init": True
    }
    
    try:
        response = requests.post(f"{GITHUB_API_URL}/user/repos", json=payload, headers=headers)
        if response.status_code == 201:
            return jsonify({"success": True, "repo": response.json()})
        else:
            return jsonify({"error": "Failed to create repo", "details": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@github_bp.route('/contents', methods=['GET'])
def get_repo_contents():
    """Obtiene el contenido (archivos/carpetas) de un repositorio"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing GitHub Token"}), 401
        
    token = auth_header.replace("Bearer ", "")
    repo_full_name = request.args.get('repo') # e.g., "username/repo-name"
    path = request.args.get('path', '') # Root if empty
    
    if not repo_full_name:
        return jsonify({"error": "Missing repo parameter"}), 400

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        # GitHub API: GET /repos/{owner}/{repo}/contents/{path}
        # If path is empty, it gets root.
        url_path = f"/{path}" if path else ""
        url = f"{GITHUB_API_URL}/repos/{repo_full_name}/contents{url_path}"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            items = response.json()
            # Transform to our file tree format
            # GitHub returns a list of objects.
            file_tree = []
            if isinstance(items, list):
                for item in items:
                    file_tree.append({
                        "name": item['name'],
                        "type": "folder" if item['type'] == "dir" else "file",
                        "path": item['path'],
                        "download_url": item['download_url']
                    })
                # Sort: folders first
                file_tree.sort(key=lambda x: (x['type'] != 'folder', x['name']))
            else:
                 pass 
                
            return jsonify({"files": file_tree})
        else:
            return jsonify({"error": "Failed to fetch contents", "details": response.text}), response.status_code
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

