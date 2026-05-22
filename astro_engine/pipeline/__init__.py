"""
Pipeline Orchestration Layer

Each pipeline stage receives explicit inputs and produces structured output.
Only this layer can see everything. Individual layers never import each other upward.

Flow:
    AstronomyResult = run_astronomy(date, birth_data, location)
    FeatureResult   = run_features(astronomy_result, birth_data, date)
    rule_output     = run_rules(feature_result, birth_data, date, config)
    decision        = run_decisions(rule_output, config)
"""

from pipeline.astronomy_pipeline import run_astronomy
from pipeline.feature_pipeline import run_features
from pipeline.rule_pipeline import run_rules
from pipeline.decision_pipeline import run_decisions

__all__ = ["run_astronomy", "run_features", "run_rules", "run_decisions"]
