# Platform & Web Layer Integration Map

## Executive Summary

The production system is a 3-tier architecture:
1. **Web (Next.js)** — renders UI, proxies API calls, manages auth state
2. **Platform Core (FastAPI)** — auth, billing, subscriptions, entitlements, user data (Firestore)
3. **Domain APIs (FastAPI)** — personality_api (port 8000), timing_api (port 8001)

The web layer does NOT directly call domain APIs. It proxies through Next.js API routes
which inject the correct API key server-side. The platform_core manages user profiles
and caches API responses in Firestore.

**Key insight:** The symbolic cognition layer can be injected at the domain API level
(personality_api, timing_api) without touching the platform or web layers at all.
The web layer renders whatever the API returns — it's shape-agnostic for new fields.

---

## 1. Platform Core Architecture

```
platform_core/ (FastAPI, port 8080)
├── auth/           — Firebase authentication
├── billing/        — Razorpay payment integration
├── subscriptions/  — Subscription lifecycle management
├── entitlements/   — Capability-based access control
├── models/         — Firestore client + Pydantic schemas
├── routers/
│   ├── auth.py         — signup, login
│   ├── users.py        — GET/PATCH /me (user profile)
│   ├── products.py     — product catalog
│   ├── subscriptions.py — subscription management
│   ├── entitlements.py — capability checks
│   ├── billing.py      — order creation
│   ├── webhooks.py     — Razorpay webhooks
│   ├── feedback.py     — user feedback
│   └── calibration.py  — birth time rectification
└── shared/         — config, exceptions
```

### User Profile (Firestore document):
```
{
    firebase_uid, email, full_name, phone,
    date_of_birth, time_of_birth, city_of_birth,
    personality_profile: dict | null,  ← CACHED personality API response
    timing_report: dict | null,        ← CACHED timing API response
    past_insights: list | null,
    status, role, created_at, last_login_at
}
```

### Platform does NOT:
- Call astro_engine directly
- Build prompts
- Generate narratives
- Score events
- Interpret charts

### Platform DOES:
- Store user birth data
- Cache API responses in Firestore
- Manage subscriptions and entitlements
- Authenticate users via Firebase
- Process payments via Razorpay

---

## 2. Web Layer Architecture

```
astralyn_web/ (Next.js, deployed on Cloud Run)
├── src/app/
│   ├── api/
│   │   ├── personality/[...path]/route.ts  — proxy to personality_api
│   │   ├── timing/[...path]/route.ts       — proxy to timing_api
│   │   └── platform/[...path]/route.ts     — proxy to platform_core
│   ├── personality/page.tsx    — renders personality profile
│   ├── timing/page.tsx         — renders timing report
│   ├── predictions/page.tsx    — renders weekly predictions
│   ├── past-insights/page.tsx  — renders past event analysis
│   ├── dashboard/page.tsx      — main dashboard
│   ├── profile-setup/page.tsx  — birth data input
│   └── pricing/page.tsx        — subscription plans
├── src/components/
│   ├── AppShell.tsx            — layout wrapper
│   ├── WeeklySummaryCard.tsx   — weekly prediction display
│   ├── DailyMoonCard.tsx       — daily moon transit
│   ├── DomainActivation.tsx    — domain score visualization
│   ├── LockedSection.tsx       — paywall UI
│   ├── RetrospectivePanel.tsx  — past insights display
│   └── CalibrationStatus.tsx   — birth time rectification
├── src/context/
│   ├── AuthContext.tsx         — Firebase auth state
│   └── LanguageContext.tsx     — i18n (en/hi)
└── src/lib/
    ├── api.ts                  — fetch helpers (timingFetch, personalityFetch)
    ├── entitlements.ts         — capability checks
    ├── firebase.ts             — Firebase client
    ├── pdf-export.ts           — PDF generation
    └── prediction-cache.ts     — local prediction caching
```

### Web data flow:
```
User action → page.tsx → lib/api.ts → /api/[service]/route.ts (proxy)
    → domain API (personality/timing) → response
    → page.tsx renders sections/narratives
    → optionally caches in platform_core via PATCH /me
```

### What the web renders from personality API:
- `sections[]` — array of {id, title, teaser, locked, data?, narrative?}
- `life_narrative` — 400-700 word prose (paid only)
- `structured_profile` — section narratives (paid only)

### What the web renders from timing API:
- `current_phase` — phase label, emotional texture
- `timeline` — 12-month GREEN/AMBER/RED zones
- `career_strategy` — job/business suitability, role fit
- `money_wealth` — income growth, investment timing
- `decision_playbook` — IF-THEN rules
- `section_envelopes` — insight + action_hint per section (from OpenAI)
- `life_narrative` — timing story (from OpenAI)

---

## 3. Data Flow Map

