"""
Pipeline Orchestration Layer

Each pipeline stage receives explicit inputs and produces an immutable Result object.
Only this layer can see everything. Individual layers never import each other upward.

Flow:
    AstronomyResult = run_astronomy(date, birth_data, location)
    FeatureResult   = run_features(astronomy_result)
    RuleResult      = run_rules(feature_result, config)
    DecisionResult  = run_decisions(rule_result, config)
"""

from pipeline.astronomy_pipeline import run_astronomy
from pipeline.feature_pipeline import run_features
from pipeline.rule_pipeline import run_rules
from pipeline.decision_pipeline import run_decisions

__all__ = ["run_astronomy", "run_features", "run_rules", "run_decisions"]
