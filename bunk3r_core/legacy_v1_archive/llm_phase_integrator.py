"""
BUNK3R AI - LLMPhaseIntegrator (34.7)
Integración Real de LLM en las 8 Fases del Constructor

Conecta AIService con AIConstructor usando SmartRetry para
llamadas robustas y prompts específicos por fase.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from bunk3r_core.ai_service import AIService, get_ai_service
except ImportError:
    AIService = None
    get_ai_service = None

try:
    from bunk3r_core.smart_retry import SmartRetrySystem, RetryConfig, RetryStrategy
except ImportError:
    SmartRetrySystem = None
    RetryConfig = None
    RetryStrategy = None

try:
    from bunk3r_core.output_verifier import OutputVerifier
except ImportError:
    OutputVerifier = None


class ConstructorPhase(Enum):
    INTENT_ANALYSIS = 1
    RESEARCH = 2
    CLARIFICATION = 3
    PROMPT_BUILDING = 4
    PLAN_PRESENTATION = 5
    EXECUTION = 6
    VERIFICATION = 7
    DELIVERY = 8


@dataclass
class PhaseResult:
    phase: ConstructorPhase
    success: bool
    data: Dict[str, Any]
    llm_response: Optional[str] = None
    tokens_used: int = 0
    provider_used: str = ""
    duration_ms: int = 0
    retries: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "phase": self.phase.value,
            "phase_name": self.phase.name,
            "success": self.success,
            "data": self.data,
            "llm_response": self.llm_response,
            "tokens_used": self.tokens_used,
            "provider_used": self.provider_used,
            "duration_ms": self.duration_ms,
            "retries": self.retries
        }


class PhasePrompts:
    """Prompts específicos para cada fase del constructor"""
    
    INTENT_ANALYSIS = """Eres un analizador de intenciones experto. Analiza la solicitud del usuario y extrae:

1. **Tipo de tarea**: (crear_web, crear_landing, crear_api, modificar_codigo, corregir_error, etc.)
2. **Contexto del proyecto**: (restaurante, ecommerce, portfolio, blog, saas, etc.)
3. **Lenguaje/Framework**: (html_css_js, python_flask, react, nodejs, etc.)
4. **Nivel de detalle**: (alto, medio, bajo, vago)
5. **Requiere clarificación**: (sí/no y por qué)
6. **Keywords importantes**: Lista de términos clave
7. **Urgencia**: (alta, media, baja)

SOLICITUD DEL USUARIO:
{user_request}

Responde en formato JSON válido:
```json
{
    "tipo_tarea": "string",
    "contexto": "string",
    "lenguaje": "string",
    "nivel_detalle": "string",
    "requiere_clarificacion": boolean,
    "razon_clarificacion": "string o null",
    "keywords": ["lista", "de", "keywords"],
    "urgencia": "string",
    "resumen": "resumen breve de lo que el usuario quiere"
}
```"""

    RESEARCH = """Eres un investigador de desarrollo web experto. Basándote en el análisis de intención, investiga y recomienda:

1. **Mejores prácticas** para este tipo de proyecto
2. **Estructura de archivos** recomendada
3. **Componentes necesarios**
4. **Paleta de colores** sugerida (si aplica)
5. **Dependencias** necesarias
6. **Patrones de diseño** recomendados
7. **Consideraciones de seguridad**

ANÁLISIS DE INTENCIÓN:
{intent_analysis}

CONTEXTO ADICIONAL:
{context}

Responde en formato JSON:
```json
{
    "mejores_practicas": ["lista de prácticas"],
    "estructura_archivos": ["lista de archivos a crear"],
    "componentes": ["componentes necesarios"],
    "paleta_colores": ["#hex1", "#hex2", "#hex3"],
    "estilo_sugerido": "descripción del estilo visual",
    "dependencias": ["lista de dependencias"],
    "patrones": ["patrones de diseño"],
    "seguridad": ["consideraciones de seguridad"],
    "tiempo_estimado_minutos": number,
    "complejidad": "baja|media|alta"
}
```"""

    CLARIFICATION = """Eres un asistente que genera preguntas clarificadoras inteligentes. 
