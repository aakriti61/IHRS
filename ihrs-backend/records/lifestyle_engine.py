from collections import defaultdict
from datetime import datetime, timezone
"""
Trend analysis + rule-based lifestyle recommendation engine.

Deliberately NOT a trained ML model -- there is no dataset of Nepali
patient outcomes to train one on, so instead every threshold below is
taken from a named, published clinical guideline, making each
recommendation traceable to a real source for your viva defense:

  - Fasting glucose / HbA1c bands: American Diabetes Association (ADA),
    Standards of Medical Care in Diabetes.
  - Blood pressure bands: ACC/AHA 2017 Hypertension Clinical Practice
    Guideline.
  - LDL cholesterol bands: NCEP ATP III / ACC-AHA cholesterol guideline.
  - BMI bands: WHO BMI classification.
  - Hemoglobin bands: WHO haemoglobin cutoffs for anemia.

TREND direction is a separate, simpler idea -- NOT from a paper, just
a "delta check": compare a patient's newest lab value to their own
immediately preceding value, the same concept lab quality-control
systems use to flag a meaningfully-changed result, rather than only
comparing each value in isolation to a population reference range.
"""

from collections import defaultdict

THRESHOLDS = {
    "glucose_fasting": {
        "unit": "mg/dL",
        "bands": [
            (0, 100, "normal"),
            (100, 126, "prediabetes"),
            (126, float("inf"), "diabetes_range"),
        ],
    },
    "hba1c": {
        "unit": "%",
        "bands": [
            (0, 5.7, "normal"),
            (5.7, 6.5, "prediabetes"),
            (6.5, float("inf"), "diabetes_range"),
        ],
    },
    "systolic_bp": {
        "unit": "mmHg",
        "bands": [
            (0, 120, "normal"),
            (120, 130, "elevated"),
            (130, 140, "hypertension_stage1"),
            (140, float("inf"), "hypertension_stage2"),
        ],
    },
    "ldl_cholesterol": {
        "unit": "mg/dL",
        "bands": [
            (0, 100, "optimal"),
            (100, 130, "borderline"),
            (130, float("inf"), "high"),
        ],
    },
    "bmi": {
        "unit": "kg/m2",
        "bands": [
            (0, 18.5, "underweight"),
            (18.5, 25, "normal"),
            (25, 30, "overweight"),
            (30, float("inf"), "obese"),
        ],
    },
    "hemoglobin": {
        "unit": "g/dL",
        "bands": [
            (0, 12, "low"),
            (12, 17, "normal"),
            (17, float("inf"), "high"),
        ],
    },
    "creatinine": {
        "unit": "mg/dL",
        "bands": [
            (0, 0.6, "low"),
            (0.6, 1.3, "normal"),
            (1.3, float("inf"), "elevated"),
        ],
    },
}

RECOMMENDATIONS = {
    ("glucose_fasting", "prediabetes"):
        "Fasting glucose is in the prediabetes range (ADA criteria). "
        "Reduce refined sugar and white-rice portions, add about 30 "
        "minutes of daily walking, and recheck in 3 months.",
    ("glucose_fasting", "diabetes_range"):
        "Fasting glucose is in the diabetic range. This needs clinical "
        "follow-up; meanwhile, cut sugary drinks and refined carbs and "
        "watch for excess thirst, frequent urination, or fatigue.",
    ("hba1c", "prediabetes"):
        "HbA1c indicates prediabetes. A sustained 5-7% body-weight "
        "reduction through diet and activity meaningfully lowers the "
        "risk of progressing to diabetes (ADA).",
    ("hba1c", "diabetes_range"):
        "HbA1c is in the diabetic range and needs clinical management. "
        "Alongside treatment, keep meal timing consistent and reduce "
        "simple carbohydrates.",
    ("systolic_bp", "elevated"):
        "Blood pressure is elevated. Reduce salt intake, add "
        "potassium-rich foods (fruits, vegetables), and recheck weekly.",
    ("systolic_bp", "hypertension_stage1"):
        "Blood pressure indicates Stage 1 hypertension (ACC/AHA). "
        "Reduce sodium, limit alcohol, increase physical activity, and "
        "arrange a clinical review.",
    ("systolic_bp", "hypertension_stage2"):
        "Blood pressure indicates Stage 2 hypertension. This needs "
        "prompt clinical evaluation, not lifestyle changes alone.",
    ("ldl_cholesterol", "borderline"):
        "LDL cholesterol is borderline high. Reduce saturated fat and "
        "fried food, increase fiber (oats, legumes), and recheck in "
        "3-6 months.",
    ("ldl_cholesterol", "high"):
        "LDL cholesterol is high. Dietary changes plus a clinical "
        "evaluation for further management are recommended.",
    ("bmi", "underweight"):
        "BMI is below the healthy range. A nutrition assessment is "
        "recommended to check for an underlying cause.",
    ("bmi", "overweight"):
        "BMI is in the overweight range. A gradual ~500 kcal/day "
        "deficit and regular activity are recommended (WHO).",
    ("bmi", "obese"):
        "BMI is in the obese range. Structured weight management with "
        "clinical guidance is recommended alongside diet and activity "
        "changes.",
    ("hemoglobin", "low"):
        "Hemoglobin is low, suggesting possible anemia. Increase "
        "iron-rich foods (leafy greens, legumes, meat) and consider "
        "clinical evaluation for the cause.",
    ("creatinine", "elevated"):
        "Creatinine is elevated, which can indicate reduced kidney "
        "function. Clinical follow-up is recommended; avoid NSAIDs and "
        "stay well hydrated meanwhile.",
}


