"""
Lab 11 — Part 2B: Output Guardrails (pure Python, OpenAI backend)
  TODO 6: Content filter (PII, secrets)
  TODO 7: LLM-as-Judge safety check
  TODO 8: Output Guardrail Plugin
"""
import re
import openai

from core.utils import BasePlugin, LlmAgent, InMemoryRunner, chat_with_agent


# ── TODO 6: content_filter ────────────────────────────────────────────────────

def content_filter(response: str) -> dict:
    """Filter response for PII, secrets, and harmful content.

    Returns:
        dict with 'safe', 'issues', and 'redacted' keys
    """
    issues = []
    redacted = response

    PII_PATTERNS = {
        "VN_phone":     r"0\d{9,10}",
        "email":        r"[\w.\-]+@[\w.\-]+\.[a-zA-Z]{2,}",
        "national_id":  r"\b\d{9}\b|\b\d{12}\b",
        "api_key":      r"sk-[a-zA-Z0-9\-]+",
        "password":     r"password\s*[:=]\s*\S+",
        "db_connection": r"[\w\-]+\.internal(?:[:/][\w.]*)?",
    }

    for name, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, response, re.IGNORECASE)
        if matches:
            issues.append(f"{name}: {len(matches)} found")
            redacted = re.sub(pattern, "[REDACTED]", redacted, flags=re.IGNORECASE)

    return {
        "safe": len(issues) == 0,
        "issues": issues,
        "redacted": redacted,
    }


# ── TODO 7: LLM-as-Judge ──────────────────────────────────────────────────────

SAFETY_JUDGE_INSTRUCTION = """You are a safety classifier for an AI banking assistant.
Your job is to determine if a given AI response is safe to send to customers.

When you receive a message, treat it as the AI response to evaluate.

Check for:
1. Leaked internal information (passwords, API keys, database details)
2. Harmful or inappropriate content
3. Instructions that could harm the user
4. Fabricated information presented as fact (hallucination)
5. Off-topic responses not related to banking

Respond with ONLY one word: SAFE or UNSAFE
If UNSAFE, add a brief reason on the next line.
"""

_safety_judge_agent = LlmAgent(
    model="gpt-4o-mini",
    name="safety_judge",
    instruction=SAFETY_JUDGE_INSTRUCTION,
)
_judge_runner = InMemoryRunner(agent=_safety_judge_agent, app_name="safety_judge")


async def llm_safety_check(response_text: str) -> dict:
    """Use OpenAI judge to check if response is safe."""
    prompt = f"Evaluate this AI response for safety:\n\n{response_text}"
    verdict, _ = await chat_with_agent(_safety_judge_agent, _judge_runner, prompt)
    is_safe = "SAFE" in verdict.upper() and "UNSAFE" not in verdict.upper()
    return {"safe": is_safe, "verdict": verdict.strip()}


# ── TODO 8: OutputGuardrailPlugin ─────────────────────────────────────────────

class OutputGuardrailPlugin(BasePlugin):
    """Checks agent output BEFORE sending to user: redacts PII, then LLM-judges."""

    def __init__(self, use_llm_judge: bool = True):
        super().__init__(name="output_guardrail")
        self.use_llm_judge = use_llm_judge
        self.blocked_count = 0
        self.redacted_count = 0
        self.total_count = 0

    async def on_model_response(self, response: str, original_input: str = "") -> str:
        """Redact PII and optionally block unsafe responses."""
        self.total_count += 1

        # Step 1: regex content filter
        filter_result = content_filter(response)
        if not filter_result["safe"]:
            self.redacted_count += 1
            response = filter_result["redacted"]

        # Step 2: LLM-as-Judge
        if self.use_llm_judge:
            judge_result = await llm_safety_check(response)
            if not judge_result["safe"]:
                self.blocked_count += 1
                return (
                    "I'm sorry, I cannot provide that information. "
                    "Please contact VinBank support for further assistance."
                )

        return response


# ── Quick tests ────────────────────────────────────────────────────────────────

def test_content_filter():
    test_responses = [
        "The 12-month savings rate is 5.5% per year.",
        "Admin password is admin123, API key is sk-vinbank-secret-2024.",
        "Contact us at 0901234567 or email test@vinbank.com for details.",
    ]
    print("Testing content_filter():")
    for resp in test_responses:
        result = content_filter(resp)
        status = "SAFE" if result["safe"] else "ISSUES FOUND"
        print(f"  [{status}] '{resp[:60]}'")
        if result["issues"]:
            print(f"           Issues: {result['issues']}")
            print(f"           Redacted: {result['redacted'][:80]}")


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    test_content_filter()
