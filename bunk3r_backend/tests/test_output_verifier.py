"""
BUNK3R AI - Tests for OutputVerifier (output_verifier.py)
Tests for Section 34.5: Code Verification System
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from bunk3r_core.output_verifier import (
    OutputVerifier, CodeLanguage, SyntaxIssue, ImportIssue,
    QualityMetric, VerificationReport
)


class TestCodeLanguageDetection:
    """Tests for language detection"""
    
    @pytest.fixture
    def verifier(self):
        return OutputVerifier()
    
    def test_detect_python_by_extension(self, verifier):
        """Test Python detection by file extension"""
        lang = verifier.detect_language("print('hello')", "test.py")
        assert lang == CodeLanguage.PYTHON
    
    def test_detect_javascript_by_extension(self, verifier):
        """Test JavaScript detection by file extension"""
        lang = verifier.detect_language("console.log('hello')", "test.js")
        assert lang == CodeLanguage.JAVASCRIPT
    
    def test_detect_html_by_extension(self, verifier):
        """Test HTML detection by file extension"""
        lang = verifier.detect_language("<html></html>", "index.html")
        assert lang == CodeLanguage.HTML
    
    def test_detect_css_by_extension(self, verifier):
        """Test CSS detection by file extension"""
        lang = verifier.detect_language("body { color: red; }", "styles.css")
        assert lang == CodeLanguage.CSS
    
    def test_detect_json_by_extension(self, verifier):
        """Test JSON detection by file extension"""
        lang = verifier.detect_language('{"key": "value"}', "config.json")
        assert lang == CodeLanguage.JSON
    
    def test_detect_python_by_content(self, verifier):
        """Test Python detection by code content"""
        code = """
import os
from typing import Dict

def hello():
    pass

class MyClass:
    pass
"""
        lang = verifier.detect_language(code)
        assert lang == CodeLanguage.PYTHON
    
    def test_detect_javascript_by_content(self, verifier):
        """Test JavaScript detection by code content"""
        code = """
const express = require('express');
let app = express();

function handler(req, res) {
    res.send('hello');
}

export default app;
"""
        lang = verifier.detect_language(code)
        assert lang == CodeLanguage.JAVASCRIPT
    
    def test_detect_html_by_doctype(self, verifier):
        """Test HTML detection by DOCTYPE"""
        code = "<!DOCTYPE html><html><body></body></html>"
        lang = verifier.detect_language(code)
        assert lang == CodeLanguage.HTML
    
    def test_detect_css_by_content(self, verifier):
        """Test CSS detection by content patterns"""
        code = """
body {
    font-size: 16px;
}

.container {
    max-width: 1200px;
}

@media (max-width: 768px) {
    .container {
        padding: 10px;
    }
}
"""
        lang = verifier.detect_language(code)
        assert lang == CodeLanguage.CSS
    
    def test_detect_sql_by_content(self, verifier):
        """Test SQL detection by content patterns"""
        code = "SELECT * FROM users WHERE id = 1; INSERT INTO logs VALUES (1, 'test');"
        lang = verifier.detect_language(code)
        assert lang == CodeLanguage.SQL


class TestPythonValidation:
    """Tests for Python code validation"""
    
    @pytest.fixture
    def verifier(self):
        return OutputVerifier()
    
    def test_valid_python(self, verifier, sample_python_code):
        """Test valid Python code passes validation"""
        report = verifier.verify(sample_python_code, "app.py")
        
        assert report.syntax_valid == True
        assert len([e for e in report.syntax_issues if e.severity == "error"]) == 0
    
    def test_invalid_python_syntax(self, verifier, sample_invalid_python):
        """Test invalid Python syntax is detected"""
        report = verifier.verify(sample_invalid_python, "broken.py")
        
        assert report.syntax_valid == False
        assert len(report.syntax_issues) > 0
    
    def test_python_import_check(self, verifier):
        """Test Python import verification"""
        code = """
