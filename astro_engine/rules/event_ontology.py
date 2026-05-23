"""
Event Ontology V3 — Full 104-event model with domain-aware schema.

Each event follows the schema from EVENT_ONTOLOGY.md:
- event_id: unique identifier
- title: human-readable name
- category: one of 6 major categories
- domains: list of domains that interpret this event
- houses: Vedic house associations (1-12)
- planetary_significators: planets that activate this event
- timing_triggers: what activates this event (dasha, transit, nakshatra, house_activation)
- polarity: positive / negative / mixed / neutral
- intensity_range: [min, max] on 1-10 scale
- repeatable: can this happen multiple times in life?
- life_stage_sensitive: does interpretation change with age?
- requires_confirmation: needs multiple factors to fire?

Events are NEUTRAL. Domains decide what they MEAN.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class Event:
    """Single event definition in the ontology."""
    event_id: str
    title: str
    category: str
    domains: List[str] = field(default_factory=list)
    houses: List[int] = field(default_factory=list)
    planetary_significators: List[str] = field(default_factory=list)
    timing_triggers: List[str] = field(default_factory=lambda: ["dasha", "transit"])
    polarity: str = "mixed"          # positive / negative / mixed / neutral
    intensity_range: List[int] = field(default_factory=lambda: [3, 7])
    repeatable: bool = True
    life_stage_sensitive: bool = False
    requires_confirmation: bool = True



# ═══════════════════════════════════════════════════════════════
# CATEGORIES
# ═══════════════════════════════════════════════════════════════

CATEGORIES = {
    "career_enterprise": "A. Career & Enterprise",
    "relationships_family": "B. Relationships & Family",
    "health_wellbeing": "C. Health & Wellbeing",
    "spiritual_learning": "D. Spiritual & Learning",
    "life_shifts_assets": "E. Life Shifts & Assets",
    "trading_market": "F. Trading & Market Operations",
}

DOMAINS = ["trading", "career", "relationship", "health", "spirituality", "general_life"]


# ═══════════════════════════════════════════════════════════════
# A. CAREER & ENTERPRISE (24 events)
# ═══════════════════════════════════════════════════════════════

_CAREER_ENTERPRISE = [
    # Role Transitions
    Event("job_entry", "Job Entry", "career_enterprise",
          domains=["career", "general_life"],
          houses=[6, 10], planetary_significators=["Saturn", "Mercury", "Sun"],
          polarity="positive", intensity_range=[4, 7], life_stage_sensitive=True),
    Event("job_switch_lateral", "Lateral Job Switch", "career_enterprise",
          domains=["career", "general_life"],
          houses=[3, 6, 10], planetary_significators=["Mercury", "Rahu", "Saturn"],
          polarity="mixed", intensity_range=[3, 6]),
    Event("job_switch_promotion", "Promotion", "career_enterprise",
          domains=["career", "general_life", "trading"],
          houses=[10, 11], planetary_significators=["Sun", "Jupiter", "Saturn"],
          polarity="positive", intensity_range=[5, 9]),
    Event("job_switch_demotion", "Demotion / Role Reduction", "career_enterprise",
          domains=["career", "general_life"],
          houses=[6, 8, 12], planetary_significators=["Saturn", "Ketu", "Sun"],
          polarity="negative", intensity_range=[4, 8]),
    Event("sector_change", "Sector / Industry Change", "career_enterprise",
          domains=["career", "general_life"],
          houses=[3, 9, 10], planetary_significators=["Rahu", "Mercury", "Jupiter"],
          polarity="mixed", intensity_range=[4, 7]),
    Event("voluntary_exit", "Voluntary Exit / Resignation", "career_enterprise",
          domains=["career", "general_life"],
          houses=[4, 12], planetary_significators=["Ketu", "Moon", "Saturn"],
          polarity="mixed", intensity_range=[3, 7]),
    Event("involuntary_loss", "Job Loss / Termination", "career_enterprise",
          domains=["career", "general_life", "trading"],
          houses=[6, 8, 12], planetary_significators=["Saturn", "Rahu", "Mars"],
          polarity="negative", intensity_range=[6, 10]),

    Event("retirement", "Retirement", "career_enterprise",
          domains=["career", "general_life", "spirituality"],
          houses=[4, 8, 12], planetary_significators=["Saturn", "Sun", "Ketu"],
          polarity="mixed", intensity_range=[5, 8], life_stage_sensitive=True),
    # Enterprise Ventures
    Event("business_start", "Business Start", "career_enterprise",
          domains=["career", "general_life", "trading"],
          houses=[7, 10, 11], planetary_significators=["Mercury", "Jupiter", "Mars"],
          polarity="positive", intensity_range=[5, 9]),
    Event("business_launch", "Business Launch / Product Launch", "career_enterprise",
          domains=["career", "trading"],
          houses=[10, 11], planetary_significators=["Mercury", "Sun", "Mars"],
          polarity="positive", intensity_range=[5, 9]),
    Event("partnership_formed", "Business Partnership Formed", "career_enterprise",
          domains=["career", "relationship", "general_life"],
          houses=[7, 10, 11], planetary_significators=["Venus", "Mercury", "Jupiter"],
          polarity="positive", intensity_range=[4, 8]),
    Event("business_expansion", "Business Expansion", "career_enterprise",
          domains=["career", "trading", "general_life"],
          houses=[9, 10, 11], planetary_significators=["Jupiter", "Mercury", "Sun"],
          polarity="positive", intensity_range=[5, 9]),
    Event("business_pivot", "Business Pivot / Restructuring", "career_enterprise",
          domains=["career", "trading"],
          houses=[8, 10], planetary_significators=["Rahu", "Saturn", "Mercury"],
          polarity="mixed", intensity_range=[4, 8]),
    Event("business_closure", "Business Closure", "career_enterprise",
          domains=["career", "trading", "general_life"],
          houses=[8, 12], planetary_significators=["Saturn", "Ketu", "Rahu"],
          polarity="negative", intensity_range=[6, 10]),
    Event("merger_acquisition", "Merger / Acquisition", "career_enterprise",
          domains=["career", "trading"],
          houses=[7, 8, 11], planetary_significators=["Rahu", "Jupiter", "Saturn"],
          polarity="mixed", intensity_range=[5, 9]),
    Event("business_exit", "Business Exit / Sale", "career_enterprise",
          domains=["career", "trading", "general_life"],
          houses=[7, 11, 12], planetary_significators=["Saturn", "Mercury", "Ketu"],
          polarity="mixed", intensity_range=[4, 8]),

    # Growth & Authority
    Event("promotion", "Promotion / Advancement", "career_enterprise",
          domains=["career", "general_life"],
          houses=[10, 11], planetary_significators=["Sun", "Jupiter", "Saturn"],
          polarity="positive", intensity_range=[5, 9]),
    Event("responsibility_escalation", "Responsibility Escalation", "career_enterprise",
          domains=["career"],
          houses=[6, 10], planetary_significators=["Saturn", "Sun", "Mars"],
          polarity="mixed", intensity_range=[3, 7]),
    Event("leadership_role", "Leadership Role", "career_enterprise",
          domains=["career", "general_life"],
          houses=[1, 9, 10], planetary_significators=["Sun", "Jupiter", "Mars"],
          polarity="positive", intensity_range=[6, 9]),
    Event("team_building", "Team Building / Management", "career_enterprise",
          domains=["career"],
          houses=[3, 7, 10], planetary_significators=["Mercury", "Moon", "Sun"],
          polarity="positive", intensity_range=[3, 6]),
    Event("project_ownership", "Project Ownership", "career_enterprise",
          domains=["career"],
          houses=[5, 10], planetary_significators=["Sun", "Mercury", "Mars"],
          polarity="positive", intensity_range=[4, 7]),
    Event("certification_completion", "Certification / Training Complete", "career_enterprise",
          domains=["career", "spirituality"],
          houses=[4, 5, 9], planetary_significators=["Mercury", "Jupiter", "Moon"],
          polarity="positive", intensity_range=[3, 6]),
    Event("recognition_award", "Recognition / Award", "career_enterprise",
          domains=["career", "general_life"],
          houses=[9, 10, 11], planetary_significators=["Sun", "Jupiter", "Venus"],
          polarity="positive", intensity_range=[5, 9]),
    Event("skill_mastery", "Skill Mastery", "career_enterprise",
          domains=["career", "spirituality"],
          houses=[4, 5], planetary_significators=["Mercury", "Jupiter", "Saturn"],
          polarity="positive", intensity_range=[4, 7]),
]



# ═══════════════════════════════════════════════════════════════
# B. RELATIONSHIPS & FAMILY (16 events)
# ═══════════════════════════════════════════════════════════════

_RELATIONSHIPS_FAMILY = [
    # Partnership Events
    Event("meeting_significant_person", "Meeting Significant Person", "relationships_family",
          domains=["relationship", "general_life"],
          houses=[5, 7, 11], planetary_significators=["Venus", "Jupiter", "Moon"],
          polarity="positive", intensity_range=[4, 8]),
    Event("commitment_deepens", "Commitment Deepens", "relationships_family",
          domains=["relationship", "general_life"],
          houses=[2, 7], planetary_significators=["Venus", "Jupiter", "Saturn"],
          polarity="positive", intensity_range=[4, 7]),
    Event("marriage_union", "Marriage / Union", "relationships_family",
          domains=["relationship", "general_life"],
          houses=[2, 7, 11], planetary_significators=["Venus", "Jupiter", "Moon"],
          polarity="positive", intensity_range=[7, 10], life_stage_sensitive=True),
    Event("cohabitation", "Cohabitation / Living Together", "relationships_family",
          domains=["relationship", "general_life"],
          houses=[4, 7], planetary_significators=["Moon", "Venus", "Mercury"],
          polarity="positive", intensity_range=[3, 6]),
    Event("trust_breach", "Trust Breach / Betrayal", "relationships_family",
          domains=["relationship", "general_life"],
          houses=[6, 7, 8], planetary_significators=["Rahu", "Saturn", "Mars"],
          polarity="negative", intensity_range=[5, 9]),
    Event("separation_divorce", "Separation / Divorce", "relationships_family",
          domains=["relationship", "general_life"],
          houses=[6, 7, 8, 12], planetary_significators=["Saturn", "Mars", "Rahu"],
          polarity="negative", intensity_range=[7, 10]),
    Event("reconciliation", "Reconciliation", "relationships_family",
          domains=["relationship", "general_life"],
          houses=[4, 7, 11], planetary_significators=["Venus", "Jupiter", "Moon"],
          polarity="positive", intensity_range=[4, 8]),
    Event("relationship_renewal", "Relationship Renewal", "relationships_family",
          domains=["relationship"],
          houses=[5, 7, 9], planetary_significators=["Venus", "Jupiter", "Sun"],
          polarity="positive", intensity_range=[4, 7]),
    # Family Events
    Event("pregnancy_awareness", "Pregnancy Awareness", "relationships_family",
          domains=["relationship", "health", "general_life"],
          houses=[2, 5], planetary_significators=["Jupiter", "Moon", "Venus"],
          polarity="positive", intensity_range=[6, 9], life_stage_sensitive=True),
    Event("childbirth", "Childbirth", "relationships_family",
          domains=["relationship", "health", "general_life"],
          houses=[2, 5, 11], planetary_significators=["Jupiter", "Venus", "Moon"],
          polarity="positive", intensity_range=[8, 10], life_stage_sensitive=True),
    Event("first_child", "First Child", "relationships_family",
          domains=["relationship", "general_life"],
          houses=[5, 9], planetary_significators=["Jupiter", "Sun", "Venus"],
          polarity="positive", intensity_range=[8, 10], life_stage_sensitive=True, repeatable=False),
    Event("child_milestone", "Child Milestone", "relationships_family",
          domains=["relationship", "general_life"],
          houses=[5, 9, 11], planetary_significators=["Jupiter", "Mercury", "Moon"],
          polarity="positive", intensity_range=[3, 6]),
    Event("sibling_event", "Sibling Event", "relationships_family",
          domains=["relationship", "general_life"],
          houses=[3, 11], planetary_significators=["Mars", "Mercury", "Moon"],
          polarity="mixed", intensity_range=[3, 6]),
    Event("parent_health_event", "Parent Health Event", "relationships_family",
          domains=["relationship", "health", "general_life"],
          houses=[4, 8, 9], planetary_significators=["Saturn", "Sun", "Moon"],
          polarity="negative", intensity_range=[5, 9]),
    Event("parent_loss", "Parent Loss", "relationships_family",
          domains=["relationship", "general_life", "spirituality"],
          houses=[4, 8, 9], planetary_significators=["Saturn", "Sun", "Ketu"],
          polarity="negative", intensity_range=[8, 10], life_stage_sensitive=True),
    Event("grandchild_arrival", "Grandchild Arrival", "relationships_family",
          domains=["relationship", "general_life"],
          houses=[5, 9, 11], planetary_significators=["Jupiter", "Moon", "Sun"],
          polarity="positive", intensity_range=[5, 8], life_stage_sensitive=True),
]



# ═══════════════════════════════════════════════════════════════
# C. HEALTH & WELLBEING (16 events)
# ═══════════════════════════════════════════════════════════════

_HEALTH_WELLBEING = [
    # Physical Health
    Event("injury_accident", "Injury / Accident", "health_wellbeing",
          domains=["health", "general_life"],
          houses=[6, 8, 12], planetary_significators=["Mars", "Saturn", "Rahu"],
          polarity="negative", intensity_range=[5, 10]),
    Event("surgery_procedure", "Surgery / Medical Procedure", "health_wellbeing",
          domains=["health", "general_life"],
          houses=[6, 8], planetary_significators=["Mars", "Saturn", "Ketu"],
          polarity="negative", intensity_range=[5, 9]),
    Event("illness_onset", "Illness Onset", "health_wellbeing",
          domains=["health", "general_life"],
          houses=[1, 6, 8], planetary_significators=["Saturn", "Sun", "Mars"],
          polarity="negative", intensity_range=[4, 8]),
    Event("chronic_diagnosis", "Chronic Condition Diagnosis", "health_wellbeing",
          domains=["health", "general_life"],
          houses=[6, 8, 12], planetary_significators=["Saturn", "Rahu", "Ketu"],
          polarity="negative", intensity_range=[6, 10], repeatable=False),
    Event("recovery_period", "Recovery Period", "health_wellbeing",
          domains=["health", "general_life", "spirituality"],
          houses=[1, 5, 9], planetary_significators=["Jupiter", "Sun", "Moon"],
          polarity="positive", intensity_range=[4, 7]),
    Event("hospitalization", "Hospitalization", "health_wellbeing",
          domains=["health", "general_life"],
          houses=[6, 8, 12], planetary_significators=["Saturn", "Ketu", "Moon"],
          polarity="negative", intensity_range=[6, 9]),
    Event("medication_change", "Medication / Treatment Change", "health_wellbeing",
          domains=["health"],
          houses=[6, 8], planetary_significators=["Mercury", "Saturn", "Ketu"],
          polarity="neutral", intensity_range=[2, 5]),
    Event("vitality_surge", "Vitality Surge", "health_wellbeing",
          domains=["health", "general_life", "career"],
          houses=[1, 5, 11], planetary_significators=["Sun", "Mars", "Jupiter"],
          polarity="positive", intensity_range=[5, 8]),
    # Mental & Behavioral
    Event("stress_burnout", "Stress / Burnout", "health_wellbeing",
          domains=["health", "career", "general_life"],
          houses=[6, 8, 12], planetary_significators=["Saturn", "Moon", "Rahu"],
          polarity="negative", intensity_range=[4, 8]),
    Event("anxiety_episode", "Anxiety Episode", "health_wellbeing",
          domains=["health", "general_life"],
          houses=[4, 6, 8], planetary_significators=["Moon", "Mercury", "Rahu"],
          polarity="negative", intensity_range=[3, 7]),
    Event("depression_onset", "Depression Onset", "health_wellbeing",
          domains=["health", "general_life", "spirituality"],
          houses=[4, 8, 12], planetary_significators=["Saturn", "Moon", "Ketu"],
          polarity="negative", intensity_range=[5, 9]),
    Event("addiction_cycle", "Addiction Cycle", "health_wellbeing",
          domains=["health", "general_life"],
          houses=[6, 8, 12], planetary_significators=["Rahu", "Moon", "Venus"],
          polarity="negative", intensity_range=[5, 9]),
    Event("therapy_counseling", "Therapy / Counseling", "health_wellbeing",
          domains=["health", "relationship", "spirituality"],
          houses=[5, 9, 12], planetary_significators=["Jupiter", "Moon", "Mercury"],
          polarity="positive", intensity_range=[3, 6]),
    Event("habit_breaking", "Habit Breaking / Discipline", "health_wellbeing",
          domains=["health", "spirituality"],
          houses=[1, 6, 10], planetary_significators=["Saturn", "Mars", "Sun"],
          polarity="positive", intensity_range=[4, 7]),
    Event("confidence_shift", "Confidence Shift", "health_wellbeing",
          domains=["health", "career", "general_life"],
          houses=[1, 5, 10], planetary_significators=["Sun", "Jupiter", "Mars"],
          polarity="mixed", intensity_range=[3, 7]),
    Event("sleep_disruption", "Sleep Disruption", "health_wellbeing",
          domains=["health"],
          houses=[4, 8, 12], planetary_significators=["Moon", "Rahu", "Saturn"],
          polarity="negative", intensity_range=[3, 6]),
]



# ═══════════════════════════════════════════════════════════════
# D. SPIRITUAL & LEARNING (15 events)
# ═══════════════════════════════════════════════════════════════

_SPIRITUAL_LEARNING = [
    # Practice & Study
    Event("meditation_begins", "Meditation Practice Begins", "spiritual_learning",
          domains=["spirituality", "health"],
          houses=[9, 12], planetary_significators=["Ketu", "Jupiter", "Moon"],
          polarity="positive", intensity_range=[3, 6]),
    Event("vedic_study_starts", "Vedic / Scriptural Study", "spiritual_learning",
          domains=["spirituality", "general_life"],
          houses=[4, 5, 9], planetary_significators=["Jupiter", "Mercury", "Ketu"],
          polarity="positive", intensity_range=[3, 6]),
    Event("formal_training", "Formal Training / Course", "spiritual_learning",
          domains=["spirituality", "career"],
          houses=[4, 5, 9], planetary_significators=["Mercury", "Jupiter", "Moon"],
          polarity="positive", intensity_range=[3, 7]),
    Event("retreat_intensive", "Retreat / Intensive Practice", "spiritual_learning",
          domains=["spirituality", "health"],
          houses=[9, 12], planetary_significators=["Ketu", "Jupiter", "Saturn"],
          polarity="positive", intensity_range=[5, 8]),
    Event("teacher_meeting", "Teacher / Guru Meeting", "spiritual_learning",
          domains=["spirituality", "general_life"],
          houses=[5, 9], planetary_significators=["Jupiter", "Sun", "Ketu"],
          polarity="positive", intensity_range=[5, 9]),
    Event("discipline_period", "Discipline / Tapas Period", "spiritual_learning",
          domains=["spirituality", "health"],
          houses=[6, 9, 12], planetary_significators=["Saturn", "Ketu", "Sun"],
          polarity="mixed", intensity_range=[4, 8]),
    Event("sadhana_shift", "Sadhana / Practice Shift", "spiritual_learning",
          domains=["spirituality"],
          houses=[9, 12], planetary_significators=["Ketu", "Moon", "Jupiter"],
          polarity="neutral", intensity_range=[3, 6]),
    Event("study_completion", "Study / Training Completion", "spiritual_learning",
          domains=["spirituality", "career", "general_life"],
          houses=[4, 5, 9, 11], planetary_significators=["Mercury", "Jupiter", "Sun"],
          polarity="positive", intensity_range=[4, 7]),
    # Insight & Realization
    Event("breakthrough_realization", "Breakthrough Realization", "spiritual_learning",
          domains=["spirituality", "general_life"],
          houses=[5, 9, 12], planetary_significators=["Jupiter", "Ketu", "Sun"],
          polarity="positive", intensity_range=[6, 10]),
    Event("belief_shift", "Belief Shift", "spiritual_learning",
          domains=["spirituality", "general_life"],
          houses=[5, 9, 12], planetary_significators=["Jupiter", "Ketu", "Moon"],
          polarity="mixed", intensity_range=[4, 8]),
    Event("perspective_change", "Perspective Change", "spiritual_learning",
          domains=["spirituality", "general_life", "career"],
          houses=[3, 9], planetary_significators=["Mercury", "Jupiter", "Rahu"],
          polarity="mixed", intensity_range=[3, 7]),
    Event("purpose_clarity", "Purpose Clarity", "spiritual_learning",
          domains=["spirituality", "career", "general_life"],
          houses=[1, 9, 10], planetary_significators=["Sun", "Jupiter", "Saturn"],
          polarity="positive", intensity_range=[5, 9]),
    Event("release_surrender", "Release / Surrender", "spiritual_learning",
          domains=["spirituality", "health"],
          houses=[8, 12], planetary_significators=["Ketu", "Saturn", "Moon"],
          polarity="mixed", intensity_range=[5, 9]),
    Event("cosmic_alignment", "Cosmic Alignment Feeling", "spiritual_learning",
          domains=["spirituality"],
          houses=[1, 5, 9], planetary_significators=["Jupiter", "Sun", "Moon"],
          polarity="positive", intensity_range=[6, 10]),
    Event("identity_dissolution", "Identity Dissolution", "spiritual_learning",
          domains=["spirituality"],
          houses=[1, 8, 12], planetary_significators=["Ketu", "Saturn", "Rahu"],
          polarity="mixed", intensity_range=[7, 10]),
]



# ═══════════════════════════════════════════════════════════════
# E. LIFE SHIFTS & ASSETS (21 events)
# ═══════════════════════════════════════════════════════════════

_LIFE_SHIFTS_ASSETS = [
    # Property & Assets
    Event("home_purchase", "Home Purchase", "life_shifts_assets",
          domains=["general_life", "career"],
          houses=[4, 11], planetary_significators=["Mars", "Venus", "Moon"],
          polarity="positive", intensity_range=[5, 8]),
    Event("property_sale", "Property Sale", "life_shifts_assets",
          domains=["general_life", "trading"],
          houses=[4, 12], planetary_significators=["Saturn", "Mercury", "Mars"],
          polarity="mixed", intensity_range=[4, 7]),
    Event("ancestral_property", "Ancestral Property", "life_shifts_assets",
          domains=["general_life", "relationship"],
          houses=[4, 8, 9], planetary_significators=["Saturn", "Jupiter", "Moon"],
          polarity="mixed", intensity_range=[4, 8]),
    Event("inheritance", "Inheritance", "life_shifts_assets",
          domains=["general_life", "trading"],
          houses=[2, 8, 11], planetary_significators=["Jupiter", "Saturn", "Ketu"],
          polarity="positive", intensity_range=[5, 9]),
    Event("asset_acquisition", "Asset Acquisition", "life_shifts_assets",
          domains=["general_life", "trading", "career"],
          houses=[2, 4, 11], planetary_significators=["Venus", "Jupiter", "Mercury"],
          polarity="positive", intensity_range=[4, 7]),
    Event("asset_loss", "Asset Loss", "life_shifts_assets",
          domains=["general_life", "trading"],
          houses=[2, 8, 12], planetary_significators=["Saturn", "Rahu", "Ketu"],
          polarity="negative", intensity_range=[5, 9]),
    Event("property_legal_dispute", "Property Legal Dispute", "life_shifts_assets",
          domains=["general_life", "career"],
          houses=[4, 6, 7], planetary_significators=["Mars", "Saturn", "Rahu"],
          polarity="negative", intensity_range=[5, 8]),
    # Movement & Travel
    Event("relocation_move", "Relocation / Move", "life_shifts_assets",
          domains=["general_life", "career"],
          houses=[3, 4, 12], planetary_significators=["Moon", "Mercury", "Rahu"],
          polarity="mixed", intensity_range=[4, 7]),
    Event("city_change", "City Change", "life_shifts_assets",
          domains=["general_life", "career"],
          houses=[3, 9, 12], planetary_significators=["Rahu", "Mercury", "Moon"],
          polarity="mixed", intensity_range=[5, 8]),
    Event("country_change", "Country Change / Immigration", "life_shifts_assets",
          domains=["general_life", "career"],
          houses=[9, 12], planetary_significators=["Rahu", "Saturn", "Jupiter"],
          polarity="mixed", intensity_range=[7, 10]),
    Event("long_journey", "Long Journey", "life_shifts_assets",
          domains=["general_life", "spirituality"],
          houses=[3, 9, 12], planetary_significators=["Mercury", "Rahu", "Moon"],
          polarity="positive", intensity_range=[3, 6]),
    Event("visa_permit", "Visa / Permit", "life_shifts_assets",
          domains=["general_life", "career"],
          houses=[9, 10, 11], planetary_significators=["Sun", "Rahu", "Saturn"],
          polarity="positive", intensity_range=[4, 7]),
    Event("immigration", "Immigration Completion", "life_shifts_assets",
          domains=["general_life", "career"],
          houses=[9, 10, 11, 12], planetary_significators=["Rahu", "Saturn", "Sun"],
          polarity="positive", intensity_range=[7, 10], repeatable=False),
    Event("homecoming", "Homecoming / Return", "life_shifts_assets",
          domains=["general_life", "relationship"],
          houses=[4, 9], planetary_significators=["Moon", "Jupiter", "Venus"],
          polarity="positive", intensity_range=[3, 6]),
    # Financial & Legal
    Event("debt_incurred", "Debt Incurred", "life_shifts_assets",
          domains=["general_life", "trading"],
          houses=[6, 8, 12], planetary_significators=["Saturn", "Rahu", "Mars"],
          polarity="negative", intensity_range=[4, 8]),
    Event("debt_cleared", "Debt Cleared", "life_shifts_assets",
          domains=["general_life", "trading"],
          houses=[6, 11], planetary_significators=["Jupiter", "Saturn", "Sun"],
          polarity="positive", intensity_range=[4, 7]),
    Event("bankruptcy", "Bankruptcy", "life_shifts_assets",
          domains=["general_life", "trading", "career"],
          houses=[2, 8, 12], planetary_significators=["Saturn", "Rahu", "Ketu"],
          polarity="negative", intensity_range=[8, 10]),
    Event("lawsuit_litigation", "Lawsuit / Litigation", "life_shifts_assets",
          domains=["general_life", "career"],
          houses=[6, 7, 8], planetary_significators=["Mars", "Saturn", "Rahu"],
          polarity="negative", intensity_range=[5, 9]),
    Event("criminal_charge", "Criminal Charge", "life_shifts_assets",
          domains=["general_life"],
          houses=[6, 8, 12], planetary_significators=["Saturn", "Mars", "Rahu"],
          polarity="negative", intensity_range=[7, 10]),
    Event("windfall_bonus", "Windfall / Bonus", "life_shifts_assets",
          domains=["general_life", "trading", "career"],
          houses=[2, 5, 8, 11], planetary_significators=["Jupiter", "Venus", "Rahu"],
          polarity="positive", intensity_range=[5, 9]),
    Event("tax_event", "Tax Event", "life_shifts_assets",
          domains=["general_life", "trading"],
          houses=[6, 8, 11], planetary_significators=["Saturn", "Mercury", "Rahu"],
          polarity="mixed", intensity_range=[3, 6]),
]



# ═══════════════════════════════════════════════════════════════
# F. TRADING & MARKET OPERATIONS (12 events)
# ═══════════════════════════════════════════════════════════════

_TRADING_MARKET = [
    # Execution States
    Event("high_conviction_window", "High Conviction Window", "trading_market",
          domains=["trading"],
          houses=[2, 10, 11], planetary_significators=["Jupiter", "Mercury", "Sun"],
          polarity="positive", intensity_range=[6, 10]),
    Event("capital_preservation_phase", "Capital Preservation Phase", "trading_market",
          domains=["trading"],
          houses=[4, 8, 12], planetary_significators=["Saturn", "Ketu", "Moon"],
          polarity="negative", intensity_range=[5, 8]),
    Event("high_volatility_phase", "High Volatility Phase", "trading_market",
          domains=["trading"],
          houses=[3, 6, 8], planetary_significators=["Mars", "Rahu", "Mercury"],
          polarity="mixed", intensity_range=[5, 9]),
    Event("whipsaw_risk", "Whipsaw Risk", "trading_market",
          domains=["trading"],
          houses=[6, 8], planetary_significators=["Rahu", "Mars", "Mercury"],
          polarity="negative", intensity_range=[5, 9]),
    Event("overtrading_risk", "Overtrading Risk", "trading_market",
          domains=["trading"],
          houses=[3, 5, 8], planetary_significators=["Mars", "Rahu", "Moon"],
          polarity="negative", intensity_range=[4, 7]),
    Event("execution_block", "Execution Block", "trading_market",
          domains=["trading"],
          houses=[6, 8, 12], planetary_significators=["Saturn", "Ketu", "Rahu"],
          polarity="negative", intensity_range=[6, 9]),
    # Portfolio States
    Event("expansion_phase", "Expansion Phase", "trading_market",
          domains=["trading", "career"],
          houses=[9, 10, 11], planetary_significators=["Jupiter", "Sun", "Mercury"],
          polarity="positive", intensity_range=[5, 9]),
    Event("risk_off_phase", "Risk-Off Phase", "trading_market",
          domains=["trading"],
          houses=[4, 8, 12], planetary_significators=["Saturn", "Moon", "Ketu"],
          polarity="negative", intensity_range=[4, 8]),
    Event("sector_rotation", "Sector Rotation", "trading_market",
          domains=["trading"],
          houses=[3, 10, 11], planetary_significators=["Mercury", "Rahu", "Jupiter"],
          polarity="neutral", intensity_range=[3, 6]),
    Event("liquidity_stress", "Liquidity Stress", "trading_market",
          domains=["trading"],
          houses=[2, 8, 12], planetary_significators=["Saturn", "Rahu", "Moon"],
          polarity="negative", intensity_range=[5, 9]),
    Event("momentum_alignment", "Momentum Alignment", "trading_market",
          domains=["trading"],
          houses=[1, 10, 11], planetary_significators=["Mars", "Sun", "Jupiter"],
          polarity="positive", intensity_range=[5, 9]),
    Event("timing_window", "Timing Window", "trading_market",
          domains=["trading"],
          houses=[2, 5, 11], planetary_significators=["Mercury", "Jupiter", "Moon"],
          polarity="positive", intensity_range=[5, 8]),
]


# ═══════════════════════════════════════════════════════════════
# MASTER REGISTRY
# ═══════════════════════════════════════════════════════════════

EVENT_MAP_V3: List[Event] = (
    _CAREER_ENTERPRISE
    + _RELATIONSHIPS_FAMILY
    + _HEALTH_WELLBEING
    + _SPIRITUAL_LEARNING
    + _LIFE_SHIFTS_ASSETS
    + _TRADING_MARKET
)

# Index by event_id for O(1) lookup
EVENT_INDEX = {e.event_id: e for e in EVENT_MAP_V3}

# Count verification
assert len(EVENT_MAP_V3) == 104, f"Expected 104 events, got {len(EVENT_MAP_V3)}"
