"""
Phase 4 Architecture Audit Tests

Locks the consistency findings from the Phase 4 audit:
- EVENT_MAP ↔ EVENT_FAMILY sync
- EVENT_MAP_V3 internal consistency
- Domain registry completeness
- No stale constants in domain interpreters

Run with:
    pytest astro_engine/tests/test_architecture_audit.py -q
"""

import sys
import os
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ═══════════════════════════════════════════════════════════════
# TEST 1: EVENT_MAP ↔ EVENT_FAMILY governance sync
# ═══════════════════════════════════════════════════════════════

class TestEventGovernanceSync:
    """Every scored event must have a governance family mapping."""

    @pytest.fixture
    def event_map(self):
        from rules.event_engine import EVENT_MAP
        return EVENT_MAP

    @pytest.fixture
    def event_family(self):
        from rules.governance import EVENT_FAMILY
        return EVENT_FAMILY

    def test_all_event_map_keys_in_family(self, event_map, event_family):
        missing = set(event_map.keys()) - set(event_family.keys())
        assert missing == set(), f"Events in EVENT_MAP but not EVENT_FAMILY: {missing}"

    def test_no_orphan_family_entries(self, event_map, event_family):
        extra = set(event_family.keys()) - set(event_map.keys())
        assert extra == set(), f"Events in EVENT_FAMILY but not EVENT_MAP: {extra}"

    def test_event_counts_match(self, event_map, event_family):
        assert len(event_map) == len(event_family)

    def test_all_families_are_valid(self, event_family):
        valid_families = {
            "wealth", "profession", "lifecycle", "risk", "sensitive",
            "wellbeing", "development", "family", "mobility",
            "relationship", "behavior",
        }
        actual_families = set(event_family.values())
        invalid = actual_families - valid_families
        assert invalid == set(), f"Unknown family values: {invalid}"


# ═══════════════════════════════════════════════════════════════
# TEST 2: EVENT_MAP_V3 internal consistency
# ═══════════════════════════════════════════════════════════════

class TestEventOntologyConsistency:
    """EVENT_MAP_V3 must be internally consistent."""

    def test_event_count(self):
        from rules.event_ontology import EVENT_MAP_V3
        assert len(EVENT_MAP_V3) == 104

    def test_all_events_have_valid_domains(self):
        from rules.event_ontology import EVENT_MAP_V3, DOMAINS
        for e in EVENT_MAP_V3:
            for d in e.domains:
                assert d in DOMAINS, f"{e.event_id} has invalid domain '{d}'"

    def test_all_events_have_valid_categories(self):
        from rules.event_ontology import EVENT_MAP_V3, CATEGORIES
        for e in EVENT_MAP_V3:
            assert e.category in CATEGORIES, f"{e.event_id} has invalid category '{e.category}'"

    def test_all_events_have_houses(self):
        from rules.event_ontology import EVENT_MAP_V3
        for e in EVENT_MAP_V3:
            assert len(e.houses) > 0, f"{e.event_id} has no houses"
            for h in e.houses:
                assert 1 <= h <= 12, f"{e.event_id} has invalid house {h}"

    def test_all_events_have_significators(self):
        from rules.event_ontology import EVENT_MAP_V3
        valid_planets = {"Sun", "Moon", "Mars", "Mercury", "Jupiter",
                        "Venus", "Saturn", "Rahu", "Ketu"}
        for e in EVENT_MAP_V3:
            assert len(e.planetary_significators) > 0, f"{e.event_id} has no significators"
            for p in e.planetary_significators:
                assert p in valid_planets, f"{e.event_id} has invalid planet '{p}'"

    def test_all_events_have_valid_polarity(self):
        from rules.event_ontology import EVENT_MAP_V3
        valid = {"positive", "negative", "mixed", "neutral"}
        for e in EVENT_MAP_V3:
            assert e.polarity in valid, f"{e.event_id} has invalid polarity '{e.polarity}'"

    def test_unique_event_ids(self):
        from rules.event_ontology import EVENT_MAP_V3
        ids = [e.event_id for e in EVENT_MAP_V3]
        assert len(ids) == len(set(ids)), "Duplicate event_ids found"

    def test_event_index_matches_list(self):
        from rules.event_ontology import EVENT_MAP_V3, EVENT_INDEX
        assert len(EVENT_INDEX) == len(EVENT_MAP_V3)
        for e in EVENT_MAP_V3:
            assert e.event_id in EVENT_INDEX
            assert EVENT_INDEX[e.event_id] is e


# ═══════════════════════════════════════════════════════════════
# TEST 3: V1 ↔ V3 overlap consistency
# ═══════════════════════════════════════════════════════════════

