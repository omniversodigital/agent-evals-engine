import re
import time
from typing import List
from src.models import TestCase, DeterministicMetrics

class DeterministicEvaluator:
    """Evaluates rule-based, deterministic constraints without relying on LLMs."""

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Heuristic token estimator (average 4 chars per token)."""
        words = text.strip().split()
        return max(1, int(len(text) / 3.8))

    @classmethod
    def evaluate(cls, test_case: TestCase, response_text: str, latency_ms: float = 0.0) -> DeterministicMetrics:
        response_lower = response_text.lower()
        
        # 1. Check forbidden patterns
        violations = []
        for pattern in test_case.forbidden_patterns:
            if re.search(r'\b' + re.escape(pattern.lower()) + r'\b', response_lower):
                violations.append(pattern)
            elif pattern.lower() in response_lower:
                violations.append(pattern)
        
        guardrail_passed = len(violations) == 0

        # 2. Check required topics
        covered_topics = []
        for topic in test_case.required_topics:
            if topic.lower() in response_lower:
                covered_topics.append(topic)
                
        coverage_rate = (
            len(covered_topics) / len(test_case.required_topics)
            if test_case.required_topics else 1.0
        )

        # 3. Check token limits
        est_tokens = cls.estimate_tokens(response_text)
        token_passed = est_tokens <= test_case.max_acceptable_tokens

        return DeterministicMetrics(
            guardrail_passed=guardrail_passed,
            forbidden_violations=violations,
            required_topics_covered=covered_topics,
            required_topics_coverage_rate=round(coverage_rate, 2),
            token_limit_passed=token_passed,
            estimated_tokens=est_tokens,
            latency_ms=round(latency_ms, 2)
        )
