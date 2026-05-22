"""
Confidence Calibration (Layer D)

Post-hoc calibration of confidence scores based on historical feedback.
Takes a raw confidence value and optional calibration config, returns adjusted confidence.

This is the top of the decision layer — it never touches ephemeris or features directly.
"""


def apply_confidence_calibration(confidence, calibration_config=None):
    """
    Apply post-hoc calibration to a raw confidence score.

    Args:
        confidence: float, raw confidence score (0-100)
        calibration_config: optional dict with calibration parameters:
            - "offset": float, additive bias correction (default 0)
            - "scale": float, multiplicative scaling (default 1.0)
            - "floor": float, minimum output (default 0.0)
            - "ceiling": float, maximum output (default 100.0)
            - "enabled": bool, if False returns confidence unchanged

    Returns:
        float: calibrated confidence (0-100)
    """
    if calibration_config is None:
        return confidence

    if not calibration_config.get("enabled", True):
        return confidence

    offset = float(calibration_config.get("offset", 0.0))
    scale = float(calibration_config.get("scale", 1.0))
    floor = float(calibration_config.get("floor", 0.0))
    ceiling = float(calibration_config.get("ceiling", 100.0))

    calibrated = (confidence * scale) + offset
    return round(max(floor, min(ceiling, calibrated)), 2)
