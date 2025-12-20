import logging
import os
import asyncio
from .base_bot import BaseAutomationBot

logger = logging.getLogger(__name__)

class GithubBot(BaseAutomationBot):
    """
    Automatización de GitHub.
    Puede usar API (preferido) o UI Automation si es necesario.
    """
    
    def __init__(self, token: str = None, headless: bool = True):
        super().__init__(headless)
        self.token = token

    async def create_repo(self, repo_name: str, private: bool = True, description: str = "") -> str:
        """
        Crea un repositorio en GitHub.
        Si hay token, usa API (Requests). Si no, intentará flujo UI (Complejo por 2FA).
        Retorna la URL del repo.
        """
        if self.token:
            return await self._create_repo_api(repo_name, private, description)
        else:
            return await self._create_repo_ui(repo_name, private, description)

    async def _create_repo_api(self, repo_name: str, private: bool, description: str) -> str:
        """Creación vía API (Más estable)"""
        import aiohttp
        
        url = "https://api.github.com/user/repos"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        payload = {
            "name": repo_name,
            "private": private,
            "description": description,
            "auto_init": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status == 201:
                    data = await resp.json()
                    logger.info(f"GitHub Repo created: {data['html_url']}")
                    return data['html_url']
                else:
                    error_text = await resp.text()
                    logger.error(f"Failed to create repo API: {error_text}")
                    raise Exception(f"GitHub API Error: {resp.status}")

    async def _create_repo_ui(self, repo_name: str, private: bool, description: str) -> str:
        """Creación vía UI (Ghost Mode - Placeholder)"""
        # IMPORTANTE: Esto requiere login previo o cookies de sesión inyectadas.
        # Por ahora, lanzaremos error si no hay token.
        raise NotImplementedError("Ghost Mode para creación de repos requiere Cookies de sesión configuradas. Por favor proporciona un GITHUB_TOKEN.")

    async def push_code(self, repo_url: str, local_path: str, user_email: str, user_name: str):
        """Inicializa git y hace push al repo"""
        try:
            # Construir URL con token para auth
            auth_url = repo_url
            if self.token and "https://" in repo_url:
                auth_url = repo_url.replace("https://", f"https://{self.token}@")
            
            # Comandos git
            commands = [
                f"cd {local_path}",
                "git init",
                f"git config user.email '{user_email}'",
                f"git config user.name '{user_name}'",
                "git add .",
                "git commit -m 'Initial commit by BUNK3R-IA'",
                "git branch -M main",
                f"git remote add origin {auth_url}",
                "git push -u origin main"
            ]
            
            full_command = " && ".join(commands)
            
            # Ejecutar en subprocess
            process = await asyncio.create_subprocess_shell(
                full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Git Push Failed: {stderr.decode()}")
                raise Exception(f"Git Error: {stderr.decode()}")
                
            logger.info("Git Push Successful")
            
        except Exception as e:
            logger.error(f"Push code error: {e}")
            raise e