def classify_value(test_type, value):
    """Returns the band label a value falls into for this test_type."""
    config = THRESHOLDS.get(test_type)
    if not config:
        return None
    for low, high, label in config["bands"]:
        if low <= value < high:
            return label
    return None


def compute_trend(values_in_order):
    """
    values_in_order: floats, OLDEST -> NEWEST, for one test_type,
    one patient. Delta check against the patient's own prior result
    -- not a comparison to population norms.

    Returns "rising", "falling", "stable", or "insufficient_data".
    """
    if len(values_in_order) < 2:
        return "insufficient_data"

    latest = values_in_order[-1]
    previous = values_in_order[-2]

    if previous == 0:
        return "insufficient_data"

    percent_change = ((latest - previous) / previous) * 100

    if percent_change > 5:
        return "rising"
    if percent_change < -5:
        return "falling"
    return "stable"


def generate_recommendation(test_type, latest_value, trend):
    """
    Combines the current threshold band with trend direction. A
    borderline-but-rising result gets a firmer nudge than a
    borderline-but-stable one, even though both sit in the same band
    -- direction of change matters clinically, not just the snapshot.
    """
    band = classify_value(test_type, latest_value)
    if band is None:
        return None

    base_message = RECOMMENDATIONS.get((test_type, band))

    if base_message is None:
        # Value is within the normal/optimal band -- nothing to flag,
        # but a rising trend even within normal range is still worth
        # a light heads-up.
        if trend == "rising":
            label = test_type.replace("_", " ").title()
            return (f"{label} is within the normal range but has been "
                    f"trending upward -- worth mentioning at your next visit.")
        return None

    if trend == "rising":
        return base_message + (" Note: this value has been rising over "
                                "your recent visits, so please don't delay follow-up.")
    return base_message

def _normalize_created_at(value):
    """
    Local DB lab reports (decrypt_helpers.py) hand over created_at as a
    real datetime.datetime object. Peer-hospital lab reports arrive via
    merge_peer_records() from a JSON API response, so created_at there
    is an ISO-format string. Normalize both to timezone-aware datetimes
    so sorted() can compare them safely.
    """
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value

def build_lifestyle_summary(lab_reports):
    """
    lab_reports: list of dicts with keys test_type, value, unit,
    created_at (already decrypted -- called from read_record_view).

    Returns: { test_type: {latest_value, unit, trend, recommendation} }
    Only test_types actually present in the patient's history appear.
    """
    grouped = defaultdict(list)
    for report in lab_reports:
        if "test_type" in report and "value" in report:
            grouped[report["test_type"]].append(report)

    summary = {}
    for test_type, reports in grouped.items():
        reports_sorted = sorted(reports, key=lambda r: _normalize_created_at(r["created_at"]))
        values = [r["value"] for r in reports_sorted]
        trend = compute_trend(values)
        latest_value = values[-1]

        summary[test_type] = {
            "latest_value": latest_value,
            "unit": reports_sorted[-1].get("unit"),
            "trend": trend,
            "recommendation": generate_recommendation(test_type, latest_value, trend),
        }

    return summary