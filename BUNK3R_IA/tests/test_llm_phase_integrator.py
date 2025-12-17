"""
BUNK3R AI - Tests for LLMPhaseIntegrator (llm_phase_integrator.py)
Tests for Section 34.7: LLM Integration with 8 Phases
"""

import pytest
import json
from unittest.mock import Mock, MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from BUNK3R_IA.core.llm_phase_integrator import (
    LLMPhaseIntegrator, ConstructorPhase, PhaseResult, PhasePrompts
)


class TestConstructorPhase:
    """Tests for ConstructorPhase enum"""
    
    def test_all_phases_exist(self):
        """Test all 8 phases exist"""
        assert ConstructorPhase.INTENT_ANALYSIS.value == 1
        assert ConstructorPhase.RESEARCH.value == 2
        assert ConstructorPhase.CLARIFICATION.value == 3
        assert ConstructorPhase.PROMPT_BUILDING.value == 4
        assert ConstructorPhase.PLAN_PRESENTATION.value == 5
        assert ConstructorPhase.EXECUTION.value == 6
        assert ConstructorPhase.VERIFICATION.value == 7
        assert ConstructorPhase.DELIVERY.value == 8
    
    def test_phase_count(self):
        """Test there are exactly 8 phases"""
        assert len(ConstructorPhase) == 8


class TestPhasePrompts:
    """Tests for PhasePrompts"""
    
    def test_intent_analysis_prompt_exists(self):
        """Test intent analysis prompt exists"""
        assert hasattr(PhasePrompts, 'INTENT_ANALYSIS')
        assert "{user_request}" in PhasePrompts.INTENT_ANALYSIS
    
    def test_research_prompt_exists(self):
        """Test research prompt exists"""
        assert hasattr(PhasePrompts, 'RESEARCH')
        assert "{intent_analysis}" in PhasePrompts.RESEARCH
    
    def test_clarification_prompt_exists(self):
        """Test clarification prompt exists"""
        assert hasattr(PhasePrompts, 'CLARIFICATION')
        assert "{user_request}" in PhasePrompts.CLARIFICATION
    
    def test_prompt_building_prompt_exists(self):
        """Test prompt building prompt exists"""
        assert hasattr(PhasePrompts, 'PROMPT_BUILDING')
    
    def test_plan_presentation_prompt_exists(self):
        """Test plan presentation prompt exists"""
        assert hasattr(PhasePrompts, 'PLAN_PRESENTATION')
    
    def test_execution_prompt_exists(self):
        """Test execution prompt exists"""
        assert hasattr(PhasePrompts, 'EXECUTION')
        assert "{current_task}" in PhasePrompts.EXECUTION
    
    def test_verification_prompt_exists(self):
        """Test verification prompt exists"""
        assert hasattr(PhasePrompts, 'VERIFICATION')
        assert "{code}" in PhasePrompts.VERIFICATION
    
    def test_delivery_prompt_exists(self):
        """Test delivery prompt exists"""
        assert hasattr(PhasePrompts, 'DELIVERY')


