"""
Asteric RiskIQ - Production API Routes

All endpoints require authentication via session token.
Hospital staff login with their access code to get a session token.
"""

import csv
import io
import json
import os
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException, Header, UploadFile, File, Request
from typing import Optional
import pandas as pd
from loguru import logger

from app import database as db
from app.data.preprocessor import extract_features_from_raw, FEATURE_COLUMNS
from app.config import settings, ICD10_MAPPINGS

router = APIRouter(prefix="/api")


# --- Auth Helper ---

def get_hospital_id(authorization: Optional[str] = Header(None)) -> str:
    """Extract and validate session token from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Access code required. Please login.")

    token = authorization.replace("Bearer ", "").strip()
    session = db.validate_session(token)

    if not session:
        raise HTTPException(status_code=401, detail="Session expired or invalid. Please login again.")

    return session["hospital_id"]


# --- Authentication ---

@router.post("/auth/login")
async def login(request: Request):
    """Login with hospital access code."""
    body = await request.json()
    access_code = body.get("access_code", "").strip()

    if not access_code:
        raise HTTPException(status_code=400, detail="Access code is required")

    # Master founder code — always works, logs into the first hospital
    master_code = os.environ.get("DEFAULT_ACCESS_CODE", "ASTERIC2024RQ")
    if access_code.upper() == master_code.upper():
        conn = db.get_db()
        first = conn.execute("SELECT * FROM hospitals WHERE is_active = 1 ORDER BY created_at ASC LIMIT 1").fetchone()
        conn.close()
        if first:
            hospital = dict(first)
            token = db.create_session(hospital["id"])
            db.log_audit(hospital["id"], "LOGIN", "hospital", hospital["id"], "Founder login")
            return {
                "token": token,
                "hospital_id": hospital["id"],
                "hospital_name": hospital["name"],
                "message": "Login successful",
            }

    hospital = db.verify_access_code(access_code)
    if not hospital:
        raise HTTPException(status_code=401, detail="Invalid access code. Contact your Asteric RiskIQ representative.")

    token = db.create_session(hospital["id"])
    db.log_audit(hospital["id"], "LOGIN", "hospital", hospital["id"], "Staff login")

    return {
        "token": token,
        "hospital_id": hospital["id"],
        "hospital_name": hospital["name"],
        "message": "Login successful",
    }


@router.post("/auth/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """Logout and invalidate session."""
    if authorization:
        token = authorization.replace("Bearer ", "").strip()
        db.invalidate_session(token)
    return {"message": "Logged out"}


@router.get("/auth/verify")
async def verify_session(authorization: Optional[str] = Header(None)):
    """Verify if current session is valid."""
    hospital_id = get_hospital_id(authorization)
    conn = db.get_db()
    hospital = conn.execute("SELECT id, name, email FROM hospitals WHERE id = ?", (hospital_id,)).fetchone()
    conn.close()

    if not hospital:
        raise HTTPException(status_code=401, detail="Invalid session")

    return {
        "valid": True,
        "hospital_id": hospital["id"],
        "hospital_name": hospital["name"],
    }


# --- Dashboard ---

@router.get("/dashboard/stats")
async def dashboard_stats(authorization: Optional[str] = Header(None)):
    hospital_id = get_hospital_id(authorization)
    stats = db.get_dashboard_stats_db(hospital_id)
    from app.main import ensemble
    stats["model_performance"] = ensemble.get_model_performance() if ensemble.is_trained else {}
    stats["timestamp"] = datetime.now().isoformat()
    return stats


@router.get("/dashboard/risk-distribution")
async def risk_distribution(authorization: Optional[str] = Header(None)):
    hospital_id = get_hospital_id(authorization)
    conn = db.get_db()
    rows = conn.execute(
        "SELECT risk_score FROM patients WHERE hospital_id = ? AND risk_score IS NOT NULL",
        (hospital_id,)
    ).fetchall()
    conn.close()

    scores = [r["risk_score"] for r in rows]
    if not scores:
        return []

    import numpy as np
    bins = list(range(0, 105, 5))
    hist, _ = np.histogram(scores, bins=bins)
    return [
        {"range": f"{bins[i]}-{bins[i+1]}", "count": int(hist[i]), "min": bins[i], "max": bins[i+1]}
        for i in range(len(hist))
    ]


# --- Patients ---

@router.get("/patients")
async def list_patients(
    sort_by: str = Query("risk_score"),
    risk_filter: Optional[str] = Query(None),
    ward_filter: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    authorization: Optional[str] = Header(None),
):
    hospital_id = get_hospital_id(authorization)
    return db.get_patients_for_hospital(
        hospital_id, risk_filter=risk_filter, ward_filter=ward_filter,
        search=search, sort_by=sort_by, limit=limit, offset=offset,
    )


@router.post("/patients")
async def create_patient(request: Request, authorization: Optional[str] = Header(None)):
    """Add a new patient record and score immediately."""
    hospital_id = get_hospital_id(authorization)
    data = await request.json()
    result = db.add_patient(hospital_id, data)

    patient = db.get_patient_by_id(hospital_id, result["patient_id"])
    if patient:
        _score_single_patient(hospital_id, patient)

    db.log_audit(hospital_id, "CREATE_PATIENT", "patient", result["patient_id"])
    return result


@router.get("/patients/{patient_id}")
async def get_patient(patient_id: str, authorization: Optional[str] = Header(None)):
    """Get comprehensive risk assessment for a patient."""
    hospital_id = get_hospital_id(authorization)
    patient = db.get_patient_by_id(hospital_id, patient_id)

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    from app.main import ensemble, explainer, anomaly_detector, nlp_engine

    features = extract_features_from_raw(_patient_to_raw(patient))
    feature_cols = [c for c in FEATURE_COLUMNS if c in features]
    ml_features = {k: features[k] for k in feature_cols}

    risk_assessment = {"overall_score": 0, "raw_ml_score": 0, "risk_level": "pending",
                       "confidence": 0, "horizons": {}, "model_breakdown": {}, "nlp_modifier": 0}
    explanation = {"top_factors": [], "natural_language": "AI model not yet trained. Import patient data with known outcomes and click Train Model in Analytics.", "counterfactuals": []}
    anomaly = {"is_anomaly": False, "anomaly_score": 0, "anomalous_features": [], "total_anomalous_features": 0, "alert_level": "none"}

    if ensemble.is_trained:
        prediction = ensemble.predict_single(ml_features)
        risk_assessment = {
            "overall_score": prediction["risk_score"],
            "raw_ml_score": prediction["risk_score"],
            "risk_level": prediction["risk_level"],
            "confidence": prediction["confidence"],
            "horizons": prediction["horizons"],
            "model_breakdown": prediction["model_breakdown"],
            "nlp_modifier": 0,
        }
        try:
            explanation = explainer.explain_patient(ml_features)
        except Exception:
            explanation = {"top_factors": [], "natural_language": "Explanation generation in progress.", "counterfactuals": []}
        try:
            anomaly = anomaly_detector.detect(ml_features)
        except Exception:
            pass

    nlp_result = nlp_engine.analyze_notes(patient.get("clinical_notes", ""))

    if ensemble.is_trained:
        modifier = nlp_result.get("risk_score_modifier", 0)
        adjusted = min(100, max(0, risk_assessment["overall_score"] + modifier))
        risk_assessment["overall_score"] = adjusted
        risk_assessment["nlp_modifier"] = modifier
        if adjusted >= settings.risk_threshold_high:
            risk_assessment["risk_level"] = "critical" if adjusted >= 90 else "high"
        elif adjusted >= settings.risk_threshold_medium:
            risk_assessment["risk_level"] = "medium"
        else:
            risk_assessment["risk_level"] = "low"

    vitals = {k: patient.get(k) or v for k, v in [
        ("bp_systolic", 120), ("bp_diastolic", 80), ("heart_rate", 75),
        ("temperature", 98.6), ("oxygen_saturation", 97), ("respiratory_rate", 16),
    ]}
    labs = {k: patient.get(k) or v for k, v in [
        ("hemoglobin", 13.5), ("wbc_count", 7.5), ("creatinine", 1.0),
        ("glucose", 100), ("bun", 15), ("sodium", 140), ("potassium", 4.2),
    ]}
    social = {
        "lives_alone": bool(patient.get("lives_alone", 0)),
        "has_caregiver": bool(patient.get("has_caregiver", 1)),
        "transportation_access": bool(patient.get("transportation_access", 1)),
        "housing_stable": bool(patient.get("housing_stable", 1)),
    }

    return {
        "patient_id": patient_id,
        "patient_info": {
            "name": patient.get("name"),
            "age": patient.get("age"),
            "gender": patient.get("gender"),
            "diagnosis": patient.get("diagnosis_name"),
            "diagnosis_code": patient.get("diagnosis_code"),
            "ward": patient.get("ward"),
            "insurance": patient.get("insurance"),
            "admission_date": patient.get("admission_date"),
            "discharge_date": patient.get("discharge_date"),
            "length_of_stay": patient.get("length_of_stay"),
            "chronic_conditions": patient.get("chronic_conditions", []),
            "medication_count": patient.get("medication_count"),
            "vitals": vitals, "labs": labs, "social_factors": social,
            "bmi": patient.get("bmi"),
            "smoking_status": patient.get("smoking_status"),
            "alcohol_use": patient.get("alcohol_use"),
        },
        "risk_assessment": risk_assessment,
        "explanation": {
            "top_factors": explanation.get("top_factors", [])[:10],
            "natural_language": explanation.get("natural_language", ""),
            "counterfactuals": explanation.get("counterfactuals", []),
        },
        "anomaly_detection": anomaly,
        "nlp_analysis": nlp_result,
        "readmission_velocity": {"velocity_score": 0, "avg_days_between": None, "accelerating": False},
        "similar_patients": [],
        "timestamp": datetime.now().isoformat(),
    }


@router.put("/patients/{patient_id}")
async def update_patient_route(patient_id: str, request: Request, authorization: Optional[str] = Header(None)):
    hospital_id = get_hospital_id(authorization)
    data = await request.json()
    db.update_patient(hospital_id, patient_id, data)
    patient = db.get_patient_by_id(hospital_id, patient_id)
    if patient:
        _score_single_patient(hospital_id, patient)
    db.log_audit(hospital_id, "UPDATE_PATIENT", "patient", patient_id)
    return {"status": "updated", "patient_id": patient_id}


@router.delete("/patients/{patient_id}")
async def delete_patient_route(patient_id: str, authorization: Optional[str] = Header(None)):
    hospital_id = get_hospital_id(authorization)
    db.delete_patient(hospital_id, patient_id)
    db.log_audit(hospital_id, "DELETE_PATIENT", "patient", patient_id)
    return {"status": "deleted"}


@router.get("/patients/{patient_id}/interventions")
async def get_interventions(patient_id: str, authorization: Optional[str] = Header(None)):
    hospital_id = get_hospital_id(authorization)
    assessment = await get_patient(patient_id, authorization)
    from app.main import intervention_engine
    interventions = intervention_engine.recommend(assessment)
    return {
        "patient_id": patient_id,
        "risk_score": assessment["risk_assessment"]["overall_score"],
        "risk_level": assessment["risk_assessment"]["risk_level"],
        "interventions": interventions,
        "total_interventions": len(interventions),
    }


@router.get("/patients/{patient_id}/survival-curve")
async def patient_survival_curve(patient_id: str, authorization: Optional[str] = Header(None)):
    hospital_id = get_hospital_id(authorization)
    patient = db.get_patient_by_id(hospital_id, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    from app.main import temporal_analyzer
    risk_score = patient.get("risk_score", 50) or 50
    risk_level = patient.get("risk_level", "medium") or "medium"

    conn = db.get_db()
    rows = conn.execute(
        "SELECT risk_score, risk_level FROM patients WHERE hospital_id = ? AND risk_score IS NOT NULL", (hospital_id,)
    ).fetchall()
    conn.close()

    similar = [{"risk_score": r["risk_score"], "risk_level": r["risk_level"]} for r in rows
               if r["risk_score"] and abs(r["risk_score"] - risk_score) < 20]
    if len(similar) < 5:
        similar = [{"risk_score": risk_score, "risk_level": risk_level}] * 10

    curve = temporal_analyzer.compute_survival_curve(similar)
    curve["patient_risk_score"] = risk_score
    curve["patient_risk_level"] = risk_level
    return curve


# --- CSV Import ---

@router.post("/patients/import")
async def import_patients_csv(file: UploadFile = File(...), authorization: Optional[str] = Header(None)):
    """Import patients from a CSV file."""
    hospital_id = get_hospital_id(authorization)

    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")

    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    imported = 0
    errors = []

    for row_num, row in enumerate(reader, start=2):
        try:
            patient_data = _map_csv_row(row)
            if not patient_data.get("first_name") and not patient_data.get("last_name"):
                errors.append(f"Row {row_num}: Missing patient name")
                continue
            result = db.add_patient(hospital_id, patient_data)
            patient = db.get_patient_by_id(hospital_id, result["patient_id"])
            if patient:
                _score_single_patient(hospital_id, patient)
            imported += 1
        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")

    db.log_audit(hospital_id, "IMPORT_CSV", "patients", "", f"Imported {imported} patients")
    return {"imported": imported, "errors": errors[:20], "total_errors": len(errors),
            "message": f"Successfully imported {imported} patients"}


# --- Alerts ---

@router.get("/alerts")
async def list_alerts(
    status: Optional[str] = Query(None), priority: Optional[str] = Query(None),
    limit: int = Query(50), authorization: Optional[str] = Header(None),
):
    hospital_id = get_hospital_id(authorization)
    return db.get_alerts_db(hospital_id, status=status, priority=priority, limit=limit)


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, authorization: Optional[str] = Header(None)):
    hospital_id = get_hospital_id(authorization)
    db.update_alert_status(hospital_id, alert_id, "acknowledged")
    return {"status": "acknowledged"}


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, authorization: Optional[str] = Header(None)):
    hospital_id = get_hospital_id(authorization)
    db.update_alert_status(hospital_id, alert_id, "resolved")
    return {"status": "resolved"}


# --- Analytics ---

@router.get("/analytics/model-performance")
async def model_performance(authorization: Optional[str] = Header(None)):
    get_hospital_id(authorization)
    from app.main import ensemble
    if not ensemble.is_trained:
        return {"message": "Model not yet trained. Add patient records with known outcomes then train the model."}
    return ensemble.get_model_performance()


@router.get("/analytics/feature-importance")
async def feature_importance(authorization: Optional[str] = Header(None)):
    get_hospital_id(authorization)
    from app.main import ensemble, explainer
    if not ensemble.is_trained:
        return {"global_importances": []}
    return explainer.get_global_importance()


@router.get("/analytics/seasonal-patterns")
async def seasonal_patterns(authorization: Optional[str] = Header(None)):
    hospital_id = get_hospital_id(authorization)
    conn = db.get_db()
    rows = conn.execute(
        "SELECT admission_date FROM patients WHERE hospital_id = ? AND admission_date IS NOT NULL", (hospital_id,)
    ).fetchall()
    conn.close()
    from app.main import temporal_analyzer
    return temporal_analyzer.detect_seasonal_patterns([{"admission_date": r["admission_date"]} for r in rows])


@router.get("/analytics/drift-detection")
async def drift_detection(authorization: Optional[str] = Header(None)):
    hospital_id = get_hospital_id(authorization)
    from app.main import ensemble
    if not ensemble.is_trained:
        return {"drift_detected": False, "recommendation": "MODEL_NOT_TRAINED"}
    conn = db.get_db()
    rows = conn.execute("SELECT * FROM patients WHERE hospital_id = ? LIMIT 500", (hospital_id,)).fetchall()
    conn.close()
    if len(rows) < 10:
        return {"drift_detected": False, "recommendation": "INSUFFICIENT_DATA"}
    features_list = []
    for r in rows:
        p = dict(r)
        p["chronic_conditions"] = json.loads(p.get("chronic_conditions") or "[]")
        features = extract_features_from_raw(_patient_to_raw(p))
        features_list.append({k: features[k] for k in FEATURE_COLUMNS if k in features})
    return ensemble.detect_drift(pd.DataFrame(features_list))


@router.post("/model/train")
async def train_model(authorization: Optional[str] = Header(None)):
    """Train the AI model on this hospital's patient data."""
    hospital_id = get_hospital_id(authorization)
    conn = db.get_db()
    rows = conn.execute(
        "SELECT * FROM patients WHERE hospital_id = ? AND was_readmitted IS NOT NULL", (hospital_id,)
    ).fetchall()
    conn.close()

    if len(rows) < 50:
        raise HTTPException(status_code=400,
            detail=f"Need at least 50 patients with known readmission outcomes. Currently have {len(rows)}.")

    features_list, targets = [], []
    for r in rows:
        p = dict(r)
        p["chronic_conditions"] = json.loads(p.get("chronic_conditions") or "[]")
        features = extract_features_from_raw(_patient_to_raw(p))
        features_list.append({k: features[k] for k in FEATURE_COLUMNS if k in features})
        targets.append(int(p.get("was_readmitted", 0) or 0))

    X, y = pd.DataFrame(features_list), pd.Series(targets)
    from app.main import ensemble, explainer, anomaly_detector
    metrics = ensemble.train(X, y)
    ensemble.save()
    explainer.ensemble = ensemble
    try:
        explainer.initialize(X)
    except Exception:
        pass
    try:
        anomaly_detector.fit(X)
    except Exception:
        pass

    _rescore_all_patients(hospital_id)
    db.log_audit(hospital_id, "TRAIN_MODEL", "model", "", f"Trained on {len(rows)} patients")
    return {"status": "trained", "samples": len(rows), "metrics": metrics}


