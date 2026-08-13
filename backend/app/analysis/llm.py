from typing import Protocol

from app.analysis.contracts import RawFinding


class ReasoningProvider(Protocol):
    def enrich(self, finding: RawFinding) -> RawFinding: ...


class DeterministicReasoner:
    """Safe local default. Swap this with a provider that returns validated JSON."""

    def enrich(self, finding: RawFinding) -> RawFinding:
        return finding


def get_reasoner() -> ReasoningProvider:
    return DeterministicReasoner()

