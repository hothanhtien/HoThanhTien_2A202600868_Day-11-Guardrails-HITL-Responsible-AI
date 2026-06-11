"""
Lab 11 — Part 4: Human-in-the-Loop Design
  TODO 12: Confidence Router
  TODO 13: Design 3 HITL decision points
"""
from dataclasses import dataclass


HIGH_RISK_ACTIONS = [
    "transfer_money",
    "close_account",
    "change_password",
    "delete_data",
    "update_personal_info",
]


@dataclass
class RoutingDecision:
    """Result of the confidence router."""
    action: str          # "auto_send", "queue_review", "escalate"
    confidence: float
    reason: str
    priority: str        # "low", "normal", "high"
    requires_human: bool


class ConfidenceRouter:
    """Route agent responses based on confidence and risk level.

    HIGH  (>= 0.9)  → auto_send       (human-on-the-loop)
    MEDIUM (0.7-0.9) → queue_review   (human-in-the-loop)
    LOW   (< 0.7)   → escalate        (human-as-tiebreaker)
    HIGH_RISK action → always escalate regardless of confidence
    """

    HIGH_THRESHOLD = 0.9
    MEDIUM_THRESHOLD = 0.7

    def route(self, response: str, confidence: float,
              action_type: str = "general") -> RoutingDecision:
        """Route a response based on confidence score and action type."""
        if action_type in HIGH_RISK_ACTIONS:
            return RoutingDecision(
                action="escalate",
                confidence=confidence,
                reason=f"High-risk action: {action_type}",
                priority="high",
                requires_human=True,
            )

        if confidence >= self.HIGH_THRESHOLD:
            return RoutingDecision(
                action="auto_send",
                confidence=confidence,
                reason="High confidence",
                priority="low",
                requires_human=False,
            )
        elif confidence >= self.MEDIUM_THRESHOLD:
            return RoutingDecision(
                action="queue_review",
                confidence=confidence,
                reason="Medium confidence — needs review",
                priority="normal",
                requires_human=True,
            )
        else:
            return RoutingDecision(
                action="escalate",
                confidence=confidence,
                reason="Low confidence — escalating",
                priority="high",
                requires_human=True,
            )


# ── TODO 13: 3 HITL decision points ──────────────────────────────────────────

hitl_decision_points = [
    {
        "id": 1,
        "name": "High-Value Transaction Approval",
        "trigger": (
            "Customer requests a money transfer or withdrawal exceeding 50,000,000 VND, "
            "or any transaction flagged by the fraud detection model with confidence < 0.85."
        ),
        "hitl_model": "human-in-the-loop",
        "context_needed": (
            "Customer account history (last 30 days), transaction amount and destination, "
            "current account balance, fraud score, customer identity verification status, "
            "and any prior escalations in this session."
        ),
        "example": (
            "A customer asks to transfer 200,000,000 VND to a new payee. "
            "The AI flags it as unusual (first transfer to this account, late night). "
            "A human agent must approve or deny before the transaction executes."
        ),
    },
    {
        "id": 2,
        "name": "Complaint & Dispute Escalation",
        "trigger": (
            "Customer expresses strong dissatisfaction (sentiment score < 0.3), "
            "uses legal threat keywords ('sue', 'lawyer', 'report to authorities'), "
            "or dispute involves a transaction error over 1,000,000 VND."
        ),
        "hitl_model": "human-on-the-loop",
        "context_needed": (
            "Full conversation transcript, disputed transaction details, "
            "customer tier (priority/VIP status), previous complaint history, "
            "and the AI's proposed resolution."
        ),
        "example": (
            "A customer claims they were charged twice for an ATM withdrawal "
            "and threatens to file a complaint with the State Bank of Vietnam. "
            "The AI drafts an apology and initiates a refund investigation; "
            "a human supervisor reviews and approves the response before it is sent."
        ),
    },
    {
        "id": 3,
        "name": "Account Security Change Verification",
        "trigger": (
            "Any request to change login credentials, linked phone number, registered email, "
            "beneficiary list, or account recovery options — regardless of AI confidence."
        ),
        "hitl_model": "human-in-the-loop",
        "context_needed": (
            "Customer identity verification result (OTP/biometric), device fingerprint, "
            "IP geolocation, time since last successful login, and the specific field being changed."
        ),
        "example": (
            "A customer asks to change their registered phone number to a new one. "
            "The AI cannot approve this autonomously — it routes the request to a "
            "human agent who verifies the customer's identity via a video call before "
            "making the change in the core banking system."
        ),
    },
]


# ── Quick tests ───────────────────────────────────────────────────────────────

def test_confidence_router():
    router = ConfidenceRouter()
    test_cases = [
        ("Balance inquiry", 0.95, "general"),
        ("Interest rate question", 0.82, "general"),
        ("Ambiguous request", 0.55, "general"),
        ("Transfer $50,000", 0.98, "transfer_money"),
        ("Close my account", 0.91, "close_account"),
    ]
    print("Testing ConfidenceRouter:")
    print("=" * 80)
    print(f"{'Scenario':<25} {'Conf':<6} {'Action Type':<18} {'Decision':<15} {'Priority':<10} {'Human?'}")
    print("-" * 80)
    for scenario, conf, action_type in test_cases:
        decision = router.route(scenario, conf, action_type)
        print(
            f"{scenario:<25} {conf:<6.2f} {action_type:<18} "
            f"{decision.action:<15} {decision.priority:<10} "
            f"{'Yes' if decision.requires_human else 'No'}"
        )
    print("=" * 80)


def test_hitl_points():
    print("\nHITL Decision Points:")
    print("=" * 60)
    for point in hitl_decision_points:
        print(f"\n  Decision Point #{point['id']}: {point['name']}")
        print(f"    Trigger:  {point['trigger'][:80]}...")
        print(f"    Model:    {point['hitl_model']}")
        print(f"    Context:  {point['context_needed'][:80]}...")
        print(f"    Example:  {point['example'][:80]}...")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_confidence_router()
    test_hitl_points()
