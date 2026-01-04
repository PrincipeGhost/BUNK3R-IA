import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class ContextManager:
    """
    Manages the persistent memory of the AI session with sandbox isolation.
    Jails the AI within BUNK3R_IA/workspaces/{user_id}
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        # Define the base workspace for this user
        base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.user_workspace = base_dir / "workspaces" / user_id
        
        # Ensure workspace exists
        self.user_workspace.mkdir(parents=True, exist_ok=True)
        
        self.storage_path = self.user_workspace / "context_memory.json"
        self.state = self._load_from_disk()

    def _load_from_disk(self) -> Dict[str, Any]:
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading context for {self.user_id}: {e}")
        
        # Default state
        return {
            "metadata": {
                "session_id": f"bunk3r_{self.user_id}_{int(time.time())}",
                "last_active": "",
                "cwd": str(self.user_workspace)
            },
            "snapshot": {
                "open_files": [],
                "fs_tree_hash": ""
            },
            "history": {
                "command_log": [],
                "logical_intent": "Esperando repositorio...",
                "pending_tasks": []
            }
        }

    def save(self):
        self.state["metadata"]["last_active"] = datetime.now().isoformat()
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving context for {self.user_id}: {e}")

    def update_cwd(self, new_cwd: str) -> bool:
        """Updates CWD only if it's within the jailed user workspace."""
        new_path = Path(new_cwd).resolve()
        
        if self._is_within_jail(new_path):
            self.state["metadata"]["cwd"] = str(new_path)
            self.save()
            return True
        return False

    def _is_within_jail(self, path: Path) -> bool:
        """Checks if a path is inside the user's workspace."""
        try:
            return str(path.resolve()).startswith(str(self.user_workspace.resolve()))
        except Exception:
            return False

    def add_command(self, cmd: str, status: str, output_summary: str = ""):
        log = {
            "cmd": cmd,
            "status": status,
            "summary": output_summary[:200],
            "ts": datetime.now().isoformat()
        }
        self.state["history"]["command_log"].append(log)
        if len(self.state["history"]["command_log"]) > 10:
            self.state["history"]["command_log"] = self.state["history"]["command_log"][-10:]
        self.save()

    def update_intent(self, intent: str, pending_tasks: List[str] = None):
        self.state["history"]["logical_intent"] = intent
        if pending_tasks is not None:
            self.state["history"]["pending_tasks"] = pending_tasks
        self.save()

    def get_summarized_context(self) -> str:
        metadata = self.state["metadata"]
        history = self.state["history"]
        cwd = metadata['cwd']
        
        # Safety: If we're at root workspace, tell the IA to wait for a repo
        is_isolated = cwd != str(self.user_workspace)
        
        commands = "\n".join([f"- {c['cmd']} ({c['status']})" for c in history["command_log"]])
        
        context_str = f"""
[SISTEMA DE SEGURIDAD - SANDBOX]
Usuario: {self.user_id}
Directorio Actual (JAILED): {cwd}
Estado de Aislamiento: {"OPERATIVO EN REPOSITORIO" if is_isolated else "ROOT WORKSPACE (ESPERANDO REPOSITORIO)"}

[ESTADO DEL ARQUITECTO]
Objetivo Actual: {history['logical_intent']}
Tareas Pendientes: {', '.join(history['pending_tasks']) if history['pending_tasks'] else 'Ninguna'}

Historico de Terminal:
{commands if commands else "Ninguno"}
[NOTA: Tienes prohibido intentar acceder a directorios fuera de {self.user_workspace}]
"""
        return context_str
