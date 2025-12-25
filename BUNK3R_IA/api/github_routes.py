from flask import Blueprint, jsonify, request
from flask_dance.contrib.github import github

github_bp = Blueprint('github', __name__, url_prefix='/api/github')

@github_bp.route('/repos', methods=['GET'])
def list_repos():
    """Lista los repositorios del usuario authenticated"""
    if not github.authorized:
        return jsonify({"error": "GitHub not authorized"}), 401
    
    try:
        response = github.get("/user/repos?sort=updated&per_page=100")
        if response.ok:
            repos = response.json()
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

@github_bp.route('/contents', methods=['GET'])
def get_repo_contents():
    """Obtiene el contenido (archivos/carpetas) de un repositorio"""
    if not github.authorized:
        return jsonify({"error": "GitHub not authorized"}), 401
        
    repo_full_name = request.args.get('repo')
    path = request.args.get('path', '')
    
    if not repo_full_name:
        return jsonify({"error": "Missing repo parameter"}), 400

    try:
        url_path = f"/{path}" if path else ""
        url = f"/repos/{repo_full_name}/contents{url_path}"
        
        response = github.get(url)
        
        if response.ok:
            items = response.json()
            file_tree = []
            if isinstance(items, list):
                for item in items:
                    file_tree.append({
                        "name": item['name'],
                        "type": "folder" if item['type'] == "dir" else "file",
                        "path": item['path'],
                        "download_url": item['download_url']
                    })
                file_tree.sort(key=lambda x: (x['type'] != 'folder', x['name']))
            return jsonify({"files": file_tree})
        else:
            return jsonify({"error": "Failed to fetch contents", "details": response.text}), response.status_code
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
