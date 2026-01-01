import os
import re
import json
import logging
import subprocess
import shutil
import time
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class NervousSystem:
    """
    SISTEMA NERVIOSO (El Cuerpo): Unificación de todas las herramientas de ejecución.
    Maneja Archivos, Comandos, Búsqueda Web y Telemetría.
    
    Características Singulares:
    - Simulación Transparente (Sandbox Redirect).
    - Prevención de Errores Críticos (Safety Checks).
    - Monitoreo de Telemetría de Herramientas.
    """
    
    BLOCKED_PATHS = [
        '.env', '.git', '__pycache__', 'node_modules',
        '.replit', '.config', '.cache', '.local',
        'venv', '.venv', 'env', '.gemini'
    ]
    
    BLOCKED_EXTENSIONS = ['.pyc', '.pyo', '.so', '.dll', '.exe', '.bin']
    
    ALLOWED_COMMANDS = {
        'npm': ['install', 'run', 'init', 'list', 'start', 'build', 'test'],
        'pip': ['install', 'list', 'show', 'freeze'],
        'git': ['status', 'add', 'commit', 'push', 'pull', 'fetch', 'checkout', 'branch', 'log', 'diff', 'show'],
        'python': ['--version', '-m', 'pytest'],
        'pip3': ['install', 'list', 'show', 'freeze'],
        'ls': True, 'cat': True, 'mkdir': True, 'pwd': True, 'echo': True, 'grep': True, 'find': True
    }

    def __init__(self, project_root: str = None, sandbox_mode: bool = False):
        self.project_root = Path(project_root or os.getcwd()).resolve()
        self.sandbox_path = self.project_root / "sandbox"
        self.sandbox_mode = sandbox_mode
        self.telemetry = {"ops": 0, "errors": 0, "last_op": None}

    def _is_safe_path(self, path: str) -> Tuple[bool, str]:
        """Validación de seguridad para acceso a archivos."""
        try:
            full_path = (self.project_root / path).resolve()
            if not str(full_path).startswith(str(self.project_root)):
                return False, "Fuera del directorio del proyecto"
            
            parts = Path(path).parts
            if any(b in parts for b in self.BLOCKED_PATHS):
                return False, f"Acceso restringido a '{path}'"
            
            if full_path.suffix in self.BLOCKED_EXTENSIONS:
                return False, "Tipo de archivo bloqueado"
                
            return True, "OK"
        except Exception as e:
            return False, str(e)

    def _get_exec_path(self, path: str) -> str:
        """Reruta a sandbox si el modo simulación está activo."""
        if self.sandbox_mode:
            rel = os.path.relpath(path, self.project_root) if os.path.isabs(path) else path
            target = self.sandbox_path / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            return str(target)
        return str(self.project_root / path)

    # --- NÚCLEO ARQUIMEDES (ARCHIVOS) ---

    def read(self, path: str, max_lines: int = 2000) -> Dict:
        """Lectura segura de archivos."""
        safe, reason = self._is_safe_path(path)
        if not safe: return {"success": False, "error": reason}
        
        try:
            with open(self._get_exec_path(path), 'r', encoding='utf-8', errors='replace') as f:
                content = "".join([next(f, "") for _ in range(max_lines)])
            self.telemetry["ops"] += 1
            return {"success": True, "content": content, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def write(self, path: str, content: str) -> Dict:
        """Escritura proactiva con simulación."""
        safe, reason = self._is_safe_path(path)
        if not safe: return {"success": False, "error": reason}
        
        try:
            target = self._get_exec_path(path)
            Path(target).parent.mkdir(parents=True, exist_ok=True)
            with open(target, 'w', encoding='utf-8') as f:
                f.write(content)
            self.telemetry["ops"] += 1
            return {"success": True, "path": path, "simulated": self.sandbox_mode}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def list(self, path: str = ".", recursive: bool = False) -> Dict:
        """Exploración eficiente de directorios."""
        safe, reason = self._is_safe_path(path)
        if not safe: return {"success": False, "error": reason}
        
        try:
            root = Path(self._get_exec_path(path))
            items = []
            for item in root.iterdir():
                if any(b in item.name for b in self.BLOCKED_PATHS): continue
                items.append({
                    "name": item.name, 
                    "type": "dir" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0
                })
            return {"success": True, "items": sorted(items, key=lambda x: x["type"])}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # --- NÚCLEO VULCANO (COMANDOS) ---

    def execute(self, command: str, timeout: int = 60) -> Dict:
        """Ejecución de comandos con jaula de seguridad."""
        parts = command.split()
        if not parts: return {"success": False, "error": "Comando vacío"}
        
        base = parts[0].lower()
        if base not in self.ALLOWED_COMMANDS:
            return {"success": False, "error": f"Comando '{base}' no permitido"}
            
        try:
            start = time.time()
            res = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                cwd=self._get_exec_path("."), timeout=timeout
            )
            duration = time.time() - start
            self.telemetry["ops"] += 1
            
            return {
                "success": res.returncode == 0,
                "stdout": res.stdout[:50000], # Cap output
                "stderr": res.stderr[:50000],
                "duration": round(duration, 2),
                "code": res.returncode
            }
        except Exception as e:
            self.telemetry["errors"] += 1
            return {"success": False, "error": str(e)}

    # --- NÚCLEO MERCURIO (WEB/RESEARCH) ---

    def research(self, query: str) -> Dict:
        """Búsqueda web integrada para información de último minuto."""
        try:
            # Reutiliza el servicio existente pero unificado bajo Mercurio
            from BUNK3R_IA.core.legacy_v1_archive.web_search_service import web_search_service
            res = web_search_service.search_sync(query)
            return {"success": True, "results": res.to_dict()["results"][:5]}
        except Exception as e:
            return {"success": False, "error": str(e)}

# El Cuerpo Único listo para la Singularidad
nervous_system = NervousSystem()
