"""
BUNK3R AI Constructor - Sistema de IA Constructora de 8 Fases
Arquitectura completa para generación inteligente de proyectos web

Fases:
1. Recepción y Análisis Inicial (IntentParser)
2. Investigación Autónoma (ResearchEngine)
3. Clarificación Inteligente (ClarificationManager)
4. Construcción del Prompt Maestro (PromptBuilder)
5. Presentación del Plan (PlanPresenter)
6. Ejecución Controlada (TaskOrchestrator)
7. Verificación Automática (OutputVerifier)
8. Entrega Final (DeliveryManager)
"""

import os
import json
import logging
import re
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)

try:
    from BUNK3R_IA.core.ai_flow_logger import flow_logger
except ImportError:
    flow_logger = None

try:
    from BUNK3R_IA.core.ai_toolkit import AIFileToolkit, AICommandExecutor, AIErrorDetector, AIProjectAnalyzer
    TOOLKIT_AVAILABLE = True
except ImportError:
    TOOLKIT_AVAILABLE = False
    AIFileToolkit = None
    AICommandExecutor = None
    AIErrorDetector = None
    AIProjectAnalyzer = None


class TaskType(Enum):
    """Tipos de tareas que BUNK3R puede manejar - 30+ tipos de intenciones"""
    
    # === CREACIÓN (12 tipos) ===
    CREAR_WEB = "crear_web"
    CREAR_LANDING = "crear_landing"
    CREAR_DASHBOARD = "crear_dashboard"
    CREAR_FORMULARIO = "crear_formulario"
    CREAR_API = "crear_api"
    CREAR_COMPONENTE = "crear_componente"
    CREAR_PAGINA = "crear_pagina"
    CREAR_MODAL = "crear_modal"
    CREAR_TABLA = "crear_tabla"
    CREAR_ESTILO = "crear_estilo"
    CREAR_FUNCION = "crear_funcion"
    CREAR_CLASE = "crear_clase"
    
    # === MODIFICACIÓN (9 tipos) ===
    MODIFICAR_CODIGO = "modificar_codigo"
    MODIFICAR_ARCHIVO = "modificar_archivo"
    MODIFICAR_ESTILO = "modificar_estilo"
    MODIFICAR_CONTENIDO = "modificar_contenido"
    AGREGAR_FUNCIONALIDAD = "agregar_funcionalidad"
    QUITAR_ELEMENTO = "quitar_elemento"
    RENOMBRAR = "renombrar"
    MOVER_ARCHIVO = "mover_archivo"
    DUPLICAR = "duplicar"
    
    # === CORRECCIÓN (6 tipos) ===
    CORREGIR_ERROR = "corregir_error"
    CORREGIR_SINTAXIS = "corregir_sintaxis"
    CORREGIR_ESTILO = "corregir_estilo"
    CORREGIR_LOGICA = "corregir_logica"
    CORREGIR_IMPORTACION = "corregir_importacion"
    CORREGIR_TIPADO = "corregir_tipado"
    
    # === EJECUCIÓN (6 tipos) ===
    EJECUTAR_COMANDO = "ejecutar_comando"
    INSTALAR_DEPENDENCIA = "instalar_dependencia"
    EJECUTAR_SCRIPT = "ejecutar_script"
    REINICIAR_SERVIDOR = "reiniciar_servidor"
    COMPILAR = "compilar"
    DESPLEGAR = "desplegar"
    
    # === LECTURA (6 tipos) ===
    LEER_ARCHIVO = "leer_archivo"
    BUSCAR_CODIGO = "buscar_codigo"
    LISTAR_ARCHIVOS = "listar_archivos"
    VER_LOGS = "ver_logs"
    VER_ESTRUCTURA = "ver_estructura"
    ANALIZAR_PROYECTO = "analizar_proyecto"
    
    # === OPTIMIZACIÓN (5 tipos) ===
    OPTIMIZAR = "optimizar"
    OPTIMIZAR_RENDIMIENTO = "optimizar_rendimiento"
    OPTIMIZAR_SEO = "optimizar_seo"
    REFACTORIZAR = "refactorizar"
    LIMPIAR_CODIGO = "limpiar_codigo"
    
    # === EXPLICACIÓN (4 tipos) ===
    EXPLICAR = "explicar"
    EXPLICAR_CODIGO = "explicar_codigo"
    DOCUMENTAR = "documentar"
    CREAR_TUTORIAL = "crear_tutorial"
    
    # === BASE DE DATOS (4 tipos) ===
    CREAR_MODELO = "crear_modelo"
    CREAR_MIGRACION = "crear_migracion"
    CONSULTA_BD = "consulta_bd"
    MODIFICAR_ESQUEMA = "modificar_esquema"
    
    # === OTROS ===
    CONSULTA_GENERAL = "consulta_general"
    DESCONOCIDO = "desconocido"


class ProjectStyle(Enum):
    """Estilos de diseño disponibles"""
    MODERNO_OSCURO = "moderno_oscuro"
    MINIMALISTA = "minimalista"
    CORPORATIVO = "corporativo"
    CALIDO = "calido"
    FUTURISTA = "futurista"
    NEOBANCO = "neobanco"


class ProgrammingLanguage(Enum):
    """Lenguajes de programación soportados"""
    HTML_CSS_JS = "html_css_js"
    PYTHON_FLASK = "python_flask"
    PYTHON_FASTAPI = "python_fastapi"
    PYTHON_GENERAL = "python_general"
    NODEJS_EXPRESS = "nodejs_express"
    NODEJS_GENERAL = "nodejs_general"
    REACT = "react"
    VUE = "vue"
    SQL = "sql"
    DOCKER = "docker"
    SHELL = "shell"
    MIXED = "mixed"


LANGUAGE_TEMPLATES = {
    ProgrammingLanguage.PYTHON_FLASK: {
        "name": "Python Flask",
        "extension": ".py",
        "files": ["app.py", "requirements.txt", "templates/index.html", "static/css/styles.css"],
        "boilerplate": '''from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
''',
        "requirements": "flask==3.0.0\ngunicorn==21.2.0\n",
        "import_style": "from module import Class",
        "comment_style": "#",
    },
    ProgrammingLanguage.PYTHON_FASTAPI: {
        "name": "Python FastAPI",
        "extension": ".py",
        "files": ["main.py", "requirements.txt", "models.py", "schemas.py"],
        "boilerplate": '''from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
''',
        "requirements": "fastapi==0.109.0\nuvicorn==0.27.0\npydantic==2.5.0\n",
        "import_style": "from module import Class",
        "comment_style": "#",
    },
    ProgrammingLanguage.PYTHON_GENERAL: {
        "name": "Python General",
        "extension": ".py",
        "files": ["main.py", "requirements.txt"],
        "boilerplate": '''#!/usr/bin/env python3
"""
Main module
"""

def main():
    pass

if __name__ == "__main__":
    main()
''',
        "requirements": "",
        "import_style": "import module",
        "comment_style": "#",
    },
    ProgrammingLanguage.NODEJS_EXPRESS: {
        "name": "Node.js Express",
        "extension": ".js",
        "files": ["server.js", "package.json", "routes/index.js"],
        "boilerplate": '''const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(express.static('public'));

app.get('/', (req, res) => {
    res.send('Hello World!');
});

app.get('/api/health', (req, res) => {
    res.json({ status: 'healthy' });
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
''',
        "package_json": '''{
  "name": "app",
  "version": "1.0.0",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js"
  },
  "dependencies": {
    "express": "^4.18.2"
  }
}
''',
        "import_style": "const module = require('module');",
        "comment_style": "//",
    },
    ProgrammingLanguage.REACT: {
        "name": "React",
        "extension": ".jsx",
        "files": ["src/App.jsx", "src/index.jsx", "src/components/Component.jsx"],
        "boilerplate": '''import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [data, setData] = useState(null);

  useEffect(() => {
    // Fetch data here
  }, []);

  return (
    <div className="App">
      <h1>Hello React</h1>
    </div>
  );
}

export default App;
''',
        "import_style": "import Component from './Component';",
        "comment_style": "//",
    },
    ProgrammingLanguage.SQL: {
        "name": "SQL",
        "extension": ".sql",
        "files": ["schema.sql", "queries.sql", "migrations/001_initial.sql"],
        "boilerplate": '''-- Database Schema
-- Created: {date}

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
''',
        "comment_style": "--",
    },
    ProgrammingLanguage.DOCKER: {
        "name": "Docker",
        "extension": "",
        "files": ["Dockerfile", "docker-compose.yml", ".dockerignore"],
        "dockerfile": '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
''',
        "docker_compose": '''version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    volumes:
      - .:/app
''',
        "comment_style": "#",
    },
    ProgrammingLanguage.HTML_CSS_JS: {
        "name": "HTML/CSS/JavaScript",
        "extension": ".html",
        "files": ["index.html", "styles.css", "script.js"],
        "boilerplate": '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Título</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <main>
        <h1>Hola Mundo</h1>
    </main>
    <script src="script.js"></script>
</body>
</html>
''',
        "comment_style": "<!-- -->",
    },
}


@dataclass
class IntentAnalysis:
    """Resultado del análisis de intención"""
    tipo_tarea: TaskType
    contexto: str
    especificaciones_usuario: Dict[str, Any]
    requiere_investigacion: bool
    requiere_clarificacion: bool
    nivel_detalle: str  # "alto", "medio", "bajo", "vago"
    keywords: List[str]
    idioma: str
    urgencia: str  # "alta", "media", "baja"
    lenguaje_programacion: ProgrammingLanguage = ProgrammingLanguage.HTML_CSS_JS
    
    def to_dict(self) -> Dict:
        return {
            "tipo_tarea": self.tipo_tarea.value,
            "contexto": self.contexto,
            "especificaciones_usuario": self.especificaciones_usuario,
            "requiere_investigacion": self.requiere_investigacion,
            "requiere_clarificacion": self.requiere_clarificacion,
            "nivel_detalle": self.nivel_detalle,
            "keywords": self.keywords,
            "idioma": self.idioma,
            "urgencia": self.urgencia,
            "lenguaje_programacion": self.lenguaje_programacion.value
        }


@dataclass
class ResearchResult:
    """Resultado de la investigación autónoma"""
    referencias: List[str]
    elementos_recomendados: List[str]
    paleta_sugerida: List[str]
    estilo: str
    insights: str
    mejores_practicas: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ClarificationResult:
    """Resultado de la clarificación con el usuario"""
    preguntas_realizadas: int
    respuestas_usuario: Dict[str, str]
    clarificacion_completa: bool
    preferencias_detectadas: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class TaskItem:
    """Item de tarea individual"""
    id: int
    descripcion: str
    estado: str  # "pendiente", "en_progreso", "completada", "error"
    archivo_destino: Optional[str] = None
    codigo_generado: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ExecutionPlan:
    """Plan de ejecución completo"""
    tareas: List[TaskItem]
    tiempo_estimado: str
    riesgos: List[str]
    archivos_a_crear: List[str]
    dependencias: List[str]
    
    def to_dict(self) -> Dict:
        return {
            "tareas": [t.to_dict() for t in self.tareas],
            "tiempo_estimado": self.tiempo_estimado,
            "riesgos": self.riesgos,
            "archivos_a_crear": self.archivos_a_crear,
            "dependencias": self.dependencias
        }


@dataclass
class VerificationResult:
    """Resultado de la verificación automática"""
    sintaxis_valida: bool
    completitud: bool
    funcionalidad: bool
    responsive: bool
    coincide_requisitos: bool
    errores: List[str]
    advertencias: List[str]
    puntuacion: int  # 0-100
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ConstructorSession:
    """Sesión del constructor - mantiene estado entre fases"""
    session_id: str
    user_id: str
    fase_actual: int
    intent: Optional[IntentAnalysis] = None
    research: Optional[ResearchResult] = None
    clarification: Optional[ClarificationResult] = None
    plan: Optional[ExecutionPlan] = None
    prompt_maestro: Optional[str] = None
    archivos_generados: Dict[str, str] = field(default_factory=dict)
    verification: Optional[VerificationResult] = None
    esperando_confirmacion: bool = False
    esperando_clarificacion: bool = False
    preguntas_pendientes: List[str] = field(default_factory=list)
    historial: List[Dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "fase_actual": self.fase_actual,
            "intent": self.intent.to_dict() if self.intent else None,
            "research": self.research.to_dict() if self.research else None,
            "clarification": self.clarification.to_dict() if self.clarification else None,
            "plan": self.plan.to_dict() if self.plan else None,
            "prompt_maestro": self.prompt_maestro,
            "archivos_generados": self.archivos_generados,
            "verification": self.verification.to_dict() if self.verification else None,
            "esperando_confirmacion": self.esperando_confirmacion,
            "esperando_clarificacion": self.esperando_clarificacion,
            "preguntas_pendientes": self.preguntas_pendientes,
            "fase_nombre": self._get_fase_nombre()
        }
    
    def _get_fase_nombre(self) -> str:
        nombres = {
            1: "Análisis Inicial",
            2: "Investigación",
            3: "Clarificación",
            4: "Construcción Prompt",
            5: "Presentación Plan",
            6: "Ejecución",
            7: "Verificación",
            8: "Entrega"
        }
        return nombres.get(self.fase_actual, "Desconocida")


