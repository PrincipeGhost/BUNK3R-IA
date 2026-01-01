"""
34.A.1 - Web Search Service (Serper API Integration)
Servicio de búsqueda en vivo para obtener información actualizada de la web.
"""

import os
import json
import hashlib
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
import httpx

class SearchType(Enum):
    """Tipos de búsqueda disponibles"""
    GENERAL = "search"
    NEWS = "news"
    IMAGES = "images"
    PLACES = "places"

class ContentFilter(Enum):
    """Filtros de contenido para resultados"""
    DOCUMENTATION = "documentation"
    TUTORIAL = "tutorial"
    STACKOVERFLOW = "stackoverflow"
    GITHUB = "github"
    OFFICIAL = "official"
    ALL = "all"

@dataclass
class SearchResult:
    """Resultado individual de búsqueda"""
    title: str
    link: str
    snippet: str
    position: int
    source: str = ""
    date: Optional[str] = None
    relevance_score: float = 0.0
    content_type: str = "general"
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class SearchResponse:
    """Respuesta completa de búsqueda"""
    query: str
    results: List[SearchResult]
    total_results: int
    search_time: float
    cached: bool = False
    filters_applied: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "query": self.query,
            "results": [r.to_dict() for r in self.results],
            "total_results": self.total_results,
            "search_time": self.search_time,
            "cached": self.cached,
            "filters_applied": self.filters_applied
        }

