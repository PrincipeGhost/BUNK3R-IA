"""
BUNK3R-IA: GitHub Auto-Sync Service
Sincronización automática de repositorios del usuario
"""
import os
import logging
import subprocess
import requests
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from flask import current_app

logger = logging.getLogger(__name__)

class GitHubSyncService:
    """Servicio de sincronización automática de repositorios de GitHub"""
    
    def __init__(self, user_id: str, github_token: str):
        self.user_id = user_id
        self.github_token = github_token
        self.base_workspace = Path(current_app.config.get('WORKSPACES_DIR', 'backend/workspaces'))
        self.user_workspace = self.base_workspace / user_id / 'repos'
        self.user_workspace.mkdir(parents=True, exist_ok=True)
        
    def verify_token(self) -> Dict:
        """Verifica que el token de GitHub sea válido"""
        try:
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            response = requests.get("https://api.github.com/user", headers=headers, timeout=10)
            
            if response.ok:
                user_data = response.json()
                return {
                    "success": True,
                    "username": user_data.get("login"),
                    "name": user_data.get("name"),
                    "email": user_data.get("email"),
                    "avatar_url": user_data.get("avatar_url")
                }
            else:
                return {"success": False, "error": "Token inválido o expirado"}
        except Exception as e:
            logger.error(f"Error verificando token de GitHub: {e}")
            return {"success": False, "error": str(e)}
    
    def get_all_repos(self) -> List[Dict]:
        """Obtiene todos los repositorios del usuario"""
        try:
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            all_repos = []
            page = 1
            per_page = 100
            
            while True:
                url = f"https://api.github.com/user/repos?sort=updated&per_page={per_page}&page={page}"
                response = requests.get(url, headers=headers, timeout=10)
                
                if not response.ok:
                    logger.error(f"Error obteniendo repos: {response.status_code}")
                    break
                    
                repos = response.json()
                if not repos:
                    break
                    
                for repo in repos:
                    all_repos.append({
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "private": repo["private"],
                        "clone_url": repo["clone_url"],
                        "html_url": repo["html_url"],
                        "description": repo.get("description", ""),
                        "language": repo.get("language", "Unknown"),
                        "updated_at": repo["updated_at"],
                        "default_branch": repo.get("default_branch", "main")
                    })
                
                page += 1
                
                # Límite de seguridad
                if page > 10:
                    break
            
            logger.info(f"Encontrados {len(all_repos)} repositorios para {self.user_id}")
            return all_repos
            
        except Exception as e:
            logger.error(f"Error obteniendo repositorios: {e}")
            return []
    
    def clone_repo(self, repo: Dict) -> Dict:
        """Clona un repositorio individual"""
        repo_name = repo["name"]
        repo_full_name = repo["full_name"]
        local_path = self.user_workspace / repo_name
        
        # Si ya existe, hacer pull en lugar de clonar
        if local_path.exists():
            return self._pull_repo(local_path, repo_name)
        
        try:
            # Construir URL con token para autenticación
            clone_url = f"https://{self.github_token}@github.com/{repo_full_name}.git"
            
            logger.info(f"Clonando {repo_full_name} en {local_path}")
            
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', clone_url, str(local_path)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos máximo por repo
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Repo {repo_name} clonado exitosamente")
                return {
                    "success": True,
                    "repo_name": repo_name,
                    "local_path": str(local_path),
                    "action": "cloned"
                }
            else:
                logger.error(f"Error clonando {repo_name}: {result.stderr}")
                return {
                    "success": False,
                    "repo_name": repo_name,
                    "error": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout clonando {repo_name}")
            return {"success": False, "repo_name": repo_name, "error": "Timeout"}
        except Exception as e:
            logger.error(f"Excepción clonando {repo_name}: {e}")
            return {"success": False, "repo_name": repo_name, "error": str(e)}
    
    def _pull_repo(self, local_path: Path, repo_name: str) -> Dict:
        """Actualiza un repositorio existente"""
        try:
            result = subprocess.run(
                ['git', 'pull'],
                cwd=str(local_path),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Repo {repo_name} actualizado")
                return {
                    "success": True,
                    "repo_name": repo_name,
                    "local_path": str(local_path),
                    "action": "updated"
                }
            else:
                logger.warning(f"No se pudo actualizar {repo_name}: {result.stderr}")
                return {
                    "success": True,  # No es crítico si el pull falla
                    "repo_name": repo_name,
                    "local_path": str(local_path),
                    "action": "skipped",
                    "warning": result.stderr
                }
        except Exception as e:
            logger.error(f"Error actualizando {repo_name}: {e}")
            return {
                "success": True,
                "repo_name": repo_name,
                "local_path": str(local_path),
                "action": "skipped",
                "error": str(e)
            }
    
    def sync_all_repos(self) -> Dict:
        """Sincroniza todos los repositorios del usuario"""
        logger.info(f"🔄 Iniciando sincronización completa para {self.user_id}")
        
        # Verificar token primero
        token_check = self.verify_token()
        if not token_check["success"]:
            return {
                "success": False,
                "error": "Token de GitHub inválido",
                "details": token_check.get("error")
            }
        
        # Obtener lista de repos
        repos = self.get_all_repos()
        if not repos:
            return {
                "success": False,
                "error": "No se encontraron repositorios o error al obtenerlos"
            }
        
        # Clonar/actualizar cada repo
        results = {
            "total": len(repos),
            "cloned": 0,
            "updated": 0,
            "failed": 0,
            "skipped": 0,
            "repos": []
        }
        
        for repo in repos:
            result = self.clone_repo(repo)
            results["repos"].append(result)
            
            if result["success"]:
                action = result.get("action", "unknown")
                if action == "cloned":
                    results["cloned"] += 1
                elif action == "updated":
                    results["updated"] += 1
                elif action == "skipped":
                    results["skipped"] += 1
            else:
                results["failed"] += 1
        
        logger.info(f"✅ Sincronización completada: {results['cloned']} clonados, {results['updated']} actualizados, {results['failed']} fallidos")
        
        return {
            "success": True,
            "username": token_check.get("username"),
            "sync_results": results,
            "workspace_path": str(self.user_workspace)
        }
    
    def get_synced_repos(self) -> List[Dict]:
        """Obtiene la lista de repositorios ya sincronizados localmente"""
        synced = []
        
        if not self.user_workspace.exists():
            return synced
        
        for repo_dir in self.user_workspace.iterdir():
            if repo_dir.is_dir() and (repo_dir / '.git').exists():
                synced.append({
                    "name": repo_dir.name,
                    "local_path": str(repo_dir),
                    "exists": True
                })
        
        return synced
