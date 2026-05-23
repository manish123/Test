"""
Domain Registry — Central dispatcher for domain interpretation profiles.
"""

AVAILABLE_DOMAINS = [
    "trading",
    "career",
    "relationship",
    "health",
    "spirituality",
    "general_life",
    "business",
]


def get_domain_interpreter(domain_name):
    """
    Get the interpreter module for a specific domain.

    Args:
        domain_name: one of AVAILABLE_DOMAINS

    Returns:
        module with interpret(symbolic_state) function

    Raises:
        ValueError if domain not found
    """
    domain_name = (domain_name or "general_life").lower().strip()

    if domain_name not in AVAILABLE_DOMAINS:
        raise ValueError(f"Unknown domain: '{domain_name}'. Available: {AVAILABLE_DOMAINS}")

    if domain_name == "trading":
        from rules.domains.trading import interpreter
    elif domain_name == "career":
        from rules.domains.career import interpreter
    elif domain_name == "relationship":
        from rules.domains.relationship import interpreter
    elif domain_name == "health":
        from rules.domains.health import interpreter
    elif domain_name == "spirituality":
        from rules.domains.spirituality import interpreter
    elif domain_name == "business":
        from rules.domains.business import interpreter
    elif domain_name == "general_life":
        from rules.domains.general_life import interpreter
    else:
        from rules.domains.general_life import interpreter

    return interpreter
