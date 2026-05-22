"""
Immutable intermediate contracts between pipeline layers.

These dataclasses define the explicit inputs and outputs of each layer.
No layer should produce or consume raw dicts — only typed Result objects.

Dependency rule:
    astronomy → produces AstronomyResult
    features  → consumes AstronomyResult, produces FeatureResult
    rules/symbolic → consumes FeatureResult, produces SymbolicResult
    rules/domains  → consumes SymbolicResult, produces DomainResult (per domain)
    decisions → consumes RuleResult, produces DecisionResult
"""

from contracts.astronomy_result import AstronomyResult
from contracts.feature_result import FeatureResult
from contracts.symbolic_result import SymbolicResult
from contracts.rule_result import RuleResult
from contracts.decision_result import DecisionResult

__all__ = [
    "AstronomyResult",
    "FeatureResult",
    "SymbolicResult",
    "RuleResult",
    "DecisionResult",
]
