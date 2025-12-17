"""
BUNK3R AI - SmartRetrySystem (34.17)
Sistema de Reintentos Inteligente con Backoff Exponencial

Funcionalidades:
- Retry con backoff exponencial
- Cambio automático de proveedor en fallo
- Límite de reintentos configurable
- Logging de fallos
- Notificación al usuario
"""

import time
import random
import logging
from typing import Callable, Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)


class RetryReason(Enum):
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    SERVER_ERROR = "server_error"
    NETWORK_ERROR = "network_error"
    INVALID_RESPONSE = "invalid_response"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    UNKNOWN = "unknown"


class RetryStrategy(Enum):
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"
    FIBONACCI = "fibonacci"


@dataclass
class RetryAttempt:
    attempt_number: int
    timestamp: datetime
    provider: str
    success: bool
    error: Optional[str]
    duration_ms: int
    retry_reason: Optional[RetryReason]
    
    def to_dict(self) -> Dict:
        return {
            "attempt_number": self.attempt_number,
            "timestamp": self.timestamp.isoformat(),
            "provider": self.provider,
            "success": self.success,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "retry_reason": self.retry_reason.value if self.retry_reason else None
        }


@dataclass
class RetryResult:
    success: bool
    result: Any
    total_attempts: int
    attempts: List[RetryAttempt]
    final_provider: str
    total_duration_ms: int
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "result": self.result,
            "total_attempts": self.total_attempts,
            "attempts": [a.to_dict() for a in self.attempts],
            "final_provider": self.final_provider,
            "total_duration_ms": self.total_duration_ms
        }


@dataclass
class RetryConfig:
    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter: bool = True
    jitter_factor: float = 0.1
    switch_provider_after: int = 2
    timeout_seconds: float = 60.0
    
    def to_dict(self) -> Dict:
        return {
            "max_attempts": self.max_attempts,
            "base_delay_seconds": self.base_delay_seconds,
            "max_delay_seconds": self.max_delay_seconds,
            "strategy": self.strategy.value,
            "jitter": self.jitter,
            "jitter_factor": self.jitter_factor,
            "switch_provider_after": self.switch_provider_after,
            "timeout_seconds": self.timeout_seconds
        }


