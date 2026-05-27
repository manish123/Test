# Dasha Period Audit — Complete Evaluator Stack

**Date:** 2025-05-27  
**Scope:** All 18 evaluators in `astro_engine/rules/`  
**Finding:** 11 of 18 evaluators have their dasha layer SKIPPED by `multi_evaluator_runner`

---

## 1. Complete Evaluator Dasha Audit

| Evaluator | File | Dasha Layer? | Params | Explicit Handler? | Risk |
|-----------|------|-------------|--------|-------------------|------|
| marriage | `rules/marriage_evaluator.py` | YES | 3 (chart, md, ad) | NO | **HIGH — dasha skipped** |
| childbirth | `rules/childbirth_evaluator.py` | YES | 3 (chart, md, ad) | NO | **HIGH — dasha skipped** |
| career | `rules/career_evaluator.py` | YES | 3 (chart, md, ad) | NO | **HIGH — dasha skipped** |
| business | `rules/business_evaluator.py` | YES | 3 (chart, md, ad) | NO | **HIGH — dasha skipped** |
| relocation | `rules/relocation_evaluator.py` | YES | 3 (chart, md, ad) | NO | **HIGH — dasha skipped** |
| property | `rules/property_evaluator.py` | YES | 3 (chart, md, ad) | NO | **HIGH — dasha skipped** |
| property_purchase | `rules/property_purchase_evaluator.py` | YES | 3 (chart, md, ad) | NO | **HIGH — dasha skipped** |
| medical | `rules/medical_evaluator.py` | YES | 3 (chart, md, ad) | NO | **HIGH — dasha skipped** |
| fame | `rules/fame_evaluator.py` | YES | 3 (chart, md, ad) | NO | **HIGH — dasha skipped** |
| financial_crisis | `rules/financial_crisis_evaluator.py` | YES | 3 (chart, md, ad) | NO | **HIGH — dasha skipped** |
| vehicle_purchase | `rules/vehicle_purchase_evaluator.py` | YES | 3 (chart, md, ad) | NO | **HIGH — dasha skipped** |
| parent_loss | `rules/parent_loss_evaluator.py` | YES | 3 (chart, md, ad) | YES (fixed) | OK — explicit handler |
| wealth | `rules/wealth_evaluator.py` | YES | 2 (chart, eval_date) | YES | OK — computes dasha internally |
| career_authority | `rules/career_authority_evaluator.py` | YES | 2 (chart, eval_date) | YES | OK — computes dasha internally |
| social_network | `rules/social_network_evaluator.py` | YES | 2 (chart, eval_date) | YES | OK — computes dasha internally |
| creative_output | `rules/creative_output_evaluator.py` | YES | 2 (chart, eval_date) | YES | OK — computes dasha internally |
| litigation | `rules/litigation_evaluator.py` | YES | 2 (chart, eval_date) | YES | OK — computes dasha internally |
| foreign_migration | `rules/foreign_migration_evaluator.py` | YES | 2 (chart, eval_date) | YES | OK — computes dasha internally |

**Summary:** 11 HIGH-risk evaluators, 7 OK evaluators.

---

## 2. multi_evaluator_runner Flow Map

```
evaluate_all_domains(birth_dt, lat, lon, eval_date, alt)
    │
    ├── EXPLICIT HANDLERS (full dasha, compute internally):
    │   ├── wealth → evaluate_wealth_for_date(chart, eval_date) [2-param, dasha inside]
    │   ├── career_authority → evaluate_authority_for_date(chart, eval_date) [2-param]
    │   ├── social_network → evaluate_social_for_date(chart, eval_date) [2-param]
    │   ├── creative_output → evaluate_creative_for_date(chart, eval_date) [2-param]
    │   ├── litigation → evaluate_litigation_for_date(chart, eval_date) [2-param]
    │   ├── foreign_migration → evaluate_migration_for_date(chart, eval_date) [2-param]
    │   └── parent_loss → scan_parent_loss_windows(chart, age±1) [FIXED]
    │
    └── GENERIC FALLBACK (dasha SKIPPED for 3-param evaluators):
        ├── Instantiates: chart = mod.ChartState(...)
        ├── Instantiates: transit = mod.TransitState(eval_date, chart)
        ├── Checks: evaluate_dasha_layer signature
        │   ├── If 3 params → SKIP ("requires full dasha computation")  ← THE BUG
        │   └── If 2 params → call it (but no 2-param dasha layers exist in generic path)
        ├── Calls: evaluate_transit_layer(chart, transit) → scores
        ├── Calls: evaluate_fast_trigger_layer(chart, transit) → scores
        └── Returns: transit + fast_trigger scores ONLY (no dasha gate)
```

**The comment in the code says:** `# Need dasha info — skip for now (requires full dasha computation)`

This means **11 evaluators** run without their most important scoring layer.

---

## 3. Missing Dasha Signal — Quantified

Tested at gold-label event dates for Subject A:

