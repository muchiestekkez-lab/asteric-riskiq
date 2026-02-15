"""
Asteric RiskIQ - Explainable AI Engine

Uses SHAP (SHapley Additive exPlanations) to provide:
- Per-patient risk factor breakdown
- Global feature importance
- Feature interaction analysis
- Counterfactual explanations ("what would need to change?")
- Natural language explanations
"""

import numpy as np
import pandas as pd
import shap
from typing import Optional
from loguru import logger

from app.models.ensemble_engine import EnsembleEngine


# Human-readable feature name mappings
FEATURE_DISPLAY_NAMES = {
    "age": "Patient Age",
    "gender_encoded": "Gender",
    "length_of_stay": "Length of Stay",
    "num_previous_admissions": "Previous Admissions (Total)",
    "admissions_last_6months": "Admissions in Last 6 Months",
    "num_chronic_conditions": "Number of Chronic Conditions",
    "medication_count": "Number of Medications",
    "missed_appointments": "Missed Appointments",
    "has_diabetes": "Diabetes",
    "has_heart_failure": "Heart Failure",
    "has_copd": "COPD",
    "has_ckd": "Chronic Kidney Disease",
    "has_hypertension": "Hypertension",
    "has_depression": "Depression",
    "has_afib": "Atrial Fibrillation",
    "bp_systolic": "Blood Pressure (Systolic)",
    "bp_diastolic": "Blood Pressure (Diastolic)",
    "heart_rate": "Heart Rate",
    "temperature": "Body Temperature",
    "oxygen_saturation": "Oxygen Saturation",
    "respiratory_rate": "Respiratory Rate",
    "bmi": "Body Mass Index",
    "hemoglobin": "Hemoglobin Level",
    "wbc_count": "White Blood Cell Count",
    "creatinine": "Creatinine Level",
    "glucose": "Blood Glucose",
    "bun": "Blood Urea Nitrogen",
    "sodium": "Sodium Level",
    "potassium": "Potassium Level",
    "discharge_hour": "Discharge Hour",
    "is_weekend_discharge": "Weekend Discharge",
    "lives_alone": "Lives Alone",
    "has_caregiver": "Has Caregiver",
    "transportation_access": "Transportation Access",
    "housing_stable": "Stable Housing",
    "insurance_encoded": "Insurance Type",
    "smoking_encoded": "Smoking Status",
    "alcohol_encoded": "Alcohol Use",
    "comorbidity_interaction_score": "Comorbidity Interaction Score",
    "clinical_complexity_score": "Clinical Complexity Score",
    "social_vulnerability_score": "Social Vulnerability Score",
    "vital_instability_score": "Vital Sign Instability",
    "lab_abnormality_score": "Lab Abnormality Score",
    "readmission_velocity": "Readmission Velocity",
}


