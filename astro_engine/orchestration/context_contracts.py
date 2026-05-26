"""
Context Contracts — Stable semantic payload schemas for each API consumer.

Each contract defines: required fields, optional fields, semantic priority,
token budget, and compression strategy.
"""

# ═══════════════════════════════════════════════════════════════
# CONTRACT DEFINITIONS
# ═══════════════════════════════════════════════════════════════

CONTRACTS = {
    "minimal_context": {
        "description": "Ultra-compact identity snapshot for token-constrained scenarios",
        "token_budget": 120,
        "required_fields": ["archetype", "phase", "planet", "direction", "conflicts"],
        "optional_fields": [],
        "semantic_priority": ["identity", "lifecycle"],
        "compression": "extreme",
    },
    "personality_context": {
        "description": "Full personality profile for Personality API",
        "token_budget": 600,
        "required_fields": [
            "identity.primary_archetype", "identity.secondary_archetype", "identity.fusion_type",
            "behavioral_core.leadership", "behavioral_core.risk", "behavioral_core.economic",
            "psychological_os.primary", "psychological_os.shadow",
            "lifecycle.phase", "lifecycle.stability",
        ],
        "optional_fields": [
            "primary_conflicts", "suppression_vectors", "amplification_vectors",
            "failure_modes", "modern_expression",
        ],
        "semantic_priority": ["identity", "behavioral_core", "psychological_os", "lifecycle"],
        "compression": "moderate",
    },
    "timing_context": {
        "description": "Lifecycle and timing intelligence for Timing API",
        "token_budget": 400,
        "required_fields": [
            "lifecycle.phase", "lifecycle.stability", "lifecycle.direction",
            "lifecycle.crisis_vectors", "lifecycle.probable_next_states",
            "coherence.score", "coherence.fragmentation",
        ],
        "optional_fields": [
            "primary_conflicts", "top_narratives",
            "expansion_indicators",
        ],
        "semantic_priority": ["lifecycle", "coherence", "conflicts", "narratives"],
        "compression": "moderate",
    },
    "career_context": {
        "description": "Career and economic intelligence for Career API",
        "token_budget": 500,
        "required_fields": [
            "identity.primary_archetype", "identity.fusion_type",
            "behavioral_core.leadership", "behavioral_core.economic",
            "economic_style.wealth_behavior",
            "lifecycle.phase", "lifecycle.direction",
        ],
        "optional_fields": [
            "scaling_style", "risk_signature", "failure_modes",
            "primary_conflicts", "top_narratives",
        ],
        "semantic_priority": ["identity", "economic_style", "leadership", "lifecycle"],
        "compression": "moderate",
    },
    "prediction_context": {
        "description": "Weekly/monthly prediction context for narrative generation",
        "token_budget": 250,
        "required_fields": [
            "identity.primary_archetype",
            "lifecycle.phase", "lifecycle.direction",
            "top_narratives",
            "primary_conflicts",
        ],
        "optional_fields": [
            "coherence.score", "crisis_vectors",
        ],
        "semantic_priority": ["narratives", "lifecycle", "conflicts", "identity"],
        "compression": "high",
    },
    "relationship_context": {
        "description": "Relationship and emotional intelligence for partnership analysis",
        "token_budget": 450,
        "required_fields": [
            "identity.primary_archetype",
            "behavioral_core.risk",
            "primary_conflicts",
            "suppression_vectors", "amplification_vectors",
            "lifecycle.phase",
        ],
        "optional_fields": [
            "psychological_os.shadow", "failure_modes",
            "partnership_style",
        ],
        "semantic_priority": ["conflicts", "suppression", "behavioral_core", "identity"],
        "compression": "moderate",
    },
    "full_symbolic_context": {
        "description": "Complete symbolic export for advanced orchestration",
        "token_budget": 1200,
        "required_fields": ["*"],  # All fields
        "optional_fields": [],
        "semantic_priority": ["identity", "behavioral_core", "lifecycle", "conflicts", "narratives", "coherence"],
        "compression": "minimal",
    },
}


def get_contract(contract_name: str) -> dict:
    """Get a specific contract by name."""
    return CONTRACTS.get(contract_name, CONTRACTS["minimal_context"])


def list_contracts() -> list:
    """List all available contract names."""
    return list(CONTRACTS.keys())


def get_token_budget(contract_name: str) -> int:
    """Get the token budget for a contract."""
    return CONTRACTS.get(contract_name, {}).get("token_budget", 100)