| Event | Date | MD-AD | Domain | Dasha Score | Transit Score | Missing Signal |
|-------|------|-------|--------|-------------|---------------|----------------|
| Marriage | 2009-05-07 | Rahu-Venus | marriage | **45** | 58 | **45 points (43%)** |
| Son born | 2010-12-04 | Rahu-Venus | childbirth | **43** | 0 | **43 points (100%)** |
| Pune relocation | 2007-08-20 | Rahu-Mercury | relocation | **65** | 82 | **65 points (44%)** |
| Bhopal move | 2003-06-01 | Rahu-Saturn | relocation | **91** | 0 | **91 points (100%)** |
| Joined IBILT | 2005-06-01 | Rahu-Saturn | career | 0 | 28 | 0 (dasha not relevant) |
| Mother death | 1993-11-15 | Mars-Saturn | parent_loss | 42 | 0 | Fixed (explicit handler) |
| Father death | 2018-03-15 | Jupiter-Saturn | parent_loss | 35 | 0 | Fixed (explicit handler) |

**Critical findings:**
- **Childbirth at actual date scores 0 from transit** — the ONLY signal is from dasha (43 points), which is completely skipped
- **Bhopal relocation scores 0 from transit** — the ONLY signal is from dasha (91 points), completely skipped
- **Marriage loses 43% of its signal** — dasha contributes 45 of 103 total points

---

## 4. Why the Benchmark Still Shows Scores

The benchmark shows non-zero scores for these domains because:
1. Transit layer fires at **different dates** than the actual event (e.g., marriage transit peaks at 2008-07, not 2009-05)
2. The quarterly scan catches dates where transit happens to fire
3. But at the **actual event date**, transit may be zero while dasha is the only active signal

This explains the "peak drift" problem: the evaluator peaks where transit is strongest (wrong date) instead of where dasha+transit overlap (correct date).

---

## 5. Domains Most Affected

| Priority | Domain | Impact | Reason |
|----------|--------|--------|--------|
| 1 | **childbirth** | CRITICAL | At actual birth date, transit=0, dasha=43. Without dasha, event is invisible. |
| 2 | **relocation** | CRITICAL | Bhopal move: transit=0, dasha=91. Without dasha, event is invisible. |
| 3 | **marriage** | HIGH | Loses 43% of signal. Peak shifts to transit-only dates. |
| 4 | **business** | HIGH | TransitState crashes (missing methods). Dasha=unknown. |
| 5 | **property** | MODERATE | Likely same pattern as marriage (untested). |
| 6 | **career** | LOW | Dasha=0 at IBILT date (not relevant for this specific event). |
| 7 | **medical** | MODERATE | Untested but same architecture. |
| 8 | **fame** | LOW | Untested but same architecture. |
| 9 | **financial_crisis** | MODERATE | Untested but same architecture. |
| 10 | **vehicle_purchase** | LOW | Untested but same architecture. |

---

## 6. Root Cause

**File:** `rules/multi_evaluator_runner.py`, lines 244-248

```python
if len(params) == 3:  # chart, md_lord, ad_lord
    # Need dasha info — skip for now (requires full dasha computation)
    pass
```

This was written as a temporary workaround during the Phase 1 refactor. The "explicit handler" evaluators (wealth, career_authority, etc.) were designed with 2-param dasha layers that compute dasha internally. The older evaluators (marriage, childbirth, etc.) use 3-param dasha layers that expect the caller to provide MD/AD lords.

The fix is straightforward: compute current MD/AD in the generic fallback path and pass them to 3-param dasha layers.

---

## 7. Recommended Fix Priority

| Priority | Fix | Impact | Effort |
|----------|-----|--------|--------|
| 1 | Add dasha computation to generic fallback in `multi_evaluator_runner.py` | Fixes ALL 11 evaluators at once | LOW — ~15 lines |
| 2 | Fix `business_evaluator.TransitState` (missing methods like relocation was) | Unblocks business scoring | LOW — same pattern as relocation fix |
| 3 | Verify property, medical, fame, financial_crisis TransitState methods | May have same crash issue | LOW — inspection only |

**The single most impactful fix is adding dasha computation to the generic fallback path.** This would:
- Add 45 points to marriage scoring at actual date
- Add 43 points to childbirth scoring at actual date (from 0 to 43)
- Add 91 points to relocation scoring at actual date (from 0 to 91)
- Potentially fix the "peak drift" problem entirely for these domains

---

## 8. Proof of Issue

```
Marriage at 7 May 2009:
  Current (no dasha):  58 points (transit only)
  Correct (with dasha): 103 points (dasha=45 + transit=58)
  Missing: 45 points (43% of total signal)

Childbirth at 4 Dec 2010:
  Current (no dasha):  0 points (transit=0, fast=0)
  Correct (with dasha): 43 points (dasha=43)
  Missing: 43 points (100% of signal — event is INVISIBLE)

Bhopal relocation at Jun 2003:
  Current (no dasha):  0 points (transit=0)
  Correct (with dasha): 91 points (dasha=91)
  Missing: 91 points (100% of signal — event is INVISIBLE)
```

This definitively explains why:
- Childbirth peaks 6-12 months late (it finds transit activation, not dasha activation)
- Relocation peaks at wrong dates (transit fires at different times than dasha)
- Marriage peak is displaced from actual date (transit peak ≠ dasha+transit overlap)