Analiza la solicitud y genera MÁXIMO 3 preguntas para obtener información faltante.

Solo genera preguntas si realmente hay ambigüedad. Si la solicitud es clara, responde que no se necesitan preguntas.

SOLICITUD ORIGINAL:
{user_request}

ANÁLISIS PREVIO:
{intent_analysis}

Para cada pregunta, proporciona opciones de respuesta cuando sea posible.

Responde en formato JSON:
```json
{
    "necesita_clarificacion": boolean,
    "razon": "por qué sí o no necesita clarificación",
    "preguntas": [
        {
            "id": "q1",
            "pregunta": "texto de la pregunta",
            "tipo": "scope|technology|design|functionality",
            "opciones": ["opción 1", "opción 2", "opción 3"],
            "valor_defecto": "opción por defecto si no responde"
        }
    ]
}
```"""

    PROMPT_BUILDING = """Eres un constructor de prompts maestro para generación de código.
Combina toda la información recopilada para crear un prompt detallado y completo.

SOLICITUD ORIGINAL:
{user_request}

ANÁLISIS DE INTENCIÓN:
{intent_analysis}

INVESTIGACIÓN:
{research}

CLARIFICACIONES (si hay):
{clarifications}

Genera un prompt maestro que incluya:
1. Descripción exacta de lo que se debe crear
2. Especificaciones técnicas (lenguaje, framework, estructura)
3. Requisitos de diseño (colores, estilo, responsive)
4. Funcionalidades específicas
5. Restricciones y consideraciones
6. Formato de salida esperado

Responde en formato JSON:
```json
{
    "prompt_maestro": "El prompt completo y detallado para generar el código",
    "archivos_a_generar": ["lista de archivos"],
    "orden_generacion": ["orden en que deben generarse"],
    "variables_template": {"variable": "valor"}
}
```"""

    PLAN_PRESENTATION = """Eres un planificador de proyectos de desarrollo. 
Crea un plan de ejecución detallado y estructurado.

PROMPT MAESTRO:
{master_prompt}

ARCHIVOS A GENERAR:
{files_to_generate}

Genera un plan con:
1. Lista de tareas ordenadas por prioridad/dependencia
2. Tiempo estimado por tarea
3. Archivos afectados por tarea
4. Riesgos identificados
5. Dependencias entre tareas

Responde en formato JSON:
```json
{
    "titulo_plan": "nombre descriptivo del plan",
    "descripcion": "resumen del plan",
    "tareas": [
        {
            "id": "task_1",
            "titulo": "nombre de la tarea",
            "descripcion": "qué hace esta tarea",
            "tiempo_minutos": number,
            "archivos": ["archivos afectados"],
            "dependencias": ["ids de tareas previas"],
            "complejidad": "trivial|simple|media|compleja"
        }
    ],
    "tiempo_total_minutos": number,
    "riesgos": [
        {
            "descripcion": "descripción del riesgo",
            "nivel": "bajo|medio|alto",
            "mitigacion": "cómo mitigarlo"
        }
    ],
    "dependencias_npm_pip": ["lista de paquetes"]
}
```"""

    EXECUTION = """Eres un generador de código experto. Genera código completo, funcional y de alta calidad.

TAREA ACTUAL:
{current_task}

CONTEXTO DEL PROYECTO:
{project_context}

ARCHIVOS YA GENERADOS:
{existing_files}

REGLAS ESTRICTAS:
1. Genera código COMPLETO, no fragmentos
2. Incluye todos los imports necesarios
3. Sigue las mejores prácticas del lenguaje
4. Añade comentarios explicativos cuando sea útil
5. El código debe ser funcional sin modificaciones
6. Usa el estilo y convenciones del proyecto

Responde con el código completo del archivo:
```{language}
[código completo aquí]
```

Si generas múltiples archivos, sepáralos claramente con:
--- ARCHIVO: nombre_archivo.ext ---
[contenido]
--- FIN ARCHIVO ---"""

    VERIFICATION = """Eres un verificador de código experto. Analiza el código generado y verifica:

