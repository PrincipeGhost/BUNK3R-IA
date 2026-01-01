"""
BUNK3R AI - Live Preview System (Sección 35)
Sistema de Preview en Vivo para código generado por IA

Funcionalidades:
- Generación de código HTML/CSS/JS con OpenAI
- Guardado de proyectos por sesión
- Servir preview en iframe
"""

import os
import re
import uuid
import logging
from typing import Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

PROJECTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'generated_projects')

GENERATION_SYSTEM_PROMPT = """Eres BUNK3R IA, un experto desarrollador web. 
Genera código HTML completo basado en la descripción del usuario.

REGLAS ESTRICTAS:
1. Genera UN SOLO archivo HTML completo y funcional
2. Incluye TODO el CSS dentro de <style> tags en el <head>
3. Incluye TODO el JavaScript dentro de <script> tags antes de </body>
4. El diseño debe ser moderno, profesional y responsive
5. Usa colores oscuros (tema dark) por defecto con acentos en dorado (#FFD700)
6. NO uses librerías externas (no CDN, no imports externos)
7. El código debe funcionar SIN conexión a internet
8. Asegúrate de incluir meta viewport para responsividad
9. Usa fuentes del sistema (system-ui, -apple-system, sans-serif)
10. Incluye hover effects y transiciones suaves

Responde ÚNICAMENTE con el código HTML. Sin explicaciones, sin markdown, sin comentarios fuera del código."""


@dataclass
class GeneratedProject:
    session_id: str
    prompt: str
    html_content: str
    created_at: datetime
    files: Dict[str, str]
    
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "prompt": self.prompt,
            "html_content": self.html_content[:500] + "..." if len(self.html_content) > 500 else self.html_content,
            "created_at": self.created_at.isoformat(),
            "files": list(self.files.keys())
        }


