"""
Asteric RiskIQ - Data Preprocessor

Handles feature engineering, data validation, and transformation.
"""

import numpy as np
import pandas as pd
from typing import Optional
from loguru import logger


FEATURE_COLUMNS = [
    "age", "gender_encoded", "length_of_stay",
    "num_previous_admissions", "admissions_last_6months",
    "num_chronic_conditions", "medication_count", "missed_appointments",
    "has_diabetes", "has_heart_failure", "has_copd", "has_ckd",
    "has_hypertension", "has_depression", "has_afib",
    "bp_systolic", "bp_diastolic", "heart_rate", "temperature",
    "oxygen_saturation", "respiratory_rate", "bmi",
    "hemoglobin", "wbc_count", "creatinine", "glucose", "bun",
    "sodium", "potassium",
    "discharge_hour", "is_weekend_discharge",
    "lives_alone", "has_caregiver", "transportation_access", "housing_stable",
    "insurance_encoded", "smoking_encoded", "alcohol_encoded",
    "comorbidity_interaction_score", "clinical_complexity_score",
    "social_vulnerability_score", "vital_instability_score",
    "lab_abnormality_score", "readmission_velocity",
]

TARGET_COLUMN = "readmitted_7d"


def prepare_training_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Prepare features and target for model training."""
    available_cols = [c for c in FEATURE_COLUMNS if c in df.columns]
    missing_cols = [c for c in FEATURE_COLUMNS if c not in df.columns]

    if missing_cols:
        logger.warning(f"Missing columns: {missing_cols}")

    X = df[available_cols].copy()
    y = df[TARGET_COLUMN].copy()

    # Handle missing values
    X = X.fillna(X.median())

    # Clip extreme outliers (3 sigma)
    for col in X.select_dtypes(include=[np.number]).columns:
        mean = X[col].mean()
        std = X[col].std()
        if std > 0:
            X[col] = X[col].clip(mean - 4 * std, mean + 4 * std)

    logger.info(f"Prepared {len(X)} samples with {len(available_cols)} features")
    return X, y


def extract_features_from_raw(raw_patient: dict) -> dict:
    """Extract ML features from a raw patient record."""
    vitals = raw_patient.get("vitals", {})
    labs = raw_patient.get("labs", {})
    social = raw_patient.get("social_factors", {})
    chronic = raw_patient.get("chronic_conditions", [])

    features = {
        "age": raw_patient.get("age", 50),
        "gender_encoded": 1 if raw_patient.get("gender") == "Male" else 0,
        "length_of_stay": raw_patient.get("length_of_stay", 3),
        "num_previous_admissions": raw_patient.get("num_previous_admissions", 0),
        "admissions_last_6months": raw_patient.get("admissions_last_6months", 0),
        "num_chronic_conditions": len(chronic),
        "medication_count": raw_patient.get("medication_count", 3),
        "missed_appointments": raw_patient.get("missed_appointments", 0),
        "has_diabetes": int("Type 2 Diabetes" in chronic or "Type 1 Diabetes" in chronic),
        "has_heart_failure": int("Heart Failure" in chronic),
        "has_copd": int("COPD" in chronic),
        "has_ckd": int("Chronic Kidney Disease" in chronic),
        "has_hypertension": int("Hypertension" in chronic),
        "has_depression": int("Depression" in chronic),
        "has_afib": int("Atrial Fibrillation" in chronic),
        "bp_systolic": vitals.get("bp_systolic", 120),
        "bp_diastolic": vitals.get("bp_diastolic", 80),
        "heart_rate": vitals.get("heart_rate", 75),
        "temperature": vitals.get("temperature", 98.6),
        "oxygen_saturation": vitals.get("oxygen_saturation", 97),
        "respiratory_rate": vitals.get("respiratory_rate", 16),
        "bmi": raw_patient.get("bmi", 26),
        "hemoglobin": labs.get("hemoglobin", 13.5),
        "wbc_count": labs.get("wbc_count", 7.5),
        "creatinine": labs.get("creatinine", 1.0),
        "glucose": labs.get("glucose", 100),
        "bun": labs.get("bun", 15),
        "sodium": labs.get("sodium", 140),
        "potassium": labs.get("potassium", 4.2),
        "discharge_hour": raw_patient.get("discharge_hour", 14),
        "is_weekend_discharge": int(raw_patient.get("is_weekend_discharge", False)),
        "lives_alone": int(social.get("lives_alone", False)),
        "has_caregiver": int(social.get("has_caregiver", True)),
        "transportation_access": int(social.get("transportation_access", True)),
        "housing_stable": int(social.get("housing_stable", True)),
        "insurance_encoded": _encode_insurance(raw_patient.get("insurance", "Private")),
        "smoking_encoded": {"never": 0, "former": 1, "current": 2}.get(
            raw_patient.get("smoking_status", "never"), 0
        ),
        "alcohol_encoded": {"none": 0, "social": 1, "moderate": 2, "heavy": 3}.get(
            raw_patient.get("alcohol_use", "none"), 0
        ),
    }

    # Compute derived features
    features["comorbidity_interaction_score"] = _compute_comorbidity_score(chronic)
    features["clinical_complexity_score"] = _compute_clinical_complexity(features)
    features["social_vulnerability_score"] = _compute_social_vulnerability(features)
    features["vital_instability_score"] = _compute_vital_instability(vitals)
    features["lab_abnormality_score"] = _compute_lab_abnormality(labs)
    features["readmission_velocity"] = min(10, features["admissions_last_6months"] * 2)

    return features


def _encode_insurance(insurance: str) -> int:
    return {"Private": 0, "Medicare": 1, "Medicare Advantage": 1,
            "Medicaid": 2, "Self-Pay": 3}.get(insurance, 4)


def _compute_comorbidity_score(conditions: list) -> float:
    pairs = [
        ("Heart Failure", "Chronic Kidney Disease"),
        ("Heart Failure", "Type 2 Diabetes"),
        ("COPD", "Heart Failure"),
        ("Type 2 Diabetes", "Chronic Kidney Disease"),
        ("Hypertension", "Heart Failure"),
    ]
    score = sum(0.15 for c1, c2 in pairs if c1 in conditions and c2 in conditions)
    return min(1.0, score)


def _compute_clinical_complexity(features: dict) -> float:
    score = (
        features.get("num_chronic_conditions", 0) * 0.15 +
        (features.get("medication_count", 0) / 25) * 0.2 +
        (features.get("admissions_last_6months", 0) / 5) * 0.25 +
        (1 - features.get("oxygen_saturation", 97) / 100) * 0.2 +
        (features.get("missed_appointments", 0) / 5) * 0.2
    )
    return round(min(1.0, max(0.0, score)), 3)


def _compute_social_vulnerability(features: dict) -> float:
    return round(
        features.get("lives_alone", 0) * 0.25 +
        (1 - features.get("has_caregiver", 1)) * 0.25 +
        (1 - features.get("transportation_access", 1)) * 0.25 +
        (1 - features.get("housing_stable", 1)) * 0.25,
        3,
    )


def _compute_vital_instability(vitals: dict) -> float:
    score = 0.0
    if vitals.get("bp_systolic", 120) > 160 or vitals.get("bp_systolic", 120) < 90:
        score += 0.2
    if vitals.get("heart_rate", 75) > 100 or vitals.get("heart_rate", 75) < 50:
        score += 0.2
    if vitals.get("temperature", 98.6) > 100.4:
        score += 0.2
    if vitals.get("oxygen_saturation", 97) < 92:
        score += 0.25
    if vitals.get("respiratory_rate", 16) > 24:
        score += 0.15
    return round(min(1.0, score), 3)


def _compute_lab_abnormality(labs: dict) -> float:
    score = 0.0
    if labs.get("hemoglobin", 13.5) < 10:
        score += 0.15
    if labs.get("wbc_count", 7.5) > 12:
        score += 0.15
    if labs.get("creatinine", 1.0) > 1.5:
        score += 0.2
    if labs.get("glucose", 100) > 200:
        score += 0.15
    if labs.get("sodium", 140) < 135:
        score += 0.15
    if labs.get("potassium", 4.2) > 5.0:
        score += 0.15
    return round(min(1.0, score), 3)
