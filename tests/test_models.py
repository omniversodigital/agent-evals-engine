import pytest
from src.models import TestCase, SemanticJudgment

def test_models_validation():
    tc = TestCase(
        id="TC-99",
        category="general",
        lead_message="Olá",
        expected_behavior="Cumprimentar",
        max_acceptable_tokens=50
    )
    assert tc.id == "TC-99"

    # Semantic judgment boundaries
    sj = SemanticJudgment(
        accuracy_score=4.5,
        tone_score=5.0,
        lead_conversion_score=4.0,
        hallucination_detected=False,
        reasoning="Bom desempenho"
    )
    assert sj.accuracy_score == 4.5
