import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

class ContextManager:
    """
    Manages the persistent memory of the AI session.
    Ensures that context (CWD, command history, goals) is preserved
    even when switching between AI models or during multi-worker restarts.
    """
    
    def __init__(self, storage_path: str = "context_memory.json"):
        self.storage_path = storage_path
        self.state = self._load_from_disk()

    def _load_from_disk(self) -> Dict[str, Any]:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading context: {e}")
        
        return {
            "metadata": {
                "session_id": f"bunk3r_{int(time.time())}",
                "last_active": "",
                "cwd": os.getcwd()
            },
            "snapshot": {
                "open_files": [],
                "fs_tree_hash": ""
            },
            "history": {
                "command_log": [],
                "logical_intent": "Inicializando proyecto...",
                "pending_tasks": []
            }
        }

    def save(self):
        self.state["metadata"]["last_active"] = datetime.now().isoformat()
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving context: {e}")

    def update_cwd(self, new_cwd: str):
        self.state["metadata"]["cwd"] = new_cwd
        self.save()

    def add_command(self, cmd: str, status: str, output_summary: str = ""):
        log = {
            "cmd": cmd,
            "status": status,
            "summary": output_summary[:200], # Keep it light
            "ts": datetime.now().isoformat()
        }
        self.state["history"]["command_log"].append(log)
        # Keep only last 10 commands for context buffer
        if len(self.state["history"]["command_log"]) > 10:
            self.state["history"]["command_log"] = self.state["history"]["command_log"][-10:]
        self.save()

    def update_intent(self, intent: str, pending_tasks: List[str] = None):
        self.state["history"]["logical_intent"] = intent
        if pending_tasks is not None:
            self.state["history"]["pending_tasks"] = pending_tasks
        self.save()

    def get_summarized_context(self) -> str:
        """Returns a string formatted for insertion into a System Prompt."""
        metadata = self.state["metadata"]
        history = self.state["history"]
        
        commands = "\n".join([f"- {c['cmd']} ({c['status']})" for c in history["command_log"]])
        
        context_str = f"""
[ESTADO DEL ARQUITECTO - PERSISTENCIA]
Directorio Actual: {metadata['cwd']}
Objetivo Actual: {history['logical_intent']}
Tareas Pendientes: {', '.join(history['pending_tasks']) if history['pending_tasks'] else 'Ninguna'}

Últimos Comandos Ejecutados:
{commands if commands else "Ninguno aún"}
[FIN DEL CONTEXTO]
"""
        return context_str
