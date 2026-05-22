"""
Layer C2 — Domain Interpretation Profiles

Same symbolic state → different meaning depending on life domain.

Each domain has its own:
- interpret() function: takes symbolic_state → domain-specific reading
- risk weighting: what counts as "dangerous" differs per domain
- opportunity detection: what counts as "favorable" differs per domain
- action vocabulary: trading says "AVOID", spirituality says "GO DEEPER"

Available domains:
- trading/       — capital preservation, execution timing, directional bias
- career/        — professional growth, authority, achievement
- relationship/  — partnerships, emotional bonds, family
- health/        — physical vitality, recovery, longevity
- spirituality/  — inner growth, detachment, awakening
- general_life/  — balanced multi-domain overview

Usage:
    from rules.domains import get_domain_interpreter
    interpreter = get_domain_interpreter("trading")
    reading = interpreter.interpret(symbolic_state)
"""

from rules.domains.registry import get_domain_interpreter, AVAILABLE_DOMAINS

__all__ = ["get_domain_interpreter", "AVAILABLE_DOMAINS"]
