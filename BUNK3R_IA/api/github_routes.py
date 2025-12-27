from flask import Blueprint, jsonify, request
from flask_dance.contrib.github import github

github_api_bp = Blueprint('github_api', __name__, url_prefix='/api/github')

@github_api_bp.route('/user', methods=['GET'])
def get_user_info():
    """Get GitHub user info from token"""
    import requests
    token = request.args.get('token')
    
    if not token:
        return jsonify({"error": "Token required"}), 400
    
    try:
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        response = requests.get("https://api.github.com/user", headers=headers)
        
        if response.ok:
            user_data = response.json()
            return jsonify({
                "username": user_data.get("login"),
                "name": user_data.get("name"),
                "avatar": user_data.get("avatar_url"),
                "email": user_data.get("email")
            })
        else:
            return jsonify({"error": "Invalid token"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@github_api_bp.route('/repos', methods=['GET'])
def list_repos():
    """Lista los repositorios del usuario authenticated"""
    import requests
    manual_token = request.args.get('token')
    
    if manual_token:
        try:
            headers = {"Authorization": f"token {manual_token}", "Accept": "application/vnd.github.v3+json"}
            response = requests.get("https://api.github.com/user/repos?sort=updated&per_page=100", headers=headers)
            
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
                return jsonify({"error": "Failed to fetch repos with manual token", "details": response.text}), response.status_code
        except Exception as e:
            return jsonify({"error": str(e), "repos": []}), 500

    # Old OAuth Logic fallback
    import os
    
    # Check if GitHub OAuth is configured
    if not os.environ.get('GITHUB_CLIENT_ID'):
        return jsonify({
            "error": "GitHub not configured",
            "message": "Configure GITHUB_CLIENT_ID or provide a manual token",
            "repos": []
        }), 200
    
    try:
        if not github.authorized:
            return jsonify({
                "error": "GitHub not authorized",
                "message": "Please login with GitHub or provide a token",
                "repos": []
            }), 200
        
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
            
    except AttributeError:
        # github.authorized not available - GitHub OAuth not initialized
        return jsonify({
            "error": "GitHub OAuth not initialized",
            "message": "GitHub authentication is not configured.",
            "repos": []
        }), 200
    except Exception as e:
        return jsonify({"error": str(e), "repos": []}), 200

@github_api_bp.route('/contents', methods=['GET'])
def get_repo_contents():
    """Obtiene el contenido (archivos/carpetas) de un repositorio"""
    repo_full_name = request.args.get('repo')
    path = request.args.get('path', '')
    manual_token = request.args.get('token')
    
    if not repo_full_name:
        return jsonify({"error": "Missing repo parameter"}), 400

    try:
        url_path = f"/{path}" if path else ""
        url = f"https://api.github.com/repos/{repo_full_name}/contents{url_path}"
        
        headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Priorizar el token manual si se proporciona
        if manual_token:
            headers["Authorization"] = f"token {manual_token}"
        else:
            # Fallback a OAuth si no hay token manual
            try:
                if github.authorized:
                    # En flask-dance con proxy_fix, github.get() maneja la auth
                    response = github.get(f"/repos/{repo_full_name}/contents{url_path}")
                    if response.ok:
                        return process_github_contents(response.json(), repo_full_name)
                    else:
                        return jsonify({"error": "Failed to fetch contents", "details": response.text}), response.status_code
            except (AttributeError, Exception):
                pass
                
        # Si llegamos aquí es que usamos token manual o OAuth falló
        import requests
        response = requests.get(url, headers=headers)
        
        if response.ok:
            return process_github_contents(response.json(), repo_full_name)
        else:
            return jsonify({"error": "Failed to fetch contents", "details": response.text}), response.status_code
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def process_github_contents(items, repo_full_name=None):
    file_tree = []
    if isinstance(items, list):
        for item in items:
            file_tree.append({
                "name": item['name'],
                "type": "folder" if item['type'] == "dir" else "file",
                "path": item['path'],
                "download_url": item.get('download_url'),
                "repo": repo_full_name
            })
        file_tree.sort(key=lambda x: (x['type'] != 'folder', x['name']))
        
        # Logica simple para "analizar" el repo: 
        # Si estamos en la raiz, podriamos guardar en DB que estamos viendo este repo
        if items and repo_full_name:
            print(f"[IA-INDEX] Analizando estructura de {repo_full_name}...")
            
    return jsonify({"files": file_tree})
