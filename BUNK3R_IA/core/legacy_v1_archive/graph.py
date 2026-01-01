import os
import ast
import logging
from datetime import datetime
from BUNK3R_IA.models import db, ProjectGraph

logger = logging.getLogger(__name__)

class GraphCrawler:
    """
    Escanea el proyecto para construir un grafo de dependencias.
    Ayuda a la IA a entender el impacto de sus cambios.
    """
    
    def __init__(self, root_path):
        self.root_path = root_path

    def scan_project(self):
        """Escaneo completo del proyecto."""
        logger.info(f"GraphCrawler: Iniciando escaneo en {self.root_path}")
        for root, dirs, files in os.walk(self.root_path):
            if any(d in root for d in [".git", "__pycache__", "venv", "node_modules"]):
                continue
                
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.root_path)
                    self._analyze_python_file(full_path, rel_path)
        
        db.session.commit()
        logger.info("GraphCrawler: Escaneo completado.")

    def _analyze_python_file(self, full_path, rel_path):
        """Analiza imports y definiciones usando AST."""
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                node = ast.parse(f.read())
            
            imports = []
            exports = []
            
            for child in ast.walk(node):
                if isinstance(child, ast.Import):
                    for n in child.names:
                        imports.append(n.name)
                elif isinstance(child, ast.ImportFrom):
                    imports.append(f"{child.module}.{child.names[0].name}" if child.module else child.names[0].name)
                elif isinstance(child, ast.FunctionDef):
                    exports.append(f"func:{child.name}")
                elif isinstance(child, ast.ClassDef):
                    exports.append(f"class:{child.name}")

            # Persistir en DB
            graph_entry = ProjectGraph.query.filter_by(file_path=rel_path).first()
            if not graph_entry:
                graph_entry = ProjectGraph(file_path=rel_path)
                db.session.add(graph_entry)
            
            graph_entry.imports = imports
            graph_entry.exports = exports
            graph_entry.last_scanned = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error analizando {rel_path}: {e}")

# Instancia para exportar
def get_graph_crawler():
    return GraphCrawler(os.getcwd())