class IntentParser:
    """
    FASE 1: Analizador de Intención
    Extrae qué quiere el usuario y decide los siguientes pasos
    """
    
    TASK_PATTERNS = {
        # === CREACIÓN ===
        TaskType.CREAR_LANDING: [
            r"landing\s*page", r"página\s*de\s*aterrizaje", r"landing",
            r"one\s*page", r"página\s*única"
        ],
        TaskType.CREAR_WEB: [
            r"sitio\s*web", r"página\s*web", r"website", r"web\s*app",
            r"aplicación\s*web", r"portal"
        ],
        TaskType.CREAR_DASHBOARD: [
            r"dashboard", r"panel", r"tablero", r"admin\s*panel",
            r"panel\s*de\s*control"
        ],
        TaskType.CREAR_FORMULARIO: [
            r"formulario", r"form", r"contacto", r"registro",
            r"encuesta", r"survey"
        ],
        TaskType.CREAR_API: [
            r"api", r"endpoint", r"backend", r"servidor",
            r"rest\s*api", r"servicio"
        ],
        TaskType.CREAR_COMPONENTE: [
            r"crea.*componente", r"nuevo\s*componente", r"componente\s*de",
            r"widget", r"elemento\s*ui"
        ],
        TaskType.CREAR_PAGINA: [
            r"crea.*página", r"nueva\s*página", r"agrega.*página",
            r"page", r"vista\s*nueva"
        ],
        TaskType.CREAR_MODAL: [
            r"modal", r"popup", r"ventana\s*emergente", r"diálogo",
            r"dialog"
        ],
        TaskType.CREAR_TABLA: [
            r"tabla", r"table", r"grid", r"listado", r"lista\s*de"
        ],
        TaskType.CREAR_ESTILO: [
            r"estilos?\s*css", r"css\s*para", r"estiliza", r"diseño\s*de"
        ],
        TaskType.CREAR_FUNCION: [
            r"función", r"function", r"método", r"crea.*función"
        ],
        TaskType.CREAR_CLASE: [
            r"clase", r"class", r"modelo", r"crea.*clase"
        ],
        
        # === MODIFICACIÓN ===
        TaskType.MODIFICAR_CODIGO: [
            r"modifica", r"cambia", r"actualiza", r"edita"
        ],
        TaskType.MODIFICAR_ARCHIVO: [
            r"modifica.*archivo", r"edita.*archivo", r"cambia.*en\s*el\s*archivo"
        ],
        TaskType.AGREGAR_FUNCIONALIDAD: [
            r"agrega", r"añade", r"incorpora", r"incluye"
        ],
        TaskType.QUITAR_ELEMENTO: [
            r"quita", r"elimina", r"borra", r"remueve", r"delete"
        ],
        TaskType.RENOMBRAR: [
            r"renombra", r"cambia.*nombre", r"rename"
        ],
        TaskType.MOVER_ARCHIVO: [
            r"mueve", r"move", r"traslada"
        ],
        
        # === CORRECCIÓN ===
        TaskType.CORREGIR_ERROR: [
            r"error", r"bug", r"falla", r"no\s*funciona", r"arregla",
            r"corrige", r"fix", r"problema"
        ],
        TaskType.CORREGIR_SINTAXIS: [
            r"syntax\s*error", r"error\s*de\s*sintaxis"
        ],
        TaskType.CORREGIR_IMPORTACION: [
            r"import.*error", r"module\s*not\s*found", r"cannot\s*find\s*module"
        ],
        
        # === EJECUCIÓN ===
        TaskType.EJECUTAR_COMANDO: [
            r"ejecuta", r"corre", r"run", r"comando"
        ],
        TaskType.INSTALAR_DEPENDENCIA: [
            r"instala", r"install", r"npm\s*install", r"pip\s*install",
            r"dependencia", r"paquete", r"librería", r"package"
        ],
        TaskType.REINICIAR_SERVIDOR: [
            r"reinicia", r"restart", r"reiniciar.*servidor"
        ],
        
        # === LECTURA ===
        TaskType.LEER_ARCHIVO: [
            r"lee", r"muestra.*archivo", r"abre", r"ver\s*contenido",
            r"qué\s*hay\s*en", r"read"
        ],
        TaskType.BUSCAR_CODIGO: [
            r"busca", r"encuentra", r"dónde\s*está", r"search",
            r"grep", r"localiza"
        ],
        TaskType.LISTAR_ARCHIVOS: [
            r"lista.*archivos", r"qué\s*archivos", r"ls", r"muestra.*estructura"
        ],
        TaskType.VER_LOGS: [
            r"logs", r"errores\s*del\s*servidor", r"consola", r"ver\s*errores"
        ],
        TaskType.ANALIZAR_PROYECTO: [
            r"analiza.*proyecto", r"estructura.*proyecto", r"qué\s*tecnologías"
        ],
        
        # === OPTIMIZACIÓN ===
        TaskType.OPTIMIZAR: [
            r"optimiza", r"mejora", r"más\s*rápido", r"rendimiento",
            r"performance"
        ],
        TaskType.REFACTORIZAR: [
            r"refactoriza", r"refactor", r"reorganiza", r"limpia.*código"
        ],
        TaskType.OPTIMIZAR_SEO: [
            r"seo", r"meta\s*tags", r"posicionamiento"
        ],
        
        # === EXPLICACIÓN ===
        TaskType.EXPLICAR: [
            r"explica", r"qué\s*es", r"cómo\s*funciona", r"por\s*qué",
            r"enseña"
        ],
        TaskType.EXPLICAR_CODIGO: [
            r"explica.*código", r"qué\s*hace\s*este", r"cómo\s*funciona\s*este"
        ],
        TaskType.DOCUMENTAR: [
            r"documenta", r"documentación", r"readme", r"comments"
        ],
        
        # === BASE DE DATOS ===
        TaskType.CREAR_MODELO: [
            r"modelo.*base", r"tabla.*bd", r"schema", r"entity"
        ],
        TaskType.CREAR_MIGRACION: [
            r"migración", r"migration", r"alter\s*table"
        ],
        TaskType.CONSULTA_BD: [
            r"consulta.*sql", r"query", r"select.*from"
        ]
    }
    
    CONTEXT_KEYWORDS = {
        "restaurante": ["restaurante", "café", "cafetería", "bar", "comida", "menú", "cocina", "chef", "platos", "reserva"],
        "ecommerce": ["tienda online", "ecommerce", "e-commerce", "carrito", "checkout", "vender", "comprar", "productos", "stripe", "paypal", "pagos online"],
        "portfolio": ["portfolio", "portafolio", "proyectos", "trabajos", "cv", "curriculum", "fotógrafo", "diseñador", "freelance"],
        "blog": ["blog", "artículos", "posts", "noticias", "contenido", "publicaciones"],
        "saas": ["saas", "suscripción", "plataforma", "software", "app", "dashboard", "panel", "métricas", "usuarios"],
        "fintech": ["fintech", "banco", "inversiones", "wallet", "cripto", "finanzas", "trading", "bolsa", "acciones"],
        "negocio": ["negocio", "empresa", "comercio", "servicio", "startup", "compañía"]
    }
    
    LANGUAGE_PATTERNS = {
        ProgrammingLanguage.PYTHON_FLASK: [
            r"flask", r"python\s*web", r"jinja", r"render_template", r"app\.py"
        ],
        ProgrammingLanguage.PYTHON_FASTAPI: [
            r"fastapi", r"fast\s*api", r"pydantic", r"uvicorn", r"async\s*api"
        ],
        ProgrammingLanguage.PYTHON_GENERAL: [
            r"python", r"\.py\b", r"pip\s*install", r"script\s*python", r"automatizar"
        ],
        ProgrammingLanguage.NODEJS_EXPRESS: [
            r"express", r"node\.?js", r"npm", r"package\.json", r"servidor\s*node"
        ],
        ProgrammingLanguage.REACT: [
            r"react", r"jsx", r"componente\s*react", r"hooks?", r"useState", r"useEffect"
        ],
        ProgrammingLanguage.VUE: [
            r"vue", r"vuejs", r"vue\.js", r"nuxt"
        ],
        ProgrammingLanguage.SQL: [
            r"\bsql\b", r"base\s*de\s*datos", r"consulta\s*sql", r"tabla\s*sql", 
            r"create\s*table", r"select\s*from", r"postgresql", r"mysql", r"sqlite"
        ],
        ProgrammingLanguage.DOCKER: [
            r"docker", r"dockerfile", r"container", r"contenedor", r"docker-compose"
        ],
        ProgrammingLanguage.HTML_CSS_JS: [
            r"html", r"css", r"javascript", r"página\s*web", r"sitio\s*web", 
            r"landing", r"website", r"frontend"
        ],
    }
    
    def analyze(self, message: str) -> IntentAnalysis:
        """Analiza el mensaje del usuario y extrae la intención"""
        message_lower = message.lower().strip()
        
        # Detectar tipo de tarea
        tipo_tarea = self._detect_task_type(message_lower)
        
        # Extraer contexto
        contexto = self._extract_context(message_lower)
        
        # Extraer especificaciones
        specs = self._extract_specifications(message)
        
        # Evaluar nivel de detalle
        nivel_detalle = self._evaluate_detail_level(message, specs)
        
        # Extraer keywords
        keywords = self._extract_keywords(message_lower)
        
        # Detectar idioma
        idioma = self._detect_language(message)
        
        # Detectar urgencia
        urgencia = self._detect_urgency(message_lower)
        
        # Detectar lenguaje de programación
        lenguaje_programacion = self._detect_programming_language(message_lower, tipo_tarea)
        
        # Decidir si necesita investigación o clarificación
        requiere_investigacion = self._needs_research(tipo_tarea, nivel_detalle, specs)
        requiere_clarificacion = self._needs_clarification(tipo_tarea, nivel_detalle, specs)
        
        return IntentAnalysis(
            tipo_tarea=tipo_tarea,
            contexto=contexto,
            especificaciones_usuario=specs,
            requiere_investigacion=requiere_investigacion,
            requiere_clarificacion=requiere_clarificacion,
            nivel_detalle=nivel_detalle,
            keywords=keywords,
            idioma=idioma,
            urgencia=urgencia,
            lenguaje_programacion=lenguaje_programacion
        )
    
    def _detect_task_type(self, message: str) -> TaskType:
        """Detecta el tipo de tarea basándose en patrones"""
        for task_type, patterns in self.TASK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    return task_type
        return TaskType.CONSULTA_GENERAL
    
    def _extract_context(self, message: str) -> str:
        """Extrae el contexto del negocio/proyecto usando puntuación"""
        context_scores = {}
        
        for context_name, keywords in self.CONTEXT_KEYWORDS.items():
            score = 0
            for kw in keywords:
                if kw in message:
                    score += len(kw)
            if score > 0:
                context_scores[context_name] = score
        
        if not context_scores:
            return "general"
        
        return max(context_scores.keys(), key=lambda x: context_scores[x])
    
    def _extract_specifications(self, message: str) -> Dict[str, Any]:
        """Extrae especificaciones mencionadas"""
        specs = {
            "colores": [],
            "secciones": [],
            "funcionalidades": [],
            "estilo": None,
            "recursos_disponibles": [],
            "objetivo": None
        }
        
        # Detectar colores mencionados
        color_patterns = [
            r"color(?:es)?\s*(?:como\s*)?(azul|rojo|verde|negro|blanco|dorado|morado|naranja)",
            r"(azul|rojo|verde|negro|blanco|dorado|morado|naranja)\s*y\s*(azul|rojo|verde|negro|blanco|dorado|morado|naranja)"
        ]
        for pattern in color_patterns:
            matches = re.findall(pattern, message.lower())
            if matches:
                if isinstance(matches[0], tuple):
                    specs["colores"].extend(list(matches[0]))
                else:
                    specs["colores"].extend(matches)
        
        # Detectar secciones mencionadas
        section_keywords = ["hero", "menú", "contacto", "about", "servicios", "productos", 
                          "testimonios", "galería", "precios", "equipo", "faq"]
        for kw in section_keywords:
            if kw in message.lower():
                specs["secciones"].append(kw)
        
        # Detectar estilo
        style_keywords = {
            "minimalista": ["minimalista", "minimal", "simple", "limpio"],
            "moderno": ["moderno", "contemporáneo", "actual"],
            "elegante": ["elegante", "lujoso", "premium", "sofisticado"],
            "colorido": ["colorido", "vibrante", "llamativo"],
            "corporativo": ["corporativo", "profesional", "formal"],
            "oscuro": ["oscuro", "dark", "negro"],
            "claro": ["claro", "light", "blanco"]
        }
        for style, keywords in style_keywords.items():
            for kw in keywords:
                if kw in message.lower():
                    specs["estilo"] = style
                    break
        
        # Detectar recursos disponibles
        if any(kw in message.lower() for kw in ["tengo logo", "tengo fotos", "tengo imágenes"]):
            specs["recursos_disponibles"].append("imagenes")
        if any(kw in message.lower() for kw in ["tengo textos", "tengo contenido"]):
            specs["recursos_disponibles"].append("contenido")
        
        # Detectar objetivo
        objective_patterns = {
            "vender": ["vender", "ventas", "comprar", "ecommerce"],
            "contacto": ["contactar", "contacto", "llamar", "whatsapp"],
            "informar": ["informar", "mostrar", "presentar", "portfolio"],
            "reservar": ["reservar", "cita", "agenda", "booking"]
        }
        for obj, keywords in objective_patterns.items():
            for kw in keywords:
                if kw in message.lower():
                    specs["objetivo"] = obj
                    break
        
        return specs
    
    def _evaluate_detail_level(self, message: str, specs: Dict) -> str:
        """Evalúa cuánto detalle proporcionó el usuario"""
        score = 0
        
        # Longitud del mensaje
        if len(message) > 200:
            score += 2
        elif len(message) > 100:
            score += 1
        
        # Especificaciones encontradas
        if specs["colores"]:
            score += 1
        if specs["secciones"]:
            score += len(specs["secciones"]) // 2
        if specs["estilo"]:
            score += 1
        if specs["objetivo"]:
            score += 1
        if specs["recursos_disponibles"]:
            score += 1
        
        if score >= 5:
            return "alto"
        elif score >= 3:
            return "medio"
        elif score >= 1:
            return "bajo"
        else:
            return "vago"
    
    def _extract_keywords(self, message: str) -> List[str]:
        """Extrae palabras clave del mensaje"""
        stop_words = {"quiero", "necesito", "para", "una", "un", "que", "con", "de", "la", "el", "mi", "me"}
        words = re.findall(r'\b\w+\b', message.lower())
        return [w for w in words if len(w) > 3 and w not in stop_words][:10]
    
    def _detect_language(self, message: str) -> str:
        """Detecta el idioma del mensaje"""
        spanish_words = {"quiero", "necesito", "para", "página", "sitio", "negocio", "crear"}
        english_words = {"want", "need", "website", "page", "create", "build"}
        
        message_words = set(message.lower().split())
        spanish_count = len(message_words & spanish_words)
        english_count = len(message_words & english_words)
        
        return "es" if spanish_count >= english_count else "en"
    
    def _detect_urgency(self, message: str) -> str:
        """Detecta la urgencia del pedido"""
        urgent_words = ["urgente", "rápido", "ya", "hoy", "ahora", "pronto", "asap"]
        if any(w in message for w in urgent_words):
            return "alta"
        return "media"
    
    def _detect_programming_language(self, message: str, task_type: TaskType) -> ProgrammingLanguage:
        """Detecta el lenguaje de programación basándose en el mensaje y tipo de tarea"""
        language_scores = {}
        
        # Analizar patrones de lenguaje
        for lang, patterns in self.LANGUAGE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    score += 1
            if score > 0:
                language_scores[lang] = score
        
        # Si hay coincidencias, retornar la de mayor puntuación
        if language_scores:
            return max(language_scores.keys(), key=lambda x: language_scores[x])
        
        # Inferir por tipo de tarea si no hay coincidencia directa
        task_language_mapping = {
            TaskType.CREAR_API: ProgrammingLanguage.PYTHON_FLASK,
            TaskType.CREAR_MODELO: ProgrammingLanguage.SQL,
            TaskType.CREAR_MIGRACION: ProgrammingLanguage.SQL,
            TaskType.CONSULTA_BD: ProgrammingLanguage.SQL,
            TaskType.MODIFICAR_ESQUEMA: ProgrammingLanguage.SQL,
            TaskType.CREAR_FUNCION: ProgrammingLanguage.PYTHON_GENERAL,
            TaskType.CREAR_CLASE: ProgrammingLanguage.PYTHON_GENERAL,
            TaskType.EJECUTAR_COMANDO: ProgrammingLanguage.SHELL,
            TaskType.INSTALAR_DEPENDENCIA: ProgrammingLanguage.SHELL,
        }
        
        if task_type in task_language_mapping:
            return task_language_mapping[task_type]
        
        # Default para tareas web
        web_tasks = {
            TaskType.CREAR_WEB, TaskType.CREAR_LANDING, TaskType.CREAR_DASHBOARD,
            TaskType.CREAR_FORMULARIO, TaskType.CREAR_COMPONENTE, TaskType.CREAR_PAGINA,
            TaskType.CREAR_MODAL, TaskType.CREAR_TABLA
        }
        if task_type in web_tasks:
            return ProgrammingLanguage.HTML_CSS_JS
        
        return ProgrammingLanguage.HTML_CSS_JS
    
    def _needs_research(self, task_type: TaskType, detail_level: str, specs: Dict) -> bool:
        """Decide si necesita investigación"""
        # Tareas de creación con poco detalle necesitan investigación
        creation_tasks = {TaskType.CREAR_WEB, TaskType.CREAR_LANDING, TaskType.CREAR_DASHBOARD}
        if task_type in creation_tasks and detail_level in ["vago", "bajo"]:
            return True
        return False
    
    def _needs_clarification(self, task_type: TaskType, detail_level: str, specs: Dict) -> bool:
        """Decide si necesita clarificación del usuario"""
        # Si es tarea de creación y no tiene objetivo claro
        creation_tasks = {TaskType.CREAR_WEB, TaskType.CREAR_LANDING, TaskType.CREAR_DASHBOARD}
        if task_type in creation_tasks:
            if not specs.get("objetivo"):
                return True
            if detail_level == "vago":
                return True
        return False