class SearchCache:
    """Cache de resultados de búsqueda con TTL de 24 horas"""
    
    def __init__(self, ttl_hours: int = 24, max_entries: int = 1000):
        self.cache: Dict[str, Dict] = {}
        self.ttl = timedelta(hours=ttl_hours)
        self.max_entries = max_entries
        self.hits = 0
        self.misses = 0
    
    def _generate_key(self, query: str, search_type: str, filters: List[str]) -> str:
        """Genera una clave única para el cache"""
        content = f"{query}:{search_type}:{','.join(sorted(filters))}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, query: str, search_type: str, filters: List[str]) -> Optional[SearchResponse]:
        """Obtiene resultado del cache si existe y no ha expirado"""
        key = self._generate_key(query, search_type, filters)
        
        if key in self.cache:
            entry = self.cache[key]
            cached_time = datetime.fromisoformat(entry["cached_at"])
            
            if datetime.now() - cached_time < self.ttl:
                self.hits += 1
                response = entry["response"]
                response["cached"] = True
                return self._dict_to_response(response)
            else:
                del self.cache[key]
        
        self.misses += 1
        return None
    
    def set(self, query: str, search_type: str, filters: List[str], response: SearchResponse):
        """Guarda resultado en cache"""
        if len(self.cache) >= self.max_entries:
            self._evict_oldest()
        
        key = self._generate_key(query, search_type, filters)
        self.cache[key] = {
            "cached_at": datetime.now().isoformat(),
            "response": response.to_dict()
        }
    
    def _evict_oldest(self):
        """Elimina las entradas más antiguas"""
        if not self.cache:
            return
        
        sorted_keys = sorted(
            self.cache.keys(),
            key=lambda k: self.cache[k]["cached_at"]
        )
        
        for key in sorted_keys[:len(sorted_keys) // 4]:
            del self.cache[key]
    
    def _dict_to_response(self, data: Dict) -> SearchResponse:
        """Convierte diccionario a SearchResponse"""
        results = [SearchResult(**r) for r in data["results"]]
        return SearchResponse(
            query=data["query"],
            results=results,
            total_results=data["total_results"],
            search_time=data["search_time"],
            cached=data.get("cached", False),
            filters_applied=data.get("filters_applied", [])
        )
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del cache"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "entries": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "max_entries": self.max_entries,
            "ttl_hours": self.ttl.total_seconds() / 3600
        }
    
    def clear(self):
        """Limpia todo el cache"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

class RateLimiter:
    """Rate limiter para controlar llamadas a la API"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests: List[float] = []
    
    def can_proceed(self) -> bool:
        """Verifica si se puede hacer una nueva solicitud"""
        now = time.time()
        self.requests = [t for t in self.requests if now - t < self.window]
        return len(self.requests) < self.max_requests
    
    def record_request(self):
        """Registra una nueva solicitud"""
        self.requests.append(time.time())
    
    def wait_time(self) -> float:
        """Tiempo de espera hasta poder hacer otra solicitud"""
        if self.can_proceed():
            return 0
        
        now = time.time()
        oldest = min(self.requests)
        return max(0, self.window - (now - oldest))
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del rate limiter"""
        now = time.time()
        active = [t for t in self.requests if now - t < self.window]
        return {
            "current_requests": len(active),
            "max_requests": self.max_requests,
            "window_seconds": self.window,
            "remaining": self.max_requests - len(active)
        }

class WebSearchService:
    """
    Servicio principal de búsqueda web usando Serper API.
    
    Características:
    - Integración con Serper API (Google Search)
    - Cache de resultados (24h TTL)
    - Filtros por tipo de contenido
    - Rate limiting
    - Extracción de snippets relevantes
    """
    
    SERPER_API_URL = "https://google.serper.dev"
    
    FILTER_SITE_MAPPINGS = {
        ContentFilter.DOCUMENTATION: [
            "site:docs.python.org",
            "site:developer.mozilla.org",
            "site:docs.microsoft.com",
            "site:cloud.google.com/docs",
            "site:docs.aws.amazon.com"
        ],
        ContentFilter.TUTORIAL: [
            "site:medium.com",
            "site:dev.to",
            "site:freecodecamp.org",
            "site:tutorialspoint.com",
            "site:w3schools.com"
        ],
        ContentFilter.STACKOVERFLOW: [
            "site:stackoverflow.com",
            "site:stackexchange.com"
        ],
        ContentFilter.GITHUB: [
            "site:github.com"
        ],
        ContentFilter.OFFICIAL: [
            "official documentation",
            "official docs"
        ]
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_ttl_hours: int = 24,
        rate_limit_requests: int = 100,
        rate_limit_window: int = 60
    ):
        self.api_key = api_key or os.getenv("SERPER_API_KEY")
        self.cache = SearchCache(ttl_hours=cache_ttl_hours)
        self.rate_limiter = RateLimiter(
            max_requests=rate_limit_requests,
            window_seconds=rate_limit_window
        )
        self.total_searches = 0
        self.failed_searches = 0
    
    def is_configured(self) -> bool:
        """Verifica si el servicio está configurado correctamente"""
        return bool(self.api_key)
    
    async def search(
        self,
        query: str,
        search_type: SearchType = SearchType.GENERAL,
        filters: Optional[List[ContentFilter]] = None,
        num_results: int = 10,
        country: str = "us",
        language: str = "en",
        use_cache: bool = True
    ) -> SearchResponse:
        """
        Realiza una búsqueda web.
        
        Args:
            query: Consulta de búsqueda
            search_type: Tipo de búsqueda (general, news, images, places)
            filters: Filtros de contenido a aplicar
            num_results: Número de resultados (máx 100)
            country: Código de país
            language: Código de idioma
            use_cache: Usar cache
            
        Returns:
            SearchResponse con los resultados
        """
        filters = filters or [ContentFilter.ALL]
        filter_names = [f.value for f in filters]
        
        if use_cache:
            cached = self.cache.get(query, search_type.value, filter_names)
            if cached:
                return cached
        
        if not self.rate_limiter.can_proceed():
            wait = self.rate_limiter.wait_time()
            raise RateLimitError(f"Rate limit alcanzado. Espera {wait:.1f} segundos.")
        
        if not self.is_configured():
            return self._fallback_search(query, filters)
        
        start_time = time.time()
        
        try:
            enhanced_query = self._apply_filters(query, filters)
            
            results = await self._execute_search(
                enhanced_query,
                search_type,
                num_results,
                country,
                language
            )
            
            self.rate_limiter.record_request()
            self.total_searches += 1
            
            search_time = time.time() - start_time
            
            response = SearchResponse(
                query=query,
                results=results,
                total_results=len(results),
                search_time=search_time,
                cached=False,
                filters_applied=filter_names
            )
            
            if use_cache:
                self.cache.set(query, search_type.value, filter_names, response)
            
            return response
            
        except Exception as e:
            self.failed_searches += 1
            raise SearchError(f"Error en búsqueda: {str(e)}")
    
    def search_sync(
        self,
        query: str,
        search_type: SearchType = SearchType.GENERAL,
        filters: Optional[List[ContentFilter]] = None,
        num_results: int = 10,
        country: str = "us",
        language: str = "en",
        use_cache: bool = True
    ) -> SearchResponse:
        """Versión síncrona de search"""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.search(query, search_type, filters, num_results, country, language, use_cache)
        )
    
    def _apply_filters(self, query: str, filters: List[ContentFilter]) -> str:
        """Aplica filtros de sitio a la consulta"""
        if ContentFilter.ALL in filters:
            return query
        
        site_filters = []
        for f in filters:
            if f in self.FILTER_SITE_MAPPINGS:
                sites = self.FILTER_SITE_MAPPINGS[f]
                if sites:
                    site_filters.append(f"({' OR '.join(sites)})")
        
        if site_filters:
            return f"{query} {' '.join(site_filters)}"
        
        return query
    
    async def _execute_search(
        self,
        query: str,
        search_type: SearchType,
        num_results: int,
        country: str,
        language: str
    ) -> List[SearchResult]:
        """Ejecuta la búsqueda en Serper API"""
        endpoint = f"{self.SERPER_API_URL}/{search_type.value}"
        
        payload = {
            "q": query,
            "num": min(num_results, 100),
            "gl": country,
            "hl": language
        }
        
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        
        return self._parse_results(data, search_type)
    
    def _parse_results(self, data: Dict, search_type: SearchType) -> List[SearchResult]:
        """Parsea los resultados de Serper API"""
        results = []
        
        organic = data.get("organic", [])
        
        for idx, item in enumerate(organic):
            result = SearchResult(
                title=item.get("title", ""),
                link=item.get("link", ""),
                snippet=self._extract_snippet(item),
                position=idx + 1,
                source=self._extract_source(item.get("link", "")),
                date=item.get("date"),
                relevance_score=self._calculate_relevance(item, idx),
                content_type=self._detect_content_type(item)
            )
            results.append(result)
        
        knowledge_graph = data.get("knowledgeGraph", {})
        if knowledge_graph:
            kg_result = SearchResult(
                title=knowledge_graph.get("title", ""),
                link=knowledge_graph.get("website", ""),
                snippet=knowledge_graph.get("description", ""),
                position=0,
                source="knowledge_graph",
                relevance_score=1.0,
                content_type="knowledge"
            )
            results.insert(0, kg_result)
        
        return results
    
    def _extract_snippet(self, item: Dict) -> str:
        """Extrae y limpia el snippet del resultado"""
        snippet = item.get("snippet", "")
        
        snippet = snippet.strip()
        if len(snippet) > 500:
            snippet = snippet[:497] + "..."
        
        return snippet
    
    def _extract_source(self, url: str) -> str:
        """Extrae el dominio fuente de una URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.replace("www.", "")
        except:
            return ""
    
    def _calculate_relevance(self, item: Dict, position: int) -> float:
        """Calcula un score de relevancia basado en posición y contenido"""
        base_score = max(0, 1 - (position * 0.08))
        
        snippet_length = len(item.get("snippet", ""))
        if snippet_length > 200:
            base_score += 0.05
        
        if item.get("sitelinks"):
            base_score += 0.1
        
        return min(1.0, base_score)
    
    def _detect_content_type(self, item: Dict) -> str:
        """Detecta el tipo de contenido del resultado"""
        link = item.get("link", "").lower()
        title = item.get("title", "").lower()
        
        if "stackoverflow.com" in link or "stackexchange.com" in link:
            return "stackoverflow"
        elif "github.com" in link:
            return "github"
        elif "docs." in link or "documentation" in title:
            return "documentation"
        elif "tutorial" in title or "how to" in title:
            return "tutorial"
        elif any(site in link for site in ["medium.com", "dev.to", "freecodecamp"]):
            return "article"
        else:
            return "general"
    
    def _fallback_search(self, query: str, filters: List[ContentFilter]) -> SearchResponse:
        """Búsqueda de respaldo cuando no hay API key"""
        self.total_searches += 1
        
        suggestions = [
            SearchResult(
                title=f"Buscar '{query}' en Google",
                link=f"https://www.google.com/search?q={query.replace(' ', '+')}",
                snippet="Realiza esta búsqueda directamente en Google",
                position=1,
                source="google.com",
                relevance_score=0.5,
                content_type="fallback"
            ),
            SearchResult(
                title=f"Buscar '{query}' en Stack Overflow",
                link=f"https://stackoverflow.com/search?q={query.replace(' ', '+')}",
                snippet="Busca preguntas y respuestas en Stack Overflow",
                position=2,
                source="stackoverflow.com",
                relevance_score=0.4,
                content_type="fallback"
            ),
            SearchResult(
                title=f"Buscar '{query}' en GitHub",
                link=f"https://github.com/search?q={query.replace(' ', '+')}",
                snippet="Busca repositorios y código en GitHub",
                position=3,
                source="github.com",
                relevance_score=0.3,
                content_type="fallback"
            )
        ]
        
        return SearchResponse(
            query=query,
            results=suggestions,
            total_results=len(suggestions),
            search_time=0.0,
            cached=False,
            filters_applied=[f.value for f in filters]
        )
    
    async def search_code_examples(
        self,
        technology: str,
        task: str,
        language: str = "python"
    ) -> SearchResponse:
        """Búsqueda especializada para ejemplos de código"""
        query = f"{technology} {task} {language} example code"
        return await self.search(
            query,
            filters=[ContentFilter.GITHUB, ContentFilter.STACKOVERFLOW]
        )
    
    async def search_documentation(
        self,
        library: str,
        topic: str
    ) -> SearchResponse:
        """Búsqueda especializada para documentación"""
        query = f"{library} {topic} documentation"
        return await self.search(
            query,
            filters=[ContentFilter.DOCUMENTATION, ContentFilter.OFFICIAL]
        )
    
    async def search_error_solution(
        self,
        error_message: str,
        technology: str = ""
    ) -> SearchResponse:
        """Búsqueda especializada para soluciones de errores"""
        error_clean = error_message[:200]
        query = f"{technology} {error_clean}"
        return await self.search(
            query,
            filters=[ContentFilter.STACKOVERFLOW]
        )
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del servicio"""
        return {
            "configured": self.is_configured(),
            "total_searches": self.total_searches,
            "failed_searches": self.failed_searches,
            "success_rate": f"{((self.total_searches - self.failed_searches) / max(1, self.total_searches)) * 100:.1f}%",
            "cache": self.cache.get_stats(),
            "rate_limiter": self.rate_limiter.get_stats()
        }
    
    def clear_cache(self):
        """Limpia el cache de búsquedas"""
        self.cache.clear()

class SearchError(Exception):
    """Error general de búsqueda"""
    pass

class RateLimitError(SearchError):
    """Error de rate limit"""
    pass

web_search_service = WebSearchService()
