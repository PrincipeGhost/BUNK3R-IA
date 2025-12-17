"""
BUNK3R AI - Tests for SmartRetrySystem (smart_retry.py)
Tests for Section 34.17: Intelligent Retry System
"""

import pytest
import time
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from BUNK3R_IA.core.smart_retry import (
    SmartRetrySystem, RetryConfig, RetryStrategy, RetryReason,
    RetryAttempt, RetryResult, retry_decorator, execute_with_retry
)


class TestRetryConfig:
    """Tests for RetryConfig dataclass"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.base_delay_seconds == 1.0
        assert config.max_delay_seconds == 30.0
        assert config.strategy == RetryStrategy.EXPONENTIAL
        assert config.jitter == True
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = RetryConfig(
            max_attempts=5,
            base_delay_seconds=2.0,
            strategy=RetryStrategy.LINEAR
        )
        assert config.max_attempts == 5
        assert config.base_delay_seconds == 2.0
        assert config.strategy == RetryStrategy.LINEAR
    
    def test_config_to_dict(self):
        """Test config serialization"""
        config = RetryConfig()
        config_dict = config.to_dict()
        
        assert "max_attempts" in config_dict
        assert "strategy" in config_dict
        assert config_dict["strategy"] == "exponential"


class TestRetryStrategy:
    """Tests for RetryStrategy enum"""
    
    def test_strategies_exist(self):
        """Test all strategies exist"""
        assert RetryStrategy.EXPONENTIAL
        assert RetryStrategy.LINEAR
        assert RetryStrategy.FIXED
        assert RetryStrategy.FIBONACCI


class TestRetryReason:
    """Tests for RetryReason enum"""
    
    def test_reasons_exist(self):
        """Test all retry reasons exist"""
        assert RetryReason.TIMEOUT
        assert RetryReason.RATE_LIMIT
        assert RetryReason.SERVER_ERROR
        assert RetryReason.NETWORK_ERROR
        assert RetryReason.UNKNOWN


class TestSmartRetrySystem:
    """Tests for SmartRetrySystem class"""
    
    @pytest.fixture
    def retry_system(self):
        config = RetryConfig(
            max_attempts=3,
            base_delay_seconds=0.01,
            jitter=False
        )
        return SmartRetrySystem(config)
    
    def test_successful_first_attempt(self, retry_system):
        """Test function succeeds on first attempt"""
        mock_func = Mock(return_value={"success": True, "data": "test"})
        
        result = retry_system.execute_with_retry(mock_func, providers=["provider1"])
        
        assert result.success == True
        assert result.total_attempts == 1
        assert result.result["data"] == "test"
    
    def test_retry_on_failure(self, retry_system):
        """Test retry on function failure"""
        mock_func = Mock(side_effect=[
            {"success": False, "error": "timeout"},
            {"success": True, "data": "test"}
        ])
        
        result = retry_system.execute_with_retry(mock_func, providers=["provider1"])
        
        assert result.success == True
        assert result.total_attempts == 2
    
    def test_max_attempts_exceeded(self, retry_system):
        """Test failure after max attempts"""
        mock_func = Mock(return_value={"success": False, "error": "always fails"})
        
        result = retry_system.execute_with_retry(mock_func, providers=["provider1"])
        
        assert result.success == False
        assert result.total_attempts == 3
    
    def test_exception_handling(self, retry_system):
        """Test handling of exceptions"""
        mock_func = Mock(side_effect=Exception("Connection error"))
        
        result = retry_system.execute_with_retry(mock_func, providers=["provider1"])
        
        assert result.success == False
        assert result.total_attempts == 3
    
    def test_provider_switching(self, retry_system):
        """Test automatic provider switching after failures"""
        calls = []
        
        def track_provider(provider=None, **kwargs):
            calls.append(provider)
            if len(calls) < 3:
                return {"success": False, "error": "failed"}
            return {"success": True}
        
        result = retry_system.execute_with_retry(
            track_provider,
            providers=["provider1", "provider2", "provider3"]
        )
        
        assert len(calls) == 3
        assert calls[-1] != calls[0]
    
    def test_classify_timeout_error(self, retry_system):
        """Test timeout error classification"""
        reason = retry_system._classify_error("Request timed out after 30s")
        assert reason == RetryReason.TIMEOUT
    
    def test_classify_rate_limit_error(self, retry_system):
        """Test rate limit error classification"""
        reason = retry_system._classify_error("429 Too Many Requests")
        assert reason == RetryReason.RATE_LIMIT
    
    def test_classify_server_error(self, retry_system):
        """Test server error classification"""
        reason = retry_system._classify_error("500 Internal Server Error")
        assert reason == RetryReason.SERVER_ERROR
    
    def test_classify_network_error(self, retry_system):
        """Test network error classification"""
        reason = retry_system._classify_error("Connection refused")
        assert reason == RetryReason.NETWORK_ERROR
    
    def test_classify_unknown_error(self, retry_system):
        """Test unknown error classification"""
        reason = retry_system._classify_error("Something weird happened")
        assert reason == RetryReason.UNKNOWN
    
    def test_exponential_delay_calculation(self, retry_system):
        """Test exponential backoff delay calculation"""
        config = RetryConfig(
            base_delay_seconds=1.0,
            max_delay_seconds=100.0,
            strategy=RetryStrategy.EXPONENTIAL,
            jitter=False
        )
        retry_system.default_config = config
        
        delay1 = retry_system._calculate_delay(1, config)
        delay2 = retry_system._calculate_delay(2, config)
        delay3 = retry_system._calculate_delay(3, config)
        
        assert delay1 == 1.0
        assert delay2 == 2.0
        assert delay3 == 4.0
    
    def test_linear_delay_calculation(self, retry_system):
        """Test linear backoff delay calculation"""
        config = RetryConfig(
            base_delay_seconds=1.0,
            strategy=RetryStrategy.LINEAR,
            jitter=False
        )
        
        delay1 = retry_system._calculate_delay(1, config)
        delay2 = retry_system._calculate_delay(2, config)
        delay3 = retry_system._calculate_delay(3, config)
        
        assert delay1 == 1.0
        assert delay2 == 2.0
        assert delay3 == 3.0
    
    def test_fixed_delay_calculation(self, retry_system):
        """Test fixed delay calculation"""
        config = RetryConfig(
            base_delay_seconds=2.0,
            strategy=RetryStrategy.FIXED,
            jitter=False
        )
        
        delay1 = retry_system._calculate_delay(1, config)
        delay2 = retry_system._calculate_delay(2, config)
        
        assert delay1 == 2.0
        assert delay2 == 2.0
    
    def test_delay_max_cap(self, retry_system):
        """Test delay is capped at max_delay_seconds"""
        config = RetryConfig(
            base_delay_seconds=10.0,
            max_delay_seconds=15.0,
            strategy=RetryStrategy.EXPONENTIAL,
            jitter=False
        )
        
        delay = retry_system._calculate_delay(5, config)
        
        assert delay <= 15.0
    
    def test_failure_stats(self, retry_system):
        """Test failure statistics tracking"""
        mock_func = Mock(return_value={"success": False, "error": "timeout"})
        
        retry_system.execute_with_retry(mock_func, providers=["provider1"])
        
        stats = retry_system.get_failure_stats()
        
        assert stats["total_failures"] > 0
        assert "failures_by_reason" in stats
        assert "failures_by_provider" in stats
    
    def test_reset_provider_scores(self, retry_system):
        """Test resetting provider failure scores"""
        retry_system.provider_failures["test_provider"] = 5
        
        retry_system.reset_provider_scores()
        
        assert len(retry_system.provider_failures) == 0
    
    def test_clear_failure_log(self, retry_system):
        """Test clearing failure log"""
        mock_func = Mock(return_value={"success": False, "error": "error"})
        retry_system.execute_with_retry(mock_func, providers=["p1"])
        
        retry_system.clear_failure_log()
        
        assert len(retry_system.failure_log) == 0
    
    def test_on_retry_callback(self, retry_system):
        """Test on_retry callback is called"""
        callback_calls = []
        
        def on_retry(attempt, provider, error):
            callback_calls.append((attempt, provider, error))
        
        mock_func = Mock(side_effect=[
            {"success": False, "error": "fail"},
            {"success": True}
        ])
        
        retry_system.execute_with_retry(
            mock_func,
            providers=["p1"],
            on_retry=on_retry
        )
        
        assert len(callback_calls) == 1


class TestRetryDecorator:
    """Tests for retry_decorator"""
    
    def test_decorator_success(self):
        """Test decorator with successful function"""
        @retry_decorator(max_attempts=3, base_delay=0.01)
        def successful_func():
            return {"success": True, "data": "test"}
        
        result = successful_func()
        assert result["data"] == "test"
    
    def test_decorator_with_retries(self):
        """Test decorator retries on failure"""
        call_count = {"count": 0}
        
        @retry_decorator(max_attempts=3, base_delay=0.01)
        def flaky_func():
            call_count["count"] += 1
            if call_count["count"] < 2:
                return {"success": False}
            return {"success": True, "data": "worked"}
        
        result = flaky_func()
        assert result["data"] == "worked"
        assert call_count["count"] == 2


class TestExecuteWithRetry:
    """Tests for execute_with_retry helper function"""
    
    def test_execute_with_retry_success(self):
        """Test helper function with success"""
        mock_func = Mock(return_value={"success": True, "data": "test"})
        
        result = execute_with_retry(mock_func, max_attempts=3)
        
        assert result["success"] == True
    
    def test_execute_with_retry_returns_dict(self):
        """Test helper function returns dict"""
        mock_func = Mock(return_value={"success": True})
        
        result = execute_with_retry(mock_func)
        
        assert isinstance(result, dict)
        assert "total_attempts" in result


class TestRetryAttempt:
    """Tests for RetryAttempt dataclass"""
    
    def test_attempt_to_dict(self):
        """Test RetryAttempt serialization"""
        from datetime import datetime
        
        attempt = RetryAttempt(
            attempt_number=1,
            timestamp=datetime.now(),
            provider="test",
            success=True,
            error=None,
            duration_ms=100,
            retry_reason=None
        )
        
        attempt_dict = attempt.to_dict()
        
        assert "attempt_number" in attempt_dict
        assert "provider" in attempt_dict
        assert "success" in attempt_dict


class TestRetryResult:
    """Tests for RetryResult dataclass"""
    
    def test_result_to_dict(self):
        """Test RetryResult serialization"""
        result = RetryResult(
            success=True,
            result={"data": "test"},
            total_attempts=1,
            attempts=[],
            final_provider="test",
            total_duration_ms=100
        )
        
        result_dict = result.to_dict()
        
        assert "success" in result_dict
        assert "total_attempts" in result_dict
        assert "final_provider" in result_dict