class ResearchEngine:
    """
    FASE 2: Motor de Investigación Autónoma
    Genera recomendaciones basadas en mejores prácticas
    (Sin scraping real - usa conocimiento interno optimizado)
    """
    
    # Base de conocimiento de mejores prácticas por contexto
    BEST_PRACTICES = {
        "restaurante": {
            "elementos": ["hero con foto de plato estrella", "menú visual", "horarios", 
                         "ubicación con mapa", "reservas online", "galería de fotos", "reseñas"],
            "paleta": ["#3E2723", "#EFEBE9", "#D7CCC8", "#795548", "#BCAAA4"],
            "estilo": "cálido-acogedor",
            "insights": "Las mejores webs de restaurantes usan fotos de alta calidad de sus platos, " +
                       "menú fácil de leer, y botón de reserva/WhatsApp prominente. " +
                       "El 70% de usuarios visitan desde móvil para ver menú y ubicación.",
            "practicas": [
                "Fotos profesionales de platos (mínimo 5)",
                "Menú con precios visibles",
                "Botón de WhatsApp/llamar flotante",
                "Mapa de ubicación interactivo",
                "Horarios claros y actualizados"
            ]
        },
        "ecommerce": {
            "elementos": ["hero con producto destacado", "categorías", "productos destacados",
                         "carrito", "filtros de búsqueda", "reviews", "checkout"],
            "paleta": ["#1A1A2E", "#16213E", "#E94560", "#FFFFFF", "#0F3460"],
            "estilo": "moderno-confiable",
            "insights": "Las tiendas online exitosas priorizan velocidad de carga, fotos de producto " +
                       "de alta calidad desde múltiples ángulos, y checkout simplificado. " +
                       "Botones de compra claros y urgencia aumentan conversión 30%.",
            "practicas": [
                "Imágenes de producto en alta resolución",
                "Precios claros con descuentos visibles",
                "Botón 'Añadir al carrito' prominente",
                "Reviews de clientes",
                "Envío gratis destacado si aplica"
            ]
        },
        "portfolio": {
            "elementos": ["hero con nombre/título", "proyectos destacados", "sobre mí",
                         "skills/tecnologías", "contacto", "testimonios"],
            "paleta": ["#0D1117", "#161B22", "#58A6FF", "#F0F6FC", "#238636"],
            "estilo": "minimalista-profesional",
            "insights": "Los portfolios más efectivos muestran 4-6 proyectos destacados con casos de estudio, " +
                       "demuestran expertise con stack tecnológico visual, y tienen CTA claro para contacto.",
            "practicas": [
                "Máximo 6 proyectos destacados",
                "Cada proyecto con problema/solución",
                "Stack tecnológico visual (iconos)",
                "Links a LinkedIn/GitHub",
                "Formulario de contacto simple"
            ]
        },
        "saas": {
            "elementos": ["hero con propuesta de valor", "features", "pricing", "testimonios",
                         "FAQ", "CTA de registro", "demo/video"],
            "paleta": ["#0F172A", "#1E293B", "#3B82F6", "#FFFFFF", "#10B981"],
            "estilo": "moderno-tech",
            "insights": "Las landing pages SaaS más exitosas tienen una propuesta de valor clara en 5 palabras, " +
                       "muestran el producto en acción (video/gif), y tienen máximo 3 planes de precios.",
            "practicas": [
                "Headline clara de 5-7 palabras",
                "Demo del producto visible",
                "3 planes de precio máximo",
                "Social proof (logos clientes)",
                "CTA de 'Prueba gratis' prominente"
            ]
        },
        "fintech": {
            "elementos": ["hero con propuesta seguridad", "features", "seguridad/certificaciones",
                         "how it works", "testimonios", "app download"],
            "paleta": ["#0B0E11", "#12161C", "#F0B90B", "#FFFFFF", "#22C55E"],
            "estilo": "neo-bank-oscuro",
            "insights": "Las apps fintech priorizan la sensación de seguridad y modernidad. " +
                       "Uso de colores oscuros con acentos brillantes transmite confianza y tecnología. " +
                       "Glass morphism y animaciones sutiles son trending.",
            "practicas": [
                "Indicadores de seguridad prominentes",
                "Interfaz dark mode por defecto",
                "Animaciones suaves en números",
                "Gráficos de crecimiento/rendimiento",
                "Badges de certificación/regulación"
            ]
        },
        "general": {
            "elementos": ["hero", "servicios/features", "sobre nosotros", "contacto"],
            "paleta": ["#1F2937", "#374151", "#3B82F6", "#FFFFFF", "#10B981"],
            "estilo": "profesional-moderno",
            "insights": "Para cualquier tipo de web, los principios fundamentales son: " +
                       "claridad en la propuesta de valor, navegación intuitiva, responsive design, " +
                       "y CTA visibles.",
            "practicas": [
                "Hero claro con propuesta de valor",
                "Navegación simple (máx 5 items)",
                "Mobile-first design",
                "Tiempos de carga < 3 segundos",
                "CTA visible above the fold"
            ]
        }
    }
    
    def research(self, intent: IntentAnalysis) -> ResearchResult:
        """Realiza la investigación basada en el contexto"""
        context = intent.contexto if intent.contexto in self.BEST_PRACTICES else "general"
        practices = self.BEST_PRACTICES[context]
        
        # Combinar con estilo preferido del usuario si existe
        estilo = intent.especificaciones_usuario.get("estilo") or practices["estilo"]
        
        # Ajustar paleta según preferencias
        paleta = practices["paleta"].copy()
        user_colors = intent.especificaciones_usuario.get("colores", [])
        if user_colors:
            # El usuario mencionó colores, ajustar insights
            pass
        
        return ResearchResult(
            referencias=[
                f"Mejores prácticas para {context} 2024",
                f"Tendencias de diseño {estilo}",
                "Patrones de conversión web"
            ],
            elementos_recomendados=practices["elementos"],
            paleta_sugerida=paleta,
            estilo=estilo,
            insights=practices["insights"],
            mejores_practicas=practices["practicas"]
        )


class ClarificationManager:
    """
    FASE 3: Sistema de Clarificación Inteligente
    Genera preguntas relevantes basadas en lo que falta
    """
    
    QUESTION_TEMPLATES = {
        "objetivo": "¿Cuál es el objetivo principal? ¿Qué quieres que hagan los visitantes? (comprar, contactar, informarse, etc.)",
        "recursos": "¿Tienes recursos disponibles? (logo, fotos, textos del negocio)",
        "estilo": "¿Hay algún estilo de diseño que te guste o no te guste? (minimalista, colorido, oscuro, etc.)",
        "secciones": "¿Qué secciones necesitas? (menú, galería, precios, contacto, etc.)",
        "referencia": "¿Hay alguna web que te guste como referencia?",
        "funcionalidad": "¿Necesitas alguna funcionalidad especial? (formulario, mapa, reservas, chat)",
        "publico": "¿Quién es tu público objetivo?",
        "diferenciador": "¿Qué hace único a tu negocio/producto?"
    }
    
    def generate_questions(self, intent: IntentAnalysis, research: Optional[ResearchResult] = None) -> List[str]:
        """Genera preguntas basadas en lo que falta por clarificar"""
        questions = []
        specs = intent.especificaciones_usuario
        
        # Priorizar preguntas según lo que falta
        if not specs.get("objetivo"):
            questions.append(self.QUESTION_TEMPLATES["objetivo"])
        
        if not specs.get("recursos_disponibles"):
            questions.append(self.QUESTION_TEMPLATES["recursos"])
        
        if not specs.get("estilo"):
            questions.append(self.QUESTION_TEMPLATES["estilo"])
        
        # Máximo 3 preguntas para no abrumar
        return questions[:3]
    
    def format_clarification_message(self, intent: IntentAnalysis, research: Optional[ResearchResult], 
                                     questions: List[str]) -> str:
        """Formatea el mensaje de clarificación para el usuario"""
        message = ""
        
        # Si hay investigación, mostrar insights
        if research:
            message += f"📊 **Basándome en mi investigación sobre {intent.contexto}:**\n\n"
            message += f"Las mejores páginas de este tipo incluyen:\n"
            for elem in research.elementos_recomendados[:5]:
                message += f"• {elem.capitalize()}\n"
            message += "\n"
        
        message += "🤔 **Antes de continuar, necesito saber:**\n\n"
        for i, q in enumerate(questions, 1):
            message += f"{i}. {q}\n\n"
        
        return message
    
    def process_response(self, user_response: str, pending_questions: List[str]) -> ClarificationResult:
        """Procesa la respuesta del usuario a las preguntas"""
        respuestas = {}
        preferencias = {}
        
        response_lower = user_response.lower()
        
        # Analizar objetivo
        if "comprar" in response_lower or "vender" in response_lower:
            preferencias["objetivo"] = "venta"
        elif "contactar" in response_lower or "whatsapp" in response_lower or "llamar" in response_lower:
            preferencias["objetivo"] = "contacto"
        elif "informar" in response_lower or "ver" in response_lower or "mostrar" in response_lower:
            preferencias["objetivo"] = "informativo"
        elif "reservar" in response_lower or "cita" in response_lower:
            preferencias["objetivo"] = "reservas"
        
        # Analizar recursos
        if "tengo" in response_lower:
            if "logo" in response_lower:
                preferencias["tiene_logo"] = True
            if "foto" in response_lower:
                preferencias["tiene_fotos"] = True
        
        # Analizar estilo
        if "minimalista" in response_lower or "simple" in response_lower:
            preferencias["estilo"] = "minimalista"
        elif "oscuro" in response_lower or "dark" in response_lower:
            preferencias["estilo"] = "oscuro"
        elif "colorido" in response_lower or "vibrante" in response_lower:
            preferencias["estilo"] = "colorido"
        
        respuestas["raw"] = user_response
        
        return ClarificationResult(
            preguntas_realizadas=len(pending_questions),
            respuestas_usuario=respuestas,
            clarificacion_completa=True,
            preferencias_detectadas=preferencias
        )