class TestV1V3Overlap:
    """The 5 events shared between V1 and V3 must have consistent data."""

    def test_overlapping_events_house_match(self):
        from rules.event_engine import EVENT_MAP
        from rules.event_ontology import EVENT_INDEX

        v1_keys = set(EVENT_MAP.keys())
        v3_ids = set(EVENT_INDEX.keys())
        overlap = v1_keys & v3_ids

        for eid in overlap:
            v1_houses = set(EVENT_MAP[eid]["houses"])
            v3_houses = set(EVENT_INDEX[eid].houses)
            assert v1_houses == v3_houses, (
                f"{eid}: V1 houses {v1_houses} != V3 houses {v3_houses}"
            )

    def test_overlapping_events_planet_match(self):
        from rules.event_engine import EVENT_MAP
        from rules.event_ontology import EVENT_INDEX

        v1_keys = set(EVENT_MAP.keys())
        v3_ids = set(EVENT_INDEX.keys())
        overlap = v1_keys & v3_ids

        for eid in overlap:
            v1_planets = set(EVENT_MAP[eid]["planets"])
            v3_planets = set(EVENT_INDEX[eid].planetary_significators)
            assert v1_planets == v3_planets, (
                f"{eid}: V1 planets {v1_planets} != V3 planets {v3_planets}"
            )


# ═══════════════════════════════════════════════════════════════
# TEST 4: Domain registry completeness
# ═══════════════════════════════════════════════════════════════

class TestDomainRegistry:
    """All ontology domains must be registered in the dispatcher."""

    def test_all_domains_in_registry(self):
        from rules.event_ontology import DOMAINS
        registry_path = Path(__file__).resolve().parent.parent / "rules" / "domains" / "registry.py"
        content = registry_path.read_text()
        for domain in DOMAINS:
            assert domain in content, f"Domain '{domain}' not found in registry.py"


# ═══════════════════════════════════════════════════════════════
# TEST 5: No stale constants in domain interpreters
# ═══════════════════════════════════════════════════════════════

class TestNoStaleInterpreterConstants:
    """Domain interpreter files must not redefine shared constants."""

    @pytest.fixture
    def interpreter_files(self):
        base = Path(__file__).resolve().parent.parent / "rules" / "domains"
        files = []
        for root, dirs, fnames in os.walk(base):
            for f in fnames:
                if f.endswith('.py') and f != '__init__.py':
                    files.append(os.path.join(root, f))
        return files

    @pytest.mark.parametrize("pattern,label", [
        ("IST_OFFSET = timedelta", "IST_OFFSET"),
        ("NATURAL_BENEFICS = {", "NATURAL_BENEFICS"),
        ("NATURAL_MALEFICS = {", "NATURAL_MALEFICS"),
        ("SIGN_NAMES = {", "SIGN_NAMES"),
        ("NAKSHATRA_LORDS = [", "NAKSHATRA_LORDS"),
        ("def ist_to_utc", "ist_to_utc"),
        ("def get_jd", "get_jd"),
    ])
    def test_no_stale_constant(self, interpreter_files, pattern, label):
        violations = []
        for fpath in interpreter_files:
            content = open(fpath).read()
            if pattern in content:
                rel = fpath.split("rules/domains/")[1]
                violations.append(rel)
        assert violations == [], f"{label} redefined in: {violations}"


# ═══════════════════════════════════════════════════════════════
# TEST 6: EVENT_MAP scoring structure
# ═══════════════════════════════════════════════════════════════

class TestEventMapStructure:
    """EVENT_MAP entries must have valid structure for scoring."""

    def test_all_events_have_houses(self):
        from rules.event_engine import EVENT_MAP
        for name, cfg in EVENT_MAP.items():
            assert "houses" in cfg, f"{name} missing 'houses'"
            assert len(cfg["houses"]) > 0, f"{name} has empty houses"

    def test_all_events_have_planets(self):
        from rules.event_engine import EVENT_MAP
        valid_planets = {"Sun", "Moon", "Mars", "Mercury", "Jupiter",
                        "Venus", "Saturn", "Rahu", "Ketu"}
        for name, cfg in EVENT_MAP.items():
            assert "planets" in cfg, f"{name} missing 'planets'"
            assert len(cfg["planets"]) > 0, f"{name} has empty planets"
            for p in cfg["planets"]:
                assert p in valid_planets, f"{name} has invalid planet '{p}'"

    def test_all_houses_valid_range(self):
        from rules.event_engine import EVENT_MAP
        for name, cfg in EVENT_MAP.items():
            for h in cfg["houses"]:
                assert 1 <= h <= 12, f"{name} has invalid house {h}"