1. **Sintaxis**: ¿Es sintácticamente correcto?
2. **Completitud**: ¿Está completo o faltan partes?
3. **Funcionalidad**: ¿Cumple con los requisitos?
4. **Calidad**: ¿Sigue buenas prácticas?
5. **Seguridad**: ¿Hay vulnerabilidades obvias?

CÓDIGO A VERIFICAR:
```
{code}
```

REQUISITOS ORIGINALES:
{requirements}

Responde en formato JSON:
```json
{
    "sintaxis_valida": boolean,
    "completitud": boolean,
    "cumple_requisitos": boolean,
    "calidad_score": number (0-100),
    "errores": ["lista de errores encontrados"],
    "advertencias": ["lista de advertencias"],
    "sugerencias": ["sugerencias de mejora"],
    "requiere_correccion": boolean,
    "correcciones_sugeridas": ["lista de correcciones necesarias"]
}
```"""

    DELIVERY = """Eres un asistente de entrega de proyectos. Prepara el resumen final del proyecto completado.

ARCHIVOS GENERADOS:
{generated_files}

VERIFICACIÓN:
{verification_result}

SOLICITUD ORIGINAL:
{original_request}

Genera un resumen de entrega que incluya:
1. Qué se creó
2. Cómo usar/ejecutar el proyecto
3. Estructura de archivos
4. Próximos pasos sugeridos

