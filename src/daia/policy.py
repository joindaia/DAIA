"""Pure, fail-closed promotion logic. Agreement is not a probability of truth."""
from dataclasses import dataclass
from collections import Counter
from typing import Literal
from .crypto import digest

Mode = Literal["reproduce", "adversarial", "specification"]

@dataclass(frozen=True)
class Policy:
    version: str = "demo-factor-v1"
    modes: tuple[str, ...] = ("reproduce", "adversarial")
    min_roots: int = 2
    human_gate: bool = False

    def __post_init__(self):
        allowed = {"reproduce", "adversarial", "specification"}
        if (not self.modes or len(self.modes) > 8
                or any(m not in allowed for m in self.modes)
                or not 1 <= self.min_roots <= len(self.modes)):
            raise ValueError("Invalid verification policy")

    def document(self):
        return {"version": self.version, "modes": list(self.modes),
                "min_roots": self.min_roots, "human_gate": self.human_gate,
                "machine_check_required": True}

    @property
    def hash(self):
        return digest(self.document())


def evaluate(policy: Policy, machine_check: bool | None, reviews: list[dict]) -> str:
    """Input must be authenticated, assignment-bound, deduplicated attestations.

    FAIL means disputed (not a proven disproof); deterministic failure rejects.
    Missing modes, inconclusive results, or insufficient roots never promote.
    """
    if machine_check is False:
        return "rejected"
    if any(r["verdict"] == "fail" for r in reviews):
        return "disputed"
    if machine_check is not True:
        return "in_review"
    passes = [r for r in reviews if r["verdict"] == "pass"]
    roots = [r["root_id"] for r in passes]
    if len(roots) != len(set(roots)):
        return "in_review"
    required, received = Counter(policy.modes), Counter(r["mode"] for r in passes)
    if len(set(roots)) < policy.min_roots or any(received[m] < n for m, n in required.items()):
        return "in_review"
    return "ready_for_maintainer" if policy.human_gate else "promoted"
