from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TestCase(BaseModel):
    __test__ = False
    id: str
    category: str
    lead_message: str
    expected_behavior: str
    forbidden_patterns: List[str] = Field(default_factory=list)
    required_topics: List[str] = Field(default_factory=list)
    max_acceptable_tokens: int = 150

class DeterministicMetrics(BaseModel):
    guardrail_passed: bool
    forbidden_violations: List[str] = Field(default_factory=list)
    required_topics_covered: List[str] = Field(default_factory=list)
    required_topics_coverage_rate: float
    token_limit_passed: bool
    estimated_tokens: int
    latency_ms: float

class SemanticJudgment(BaseModel):
    accuracy_score: float = Field(ge=1.0, le=5.0, description="1 to 5 scale on factual/policy alignment")
    tone_score: float = Field(ge=1.0, le=5.0, description="1 to 5 scale on empathy and professional demeanor")
    lead_conversion_score: float = Field(ge=1.0, le=5.0, description="1 to 5 scale on proactive CTA / meeting qualification")
    hallucination_detected: bool = False
    reasoning: str

class EvalCaseResult(BaseModel):
    test_case_id: str
    prompt_version: str
    lead_message: str
    agent_response: str
    deterministic: DeterministicMetrics
    semantic: SemanticJudgment
    composite_score: float

class RunSummary(BaseModel):
    prompt_version: str
    total_cases: int
    guardrail_pass_rate: float
    avg_composite_score: float
    avg_accuracy: float
    avg_tone: float
    avg_conversion: float
    avg_latency_ms: float
    case_results: List[EvalCaseResult]

class ComparisonReport(BaseModel):
    baseline_version: str
    challenger_version: str
    baseline_score: float
    challenger_score: float
    score_delta: float
    improvements_count: int
    regressions_count: int
    is_safe_to_deploy: bool
    deployment_recommendation: str
    summary_markdown: str