class LivePreviewGenerator:
    """
    Generador de Preview en Vivo
    Usa OpenAI para generar código HTML y lo guarda para preview
    """
    
    def __init__(self):
        self.projects_dir = PROJECTS_DIR
        self._ensure_projects_dir()
        self.sessions: Dict[str, GeneratedProject] = {}
    
    def _ensure_projects_dir(self):
        """Crea el directorio de proyectos si no existe"""
        if not os.path.exists(self.projects_dir):
            os.makedirs(self.projects_dir, exist_ok=True)
            logger.info(f"Created projects directory: {self.projects_dir}")
    
    def _sanitize_session_id(self, session_id: str) -> str:
        """Sanitiza el session_id para evitar path traversal"""
        return ''.join(c for c in session_id if c.isalnum() or c in '-_')
    
    def _get_session_dir(self, session_id: str) -> str:
        """Obtiene el directorio de sesión"""
        safe_id = self._sanitize_session_id(session_id)
        return os.path.join(self.projects_dir, safe_id)
    
    def generate_with_openai(self, prompt: str, session_id: str = None) -> Dict[str, Any]:
        """
        Genera código HTML usando OpenAI
        
        Args:
            prompt: Descripción del proyecto
            session_id: ID de sesión (opcional, se genera si no se proporciona)
        
        Returns:
            Dict con resultado de la generación
        """
        import os
        
        if not session_id:
            session_id = str(uuid.uuid4())[:8]
        
        openai_key = os.environ.get('OPENAI_API_KEY', '')
        
        if not openai_key:
            return {
                "success": False,
                "error": "OpenAI API key no configurada",
                "session_id": session_id
            }
        
        try:
            import requests
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": GENERATION_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 8000
                },
                timeout=120
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                return {
                    "success": False,
                    "error": f"OpenAI error: {response.status_code} - {error_data.get('error', {}).get('message', 'Unknown error')}",
                    "session_id": session_id
                }
            
            result = response.json()
            html_content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            html_content = self._clean_html_response(html_content)
            
            if not html_content or len(html_content) < 50:
                return {
                    "success": False,
                    "error": "OpenAI no generó código válido",
                    "session_id": session_id
                }
            
            save_result = self.save_project(session_id, html_content, prompt)
            
            if not save_result["success"]:
                return save_result
            
            project = GeneratedProject(
                session_id=session_id,
                prompt=prompt,
                html_content=html_content,
                created_at=datetime.now(),
                files={"index.html": html_content}
            )
            self.sessions[session_id] = project
            
            return {
                "success": True,
                "session_id": session_id,
                "preview_url": f"/preview/{session_id}",
                "files": ["index.html"],
                "message": "Proyecto generado exitosamente"
            }
            
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Timeout al conectar con OpenAI",
                "session_id": session_id
            }
        except Exception as e:
            logger.error(f"Error generating with OpenAI: {e}")
            return {
                "success": False,
                "error": f"Error de generación: {str(e)}",
                "session_id": session_id
            }
    
    def generate_with_fallback(self, prompt: str, session_id: str = None) -> Dict[str, Any]:
        """
        Genera código usando proveedores disponibles con fallback
        Primero intenta OpenAI, luego otros proveedores
        """
        if not session_id:
            session_id = str(uuid.uuid4())[:8]
        
        result = self.generate_with_openai(prompt, session_id)
        if result.get("success"):
            return result
        
        try:
            from BUNK3R_IA.core.ai_service import get_ai_service
            
            ai_service = get_ai_service(None)
            if ai_service and ai_service.providers:
                ai_result = ai_service.chat(
                    user_id=f"preview_{session_id}",
                    message=prompt,
                    system_prompt=GENERATION_SYSTEM_PROMPT
                )
                
                if ai_result.get("success"):
                    html_content = self._clean_html_response(ai_result.get("response", ""))
                    
                    if html_content and len(html_content) > 50:
                        save_result = self.save_project(session_id, html_content, prompt)
                        
                        if save_result["success"]:
                            return {
                                "success": True,
                                "session_id": session_id,
                                "preview_url": f"/preview/{session_id}",
                                "files": ["index.html"],
                                "message": f"Proyecto generado con {ai_result.get('provider', 'fallback')}"
                            }
        except Exception as e:
            logger.warning(f"Fallback generation failed: {e}")
        
        return result
    
    def _clean_html_response(self, content: str) -> str:
        """Limpia la respuesta de la IA para obtener solo HTML"""
        content = content.strip()
        
        code_block_match = re.search(r'```(?:html)?\s*([\s\S]*?)```', content, re.IGNORECASE)
        if code_block_match:
            content = code_block_match.group(1).strip()
        
        if not content.lower().startswith('<!doctype') and not content.lower().startswith('<html'):
            if '<html' in content.lower():
                start = content.lower().find('<!doctype')
                if start == -1:
                    start = content.lower().find('<html')
                if start > 0:
                    content = content[start:]
        
        return content
    
    def save_project(self, session_id: str, html_content: str, prompt: str = "") -> Dict[str, Any]:
        """
        Guarda el proyecto generado en el sistema de archivos
        
        Args:
            session_id: ID de sesión
            html_content: Contenido HTML a guardar
            prompt: Prompt original (para referencia)
        
        Returns:
            Dict con resultado del guardado
        """
        try:
            session_dir = self._get_session_dir(session_id)
            
            os.makedirs(session_dir, exist_ok=True)
            
            html_path = os.path.join(session_dir, 'index.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            if prompt:
                meta_path = os.path.join(session_dir, 'meta.txt')
                with open(meta_path, 'w', encoding='utf-8') as f:
                    f.write(f"Prompt: {prompt}\n")
                    f.write(f"Created: {datetime.now().isoformat()}\n")
            
            logger.info(f"Project saved: {session_id}")
            
            return {
                "success": True,
                "session_id": session_id,
                "path": session_dir
            }
            
        except Exception as e:
            logger.error(f"Error saving project {session_id}: {e}")
            return {
                "success": False,
                "error": f"Error guardando proyecto: {str(e)}"
            }
    
    def get_project_html(self, session_id: str) -> Optional[str]:
        """
        Obtiene el HTML de un proyecto guardado
        
        Args:
            session_id: ID de sesión
        
        Returns:
            Contenido HTML o None si no existe
        """
        session_dir = self._get_session_dir(session_id)
        html_path = os.path.join(session_dir, 'index.html')
        
        if os.path.exists(html_path):
            try:
                with open(html_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading project {session_id}: {e}")
                return None
        
        if session_id in self.sessions:
            return self.sessions[session_id].html_content
        
        return None
    
    def get_project_file(self, session_id: str, filename: str) -> Optional[str]:
        """
        Obtiene un archivo específico del proyecto
        
        Args:
            session_id: ID de sesión
            filename: Nombre del archivo
        
        Returns:
            Contenido del archivo o None
        """
        session_dir = self._get_session_dir(session_id)
        
        safe_filename = os.path.basename(filename)
        file_path = os.path.join(session_dir, safe_filename)
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading file {filename} in {session_id}: {e}")
                return None
        
        return None
    
    def list_projects(self) -> list:
        """Lista todos los proyectos generados"""
        projects = []
        
        if os.path.exists(self.projects_dir):
            for session_id in os.listdir(self.projects_dir):
                session_dir = os.path.join(self.projects_dir, session_id)
                if os.path.isdir(session_dir):
                    html_path = os.path.join(session_dir, 'index.html')
                    if os.path.exists(html_path):
                        projects.append({
                            "session_id": session_id,
                            "has_html": True,
                            "created": datetime.fromtimestamp(os.path.getctime(html_path)).isoformat()
                        })
        
        return projects
    
    def delete_project(self, session_id: str) -> Dict[str, Any]:
        """Elimina un proyecto"""
        import shutil
        
        session_dir = self._get_session_dir(session_id)
        
        if os.path.exists(session_dir):
            try:
                shutil.rmtree(session_dir)
                
                if session_id in self.sessions:
                    del self.sessions[session_id]
                
                return {"success": True, "message": f"Proyecto {session_id} eliminado"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Proyecto no encontrado"}


live_preview = LivePreviewGenerator()


def generate_preview(prompt: str, session_id: str = None) -> Dict[str, Any]:
    """Helper function para generar preview"""
    return live_preview.generate_with_fallback(prompt, session_id)


def get_preview_html(session_id: str) -> Optional[str]:
    """Helper function para obtener HTML"""
    return live_preview.get_project_html(session_id)