class TestPhaseResult:
    """Tests for PhaseResult dataclass"""
    
    def test_phase_result_creation(self):
        """Test PhaseResult creation"""
        result = PhaseResult(
            phase=ConstructorPhase.INTENT_ANALYSIS,
            success=True,
            data={"tipo_tarea": "crear_web"},
            llm_response="test response",
            tokens_used=100,
            provider_used="test_provider",
            duration_ms=500,
            retries=0
        )
        
        assert result.phase == ConstructorPhase.INTENT_ANALYSIS
        assert result.success == True
        assert result.data["tipo_tarea"] == "crear_web"
    
    def test_phase_result_to_dict(self):
        """Test PhaseResult serialization"""
        result = PhaseResult(
            phase=ConstructorPhase.RESEARCH,
            success=True,
            data={"test": "data"},
            provider_used="groq"
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["phase"] == 2
        assert result_dict["phase_name"] == "RESEARCH"
        assert result_dict["success"] == True
        assert result_dict["provider_used"] == "groq"


class TestLLMPhaseIntegrator:
    """Tests for LLMPhaseIntegrator class"""
    
    @pytest.fixture
    def mock_ai_service(self):
        """Create mock AI service"""
        service = Mock()
        service.chat.return_value = {
            "success": True,
            "response": '```json\n{"tipo_tarea": "crear_web"}\n```',
            "provider": "mock"
        }
        service.get_available_providers.return_value = ["mock"]
        return service
    
    @pytest.fixture
    def integrator(self, mock_ai_service):
        """Create integrator with mock service"""
        with patch('BUNK3R_IA.core.llm_phase_integrator.get_ai_service', return_value=mock_ai_service):
            integrator = LLMPhaseIntegrator(ai_service=mock_ai_service)
            return integrator
    
    def test_integrator_creation(self, integrator):
        """Test integrator is created correctly"""
        assert integrator is not None
        assert integrator.ai_service is not None
    
    def test_parse_json_from_markdown(self, integrator):
        """Test JSON parsing from markdown code blocks"""
        response = '```json\n{"key": "value"}\n```'
        
        success, data = integrator._parse_json_response(response)
        
        assert success == True
        assert data["key"] == "value"
    
    def test_parse_json_direct(self, integrator):
        """Test direct JSON parsing"""
        response = '{"key": "value"}'
        
        success, data = integrator._parse_json_response(response)
        
        assert success == True
        assert data["key"] == "value"
    
    def test_parse_invalid_json(self, integrator):
        """Test handling of invalid JSON"""
        response = "This is not JSON"
        
        success, data = integrator._parse_json_response(response)
        
        assert success == False
        assert "raw_response" in data
    
    def test_phase_prompts_defined(self, integrator):
        """Test that phase prompts are defined"""
        assert PhasePrompts.INTENT_ANALYSIS is not None
        assert PhasePrompts.RESEARCH is not None
        assert PhasePrompts.EXECUTION is not None
        assert "{user_request}" in PhasePrompts.INTENT_ANALYSIS
    
    def test_get_phase_system_prompt_returns_string(self, integrator):
        """Test that system prompts are returned for each phase"""
        for phase in ConstructorPhase:
            prompt = integrator._get_phase_system_prompt(phase)
            assert isinstance(prompt, str)
            assert "BUNK3R" in prompt
    
    def test_process_phase_result_adds_defaults(self, integrator):
        """Test that processing adds default values"""
        parsed_data = {}
        input_data = {"user_request": "test"}
        
        processed = integrator._process_phase_result(
            ConstructorPhase.INTENT_ANALYSIS,
            parsed_data,
            input_data
        )
        
        assert "tipo_tarea" in processed
        assert processed["tipo_tarea"] == "consulta_general"
    
    def test_get_phase_system_prompt(self, integrator):
        """Test getting phase-specific system prompts"""
        prompt = integrator._get_phase_system_prompt(ConstructorPhase.INTENT_ANALYSIS)
        
        assert "BUNK3R" in prompt
        assert "requerimientos" in prompt.lower() or "intenciones" in prompt.lower()
    
    def test_call_llm_without_service(self, integrator):
        """Test _call_llm returns error without service"""
        integrator.ai_service = None
        
        result = integrator._call_llm("test prompt")
        
        assert result["success"] == False
        assert "error" in result
    
    def test_process_execution_phase_code_extraction(self, integrator):
        """Test code extraction from execution phase"""
        parsed_data = {
            "raw_response": "```python\nprint('hello')\n```"
        }
        input_data = {}
        
        processed = integrator._process_phase_result(
            ConstructorPhase.EXECUTION,
            parsed_data,
            input_data
        )
        
        assert "generated_code" in processed
        assert "print('hello')" in processed["generated_code"]


class TestLLMPhaseIntegratorNoService:
    """Tests for LLMPhaseIntegrator without AI service"""
    
    def test_integrator_without_service(self):
        """Test integrator handles missing AI service"""
        with patch('BUNK3R_IA.core.llm_phase_integrator.get_ai_service', return_value=None):
            with patch('BUNK3R_IA.core.llm_phase_integrator.AIService', None):
                integrator = LLMPhaseIntegrator()
                
                result = integrator._call_llm("test prompt")
                
                assert result["success"] == False
                assert "no disponible" in result["error"].lower()


class TestLLMPhaseIntegratorIntegration:
    """Integration tests for LLMPhaseIntegrator"""
    
    def test_phase_result_serialization(self):
        """Test that PhaseResult can be serialized"""
        result = PhaseResult(
            phase=ConstructorPhase.INTENT_ANALYSIS,
            success=True,
            data={"tipo_tarea": "crear_web"},
            llm_response="test",
            provider_used="mock"
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["phase"] == 1
        assert result_dict["success"] == True
        assert "tipo_tarea" in result_dict["data"]
    
    def test_all_phases_have_prompts(self):
        """Test that all phases have defined prompts"""
        prompts = [
            PhasePrompts.INTENT_ANALYSIS,
            PhasePrompts.RESEARCH,
            PhasePrompts.CLARIFICATION,
            PhasePrompts.PROMPT_BUILDING,
            PhasePrompts.PLAN_PRESENTATION,
            PhasePrompts.EXECUTION,
            PhasePrompts.VERIFICATION,
            PhasePrompts.DELIVERY
        ]
        
        for prompt in prompts:
            assert prompt is not None
            assert len(prompt) > 100
