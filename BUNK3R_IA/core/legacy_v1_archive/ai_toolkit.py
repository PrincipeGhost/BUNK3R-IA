"""
AI Toolkit - File operations, command execution, error detection for AI Constructor
Provides secure tools for the AI to interact with the file system and execute commands
"""

import os
import re
import json
import logging
import subprocess
import shutil
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class AIFileToolkit:
    """
    Secure file operations toolkit for AI Constructor.
    All operations are restricted to the project root directory.
    """
    
    BLOCKED_PATHS = [
        '.env', '.git', '__pycache__', 'node_modules',
        '.replit', '.config', '.cache', '.local',
        'venv', '.venv', 'env'
    ]
    
    BLOCKED_EXTENSIONS = ['.pyc', '.pyo', '.so', '.dll', '.exe', '.bin']
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB max file size
    MAX_READ_LINES = 5000
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.operations_log: List[Dict] = []
    
    def _is_safe_path(self, path: str) -> Tuple[bool, str]:
        """Check if path is safe to access (within project root and not blocked)"""
        try:
            full_path = (self.project_root / path).resolve()
            
            if not str(full_path).startswith(str(self.project_root.resolve())):
                return False, "Path is outside project directory"
            
            path_parts = Path(path).parts
            for blocked in self.BLOCKED_PATHS:
                if blocked in path_parts:
                    return False, f"Access to '{blocked}' is blocked"
            
            if full_path.suffix in self.BLOCKED_EXTENSIONS:
                return False, f"File type '{full_path.suffix}' is blocked"
            
            return True, "OK"
        except Exception as e:
            return False, str(e)
    
    def _log_operation(self, operation: str, path: str, success: bool, details: Optional[str] = None):
        """Log file operation for audit"""
        self.operations_log.append({
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'path': path,
            'success': success,
            'details': details
        })
        logger.info(f"AIToolkit: {operation} {path} - {'SUCCESS' if success else 'FAILED'}: {details}")
    
    def read_file(self, path: str, max_lines: Optional[int] = None) -> Dict[str, Any]:
        """Read file content with line limit"""
        safe, reason = self._is_safe_path(path)
        if not safe:
            self._log_operation('read_file', path, False, reason)
            return {'success': False, 'error': reason}
        
        try:
            full_path = self.project_root / path
            
            if not full_path.exists():
                self._log_operation('read_file', path, False, "File not found")
                return {'success': False, 'error': 'File not found'}
            
            if not full_path.is_file():
                self._log_operation('read_file', path, False, "Not a file")
                return {'success': False, 'error': 'Not a file'}
            
            file_size = full_path.stat().st_size
            if file_size > self.MAX_FILE_SIZE:
                self._log_operation('read_file', path, False, "File too large")
                return {'success': False, 'error': f'File too large ({file_size} bytes)'}
            
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                if max_lines or self.MAX_READ_LINES:
                    lines = []
                    limit = max_lines or self.MAX_READ_LINES
                    line_count = 0
                    for line_count, line in enumerate(f):
                        if line_count >= limit:
                            break
                        lines.append(line)
                    content = ''.join(lines)
                    truncated = line_count >= limit
                else:
                    content = f.read()
                    truncated = False
            
            self._log_operation('read_file', path, True, f"{len(content)} chars")
            return {
                'success': True,
                'content': content,
                'path': path,
                'size': file_size,
                'truncated': truncated
            }
        except Exception as e:
            self._log_operation('read_file', path, False, str(e))
            return {'success': False, 'error': str(e)}
    
    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Create or overwrite file"""
        safe, reason = self._is_safe_path(path)
        if not safe:
            self._log_operation('write_file', path, False, reason)
            return {'success': False, 'error': reason}
        
        try:
            full_path = self.project_root / path
            
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self._log_operation('write_file', path, True, f"{len(content)} chars")
            return {
                'success': True,
                'path': path,
                'size': len(content),
                'created': True
            }
        except Exception as e:
            self._log_operation('write_file', path, False, str(e))
            return {'success': False, 'error': str(e)}
    
    def edit_file(self, path: str, old_content: str, new_content: str) -> Dict[str, Any]:
        """Edit file by replacing old content with new content"""
        safe, reason = self._is_safe_path(path)
        if not safe:
            self._log_operation('edit_file', path, False, reason)
            return {'success': False, 'error': reason}
        
        try:
            full_path = self.project_root / path
            
            if not full_path.exists():
                self._log_operation('edit_file', path, False, "File not found")
                return {'success': False, 'error': 'File not found'}
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if old_content not in content:
                self._log_operation('edit_file', path, False, "Old content not found")
                return {'success': False, 'error': 'Old content not found in file'}
            
            count = content.count(old_content)
            if count > 1:
                self._log_operation('edit_file', path, False, f"Multiple matches ({count})")
                return {'success': False, 'error': f'Multiple matches found ({count}). Be more specific.'}
            
            new_file_content = content.replace(old_content, new_content, 1)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_file_content)
            
            self._log_operation('edit_file', path, True, f"Replaced {len(old_content)} chars")
            return {
                'success': True,
                'path': path,
                'replaced': True,
                'old_size': len(old_content),
                'new_size': len(new_content)
            }
        except Exception as e:
            self._log_operation('edit_file', path, False, str(e))
            return {'success': False, 'error': str(e)}
    
    def append_file(self, path: str, content: str) -> Dict[str, Any]:
        """Append content to end of file"""
        safe, reason = self._is_safe_path(path)
        if not safe:
            self._log_operation('append_file', path, False, reason)
            return {'success': False, 'error': reason}
        
        try:
            full_path = self.project_root / path
            
            if not full_path.exists():
                self._log_operation('append_file', path, False, "File not found")
                return {'success': False, 'error': 'File not found'}
            
            with open(full_path, 'a', encoding='utf-8') as f:
                f.write(content)
            
            self._log_operation('append_file', path, True, f"{len(content)} chars appended")
            return {
                'success': True,
                'path': path,
                'appended': len(content)
            }
        except Exception as e:
            self._log_operation('append_file', path, False, str(e))
            return {'success': False, 'error': str(e)}
    
    def delete_file(self, path: str, confirm: bool = False) -> Dict[str, Any]:
        """Delete file (requires confirmation)"""
        if not confirm:
            return {
                'success': False,
                'error': 'Deletion requires explicit confirmation',
                'requires_confirm': True
            }
        
        safe, reason = self._is_safe_path(path)
        if not safe:
            self._log_operation('delete_file', path, False, reason)
            return {'success': False, 'error': reason}
        
        try:
            full_path = self.project_root / path
            
            if not full_path.exists():
                self._log_operation('delete_file', path, False, "File not found")
                return {'success': False, 'error': 'File not found'}
            
            if full_path.is_dir():
                shutil.rmtree(full_path)
            else:
                full_path.unlink()
            
            self._log_operation('delete_file', path, True, "Deleted")
            return {'success': True, 'path': path, 'deleted': True}
        except Exception as e:
            self._log_operation('delete_file', path, False, str(e))
            return {'success': False, 'error': str(e)}
    
    def list_directory(self, path: str = '.', recursive: bool = False, max_depth: int = 3) -> Dict[str, Any]:
        """List directory contents"""
        safe, reason = self._is_safe_path(path)
        if not safe:
            self._log_operation('list_directory', path, False, reason)
            return {'success': False, 'error': reason}
        
        try:
            full_path = self.project_root / path
            
            if not full_path.exists():
                self._log_operation('list_directory', path, False, "Directory not found")
                return {'success': False, 'error': 'Directory not found'}
            
            if not full_path.is_dir():
                self._log_operation('list_directory', path, False, "Not a directory")
                return {'success': False, 'error': 'Not a directory'}
            
            items = []
            
            def scan_dir(dir_path: Path, depth: int = 0):
                if depth > max_depth:
                    return
                
                try:
                    for item in sorted(dir_path.iterdir()):
                        rel_path = item.relative_to(self.project_root)
                        
                        skip = False
                        for blocked in self.BLOCKED_PATHS:
                            if blocked in rel_path.parts:
                                skip = True
                                break
                        if skip:
                            continue
                        
                        item_info = {
                            'name': item.name,
                            'path': str(rel_path),
                            'type': 'directory' if item.is_dir() else 'file',
                            'size': item.stat().st_size if item.is_file() else None
                        }
                        items.append(item_info)
                        
                        if recursive and item.is_dir():
                            scan_dir(item, depth + 1)
                except PermissionError:
                    pass
            
            scan_dir(full_path)
            
            self._log_operation('list_directory', path, True, f"{len(items)} items")
            return {
                'success': True,
                'path': path,
                'items': items,
                'count': len(items)
            }
        except Exception as e:
            self._log_operation('list_directory', path, False, str(e))
            return {'success': False, 'error': str(e)}
    
    def search_code(self, query: str, path: str = '.', file_pattern: Optional[str] = None) -> Dict[str, Any]:
        """Search for text/pattern in code files"""
        safe, reason = self._is_safe_path(path)
        if not safe:
            self._log_operation('search_code', path, False, reason)
            return {'success': False, 'error': reason}
        
        try:
            full_path = self.project_root / path
            
            if not full_path.exists():
                return {'success': False, 'error': 'Path not found'}
            
            matches = []
            code_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', 
                             '.json', '.yaml', '.yml', '.md', '.txt', '.sql']
            
            try:
                pattern = re.compile(query, re.IGNORECASE)
            except re.error:
                pattern = re.compile(re.escape(query), re.IGNORECASE)
            
            def search_file(file_path: Path):
                try:
                    if file_path.suffix not in code_extensions:
                        return
                    
                    if file_path.stat().st_size > 1024 * 1024:  # Skip files > 1MB
                        return
                    
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        for line_num, line in enumerate(f, 1):
                            if pattern.search(line):
                                rel_path = file_path.relative_to(self.project_root)
                                matches.append({
                                    'file': str(rel_path),
                                    'line': line_num,
                                    'content': line.strip()[:200]
                                })
                                if len(matches) >= 100:  # Limit results
                                    return
                except Exception:
                    pass
            
            if full_path.is_file():
                search_file(full_path)
            else:
                for root, dirs, files in os.walk(full_path):
                    dirs[:] = [d for d in dirs if d not in self.BLOCKED_PATHS]
                    
                    for file in files:
                        if file_pattern:
                            if not Path(file).match(file_pattern):
                                continue
                        search_file(Path(root) / file)
                        
                        if len(matches) >= 100:
                            break
            
            self._log_operation('search_code', query, True, f"{len(matches)} matches")
            return {
                'success': True,
                'query': query,
                'matches': matches,
                'count': len(matches),
                'truncated': len(matches) >= 100
            }
        except Exception as e:
            self._log_operation('search_code', query, False, str(e))
            return {'success': False, 'error': str(e)}
    
    def create_directory(self, path: str) -> Dict[str, Any]:
        """Create directory"""
        safe, reason = self._is_safe_path(path)
        if not safe:
            self._log_operation('create_directory', path, False, reason)
            return {'success': False, 'error': reason}
        
        try:
            full_path = self.project_root / path
            full_path.mkdir(parents=True, exist_ok=True)
            
            self._log_operation('create_directory', path, True, "Created")
            return {'success': True, 'path': path, 'created': True}
        except Exception as e:
            self._log_operation('create_directory', path, False, str(e))
            return {'success': False, 'error': str(e)}
    
    def move_file(self, old_path: str, new_path: str) -> Dict[str, Any]:
        """Move or rename file"""
        safe1, reason1 = self._is_safe_path(old_path)
        safe2, reason2 = self._is_safe_path(new_path)
        
        if not safe1:
            return {'success': False, 'error': f'Source: {reason1}'}
        if not safe2:
            return {'success': False, 'error': f'Destination: {reason2}'}
        
        try:
            old_full = self.project_root / old_path
            new_full = self.project_root / new_path
            
            if not old_full.exists():
                return {'success': False, 'error': 'Source file not found'}
            
            new_full.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(old_full), str(new_full))
            
            self._log_operation('move_file', f"{old_path} -> {new_path}", True, "Moved")
            return {
                'success': True,
                'old_path': old_path,
                'new_path': new_path,
                'moved': True
            }
        except Exception as e:
            self._log_operation('move_file', old_path, False, str(e))
            return {'success': False, 'error': str(e)}
    
    def get_file_info(self, path: str) -> Dict[str, Any]:
        """Get file metadata"""
        safe, reason = self._is_safe_path(path)
        if not safe:
            return {'success': False, 'error': reason}
        
        try:
            full_path = self.project_root / path
            
            if not full_path.exists():
                return {'success': False, 'error': 'File not found'}
            
            stat = full_path.stat()
            return {
                'success': True,
                'path': path,
                'name': full_path.name,
                'type': 'directory' if full_path.is_dir() else 'file',
                'size': stat.st_size,
                'extension': full_path.suffix,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_operations_log(self) -> List[Dict]:
        """Get log of all operations performed"""
        return self.operations_log.copy()


class AICommandExecutor:
    """
    Secure command execution for AI Constructor.
    Only whitelisted commands are allowed.
    """
    
    ALLOWED_COMMANDS = {
        'npm': ['install', 'run', 'init', 'list', 'start', 'build', 'test'],
        'pip': ['install', 'list', 'show', 'freeze'],
        'pip3': ['install', 'list', 'show', 'freeze'],
        'ls': True,
        'cat': True,
        'head': True,
        'tail': True,
        'mkdir': True,
        'touch': True,
        'pwd': True,
        'echo': True,
        'grep': True,
        'find': True,
        'wc': True,
        'git': ['status', 'log', 'diff', 'branch', 'show'],
    }
    
    SCRIPT_ALLOWED_EXTENSIONS = ['.py', '.js', '.ts']
    
    BLOCKED_PATTERNS = [
        r'rm\s+-rf',
        r'rm\s+-r\s+/',
        r'rm\s+/',
        r'sudo',
        r'chmod\s+777',
        r'curl.*\|.*bash',
        r'wget.*\|.*sh',
        r'eval\s*\(',
        r'exec\s*\(',
        r'>\s*/dev/',
        r'mkfs',
        r'dd\s+if=',
        r':\(\)\s*{\s*:\|:&\s*}',  # Fork bomb
        r'shutdown',
        r'reboot',
        r'kill\s+-9\s+1',
        r'python\s+-c',  # Block inline Python code
        r'python3\s+-c',
        r'node\s+-e',  # Block inline Node code
        r'python\s+.*\|',  # Block piping to Python
        r'python3\s+.*\|',
        r'node\s+.*\|',
        r'import\s+os.*system',  # Block os.system in inline
        r'subprocess',  # Block subprocess in inline
        r'__import__',  # Block dynamic imports
    ]
    
    DEFAULT_TIMEOUT = 30  # seconds
    MAX_TIMEOUT = 300  # 5 minutes max
    MAX_OUTPUT_SIZE = 100 * 1024  # 100KB
    
    def __init__(self, working_dir: Optional[str] = None):
        self.working_dir = working_dir or os.getcwd()
        self.execution_log: List[Dict] = []
    
    def _is_command_allowed(self, command: str) -> Tuple[bool, str]:
        """Check if command is in whitelist and not in blacklist"""
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"Blocked pattern detected: {pattern}"
        
        parts = command.strip().split()
        if not parts:
            return False, "Empty command"
        
        base_cmd = parts[0]
        
        if base_cmd not in self.ALLOWED_COMMANDS:
            return False, f"Command '{base_cmd}' is not whitelisted"
        
        allowed = self.ALLOWED_COMMANDS[base_cmd]
        
        if allowed is True:
            return True, "OK"
        
        if isinstance(allowed, list) and len(parts) > 1:
            subcommand = parts[1]
            if subcommand not in allowed:
                return False, f"Subcommand '{subcommand}' is not allowed for '{base_cmd}'"
            
            # Validar paquetes en comandos pip/npm install contra whitelist
            if subcommand == 'install' and len(parts) > 2:
                package_name = parts[2].lower()
                # Remover versión si existe (ej: flask==2.0.0 -> flask)
                package_name = re.sub(r'[=<>@].*', '', package_name)
                
                if base_cmd in ['pip', 'pip3']:
                    if package_name not in self.SAFE_PYTHON_PACKAGES:
                        return False, f"Package '{package_name}' not in Python whitelist (use install_package method)"
                elif base_cmd == 'npm':
                    if package_name not in self.SAFE_NODE_PACKAGES:
                        return False, f"Package '{package_name}' not in Node whitelist (use install_package method)"
        
        return True, "OK"
    
    def _log_execution(self, command: str, success: bool, exit_code: Optional[int] = None, 
                       output: Optional[str] = None, error: Optional[str] = None, duration: Optional[float] = None):
        """Log command execution"""
        self.execution_log.append({
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'success': success,
            'exit_code': exit_code,
            'output_size': len(output) if output else 0,
            'error_size': len(error) if error else 0,
            'duration': duration
        })
        logger.info(f"AICommandExecutor: {command} - {'SUCCESS' if success else 'FAILED'} (exit: {exit_code})")
    
    def run_command(self, command: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Execute command with security checks and timeout"""
        allowed, reason = self._is_command_allowed(command)
        if not allowed:
            self._log_execution(command, False, error=reason)
            return {'success': False, 'error': reason, 'blocked': True}
        
        timeout = min(timeout or self.DEFAULT_TIMEOUT, self.MAX_TIMEOUT)
        
        try:
            import time
            start_time = time.time()
            
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
            )
            
            duration = time.time() - start_time
            
            stdout = result.stdout
            stderr = result.stderr
            
            if len(stdout) > self.MAX_OUTPUT_SIZE:
                stdout = stdout[:self.MAX_OUTPUT_SIZE] + "\n... (output truncated)"
            if len(stderr) > self.MAX_OUTPUT_SIZE:
                stderr = stderr[:self.MAX_OUTPUT_SIZE] + "\n... (output truncated)"
            
            success = result.returncode == 0
            self._log_execution(command, success, result.returncode, stdout, stderr, duration)
            
            return {
                'success': success,
                'command': command,
                'exit_code': result.returncode,
                'stdout': stdout,
                'stderr': stderr,
                'duration': duration
            }
        except subprocess.TimeoutExpired:
            self._log_execution(command, False, error="Timeout")
            return {
                'success': False,
                'error': f'Command timed out after {timeout} seconds',
                'timeout': True
            }
        except Exception as e:
            self._log_execution(command, False, error=str(e))
            return {'success': False, 'error': str(e)}
    
    # Lista blanca de paquetes seguros para instalación automática
    SAFE_PYTHON_PACKAGES = {
        'flask', 'requests', 'beautifulsoup4', 'pillow', 'pandas', 'numpy',
        'matplotlib', 'jinja2', 'werkzeug', 'gunicorn', 'pytest', 'click',
        'pyyaml', 'python-dotenv', 'sqlalchemy', 'aiohttp', 'httpx', 'fastapi',
        'uvicorn', 'psycopg2-binary', 'redis', 'celery'
    }
    SAFE_NODE_PACKAGES = {
        'express', 'react', 'vue', 'axios', 'lodash', 'moment', 'dayjs',
        'tailwindcss', 'postcss', 'autoprefixer', 'vite', 'webpack',
        'typescript', 'eslint', 'prettier', 'jest', 'nodemon', 'cors'
    }
    
    def install_package(self, package: str, manager: str = 'pip', force_allow: bool = False) -> Dict[str, Any]:
        """Install package using npm or pip (only whitelisted packages allowed)"""
        # Sanitizar nombre de paquete
        package = re.sub(r'[;&|`$<>(){}[\]\'"]', '', package).strip()
        
        # Validar solo caracteres alfanuméricos, guiones y puntos
        if not re.match(r'^[a-zA-Z0-9_\-.]+$', package):
            return {'success': False, 'error': f'Invalid package name: {package}', 'blocked': True}
        
        # Verificar contra lista blanca (a menos que force_allow=True)
        if not force_allow:
            if manager == 'npm':
                if package.lower() not in self.SAFE_NODE_PACKAGES:
                    return {'success': False, 'error': f'Package not in whitelist: {package}', 'blocked': True, 'requires_manual': True}
            elif manager in ['pip', 'pip3']:
                if package.lower() not in self.SAFE_PYTHON_PACKAGES:
                    return {'success': False, 'error': f'Package not in whitelist: {package}', 'blocked': True, 'requires_manual': True}
        
        if manager == 'npm':
            command = f'npm install {package}'
        elif manager in ['pip', 'pip3']:
            command = f'{manager} install {package}'
        else:
            return {'success': False, 'error': f'Unknown package manager: {manager}'}
        
        return self.run_command(command, timeout=120)
    
    def run_script(self, script_path: str, interpreter: str = 'python') -> Dict[str, Any]:
        """Run a script file (with strict validation)"""
        script_path = script_path.strip()
        
        if '..' in script_path or script_path.startswith('/'):
            return {'success': False, 'error': 'Invalid script path'}
        
        full_path = os.path.join(self.working_dir, script_path)
        if not os.path.exists(full_path):
            return {'success': False, 'error': 'Script not found'}
        
        if not os.path.isfile(full_path):
            return {'success': False, 'error': 'Path is not a file'}
        
        ext = os.path.splitext(script_path)[1].lower()
        if ext not in self.SCRIPT_ALLOWED_EXTENSIONS:
            return {'success': False, 'error': f'Script extension not allowed: {ext}'}
        
        if interpreter not in ['python', 'python3', 'node']:
            return {'success': False, 'error': f'Interpreter not allowed: {interpreter}'}
        
        if interpreter in ['python', 'python3'] and ext != '.py':
            return {'success': False, 'error': 'Python interpreter requires .py file'}
        if interpreter == 'node' and ext not in ['.js', '.ts']:
            return {'success': False, 'error': 'Node interpreter requires .js or .ts file'}
        
        try:
            import time
            start_time = time.time()
            
            result = subprocess.run(
                [interpreter, script_path],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=60,
                env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
            )
            
            duration = time.time() - start_time
            command = f'{interpreter} {script_path}'
            
            stdout = result.stdout
            stderr = result.stderr
            
            if len(stdout) > self.MAX_OUTPUT_SIZE:
                stdout = stdout[:self.MAX_OUTPUT_SIZE] + "\n... (output truncated)"
            if len(stderr) > self.MAX_OUTPUT_SIZE:
                stderr = stderr[:self.MAX_OUTPUT_SIZE] + "\n... (output truncated)"
            
            success = result.returncode == 0
            self._log_execution(command, success, result.returncode, stdout, stderr, duration)
            
            return {
                'success': success,
                'command': command,
                'exit_code': result.returncode,
                'stdout': stdout,
                'stderr': stderr,
                'duration': duration
            }
        except subprocess.TimeoutExpired:
            self._log_execution(f'{interpreter} {script_path}', False, error="Timeout")
            return {'success': False, 'error': 'Script timed out after 60 seconds', 'timeout': True}
        except Exception as e:
            self._log_execution(f'{interpreter} {script_path}', False, error=str(e))
            return {'success': False, 'error': str(e)}
    
    def get_execution_log(self) -> List[Dict]:
        """Get log of all command executions"""
        return self.execution_log.copy()