class SmartRetrySystem:
    """
    Sistema de Reintentos Inteligente
    
    Maneja reintentos con backoff exponencial, cambio de proveedor,
    y logging detallado de fallos.
    """
    
    ERROR_PATTERNS = {
        RetryReason.TIMEOUT: [
            "timeout", "timed out", "deadline exceeded"
        ],
        RetryReason.RATE_LIMIT: [
            "rate limit", "too many requests", "429", "quota exceeded"
        ],
        RetryReason.SERVER_ERROR: [
            "500", "502", "503", "504", "internal server error", "bad gateway"
        ],
        RetryReason.NETWORK_ERROR: [
            "connection", "network", "dns", "refused", "reset"
        ],
        RetryReason.INVALID_RESPONSE: [
            "invalid", "malformed", "parse error", "json"
        ],
        RetryReason.PROVIDER_UNAVAILABLE: [
            "unavailable", "not available", "model is loading"
        ],
    }
    
    FIBONACCI_SEQUENCE = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
    
    def __init__(self, default_config: RetryConfig = None):
        self.default_config = default_config or RetryConfig()
        self.failure_log: List[RetryAttempt] = []
        self.provider_failures: Dict[str, int] = {}
    
    def _classify_error(self, error_message: str) -> RetryReason:
        """Clasifica el tipo de error para decidir estrategia"""
        error_lower = error_message.lower()
        
        for reason, patterns in self.ERROR_PATTERNS.items():
            if any(pattern in error_lower for pattern in patterns):
                return reason
        
        return RetryReason.UNKNOWN
    
    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calcula el delay para el próximo intento"""
        if config.strategy == RetryStrategy.EXPONENTIAL:
            delay = config.base_delay_seconds * (2 ** (attempt - 1))
        
        elif config.strategy == RetryStrategy.LINEAR:
            delay = config.base_delay_seconds * attempt
        
        elif config.strategy == RetryStrategy.FIXED:
            delay = config.base_delay_seconds
        
        elif config.strategy == RetryStrategy.FIBONACCI:
            idx = min(attempt - 1, len(self.FIBONACCI_SEQUENCE) - 1)
            delay = config.base_delay_seconds * self.FIBONACCI_SEQUENCE[idx]
        
        else:
            delay = config.base_delay_seconds
        
        delay = min(delay, config.max_delay_seconds)
        
        if config.jitter:
            jitter = delay * config.jitter_factor * random.random()
            delay = delay + jitter
        
        return delay
    
    def _should_switch_provider(self, attempt: int, config: RetryConfig,
                               current_provider: str) -> bool:
        """Decide si cambiar de proveedor"""
        if attempt >= config.switch_provider_after:
            return True
        
        if self.provider_failures.get(current_provider, 0) >= 3:
            return True
        
        return False
    
    def _select_next_provider(self, available_providers: List[str],
                             current_provider: str) -> str:
        """Selecciona el siguiente proveedor a usar"""
        sorted_providers = sorted(
            available_providers,
            key=lambda p: self.provider_failures.get(p, 0)
        )
        
        for provider in sorted_providers:
            if provider != current_provider:
                return provider
        
        return current_provider
    
    def execute_with_retry(
        self,
        func: Callable,
        providers: List[str] = None,
        config: RetryConfig = None,
        on_retry: Callable[[int, str, str], None] = None,
        **kwargs
    ) -> RetryResult:
        """
        Ejecuta una función con reintentos inteligentes
        
        Args:
            func: Función a ejecutar (debe aceptar 'provider' como kwarg)
            providers: Lista de proveedores disponibles
            config: Configuración de reintentos
            on_retry: Callback llamado antes de cada reintento
            **kwargs: Argumentos adicionales para la función
        
        Returns:
            RetryResult con el resultado final
        """
        config = config or self.default_config
        providers = providers or ["default"]
        current_provider = providers[0]
        
        attempts = []
        start_time = time.time()
        result = None
        success = False
        
        for attempt in range(1, config.max_attempts + 1):
            attempt_start = time.time()
            error_msg = None
            retry_reason = None
            
            try:
                result = func(provider=current_provider, **kwargs)
                
                if isinstance(result, dict) and result.get("success") == False:
                    error_msg = result.get("error", "Unknown error")
                    retry_reason = self._classify_error(error_msg)
                    
                    self.provider_failures[current_provider] = \
                        self.provider_failures.get(current_provider, 0) + 1
                else:
                    success = True
                
            except Exception as e:
                error_msg = str(e)
                retry_reason = self._classify_error(error_msg)
                
                self.provider_failures[current_provider] = \
                    self.provider_failures.get(current_provider, 0) + 1
            
            duration_ms = int((time.time() - attempt_start) * 1000)
            
            attempt_record = RetryAttempt(
                attempt_number=attempt,
                timestamp=datetime.now(),
                provider=current_provider,
                success=success,
                error=error_msg,
                duration_ms=duration_ms,
                retry_reason=retry_reason
            )
            attempts.append(attempt_record)
            
            if not success:
                self.failure_log.append(attempt_record)
                logger.warning(
                    f"Intento {attempt}/{config.max_attempts} falló con {current_provider}: {error_msg}"
                )
            
            if success:
                break
            
            if attempt < config.max_attempts:
                if self._should_switch_provider(attempt, config, current_provider):
                    new_provider = self._select_next_provider(providers, current_provider)
                    if new_provider != current_provider:
                        logger.info(f"Cambiando de {current_provider} a {new_provider}")
                        current_provider = new_provider
                
                delay = self._calculate_delay(attempt, config)
                
                if retry_reason == RetryReason.RATE_LIMIT:
                    delay = min(delay * 2, config.max_delay_seconds)
                
                if on_retry:
                    on_retry(attempt, current_provider, error_msg)
                
                logger.info(f"Esperando {delay:.2f}s antes del siguiente intento...")
                time.sleep(delay)
        
        total_duration = int((time.time() - start_time) * 1000)
        
        return RetryResult(
            success=success,
            result=result,
            total_attempts=len(attempts),
            attempts=attempts,
            final_provider=current_provider,
            total_duration_ms=total_duration
        )
    
    def get_failure_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de fallos"""
        total_failures = len(self.failure_log)
        
        by_reason = {}
        for attempt in self.failure_log:
            if attempt.retry_reason:
                reason = attempt.retry_reason.value
                by_reason[reason] = by_reason.get(reason, 0) + 1
        
        by_provider = {}
        for attempt in self.failure_log:
            by_provider[attempt.provider] = by_provider.get(attempt.provider, 0) + 1
        
        return {
            "total_failures": total_failures,
            "failures_by_reason": by_reason,
            "failures_by_provider": by_provider,
            "current_provider_scores": self.provider_failures.copy()
        }
    
    def reset_provider_scores(self):
        """Resetea los scores de proveedores"""
        self.provider_failures.clear()
    
    def clear_failure_log(self):
        """Limpia el log de fallos"""
        self.failure_log.clear()


def retry_decorator(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
):
    """
    Decorador para añadir reintentos a una función
    
    Usage:
        @retry_decorator(max_attempts=3)
        def my_function():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            config = RetryConfig(
                max_attempts=max_attempts,
                base_delay_seconds=base_delay,
                strategy=strategy
            )
            
            retry_system = SmartRetrySystem(config)
            
            def execute_func(provider=None, **kw):
                return func(*args, **{**kwargs, **kw})
            
            result = retry_system.execute_with_retry(execute_func)
            
            if result.success:
                return result.result
            else:
                raise Exception(f"Falló después de {result.total_attempts} intentos")
        
        return wrapper
    return decorator


smart_retry = SmartRetrySystem()


def execute_with_retry(func: Callable, providers: List[str] = None,
                      max_attempts: int = 3) -> Dict:
    """Helper para ejecutar con reintentos"""
    config = RetryConfig(max_attempts=max_attempts)
    result = smart_retry.execute_with_retry(func, providers, config)
    return result.to_dict()
