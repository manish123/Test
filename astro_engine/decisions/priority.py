def rank_events(event_scores):
    sorted_events = sorted(
        event_scores.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    return sorted_events[:2]
