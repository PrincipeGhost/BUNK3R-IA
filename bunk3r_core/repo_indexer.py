"""
BUNK3R-IA: Repository Indexer
Indexa el código de los repositorios para que la IA tenga contexto
"""
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class RepoIndexer:
    """Indexa repositorios para proporcionar contexto a la IA"""
    
    # Extensiones de archivos a indexar
    CODE_EXTENSIONS = {
        '.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.scss',
        '.java', '.cpp', '.c', '.h', '.go', '.rs', '.rb', '.php',
        '.json', '.yaml', '.yml', '.md', '.txt', '.sql', '.sh'
    }
    
    # Archivos importantes a priorizar
    IMPORTANT_FILES = {
        'README.md', 'package.json', 'requirements.txt', 'Cargo.toml',
        'go.mod', 'pom.xml', 'build.gradle', 'Gemfile', 'composer.json',
        '.env.example', 'docker-compose.yml', 'Dockerfile'
    }
    
    # Directorios a ignorar
    IGNORE_DIRS = {
        '.git', 'node_modules', '__pycache__', '.venv', 'venv', 'env',
        'dist', 'build', 'target', '.next', '.cache', 'vendor'
    }
    
    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path)
        self.repo_name = self.repo_path.name
        
    def index_repo(self) -> Dict:
        """Indexa un repositorio completo"""
        if not self.repo_path.exists():
            return {"success": False, "error": "Repositorio no encontrado"}
        
        logger.info(f"📚 Indexando repositorio: {self.repo_name}")
        
        index = {
            "repo_name": self.repo_name,
            "repo_path": str(self.repo_path),
            "structure": self._build_structure(),
            "languages": self._detect_languages(),
            "important_files": self._find_important_files(),
            "dependencies": self._extract_dependencies(),
            "file_count": 0,
            "total_size": 0
        }
        
        # Contar archivos y tamaño
        for file_info in index["structure"]:
            if file_info["type"] == "file":
                index["file_count"] += 1
                index["total_size"] += file_info.get("size", 0)
        
        logger.info(f"✅ Indexado completado: {index['file_count']} archivos, {len(index['languages'])} lenguajes")
        
        return {"success": True, "index": index}
    
    def _build_structure(self, max_depth: int = 5) -> List[Dict]:
        """Construye la estructura de archivos del repositorio"""
        structure = []
        
        def scan_dir(path: Path, depth: int = 0):
            if depth > max_depth:
                return
            
            try:
                for item in sorted(path.iterdir()):
                    # Ignorar directorios especiales
                    if item.name in self.IGNORE_DIRS:
                        continue
                    
                    if item.is_dir():
                        structure.append({
                            "type": "dir",
                            "name": item.name,
                            "path": str(item.relative_to(self.repo_path)),
                            "depth": depth
                        })
                        scan_dir(item, depth + 1)
                    elif item.is_file():
                        # Solo indexar archivos de código
                        if item.suffix in self.CODE_EXTENSIONS or item.name in self.IMPORTANT_FILES:
                            try:
                                size = item.stat().st_size
                                structure.append({
                                    "type": "file",
                                    "name": item.name,
                                    "path": str(item.relative_to(self.repo_path)),
                                    "extension": item.suffix,
                                    "size": size,
                                    "depth": depth
                                })
                            except:
                                pass
            except PermissionError:
                pass
        
        scan_dir(self.repo_path)
        return structure
    
    def _detect_languages(self) -> Dict[str, int]:
        """Detecta los lenguajes de programación usados"""
        languages = {}
        
        extension_to_language = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.sql': 'SQL',
            '.sh': 'Shell'
        }
        
        for item in self.repo_path.rglob('*'):
            if item.is_file() and item.suffix in extension_to_language:
                lang = extension_to_language[item.suffix]
                languages[lang] = languages.get(lang, 0) + 1
        
        return languages
    
    def _find_important_files(self) -> List[Dict]:
        """Encuentra archivos importantes del proyecto"""
        important = []
        
        for filename in self.IMPORTANT_FILES:
            file_path = self.repo_path / filename
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    important.append({
                        "name": filename,
                        "path": str(file_path.relative_to(self.repo_path)),
                        "content_preview": content[:500] if len(content) > 500 else content
                    })
                except:
                    pass
        
        return important
    
    def _extract_dependencies(self) -> Dict:
        """Extrae las dependencias del proyecto"""
        deps = {
            "python": [],
            "node": [],
            "other": []
        }
        
        # Python: requirements.txt
        req_file = self.repo_path / 'requirements.txt'
        if req_file.exists():
            try:
                content = req_file.read_text(encoding='utf-8')
                deps["python"] = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
            except:
                pass
        
        # Node.js: package.json
        pkg_file = self.repo_path / 'package.json'
        if pkg_file.exists():
            try:
                content = json.loads(pkg_file.read_text(encoding='utf-8'))
                if 'dependencies' in content:
                    deps["node"] = list(content['dependencies'].keys())
            except:
                pass
        
        return deps
    
    def get_file_content(self, relative_path: str, max_lines: int = 1000) -> Optional[str]:
        """Obtiene el contenido de un archivo específico"""
        file_path = self.repo_path / relative_path
        
        if not file_path.exists() or not file_path.is_file():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [next(f, '') for _ in range(max_lines)]
                return ''.join(lines)
        except:
            return None
    
    def search_in_repo(self, query: str, case_sensitive: bool = False) -> List[Dict]:
        """Busca un término en todos los archivos del repositorio"""
        results = []
        
        if not case_sensitive:
            query = query.lower()
        
        for item in self.repo_path.rglob('*'):
            if item.is_file() and item.suffix in self.CODE_EXTENSIONS:
                try:
                    content = item.read_text(encoding='utf-8', errors='ignore')
                    search_content = content if case_sensitive else content.lower()
                    
                    if query in search_content:
                        # Encontrar líneas que contienen el query
                        lines = content.split('\n')
                        matches = []
                        for i, line in enumerate(lines, 1):
                            search_line = line if case_sensitive else line.lower()
                            if query in search_line:
                                matches.append({
                                    "line_number": i,
                                    "content": line.strip()
                                })
                                if len(matches) >= 5:  # Máximo 5 matches por archivo
                                    break
                        
                        results.append({
                            "file": str(item.relative_to(self.repo_path)),
                            "matches": matches
                        })
                except:
                    pass
        
        return results