```
┌─────────────────────────────────────────────────────────────┐
│  WEB LAYER (Next.js)                                        │
│  - Renders sections, narratives, charts                     │
│  - Proxies API calls (injects API key server-side)          │
│  - Caches responses in platform_core                        │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP (proxied)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  PLATFORM CORE (FastAPI)                                    │
│  - Auth (Firebase)                                          │
│  - Billing (Razorpay)                                       │
│  - Entitlements (capability checks)                         │
│  - User profiles (Firestore cache)                          │
│  - Does NOT interpret astrology                             │
└────────────────────────┬────────────────────────────────────┘
                         │ (user birth data stored here)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  DOMAIN APIs                                                │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ personality_api   │  │ timing_api        │                │
│  │ (port 8000)       │  │ (port 8001)       │                │
│  │                   │  │                   │                │
│  │ engine_bridge ────┼──┼─ engine_bridge ───┼──→ astro_engine│
│  │ openai_client     │  │ openai_client     │                │
│  │ section builders  │  │ section builders  │                │
│  └──────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  ASTRO ENGINE (computation core)                            │
│  - Swiss Ephemeris positions                                │
│  - Event scoring                                            │
│  - Risk calculation                                         │
│  - Personality engine                                       │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│  NEW (TEST repo):                                           │
│  - Symbolic cognition layer                                 │
│  - Orchestration contracts                                  │
│  - API adapters (personality, timing, career)               │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Mapping: Current → Future Symbolic

| Current Field | Source | Future Symbolic Equivalent | Integration Point |
|---------------|--------|---------------------------|-------------------|
| `personality_profile.sections[].narrative` | OpenAI Call 1 | Enriched by `personality_context` injection | openai_client.py prompt |
| `personality_profile.life_narrative` | OpenAI Call 2 | Enriched by `prompt_injection` text | openai_client.py prompt |
| `personality_profile.dispositional_profile` | personality_engine | Augmented by `behavioral_core` | engine_bridge.py |
| `timing_report.current_phase` | section_builder | Augmented by `lifecycle.phase` | engine_bridge.py |
| `timing_report.career_strategy` | section_builder | Augmented by `career_context` | engine_bridge.py |
| `timing_report.v2_signals.psychological_tendency` | dispositional_traits | Replaced by `identity.primary_archetype` | engine_bridge.py |
| `timing_report.v2_signals.vulnerability_level` | vulnerability_index | Augmented by `coherence.fragmentation` | engine_bridge.py |
| — (new) | — | `symbolic_context` (full payload) | NEW field in API response |

---

## 5. Compatibility Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Web renders `sections[]` by index/id | LOW | New fields are additive — existing sections unchanged |
| Platform caches full API response in Firestore | LOW | Larger payload but Firestore handles it |
| Web checks `personality_profile.dispositional_profile` existence | LOW | Field remains present; symbolic is additional |
| OpenAI prompts have hardcoded section expectations | MEDIUM | Symbolic context is APPENDED, not replacing existing prompt |
| PDF export uses `sections[].narrative` | NONE | Unchanged |
| Entitlement checks gate on capability strings | NONE | Unrelated to payload shape |

### No breaking changes identified.

The symbolic layer is purely additive. The web layer renders whatever the API returns —
it doesn't validate response shape beyond checking for `sections`, `life_narrative`, etc.

---

## 6. Recommended Integration Order

| Phase | Change | Risk | Where |
|-------|--------|------|-------|
| 1 | Add `symbolic_context` to personality_api engine_bridge output | ZERO | personality_api/engine_bridge.py |
| 2 | Append symbolic context to OpenAI prompts (personality) | LOW | personality_api/openai_client.py |
| 3 | Add `symbolic_timing` to timing_api engine_bridge output | ZERO | timing_api/engine_bridge.py |
| 4 | Append symbolic context to OpenAI prompts (timing) | LOW | timing_api/openai_client.py |
| 5 | Expose `symbolic_context` in API response for web display | LOW | models.py + routers |
| 6 | Web renders archetype/lifecycle in UI (optional) | LOW | astralyn_web components |
| 7 | Platform caches symbolic context in Firestore | ZERO | Automatic (already caches full response) |

**Each phase is independently deployable and reversible.**

---

## 7. Production Files That Remain Untouched

### Platform Core (ALL files — no changes needed):
- `platform_core/*` — auth, billing, subscriptions, entitlements, models, routers

### Web Layer (ALL files — no changes needed for Phases 1-4):
- `astralyn_web/*` — pages, components, lib, context

### Domain APIs (modify ONLY in Phases 1-4):
- `personality_api/engine_bridge.py` — add 1 line (Phase 1)
- `personality_api/openai_client.py` — append to prompt (Phase 2)
- `timing_api/engine_bridge.py` — add 1 line (Phase 3)
- `timing_api/openai_client.py` — append to prompt (Phase 4)

### Everything else remains untouched:
- All auth, rate limiting, geocoding, timezone, billing, subscription code
- All Dockerfiles, deploy scripts, config files
- All web components, pages, and API proxy routes
