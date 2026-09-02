def calculate_mosca_risk(
    data_lifetime,
    migration_time,
    quantum_horizon,
    business_criticality="Medium"
):
    """
    Mosca-style migration urgency assessment.

    X = data confidentiality lifetime
    Y = migration time
    Z = estimated quantum threat horizon

    If X + Y > Z, migration planning is urgent.

    quantum_horizon is a planning assumption,
    not a prediction.
    """

    x = float(data_lifetime)
    y = float(migration_time)
    z = float(quantum_horizon)

    exposure_window = x + y
    margin = z - exposure_window

    criticality = business_criticality.strip().lower()

    if exposure_window > z:

        if criticality == "critical":
            risk = "CRITICAL"

        elif criticality == "high":
            risk = "CRITICAL"

        else:
            risk = "HIGH"

        status = "AT_RISK"

        explanation = (
            f"Data lifetime ({x:g} years) plus estimated migration "
            f"time ({y:g} years) equals {exposure_window:g} years, "
            f"which exceeds the assumed quantum-threat horizon of "
            f"{z:g} years. Migration planning should begin now."
        )

    elif exposure_window == z:

        risk = "HIGH"
        status = "BOUNDARY"

        explanation = (
            f"Data lifetime plus migration time equals the assumed "
            f"quantum-threat horizon ({z:g} years). There is no "
            f"migration safety margin."
        )

    else:

        if margin <= 2:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        status = "WITHIN_MARGIN"

        explanation = (
            f"Data lifetime plus migration time is "
            f"{exposure_window:g} years, leaving an estimated "
            f"{margin:g}-year margin before the assumed "
            f"quantum-threat horizon."
        )

    return {
        "data_lifetime": x,
        "migration_time": y,
        "quantum_horizon": z,
        "business_criticality": business_criticality,
        "x_plus_y": exposure_window,
        "margin": margin,
        "mosca_status": status,
        "mosca_risk": risk,
        "mosca_explanation": explanation,
    }