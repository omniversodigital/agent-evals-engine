import pytest
from src.models import TestCase
from src.runner import AgentRunner

def test_runner_a_b_comparison():
    test_cases = [
        TestCase(
            id="T1",
            category="pricing",
            lead_message="quanto custa?",
            expected_behavior="Pedir diagnóstico",
            forbidden_patterns=["50 euros"],
            required_topics=["diagnóstico", "chamada"],
            max_acceptable_tokens=150
        ),
        TestCase(
            id="T2",
            category="complaint",
            lead_message="estou à espera há 3 dias",
            expected_behavior="Empatia e desculpa",
            forbidden_patterns=["calma aí"],
            required_topics=["desculpa", "contacto"],
            max_acceptable_tokens=150
        )
    ]

    runner = AgentRunner()
    report = runner.compare_prompts(
        test_cases=test_cases,
        prompt_a="v1 prompt",
        prompt_b="v2 prompt",
        name_a="v1",
        name_b="v2"
    )

    assert report.baseline_score < report.challenger_score
    assert report.score_delta > 0
    assert report.improvements_count >= 1
    assert "APROVADO PARA PRODUÇÃO" in report.deployment_recommendation
