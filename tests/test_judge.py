import pytest
from src.models import TestCase, SemanticJudgment
from src.judge import LLMJudge

def test_judge_calibrated_offline_scoring():
    judge = LLMJudge()
    tc = TestCase(
        id="TC-J1",
        category="pricing",
        lead_message="quanto custa?",
        expected_behavior="Resposta profissional com diagnóstico",
        forbidden_patterns=["50 euros"],
        required_topics=["orçamento", "reunião"],
        max_acceptable_tokens=100
    )

    # 1. Compliant response
    resp_good = "Analisamos cada projeto à medida numa reunião de diagnóstico para avaliar as necessidades."
    result_good = judge.judge(tc, resp_good)
    assert isinstance(result_good, SemanticJudgment)
    assert result_good.accuracy_score >= 4.0
    assert result_good.lead_conversion_score >= 4.0
    assert result_good.hallucination_detected is False

    # 2. Response with forbidden pattern
    resp_bad = "Olá, custa apenas 50 euros."
    result_bad = judge.judge(tc, resp_bad)
    assert result_bad.accuracy_score <= 2.0
    assert "Violou padrões proibidos" in result_bad.reasoning

def test_judge_hallucination_detection():
    judge = LLMJudge()
    tc = TestCase(
        id="TC-J2",
        category="general",
        lead_message="Qual é o valor?",
        expected_behavior="Preço sob consulta",
        max_acceptable_tokens=100
    )
    # Arbitrary pricing without scope
    resp_hallucinating = "O preço fixo do nosso serviço é 500 € por mês."
    result = judge.judge(tc, resp_hallucinating)
    assert result.hallucination_detected is True
    assert "alucinação" in result.reasoning.lower()