Responde en formato JSON:
```json
{
    "resumen": "resumen de lo que se creó",
    "archivos_creados": ["lista de archivos"],
    "instrucciones_uso": "cómo ejecutar/usar el proyecto",
    "comandos": ["comandos necesarios si aplica"],
    "proximos_pasos": ["sugerencias para el usuario"],
    "notas": "notas adicionales importantes"
}
```"""


class LLMPhaseIntegrator:
    """
    Integrador de LLM para las 8 fases del Constructor
    
    Conecta AIService con cada fase usando prompts específicos
    y SmartRetry para llamadas robustas.
    """
    
    def __init__(self, ai_service: 'AIService' = None):
        self.ai_service = ai_service or self._create_ai_service()
        self.retry_system = self._create_retry_system()
        self.output_verifier = OutputVerifier() if OutputVerifier else None
        self.phase_prompts = PhasePrompts()
        self.session_data: Dict[str, Any] = {}
    
    def _create_ai_service(self) -> Optional['AIService']:
        """Crea o obtiene instancia global de AIService"""
        if get_ai_service:
            try:
                return get_ai_service()
            except Exception as e:
                logger.warning(f"No se pudo obtener AIService: {e}")
                return None
        elif AIService:
            try:
                return AIService()
            except Exception as e:
                logger.warning(f"No se pudo crear AIService: {e}")
                return None
        return None
    
    def _create_retry_system(self) -> Optional['SmartRetrySystem']:
        """Crea sistema de reintentos con configuración para LLM"""
        if SmartRetrySystem and RetryConfig:
            config = RetryConfig(
                max_attempts=3,
                base_delay_seconds=2.0,
                max_delay_seconds=30.0,
                strategy=RetryStrategy.EXPONENTIAL if RetryStrategy else None,
                jitter=True,
                switch_provider_after=2
            )
            return SmartRetrySystem(config)
        return None
    
    def _call_llm(self, prompt: str, system_prompt: str = None,
                  user_id: str = "system") -> Dict[str, Any]:
        """
        Llama al LLM con reintentos inteligentes
        
        Args:
            prompt: El prompt a enviar
            system_prompt: Prompt de sistema opcional
            user_id: ID del usuario
            
        Returns:
            Dict con respuesta y metadata
        """
        if not self.ai_service:
            return {
                "success": False,
                "error": "AIService no disponible",
                "response": None
            }
        
        import time
        start_time = time.time()
        
        providers = self.ai_service.get_available_providers()
        
        if self.retry_system:
            def call_provider(provider: str = None, **kwargs):
                return self.ai_service.chat(
                    user_id=user_id,
                    message=prompt,
                    system_prompt=system_prompt,
                    preferred_provider=provider,
                    enable_auto_rectify=True
                )
            
            result = self.retry_system.execute_with_retry(
                call_provider,
                providers=providers
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            if result.success:
                return {
                    "success": True,
                    "response": result.result.get("response", ""),
                    "provider": result.final_provider,
                    "retries": result.total_attempts - 1,
                    "duration_ms": duration_ms
                }
            else:
                return {
                    "success": False,
                    "error": "Todos los proveedores fallaron",
                    "response": None,
                    "retries": result.total_attempts
                }
        else:
            result = self.ai_service.chat(
                user_id=user_id,
                message=prompt,
                system_prompt=system_prompt,
                enable_auto_rectify=True
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            return {
                "success": result.get("success", False),
                "response": result.get("response", ""),
                "provider": result.get("provider", "unknown"),
                "retries": 0,
                "duration_ms": duration_ms
            }
    
    def _parse_json_response(self, response: str) -> Tuple[bool, Dict]:
        """Extrae JSON de la respuesta del LLM"""
        import re
        
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
        if json_match:
            try:
                return True, json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        json_match = re.search(r'```\s*([\s\S]*?)\s*```', response)
        if json_match:
            try:
                return True, json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        try:
            return True, json.loads(response)
        except json.JSONDecodeError:
            pass
        
        return False, {"raw_response": response}
    
    def execute_phase(self, phase: ConstructorPhase, 
                      input_data: Dict[str, Any],
                      user_id: str = "system") -> PhaseResult:
        """
        Ejecuta una fase específica del constructor con LLM
        
        Args:
            phase: La fase a ejecutar
            input_data: Datos de entrada para la fase
            user_id: ID del usuario
            
        Returns:
            PhaseResult con el resultado de la fase
        """
        import time
        start_time = time.time()
        
        prompt = self._build_phase_prompt(phase, input_data)
        system_prompt = self._get_phase_system_prompt(phase)
        
        llm_result = self._call_llm(prompt, system_prompt, user_id)
        
        if not llm_result.get("success"):
            return PhaseResult(
                phase=phase,
                success=False,
                data={"error": llm_result.get("error", "Unknown error")},
                llm_response=None,
                provider_used=llm_result.get("provider", ""),
                retries=llm_result.get("retries", 0),
                duration_ms=llm_result.get("duration_ms", 0)
            )
        
        response = llm_result.get("response", "")
        parsed_ok, parsed_data = self._parse_json_response(response)
        
        processed_data = self._process_phase_result(phase, parsed_data, input_data)
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        return PhaseResult(
            phase=phase,
            success=True,
            data=processed_data,
            llm_response=response,
            provider_used=llm_result.get("provider", ""),
            retries=llm_result.get("retries", 0),
            duration_ms=duration_ms
        )
    
    def _build_phase_prompt(self, phase: ConstructorPhase, 
                           input_data: Dict[str, Any]) -> str:
        """Construye el prompt específico para cada fase"""
        
        if phase == ConstructorPhase.INTENT_ANALYSIS:
            return PhasePrompts.INTENT_ANALYSIS.format(
                user_request=input_data.get("user_request", "")
            )
        
        elif phase == ConstructorPhase.RESEARCH:
            return PhasePrompts.RESEARCH.format(
                intent_analysis=json.dumps(input_data.get("intent", {}), indent=2, ensure_ascii=False),
                context=input_data.get("context", "")
            )
        
        elif phase == ConstructorPhase.CLARIFICATION:
            return PhasePrompts.CLARIFICATION.format(
                user_request=input_data.get("user_request", ""),
                intent_analysis=json.dumps(input_data.get("intent", {}), indent=2, ensure_ascii=False)
            )
        
        elif phase == ConstructorPhase.PROMPT_BUILDING:
            return PhasePrompts.PROMPT_BUILDING.format(
                user_request=input_data.get("user_request", ""),
                intent_analysis=json.dumps(input_data.get("intent", {}), indent=2, ensure_ascii=False),
                research=json.dumps(input_data.get("research", {}), indent=2, ensure_ascii=False),
                clarifications=json.dumps(input_data.get("clarifications", {}), indent=2, ensure_ascii=False)
            )
        
        elif phase == ConstructorPhase.PLAN_PRESENTATION:
            return PhasePrompts.PLAN_PRESENTATION.format(
                master_prompt=input_data.get("master_prompt", ""),
                files_to_generate=json.dumps(input_data.get("files", []), ensure_ascii=False)
            )
        
        elif phase == ConstructorPhase.EXECUTION:
            return PhasePrompts.EXECUTION.format(
                current_task=json.dumps(input_data.get("task", {}), indent=2, ensure_ascii=False),
                project_context=input_data.get("context", ""),
                existing_files=json.dumps(list(input_data.get("existing_files", {}).keys()), ensure_ascii=False),
                language=input_data.get("language", "")
            )
        
        elif phase == ConstructorPhase.VERIFICATION:
            return PhasePrompts.VERIFICATION.format(
                code=input_data.get("code", ""),
                requirements=input_data.get("requirements", "")
            )
        
        elif phase == ConstructorPhase.DELIVERY:
            return PhasePrompts.DELIVERY.format(
                generated_files=json.dumps(list(input_data.get("files", {}).keys()), ensure_ascii=False),
                verification_result=json.dumps(input_data.get("verification", {}), indent=2, ensure_ascii=False),
                original_request=input_data.get("original_request", "")
            )
        
        return str(input_data)
    
    def _get_phase_system_prompt(self, phase: ConstructorPhase) -> str:
        """Obtiene el prompt de sistema para cada fase"""
        base_prompt = """Eres BUNK3R AI, un asistente de desarrollo experto.
