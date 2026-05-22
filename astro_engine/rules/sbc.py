from features.nakshatra import nakshatra_list

BENEFICS = {"Jupiter", "Venus", "Mercury"}
MALEFICS = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}
FAST_MOVING_PLANETS = {"Moon", "Mercury", "Venus", "Sun"}

VOWEL_SET = ["a", "aa", "i", "ii", "u", "uu", "ri", "e", "ai"]
CONSONANT_SET = ["ka", "cha", "ta", "tha", "pa", "ya", "sha", "sa", "ha"]
VEDHA_OFFSETS = {1, 2, 4, 5, 7, 8, 10, 11, 13}


def _safe_index(seq, value, default=0):
    try:
        return seq.index(value)
    except ValueError:
        return default


def _nak_by_offset(nak, offset):
    idx = _safe_index(nakshatra_list, nak)
    return nakshatra_list[(idx + offset) % len(nakshatra_list)]


def _motion_direction(planet_name, retrograde):
    if retrograde:
        return "left"
    if planet_name in FAST_MOVING_PLANETS:
        return "right"
    return "right"


def _is_vedha_hit(anchor_idx, actor_idx, direction):
    if direction == "left":
        offset = (anchor_idx - actor_idx) % len(nakshatra_list)
    else:
        offset = (actor_idx - anchor_idx) % len(nakshatra_list)
    return offset in VEDHA_OFFSETS


def evaluate_sbc_vedha(planets, janma_nak, tithi=1, retrograde_flags=None):
    retrograde_flags = retrograde_flags or {}
    tithi = int(tithi or 1)

    sampat_nak = _nak_by_offset(janma_nak, 1)
    karma_nak = _nak_by_offset(janma_nak, 5)  # Sadhana position (6th from janma) = karma/work zone

    sensitive = {
        "janma": janma_nak,
        "sampat": sampat_nak,
        "karma": karma_nak,
    }

    anchor_meta = {}
    for key, nak in sensitive.items():
        idx = _safe_index(nakshatra_list, nak)
        anchor_meta[key] = {
            "nakshatra": nak,
            "nak_index": idx,
            "vowel": VOWEL_SET[(idx + tithi) % len(VOWEL_SET)],
            "consonant": CONSONANT_SET[(idx + tithi) % len(CONSONANT_SET)],
        }

    hits = []
    motion_logic = {}
    malefic_by_zone = {"janma": set(), "sampat": set(), "karma": set()}
    benefic_by_zone = {"janma": set(), "sampat": set(), "karma": set()}

    for p in planets:
        name = p.get("name")
        planet_nak = p.get("nakshatra")
        if not name or not planet_nak:
            continue

        actor_idx = _safe_index(nakshatra_list, planet_nak)
        motion = _motion_direction(name, bool(retrograde_flags.get(name, False)))
        motion_logic[name] = motion

        for zone, info in anchor_meta.items():
            hit = _is_vedha_hit(info["nak_index"], actor_idx, motion)
            if not hit:
                continue

            layer = "malefic" if name in MALEFICS else "benefic" if name in BENEFICS else "neutral"
            if layer == "malefic":
                malefic_by_zone[zone].add(name)
            elif layer == "benefic":
                benefic_by_zone[zone].add(name)

            hits.append(
                {
                    "planet": name,
                    "zone": zone,
                    "layer": layer,
                    "direction": motion,
                    "planet_nakshatra": planet_nak,
                    "anchor_nakshatra": info["nakshatra"],
                    "anchor_vowel": info["vowel"],
                    "anchor_consonant": info["consonant"],
                }
            )

    malefic_hit_count = sum(len(v) for v in malefic_by_zone.values())

    return {
        "enabled": True,
        "sensitive_points": anchor_meta,
        "zones": {
            "janma": {
                "malefic_vedha": len(malefic_by_zone["janma"]) > 0,
                "benefic_vedha": len(benefic_by_zone["janma"]) > 0,
                "malefics": sorted(malefic_by_zone["janma"]),
                "benefics": sorted(benefic_by_zone["janma"]),
            },
            "sampat": {
                "malefic_vedha": len(malefic_by_zone["sampat"]) > 0,
                "benefic_vedha": len(benefic_by_zone["sampat"]) > 0,
                "malefics": sorted(malefic_by_zone["sampat"]),
                "benefics": sorted(benefic_by_zone["sampat"]),
            },
            "karma": {
                "malefic_vedha": len(malefic_by_zone["karma"]) > 0,
                "benefic_vedha": len(benefic_by_zone["karma"]) > 0,
                "malefics": sorted(malefic_by_zone["karma"]),
                "benefics": sorted(benefic_by_zone["karma"]),
            },
        },
        "motion_logic": motion_logic,
        "hits": hits,
        "malefic_vedha_count": malefic_hit_count,
        "extreme_malefic_pressure": malefic_hit_count >= 4,
    }
