"""
Asteric RiskIQ - Alert Management Service

Manages real-time alerts for high-risk patients:
- Priority-based alert generation
- Alert escalation workflows
- Alert history and audit trail
- Configurable thresholds
"""

from datetime import datetime
from typing import Optional
from loguru import logger

from app.config import settings


class AlertManager:
    """Manages patient risk alerts."""

    def __init__(self):
        self.alerts: list[dict] = []
        self.alert_counter = 0

    def generate_alerts(self, patients: list[dict]) -> list[dict]:
        """Generate alerts for patients exceeding risk thresholds."""
        new_alerts = []

        for patient in patients:
            risk_score = patient.get("risk_score", 0)
            risk_level = patient.get("risk_level", "low")
            patient_id = patient.get("patient_id", "unknown")

            if risk_level in ("critical", "high"):
                alert = self._create_alert(
                    patient_id=patient_id,
                    patient_name=patient.get("name", "Unknown"),
                    risk_score=risk_score,
                    risk_level=risk_level,
                    alert_type="high_risk_discharge",
                    message=self._generate_alert_message(patient),
                    priority="critical" if risk_level == "critical" else "high",
                    ward=patient.get("ward", "Unknown"),
                )
                new_alerts.append(alert)

            # Anomaly alerts
            if risk_score > 80 and patient.get("admissions_last_6months", 0) >= 3:
                alert = self._create_alert(
                    patient_id=patient_id,
                    patient_name=patient.get("name", "Unknown"),
                    risk_score=risk_score,
                    risk_level=risk_level,
                    alert_type="frequent_readmitter",
                    message=f"Frequent readmitter: {patient.get('admissions_last_6months', 0)} admissions in 6 months",
                    priority="high",
                    ward=patient.get("ward", "Unknown"),
                )
                new_alerts.append(alert)

        self.alerts.extend(new_alerts)
        return new_alerts

    def _create_alert(
        self,
        patient_id: str,
        patient_name: str,
        risk_score: float,
        risk_level: str,
        alert_type: str,
        message: str,
        priority: str,
        ward: str,
    ) -> dict:
        """Create a structured alert."""
        self.alert_counter += 1

        return {
            "alert_id": f"ALT-{self.alert_counter:06d}",
            "patient_id": patient_id,
            "patient_name": patient_name,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "alert_type": alert_type,
            "message": message,
            "priority": priority,
            "ward": ward,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "acknowledged_at": None,
            "acknowledged_by": None,
            "resolved_at": None,
        }

    def _generate_alert_message(self, patient: dict) -> str:
        """Generate descriptive alert message."""
        parts = [
            f"{patient.get('name', 'Patient')} ({patient.get('age', '?')}y {patient.get('gender', '')})",
            f"Risk Score: {patient.get('risk_score', 0)}%",
            f"Diagnosis: {patient.get('diagnosis_name', 'Unknown')}",
        ]

        chronic = patient.get("chronic_conditions", [])
        if chronic:
            parts.append(f"Conditions: {', '.join(chronic[:3])}")

        admissions = patient.get("admissions_last_6months", 0)
        if admissions > 0:
            parts.append(f"{admissions} admission(s) in 6 months")

        return " | ".join(parts)

    def get_alerts(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        ward: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """Get filtered alerts."""
        alerts = self.alerts.copy()

        if status:
            alerts = [a for a in alerts if a["status"] == status]
        if priority:
            alerts = [a for a in alerts if a["priority"] == priority]
        if ward and ward != "all":
            alerts = [a for a in alerts if a["ward"] == ward]

        # Sort by priority and time
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        alerts.sort(key=lambda a: (priority_order.get(a["priority"], 4), a["created_at"]))

        return alerts[:limit]

    def acknowledge_alert(self, alert_id: str, user: str = "system") -> Optional[dict]:
        """Acknowledge an alert."""
        for alert in self.alerts:
            if alert["alert_id"] == alert_id:
                alert["status"] = "acknowledged"
                alert["acknowledged_at"] = datetime.now().isoformat()
                alert["acknowledged_by"] = user
                return alert
        return None

    def resolve_alert(self, alert_id: str) -> Optional[dict]:
        """Resolve an alert."""
        for alert in self.alerts:
            if alert["alert_id"] == alert_id:
                alert["status"] = "resolved"
                alert["resolved_at"] = datetime.now().isoformat()
                return alert
        return None

    def get_alert_stats(self) -> dict:
        """Get alert statistics."""
        return {
            "total": len(self.alerts),
            "active": sum(1 for a in self.alerts if a["status"] == "active"),
            "acknowledged": sum(1 for a in self.alerts if a["status"] == "acknowledged"),
            "resolved": sum(1 for a in self.alerts if a["status"] == "resolved"),
            "by_priority": {
                "critical": sum(1 for a in self.alerts if a["priority"] == "critical"),
                "high": sum(1 for a in self.alerts if a["priority"] == "high"),
                "medium": sum(1 for a in self.alerts if a["priority"] == "medium"),
                "low": sum(1 for a in self.alerts if a["priority"] == "low"),
            },
        }
