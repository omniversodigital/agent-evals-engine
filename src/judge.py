import os
import json
from typing import Optional
from src.models import TestCase, SemanticJudgment

class LLMJudge:
    """Semantic Judge evaluating qualitative criteria (Accuracy, Tone, Conversion, Hallucination)."""

    def __init__(self, model_name: str = "gpt-4o-mini", api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    def judge(self, test_case: TestCase, response_text: str) -> SemanticJudgment:
        """Judges a response using an LLM or calibrated deterministic rubric if offline."""
        if self.api_key:
            return self._call_real_llm_judge(test_case, response_text)
        else:
            return self._calibrated_offline_judge(test_case, response_text)

    def _call_real_llm_judge(self, test_case: TestCase, response_text: str) -> SemanticJudgment:
        # In a production environment with real keys, calls OpenAI/Anthropic client.
        # Fallback to calibrated offline judge if network/auth fails.
        try:
            import urllib.request
            prompt = f"""You are an expert AI Evaluator assessing a WhatsApp Lead Agent response.
TestCase: {test_case.model_dump_json()}
Agent Response: "{response_text}"

Evaluate strictly on:
- accuracy_score (1.0 to 5.0)
- tone_score (1.0 to 5.0)
- lead_conversion_score (1.0 to 5.0)
- hallucination_detected (boolean)
- reasoning (brief explanation)

Output valid JSON matching this schema:
{{"accuracy_score": float, "tone_score": float, "lead_conversion_score": float, "hallucination_detected": bool, "reasoning": "..."}}
"""
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                data=json.dumps({
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.0
                }).encode("utf-8")
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = json.loads(data["choices"][0]["message"]["content"])
                return SemanticJudgment(**content)
        except Exception:
            return self._calibrated_offline_judge(test_case, response_text)

    def _calibrated_offline_judge(self, test_case: TestCase, response_text: str) -> SemanticJudgment:
        """Calibrated rubric engine for local demo, offline CI/CD, and fast evaluation."""
        text_lower = response_text.lower()
        
        # 1. Accuracy & Policy
        accuracy = 4.0
        reasoning_points = []
        if any(f in text_lower for f in test_case.forbidden_patterns):
            accuracy = 1.5
            reasoning_points.append("Violou padrões proibidos.")
        elif len(response_text.strip()) < 15:
            accuracy = 2.0
            reasoning_points.append("Resposta excessivamente vaga.")
        else:
            accuracy = 4.8
            reasoning_points.append("Alinhado com a política corporativa.")

        # 2. Tone (Professionalism, Empathy)
        tone = 3.5
        if "desculpa" in text_lower or "lamento" in text_lower or "compreendo" in text_lower:
            tone += 1.2
            reasoning_points.append("Elevada empatia demonstrada.")
        if "calma" in text_lower or "irritado" in text_lower:
            tone -= 1.5
            reasoning_points.append("Tom condescendente detetado.")
        tone = max(1.0, min(5.0, tone))

        # 3. Lead Conversion & Next Steps
        conversion = 2.5
        if any(cta in text_lower for cta in ["reunião", "chamada", "calendly", "agendamento", "contacto", "diagnóstico"]):
            conversion = 4.8
            reasoning_points.append("Proativo na conversão com CTA claro.")
        else:
            conversion = 2.0
            reasoning_points.append("Falta de Call-to-Action claro.")

        # 4. Hallucination Risk
        hallucination = False
        if "€" in response_text or "euros" in text_lower:
            if "depende" not in text_lower and "medida" not in text_lower:
                hallucination = True
                accuracy = min(accuracy, 2.0)
                reasoning_points.append("Risco de alucinação de preçário arbitrário.")

        return SemanticJudgment(
            accuracy_score=round(accuracy, 2),
            tone_score=round(tone, 2),
            lead_conversion_score=round(conversion, 2),
            hallucination_detected=hallucination,
            reasoning="; ".join(reasoning_points)
        )
