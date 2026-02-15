"""
Asteric RiskIQ - Intervention Recommendation Engine

Provides evidence-based intervention recommendations based on:
- Patient risk score and level
- Specific risk factors identified
- Patient social circumstances
- Intervention effectiveness data
- Cost-benefit analysis
"""

from typing import Optional
from app.config import INTERVENTION_CATALOG


class InterventionEngine:
    """Recommends targeted interventions based on patient risk profile."""

    def recommend(self, risk_assessment: dict) -> list[dict]:
        """Generate intervention recommendations for a patient."""
        risk_score = risk_assessment.get("risk_assessment", {}).get("overall_score", 0)
        risk_level = risk_assessment.get("risk_assessment", {}).get("risk_level", "low")
        explanation = risk_assessment.get("explanation", {})
        patient_info = risk_assessment.get("patient_info", {})
        nlp = risk_assessment.get("nlp_analysis", {})
        anomaly = risk_assessment.get("anomaly_detection", {})
        social = patient_info.get("social_factors", {})

        interventions = []

        # --- Critical / High Risk ---
        if risk_level in ("critical", "high"):
            interventions.append(self._build_intervention(
                "care_coordinator",
                urgency="immediate",
                rationale="Patient is high risk and needs coordinated transition care",
            ))
            interventions.append(self._build_intervention(
                "medication_reconciliation",
                urgency="before_discharge",
                rationale="High-risk patients benefit most from pharmacist medication review",
            ))
            interventions.append(self._build_intervention(
                "phone_followup_24h",
                urgency="post_discharge",
                rationale="Early check-in to catch complications within first 24 hours",
            ))

            if risk_score >= 85:
                interventions.append(self._build_intervention(
                    "delay_discharge",
                    urgency="immediate",
                    rationale=f"Very high risk score ({risk_score}%) suggests premature discharge risk",
                ))

            if risk_score >= 80:
                interventions.append(self._build_intervention(
                    "remote_monitoring",
                    urgency="before_discharge",
                    rationale="Continuous vital monitoring post-discharge for critical patients",
                ))

        # --- Medium Risk ---
        if risk_level == "medium":
            interventions.append(self._build_intervention(
                "telehealth",
                urgency="post_discharge",
                rationale="Virtual follow-up within 48-72 hours for moderate-risk patients",
            ))
            interventions.append(self._build_intervention(
                "rapid_clinic_appointment",
                urgency="before_discharge",
                rationale="Schedule PCP visit within 7 days of discharge",
            ))

        # --- Social Factor Based ---
        if social.get("lives_alone") and not social.get("has_caregiver"):
            interventions.append(self._build_intervention(
                "home_visit",
                urgency="post_discharge",
                rationale="Patient lives alone without caregiver support",
            ))
            interventions.append(self._build_intervention(
                "social_work_consult",
                urgency="before_discharge",
                rationale="Address social isolation and support needs",
            ))

        if not social.get("transportation_access"):
            interventions.append(self._build_intervention(
                "telehealth",
                urgency="post_discharge",
                rationale="Patient lacks transportation - virtual visit preferred",
            ))

        if not social.get("housing_stable"):
            interventions.append(self._build_intervention(
                "social_work_consult",
                urgency="immediate",
                rationale="Housing instability identified - social work referral needed",
            ))

        # --- Condition Based ---
        top_factors = explanation.get("top_factors", [])
        factor_names = [f["feature"] for f in top_factors[:5]]

        if "missed_appointments" in factor_names:
            interventions.append(self._build_intervention(
                "phone_followup_72h",
                urgency="post_discharge",
                rationale="History of missed appointments - proactive follow-up needed",
            ))

        if "medication_count" in factor_names or patient_info.get("medication_count", 0) > 10:
            interventions.append(self._build_intervention(
                "medication_reconciliation",
                urgency="before_discharge",
                rationale=f"Polypharmacy ({patient_info.get('medication_count', 0)} medications) requires review",
            ))

        # --- NLP-driven ---
        if nlp.get("concern_level") in ("critical", "high"):
            interventions.append(self._build_intervention(
                "nurse_followup",
                urgency="before_discharge",
                rationale="Clinical notes indicate significant concern factors",
            ))

        if nlp.get("social_factors", {}).get("substance_use"):
            interventions.append(self._build_intervention(
                "social_work_consult",
                urgency="before_discharge",
                rationale="Substance use concern identified in clinical notes",
            ))

        # --- Patient education for all ---
        if risk_level != "low":
            interventions.append(self._build_intervention(
                "patient_education",
                urgency="before_discharge",
                rationale="Enhanced discharge education with teach-back method",
            ))

        # --- Anomaly-based ---
        if anomaly.get("is_anomaly"):
            interventions.append(self._build_intervention(
                "nurse_followup",
                urgency="immediate",
                rationale="Anomalous patient profile detected - additional assessment recommended",
            ))

        # Deduplicate and sort by priority
        seen = set()
        unique_interventions = []
        for intv in interventions:
            key = intv["id"]
            if key not in seen:
                seen.add(key)
                unique_interventions.append(intv)

        priority_order = {"immediate": 0, "before_discharge": 1, "post_discharge": 2}
        unique_interventions.sort(
            key=lambda x: (priority_order.get(x["urgency"], 3), -x.get("evidence_score", 0))
        )

        return unique_interventions

    def _build_intervention(self, intervention_id: str, urgency: str, rationale: str) -> dict:
        """Build a structured intervention recommendation."""
        catalog_entry = INTERVENTION_CATALOG.get(intervention_id, {})

        evidence_scores = {"A": 0.95, "B": 0.80, "C": 0.65}
        evidence_level = catalog_entry.get("evidence_level", "B")

        return {
            "id": intervention_id,
            "name": catalog_entry.get("name", intervention_id.replace("_", " ").title()),
            "description": catalog_entry.get("description", ""),
            "urgency": urgency,
            "priority": catalog_entry.get("priority", "medium"),
            "evidence_level": evidence_level,
            "evidence_score": evidence_scores.get(evidence_level, 0.5),
            "cost_category": catalog_entry.get("cost_category", "medium"),
            "rationale": rationale,
        }
