"""
Asteric RiskIQ - Core Risk Scoring Service

Orchestrates all ML models to produce comprehensive risk assessments.
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional
from loguru import logger

from app.models.ensemble_engine import EnsembleEngine
from app.models.explainability import ExplainabilityEngine
from app.models.anomaly_detection import AnomalyDetector
from app.models.temporal_analysis import TemporalAnalyzer
from app.models.nlp_engine import ClinicalNLPEngine
from app.data.preprocessor import extract_features_from_raw, FEATURE_COLUMNS
from app.config import settings


class RiskScorer:
    """Central risk scoring service that orchestrates all AI models."""

    def __init__(self):
        self.ensemble = EnsembleEngine()
        self.explainer = ExplainabilityEngine(self.ensemble)
        self.anomaly_detector = AnomalyDetector()
        self.temporal_analyzer = TemporalAnalyzer()
        self.nlp_engine = ClinicalNLPEngine()
        self.is_ready = False
        self.patients_db: list[dict] = []
        self.risk_cache: dict = {}

    def initialize(self, X_train: pd.DataFrame, y_train: pd.Series, raw_patients: list[dict]):
        """Initialize all models with training data."""
        logger.info("Initializing Asteric RiskIQ Risk Scoring Engine...")

        # Train ensemble
        self.ensemble.train(X_train, y_train)

        # Initialize SHAP explainer
        self.explainer.initialize(X_train)

        # Fit anomaly detector
        target_col = "readmitted_7d"
        feature_cols = [c for c in X_train.columns if c != target_col]
        self.anomaly_detector.fit(X_train[feature_cols] if target_col in X_train.columns else X_train)

        # Store patient data
        self.patients_db = raw_patients

        # Pre-compute risk scores for all patients
        self._precompute_risks(X_train)

        self.is_ready = True
        logger.info("Risk Scoring Engine initialized successfully")

    def _precompute_risks(self, X: pd.DataFrame):
        """Pre-compute risk scores for all patients."""
        feature_cols = [c for c in FEATURE_COLUMNS if c in X.columns]
        X_features = X[feature_cols]

        probas = self.ensemble.predict_proba(X_features)
        multi_horizon = self.ensemble.predict_multi_horizon(X_features)

        for i, patient in enumerate(self.patients_db):
            if i >= len(probas):
                break

            score = round(float(probas[i]) * 100, 1)

            if score >= settings.risk_threshold_high:
                risk_level = "critical" if score >= 90 else "high"
            elif score >= settings.risk_threshold_medium:
                risk_level = "medium"
            else:
                risk_level = "low"

            patient["risk_score"] = score
            patient["risk_level"] = risk_level
            patient["risk_horizons"] = {
                k: round(float(v[i]) * 100, 1)
                for k, v in multi_horizon.items()
            }

    def score_patient(self, patient_id: str) -> Optional[dict]:
        """Get comprehensive risk assessment for a patient."""
        patient = self._find_patient(patient_id)
        if not patient:
            return None

        features = extract_features_from_raw(patient)
        feature_cols = [c for c in FEATURE_COLUMNS if c in features]
        ml_features = {k: features[k] for k in feature_cols}

        # Core prediction
        prediction = self.ensemble.predict_single(ml_features)

        # Explainability
        explanation = self.explainer.explain_patient(ml_features)

        # Anomaly detection
        anomaly = self.anomaly_detector.detect(ml_features)

        # NLP analysis
        nlp_result = self.nlp_engine.analyze_notes(patient.get("clinical_notes", ""))

        # Adjust score based on NLP
        nlp_modifier = nlp_result.get("risk_score_modifier", 0)
        adjusted_score = min(100, max(0, prediction["risk_score"] + nlp_modifier))

        # Temporal analysis
        trajectory = None
        if patient.get("previous_admission_dates"):
            velocity = self.temporal_analyzer.analyze_readmission_velocity(
                patient["previous_admission_dates"]
            )
        else:
            velocity = {"velocity_score": 0, "accelerating": False}

        # Similar patients
        similar = self.temporal_analyzer.find_similar_patients(
            features,
            [extract_features_from_raw(p) | {"patient_id": p["patient_id"],
                                               "risk_score": p.get("risk_score", 50),
                                               "was_readmitted": p.get("readmitted_7d", False)}
             for p in self.patients_db[:200]],
            top_k=5,
        )

        # Update risk level based on adjusted score
        if adjusted_score >= settings.risk_threshold_high:
            risk_level = "critical" if adjusted_score >= 90 else "high"
        elif adjusted_score >= settings.risk_threshold_medium:
            risk_level = "medium"
        else:
            risk_level = "low"

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
                "vitals": patient.get("vitals"),
                "labs": patient.get("labs"),
                "social_factors": patient.get("social_factors"),
                "bmi": patient.get("bmi"),
                "smoking_status": patient.get("smoking_status"),
                "alcohol_use": patient.get("alcohol_use"),
            },
            "risk_assessment": {
                "overall_score": adjusted_score,
                "raw_ml_score": prediction["risk_score"],
                "risk_level": risk_level,
                "confidence": prediction["confidence"],
                "horizons": prediction["horizons"],
                "model_breakdown": prediction["model_breakdown"],
                "nlp_modifier": nlp_modifier,
            },
            "explanation": {
                "top_factors": explanation.get("top_factors", [])[:10],
                "natural_language": explanation.get("natural_language", ""),
                "counterfactuals": explanation.get("counterfactuals", []),
            },
            "anomaly_detection": anomaly,
            "nlp_analysis": nlp_result,
            "readmission_velocity": velocity,
            "similar_patients": similar,
            "timestamp": datetime.now().isoformat(),
        }

    def get_all_patients(
        self,
        sort_by: str = "risk_score",
        risk_filter: Optional[str] = None,
        ward_filter: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """Get all patients with risk scores."""
        patients = self.patients_db.copy()

        # Apply filters
        if risk_filter and risk_filter != "all":
            patients = [p for p in patients if p.get("risk_level") == risk_filter]

        if ward_filter and ward_filter != "all":
            patients = [p for p in patients if p.get("ward") == ward_filter]

        if search:
            search_lower = search.lower()
            patients = [
                p for p in patients
                if search_lower in p.get("name", "").lower()
                or search_lower in p.get("patient_id", "").lower()
                or search_lower in p.get("diagnosis_name", "").lower()
            ]

        total = len(patients)

        # Sort
        reverse = True
        if sort_by == "name":
            patients.sort(key=lambda p: p.get("name", ""), reverse=False)
        elif sort_by == "age":
            patients.sort(key=lambda p: p.get("age", 0), reverse=True)
        elif sort_by == "discharge_date":
            patients.sort(key=lambda p: p.get("discharge_date", ""), reverse=True)
        else:
            patients.sort(key=lambda p: p.get("risk_score", 0), reverse=True)

        # Paginate
        patients = patients[offset:offset + limit]

        return {
            "patients": [
                {
                    "patient_id": p["patient_id"],
                    "name": p.get("name"),
                    "age": p.get("age"),
                    "gender": p.get("gender"),
                    "diagnosis": p.get("diagnosis_name"),
                    "diagnosis_code": p.get("diagnosis_code"),
                    "ward": p.get("ward"),
                    "chronic_conditions": p.get("chronic_conditions", []),
                    "length_of_stay": p.get("length_of_stay"),
                    "discharge_date": p.get("discharge_date"),
                    "risk_score": p.get("risk_score", 0),
                    "risk_level": p.get("risk_level", "low"),
                    "risk_horizons": p.get("risk_horizons", {}),
                    "admission_date": p.get("admission_date"),
                }
                for p in patients
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def get_dashboard_stats(self) -> dict:
        """Get aggregate dashboard statistics."""
        if not self.patients_db:
            return {}

        scores = [p.get("risk_score", 0) for p in self.patients_db]
        levels = [p.get("risk_level", "low") for p in self.patients_db]

        # Risk distribution
        risk_dist = {
            "critical": sum(1 for l in levels if l == "critical"),
            "high": sum(1 for l in levels if l == "high"),
            "medium": sum(1 for l in levels if l == "medium"),
            "low": sum(1 for l in levels if l == "low"),
        }

        # Ward distribution
        wards = {}
        for p in self.patients_db:
            ward = p.get("ward", "Unknown")
            if ward not in wards:
                wards[ward] = {"count": 0, "avg_risk": 0, "high_risk_count": 0}
            wards[ward]["count"] += 1
            wards[ward]["avg_risk"] += p.get("risk_score", 0)
            if p.get("risk_level") in ("high", "critical"):
                wards[ward]["high_risk_count"] += 1

        for ward in wards:
            if wards[ward]["count"] > 0:
                wards[ward]["avg_risk"] = round(wards[ward]["avg_risk"] / wards[ward]["count"], 1)

        # Age distribution
        ages = [p.get("age", 0) for p in self.patients_db]
        age_groups = {
            "18-30": sum(1 for a in ages if 18 <= a <= 30),
            "31-45": sum(1 for a in ages if 31 <= a <= 45),
            "46-60": sum(1 for a in ages if 46 <= a <= 60),
            "61-75": sum(1 for a in ages if 61 <= a <= 75),
            "76+": sum(1 for a in ages if a > 75),
        }

        # Diagnosis distribution
        diagnoses = {}
        for p in self.patients_db:
            dx = p.get("diagnosis_name", "Other")
            if dx not in diagnoses:
                diagnoses[dx] = 0
            diagnoses[dx] += 1
        top_diagnoses = sorted(diagnoses.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "total_patients": len(self.patients_db),
            "average_risk_score": round(float(np.mean(scores)), 1),
            "median_risk_score": round(float(np.median(scores)), 1),
            "high_risk_count": risk_dist["critical"] + risk_dist["high"],
            "risk_distribution": risk_dist,
            "ward_breakdown": wards,
            "age_distribution": age_groups,
            "top_diagnoses": [{"name": d[0], "count": d[1]} for d in top_diagnoses],
            "readmission_rate": round(
                sum(1 for p in self.patients_db if p.get("readmitted_7d")) / max(len(self.patients_db), 1) * 100,
                1,
            ),
            "model_performance": self.ensemble.get_model_performance(),
            "timestamp": datetime.now().isoformat(),
        }

    def get_risk_distribution_data(self) -> list[dict]:
        """Get risk score distribution for histogram."""
        scores = [p.get("risk_score", 0) for p in self.patients_db]
        bins = list(range(0, 105, 5))
        hist, _ = np.histogram(scores, bins=bins)

        return [
            {"range": f"{bins[i]}-{bins[i+1]}", "count": int(hist[i]),
             "min": bins[i], "max": bins[i+1]}
            for i in range(len(hist))
        ]

    def _find_patient(self, patient_id: str) -> Optional[dict]:
        for p in self.patients_db:
            if p["patient_id"] == patient_id:
                return p
        return None
