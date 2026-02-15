"""
Asteric RiskIQ - Realistic Synthetic Hospital Data Generator

Generates clinically realistic patient data with proper correlations:
- Age-dependent comorbidity patterns
- Realistic vital sign distributions
- Correlated lab values
- Proper readmission risk factors
- Clinical notes with embedded risk signals
- Social determinant data
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from faker import Faker
from loguru import logger
import json

from app.config import settings, ICD10_MAPPINGS, CHRONIC_CONDITIONS

fake = Faker()
Faker.seed(42)
np.random.seed(42)

# Clinical notes templates
CLINICAL_NOTES_TEMPLATES = {
    "high_risk": [
        "Patient is {age}yo {gender} presenting with {diagnosis}. History of {chronic1} and {chronic2}. "
        "Non-compliant with medications. {prev_admissions} admissions in last 6 months. "
        "Lives alone, limited support system. Unstable vitals on admission. "
        "Patient declined home health referral. Transportation issues noted.",

        "Readmission for {diagnosis} exacerbation. Patient has multiple comorbidities including "
        "{chronic1}, {chronic2}. Frequent flyer - {prev_admissions}x in 6 months. "
        "Altered mental status on arrival. Substance abuse history noted. "
        "No fixed address, shelter referral made. Poor prognosis discussed.",

        "{age}yo {gender} with {diagnosis}. Polypharmacy ({med_count} medications). "
        "Non-adherent to treatment plan. Missed {missed_appts} follow-up appointments. "
        "Social work consult requested - financial concerns, unable to afford medications. "
        "Fall risk assessment: HIGH. Confusion noted during exam.",
    ],
    "medium_risk": [
        "Patient is {age}yo {gender} admitted for {diagnosis}. Known history of {chronic1}. "
        "Generally compliant with medications but reports occasional missed doses. "
        "Follow-up needed with PCP within 7 days. Limited mobility, requires assistance with ADLs. "
        "Family involved in care planning.",

        "{age}yo {gender} with {diagnosis}. Comorbidities include {chronic1}. "
        "Borderline lab values, close monitoring recommended. Partial compliance with diet. "
        "Anxiety noted, counseling referral placed. Transportation arranged for follow-up.",

        "Admission for {diagnosis}. Patient has {chronic1}, well-controlled. "
        "Obesity noted, BMI {bmi}. Inconsistent medication adherence reported. "
        "Depression screening positive. Home health evaluation recommended.",
    ],
    "low_risk": [
        "Patient is {age}yo {gender} admitted for {diagnosis}. No significant past medical history. "
        "Vital signs stable throughout admission. Independent with ADLs. "
        "Strong family support, caregiver available 24/7. Follow-up scheduled with PCP. "
        "Goals of care met, medically stable for discharge.",

        "{age}yo {gender}, routine admission for {diagnosis}. Recovery proceeding as expected. "
        "Compliant with all treatments. Ambulatory, self-care independent. "
        "Well-nourished, good appetite. Discharge plan reviewed with patient and family. "
        "All follow-up appointments confirmed.",

        "Uncomplicated {diagnosis} admission. Patient is {age}yo {gender}. "
        "Improving steadily, stable for discharge. Motivated patient with strong support system. "
        "Cleared for discharge by all services. Transportation confirmed.",
    ],
}


def generate_patient_data(n_patients: int = None) -> tuple[pd.DataFrame, list[dict]]:
    """Generate realistic synthetic hospital patient data."""
    n = n_patients or settings.num_synthetic_patients
    logger.info(f"Generating {n} synthetic patients...")

    patients = []
    raw_records = []

    for i in range(n):
        patient = _generate_single_patient(i)
        patients.append(patient["features"])
        raw_records.append(patient["raw"])

    df = pd.DataFrame(patients)
    logger.info(f"Generated {len(df)} patients | Readmission rate: {df['readmitted_7d'].mean():.3f}")

    return df, raw_records


def _generate_single_patient(idx: int) -> dict:
    """Generate a single patient with realistic correlated features."""
    patient_id = f"PT-{idx + 1:05d}"

    # Demographics
    age = _generate_age()
    gender = np.random.choice(["Male", "Female"], p=[0.48, 0.52])
    gender_encoded = 1 if gender == "Male" else 0

    # Insurance (correlated with age)
    if age >= 65:
        insurance = np.random.choice(
            ["Medicare", "Medicare Advantage", "Private", "Medicaid"],
            p=[0.45, 0.25, 0.20, 0.10]
        )
    else:
        insurance = np.random.choice(
            ["Private", "Medicaid", "Medicare", "Self-Pay", "Other"],
            p=[0.45, 0.25, 0.10, 0.12, 0.08]
        )
    insurance_encoded = {"Private": 0, "Medicare": 1, "Medicare Advantage": 1,
                         "Medicaid": 2, "Self-Pay": 3, "Other": 4}.get(insurance, 4)

    # Chronic conditions (age-correlated)
    num_chronic = _generate_chronic_count(age)
    chronic_conditions = _select_chronic_conditions(num_chronic, age)

    # Binary chronic flags
    has_diabetes = int("Type 2 Diabetes" in chronic_conditions or "Type 1 Diabetes" in chronic_conditions)
    has_heart_failure = int("Heart Failure" in chronic_conditions)
    has_copd = int("COPD" in chronic_conditions)
    has_ckd = int("Chronic Kidney Disease" in chronic_conditions)
    has_hypertension = int("Hypertension" in chronic_conditions)
    has_depression = int("Depression" in chronic_conditions)
    has_afib = int("Atrial Fibrillation" in chronic_conditions)

    # Diagnosis
    diagnosis_code = _select_diagnosis(chronic_conditions, age)
    diagnosis_name = ICD10_MAPPINGS.get(diagnosis_code, "Other")

    # Admission history
    base_admission_rate = 0.3 + (num_chronic * 0.15) + (max(0, age - 60) * 0.005)
    num_previous_admissions = max(0, int(np.random.poisson(base_admission_rate * 3)))
    admissions_last_6months = min(num_previous_admissions,
                                   max(0, int(np.random.poisson(base_admission_rate * 1.5))))

    # Length of stay (correlated with severity)
    avg_los = 3 + num_chronic * 0.5 + (1 if age > 75 else 0)
    length_of_stay = max(1, int(np.random.lognormal(np.log(avg_los), 0.5)))
    length_of_stay = min(length_of_stay, 45)

    # Medications (correlated with chronic conditions)
    base_meds = num_chronic * 2 + (2 if has_diabetes else 0) + (2 if has_heart_failure else 0)
    medication_count = max(1, int(np.random.poisson(max(1, base_meds))))
    medication_count = min(medication_count, 25)

    # Missed appointments
    compliance_factor = np.random.beta(2, 5)  # Most patients are somewhat compliant
    missed_appointments = int(np.random.poisson(compliance_factor * 3))

    # Vital signs (realistic, correlated with conditions)
    vitals = _generate_vitals(age, chronic_conditions)

    # Lab results (correlated with conditions)
    labs = _generate_labs(age, chronic_conditions)

    # BMI
    if "Obesity" in chronic_conditions:
        bmi = round(np.random.normal(35, 5), 1)
    else:
        bmi = round(np.random.normal(26, 5), 1)
    bmi = max(15, min(55, bmi))

    # Smoking & alcohol
    smoking_status = np.random.choice(
        ["never", "former", "current"],
        p=[0.50, 0.30, 0.20] if has_copd else [0.60, 0.25, 0.15]
    )
    smoking_encoded = {"never": 0, "former": 1, "current": 2}[smoking_status]

    alcohol_use = np.random.choice(
        ["none", "social", "moderate", "heavy"],
        p=[0.40, 0.30, 0.20, 0.10]
    )
    alcohol_encoded = {"none": 0, "social": 1, "moderate": 2, "heavy": 3}[alcohol_use]

    # Social factors
    lives_alone = int(np.random.random() < (0.35 if age > 65 else 0.25))
    has_caregiver = int(np.random.random() < (0.6 if not lives_alone else 0.2))
    transportation_access = int(np.random.random() < 0.75)
    housing_stable = int(np.random.random() < 0.85)

    # Discharge timing
    discharge_date = fake.date_time_between(start_date="-90d", end_date="now")
    admission_date = discharge_date - timedelta(days=length_of_stay)
    discharge_hour = int(np.random.choice(range(8, 20), p=_discharge_hour_probs()))
    is_weekend_discharge = int(discharge_date.weekday() >= 5)

    # Computed risk features
    comorbidity_interaction_score = _compute_comorbidity_interaction(chronic_conditions)
    clinical_complexity_score = (
        num_chronic * 0.15 +
        (medication_count / 25) * 0.2 +
        (admissions_last_6months / 5) * 0.25 +
        (1 - vitals["oxygen_saturation"] / 100) * 0.2 +
        (missed_appointments / 5) * 0.2
    )
    clinical_complexity_score = min(1.0, max(0.0, clinical_complexity_score))

    social_vulnerability_score = (
        lives_alone * 0.25 +
        (1 - has_caregiver) * 0.25 +
        (1 - transportation_access) * 0.25 +
        (1 - housing_stable) * 0.25
    )

    vital_instability_score = _compute_vital_instability(vitals)
    lab_abnormality_score = _compute_lab_abnormality(labs)
    readmission_velocity = min(10, admissions_last_6months * 2)

    # --- READMISSION OUTCOME (target variable) ---
    readmission_prob = _compute_readmission_probability(
        age=age,
        num_chronic=num_chronic,
        admissions_6m=admissions_last_6months,
        length_of_stay=length_of_stay,
        medication_count=medication_count,
        missed_appointments=missed_appointments,
        lives_alone=lives_alone,
        has_caregiver=has_caregiver,
        vital_instability=vital_instability_score,
        lab_abnormality=lab_abnormality_score,
        clinical_complexity=clinical_complexity_score,
        social_vulnerability=social_vulnerability_score,
        has_diabetes=has_diabetes,
        has_heart_failure=has_heart_failure,
        has_copd=has_copd,
    )

    readmitted_7d = int(np.random.random() < readmission_prob)

    # Generate clinical notes based on risk
    if readmission_prob > 0.6:
        note_category = "high_risk"
    elif readmission_prob > 0.3:
        note_category = "medium_risk"
    else:
        note_category = "low_risk"

    clinical_notes = _generate_clinical_notes(
        note_category, age, gender, diagnosis_name,
        chronic_conditions, admissions_last_6months,
        missed_appointments, medication_count, bmi,
    )

    # Previous admission dates
    prev_admission_dates = []
    for j in range(num_previous_admissions):
        days_ago = np.random.randint(30, 365)
        prev_admission_dates.append(
            (datetime.now() - timedelta(days=days_ago)).isoformat()
        )

    features = {
        "age": age,
        "gender_encoded": gender_encoded,
        "length_of_stay": length_of_stay,
        "num_previous_admissions": num_previous_admissions,
        "admissions_last_6months": admissions_last_6months,
        "num_chronic_conditions": num_chronic,
        "medication_count": medication_count,
        "missed_appointments": missed_appointments,
        "has_diabetes": has_diabetes,
        "has_heart_failure": has_heart_failure,
        "has_copd": has_copd,
        "has_ckd": has_ckd,
        "has_hypertension": has_hypertension,
        "has_depression": has_depression,
        "has_afib": has_afib,
        "bp_systolic": vitals["bp_systolic"],
        "bp_diastolic": vitals["bp_diastolic"],
        "heart_rate": vitals["heart_rate"],
        "temperature": vitals["temperature"],
        "oxygen_saturation": vitals["oxygen_saturation"],
        "respiratory_rate": vitals["respiratory_rate"],
        "bmi": bmi,
        "hemoglobin": labs["hemoglobin"],
        "wbc_count": labs["wbc_count"],
        "creatinine": labs["creatinine"],
        "glucose": labs["glucose"],
        "bun": labs["bun"],
        "sodium": labs["sodium"],
        "potassium": labs["potassium"],
        "discharge_hour": discharge_hour,
        "is_weekend_discharge": is_weekend_discharge,
        "lives_alone": lives_alone,
        "has_caregiver": has_caregiver,
        "transportation_access": transportation_access,
        "housing_stable": housing_stable,
        "insurance_encoded": insurance_encoded,
        "smoking_encoded": smoking_encoded,
        "alcohol_encoded": alcohol_encoded,
        "comorbidity_interaction_score": round(comorbidity_interaction_score, 3),
        "clinical_complexity_score": round(clinical_complexity_score, 3),
        "social_vulnerability_score": round(social_vulnerability_score, 3),
        "vital_instability_score": round(vital_instability_score, 3),
        "lab_abnormality_score": round(lab_abnormality_score, 3),
        "readmission_velocity": readmission_velocity,
        "readmitted_7d": readmitted_7d,
    }

    raw = {
        "patient_id": patient_id,
        "name": fake.name(),
        "age": age,
        "gender": gender,
        "insurance": insurance,
        "diagnosis_code": diagnosis_code,
        "diagnosis_name": diagnosis_name,
        "chronic_conditions": chronic_conditions,
        "admission_date": admission_date.isoformat(),
        "discharge_date": discharge_date.isoformat(),
        "length_of_stay": length_of_stay,
        "num_previous_admissions": num_previous_admissions,
        "admissions_last_6months": admissions_last_6months,
        "medication_count": medication_count,
        "missed_appointments": missed_appointments,
        "vitals": vitals,
        "labs": labs,
        "bmi": bmi,
        "smoking_status": smoking_status,
        "alcohol_use": alcohol_use,
        "social_factors": {
            "lives_alone": bool(lives_alone),
            "has_caregiver": bool(has_caregiver),
            "transportation_access": bool(transportation_access),
            "housing_stable": bool(housing_stable),
        },
        "clinical_notes": clinical_notes,
        "discharge_hour": discharge_hour,
        "is_weekend_discharge": bool(is_weekend_discharge),
        "previous_admission_dates": prev_admission_dates,
        "readmitted_7d": bool(readmitted_7d),
        "ward": np.random.choice(["ICU", "Cardiology", "Pulmonology", "General Medicine",
                                    "Surgery", "Neurology", "Oncology", "Orthopedics"]),
    }

    return {"features": features, "raw": raw}


def _generate_age() -> int:
    """Generate age with realistic hospital distribution (skewed older)."""
    age = int(np.random.beta(5, 3) * 70 + 18)
    return max(18, min(100, age))


def _generate_chronic_count(age: int) -> int:
    """Generate number of chronic conditions correlated with age."""
    if age < 40:
        return max(0, int(np.random.poisson(0.5)))
    elif age < 60:
        return max(0, int(np.random.poisson(1.5)))
    elif age < 75:
        return max(0, int(np.random.poisson(2.5)))
    else:
        return max(0, int(np.random.poisson(3.5)))


def _select_chronic_conditions(n: int, age: int) -> list[str]:
    """Select chronic conditions with age-appropriate probabilities."""
    if n == 0:
        return []

    # Age-adjusted probabilities
    weights = []
    for condition in CHRONIC_CONDITIONS:
        w = 1.0
        if condition == "Hypertension" and age > 50:
            w = 3.0
        elif condition == "Type 2 Diabetes" and age > 45:
            w = 2.5
        elif condition == "Heart Failure" and age > 60:
            w = 2.0
        elif condition == "COPD" and age > 55:
            w = 2.0
        elif condition == "Dementia" and age > 70:
            w = 2.5
        elif condition == "Dementia" and age < 60:
            w = 0.1
        elif condition == "Coronary Artery Disease" and age > 55:
            w = 2.0
        weights.append(w)

    weights = np.array(weights)
    weights /= weights.sum()

    n = min(n, len(CHRONIC_CONDITIONS))
    selected = list(np.random.choice(CHRONIC_CONDITIONS, size=n, replace=False, p=weights))
    return selected


def _select_diagnosis(chronic_conditions: list, age: int) -> str:
    """Select primary diagnosis correlated with chronic conditions."""
    codes = list(ICD10_MAPPINGS.keys())

    # Bias towards related diagnoses
    if "Heart Failure" in chronic_conditions:
        if np.random.random() < 0.4:
            return "I50"
    if "COPD" in chronic_conditions:
        if np.random.random() < 0.35:
            return "J44"
    if "Type 2 Diabetes" in chronic_conditions:
        if np.random.random() < 0.3:
            return "E11"
    if "Chronic Kidney Disease" in chronic_conditions:
        if np.random.random() < 0.3:
            return "N18"

    return np.random.choice(codes)


def _generate_vitals(age: int, chronic_conditions: list) -> dict:
    """Generate realistic vital signs correlated with conditions."""
    bp_sys_base = 120 + (age - 50) * 0.3
    if "Hypertension" in chronic_conditions:
        bp_sys_base += 20

    bp_systolic = round(max(80, min(200, np.random.normal(bp_sys_base, 15))))
    bp_diastolic = round(max(50, min(120, np.random.normal(bp_systolic * 0.6, 8))))

    hr_base = 75
    if "Heart Failure" in chronic_conditions:
        hr_base += 10
    if "Atrial Fibrillation" in chronic_conditions:
        hr_base += 15
    heart_rate = round(max(45, min(150, np.random.normal(hr_base, 12))))

    temperature = round(np.random.normal(98.6, 0.5), 1)
    if np.random.random() < 0.08:  # Fever
        temperature = round(np.random.normal(101, 1), 1)

    o2_base = 97
    if "COPD" in chronic_conditions:
        o2_base = 93
    if "Heart Failure" in chronic_conditions:
        o2_base -= 1
    oxygen_saturation = round(max(82, min(100, np.random.normal(o2_base, 2))))

    rr_base = 16
    if "COPD" in chronic_conditions:
        rr_base += 4
    respiratory_rate = round(max(10, min(35, np.random.normal(rr_base, 3))))

    return {
        "bp_systolic": bp_systolic,
        "bp_diastolic": bp_diastolic,
        "heart_rate": heart_rate,
        "temperature": temperature,
        "oxygen_saturation": oxygen_saturation,
        "respiratory_rate": respiratory_rate,
    }


def _generate_labs(age: int, chronic_conditions: list) -> dict:
    """Generate realistic lab values correlated with conditions."""
    hemoglobin = round(np.random.normal(13.5, 1.5), 1)
    if "Chronic Kidney Disease" in chronic_conditions:
        hemoglobin -= 2

    wbc = round(np.random.normal(7.5, 2.5), 1)
    if np.random.random() < 0.1:
        wbc = round(np.random.normal(15, 3), 1)  # Infection

    creatinine = round(np.random.normal(1.0, 0.3), 2)
    if "Chronic Kidney Disease" in chronic_conditions:
        creatinine = round(np.random.normal(2.5, 1.0), 2)

    glucose = round(np.random.normal(100, 15))
    if "Type 2 Diabetes" in chronic_conditions:
        glucose = round(np.random.normal(180, 50))

    bun = round(np.random.normal(15, 5), 1)
    if "Chronic Kidney Disease" in chronic_conditions:
        bun = round(np.random.normal(35, 10), 1)

    sodium = round(np.random.normal(140, 3))
    if "Heart Failure" in chronic_conditions:
        sodium -= 3

    potassium = round(np.random.normal(4.2, 0.4), 1)
    if "Chronic Kidney Disease" in chronic_conditions:
        potassium += 0.5

    return {
        "hemoglobin": max(5, min(20, hemoglobin)),
        "wbc_count": max(1, min(30, wbc)),
        "creatinine": max(0.3, min(8, creatinine)),
        "glucose": max(40, min(500, glucose)),
        "bun": max(5, min(80, bun)),
        "sodium": max(120, min(155, sodium)),
        "potassium": max(2.5, min(7, potassium)),
    }


def _discharge_hour_probs():
    """Discharge hour probabilities (peak in afternoon)."""
    hours = list(range(8, 20))  # 8 AM to 7 PM
    probs = [0.03, 0.05, 0.08, 0.10, 0.12, 0.14, 0.13, 0.11, 0.09, 0.07, 0.05, 0.03]
    return probs


def _compute_comorbidity_interaction(conditions: list) -> float:
    """Compute comorbidity interaction score based on disease pairs."""
    high_risk_pairs = [
        ("Heart Failure", "Chronic Kidney Disease"),
        ("Heart Failure", "Type 2 Diabetes"),
        ("COPD", "Heart Failure"),
        ("Type 2 Diabetes", "Chronic Kidney Disease"),
        ("Hypertension", "Heart Failure"),
        ("Atrial Fibrillation", "Heart Failure"),
        ("Depression", "Heart Failure"),
        ("Coronary Artery Disease", "Type 2 Diabetes"),
    ]

    score = 0.0
    for c1, c2 in high_risk_pairs:
        if c1 in conditions and c2 in conditions:
            score += 0.15

    return min(1.0, score)


def _compute_vital_instability(vitals: dict) -> float:
    """Score how abnormal vital signs are."""
    score = 0.0

    if vitals["bp_systolic"] > 160 or vitals["bp_systolic"] < 90:
        score += 0.2
    if vitals["heart_rate"] > 100 or vitals["heart_rate"] < 50:
        score += 0.2
    if vitals["temperature"] > 100.4 or vitals["temperature"] < 96:
        score += 0.2
    if vitals["oxygen_saturation"] < 92:
        score += 0.25
    elif vitals["oxygen_saturation"] < 95:
        score += 0.1
    if vitals["respiratory_rate"] > 24 or vitals["respiratory_rate"] < 12:
        score += 0.15

    return min(1.0, score)


def _compute_lab_abnormality(labs: dict) -> float:
    """Score how abnormal lab values are."""
    score = 0.0

    if labs["hemoglobin"] < 10:
        score += 0.15
    if labs["wbc_count"] > 12 or labs["wbc_count"] < 4:
        score += 0.15
    if labs["creatinine"] > 1.5:
        score += 0.2
    if labs["glucose"] > 200 or labs["glucose"] < 70:
        score += 0.15
    if labs["bun"] > 25:
        score += 0.1
    if labs["sodium"] < 135 or labs["sodium"] > 145:
        score += 0.15
    if labs["potassium"] > 5.0 or labs["potassium"] < 3.5:
        score += 0.15

    return min(1.0, score)


def _compute_readmission_probability(
    age, num_chronic, admissions_6m, length_of_stay,
    medication_count, missed_appointments, lives_alone,
    has_caregiver, vital_instability, lab_abnormality,
    clinical_complexity, social_vulnerability,
    has_diabetes, has_heart_failure, has_copd,
) -> float:
    """Compute realistic readmission probability based on all factors."""
    # Base rate
    prob = settings.readmission_rate

    # Age effect
    if age > 80:
        prob += 0.08
    elif age > 70:
        prob += 0.05
    elif age > 60:
        prob += 0.02

    # Previous admissions (strongest predictor)
    prob += admissions_6m * 0.08

    # Chronic conditions
    prob += num_chronic * 0.03
    if has_heart_failure:
        prob += 0.06
    if has_copd:
        prob += 0.04
    if has_diabetes:
        prob += 0.03

    # Short stay (premature discharge risk)
    if length_of_stay <= 2:
        prob += 0.05
    elif length_of_stay >= 10:
        prob += 0.03  # Very long stays also risky

    # Polypharmacy
    if medication_count > 10:
        prob += 0.04
    elif medication_count > 7:
        prob += 0.02

    # Missed appointments
    prob += missed_appointments * 0.03

    # Social factors
    if lives_alone:
        prob += 0.04
    if not has_caregiver:
        prob += 0.03
    prob += social_vulnerability * 0.06

    # Clinical factors
    prob += vital_instability * 0.08
    prob += lab_abnormality * 0.06
    prob += clinical_complexity * 0.05

    # Add noise
    noise = np.random.normal(0, 0.04)
    prob += noise

    return max(0.02, min(0.95, prob))


def _generate_clinical_notes(
    risk_category, age, gender, diagnosis,
    chronic_conditions, prev_admissions, missed_appts,
    med_count, bmi,
) -> str:
    """Generate realistic clinical notes based on risk category."""
    templates = CLINICAL_NOTES_TEMPLATES[risk_category]
    template = np.random.choice(templates)

    chronic1 = chronic_conditions[0] if len(chronic_conditions) > 0 else "no significant PMH"
    chronic2 = chronic_conditions[1] if len(chronic_conditions) > 1 else "general deconditioning"

    notes = template.format(
        age=age,
        gender=gender.lower(),
        diagnosis=diagnosis,
        chronic1=chronic1,
        chronic2=chronic2,
        prev_admissions=prev_admissions,
        missed_appts=missed_appts,
        med_count=med_count,
        bmi=round(bmi, 1),
    )

    return notes
