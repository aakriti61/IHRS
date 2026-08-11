
"""
NEWS2 -- National Early Warning Score 2 (Royal College of Physicians, 2017).

A public, non-proprietary early-warning score used across NHS hospitals
to flag deteriorating patients from six routinely-collected vital signs.
Thresholds below are exactly the published RCP NEWS2 scoring table
(SpO2 Scale 1 -- i.e. NOT the Scale 2 table used for COPD/hypercapnic
patients on target 88-92% saturation, which is a separate clinical
decision the treating doctor would flag manually if needed).

WHY this score and not a machine-learning model: NEWS2 needs no
training dataset -- it's a fixed lookup table -- which fits a project
with no real patient dataset to train on, and its published, cited
weights make it fully defensible in a viva ("why these thresholds" ->
"they are the RCP's own published table, not invented").

This score is computed at READ-TIME from decrypted vitals and is
NEVER persisted in plaintext or shown to the patient -- read_record_view
only attaches this to the response when request.user.role is a
clinical role (doctor/nurse), never for the patient themself.
"""


def _score_respiration_rate(rr):
    if rr is None:
        return 0
    if rr <= 8:
        return 3
    if 9 <= rr <= 11:
        return 1
    if 12 <= rr <= 20:
        return 0
    if 21 <= rr <= 24:
        return 2
    return 3  # >=25


def _score_spo2(spo2):
    if spo2 is None:
        return 0
    if spo2 <= 91:
        return 3
    if 92 <= spo2 <= 93:
        return 2
    if 94 <= spo2 <= 95:
        return 1
    return 0  # >=96


def _score_oxygen(on_oxygen):
    return 2 if on_oxygen else 0


def _score_systolic_bp(sbp):
    if sbp is None:
        return 0
    if sbp <= 90:
        return 3
    if 91 <= sbp <= 100:
        return 2
    if 101 <= sbp <= 110:
        return 1
    if 111 <= sbp <= 219:
        return 0
    return 3  # >=220


def _score_pulse(pulse):
    if pulse is None:
        return 0
    if pulse <= 40:
        return 3
    if 41 <= pulse <= 50:
        return 1
    if 51 <= pulse <= 90:
        return 0
    if 91 <= pulse <= 110:
        return 1
    if 111 <= pulse <= 130:
        return 2
    return 3  # >=131


def _score_consciousness(level):
    # ACVPU: Alert / new-onset Confusion / Voice / Pain / Unresponsive.
    # Anything other than "A" (Alert) scores 3 -- new confusion is
    # treated with the same urgency as unresponsiveness in NEWS2.
    if level is None:
        return 0
    return 0 if level == "A" else 3


def _score_temperature(temp):
    if temp is None:
        return 0
    if temp <= 35.0:
        return 3
    if 35.1 <= temp <= 36.0:
        return 1
    if 36.1 <= temp <= 38.0:
        return 0
    if 38.1 <= temp <= 39.0:
        return 1
    return 2  # >=39.1


def calculate_news2(vitals: dict) -> dict:
    """
    vitals keys expected (all optional, missing = 0 contribution):
        respiratory_rate (int, breaths/min)
        spo2 (int, %)
        on_oxygen (bool)
        systolic_bp (int, mmHg)
        pulse (int, bpm)
        consciousness (str: 'A'/'C'/'V'/'P'/'U')
        temperature (float, degrees C)

    Returns:
        {
          "total_score": int,
          "risk_level": "low" | "medium" | "high",
          "breakdown": {<parameter>: <points>, ...},
        }
    """
    breakdown = {
        "respiratory_rate": _score_respiration_rate(vitals.get("respiratory_rate")),
        "spo2": _score_spo2(vitals.get("spo2")),
        "oxygen": _score_oxygen(vitals.get("on_oxygen", False)),
        "systolic_bp": _score_systolic_bp(vitals.get("systolic_bp")),
        "pulse": _score_pulse(vitals.get("pulse")),
        "consciousness": _score_consciousness(vitals.get("consciousness")),
        "temperature": _score_temperature(vitals.get("temperature")),
    }

    total = sum(breakdown.values())

    # NEWS2 risk banding (RCP standard): a single parameter scoring 3
    # bumps risk to at least "medium" even if the total looks moderate
    # -- one extreme reading matters clinically on its own.
    any_single_3 = any(v == 3 for v in breakdown.values())

    if total >= 7:
        risk_level = "high"
    elif total >= 5 or any_single_3:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "total_score": total,
        "risk_level": risk_level,
        "breakdown": breakdown,
    }