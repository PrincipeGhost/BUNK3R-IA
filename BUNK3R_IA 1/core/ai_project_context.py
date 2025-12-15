"""
AI Project Context - Memory and context management for AI Constructor
Maintains project state between requests to provide continuity in AI interactions
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class AIProjectContext:
    """
    Maintains context of the project between AI requests.
    
    This allows the AI to remember:
    - Files created/modified during session
    - Commands executed
    - Errors found and fixed
    - Project structure and analysis
    """
    
    def __init__(self, user_id: str, project_id: str):
        self.user_id = user_id
        self.project_id = project_id
        self.session_start = datetime.now()
        
        self.project_info: Optional[Dict] = None
        self.file_tree: List[Dict] = []
        
        self.files_created: List[Dict] = []
        self.files_modified: List[Dict] = []
        self.files_deleted: List[Dict] = []
        self.commands_executed: List[Dict] = []
        self.errors_found: List[Dict] = []
        self.errors_fixed: List[Dict] = []
        self.packages_installed: List[Dict] = []
        
        self.conversation_history: List[Dict] = []
        self.current_task: Optional[Dict] = None
        self.pending_confirmations: List[Dict] = []
    
    def initialize(self, project_analyzer) -> bool:
        """
        Initialize context by analyzing the project.
        Should be called at the start of each session.
        """
        try:
            result = project_analyzer.analyze_project()
            if result.get('success'):
                self.project_info = result.get('analysis', {})
            
            list_result = project_analyzer.list_directory('.', recursive=False) if hasattr(project_analyzer, 'list_directory') else None
            if list_result and list_result.get('success'):
                self.file_tree = list_result.get('items', [])
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize context: {e}")
            return False
    
    def remember_file_created(self, path: str, content: str, description: str = ""):
        """Record that a file was created"""
        self.files_created.append({
            "path": path,
            "size": len(content),
            "description": description,
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"Context: File created - {path}")
    
    def remember_file_modified(self, path: str, change_description: str, diff: str = ""):
        """Record that a file was modified"""
        self.files_modified.append({
            "path": path,
            "change": change_description,
            "diff": diff[:500] if diff else "",
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"Context: File modified - {path}")
    
    def remember_file_deleted(self, path: str):
        """Record that a file was deleted"""
        self.files_deleted.append({
            "path": path,
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"Context: File deleted - {path}")
    
    def remember_command_executed(self, command: str, result: Dict):
        """Record a command that was executed"""
        self.commands_executed.append({
            "command": command,
            "success": result.get("success", False),
            "output": result.get("stdout", "")[:500],
            "exit_code": result.get("exit_code"),
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"Context: Command executed - {command}")
    
    def remember_error_found(self, error: Dict):
        """Record an error that was found"""
        self.errors_found.append({
            **error,
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"Context: Error found - {error.get('type', 'unknown')}")
    
    def remember_error_fixed(self, error: Dict, fix: Dict):
        """Record an error that was fixed"""
        self.errors_fixed.append({
            "error": error,
            "fix": fix,
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"Context: Error fixed - {error.get('type', 'unknown')}")
    
    def remember_package_installed(self, package: str, manager: str):
        """Record a package that was installed"""
        self.packages_installed.append({
            "package": package,
            "manager": manager,
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"Context: Package installed - {package} via {manager}")
    
    def add_conversation(self, role: str, message: str):
        """Add message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    def set_current_task(self, task_type: str, description: str, context: Optional[Dict] = None):
        """Set the current task being worked on"""
        self.current_task = {
            "type": task_type,
            "description": description,
            "context": context or {},
            "started_at": datetime.now().isoformat()
        }
    
    def clear_current_task(self):
        """Clear the current task"""
        self.current_task = None
    
    def add_pending_confirmation(self, confirmation_id: str, action: str, details: Dict):
        """Add a pending confirmation request"""
        self.pending_confirmations.append({
            "id": confirmation_id,
            "action": action,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def remove_pending_confirmation(self, confirmation_id: str):
        """Remove a confirmation after it's been handled"""
        self.pending_confirmations = [
            c for c in self.pending_confirmations 
            if c["id"] != confirmation_id
        ]
    
    def get_context_summary(self) -> str:
        """
        Generate context summary to include in AI prompts.
        This is passed to the AI so it understands the current state.
        """
        summary = f"""
================================================================
PROJECT CONTEXT
================================================================

PROJECT INFORMATION:
- Primary Language: {self.project_info.get('language', 'unknown') if self.project_info else 'unknown'}
- Framework: {self.project_info.get('framework', 'none') if self.project_info else 'none'}
- Entry Points: {', '.join(self.project_info.get('entry_points', [])) if self.project_info else 'unknown'}
- Database: {self.project_info.get('database', 'none') if self.project_info else 'none'}

SESSION ACTIVITY:
- Files created: {len(self.files_created)}
- Files modified: {len(self.files_modified)}
- Commands executed: {len(self.commands_executed)}
- Errors fixed: {len(self.errors_fixed)}
- Packages installed: {len(self.packages_installed)}
"""
        
        if self.files_created:
            summary += "\nFILES CREATED:\n"
            for f in self.files_created[-5:]:
                summary += f"  - {f['path']}: {f.get('description', '')}\n"
        
        if self.files_modified:
            summary += "\nFILES MODIFIED:\n"
            for f in self.files_modified[-5:]:
                summary += f"  - {f['path']}: {f['change']}\n"
        
        if self.packages_installed:
            summary += "\nPACKAGES INSTALLED:\n"
            for p in self.packages_installed:
                summary += f"  - {p['package']} ({p['manager']})\n"
        
        if self.errors_fixed:
            summary += "\nERRORS FIXED:\n"
            for e in self.errors_fixed[-3:]:
                error = e.get('error', {})
                summary += f"  - {error.get('type', 'Error')}: {error.get('message', '')[:50]}\n"
        
        if self.current_task:
            summary += f"\nCURRENT TASK:\n  - {self.current_task['type']}: {self.current_task['description']}\n"
        
        return summary
    
    def get_recent_conversation(self, limit: int = 10) -> List[Dict]:
        """Get the last N messages from conversation"""
        return self.conversation_history[-limit:]
    
    def get_session_stats(self) -> Dict:
        """Get statistics for the current session"""
        return {
            "session_start": self.session_start.isoformat(),
            "duration_minutes": (datetime.now() - self.session_start).seconds // 60,
            "files_created": len(self.files_created),
            "files_modified": len(self.files_modified),
            "files_deleted": len(self.files_deleted),
            "commands_executed": len(self.commands_executed),
            "errors_found": len(self.errors_found),
            "errors_fixed": len(self.errors_fixed),
            "packages_installed": len(self.packages_installed),
            "conversation_messages": len(self.conversation_history)
        }
    
    def to_dict(self) -> Dict:
        """Convert context to dictionary for serialization"""
        return {
            "user_id": self.user_id,
            "project_id": self.project_id,
            "session_start": self.session_start.isoformat(),
            "project_info": self.project_info,
            "file_tree": self.file_tree,
            "files_created": self.files_created,
            "files_modified": self.files_modified,
            "files_deleted": self.files_deleted,
            "commands_executed": self.commands_executed,
            "errors_found": self.errors_found,
            "errors_fixed": self.errors_fixed,
            "packages_installed": self.packages_installed,
            "conversation_history": self.conversation_history,
            "current_task": self.current_task,
            "pending_confirmations": self.pending_confirmations
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AIProjectContext':
        """Create context from dictionary"""
        context = cls(data.get('user_id', ''), data.get('project_id', ''))
        
        context.project_info = data.get('project_info')
        context.file_tree = data.get('file_tree', [])
        context.files_created = data.get('files_created', [])
        context.files_modified = data.get('files_modified', [])
        context.files_deleted = data.get('files_deleted', [])
        context.commands_executed = data.get('commands_executed', [])
        context.errors_found = data.get('errors_found', [])
        context.errors_fixed = data.get('errors_fixed', [])
        context.packages_installed = data.get('packages_installed', [])
        context.conversation_history = data.get('conversation_history', [])
        context.current_task = data.get('current_task')
        context.pending_confirmations = data.get('pending_confirmations', [])
        
        if data.get('session_start'):
            try:
                context.session_start = datetime.fromisoformat(data['session_start'])
            except:
                pass
        
        return context
    
    def save_to_file(self, filepath: str) -> bool:
        """Save context to JSON file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save context: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, filepath: str) -> Optional['AIProjectContext']:
        """Load context from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except FileNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Failed to load context: {e}")
            return None


class AIContextManager:
    """
    Manages multiple project contexts with caching and persistence.
    """
    
    def __init__(self, storage_dir: str = ".ai_context"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.contexts: Dict[str, AIProjectContext] = {}
    
    def _get_context_key(self, user_id: str, project_id: str) -> str:
        """Generate unique key for context"""
        return f"{user_id}_{project_id}"
    
    def _get_context_filepath(self, user_id: str, project_id: str) -> Path:
        """Get filepath for context storage"""
        return self.storage_dir / f"{self._get_context_key(user_id, project_id)}.json"
    
    def get_context(self, user_id: str, project_id: str, create_if_missing: bool = True) -> Optional[AIProjectContext]:
        """Get or create context for user/project"""
        key = self._get_context_key(user_id, project_id)
        
        if key in self.contexts:
            return self.contexts[key]
        
        filepath = self._get_context_filepath(user_id, project_id)
        context = AIProjectContext.load_from_file(str(filepath))
        
        if context is None and create_if_missing:
            context = AIProjectContext(user_id, project_id)
        
        if context:
            self.contexts[key] = context
        
        return context
    
    def save_context(self, context: AIProjectContext) -> bool:
        """Save context to storage"""
        filepath = self._get_context_filepath(context.user_id, context.project_id)
        return context.save_to_file(str(filepath))
    
    def save_all(self) -> int:
        """Save all contexts and return count of saved"""
        saved = 0
        for context in self.contexts.values():
            if self.save_context(context):
                saved += 1
        return saved
    
    def clear_context(self, user_id: str, project_id: str) -> bool:
        """Clear context for user/project"""
        key = self._get_context_key(user_id, project_id)
        
        if key in self.contexts:
            del self.contexts[key]
        
        filepath = self._get_context_filepath(user_id, project_id)
        try:
            if filepath.exists():
                filepath.unlink()
            return True
        except:
            return False
    
    def list_contexts(self) -> List[Dict]:
        """List all stored contexts"""
        contexts = []
        for filepath in self.storage_dir.glob("*.json"):
            try:
                context = AIProjectContext.load_from_file(str(filepath))
                if context:
                    contexts.append({
                        "user_id": context.user_id,
                        "project_id": context.project_id,
                        "session_start": context.session_start.isoformat(),
                        "stats": context.get_session_stats()
                    })
            except:
                pass
        return contexts