class PromptBuilder:
    """
    FASE 4: Constructor del Prompt Maestro
    Combina toda la información en un super-prompt optimizado
    """
    
    def build(self, intent: IntentAnalysis, research: Optional[ResearchResult], 
              clarification: Optional[ClarificationResult]) -> str:
        """Construye el prompt maestro optimizado con soporte multi-lenguaje"""
        
        # Determinar contexto y objetivo
        contexto = intent.contexto
        objetivo = intent.especificaciones_usuario.get("objetivo", "informativo")
        
        if clarification and clarification.preferencias_detectadas:
            objetivo = clarification.preferencias_detectadas.get("objetivo", objetivo)
        
        # Determinar estilo
        estilo = intent.especificaciones_usuario.get("estilo", "moderno")
        if clarification and clarification.preferencias_detectadas.get("estilo"):
            estilo = clarification.preferencias_detectadas["estilo"]
        elif research:
            estilo = research.estilo
        
        # Determinar paleta
        paleta = research.paleta_sugerida if research else ["#1F2937", "#3B82F6", "#FFFFFF"]
        
        # Determinar secciones
        secciones = intent.especificaciones_usuario.get("secciones", [])
        if not secciones and research:
            secciones = research.elementos_recomendados[:5]
        
        # Obtener información del lenguaje
        lang = intent.lenguaje_programacion
        lang_info = LANGUAGE_TEMPLATES.get(lang, {})
        lang_name = lang_info.get("name", "HTML/CSS/JavaScript")
        
        # Construir el prompt con sección de lenguaje
        prompt = f"""[PROMPT MAESTRO - GENERACIÓN DE CÓDIGO]

═══════════════════════════════════════════════════════════════
CONTEXTO DEL PROYECTO
═══════════════════════════════════════════════════════════════
- Tipo: {intent.tipo_tarea.value}
- Contexto: {contexto}
- Objetivo principal: {objetivo}
- Idioma del usuario: {intent.idioma}

═══════════════════════════════════════════════════════════════
LENGUAJE DE PROGRAMACIÓN
═══════════════════════════════════════════════════════════════
- Lenguaje principal: {lang_name}
- Tipo de stack: {lang.value}
- Archivos a generar: {', '.join(lang_info.get('files', ['index.html', 'styles.css', 'script.js']))}

═══════════════════════════════════════════════════════════════
ESPECIFICACIONES DE DISEÑO
═══════════════════════════════════════════════════════════════
- Estilo visual: {estilo}
- Paleta de colores: {', '.join(paleta)}
- Keywords del usuario: {', '.join(intent.keywords[:5])}

═══════════════════════════════════════════════════════════════
SECCIONES REQUERIDAS
═══════════════════════════════════════════════════════════════
"""
        for i, seccion in enumerate(secciones, 1):
            prompt += f"{i}. {seccion.capitalize()}\n"
        
        if research:
            prompt += f"""
═══════════════════════════════════════════════════════════════
MEJORES PRÁCTICAS A APLICAR
═══════════════════════════════════════════════════════════════
"""
            for practica in research.mejores_practicas[:5]:
                prompt += f"• {practica}\n"
        
        # Requisitos técnicos según lenguaje
        requisitos_por_lenguaje = {
            ProgrammingLanguage.PYTHON_FLASK: [
                "Flask best practices con blueprints si es necesario",
                "Jinja2 templates con herencia",
                "Rutas RESTful y manejo de errores",
                "Validación de inputs del usuario",
                "Configuración segura con variables de entorno"
            ],
            ProgrammingLanguage.PYTHON_FASTAPI: [
                "Async/await para operaciones IO",
                "Modelos Pydantic con validación",
                "Documentación automática OpenAPI",
                "Manejo de excepciones HTTP",
                "Dependency injection cuando sea apropiado"
            ],
            ProgrammingLanguage.NODEJS_EXPRESS: [
                "Middleware pattern para cross-cutting concerns",
                "Rutas modulares con Router",
                "Manejo de errores centralizado",
                "Validación de datos de entrada",
                "Async/await para operaciones asíncronas"
            ],
            ProgrammingLanguage.REACT: [
                "Componentes funcionales con hooks",
                "Estado manejado correctamente (useState/useReducer)",
                "Efectos secundarios en useEffect",
                "Props tipadas y validadas",
                "CSS modular o styled-components"
            ],
            ProgrammingLanguage.SQL: [
                "Normalización apropiada (3NF mínimo)",
                "Constraints de integridad (PK, FK, UNIQUE)",
                "Índices para queries frecuentes",
                "Tipos de datos apropiados",
                "Comentarios descriptivos"
            ]
        }
        
        requisitos = requisitos_por_lenguaje.get(lang, [
            "Mobile-first y 100% responsive",
            "HTML5 semántico con accesibilidad",
            "CSS moderno con variables",
            "JavaScript ES6+ para interactividad",
            "Optimizado para carga rápida",
            "Sin dependencias externas innecesarias"
        ])
        
        prompt += f"""
═══════════════════════════════════════════════════════════════
REQUISITOS TÉCNICOS OBLIGATORIOS ({lang_name})
═══════════════════════════════════════════════════════════════
"""
        for i, req in enumerate(requisitos, 1):
            prompt += f"{i}. {req}\n"
        
        prompt += """
NOTAS ADICIONALES:
- Código limpio y bien comentado
- Manejo de errores robusto
- Seguir convenciones del lenguaje

═══════════════════════════════════════════════════════════════
FORMATO DE SALIDA
═══════════════════════════════════════════════════════════════
Genera el código completo en formato JSON:
{
    "files": {
        "<archivo1>": "<contenido completo>",
        "<archivo2>": "<contenido completo>"
    },
    "message": "Explicación de lo creado y sugerencias"
}
"""
        
        return prompt


class TaskOrchestrator:
    """
    FASE 5-6: Orquestador de Tareas y Ejecución
    Divide el trabajo en tareas y controla la ejecución
    """
    
    def create_plan(self, intent: IntentAnalysis, research: Optional[ResearchResult]) -> ExecutionPlan:
        """Crea el plan de ejecución basado en el análisis y lenguaje detectado"""
        tareas = []
        archivos = []
        dependencias = []
        
        lang = intent.lenguaje_programacion
        
        # Obtener archivos del template de lenguaje si existe
        if lang in LANGUAGE_TEMPLATES:
            archivos = LANGUAGE_TEMPLATES[lang].get("files", [])[:]
        
        # Determinar tareas según el lenguaje y tipo de tarea
        if lang == ProgrammingLanguage.PYTHON_FLASK:
            tareas = [
                TaskItem(1, "Crear aplicación Flask principal", "pendiente", "app.py"),
                TaskItem(2, "Configurar rutas y endpoints", "pendiente", "app.py"),
                TaskItem(3, "Crear templates HTML con Jinja2", "pendiente", "templates/"),
                TaskItem(4, "Agregar estilos CSS", "pendiente", "static/css/styles.css"),
                TaskItem(5, "Generar requirements.txt", "pendiente", "requirements.txt"),
            ]
            dependencias = ["flask", "gunicorn"]
            
        elif lang == ProgrammingLanguage.PYTHON_FASTAPI:
            tareas = [
                TaskItem(1, "Crear aplicación FastAPI", "pendiente", "main.py"),
                TaskItem(2, "Definir modelos Pydantic", "pendiente", "schemas.py"),
                TaskItem(3, "Implementar endpoints API", "pendiente", "main.py"),
                TaskItem(4, "Configurar validaciones", "pendiente"),
                TaskItem(5, "Generar requirements.txt", "pendiente", "requirements.txt"),
            ]
            dependencias = ["fastapi", "uvicorn", "pydantic"]
            
        elif lang == ProgrammingLanguage.PYTHON_GENERAL:
            tareas = [
                TaskItem(1, "Crear módulo principal", "pendiente", "main.py"),
                TaskItem(2, "Implementar funciones/clases", "pendiente"),
                TaskItem(3, "Agregar documentación", "pendiente"),
                TaskItem(4, "Generar requirements.txt si hay dependencias", "pendiente"),
            ]
            archivos = ["main.py", "requirements.txt"]
            
        elif lang == ProgrammingLanguage.NODEJS_EXPRESS:
            tareas = [
                TaskItem(1, "Crear servidor Express", "pendiente", "server.js"),
                TaskItem(2, "Configurar rutas API", "pendiente", "routes/index.js"),
                TaskItem(3, "Agregar middlewares", "pendiente"),
                TaskItem(4, "Generar package.json", "pendiente", "package.json"),
            ]
            dependencias = ["express"]
            archivos = ["server.js", "package.json", "routes/index.js"]
            
        elif lang == ProgrammingLanguage.REACT:
            tareas = [
                TaskItem(1, "Crear componente principal App", "pendiente", "src/App.jsx"),
                TaskItem(2, "Crear componentes adicionales", "pendiente", "src/components/"),
                TaskItem(3, "Agregar estilos CSS", "pendiente", "src/App.css"),
                TaskItem(4, "Configurar estado y hooks", "pendiente"),
            ]
            dependencias = ["react", "react-dom"]
            archivos = ["src/App.jsx", "src/App.css", "src/index.jsx"]
            
        elif lang == ProgrammingLanguage.SQL:
            tareas = [
                TaskItem(1, "Diseñar esquema de base de datos", "pendiente", "schema.sql"),
                TaskItem(2, "Crear tablas con constraints", "pendiente"),
                TaskItem(3, "Agregar índices de rendimiento", "pendiente"),
                TaskItem(4, "Crear queries de ejemplo", "pendiente", "queries.sql"),
            ]
            archivos = ["schema.sql", "queries.sql"]
            
        elif lang == ProgrammingLanguage.DOCKER:
            tareas = [
                TaskItem(1, "Crear Dockerfile", "pendiente", "Dockerfile"),
                TaskItem(2, "Configurar docker-compose.yml", "pendiente", "docker-compose.yml"),
                TaskItem(3, "Agregar .dockerignore", "pendiente", ".dockerignore"),
            ]
            archivos = ["Dockerfile", "docker-compose.yml", ".dockerignore"]
            
        elif intent.tipo_tarea in [TaskType.CREAR_WEB, TaskType.CREAR_LANDING, TaskType.CREAR_DASHBOARD]:
            tareas = [
                TaskItem(1, "Crear estructura HTML con secciones", "pendiente", "index.html"),
                TaskItem(2, "Diseñar estilos CSS responsivos", "pendiente", "styles.css"),
                TaskItem(3, "Implementar interactividad JavaScript", "pendiente", "script.js"),
                TaskItem(4, "Optimizar para mobile y rendimiento", "pendiente"),
                TaskItem(5, "Verificar accesibilidad y SEO básico", "pendiente"),
            ]
            archivos = ["index.html", "styles.css", "script.js"]
            
        elif intent.tipo_tarea == TaskType.CREAR_FORMULARIO:
            tareas = [
                TaskItem(1, "Crear formulario HTML con validación", "pendiente", "index.html"),
                TaskItem(2, "Estilos del formulario", "pendiente", "styles.css"),
                TaskItem(3, "Validación JavaScript", "pendiente", "script.js"),
            ]
            archivos = ["index.html", "styles.css", "script.js"]
            
        else:
            tareas = [
                TaskItem(1, "Analizar requerimiento", "pendiente"),
                TaskItem(2, "Implementar solución", "pendiente"),
                TaskItem(3, "Verificar resultado", "pendiente"),
            ]
        
        # Estimar tiempo
        tiempo = f"{len(tareas) * 2} minutos aprox."
        
        # Identificar riesgos
        riesgos = []
        if intent.nivel_detalle == "vago":
            riesgos.append("Especificaciones vagas - resultado puede necesitar ajustes")
        if not intent.especificaciones_usuario.get("recursos_disponibles"):
            riesgos.append("Sin recursos (logo/fotos) - se usarán placeholders")
        
        return ExecutionPlan(
            tareas=tareas,
            tiempo_estimado=tiempo,
            riesgos=riesgos if riesgos else ["Ninguno identificado"],
            archivos_a_crear=archivos,
            dependencias=dependencias
        )
    
    def format_plan_message(self, plan: ExecutionPlan) -> str:
        """Formatea el plan para mostrar al usuario"""
        message = "📋 **PLAN DE EJECUCIÓN**\n\n"
        message += "**Tareas a realizar:**\n"
        for tarea in plan.tareas:
            message += f"  {tarea.id}. {tarea.descripcion}\n"
        
        message += f"\n⏱️ **Tiempo estimado:** {plan.tiempo_estimado}\n"
        
        if plan.archivos_a_crear:
            message += f"\n📁 **Archivos a crear:**\n"
            for archivo in plan.archivos_a_crear:
                message += f"  • {archivo}\n"
        
        if plan.riesgos:
            message += f"\n⚠️ **Consideraciones:**\n"
            for riesgo in plan.riesgos:
                message += f"  • {riesgo}\n"
        
        message += "\n¿Procedo con la generación? (sí/no/ajustar)"
        
        return message