# --- System ---

@router.get("/system/health")
async def health_check():
    from app.main import ensemble
    return {"status": "healthy", "version": "1.0.0", "models_loaded": ensemble.is_trained}


@router.get("/system/icd10")
async def icd10_codes(authorization: Optional[str] = Header(None)):
    get_hospital_id(authorization)
    return ICD10_MAPPINGS


# --- Helpers ---

def _patient_to_raw(patient: dict) -> dict:
    chronic = patient.get("chronic_conditions", [])
    if isinstance(chronic, str):
        chronic = json.loads(chronic)
    return {
        "age": patient.get("age", 50), "gender": patient.get("gender", ""),
        "insurance": patient.get("insurance", ""),
        "diagnosis_code": patient.get("diagnosis_code", ""),
        "diagnosis_name": patient.get("diagnosis_name", ""),
        "chronic_conditions": chronic,
        "length_of_stay": patient.get("length_of_stay", 0),
        "num_previous_admissions": patient.get("num_previous_admissions", 0),
        "admissions_last_6months": patient.get("admissions_last_6months", 0),
        "medication_count": patient.get("medication_count", 0),
        "missed_appointments": patient.get("missed_appointments", 0),
        "vitals": {"bp_systolic": patient.get("bp_systolic", 120), "bp_diastolic": patient.get("bp_diastolic", 80),
                   "heart_rate": patient.get("heart_rate", 75), "temperature": patient.get("temperature", 98.6),
                   "oxygen_saturation": patient.get("oxygen_saturation", 97), "respiratory_rate": patient.get("respiratory_rate", 16)},
        "labs": {"hemoglobin": patient.get("hemoglobin", 13.5), "wbc_count": patient.get("wbc_count", 7.5),
                 "creatinine": patient.get("creatinine", 1.0), "glucose": patient.get("glucose", 100),
                 "bun": patient.get("bun", 15), "sodium": patient.get("sodium", 140), "potassium": patient.get("potassium", 4.2)},
        "bmi": patient.get("bmi", 26), "smoking_status": patient.get("smoking_status", "unknown"),
        "alcohol_use": patient.get("alcohol_use", "unknown"),
        "social_factors": {"lives_alone": bool(patient.get("lives_alone", 0)), "has_caregiver": bool(patient.get("has_caregiver", 1)),
                           "transportation_access": bool(patient.get("transportation_access", 1)), "housing_stable": bool(patient.get("housing_stable", 1))},
        "discharge_hour": patient.get("discharge_hour", 14), "is_weekend_discharge": bool(patient.get("is_weekend_discharge", 0)),
        "clinical_notes": patient.get("clinical_notes", ""),
    }