class AIErrorDetector:
    """
    Error detection and analysis for AI Constructor.
    Detects errors in logs and suggests fixes.
    """
    
    ERROR_PATTERNS = {
        'python': [
            (r"ModuleNotFoundError: No module named '(\w+)'", 'missing_module'),
            (r"ImportError: cannot import name '(\w+)'", 'import_error'),
            (r"SyntaxError: (.+)", 'syntax_error'),
            (r"IndentationError: (.+)", 'indentation_error'),
            (r"TypeError: (.+)", 'type_error'),
            (r"NameError: name '(\w+)' is not defined", 'name_error'),
            (r"AttributeError: (.+)", 'attribute_error'),
            (r"KeyError: (.+)", 'key_error'),
            (r"ValueError: (.+)", 'value_error'),
            (r"FileNotFoundError: (.+)", 'file_not_found'),
            (r"ZeroDivisionError", 'zero_division'),
            (r"RecursionError", 'recursion_error'),
        ],
        'node': [
            (r"Error: Cannot find module '([^']+)'", 'missing_module'),
            (r"SyntaxError: (.+)", 'syntax_error'),
            (r"TypeError: (.+)", 'type_error'),
            (r"ReferenceError: (\w+) is not defined", 'reference_error'),
            (r"RangeError: (.+)", 'range_error'),
            (r"Error: ENOENT: no such file or directory", 'file_not_found'),
        ],
        'general': [
            (r"error:?\s*(.+)", 'general_error'),
            (r"Error:?\s*(.+)", 'general_error'),
            (r"ERROR:?\s*(.+)", 'general_error'),
            (r"failed:?\s*(.+)", 'failure'),
            (r"FAILED:?\s*(.+)", 'failure'),
            (r"exception:?\s*(.+)", 'exception'),
        ]
    }
    
    FIX_SUGGESTIONS = {
        'missing_module': "Install the missing module using: pip install {0} or npm install {0}",
        'import_error': "Check if the module/function exists and is spelled correctly",
        'syntax_error': "Check for missing colons, brackets, or quotes near the error",
        'indentation_error': "Fix the indentation - Python uses 4 spaces",
        'type_error': "Check that you're using the correct data types for the operation",
        'name_error': "Variable '{0}' is not defined. Check spelling or define it first",
        'attribute_error': "Object doesn't have the attribute. Check spelling or object type",
        'key_error': "Key doesn't exist in dictionary. Use .get() or check key exists",
        'value_error': "Invalid value. Check input data and expected format",
        'file_not_found': "File doesn't exist. Check the path is correct",
        'reference_error': "Variable '{0}' is not defined. Define it before use",
    }
    
    def __init__(self):
        self.detected_errors: List[Dict] = []
    
    def read_server_logs(self, log_file: Optional[str] = None, lines: int = 100) -> Dict[str, Any]:
        """Read server logs"""
        try:
            log_content = []
            
            if log_file and os.path.exists(log_file):
                with open(log_file, 'r', errors='replace') as f:
                    log_content = f.readlines()[-lines:]
            else:
                import subprocess
                result = subprocess.run(
                    ['tail', '-n', str(lines), '/tmp/server.log'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    log_content = result.stdout.split('\n')
            
            return {
                'success': True,
                'logs': log_content,
                'count': len(log_content)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def detect_errors(self, logs: List[str], language: str = 'python') -> Dict[str, Any]:
        """Detect errors in log content"""
        errors = []
        
        patterns = self.ERROR_PATTERNS.get(language, []) + self.ERROR_PATTERNS.get('general', [])
        
        for i, line in enumerate(logs):
            for pattern, error_type in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    errors.append({
                        'line_number': i + 1,
                        'line': line.strip(),
                        'error_type': error_type,
                        'match': match.group(1) if match.groups() else match.group(0),
                        'language': language
                    })
                    break
        
        self.detected_errors.extend(errors)
        
        return {
            'success': True,
            'errors': errors,
            'count': len(errors)
        }
    
    def analyze_error(self, error: Dict) -> Dict[str, Any]:
        """Analyze error and provide insights"""
        error_type = error.get('error_type', 'unknown')
        match_value = error.get('match', '')
        
        suggestion = self.FIX_SUGGESTIONS.get(
            error_type,
            "Check the error message for more details"
        )
        
        if '{0}' in suggestion:
            suggestion = suggestion.format(match_value)
        
        analysis = {
            'error_type': error_type,
            'severity': self._get_severity(error_type),
            'suggestion': suggestion,
            'category': self._get_category(error_type),
            'quick_fix_available': error_type in ['missing_module', 'indentation_error']
        }
        
        return {'success': True, 'analysis': analysis}
    
    def _get_severity(self, error_type: str) -> str:
        """Get error severity level"""
        critical = ['syntax_error', 'indentation_error', 'missing_module']
        high = ['import_error', 'file_not_found', 'reference_error']
        medium = ['type_error', 'attribute_error', 'key_error', 'name_error']
        
        if error_type in critical:
            return 'critical'
        elif error_type in high:
            return 'high'
        elif error_type in medium:
            return 'medium'
        return 'low'
    
    def _get_category(self, error_type: str) -> str:
        """Categorize error type"""
        if error_type in ['syntax_error', 'indentation_error']:
            return 'syntax'
        elif error_type in ['missing_module', 'import_error']:
            return 'dependency'
        elif error_type in ['type_error', 'value_error', 'attribute_error']:
            return 'type'
        elif error_type in ['file_not_found']:
            return 'filesystem'
        return 'runtime'
    
    def suggest_fix(self, error: Dict) -> Dict[str, Any]:
        """Suggest fix for error"""
        error_type = error.get('error_type')
        match_value = error.get('match', '')
        
        fixes = []
        
        if error_type == 'missing_module':
            module_name = match_value
            fixes.append({
                'type': 'install',
                'command': f'pip install {module_name}',
                'description': f"Install the missing Python module '{module_name}'"
            })
            fixes.append({
                'type': 'install',
                'command': f'npm install {module_name}',
                'description': f"Install the missing Node module '{module_name}'"
            })
        
        elif error_type == 'indentation_error':
            fixes.append({
                'type': 'code_fix',
                'description': "Convert tabs to 4 spaces and ensure consistent indentation"
            })
        
        elif error_type == 'name_error':
            fixes.append({
                'type': 'code_fix',
                'description': f"Define variable '{match_value}' before using it, or check spelling"
            })
        
        return {
            'success': True,
            'error': error,
            'fixes': fixes,
            'auto_fixable': error_type in ['missing_module']
        }
    
    def get_detected_errors(self) -> List[Dict]:
        """Get all detected errors"""
        return self.detected_errors.copy()
    
    def clear_errors(self):
        """Clear detected errors history"""
        self.detected_errors = []


class AIProjectAnalyzer:
    """
    Project structure analyzer for AI Constructor.
    Understands project layout, frameworks, and dependencies.
    """
    
    FRAMEWORK_INDICATORS = {
        'flask': ['app.py', 'flask', 'Flask'],
        'django': ['manage.py', 'django', 'Django'],
        'fastapi': ['fastapi', 'FastAPI'],
        'express': ['express', 'app.js', 'server.js'],
        'react': ['react', 'React', 'jsx', 'tsx'],
        'vue': ['vue', 'Vue', '.vue'],
        'angular': ['angular', '@angular'],
        'nextjs': ['next', 'Next.js', '_app.js'],
        'streamlit': ['streamlit', 'st.'],
    }
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
    
    def analyze_project(self) -> Dict[str, Any]:
        """Perform full project analysis"""
        try:
            analysis = {
                'language': self._detect_language(),
                'framework': self._detect_framework(),
                'dependencies': self._get_dependencies(),
                'structure': self._map_structure(),
                'entry_points': self._find_entry_points(),
                'database': self._detect_database(),
                'has_tests': self._has_tests(),
                'file_count': self._count_files(),
            }
            
            return {'success': True, 'analysis': analysis}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _detect_language(self) -> str:
        """Detect primary programming language"""
        extensions = {}
        
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'venv', '.venv']]
            
            for f in files:
                ext = Path(f).suffix.lower()
                if ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.rb', '.php']:
                    extensions[ext] = extensions.get(ext, 0) + 1
        
        if not extensions:
            return 'unknown'
        
        primary = max(extensions, key=lambda x: extensions.get(x, 0))
        
        lang_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php'
        }
        
        return lang_map.get(primary, 'unknown')
    
    def _detect_framework(self) -> Optional[str]:
        """Detect web framework in use"""
        files_to_check = []
        
        for f in ['app.py', 'main.py', 'server.py', 'index.js', 'app.js', 'package.json', 'requirements.txt']:
            path = self.project_root / f
            if path.exists():
                files_to_check.append(path)
        
        for file_path in files_to_check:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                
                for framework, indicators in self.FRAMEWORK_INDICATORS.items():
                    for indicator in indicators:
                        if indicator in content:
                            return framework
            except:
                pass
        
        return None
    
    def _get_dependencies(self) -> Dict[str, List[str]]:
        """Get project dependencies from package files"""
        deps = {'python': [], 'node': []}
        
        req_file = self.project_root / 'requirements.txt'
        if req_file.exists():
            try:
                with open(req_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            pkg = re.split(r'[=<>~!]', line)[0].strip()
                            if pkg:
                                deps['python'].append(pkg)
            except:
                pass
        
        pkg_file = self.project_root / 'package.json'
        if pkg_file.exists():
            try:
                with open(pkg_file, 'r') as f:
                    pkg_data = json.load(f)
                    deps['node'].extend(pkg_data.get('dependencies', {}).keys())
                    deps['node'].extend(pkg_data.get('devDependencies', {}).keys())
            except:
                pass
        
        return deps
    
    def _map_structure(self) -> Dict[str, str]:
        """Map project structure with purpose annotations"""
        structure = {}
        
        common_patterns = {
            'app.py': 'main',
            'main.py': 'main',
            'run.py': 'runner',
            'server.py': 'server',
            'index.js': 'main',
            'templates': 'views',
            'static': 'assets',
            'src': 'source',
            'lib': 'library',
            'tests': 'tests',
            'test': 'tests',
            'docs': 'documentation',
            'api': 'api',
            'models': 'models',
            'views': 'views',
            'controllers': 'controllers',
            'services': 'services',
            'utils': 'utilities',
            'config': 'configuration',
            'tracking': 'services',
        }
        
        for item in self.project_root.iterdir():
            if item.name.startswith('.'):
                continue
            if item.name in ['node_modules', '__pycache__', 'venv', '.venv']:
                continue
            
            structure[item.name] = common_patterns.get(item.name, 'unknown')
        
        return structure
    
    def _find_entry_points(self) -> List[str]:
        """Find main entry point files"""
        entry_points = []
        
        candidates = ['app.py', 'main.py', 'run.py', 'server.py', 'index.js', 'app.js', 'server.js']
        
        for candidate in candidates:
            if (self.project_root / candidate).exists():
                entry_points.append(candidate)
        
        return entry_points
    
    def _detect_database(self) -> Optional[str]:
        """Detect database in use"""
        search_patterns = [
            ('postgresql', ['psycopg2', 'pg8000', 'DATABASE_URL', 'postgres://']),
            ('mysql', ['mysql', 'pymysql', 'mysql://']),
            ('sqlite', ['sqlite3', 'sqlite://', '.db']),
            ('mongodb', ['pymongo', 'mongodb://', 'mongo']),
            ('redis', ['redis', 'redis://']),
        ]
        
        files_to_check = ['app.py', 'main.py', 'requirements.txt', 'package.json', '.env']
        
        for f in files_to_check:
            path = self.project_root / f
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8', errors='replace') as file:
                        content = file.read().lower()
                        
                        for db, patterns in search_patterns:
                            for pattern in patterns:
                                if pattern.lower() in content:
                                    return db
                except:
                    pass
        
        return None
    
    def _has_tests(self) -> bool:
        """Check if project has tests"""
        test_indicators = ['test_', '_test.py', 'tests/', 'test/', 'spec/', '.test.js', '.spec.js']
        
        for root, dirs, files in os.walk(self.project_root):
            for d in dirs:
                if d in ['test', 'tests', 'spec', '__tests__']:
                    return True
            for f in files:
                if 'test' in f.lower() or 'spec' in f.lower():
                    return True
            break
        
        return False
    
    def _count_files(self) -> Dict[str, int]:
        """Count files by type"""
        counts = {'total': 0, 'python': 0, 'javascript': 0, 'html': 0, 'css': 0, 'other': 0}
        
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'venv']]
            
            for f in files:
                ext = Path(f).suffix.lower()
                counts['total'] += 1
                
                if ext == '.py':
                    counts['python'] += 1
                elif ext in ['.js', '.jsx', '.ts', '.tsx']:
                    counts['javascript'] += 1
                elif ext in ['.html', '.htm']:
                    counts['html'] += 1
                elif ext == '.css':
                    counts['css'] += 1
                else:
                    counts['other'] += 1
        
        return counts
    
    def generate_context(self) -> str:
        """Generate context string for AI"""
        result = self.analyze_project()
        if not result['success']:
            return "Unable to analyze project"
        
        analysis = result['analysis']
        
        context = f"""
Project Analysis:
- Primary Language: {analysis['language']}
- Framework: {analysis['framework'] or 'None detected'}
- Database: {analysis['database'] or 'None detected'}
- Has Tests: {'Yes' if analysis['has_tests'] else 'No'}
- Entry Points: {', '.join(analysis['entry_points']) or 'None found'}

Dependencies:
- Python: {', '.join(analysis['dependencies']['python'][:10]) or 'None'}
- Node: {', '.join(analysis['dependencies']['node'][:10]) or 'None'}

Structure:
{chr(10).join(f'  - {k}: {v}' for k, v in analysis['structure'].items())}

File Count: {analysis['file_count']['total']} files
  - Python: {analysis['file_count']['python']}
  - JavaScript: {analysis['file_count']['javascript']}
  - HTML: {analysis['file_count']['html']}
  - CSS: {analysis['file_count']['css']}
"""
        return context.strip()
