"""
Prompt Sections — Define structured injection sections for future LLM prompts.

IMPORTANT: This module does NOT write final prompts or call OpenAI.
It defines the STRUCTURE and ORDERING of semantic sections that future
prompt builders will inject into LLM context windows.
"""

# ═══════════════════════════════════════════════════════════════
# SECTION DEFINITIONS
# ═══════════════════════════════════════════════════════════════

SECTIONS = {
    "identity": {
        "order": 1,
        "label": "Core Identity",
        "description": "Who this person fundamentally IS in symbolic terms",
        "max_tokens": 80,
        "always_include": True,
    },
    "behavioral_core": {
        "order": 2,
        "label": "Behavioral Operating System",
        "description": "How they lead, take risks, and generate wealth",
        "max_tokens": 120,
        "always_include": True,
    },
    "lifecycle_state": {
        "order": 3,
        "label": "Current Life Phase",
        "description": "Where they are in their lifecycle arc",
        "max_tokens": 60,
        "always_include": True,
    },
    "active_conflicts": {
        "order": 4,
        "label": "Active Symbolic Conflicts",
        "description": "Internal contradictions and suppressed energies",
        "max_tokens": 80,
        "always_include": False,
    },
    "causal_narratives": {
        "order": 5,
        "label": "Causal Explanations",
        "description": "Why things are happening the way they are",
        "max_tokens": 100,
        "always_include": False,
    },
    "opportunity_vectors": {
        "order": 6,
        "label": "Opportunity Vectors",
        "description": "Amplified energies and expansion indicators",
        "max_tokens": 60,
        "always_include": False,
    },
    "suppression_vectors": {
        "order": 7,
        "label": "Suppression Vectors",
        "description": "Blocked or dormant energies",
        "max_tokens": 60,
        "always_include": False,
    },
    "risk_vectors": {
        "order": 8,
        "label": "Risk Vectors",
        "description": "Failure modes and collapse tendencies",
        "max_tokens": 60,
        "always_include": False,
    },
}


def get_section_order() -> list:
    """Get sections in injection order."""
    return sorted(SECTIONS.keys(), key=lambda k: SECTIONS[k]["order"])


def get_required_sections() -> list:
    """Get sections that must always be included."""
    return [k for k, v in SECTIONS.items() if v["always_include"]]


def get_optional_sections() -> list:
    """Get sections that can be pruned for token savings."""
    return [k for k, v in SECTIONS.items() if not v["always_include"]]


def compute_section_budget(total_budget: int) -> dict:
    """
    Allocate token budget across sections proportionally.

    Required sections get their full allocation first.
    Remaining budget is distributed to optional sections.
    """
    required = get_required_sections()
    optional = get_optional_sections()

    # Required sections get their max_tokens (capped at budget)
    required_total = sum(SECTIONS[s]["max_tokens"] for s in required)
    remaining = total_budget - required_total

    allocation = {}
    for s in required:
        allocation[s] = SECTIONS[s]["max_tokens"]

    # Distribute remaining to optional sections proportionally
    if remaining > 0 and optional:
        optional_total = sum(SECTIONS[s]["max_tokens"] for s in optional)
        for s in optional:
            share = SECTIONS[s]["max_tokens"] / max(optional_total, 1)
            allocation[s] = min(SECTIONS[s]["max_tokens"], int(remaining * share))
    else:
        for s in optional:
            allocation[s] = 0

    return allocation


def build_section_manifest(routed_payload: dict, budget: int) -> list:
    """
    Build an ordered manifest of sections to inject, with their content and token allocation.

    Returns list of {section, label, content, allocated_tokens, included}
    """
    allocation = compute_section_budget(budget)
    order = get_section_order()
    manifest = []

    section_content_map = {
        "identity": routed_payload.get("identity", {}),
        "behavioral_core": routed_payload.get("behavioral_core", {}),
        "lifecycle_state": routed_payload.get("lifecycle", {}),
        "active_conflicts": routed_payload.get("primary_conflicts", []),
        "causal_narratives": routed_payload.get("top_narratives", []),
        "opportunity_vectors": routed_payload.get("amplification_vectors", []),
        "suppression_vectors": routed_payload.get("suppression_vectors", []),
        "risk_vectors": routed_payload.get("risk_vectors", []),
    }

    for section in order:
        content = section_content_map.get(section, {})
        allocated = allocation.get(section, 0)
        included = allocated > 0 and bool(content)

        manifest.append({
            "section": section,
            "label": SECTIONS[section]["label"],
            "content": content if included else None,
            "allocated_tokens": allocated,
            "included": included,
        })

    return manifest
