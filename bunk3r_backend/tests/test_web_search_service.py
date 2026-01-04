"""
Tests para WebSearchService (34.A.1)
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import time
from datetime import datetime, timedelta

from bunk3r_core.web_search_service import (
    WebSearchService,
    SearchCache,
    RateLimiter,
    SearchType,
    ContentFilter,
    SearchResult,
    SearchResponse,
    SearchError,
    RateLimitError,
    web_search_service
)


class TestSearchCache:
    """Tests para SearchCache"""
    
    def test_cache_creation(self):
        """Test crear cache con TTL"""
        cache = SearchCache(ttl_hours=24, max_entries=100)
        assert cache.ttl == timedelta(hours=24)
        assert cache.max_entries == 100
        assert len(cache.cache) == 0
    
    def test_cache_set_and_get(self):
        """Test guardar y recuperar del cache"""
        cache = SearchCache()
        
        response = SearchResponse(
            query="test query",
            results=[
                SearchResult(
                    title="Test Result",
                    link="https://example.com",
                    snippet="Test snippet",
                    position=1
                )
            ],
            total_results=1,
            search_time=0.5
        )
        
        cache.set("test query", "search", ["all"], response)
        
        cached = cache.get("test query", "search", ["all"])
        assert cached is not None
        assert cached.query == "test query"
        assert cached.cached is True
        assert len(cached.results) == 1
    
    def test_cache_miss(self):
        """Test cache miss"""
        cache = SearchCache()
        result = cache.get("nonexistent", "search", ["all"])
        assert result is None
    
    def test_cache_key_generation(self):
        """Test generación de claves únicas"""
        cache = SearchCache()
        
        key1 = cache._generate_key("query1", "search", ["all"])
        key2 = cache._generate_key("query2", "search", ["all"])
        key3 = cache._generate_key("query1", "news", ["all"])
        
        assert key1 != key2
        assert key1 != key3
    
    def test_cache_stats(self):
        """Test estadísticas del cache"""
        cache = SearchCache()
        
        response = SearchResponse(
            query="test",
            results=[],
            total_results=0,
            search_time=0.1
        )
        
        cache.set("test", "search", [], response)
        cache.get("test", "search", [])
        cache.get("nonexistent", "search", [])
        
        stats = cache.get_stats()
        assert stats["entries"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 1
    
    def test_cache_clear(self):
        """Test limpiar cache"""
        cache = SearchCache()
        
        response = SearchResponse(
            query="test",
            results=[],
            total_results=0,
            search_time=0.1
        )
        
        cache.set("test", "search", [], response)
        assert len(cache.cache) == 1
        
        cache.clear()
        assert len(cache.cache) == 0
        assert cache.hits == 0
        assert cache.misses == 0


class TestRateLimiter:
    """Tests para RateLimiter"""
    
    def test_rate_limiter_creation(self):
        """Test crear rate limiter"""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        assert limiter.max_requests == 10
        assert limiter.window == 60
    
    def test_can_proceed_when_empty(self):
        """Test que permite solicitudes cuando está vacío"""
        limiter = RateLimiter(max_requests=5)
        assert limiter.can_proceed() is True
    
    def test_can_proceed_after_limit(self):
        """Test que bloquea después del límite"""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        limiter.record_request()
        limiter.record_request()
        
        assert limiter.can_proceed() is False
    
    def test_wait_time(self):
        """Test tiempo de espera"""
        limiter = RateLimiter(max_requests=1, window_seconds=10)
        
        assert limiter.wait_time() == 0
        
        limiter.record_request()
        wait = limiter.wait_time()
        assert wait > 0
    
    def test_rate_limiter_stats(self):
        """Test estadísticas"""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        limiter.record_request()
        limiter.record_request()
        
        stats = limiter.get_stats()
        assert stats["current_requests"] == 2
        assert stats["max_requests"] == 10
        assert stats["remaining"] == 8


class TestSearchResult:
    """Tests para SearchResult"""
    
    def test_search_result_creation(self):
        """Test crear resultado de búsqueda"""
        result = SearchResult(
            title="Test Title",
            link="https://example.com",
            snippet="Test snippet text",
            position=1,
            source="example.com",
            relevance_score=0.9,
            content_type="documentation"
        )
        
        assert result.title == "Test Title"
        assert result.link == "https://example.com"
        assert result.position == 1
        assert result.content_type == "documentation"
    
    def test_search_result_to_dict(self):
        """Test convertir a diccionario"""
        result = SearchResult(
            title="Test",
            link="https://test.com",
            snippet="Snippet",
            position=1
        )
        
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["title"] == "Test"
        assert d["link"] == "https://test.com"


class TestSearchResponse:
    """Tests para SearchResponse"""
    
    def test_search_response_creation(self):
        """Test crear respuesta de búsqueda"""
        results = [
            SearchResult(
                title="Result 1",
                link="https://r1.com",
                snippet="S1",
                position=1
            ),
            SearchResult(
                title="Result 2",
                link="https://r2.com",
                snippet="S2",
                position=2
            )
        ]
        
        response = SearchResponse(
            query="test query",
            results=results,
            total_results=2,
            search_time=0.5,
            filters_applied=["documentation"]
        )
        
        assert response.query == "test query"
        assert len(response.results) == 2
        assert response.total_results == 2
        assert response.search_time == 0.5
    
    def test_search_response_to_dict(self):
        """Test convertir respuesta a diccionario"""
        response = SearchResponse(
            query="test",
            results=[],
            total_results=0,
            search_time=0.1
        )
        
        d = response.to_dict()
        assert isinstance(d, dict)
        assert d["query"] == "test"
        assert d["results"] == []


class TestContentFilter:
    """Tests para ContentFilter"""
    
    def test_content_filter_values(self):
        """Test valores de filtros"""
        assert ContentFilter.DOCUMENTATION.value == "documentation"
        assert ContentFilter.TUTORIAL.value == "tutorial"
        assert ContentFilter.STACKOVERFLOW.value == "stackoverflow"
        assert ContentFilter.GITHUB.value == "github"
        assert ContentFilter.ALL.value == "all"


class TestSearchType:
    """Tests para SearchType"""
    
    def test_search_type_values(self):
        """Test valores de tipos de búsqueda"""
        assert SearchType.GENERAL.value == "search"
        assert SearchType.NEWS.value == "news"
        assert SearchType.IMAGES.value == "images"


class TestWebSearchService:
    """Tests para WebSearchService"""
    
    def test_service_creation(self):
        """Test crear servicio"""
        service = WebSearchService()
        assert service.cache is not None
        assert service.rate_limiter is not None
    
    def test_service_with_api_key(self):
        """Test servicio con API key"""
        service = WebSearchService(api_key="test_key")
        assert service.is_configured() is True
    
    def test_service_without_api_key(self):
        """Test servicio sin API key usa fallback"""
        service = WebSearchService(api_key=None)
        with patch.dict('os.environ', {}, clear=True):
            assert service.api_key is None
    
    def test_apply_filters_all(self):
        """Test aplicar filtro ALL no modifica query"""
        service = WebSearchService()
        query = service._apply_filters("test query", [ContentFilter.ALL])
        assert query == "test query"
    
    def test_apply_filters_stackoverflow(self):
        """Test aplicar filtro StackOverflow"""
        service = WebSearchService()
        query = service._apply_filters("python error", [ContentFilter.STACKOVERFLOW])
        assert "site:stackoverflow.com" in query
    
    def test_apply_filters_github(self):
        """Test aplicar filtro GitHub"""
        service = WebSearchService()
        query = service._apply_filters("flask example", [ContentFilter.GITHUB])
        assert "site:github.com" in query
    
    def test_extract_source(self):
        """Test extraer dominio de URL"""
        service = WebSearchService()
        
        source = service._extract_source("https://www.example.com/page")
        assert source == "example.com"
        
        source = service._extract_source("https://docs.python.org/3/")
        assert source == "docs.python.org"
    
    def test_detect_content_type_stackoverflow(self):
        """Test detectar tipo StackOverflow"""
        service = WebSearchService()
        item = {"link": "https://stackoverflow.com/questions/12345"}
        assert service._detect_content_type(item) == "stackoverflow"
    
    def test_detect_content_type_github(self):
        """Test detectar tipo GitHub"""
        service = WebSearchService()
        item = {"link": "https://github.com/user/repo"}
        assert service._detect_content_type(item) == "github"
    
    def test_detect_content_type_documentation(self):
        """Test detectar tipo documentación"""
        service = WebSearchService()
        item = {"link": "https://docs.python.org/", "title": "Python documentation"}
        assert service._detect_content_type(item) == "documentation"
    
    def test_detect_content_type_tutorial(self):
        """Test detectar tipo tutorial"""
        service = WebSearchService()
        item = {"link": "https://example.com", "title": "How to build a web app"}
        assert service._detect_content_type(item) == "tutorial"
    
    def test_calculate_relevance(self):
        """Test calcular relevancia"""
        service = WebSearchService()
        
        score1 = service._calculate_relevance({"snippet": "short"}, 0)
        score2 = service._calculate_relevance({"snippet": "short"}, 5)
        
        assert score1 > score2
    
    def test_extract_snippet(self):
        """Test extraer snippet"""
        service = WebSearchService()
        
        item = {"snippet": "   Test snippet   "}
        snippet = service._extract_snippet(item)
        assert snippet == "Test snippet"
    
    def test_extract_snippet_truncate(self):
        """Test truncar snippet largo"""
        service = WebSearchService()
        
        long_text = "x" * 600
        item = {"snippet": long_text}
        snippet = service._extract_snippet(item)
        assert len(snippet) == 500
        assert snippet.endswith("...")
    
    def test_fallback_search(self):
        """Test búsqueda fallback sin API"""
        service = WebSearchService(api_key=None)
        
        response = service._fallback_search("python flask", [ContentFilter.ALL])
        
        assert response.query == "python flask"
        assert len(response.results) == 3
        assert response.results[0].content_type == "fallback"
    
    def test_get_stats(self):
        """Test obtener estadísticas"""
        service = WebSearchService()
        
        stats = service.get_stats()
        
        assert "configured" in stats
        assert "total_searches" in stats
        assert "cache" in stats
        assert "rate_limiter" in stats
    
    def test_clear_cache(self):
        """Test limpiar cache"""
        service = WebSearchService()
        
        response = SearchResponse(
            query="test",
            results=[],
            total_results=0,
            search_time=0.1
        )
        service.cache.set("test", "search", [], response)
        
        service.clear_cache()
        
        assert len(service.cache.cache) == 0
    
    def test_search_rate_limit(self):
        """Test rate limiting"""
        service = WebSearchService(rate_limit_requests=1, rate_limit_window=60)
        service.rate_limiter.record_request()
        
        with pytest.raises(RateLimitError):
            service.search_sync("test query")
    
    def test_search_sync_fallback(self):
        """Test búsqueda síncrona con fallback"""
        service = WebSearchService(api_key=None)
        
        with patch.object(service, 'api_key', None):
            response = service.search_sync("test query")
            
            assert response.query == "test query"
            assert len(response.results) >= 1


class TestWebSearchServiceIntegration:
    """Tests de integración"""
    
    def test_global_service_instance(self):
        """Test instancia global"""
        assert web_search_service is not None
        assert isinstance(web_search_service, WebSearchService)
    
    def test_search_code_examples(self):
        """Test búsqueda de ejemplos de código"""
        service = WebSearchService(api_key=None)
        
        query = "flask routing python example code"
        response = service.search_sync(
            query=query,
            filters=[ContentFilter.GITHUB, ContentFilter.STACKOVERFLOW]
        )
        assert response is not None
        assert response.query == query
    
    def test_search_documentation(self):
        """Test búsqueda de documentación"""
        service = WebSearchService(api_key=None)
        
        query = "flask blueprints documentation"
        response = service.search_sync(
            query=query,
            filters=[ContentFilter.DOCUMENTATION]
        )
        assert response is not None
        assert response.query == query
    
    def test_search_error_solution(self):
        """Test búsqueda de solución de errores"""
        service = WebSearchService(api_key=None)
        
        query = "python ImportError: No module"
        response = service.search_sync(
            query=query,
            filters=[ContentFilter.STACKOVERFLOW]
        )
        assert response is not None
        assert response.query == query


class TestParseResults:
    """Tests para parseo de resultados"""
    
    def test_parse_empty_results(self):
        """Test parsear resultados vacíos"""
        service = WebSearchService()
        
        data = {"organic": []}
        results = service._parse_results(data, SearchType.GENERAL)
        
        assert results == []
    
    def test_parse_organic_results(self):
        """Test parsear resultados orgánicos"""
        service = WebSearchService()
        
        data = {
            "organic": [
                {
                    "title": "Test Title",
                    "link": "https://example.com",
                    "snippet": "Test snippet"
                }
            ]
        }
        
        results = service._parse_results(data, SearchType.GENERAL)
        
        assert len(results) == 1
        assert results[0].title == "Test Title"
        assert results[0].position == 1
    
    def test_parse_with_knowledge_graph(self):
        """Test parsear con knowledge graph"""
        service = WebSearchService()
        
        data = {
            "organic": [
                {"title": "Result", "link": "https://r.com", "snippet": "S"}
            ],
            "knowledgeGraph": {
                "title": "Knowledge Title",
                "description": "KG Description",
                "website": "https://kg.com"
            }
        }
        
        results = service._parse_results(data, SearchType.GENERAL)
        
        assert len(results) == 2
        assert results[0].source == "knowledge_graph"
        assert results[0].position == 0