import os
import json
from custom_module import something
"""
        report = verifier.verify(code, "test.py")
        
        assert any(i.module == "custom_module" for i in report.import_issues)


class TestJavaScriptValidation:
    """Tests for JavaScript code validation"""
    
    @pytest.fixture
    def verifier(self):
        return OutputVerifier()
    
    def test_valid_javascript(self, verifier, sample_javascript_code):
        """Test valid JavaScript code passes validation"""
        report = verifier.verify(sample_javascript_code, "script.js")
        
        assert report.syntax_valid == True
    
    def test_unbalanced_brackets(self, verifier):
        """Test unbalanced brackets are detected"""
        code = """
function test() {
    if (true) {
        console.log('hello');
    // missing closing braces
"""
        report = verifier.verify(code, "broken.js")
        
        assert report.syntax_valid == False
        assert any("sin cerrar" in i.message or "no coincide" in i.message 
                  for i in report.syntax_issues)
    
    def test_unclosed_string(self, verifier):
        """Test unclosed string is detected"""
        code = """
const msg = "Hello world
console.log(msg);
"""
        report = verifier.verify(code, "test.js")
        
        assert report.syntax_valid == False


class TestHTMLValidation:
    """Tests for HTML code validation"""
    
    @pytest.fixture
    def verifier(self):
        return OutputVerifier()
    
    def test_valid_html(self, verifier, sample_html_code):
        """Test valid HTML passes validation"""
        report = verifier.verify(sample_html_code, "index.html")
        
        assert report.language == "html"
    
    def test_missing_doctype(self, verifier):
        """Test missing DOCTYPE warning"""
        code = "<html><body><h1>Hello</h1></body></html>"
        report = verifier.verify(code, "test.html")
        
        assert any("DOCTYPE" in i.message for i in report.syntax_issues)
    
    def test_unclosed_tags(self, verifier):
        """Test unclosed tags are detected"""
        code = """<!DOCTYPE html>
<html>
<body>
    <div>
        <p>Hello
    </div>
</body>
</html>"""
        report = verifier.verify(code, "test.html")
        
        assert any("sin cerrar" in i.message or "no coincide" in i.message 
                  for i in report.syntax_issues)


class TestCSSValidation:
    """Tests for CSS code validation"""
    
    @pytest.fixture
    def verifier(self):
        return OutputVerifier()
    
    def test_valid_css(self, verifier, sample_css_code):
        """Test valid CSS passes validation"""
        report = verifier.verify(sample_css_code, "styles.css")
        
        assert report.syntax_valid == True
    
    def test_unbalanced_braces(self, verifier):
        """Test unbalanced braces are detected"""
        code = """
body {
    color: red;

.container {
    padding: 10px;
}
"""
        report = verifier.verify(code, "styles.css")
        
        assert report.syntax_valid == False


class TestJSONValidation:
    """Tests for JSON validation"""
    
    @pytest.fixture
    def verifier(self):
        return OutputVerifier()
    
    def test_valid_json(self, verifier, sample_json_code):
        """Test valid JSON passes validation"""
        report = verifier.verify(sample_json_code, "config.json")
        
        assert report.syntax_valid == True
    
    def test_invalid_json(self, verifier, sample_invalid_json):
        """Test invalid JSON is detected"""
        report = verifier.verify(sample_invalid_json, "broken.json")
        
        assert report.syntax_valid == False


class TestCompletenessScore:
    """Tests for code completeness scoring"""
    
    @pytest.fixture
    def verifier(self):
        return OutputVerifier()
    
    def test_complete_code_high_score(self, verifier, sample_python_code):
        """Test complete code gets high completeness score"""
        report = verifier.verify(sample_python_code, "app.py")
        
        assert report.completeness_score >= 80
    
    def test_incomplete_code_low_score(self, verifier, sample_incomplete_code):
        """Test incomplete code gets low completeness score"""
        report = verifier.verify(sample_incomplete_code, "incomplete.py")
        
        assert report.completeness_score < 80
    
    def test_todo_reduces_score(self, verifier):
        """Test TODO comments reduce completeness"""
        code = """
def process():
    # TODO: implement this
    pass
"""
        report = verifier.verify(code, "test.py")
        
        assert report.completeness_score < 100


class TestQualityMetrics:
    """Tests for code quality metrics"""
    
    @pytest.fixture
    def verifier(self):
        return OutputVerifier()
    
    def test_quality_metrics_generated(self, verifier, sample_python_code):
        """Test quality metrics are generated"""
        report = verifier.verify(sample_python_code, "app.py")
        
        assert len(report.quality_metrics) > 0
        assert report.quality_score >= 0
        assert report.quality_score <= 100
    
    def test_documentation_metric(self, verifier):
        """Test documentation metric exists"""
        code = '''
# Main module
def hello():
    """Say hello"""
    pass
'''
        report = verifier.verify(code, "test.py")
        
        metric_names = [m.name for m in report.quality_metrics]
        assert "Documentación" in metric_names
    
    def test_format_metric(self, verifier):
        """Test format metric exists"""
        report = verifier.verify("def test(): pass", "test.py")
        
        metric_names = [m.name for m in report.quality_metrics]
        assert "Formato" in metric_names


class TestVerificationReport:
    """Tests for VerificationReport"""
    
    @pytest.fixture
    def verifier(self):
        return OutputVerifier()
    
    def test_report_to_dict(self, verifier, sample_python_code):
        """Test report serialization"""
        report = verifier.verify(sample_python_code, "app.py")
        report_dict = report.to_dict()
        
        assert "is_valid" in report_dict
        assert "language" in report_dict
        assert "syntax_valid" in report_dict
        assert "quality_score" in report_dict
        assert "suggestions" in report_dict
    
    def test_report_is_valid_flag(self, verifier, sample_python_code):
        """Test is_valid flag for valid code"""
        report = verifier.verify(sample_python_code, "app.py")
        
        assert report.is_valid == True
    
    def test_report_invalid_for_broken_code(self, verifier, sample_invalid_python):
        """Test is_valid is False for broken code"""
        report = verifier.verify(sample_invalid_python, "broken.py")
        
        assert report.is_valid == False
    
    def test_code_stats_generated(self, verifier, sample_python_code):
        """Test code statistics are generated"""
        report = verifier.verify(sample_python_code, "app.py")
        
        assert "code_stats" in report.to_dict()
        assert isinstance(report.code_stats, dict)


class TestSuggestions:
    """Tests for improvement suggestions"""
    
    @pytest.fixture
    def verifier(self):
        return OutputVerifier()
    
    def test_suggestions_generated(self, verifier):
        """Test suggestions are generated"""
        code = """
def very_long_function_that_does_many_things_and_has_a_very_long_name_that_should_be_split():
    x=1
    y=2
    return x+y
"""
        report = verifier.verify(code, "test.py")
        
        assert isinstance(report.suggestions, list)


class TestDataclasses:
    """Tests for dataclass serialization"""
    
    def test_syntax_issue_to_dict(self):
        """Test SyntaxIssue serialization"""
        issue = SyntaxIssue(
            line=10,
            column=5,
            message="Test error",
            severity="error",
            code="print("
        )
        
        issue_dict = issue.to_dict()
        
        assert issue_dict["line"] == 10
        assert issue_dict["message"] == "Test error"
    
    def test_import_issue_to_dict(self):
        """Test ImportIssue serialization"""
        issue = ImportIssue(
            module="custom_lib",
            issue_type="non_standard",
            suggestion="Add to requirements.txt"
        )
        
        issue_dict = issue.to_dict()
        
        assert issue_dict["module"] == "custom_lib"
    
    def test_quality_metric_to_dict(self):
        """Test QualityMetric serialization"""
        metric = QualityMetric(
            name="Test",
            score=80,
            max_score=100,
            details="Good"
        )
        
        metric_dict = metric.to_dict()
        
        assert metric_dict["score"] == 80
