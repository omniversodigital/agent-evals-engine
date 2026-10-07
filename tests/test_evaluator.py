import pytest
from src.models import TestCase
from src.evaluator import DeterministicEvaluator

def test_forbidden_pattern_detection():
    tc = TestCase(
        id="T1",
        category="pricing",
        lead_message="Quanto custa?",
        expected_behavior="Resposta profissional",
        forbidden_patterns=["custa apenas 50 euros", "de graça"],
        required_topics=["orçamento", "reunião"],
        max_acceptable_tokens=100
    )
    
    # Violating text
    res = DeterministicEvaluator.evaluate(tc, "Olá, custa apenas 50 euros para si!")
    assert res.guardrail_passed is False
    assert "custa apenas 50 euros" in res.forbidden_violations

    # Compliant text
    res_ok = DeterministicEvaluator.evaluate(tc, "Olá, analisamos cada projeto à medida numa reunião de orçamento.")
    assert res_ok.guardrail_passed is True
    assert len(res_ok.forbidden_violations) == 0
    assert res_ok.required_topics_coverage_rate == 1.0

def test_token_limit_handling():
    tc = TestCase(
        id="T2",
        category="short",
        lead_message="Breve",
        expected_behavior="Curto",
        max_acceptable_tokens=10
    )
    long_text = "Esta é uma resposta extremamente longa e desnecessariamente prolixa para testar o limite de tokens permitidos neste caso de teste."
    res = DeterministicEvaluator.evaluate(tc, long_text)
    assert res.token_limit_passed is False
