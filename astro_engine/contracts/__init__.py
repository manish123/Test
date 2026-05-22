"""
Immutable intermediate contracts between pipeline layers.

These dataclasses define the explicit inputs and outputs of each layer.
No layer should produce or consume raw dicts — only typed Result objects.

Dependency rule:
    astronomy → produces AstronomyResult
    features  → consumes AstronomyResult, produces FeatureResult
    rules     → consumes FeatureResult, produces RuleResult
    decisions → consumes RuleResult, produces DecisionResult
"""

from contracts.astronomy_result import AstronomyResult
from contracts.feature_result import FeatureResult
from contracts.rule_result import RuleResult
from contracts.decision_result import DecisionResult

__all__ = [
    "AstronomyResult",
    "FeatureResult",
    "RuleResult",
    "DecisionResult",
]
