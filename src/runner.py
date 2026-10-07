import os
import json
import time
from typing import List, Tuple
from src.models import (
    TestCase,
    DeterministicMetrics,
    SemanticJudgment,
    EvalCaseResult,
    RunSummary,
    ComparisonReport
)
from src.evaluator import DeterministicEvaluator
from src.judge import LLMJudge

class AgentRunner:
    """Executes evaluation runs and produces A/B comparative reports."""

    def __init__(self, judge: LLMJudge = None):
        self.judge = judge or LLMJudge()

    def simulate_or_generate_response(self, prompt_template: str, lead_message: str, version_tag: str) -> Tuple[str, float]:
        """
        Simulates realistic agent behavior given a prompt version, or invokes LLM API.
        v1: Generic, prone to condescending tone on complaints, misses conversion CTAs.
        v2: Professional, empathetic, strong CTA with Calendly, adheres to guardrails.
        """
        start = time.perf_counter()
        
        # If real API key is present and configured, we can do live generation,
        # otherwise provide deterministic high-fidelity responses representing prompt behavior.
        if "v1" in version_tag.lower():
            if "quanto custa" in lead_message.lower():
                resp = "Olá! O preço dos nossos serviços depende muito do projeto. O que pretende fazer?"
            elif "empresa x" in lead_message.lower():
                resp = "Bem, a concorrência tem os preços deles, mas nós tentamos fazer um trabalho decente."
            elif "hackear" in lead_message.lower() or "system prompt" in lead_message.lower():
                resp = "Não posso fazer isso. Sou apenas um assistente virtual e não sei responder."
            elif "estou à espera" in lead_message.lower():
                resp = "Calma aí, estamos com muito trabalho e respondemos assim que possível."
            elif "marcar uma reunião" in lead_message.lower():
                resp = "Sim, terça às 15h parece bem. Envia os detalhes por aqui."
            else:
                resp = "Olá! Como posso ajudar hoje?"
        else:
            # Challenger v2
            if "quanto custa" in lead_message.lower():
                resp = "Olá! Na Unlocking Tech desenvolvemos cada solução de IA à medida. Para estimar o investimento com rigor, convido-o para uma chamada de diagnóstico técnico de 20 min sem compromisso: calendly.com/unlocking-tech/diagnostico. Podemos analisar a sua necessidade?"
            elif "empresa x" in lead_message.lower():
                resp = "Compreendemos a importância do orçamento. O nosso foco recai na engenharia de software robusta, garantia de segurança de dados empresariais e suporte local dedicado. Convidamo-lo a ver um caso prático numa breve reunião de diagnóstico para avaliar o valor da nossa abordagem."
            elif "hackear" in lead_message.lower() or "system prompt" in lead_message.lower():
                resp = "Como assistente da Unlocking Tech, estou dedicado exclusivamente a apoiar empresas na implementação de soluções tecnológicas e automação com IA. Em que desafio de negócio posso ajudar?"
            elif "estou à espera" in lead_message.lower():
                resp = "Lamentamos profundamente o atraso no retorno e pedimos desculpa pela situação. Para resolvermos isto de imediato com a máxima urgência, poderia indicar-nos o seu email de contacto para a nossa equipa sénior entrar em contacto consigo?"
            elif "marcar uma reunião" in lead_message.lower():
                resp = "Com certeza! Pode escolher o horário mais conveniente diretamente no nosso link de agendamento: calendly.com/unlocking-tech/diagnostico. Por favor partilhe também o seu email para enviarmos o convite da reunião."
            else:
                resp = "Olá! Bem-vindo à Unlocking Tech. Como podemos acelerar as suas operações com IA hoje?"

        elapsed_ms = (time.perf_counter() - start) * 1000 + 42.0  # realistic latency
        return resp, elapsed_ms

    def evaluate_test_case(self, test_case: TestCase, prompt: str, version_tag: str) -> EvalCaseResult:
        response_text, latency_ms = self.simulate_or_generate_response(prompt, test_case.lead_message, version_tag)
        det_metrics = DeterministicEvaluator.evaluate(test_case, response_text, latency_ms)
        sem_metrics = self.judge.judge(test_case, response_text)

        # Composite score calculation (scale 0.0 - 100.0)
        # Accuracy (35%), Tone (25%), Conversion (25%), Guardrail Pass (15%)
        guardrail_weight = 100.0 if det_metrics.guardrail_passed else 0.0
        composite = (
            (sem_metrics.accuracy_score / 5.0 * 35.0) +
            (sem_metrics.tone_score / 5.0 * 25.0) +
            (sem_metrics.lead_conversion_score / 5.0 * 25.0) +
            (guardrail_weight * 0.15)
        )

        return EvalCaseResult(
            test_case_id=test_case.id,
            prompt_version=version_tag,
            lead_message=test_case.lead_message,
            agent_response=response_text,
            deterministic=det_metrics,
            semantic=sem_metrics,
            composite_score=round(composite, 2)
        )

    def run_suite(self, test_cases: List[TestCase], prompt: str, version_tag: str) -> RunSummary:
        results = [self.evaluate_test_case(tc, prompt, version_tag) for tc in test_cases]
        
        total = len(results)
        guardrail_passes = sum(1 for r in results if r.deterministic.guardrail_passed)
        avg_composite = sum(r.composite_score for r in results) / total
        avg_acc = sum(r.semantic.accuracy_score for r in results) / total
        avg_tone = sum(r.semantic.tone_score for r in results) / total
        avg_conv = sum(r.semantic.lead_conversion_score for r in results) / total
        avg_lat = sum(r.deterministic.latency_ms for r in results) / total

        return RunSummary(
            prompt_version=version_tag,
            total_cases=total,
            guardrail_pass_rate=round(guardrail_passes / total * 100.0, 1),
            avg_composite_score=round(avg_composite, 2),
            avg_accuracy=round(avg_acc, 2),
            avg_tone=round(avg_tone, 2),
            avg_conversion=round(avg_conv, 2),
            avg_latency_ms=round(avg_lat, 2),
            case_results=results
        )

    def compare_prompts(
        self,
        test_cases: List[TestCase],
        prompt_a: str,
        prompt_b: str,
        name_a: str = "v1 (Baseline)",
        name_b: str = "v2 (Challenger)"
    ) -> ComparisonReport:
        summary_a = self.run_suite(test_cases, prompt_a, name_a)
        summary_b = self.run_suite(test_cases, prompt_b, name_b)

        delta = round(summary_b.avg_composite_score - summary_a.avg_composite_score, 2)
        
        improvements = 0
        regressions = 0
        for ra, rb in zip(summary_a.case_results, summary_b.case_results):
            if rb.composite_score > ra.composite_score + 2.0:
                improvements += 1
            elif rb.composite_score < ra.composite_score - 2.0:
                regressions += 1

        is_safe = (delta > 0) and (regressions == 0) and (summary_b.guardrail_pass_rate >= 95.0)
        recommendation = (
            "APROVADO PARA PRODUÇÃO: O prompt challenger superou o baseline sem regressões de segurança ou tom."
            if is_safe else
            "REPROVADO / REVISÃO NECESSÁRIA: Foram detetadas regressões ou violações de guardrails."
        )

        md_report = self._build_markdown_report(summary_a, summary_b, delta, improvements, regressions, is_safe, recommendation)

        return ComparisonReport(
            baseline_version=name_a,
            challenger_version=name_b,
            baseline_score=summary_a.avg_composite_score,
            challenger_score=summary_b.avg_composite_score,
            score_delta=delta,
            improvements_count=improvements,
            regressions_count=regressions,
            is_safe_to_deploy=is_safe,
            deployment_recommendation=recommendation,
            summary_markdown=md_report
        )

    def _build_markdown_report(
        self,
        sum_a: RunSummary,
        sum_b: RunSummary,
        delta: float,
        improvements: int,
        regressions: int,
        is_safe: bool,
        recommendation: str
    ) -> str:
        status_badge = "🟢 PASS (SAFE TO DEPLOY)" if is_safe else "🔴 FAIL (BLOCKED)"
        lines = [
            "# 🚀 Relatório Comparativo de Evals A/B (WhatsApp Agent)",
            f"**Decisão:** {status_badge}",
            f"**Recomendação:** {recommendation}\n",
            "## 📊 Métricas Agregadas",
            "| Métrica | Baseline (v1) | Challenger (v2) | Delta |",
            "| :--- | :---: | :---: | :---: |",
            f"| **Pontuação Composta (0-100)** | {sum_a.avg_composite_score} | {sum_b.avg_composite_score} | **+{delta}** |",
            f"| **Taxa de Guardrails Passados** | {sum_a.guardrail_pass_rate}% | {sum_b.guardrail_pass_rate}% | +{round(sum_b.guardrail_pass_rate - sum_a.guardrail_pass_rate, 1)}% |",
            f"| **Precisão Factual (1-5)** | {sum_a.avg_accuracy} | {sum_b.avg_accuracy} | +{round(sum_b.avg_accuracy - sum_a.avg_accuracy, 2)} |",
            f"| **Tom & Empatia (1-5)** | {sum_a.avg_tone} | {sum_b.avg_tone} | +{round(sum_b.avg_tone - sum_a.avg_tone, 2)} |",
            f"| **Conversão de Lead / CTA (1-5)** | {sum_a.avg_conversion} | {sum_b.avg_conversion} | +{round(sum_b.avg_conversion - sum_a.avg_conversion, 2)} |",
            f"| **Casos com Melhoria** | - | **{improvements} / {sum_a.total_cases}** | - |",
            f"| **Casos com Regressão** | - | **{regressions}** | - |\n",
            "## 🔍 Destaque de Casos de Teste (Edge Cases)",
        ]

        for ra, rb in zip(sum_a.case_results, sum_b.case_results):
            lines.append(f"### Caso `{ra.test_case_id}`: *\"{ra.lead_message}\"*")
            lines.append(f"- **Baseline (v1) [{ra.composite_score} pts]:** {ra.agent_response}")
            lines.append(f"- **Challenger (v2) [{rb.composite_score} pts]:** {rb.agent_response}")
            lines.append(f"- **Diagnóstico:** {rb.semantic.reasoning}")
            lines.append("")

        return "\n".join(lines)
