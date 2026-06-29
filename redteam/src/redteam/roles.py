"""The standing committee. Each role is one parallel adversarial reviewer."""
from __future__ import annotations

ROLES: dict[str, str] = {
    "Legal": ("a senior contracts attorney. Hunt for unbounded liability, missing "
              "indemnity/limitation-of-liability, auto-renewal traps, IP assignment, "
              "governing-law and termination gaps."),
    "Risk": ("an enterprise risk officer. Hunt for SLA gaps, vague obligations, "
             "single points of failure, and uncapped commitments."),
    "Finance": ("a CFO's analyst. Hunt for hidden fees, price-escalation clauses, "
                "payment-term traps, and currency/tax exposure."),
    "Security & Privacy": ("a CISO. Hunt for data-handling, breach-notification, "
                           "sub-processor, retention, and compliance (GDPR/SOC2) gaps."),
}
