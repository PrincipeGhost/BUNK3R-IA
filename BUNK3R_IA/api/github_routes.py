from flask import Blueprint, jsonify, request
from flask_dance.contrib.github import github

github_bp = Blueprint('github', __name__, url_prefix='/api/github')

@github_bp.route('/repos', methods=['GET'])
def list_repos():
    """Lista los repositorios del usuario authenticated"""
    import os
    
    # Check if GitHub OAuth is configured
    if not os.environ.get('GITHUB_CLIENT_ID'):
        return jsonify({
            "error": "GitHub not configured",
            "message": "Configure GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET to enable GitHub integration",
            "repos": []
        }), 200
    
    try:
        if not github.authorized:
            return jsonify({
                "error": "GitHub not authorized",
                "message": "Please login with GitHub to view your repositories",
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
            "message": "GitHub authentication is not configured. Please set up GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET",
            "repos": []
        }), 200
    except Exception as e:
        return jsonify({"error": str(e), "repos": []}), 200

@github_bp.route('/contents', methods=['GET'])
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
                        return process_github_contents(response.json())
                    else:
                        return jsonify({"error": "Failed to fetch contents", "details": response.text}), response.status_code
            except (AttributeError, Exception):
                pass
                
        # Si llegamos aquí es que usamos token manual o OAuth falló
        import requests
        response = requests.get(url, headers=headers)
        
        if response.ok:
            return process_github_contents(response.json())
        else:
            return jsonify({"error": "Failed to fetch contents", "details": response.text}), response.status_code
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def process_github_contents(items):
    file_tree = []
    if isinstance(items, list):
        for item in items:
            file_tree.append({
                "name": item['name'],
                "type": "folder" if item['type'] == "dir" else "file",
                "path": item['path'],
                "download_url": item.get('download_url')
            })
        file_tree.sort(key=lambda x: (x['type'] != 'folder', x['name']))
    return jsonify({"files": file_tree})