class OutputVerifier:
    """
    FASE 7: Verificador de Salidas
    Valida que el código generado sea correcto y completo
    """
    
    def verify(self, files: Dict[str, str], intent: IntentAnalysis, 
               plan: ExecutionPlan) -> VerificationResult:
        """Verifica el código generado"""
        errores = []
        advertencias = []
        puntuacion = 100
        
        # Verificar que existan los archivos esperados
        for archivo_esperado in plan.archivos_a_crear:
            if archivo_esperado not in files:
                errores.append(f"Archivo faltante: {archivo_esperado}")
                puntuacion -= 20
        
        # Verificar HTML
        html_content = files.get("index.html", "")
        if html_content:
            # Verificar estructura básica
            if "<!DOCTYPE html>" not in html_content:
                advertencias.append("Falta <!DOCTYPE html>")
                puntuacion -= 5
            if "<meta name=\"viewport\"" not in html_content:
                advertencias.append("Falta meta viewport para responsive")
                puntuacion -= 10
            if "</html>" not in html_content:
                errores.append("HTML incompleto - falta cierre </html>")
                puntuacion -= 15
            
            # Verificar secciones requeridas
            secciones_usuario = intent.especificaciones_usuario.get("secciones", [])
            for seccion in secciones_usuario:
                if seccion.lower() not in html_content.lower():
                    advertencias.append(f"Posible sección faltante: {seccion}")
                    puntuacion -= 5
        
        # Verificar CSS
        css_content = files.get("styles.css", "")
        if css_content:
            if "@media" not in css_content:
                advertencias.append("No se detectan media queries - verificar responsive")
                puntuacion -= 10
            if ":root" not in css_content:
                advertencias.append("No se usan variables CSS")
                puntuacion -= 5
        
        # Verificar JS
        js_content = files.get("script.js", "")
        if js_content:
            if "var " in js_content and "const " not in js_content and "let " not in js_content:
                advertencias.append("Usar const/let en lugar de var")
                puntuacion -= 5
        
        # Calcular flags booleanos
        sintaxis_valida = len([e for e in errores if "incompleto" in e.lower()]) == 0
        completitud = len(errores) == 0
        funcionalidad = len([e for e in errores if "faltante" in e.lower()]) == 0
        responsive = "@media" in css_content if css_content else False
        coincide = puntuacion >= 70
        
        return VerificationResult(
            sintaxis_valida=sintaxis_valida,
            completitud=completitud,
            funcionalidad=funcionalidad,
            responsive=responsive,
            coincide_requisitos=coincide,
            errores=errores,
            advertencias=advertencias,
            puntuacion=max(0, puntuacion)
        )
    
    def format_verification_message(self, result: VerificationResult) -> str:
        """Formatea el resultado de verificación"""
        message = "🔍 **VERIFICACIÓN AUTOMÁTICA**\n\n"
        
        checks = [
            ("Sintaxis válida", result.sintaxis_valida),
            ("Código completo", result.completitud),
            ("Funcionalidad OK", result.funcionalidad),
            ("Diseño responsive", result.responsive),
            ("Cumple requisitos", result.coincide_requisitos),
        ]
        
        for check_name, passed in checks:
            icon = "✅" if passed else "❌"
            message += f"{icon} {check_name}\n"
        
        message += f"\n📊 **Puntuación:** {result.puntuacion}/100\n"
        
        if result.errores:
            message += "\n🔴 **Errores encontrados:**\n"
            for error in result.errores:
                message += f"  • {error}\n"
        
        if result.advertencias:
            message += "\n🟡 **Advertencias:**\n"
            for adv in result.advertencias:
                message += f"  • {adv}\n"
        
        return message


class AIConstructorService:
    """
    Servicio Principal del Constructor de IA
    Orquesta todas las fases y mantiene el estado de las sesiones
    
    Ahora con AIToolkit integrado para operaciones reales de archivos,
    ejecución de comandos, detección de errores y análisis de proyecto.
    """
    
    def __init__(self, ai_service=None, db_manager=None, project_root: Optional[str] = None):
        self.ai_service = ai_service
        self.db_manager = db_manager
        self.sessions: Dict[str, ConstructorSession] = {}
        self.project_root = project_root or os.getcwd()
        
        # Inicializar componentes de fases
        self.intent_parser = IntentParser()
        self.research_engine = ResearchEngine()
        self.clarification_manager = ClarificationManager()
        self.prompt_builder = PromptBuilder()
        self.task_orchestrator = TaskOrchestrator()
        self.output_verifier = OutputVerifier()
        
        # Inicializar AIToolkit para operaciones reales
        self.toolkit_enabled = TOOLKIT_AVAILABLE
        self.file_toolkit: Optional[Any] = None
        self.command_executor: Optional[Any] = None
        self.error_detector: Optional[Any] = None
        self.project_analyzer: Optional[Any] = None
        
        if TOOLKIT_AVAILABLE and AIFileToolkit and AICommandExecutor and AIErrorDetector and AIProjectAnalyzer:
            self.file_toolkit = AIFileToolkit(self.project_root)
            self.command_executor = AICommandExecutor(self.project_root)
            self.error_detector = AIErrorDetector()
            self.project_analyzer = AIProjectAnalyzer(self.project_root)
            logger.info("AIConstructorService initialized with AIToolkit (full capabilities)")
        else:
            logger.warning("AIConstructorService initialized WITHOUT AIToolkit (limited capabilities)")
        
        logger.info(f"AIConstructorService initialized - Toolkit: {self.toolkit_enabled}")
    
    def get_or_create_session(self, user_id: str) -> ConstructorSession:
        """Obtiene o crea una sesión para el usuario"""
        session_id = f"constructor_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if user_id not in self.sessions:
            self.sessions[user_id] = ConstructorSession(
                session_id=session_id,
                user_id=user_id,
                fase_actual=1
            )
        
        return self.sessions[user_id]
    
    def reset_session(self, user_id: str) -> ConstructorSession:
        """Reinicia la sesión del usuario"""
        session_id = f"constructor_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.sessions[user_id] = ConstructorSession(
            session_id=session_id,
            user_id=user_id,
            fase_actual=1
        )
        return self.sessions[user_id]
    
    def process_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Procesa un mensaje del usuario a través del flujo de fases
        Retorna la respuesta y el estado actual
        """
        session = self.get_or_create_session(user_id)
        
        # Guardar mensaje en historial
        session.historial.append({"role": "user", "content": message, "timestamp": datetime.now().isoformat()})
        
        # Si estaba esperando clarificación, procesarla
        if session.esperando_clarificacion:
            return self._process_clarification_response(session, message)
        
        # Si estaba esperando confirmación del plan
        if session.esperando_confirmacion:
            return self._process_confirmation(session, message)
        
        # Nuevo flujo desde fase 1
        return self._run_full_flow(session, message)
    
    def _run_full_flow(self, session: ConstructorSession, message: str) -> Dict[str, Any]:
        """Ejecuta el flujo completo de fases"""
        
        if flow_logger:
            flow_logger.start_session(session.session_id, session.user_id, message)
        
        # ═══════════════════════════════════════════════════════════════
        # FASE 1: ANÁLISIS INICIAL + CONTEXTO DEL PROYECTO
        # ═══════════════════════════════════════════════════════════════
        session.fase_actual = 1
        if flow_logger:
            flow_logger.start_fase(session.user_id, 1, "Análisis de Intención", {"mensaje": message})
        
        # Analizar el proyecto para obtener contexto (si toolkit disponible)
        project_context = None
        if self.toolkit_enabled and self.project_analyzer:
            try:
                analysis_result = self.project_analyzer.analyze_project()
                if analysis_result.get("success"):
                    project_context = analysis_result.get("analysis")
                    logger.info(f"[FASE 1] Proyecto analizado: {project_context.get('language', 'unknown')}, framework: {project_context.get('framework', 'none')}")
            except Exception as e:
                logger.warning(f"[FASE 1] No se pudo analizar el proyecto: {e}")
        
        intent = self.intent_parser.analyze(message)
        session.intent = intent
        
        # Agregar contexto del proyecto al intent si está disponible
        if project_context:
            intent.especificaciones_usuario["project_context"] = project_context
        
        if flow_logger:
            flow_logger.end_fase(session.user_id, 1, {
                "tipo_tarea": intent.tipo_tarea.value,
                "contexto": intent.contexto,
                "nivel_detalle": intent.nivel_detalle,
                "requiere_clarificacion": intent.requiere_clarificacion,
                "project_analyzed": project_context is not None
            })
        
        logger.info(f"[FASE 1] Intent analizado: {intent.tipo_tarea.value}, contexto: {intent.contexto}")
        
        # ═══════════════════════════════════════════════════════════════
        # ACCIONES INMEDIATAS: Operaciones que no requieren plan
        # ═══════════════════════════════════════════════════════════════
        immediate_actions = {
            TaskType.LEER_ARCHIVO, TaskType.LISTAR_ARCHIVOS, TaskType.VER_ESTRUCTURA,
            TaskType.VER_LOGS, TaskType.BUSCAR_CODIGO, TaskType.ANALIZAR_PROYECTO,
            TaskType.EJECUTAR_COMANDO, TaskType.INSTALAR_DEPENDENCIA, TaskType.EXPLICAR,
            TaskType.CONSULTA_GENERAL
        }
        
        if intent.tipo_tarea in immediate_actions:
            return self._execute_immediate_action(session, message, intent)
        
        # ═══════════════════════════════════════════════════════════════
        # FASE 2: INVESTIGACIÓN (si es necesaria)
        # ═══════════════════════════════════════════════════════════════
        research = None
        if intent.requiere_investigacion:
            session.fase_actual = 2
            if flow_logger:
                flow_logger.start_fase(session.user_id, 2, "Investigación Autónoma", {"contexto": intent.contexto})
            
            research = self.research_engine.research(intent)
            session.research = research
            
            if flow_logger:
                flow_logger.end_fase(session.user_id, 2, {
                    "estilo": research.estilo,
                    "elementos": research.elementos_recomendados[:5],
                    "paleta": research.paleta_sugerida
                })
            
            logger.info(f"[FASE 2] Investigación completada: {research.estilo}")
        
        # ═══════════════════════════════════════════════════════════════
        # FASE 3: CLARIFICACIÓN (si es necesaria)
        # ═══════════════════════════════════════════════════════════════
        if intent.requiere_clarificacion:
            session.fase_actual = 3
            if flow_logger:
                flow_logger.start_fase(session.user_id, 3, "Clarificación", {"requiere": True})
            
            questions = self.clarification_manager.generate_questions(intent, research)
            
            if questions:
                session.preguntas_pendientes = questions
                session.esperando_clarificacion = True
                
                clarification_msg = self.clarification_manager.format_clarification_message(
                    intent, research, questions
                )
                
                if flow_logger:
                    flow_logger.end_fase(session.user_id, 3, {
                        "preguntas_generadas": len(questions),
                        "preguntas": questions,
                        "esperando_respuesta": True
                    })
                
                return {
                    "success": True,
                    "response": clarification_msg,
                    "fase": session.fase_actual,
                    "fase_nombre": "Clarificación",
                    "esperando_input": True,
                    "session": session.to_dict()
                }
        
        # Si no necesita clarificación, continuar al plan
        return self._continue_to_plan(session)
    
    def _process_clarification_response(self, session: ConstructorSession, response: str) -> Dict[str, Any]:
        """Procesa la respuesta de clarificación del usuario"""
        clarification = self.clarification_manager.process_response(
            response, session.preguntas_pendientes
        )
        session.clarification = clarification
        session.esperando_clarificacion = False
        session.preguntas_pendientes = []
        
        logger.info(f"[FASE 3] Clarificación procesada: {clarification.preferencias_detectadas}")
        
        return self._continue_to_plan(session)
    
    def _continue_to_plan(self, session: ConstructorSession) -> Dict[str, Any]:
        """Continúa con las fases 4 y 5: Prompt y Plan"""
        
        # ═══════════════════════════════════════════════════════════════
        # FASE 4: CONSTRUCCIÓN DEL PROMPT MAESTRO
        # ═══════════════════════════════════════════════════════════════
        session.fase_actual = 4
        if flow_logger:
            flow_logger.start_fase(session.user_id, 4, "Construcción Prompt Maestro", {
                "intent": session.intent.tipo_tarea.value if session.intent else None,
                "tiene_research": session.research is not None,
                "tiene_clarificacion": session.clarification is not None
            })
        
        if not session.intent:
            session.esperando_confirmacion = False
            session.esperando_clarificacion = False
            return {
                "success": False,
                "error": "No se pudo analizar la intención del mensaje. Por favor, intenta reformular tu solicitud.",
                "fase": session.fase_actual,
                "recoverable": True,
                "session": session.to_dict()
            }
        
        prompt_maestro = self.prompt_builder.build(
            session.intent, session.research, session.clarification
        )
        session.prompt_maestro = prompt_maestro
        
        if flow_logger:
            flow_logger.end_fase(session.user_id, 4, {
                "prompt_length": len(prompt_maestro),
                "prompt_preview": prompt_maestro[:500] + "..." if len(prompt_maestro) > 500 else prompt_maestro
            })
        
        logger.info(f"[FASE 4] Prompt maestro construido ({len(prompt_maestro)} chars)")
        
        # ═══════════════════════════════════════════════════════════════
        # FASE 5: PRESENTACIÓN DEL PLAN
        # ═══════════════════════════════════════════════════════════════
        session.fase_actual = 5
        if flow_logger:
            flow_logger.start_fase(session.user_id, 5, "Generación del Plan", {
                "tipo_tarea": session.intent.tipo_tarea.value if session.intent else None
            })
        
        plan = self.task_orchestrator.create_plan(session.intent, session.research)  # session.intent ya validado arriba
        session.plan = plan
        session.esperando_confirmacion = True
        
        plan_message = self.task_orchestrator.format_plan_message(plan)
        
        if flow_logger:
            flow_logger.end_fase(session.user_id, 5, {
                "tareas": len(plan.tareas),
                "archivos": plan.archivos_a_crear,
                "tiempo_estimado": plan.tiempo_estimado,
                "esperando_confirmacion": True
            })
        
        return {
            "success": True,
            "response": plan_message,
            "fase": session.fase_actual,
            "fase_nombre": "Presentación del Plan",
            "esperando_input": True,
            "plan": plan.to_dict(),
            "session": session.to_dict()
        }
    
    def _process_confirmation(self, session: ConstructorSession, response: str) -> Dict[str, Any]:
        """Procesa la confirmación del usuario para ejecutar"""
        response_lower = response.lower().strip()
        
        # Detectar confirmación
        confirmaciones = ["sí", "si", "dale", "procede", "ok", "adelante", "hazlo", "yes", "go"]
        rechazos = ["no", "cancelar", "parar", "stop", "espera"]
        
        if any(c in response_lower for c in rechazos):
            session.esperando_confirmacion = False
            return {
                "success": True,
                "response": "Entendido. ¿Qué te gustaría ajustar del plan? Puedes decirme los cambios o empezar de nuevo.",
                "fase": session.fase_actual,
                "cancelado": True,
                "session": session.to_dict()
            }
        
        if any(c in response_lower for c in confirmaciones):
            session.esperando_confirmacion = False
            return self._execute_generation(session)
        
        # No se entiende la respuesta
        return {
            "success": True,
            "response": "No entendí tu respuesta. Por favor responde 'sí' para proceder o 'no' para cancelar/ajustar.",
            "fase": session.fase_actual,
            "esperando_input": True,
            "session": session.to_dict()
        }
    
    def _execute_generation(self, session: ConstructorSession) -> Dict[str, Any]:
        """Ejecuta la generación del código (Fase 6)"""
        
        # ═══════════════════════════════════════════════════════════════
        # FASE 6: EJECUCIÓN CONTROLADA
        # ═══════════════════════════════════════════════════════════════
        session.fase_actual = 6
        
        # Marcar tareas como en progreso
        if session.plan and session.plan.tareas:
            for tarea in session.plan.tareas:
                tarea.estado = "en_progreso"
        
        # Usar el AI Service para generar el código
        if not self.ai_service:
            return {
                "success": False,
                "error": "No hay servicio de IA configurado",
                "fase": session.fase_actual,
                "session": session.to_dict()
            }
        
        # Construir mensaje con el prompt maestro
        generation_prompt = f"""Eres BUNK3R Code Builder. Genera el código completo siguiendo estas instrucciones:

{session.prompt_maestro}

IMPORTANTE: Responde ÚNICAMENTE con el JSON solicitado, sin texto adicional antes o después.
"""
        
        # Llamar al AI Service
        result = self.ai_service.chat(
            user_id=f"constructor_{session.user_id}",
            message=generation_prompt,
            enable_auto_rectify=True
        )
        
        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error", "Error desconocido en la generación"),
                "fase": session.fase_actual,
                "session": session.to_dict()
            }
        
        # Parsear la respuesta para extraer los archivos
        response_text = result.get("response", "")
        files, parse_message = self._parse_generated_code(response_text)
        
        if not files:
            # Si no se pudo parsear, intentar de nuevo con instrucciones más claras
            return {
                "success": True,
                "response": f"He generado el código. Aquí está el resultado:\n\n{response_text}",
                "fase": session.fase_actual,
                "raw_response": True,
                "session": session.to_dict()
            }
        
        session.archivos_generados = files
        
        # ═════════════════════════════════════════════════════════════════════
        # FASE 6.1: GUARDAR ARCHIVOS EN DISCO REAL (usando AIToolkit)
        # ═════════════════════════════════════════════════════════════════════
        files_saved_to_disk = []
        disk_save_errors = []
        
        # Extensiones de archivo permitidas para guardar
        ALLOWED_EXTENSIONS = {'.html', '.css', '.js', '.jsx', '.ts', '.tsx', '.json', '.py', '.md', '.txt', '.svg', '.vue'}
        
        if self.toolkit_enabled and self.file_toolkit and files:
            logger.info("[FASE 6.1] Guardando archivos en disco real...")
            base_path = "ai_generated"
            
            for filename, content in files.items():
                try:
                    # Paso 1: Sanitizar nombre (solo caracteres permitidos)
                    safe_filename = re.sub(r'[^a-zA-Z0-9_\-.]', '_', os.path.basename(filename))
                    
                    # Paso 2: Validar extensión
                    file_ext = os.path.splitext(safe_filename)[1].lower()
                    if file_ext not in ALLOWED_EXTENSIONS:
                        disk_save_errors.append({"file": filename, "error": f"Extensión {file_ext} no permitida"})
                        logger.warning(f"[FASE 6.1] Extensión no permitida: {filename}")
                        continue
                    
                    # Paso 3: Construir ruta final y validar con resolve()
                    file_path = f"{base_path}/{safe_filename}"
                    full_resolved = os.path.abspath(os.path.join(self.project_root, file_path))
                    base_resolved = os.path.abspath(os.path.join(self.project_root, base_path))
                    
                    # Verificar que la ruta final está dentro del directorio base
                    if not full_resolved.startswith(base_resolved):
                        disk_save_errors.append({"file": filename, "error": "Path traversal detectado - archivo bloqueado"})
                        logger.warning(f"[FASE 6.1] Path traversal bloqueado después de resolve: {filename}")
                        continue
                    
                    result = self.file_toolkit.write_file(file_path, content)
                    if result.get("success"):
                        files_saved_to_disk.append(file_path)
                        logger.info(f"[FASE 6.1] Archivo guardado: {file_path}")
                    else:
                        disk_save_errors.append({"file": filename, "error": result.get("error")})
                        logger.warning(f"[FASE 6.1] Error guardando {filename}: {result.get('error')}")
                except Exception as e:
                    disk_save_errors.append({"file": filename, "error": str(e)})
                    logger.error(f"[FASE 6.1] Excepción guardando {filename}: {e}")
        
        # ═════════════════════════════════════════════════════════════════════
        # FASE 6.2: DETECTAR DEPENDENCIAS (instalación manual requerida)
        # ═════════════════════════════════════════════════════════════════════
        dependencies_installed = []
        dependencies_detected = []
        dependency_errors = []
        
        # Lista blanca de paquetes seguros que se pueden instalar automáticamente
        SAFE_PYTHON_PACKAGES = {
            'flask', 'requests', 'beautifulsoup4', 'pillow', 'pandas', 'numpy',
            'matplotlib', 'jinja2', 'werkzeug', 'gunicorn', 'pytest', 'click',
            'pyyaml', 'python-dotenv', 'sqlalchemy', 'aiohttp', 'httpx'
        }
        SAFE_NODE_PACKAGES = {
            'express', 'react', 'vue', 'axios', 'lodash', 'moment', 'dayjs',
            'tailwindcss', 'postcss', 'autoprefixer', 'vite', 'webpack',
            'typescript', 'eslint', 'prettier', 'jest', 'nodemon'
        }
        
        if self.toolkit_enabled and self.command_executor:
            # Detectar dependencias en el código generado
            all_code = "\n".join(files.values())
            
            # Detectar imports de Python
            python_imports = re.findall(r'^(?:from|import)\s+([a-zA-Z_][a-zA-Z0-9_]*)', all_code, re.MULTILINE)
            # Detectar requires de Node.js
            node_requires = re.findall(r"require\(['\"]([^'\"]+)['\"]\)", all_code)
            node_imports = re.findall(r"from\s+['\"]([^'\"]+)['\"]", all_code)
            
            # Filtrar dependencias estándar de Python
            python_std_libs = {'os', 'sys', 'json', 're', 'typing', 'datetime', 'collections', 'math', 
                              'random', 'functools', 'itertools', 'pathlib', 'logging', 'time', 'io',
                              'dataclasses', 'enum', 'abc', 'copy', 'operator', 'html', 'urllib'}
            external_python = [pkg for pkg in set(python_imports) if pkg.lower() not in python_std_libs]
            
            # Detectar paquetes Node.js externos (no rutas relativas)
            external_node = [pkg for pkg in set(node_requires + node_imports) 
                            if not pkg.startswith('.') and not pkg.startswith('/')]
            
            logger.info(f"[FASE 6.2] Dependencias detectadas - Python: {external_python}, Node: {external_node}")
            
            # Solo instalar paquetes de la lista blanca (máximo 3 por seguridad)
            safe_python_to_install = [pkg for pkg in external_python if pkg.lower() in SAFE_PYTHON_PACKAGES][:3]
            safe_node_to_install = [pkg for pkg in external_node if pkg.lower() in SAFE_NODE_PACKAGES][:3]
            
            # Registrar paquetes detectados pero no instalados
            for pkg in external_python:
                if pkg.lower() not in SAFE_PYTHON_PACKAGES:
                    dependencies_detected.append(f"pip:{pkg} (requiere instalación manual)")
            for pkg in external_node:
                if pkg.lower() not in SAFE_NODE_PACKAGES:
                    dependencies_detected.append(f"npm:{pkg} (requiere instalación manual)")
            
            # Instalar dependencias seguras de Python
            for pkg in safe_python_to_install:
                try:
                    install_result = self.command_executor.install_package(pkg, "pip")
                    if install_result.get("success"):
                        dependencies_installed.append(f"pip:{pkg}")
                        logger.info(f"[FASE 6.2] Instalado pip: {pkg}")
                    else:
                        dependency_errors.append({"package": pkg, "manager": "pip", "error": install_result.get("error")})
                except Exception as e:
                    dependency_errors.append({"package": pkg, "manager": "pip", "error": str(e)})
            
            # Instalar dependencias seguras de Node
            for pkg in safe_node_to_install:
                try:
                    install_result = self.command_executor.install_package(pkg, "npm")
                    if install_result.get("success"):
                        dependencies_installed.append(f"npm:{pkg}")
                        logger.info(f"[FASE 6.2] Instalado npm: {pkg}")
                    else:
                        dependency_errors.append({"package": pkg, "manager": "npm", "error": install_result.get("error")})
                except Exception as e:
                    dependency_errors.append({"package": pkg, "manager": "npm", "error": str(e)})
        
        # Marcar tareas como completadas
        if session.plan and session.plan.tareas:
            for tarea in session.plan.tareas:
                tarea.estado = "completada"
        
        logger.info(f"[FASE 6] Generación completada: {list(files.keys())}, guardados: {len(files_saved_to_disk)}, deps: {len(dependencies_installed)}")
        
        # ═══════════════════════════════════════════════════════════════
        # FASE 7: VERIFICACIÓN AUTOMÁTICA + DETECCIÓN DE ERRORES
        # ═══════════════════════════════════════════════════════════════
        session.fase_actual = 7
        
        if not session.intent or not session.plan:
            logger.error("[FASE 7] Estado inconsistente: intent o plan no disponible")
            return {
                "success": False,
                "error": "Error interno: estado de sesión inconsistente. Por favor, reinicia el proceso.",
                "fase": session.fase_actual,
                "files": files,
                "session": session.to_dict()
            }
        
        # Verificación tradicional
        verification = self.output_verifier.verify(files, session.intent, session.plan)
        session.verification = verification
        verification_msg = self.output_verifier.format_verification_message(verification)
        
        # Detección de errores con AIToolkit
        detected_errors = []
        if self.toolkit_enabled and self.error_detector and files:
            for filename, content in files.items():
                # Determinar lenguaje del archivo
                lang = "python"
                if filename.endswith(('.js', '.jsx', '.ts', '.tsx')):
                    lang = "javascript"
                elif filename.endswith('.html'):
                    lang = "html"
                elif filename.endswith('.css'):
                    lang = "css"
                
                # Detectar errores en el código
                try:
                    error_result = self.error_detector.detect_errors([content], lang)
                    if error_result.get("success") and error_result.get("errors"):
                        for err in error_result["errors"]:
                            detected_errors.append({
                                "file": filename,
                                "type": err.get("type"),
                                "message": err.get("message"),
                                "line": err.get("line")
                            })
                except Exception as e:
                    logger.warning(f"[FASE 7] Error detectando errores en {filename}: {e}")
        
        if detected_errors:
            verification_msg += f"\n\n🔍 **Errores detectados automáticamente:** {len(detected_errors)}\n"
            for err in detected_errors[:5]:  # Mostrar máximo 5
                verification_msg += f"  • {err['file']}: {err['message']}\n"
        
        logger.info(f"[FASE 7] Verificación: {verification.puntuacion}/100, Errores detectados: {len(detected_errors)}")
        
        # ═══════════════════════════════════════════════════════════════
        # FASE 8: ENTREGA FINAL
        # ═══════════════════════════════════════════════════════════════
        session.fase_actual = 8
        
        # Información adicional de toolkit
        toolkit_info = {
            "files_saved": files_saved_to_disk,
            "disk_errors": disk_save_errors,
            "dependencies_installed": dependencies_installed,
            "dependencies_detected": dependencies_detected,
            "dependency_errors": dependency_errors,
            "detected_errors": detected_errors
        }
        
        delivery_message = self._format_delivery(session, verification_msg, parse_message, toolkit_info)
        
        return {
            "success": True,
            "response": delivery_message,
            "fase": session.fase_actual,
            "fase_nombre": "Entrega Final",
            "files": files,
            "files_saved_to_disk": files_saved_to_disk,
            "dependencies_installed": dependencies_installed,
            "detected_errors": detected_errors,
            "verification": verification.to_dict(),
            "session": session.to_dict()
        }
    
    def _parse_generated_code(self, response: str) -> Tuple[Dict[str, str], str]:
        """Intenta parsear el código generado del response"""
        files = {}
        message = ""
        
        # Buscar JSON en la respuesta
        json_patterns = [
            r'\{[\s\S]*"files"[\s\S]*\}',  # Formato esperado
            r'```json\s*([\s\S]*?)\s*```',  # Código en bloque
            r'```\s*([\s\S]*?)\s*```'  # Cualquier bloque de código
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, response)
            for match in matches:
                try:
                    # Limpiar el match
                    json_str = match if isinstance(match, str) else match
                    json_str = json_str.strip()
                    
                    # Intentar parsear
                    data = json.loads(json_str)
                    
                    if "files" in data:
                        files = data["files"]
                        message = data.get("message", "Código generado exitosamente")
                        return files, message
                except json.JSONDecodeError:
                    continue
        
        # Si no se encontró JSON, buscar bloques de código individuales
        html_match = re.search(r'```html\s*([\s\S]*?)\s*```', response)
        css_match = re.search(r'```css\s*([\s\S]*?)\s*```', response)
        js_match = re.search(r'```(?:javascript|js)\s*([\s\S]*?)\s*```', response)
        
        if html_match:
            files["index.html"] = html_match.group(1).strip()
        if css_match:
            files["styles.css"] = css_match.group(1).strip()
        if js_match:
            files["script.js"] = js_match.group(1).strip()
        
        if files:
            message = "Código extraído de bloques"
        
        return files, message
    
    def _format_delivery(self, session: ConstructorSession, verification_msg: str, 
                         ai_message: str, toolkit_info: Optional[Dict] = None) -> str:
        """Formatea el mensaje de entrega final con información del toolkit"""
        message = "✨ **ENTREGA COMPLETADA**\n\n"
        
        # Resumen de lo creado
        if session.archivos_generados:
            message += "📁 **Archivos creados:**\n"
            for filename in session.archivos_generados.keys():
                message += f"  • {filename}\n"
            message += "\n"
        
        # Información de archivos guardados en disco (si toolkit disponible)
        if toolkit_info and toolkit_info.get("files_saved"):
            message += "💾 **Guardados en disco:**\n"
            for path in toolkit_info["files_saved"]:
                message += f"  • {path}\n"
            message += "\n"
        
        # Dependencias instaladas
        if toolkit_info and toolkit_info.get("dependencies_installed"):
            message += "📦 **Dependencias instaladas:**\n"
            for dep in toolkit_info["dependencies_installed"]:
                message += f"  • {dep}\n"
            message += "\n"
        
        # Dependencias detectadas pero no instaladas automáticamente
        if toolkit_info and toolkit_info.get("dependencies_detected"):
            message += "📋 **Dependencias detectadas (instalación manual):**\n"
            for dep in toolkit_info["dependencies_detected"][:5]:
                message += f"  • {dep}\n"
            message += "\n"
        
        # Errores de dependencias (si hay)
        if toolkit_info and toolkit_info.get("dependency_errors"):
            message += "⚠️ **Advertencias de dependencias:**\n"
            for err in toolkit_info["dependency_errors"][:3]:
                message += f"  • {err.get('package')}: {err.get('error', 'error desconocido')[:50]}\n"
            message += "\n"
        
        # Secciones implementadas
        if session.plan:
            completed = [t for t in session.plan.tareas if t.estado == "completada"]
            message += f"✅ **Tareas completadas:** {len(completed)}/{len(session.plan.tareas)}\n\n"
        
        # Verificación
        message += verification_msg
        message += "\n"
        
        # Mensaje del AI
        if ai_message:
            message += f"\n💬 **Notas:** {ai_message}\n"
        
        message += "\n¿Te gustaría que ajuste algo?"
        
        return message
    
    def get_session_status(self, user_id: str) -> Optional[Dict]:
        """Obtiene el estado de la sesión del usuario"""
        if user_id in self.sessions:
            return self.sessions[user_id].to_dict()
        return None
    
    def get_generated_files(self, user_id: str) -> Optional[Dict[str, str]]:
        """Obtiene los archivos generados en la sesión"""
        if user_id in self.sessions:
            return self.sessions[user_id].archivos_generados
        return None
    
    # ═══════════════════════════════════════════════════════════════════
    # MÉTODOS DE TOOLKIT - Operaciones reales de archivos y comandos
    # ═══════════════════════════════════════════════════════════════════
    
    def read_project_file(self, path: str, max_lines: Optional[int] = None) -> Dict[str, Any]:
        """Lee un archivo del proyecto usando AIToolkit"""
        if not self.toolkit_enabled or not self.file_toolkit:
            return {"success": False, "error": "AIToolkit no disponible"}
        return self.file_toolkit.read_file(path, max_lines)
    
    def write_project_file(self, path: str, content: str) -> Dict[str, Any]:
        """Escribe un archivo en el proyecto usando AIToolkit"""
        if not self.toolkit_enabled or not self.file_toolkit:
            return {"success": False, "error": "AIToolkit no disponible"}
        return self.file_toolkit.write_file(path, content)
    
    def edit_project_file(self, path: str, old_content: str, new_content: str) -> Dict[str, Any]:
        """Edita un archivo del proyecto usando AIToolkit"""
        if not self.toolkit_enabled or not self.file_toolkit:
            return {"success": False, "error": "AIToolkit no disponible"}
        return self.file_toolkit.edit_file(path, old_content, new_content)
    
    def list_project_files(self, path: str = ".", recursive: bool = False) -> Dict[str, Any]:
        """Lista archivos del proyecto usando AIToolkit"""
        if not self.toolkit_enabled or not self.file_toolkit:
            return {"success": False, "error": "AIToolkit no disponible"}
        return self.file_toolkit.list_directory(path, recursive)
    
    def search_in_code(self, query: str, path: str = ".") -> Dict[str, Any]:
        """Busca en el código del proyecto usando AIToolkit"""
        if not self.toolkit_enabled or not self.file_toolkit:
            return {"success": False, "error": "AIToolkit no disponible"}
        return self.file_toolkit.search_code(query, path)
    
    def run_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Ejecuta un comando usando AIToolkit (solo comandos seguros)"""
        if not self.toolkit_enabled or not self.command_executor:
            return {"success": False, "error": "AIToolkit no disponible"}
        return self.command_executor.run_command(command, timeout)
    
    def install_package(self, package: str, manager: str = "pip") -> Dict[str, Any]:
        """Instala un paquete usando AIToolkit"""
        if not self.toolkit_enabled or not self.command_executor:
            return {"success": False, "error": "AIToolkit no disponible"}
        return self.command_executor.install_package(package, manager)
    
    def detect_errors_in_logs(self, logs: List[str], language: str = "python") -> Dict[str, Any]:
        """Detecta errores en logs usando AIToolkit"""
        if not self.toolkit_enabled or not self.error_detector:
            return {"success": False, "error": "AIToolkit no disponible"}
        return self.error_detector.detect_errors(logs, language)
    
    def analyze_project_structure(self) -> Dict[str, Any]:
        """Analiza la estructura del proyecto usando AIToolkit"""
        if not self.toolkit_enabled or not self.project_analyzer:
            return {"success": False, "error": "AIToolkit no disponible"}
        return self.project_analyzer.analyze_project()
    
    def get_project_context(self) -> str:
        """Obtiene contexto del proyecto para incluir en prompts"""
        if not self.toolkit_enabled or not self.project_analyzer:
            return "Proyecto no analizado - AIToolkit no disponible"
        return self.project_analyzer.generate_context()
    
    def save_generated_files_to_disk(self, user_id: str, base_path: str = "ai_generated") -> Dict[str, Any]:
        """Guarda los archivos generados en disco real"""
        if not self.toolkit_enabled or not self.file_toolkit:
            return {"success": False, "error": "AIToolkit no disponible"}
        
        files = self.get_generated_files(user_id)
        if not files:
            return {"success": False, "error": "No hay archivos generados"}
        
        saved = []
        errors = []
        
        for filename, content in files.items():
            path = f"{base_path}/{filename}"
            result = self.file_toolkit.write_file(path, content)
            if result.get("success"):
                saved.append(path)
            else:
                errors.append({"file": filename, "error": result.get("error")})
        
        return {
            "success": len(errors) == 0,
            "saved_files": saved,
            "errors": errors,
            "total": len(files)
        }
    
    def get_toolkit_status(self) -> Dict[str, Any]:
        """Devuelve el estado del toolkit"""
        return {
            "enabled": self.toolkit_enabled,
            "file_toolkit": self.file_toolkit is not None,
            "command_executor": self.command_executor is not None,
            "error_detector": self.error_detector is not None,
            "project_analyzer": self.project_analyzer is not None,
            "project_root": self.project_root
        }
    
    # ═══════════════════════════════════════════════════════════════════
    # ACCIONES INMEDIATAS - Sin necesidad de plan/confirmación
    # ═══════════════════════════════════════════════════════════════════
    
    def _execute_immediate_action(self, session: ConstructorSession, message: str, intent: 'IntentAnalysis') -> Dict[str, Any]:
        """Ejecuta acciones inmediatas que no requieren planificación"""
        
        session.fase_actual = 6  # Fase de ejecución directa
        task_type = intent.tipo_tarea
        
        if flow_logger:
            flow_logger.start_fase(session.user_id, 6, f"Acción Inmediata: {task_type.value}", {"mensaje": message})
        
        result = {"success": False, "response": "Acción no implementada", "fase": 6}
        
        try:
            # === LEER ARCHIVO ===
            if task_type == TaskType.LEER_ARCHIVO:
                result = self._action_read_file(session, message, intent)
            
            # === LISTAR ARCHIVOS / VER ESTRUCTURA ===
            elif task_type in [TaskType.LISTAR_ARCHIVOS, TaskType.VER_ESTRUCTURA]:
                result = self._action_list_files(session, message, intent)
            
            # === BUSCAR EN CÓDIGO ===
            elif task_type == TaskType.BUSCAR_CODIGO:
                result = self._action_search_code(session, message, intent)
            
            # === ANALIZAR PROYECTO ===
            elif task_type == TaskType.ANALIZAR_PROYECTO:
                result = self._action_analyze_project(session)
            
            # === EJECUTAR COMANDO ===
            elif task_type == TaskType.EJECUTAR_COMANDO:
                result = self._action_run_command(session, message, intent)
            
            # === INSTALAR DEPENDENCIA ===
            elif task_type == TaskType.INSTALAR_DEPENDENCIA:
                result = self._action_install_package(session, message, intent)
            
            # === VER LOGS ===
            elif task_type == TaskType.VER_LOGS:
                result = self._action_view_logs(session)
            
            # === EXPLICAR / CONSULTA GENERAL ===
            elif task_type in [TaskType.EXPLICAR, TaskType.CONSULTA_GENERAL]:
                result = self._action_explain_or_consult(session, message, intent)
            
            else:
                result = {
                    "success": True,
                    "response": f"La acción '{task_type.value}' aún no está completamente implementada. ¿Puedo ayudarte con algo más específico?",
                    "fase": 6
                }
        
        except Exception as e:
            logger.error(f"[ACCIÓN INMEDIATA] Error ejecutando {task_type.value}: {e}")
            result = {
                "success": False,
                "error": f"Error ejecutando la acción: {str(e)}",
                "fase": 6
            }
        
        if flow_logger:
            flow_logger.end_fase(session.user_id, 6, {"resultado": result.get("success"), "tipo": task_type.value})
        
        result["session"] = session.to_dict()
        result["fase_nombre"] = "Acción Inmediata"
        return result
    
    def _action_read_file(self, session: ConstructorSession, message: str, intent: 'IntentAnalysis') -> Dict[str, Any]:
        """Lee un archivo del proyecto"""
        if not self.toolkit_enabled or not self.file_toolkit:
            return {"success": False, "response": "El toolkit de archivos no está disponible.", "fase": 6}
        
        # Extraer ruta del archivo del mensaje
        file_path = self._extract_file_path(message)
        if not file_path:
            # Listar archivos disponibles para ayudar al usuario
            files_result = self.file_toolkit.list_directory(".", recursive=True)
            if files_result.get("success"):
                available = [f["path"] for f in files_result.get("items", [])[:20] if f["type"] == "file"]
                return {
                    "success": True,
                    "response": f"No pude identificar qué archivo quieres ver. Archivos disponibles:\n" + "\n".join([f"• {f}" for f in available]),
                    "fase": 6,
                    "needs_clarification": True
                }
            return {"success": False, "response": "No pude identificar qué archivo quieres leer. Por favor especifica la ruta.", "fase": 6}
        
        # Leer el archivo
        read_result = self.file_toolkit.read_file(file_path, max_lines=200)
        
        if not read_result.get("success"):
            return {
                "success": False,
                "response": f"No pude leer el archivo '{file_path}': {read_result.get('error')}",
                "fase": 6
            }
        
        content = read_result.get("content", "")
        lines = read_result.get("lines", 0)
        truncated = read_result.get("truncated", False)
        
        response = f"📄 **Archivo: {file_path}** ({lines} líneas)\n\n```\n{content}\n```"
        if truncated:
            response += f"\n\n⚠️ Archivo truncado (mostrando primeras 200 líneas)"
        
        return {
            "success": True,
            "response": response,
            "fase": 6,
            "file_content": content,
            "file_path": file_path
        }
    
    def _action_list_files(self, session: ConstructorSession, message: str, intent: 'IntentAnalysis') -> Dict[str, Any]:
        """Lista archivos del proyecto"""
        if not self.toolkit_enabled or not self.file_toolkit:
            return {"success": False, "response": "El toolkit de archivos no está disponible.", "fase": 6}
        
        # Extraer ruta del mensaje o usar raíz
        path = self._extract_file_path(message) or "."
        
        list_result = self.file_toolkit.list_directory(path, recursive=True, max_depth=3)
        
        if not list_result.get("success"):
            return {
                "success": False,
                "response": f"No pude listar archivos en '{path}': {list_result.get('error')}",
                "fase": 6
            }
        
        items = list_result.get("items", [])
        
        # Formatear como árbol
        response = f"📁 **Estructura del proyecto** ({len(items)} elementos)\n\n"
        dirs = [i for i in items if i["type"] == "directory"][:15]
        files = [i for i in items if i["type"] == "file"][:25]
        
        if dirs:
            response += "**Carpetas:**\n"
            for d in dirs:
                response += f"  📁 {d['path']}/\n"
        
        if files:
            response += "\n**Archivos:**\n"
            for f in files:
                size = f.get("size", 0)
                size_str = f"{size} bytes" if size < 1024 else f"{size//1024} KB"
                response += f"  📄 {f['path']} ({size_str})\n"
        
        if len(items) > 40:
            response += f"\n... y {len(items) - 40} elementos más"
        
        return {
            "success": True,
            "response": response,
            "fase": 6,
            "items": items
        }
    
    def _action_search_code(self, session: ConstructorSession, message: str, intent: 'IntentAnalysis') -> Dict[str, Any]:
        """Busca texto en el código"""
        if not self.toolkit_enabled or not self.file_toolkit:
            return {"success": False, "response": "El toolkit de búsqueda no está disponible.", "fase": 6}
        
        # Extraer término de búsqueda
        search_term = self._extract_search_term(message)
        if not search_term:
            return {
                "success": True,
                "response": "¿Qué término deseas buscar en el código? Por ejemplo: 'busca la función login' o 'busca import flask'",
                "fase": 6,
                "needs_clarification": True
            }
        
        search_result = self.file_toolkit.search_code(search_term)
        
        if not search_result.get("success"):
            return {
                "success": False,
                "response": f"Error en la búsqueda: {search_result.get('error')}",
                "fase": 6
            }
        
        matches = search_result.get("matches", [])
        
        if not matches:
            return {
                "success": True,
                "response": f"🔍 No se encontraron resultados para: **{search_term}**",
                "fase": 6
            }
        
        response = f"🔍 **Resultados de búsqueda: '{search_term}'** ({len(matches)} coincidencias)\n\n"
        for match in matches[:15]:
            response += f"📄 **{match['file']}** (línea {match['line']}):\n"
            response += f"```\n{match['content'][:150]}\n```\n\n"
        
        if len(matches) > 15:
            response += f"... y {len(matches) - 15} coincidencias más"
        
        return {
            "success": True,
            "response": response,
            "fase": 6,
            "matches": matches
        }
    
    def _action_analyze_project(self, session: ConstructorSession) -> Dict[str, Any]:
        """Analiza la estructura del proyecto"""
        if not self.toolkit_enabled or not self.project_analyzer:
            return {"success": False, "response": "El analizador de proyecto no está disponible.", "fase": 6}
        
        analysis = self.project_analyzer.analyze_project()
        
        if not analysis.get("success"):
            return {
                "success": False,
                "response": f"Error analizando el proyecto: {analysis.get('error')}",
                "fase": 6
            }
        
        data = analysis.get("analysis", {})
        
        response = "📊 **Análisis del Proyecto**\n\n"
        response += f"**Lenguaje principal:** {data.get('language', 'No detectado')}\n"
        response += f"**Framework:** {data.get('framework', 'Ninguno detectado')}\n"
        response += f"**Total de archivos:** {data.get('total_files', 0)}\n"
        
        if data.get("dependencies"):
            response += f"\n**Dependencias ({len(data['dependencies'])}):**\n"
            for dep in list(data["dependencies"])[:10]:
                response += f"  • {dep}\n"
        
        if data.get("entry_points"):
            response += f"\n**Puntos de entrada:**\n"
            for ep in data["entry_points"][:5]:
                response += f"  • {ep}\n"
        
        return {
            "success": True,
            "response": response,
            "fase": 6,
            "analysis": data
        }
    
    def _action_run_command(self, session: ConstructorSession, message: str, intent: 'IntentAnalysis') -> Dict[str, Any]:
        """Ejecuta un comando del sistema"""
        if not self.toolkit_enabled or not self.command_executor:
            return {"success": False, "response": "El ejecutor de comandos no está disponible.", "fase": 6}
        
        # Extraer comando del mensaje
        command = self._extract_command(message)
        if not command:
            return {
                "success": True,
                "response": "¿Qué comando deseas ejecutar? Por ejemplo: 'ejecuta pip list' o 'corre npm install'",
                "fase": 6,
                "needs_clarification": True
            }
        
        # Verificar que el comando esté permitido
        cmd_result = self.command_executor.run_command(command, timeout=60)
        
        if not cmd_result.get("success"):
            error = cmd_result.get("error", "Error desconocido")
            if "not allowed" in error.lower() or "blocked" in error.lower():
                return {
                    "success": False,
                    "response": f"⚠️ El comando '{command}' no está permitido por seguridad.\n\nComandos permitidos: pip, npm, ls, cat, grep, git status, etc.",
                    "fase": 6
                }
            return {
                "success": False,
                "response": f"Error ejecutando comando: {error}",
                "fase": 6
            }
        
        stdout = cmd_result.get("stdout", "")
        stderr = cmd_result.get("stderr", "")
        exit_code = cmd_result.get("exit_code", 0)
        
        response = f"⚡ **Comando ejecutado:** `{command}`\n\n"
        if exit_code == 0:
            response += "✅ **Éxito**\n\n"
        else:
            response += f"⚠️ **Código de salida:** {exit_code}\n\n"
        
        if stdout:
            output = stdout[:2000]
            response += f"**Salida:**\n```\n{output}\n```\n"
            if len(stdout) > 2000:
                response += "(salida truncada...)\n"
        
        if stderr:
            response += f"\n**Errores/Advertencias:**\n```\n{stderr[:500]}\n```"
        
        return {
            "success": True,
            "response": response,
            "fase": 6,
            "command": command,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code
        }
    
    def _action_install_package(self, session: ConstructorSession, message: str, intent: 'IntentAnalysis') -> Dict[str, Any]:
        """Instala un paquete"""
        if not self.toolkit_enabled or not self.command_executor:
            return {"success": False, "response": "El instalador de paquetes no está disponible.", "fase": 6}
        
        # Extraer nombre del paquete y manager
        package, manager = self._extract_package_info(message)
        if not package:
            return {
                "success": True,
                "response": "¿Qué paquete deseas instalar? Por ejemplo: 'instala flask' o 'npm install express'",
                "fase": 6,
                "needs_clarification": True
            }
        
        install_result = self.command_executor.install_package(package, manager)
        
        if not install_result.get("success"):
            error = install_result.get("error", "Error desconocido")
            return {
                "success": False,
                "response": f"❌ No pude instalar **{package}**: {error}",
                "fase": 6
            }
        
        return {
            "success": True,
            "response": f"✅ **Paquete instalado:** {package} ({manager})\n\n{install_result.get('stdout', '')}",
            "fase": 6,
            "package": package,
            "manager": manager
        }
    
    def _action_view_logs(self, session: ConstructorSession) -> Dict[str, Any]:
        """Muestra logs recientes del servidor"""
        # Por ahora retornamos un mensaje indicando dónde ver los logs
        return {
            "success": True,
            "response": "📋 **Logs del sistema**\n\nPuedes ver los logs en tiempo real en la consola del servidor.\n\nPara ver errores específicos, puedo buscar patrones en el código con 'busca ERROR' o 'busca Exception'.",
            "fase": 6
        }
    
    def _action_explain_or_consult(self, session: ConstructorSession, message: str, intent: 'IntentAnalysis') -> Dict[str, Any]:
        """Responde preguntas generales o explica código"""
        if not self.ai_service:
            return {"success": False, "response": "El servicio de IA no está disponible.", "fase": 6}
        
        # Para explicaciones, usamos el AI service directamente
        prompt = f"""Eres BUNK3R Assistant, un asistente experto en programación.
        
El usuario pregunta: {message}

Responde de forma clara, concisa y útil. Si es sobre código, da ejemplos prácticos.
Si necesitas ver un archivo específico para ayudar mejor, indícalo."""

        result = self.ai_service.chat(
            user_id=f"constructor_{session.user_id}",
            message=prompt,
            enable_auto_rectify=False
        )
        
        if not result.get("success"):
            return {
                "success": False,
                "response": "No pude procesar tu consulta. ¿Podrías reformularla?",
                "fase": 6
            }
        
        return {
            "success": True,
            "response": result.get("response", ""),
            "fase": 6,
            "is_explanation": True
        }
    
    # ═══════════════════════════════════════════════════════════════════
    # HELPERS PARA EXTRAER INFORMACIÓN DE MENSAJES
    # ═══════════════════════════════════════════════════════════════════
    
    def _extract_file_path(self, message: str) -> Optional[str]:
        """Extrae una ruta de archivo del mensaje"""
        # Patrones comunes para detectar rutas de archivo
        patterns = [
            r'(?:archivo|file|ver|lee|leer|muestra|mostrar|abre|open)\s+["\']?([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+)["\']?',
            r'["\']([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+)["\']',
            r'(?:en|in)\s+([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+)',
            r'([a-zA-Z0-9_\-]+\.(?:py|js|ts|html|css|json|md|txt|jsx|tsx|vue|sql|yaml|yml))'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_search_term(self, message: str) -> Optional[str]:
        """Extrae un término de búsqueda del mensaje"""
        patterns = [
            r'(?:busca|buscar|encuentra|find|search|grep)\s+["\']([^"\']+)["\']',
            r'(?:busca|buscar|encuentra|find|search|grep)\s+(.+?)(?:\s+en|\s+in|$)',
            r'["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                term = match.group(1).strip()
                if len(term) >= 2:
                    return term
        
        return None
    
    def _extract_command(self, message: str) -> Optional[str]:
        """Extrae un comando del mensaje"""
        patterns = [
            r'(?:ejecuta|run|corre|lanza)\s+["`]([^"`]+)["`]',
            r'(?:ejecuta|run|corre|lanza)\s+(.+?)$',
            r'["`]([^"`]+)["`]'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                cmd = match.group(1).strip()
                if len(cmd) >= 2:
                    return cmd
        
        return None
    
    def _extract_package_info(self, message: str) -> Tuple[Optional[str], str]:
        """Extrae información del paquete a instalar"""
        # Detectar manager
        manager = "pip"  # Default
        if "npm" in message.lower() or "node" in message.lower():
            manager = "npm"
        
        # Extraer nombre del paquete
        patterns = [
            r'(?:instala|install)\s+([a-zA-Z0-9_\-@/]+)',
            r'(?:pip|npm)\s+install\s+([a-zA-Z0-9_\-@/]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1).strip(), manager
        
        return None, manager