def _score_single_patient(hospital_id: str, patient: dict):
    from app.main import ensemble
    if not ensemble.is_trained:
        return
    raw = _patient_to_raw(patient)
    features = extract_features_from_raw(raw)
    ml_features = {k: features[k] for k in FEATURE_COLUMNS if k in features}
    try:
        prediction = ensemble.predict_single(ml_features)
        pid = patient.get("patient_id") or patient.get("id")
        db.update_patient_risk(pid, prediction["risk_score"], prediction["risk_level"], prediction["horizons"])
        if prediction["risk_level"] in ("high", "critical"):
            name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
            db.add_alert(hospital_id, pid, "high_risk_discharge",
                "critical" if prediction["risk_level"] == "critical" else "high",
                f"{name} | Risk: {prediction['risk_score']}% | {patient.get('diagnosis_name', '')}")
    except Exception as e:
        logger.error(f"Failed to score patient: {e}")


def _rescore_all_patients(hospital_id: str):
    result = db.get_patients_for_hospital(hospital_id, limit=10000)
    for patient in result["patients"]:
        _score_single_patient(hospital_id, patient)


def _map_csv_row(row: dict) -> dict:
    def get(keys, default=""):
        for k in keys:
            if row.get(k): return row[k]
        return default
    def get_num(keys, default=None):
        val = get(keys, "")
        try: return float(val) if val else default
        except ValueError: return default
    def get_int(keys, default=0):
        val = get(keys, "")
        try: return int(float(val)) if val else default
        except ValueError: return default

    chronic_raw = get(["chronic_conditions", "chronic", "comorbidities"], "")
    chronic = [c.strip() for c in chronic_raw.split(";") if c.strip()] if chronic_raw else []

    return {
        "mrn": get(["mrn", "MRN", "medical_record_number"]),
        "first_name": get(["first_name", "firstName", "First Name"]),
        "last_name": get(["last_name", "lastName", "Last Name"]),
        "date_of_birth": get(["date_of_birth", "dob", "DOB"]),
        "age": get_int(["age", "Age"]),
        "gender": get(["gender", "Gender", "sex"]),
        "insurance": get(["insurance", "Insurance", "payer"]),
        "diagnosis_code": get(["diagnosis_code", "icd10", "ICD10"]),
        "diagnosis_name": get(["diagnosis_name", "diagnosis", "Diagnosis"]),
        "chronic_conditions": chronic,
        "admission_date": get(["admission_date", "admit_date"]),
        "discharge_date": get(["discharge_date", "discharge"]),
        "length_of_stay": get_int(["length_of_stay", "los", "LOS"]),
        "ward": get(["ward", "unit", "department"]),
        "num_previous_admissions": get_int(["num_previous_admissions", "prev_admissions"]),
        "admissions_last_6months": get_int(["admissions_last_6months", "recent_admissions"]),
        "medication_count": get_int(["medication_count", "medications"]),
        "missed_appointments": get_int(["missed_appointments", "no_shows"]),
        "bp_systolic": get_num(["bp_systolic", "systolic"]),
        "bp_diastolic": get_num(["bp_diastolic", "diastolic"]),
        "heart_rate": get_num(["heart_rate", "hr", "pulse"]),
        "temperature": get_num(["temperature", "temp"]),
        "oxygen_saturation": get_num(["oxygen_saturation", "spo2", "SpO2"]),
        "respiratory_rate": get_num(["respiratory_rate", "rr"]),
        "bmi": get_num(["bmi", "BMI"]),
        "hemoglobin": get_num(["hemoglobin", "hgb"]),
        "wbc_count": get_num(["wbc_count", "wbc"]),
        "creatinine": get_num(["creatinine"]),
        "glucose": get_num(["glucose"]),
        "bun": get_num(["bun", "BUN"]),
        "sodium": get_num(["sodium"]),
        "potassium": get_num(["potassium"]),
        "smoking_status": get(["smoking_status", "smoking"]),
        "alcohol_use": get(["alcohol_use", "alcohol"]),
        "lives_alone": get(["lives_alone"]).lower() in ("true", "yes", "1"),
        "has_caregiver": get(["has_caregiver"], "true").lower() in ("true", "yes", "1"),
        "transportation_access": get(["transportation_access"], "true").lower() in ("true", "yes", "1"),
        "housing_stable": get(["housing_stable"], "true").lower() in ("true", "yes", "1"),
        "clinical_notes": get(["clinical_notes", "notes"]),
        "was_readmitted": get(["was_readmitted", "readmitted"]).lower() in ("true", "yes", "1") if get(["was_readmitted", "readmitted"]) else None,
        "status": get(["status"], "discharged"),
    }
