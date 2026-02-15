"""Asteric RiskIQ - Configuration Management"""
from pydantic import BaseModel
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data_store"
MODEL_DIR = BASE_DIR / "trained_models"
REPORTS_DIR = BASE_DIR / "reports"

DATA_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)


def _parse_origins() -> list[str]:
    """Parse CORS origins from environment or use defaults."""
    env_origins = os.getenv("CORS_ORIGINS", "")
    origins = [o.strip() for o in env_origins.split(",") if o.strip()] if env_origins else []
    # Production frontend
    origins.append("https://asteric-riskiq-51t5.vercel.app")
    # Localhost for development
    origins.extend([
        "http://localhost:4000",
        "http://127.0.0.1:4000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ])
    return list(set(origins))


class Settings(BaseModel):
    app_name: str = "Asteric RiskIQ"
    version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    # ML Configuration
    ensemble_models: list[str] = [
        "xgboost",
        "lightgbm",
        "random_forest",
        "gradient_boosting",
        "neural_network",
    ]
    ensemble_weights: list[float] = [0.30, 0.25, 0.20, 0.15, 0.10]
    model_retrain_interval_hours: int = 24
    prediction_horizons: list[int] = [1, 3, 7, 30]  # days

    # Risk Thresholds
    risk_threshold_low: float = 30.0
    risk_threshold_medium: float = 55.0
    risk_threshold_high: float = 75.0

    # Alert Configuration
    alert_cooldown_minutes: int = 60
    max_alerts_per_patient: int = 5

    # Readmission rate
    readmission_rate: float = 0.18  # ~18% national average

    # WebSocket
    ws_heartbeat_interval: int = 30

    # SHAP Configuration
    shap_max_display: int = 15
    shap_background_samples: int = 100

    # Anomaly Detection
    anomaly_contamination: float = 0.05

    # Security
    secret_key: str = os.getenv("SECRET_KEY", "asteric-riskiq-dev-key-change-in-production")

    # CORS - reads from CORS_ORIGINS env var (comma-separated)
    allowed_origins: list[str] = _parse_origins()


settings = Settings()

# ICD-10 Code Mappings for readable diagnoses
ICD10_MAPPINGS = {
    "I50": "Heart Failure",
    "J44": "COPD",
    "E11": "Type 2 Diabetes",
    "N18": "Chronic Kidney Disease",
    "I25": "Chronic Ischemic Heart Disease",
    "J18": "Pneumonia",
    "I10": "Essential Hypertension",
    "K70": "Alcoholic Liver Disease",
    "I21": "Acute Myocardial Infarction",
    "I63": "Cerebral Infarction",
    "J96": "Respiratory Failure",
    "E10": "Type 1 Diabetes",
    "N17": "Acute Kidney Failure",
    "A41": "Sepsis",
    "K85": "Acute Pancreatitis",
    "I48": "Atrial Fibrillation",
    "J45": "Asthma",
    "K21": "GERD",
    "M17": "Osteoarthritis of Knee",
    "G20": "Parkinson's Disease",
    "F32": "Major Depressive Disorder",
    "C34": "Lung Cancer",
    "C50": "Breast Cancer",
    "K57": "Diverticular Disease",
    "I26": "Pulmonary Embolism",
}

CHRONIC_CONDITIONS = [
    "Hypertension",
    "Type 2 Diabetes",
    "Heart Failure",
    "COPD",
    "Chronic Kidney Disease",
    "Atrial Fibrillation",
    "Coronary Artery Disease",
    "Asthma",
    "Depression",
    "Obesity",
    "Osteoarthritis",
    "Hypothyroidism",
    "Anxiety Disorder",
    "Peripheral Vascular Disease",
    "Dementia",
]

INTERVENTION_CATALOG = {
    "delay_discharge": {
        "name": "Delay Discharge",
        "description": "Extend stay by 24-48 hours for additional monitoring",
        "priority": "high",
        "evidence_level": "A",
        "cost_category": "medium",
    },
    "nurse_followup": {
        "name": "Extra Nurse Check",
        "description": "Schedule additional nursing assessments post-discharge",
        "priority": "medium",
        "evidence_level": "A",
        "cost_category": "low",
    },
    "phone_followup_24h": {
        "name": "Follow-up Call in 24h",
        "description": "Automated or nurse-led phone call within 24 hours",
        "priority": "medium",
        "evidence_level": "B",
        "cost_category": "low",
    },
    "phone_followup_72h": {
        "name": "Follow-up Call in 72h",
        "description": "Check-in call at 72 hours post-discharge",
        "priority": "low",
        "evidence_level": "B",
        "cost_category": "low",
    },
    "home_visit": {
        "name": "Home Visit",
        "description": "Schedule home health visit within 7 days",
        "priority": "high",
        "evidence_level": "A",
        "cost_category": "high",
    },
    "telehealth": {
        "name": "Telehealth Follow-up",
        "description": "Virtual visit within 48-72 hours",
        "priority": "medium",
        "evidence_level": "B",
        "cost_category": "low",
    },
    "medication_reconciliation": {
        "name": "Medication Reconciliation",
        "description": "Pharmacist review of all medications pre-discharge",
        "priority": "high",
        "evidence_level": "A",
        "cost_category": "medium",
    },
    "care_coordinator": {
        "name": "Assign Care Coordinator",
        "description": "Dedicated care coordinator for 30-day transition",
        "priority": "high",
        "evidence_level": "A",
        "cost_category": "high",
    },
    "patient_education": {
        "name": "Enhanced Patient Education",
        "description": "Comprehensive discharge education with teach-back",
        "priority": "medium",
        "evidence_level": "B",
        "cost_category": "low",
    },
    "social_work_consult": {
        "name": "Social Work Consult",
        "description": "Address social determinants before discharge",
        "priority": "medium",
        "evidence_level": "B",
        "cost_category": "medium",
    },
    "rapid_clinic_appointment": {
        "name": "Rapid Clinic Appointment",
        "description": "Schedule PCP visit within 7 days of discharge",
        "priority": "high",
        "evidence_level": "A",
        "cost_category": "low",
    },
    "remote_monitoring": {
        "name": "Remote Patient Monitoring",
        "description": "IoT device monitoring for vitals post-discharge",
        "priority": "high",
        "evidence_level": "A",
        "cost_category": "high",
    },
}