class ExplainabilityEngine:
    """SHAP-based explainability for patient risk predictions."""

    def __init__(self, ensemble: EnsembleEngine):
        self.ensemble = ensemble
        self.explainer: Optional[shap.Explainer] = None
        self.background_data: Optional[pd.DataFrame] = None

    def initialize(self, X_background: pd.DataFrame):
        """Initialize SHAP explainer with background data."""
        n_samples = min(100, len(X_background))
        self.background_data = X_background.sample(n=n_samples, random_state=42)

        # Scale background data
        bg_scaled = self.ensemble.scaler.transform(self.background_data)
        bg_scaled_df = pd.DataFrame(bg_scaled, columns=self.ensemble.feature_names)

        # Use the best-performing tree model for SHAP (XGBoost)
        if "xgboost" in self.ensemble.models:
            self.explainer = shap.TreeExplainer(
                self.ensemble.models["xgboost"],
                bg_scaled_df,
            )
        else:
            # Fallback to KernelSHAP
            def predict_fn(X):
                X_df = pd.DataFrame(X, columns=self.ensemble.feature_names)
                X_orig = self.ensemble.scaler.inverse_transform(X_df)
                X_orig_df = pd.DataFrame(X_orig, columns=self.ensemble.feature_names)
                return self.ensemble.predict_proba(X_orig_df)

            self.explainer = shap.KernelExplainer(predict_fn, bg_scaled_df)

        logger.info("SHAP explainer initialized")

    def explain_patient(self, features: dict, top_k: int = 10) -> dict:
        """Generate comprehensive explanation for a single patient."""
        if self.explainer is None:
            return {"error": "Explainer not initialized"}

        X = pd.DataFrame([features])[self.ensemble.feature_names]
        X_scaled = self.ensemble.scaler.transform(X)
        X_scaled_df = pd.DataFrame(X_scaled, columns=self.ensemble.feature_names)

        # Get SHAP values
        shap_values = self.explainer.shap_values(X_scaled_df)

        # Handle different SHAP output formats
        if isinstance(shap_values, list):
            # Binary classification returns [class_0, class_1]
            sv = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
        elif isinstance(shap_values, np.ndarray):
            if shap_values.ndim == 3:
                sv = shap_values[0, :, 1]
            else:
                sv = shap_values[0]
        else:
            sv = np.array(shap_values.values[0])

        # Build factor breakdown
        factors = []
        for i, feat in enumerate(self.ensemble.feature_names):
            shap_val = float(sv[i])
            raw_val = float(X.iloc[0][feat])
            display_name = FEATURE_DISPLAY_NAMES.get(feat, feat.replace("_", " ").title())

            factors.append({
                "feature": feat,
                "display_name": display_name,
                "shap_value": round(shap_val, 4),
                "raw_value": round(raw_val, 2),
                "impact": "increases" if shap_val > 0 else "decreases",
                "abs_impact": abs(shap_val),
            })

        # Sort by absolute impact
        factors.sort(key=lambda x: x["abs_impact"], reverse=True)

        # Generate natural language explanation
        top_factors = factors[:top_k]
        explanation = self._generate_explanation(top_factors, features)

        # Generate counterfactual insights
        counterfactuals = self._generate_counterfactuals(factors, features)

        return {
            "top_factors": top_factors[:top_k],
            "all_factors": factors,
            "natural_language": explanation,
            "counterfactuals": counterfactuals,
            "base_value": float(self.explainer.expected_value[1])
            if isinstance(self.explainer.expected_value, (list, np.ndarray))
            else float(self.explainer.expected_value),
            "shap_sum": round(float(np.sum(sv)), 4),
        }

    def _generate_explanation(self, top_factors: list, features: dict) -> str:
        """Generate human-readable natural language explanation."""
        increasing = [f for f in top_factors if f["impact"] == "increases"]
        decreasing = [f for f in top_factors if f["impact"] == "decreases"]

        parts = []

        if increasing:
            risk_drivers = []
            for f in increasing[:5]:
                name = f["display_name"]
                val = f["raw_value"]

                if f["feature"] == "admissions_last_6months" and val > 0:
                    risk_drivers.append(f"{int(val)} admission(s) in the last 6 months")
                elif f["feature"] == "num_chronic_conditions" and val > 2:
                    risk_drivers.append(f"{int(val)} chronic conditions")
                elif f["feature"] == "length_of_stay":
                    risk_drivers.append(f"{'short' if val < 3 else 'extended'} hospital stay ({int(val)} days)")
                elif f["feature"] == "missed_appointments" and val > 0:
                    risk_drivers.append(f"{int(val)} missed appointment(s)")
                elif f["feature"] == "age" and val > 65:
                    risk_drivers.append(f"advanced age ({int(val)})")
                elif f["feature"] == "medication_count" and val > 8:
                    risk_drivers.append(f"polypharmacy ({int(val)} medications)")
                elif f["feature"] == "lives_alone" and val == 1:
                    risk_drivers.append("lives alone")
                elif f["feature"].startswith("has_") and val == 1:
                    condition = name
                    risk_drivers.append(condition)
                elif f["feature"] == "oxygen_saturation" and val < 95:
                    risk_drivers.append(f"low oxygen saturation ({val}%)")
                elif f["feature"] == "vital_instability_score":
                    risk_drivers.append("unstable vital signs")
                elif f["feature"] == "comorbidity_interaction_score":
                    risk_drivers.append("high comorbidity interactions")
                else:
                    risk_drivers.append(f"{name}: {val}")

            if risk_drivers:
                parts.append("Risk increased by: " + "; ".join(risk_drivers))

        if decreasing:
            protective = []
            for f in decreasing[:3]:
                name = f["display_name"]
                val = f["raw_value"]

                if f["feature"] == "has_caregiver" and val == 1:
                    protective.append("has caregiver support")
                elif f["feature"] == "transportation_access" and val == 1:
                    protective.append("has transportation access")
                elif f["feature"] == "housing_stable" and val == 1:
                    protective.append("stable housing")
                elif f["feature"] == "oxygen_saturation" and val >= 97:
                    protective.append(f"good oxygen levels ({val}%)")
                else:
                    protective.append(f"{name}")

            if protective:
                parts.append("Protective factors: " + "; ".join(protective))

        return " | ".join(parts) if parts else "Risk factors are within normal ranges."

    def _generate_counterfactuals(self, factors: list, features: dict) -> list:
        """Generate actionable counterfactual explanations."""
        counterfactuals = []

        # Only look at top risk-increasing factors
        risk_factors = [f for f in factors if f["impact"] == "increases"][:8]

        for f in risk_factors:
            feat = f["feature"]
            val = f["raw_value"]

            # Generate actionable counterfactuals for modifiable factors
            if feat == "missed_appointments" and val > 0:
                counterfactuals.append({
                    "factor": f["display_name"],
                    "current": f"{int(val)} missed",
                    "target": "0 missed",
                    "action": "Improve appointment adherence through reminders and transportation assistance",
                    "estimated_risk_reduction": round(f["abs_impact"] * 100, 1),
                })
            elif feat == "medication_count" and val > 10:
                counterfactuals.append({
                    "factor": f["display_name"],
                    "current": f"{int(val)} medications",
                    "target": "Optimized regimen",
                    "action": "Pharmacist medication reconciliation to reduce polypharmacy",
                    "estimated_risk_reduction": round(f["abs_impact"] * 70, 1),
                })
            elif feat == "lives_alone" and val == 1:
                counterfactuals.append({
                    "factor": f["display_name"],
                    "current": "Yes",
                    "target": "Support system",
                    "action": "Arrange home health aide or community support services",
                    "estimated_risk_reduction": round(f["abs_impact"] * 80, 1),
                })
            elif feat == "length_of_stay" and val < 3:
                counterfactuals.append({
                    "factor": f["display_name"],
                    "current": f"{int(val)} days",
                    "target": f"{int(val) + 1}-{int(val) + 2} days",
                    "action": "Consider extending stay for additional stabilization",
                    "estimated_risk_reduction": round(f["abs_impact"] * 60, 1),
                })
            elif feat == "has_caregiver" and val == 0:
                counterfactuals.append({
                    "factor": "No Caregiver",
                    "current": "No caregiver",
                    "target": "Caregiver assigned",
                    "action": "Connect with family or assign professional caregiver",
                    "estimated_risk_reduction": round(f["abs_impact"] * 75, 1),
                })
            elif feat == "vital_instability_score" and val > 0.3:
                counterfactuals.append({
                    "factor": f["display_name"],
                    "current": f"Score: {round(val, 2)}",
                    "target": "Stabilized",
                    "action": "Extended monitoring and vital sign stabilization before discharge",
                    "estimated_risk_reduction": round(f["abs_impact"] * 85, 1),
                })

        return counterfactuals[:5]

    def get_global_importance(self) -> dict:
        """Get global feature importance from ensemble."""
        importances = self.ensemble.feature_importances
        result = []
        for feat, imp in importances.items():
            result.append({
                "feature": feat,
                "display_name": FEATURE_DISPLAY_NAMES.get(feat, feat.replace("_", " ").title()),
                "importance": imp,
            })
        return {"global_importances": result[:20]}