Respondes siempre en el formato JSON especificado.
Eres preciso, completo y sigues las instrucciones exactamente."""
        
        phase_additions = {
            ConstructorPhase.INTENT_ANALYSIS: "\nEres experto en análisis de requerimientos y detección de intenciones.",
            ConstructorPhase.RESEARCH: "\nEres experto en arquitectura de software y mejores prácticas de desarrollo.",
            ConstructorPhase.CLARIFICATION: "\nEres experto en comunicación y en hacer las preguntas correctas.",
            ConstructorPhase.PROMPT_BUILDING: "\nEres experto en ingeniería de prompts y especificaciones técnicas.",
            ConstructorPhase.PLAN_PRESENTATION: "\nEres experto en gestión de proyectos y planificación.",
            ConstructorPhase.EXECUTION: "\nEres un desarrollador senior experto en múltiples lenguajes y frameworks.",
            ConstructorPhase.VERIFICATION: "\nEres experto en code review, testing y aseguramiento de calidad.",
            ConstructorPhase.DELIVERY: "\nEres experto en documentación y comunicación técnica.",
        }
        
        return base_prompt + phase_additions.get(phase, "")
    
    def _process_phase_result(self, phase: ConstructorPhase,
                             parsed_data: Dict, 
                             input_data: Dict) -> Dict:
        """Procesa y valida el resultado de cada fase"""
        
        if phase == ConstructorPhase.INTENT_ANALYSIS:
            defaults = {
                "tipo_tarea": "consulta_general",
                "contexto": "",
                "lenguaje": "html_css_js",
                "nivel_detalle": "medio",
                "requiere_clarificacion": False,
                "keywords": [],
                "urgencia": "media"
            }
            for key, value in defaults.items():
                if key not in parsed_data:
                    parsed_data[key] = value
        
        elif phase == ConstructorPhase.EXECUTION:
            if "raw_response" in parsed_data:
                code = parsed_data["raw_response"]
                import re
                code_match = re.search(r'```\w*\s*([\s\S]*?)\s*```', code)
                if code_match:
                    parsed_data["generated_code"] = code_match.group(1)
                else:
                    parsed_data["generated_code"] = code
        
        elif phase == ConstructorPhase.VERIFICATION:
            if self.output_verifier and "code" in input_data:
                code = input_data["code"]
                filename = input_data.get("filename", "")
                report = self.output_verifier.verify(code, filename)
                parsed_data["verifier_report"] = report.to_dict()
        
        return parsed_data
    
    def run_full_pipeline(self, user_request: str, 
                         user_id: str = "system",
                         skip_clarification: bool = False) -> Dict[str, PhaseResult]:
        """
        Ejecuta el pipeline completo de 8 fases
        
        Args:
            user_request: Solicitud del usuario
            user_id: ID del usuario
            skip_clarification: Saltar fase de clarificación
            
        Returns:
            Dict con resultados de cada fase
        """
        results = {}
        
        intent_result = self.execute_phase(
            ConstructorPhase.INTENT_ANALYSIS,
            {"user_request": user_request},
            user_id
        )
        results["intent"] = intent_result
        
        if not intent_result.success:
            return results
        
        research_result = self.execute_phase(
            ConstructorPhase.RESEARCH,
            {
                "intent": intent_result.data,
                "context": user_request
            },
            user_id
        )
        results["research"] = research_result
        
        if not skip_clarification:
            clarification_result = self.execute_phase(
                ConstructorPhase.CLARIFICATION,
                {
                    "user_request": user_request,
                    "intent": intent_result.data
                },
                user_id
            )
            results["clarification"] = clarification_result
            
            if clarification_result.success and clarification_result.data.get("necesita_clarificacion"):
                results["awaiting_clarification"] = True
                return results
        
        prompt_result = self.execute_phase(
            ConstructorPhase.PROMPT_BUILDING,
            {
                "user_request": user_request,
                "intent": intent_result.data,
                "research": research_result.data,
                "clarifications": results.get("clarification", {})
            },
            user_id
        )
        results["prompt"] = prompt_result
        
        if not prompt_result.success:
            return results
        
        plan_result = self.execute_phase(
            ConstructorPhase.PLAN_PRESENTATION,
            {
                "master_prompt": prompt_result.data.get("prompt_maestro", ""),
                "files": prompt_result.data.get("archivos_a_generar", [])
            },
            user_id
        )
        results["plan"] = plan_result
        
        results["ready_for_execution"] = True
        results["plan_data"] = plan_result.data
        
        return results
    
    def execute_plan(self, plan_data: Dict, 
                    original_request: str,
                    user_id: str = "system") -> Dict[str, Any]:
        """
        Ejecuta un plan aprobado (fases 6-8)
        
        Args:
            plan_data: Datos del plan a ejecutar
            original_request: Solicitud original
            user_id: ID del usuario
            
        Returns:
            Dict con archivos generados y resultado de verificación
        """
        generated_files = {}
        tasks = plan_data.get("tareas", [])
        
        for task in tasks:
            exec_result = self.execute_phase(
                ConstructorPhase.EXECUTION,
                {
                    "task": task,
                    "context": original_request,
                    "existing_files": generated_files,
                    "language": task.get("language", "")
                },
                user_id
            )
            
            if exec_result.success:
                code = exec_result.data.get("generated_code", "")
                for filename in task.get("archivos", []):
                    generated_files[filename] = code
        
        verification_results = {}
        for filename, code in generated_files.items():
            verify_result = self.execute_phase(
                ConstructorPhase.VERIFICATION,
                {
                    "code": code,
                    "filename": filename,
                    "requirements": original_request
                },
                user_id
            )
            verification_results[filename] = verify_result.data
        
        delivery_result = self.execute_phase(
            ConstructorPhase.DELIVERY,
            {
                "files": generated_files,
                "verification": verification_results,
                "original_request": original_request
            },
            user_id
        )
        
        return {
            "files": generated_files,
            "verification": verification_results,
            "delivery": delivery_result.data,
            "success": all(
                v.get("sintaxis_valida", True) 
                for v in verification_results.values()
            )
        }


llm_integrator = LLMPhaseIntegrator()


def execute_phase(phase_num: int, input_data: Dict, user_id: str = "system") -> Dict:
    """Helper para ejecutar una fase específica"""
    try:
        phase = ConstructorPhase(phase_num)
    except ValueError:
        return {"success": False, "error": f"Fase inválida: {phase_num}"}
    
    result = llm_integrator.execute_phase(phase, input_data, user_id)
    return result.to_dict()


def run_pipeline(user_request: str, user_id: str = "system") -> Dict:
    """Helper para ejecutar el pipeline completo"""
    results = llm_integrator.run_full_pipeline(user_request, user_id)
    return {k: v.to_dict() if isinstance(v, PhaseResult) else v for k, v in results.items()}
