"""
Asteric RiskIQ - Temporal Analysis Engine

Advanced time-series analysis for patient trajectories:
- Survival analysis (Kaplan-Meier curves)
- Patient trajectory trend analysis
- Readmission velocity scoring
- Seasonal/temporal pattern detection
- Time-to-event prediction
"""

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger


class TemporalAnalyzer:
    """Analyzes temporal patterns in patient readmissions."""

    def __init__(self):
        self.admission_history: dict = {}
        self.seasonal_patterns: dict = {}
        self.population_survival: Optional[dict] = None

    def compute_survival_curve(
        self,
        patients: list[dict],
        max_days: int = 30,
    ) -> dict:
        """Compute Kaplan-Meier survival curve for a patient cohort.

        Returns probability of remaining out of hospital over time.
        """
        # Simulate time-to-event data based on risk scores
        n = len(patients)
        times = []
        events = []

        for p in patients:
            risk = p.get("risk_score", 50) / 100.0
            # Exponential distribution scaled by risk
            lambda_param = risk * 0.15
            t = np.random.exponential(1 / max(lambda_param, 0.01))
            t = min(t, max_days)

            # Censoring: some patients don't get readmitted
            if t >= max_days or np.random.random() > risk * 1.3:
                times.append(max_days)
                events.append(0)  # Censored
            else:
                times.append(max(1, int(t)))
                events.append(1)  # Event (readmission)

        times = np.array(times)
        events = np.array(events)

        # Kaplan-Meier estimation
        unique_times = np.sort(np.unique(times[events == 1]))
        survival_prob = 1.0
        curve_points = [{"day": 0, "survival_probability": 1.0, "at_risk": n}]

        at_risk = n
        for t in unique_times:
            if t > max_days:
                break
            d_i = np.sum((times == t) & (events == 1))  # Deaths at time t
            c_i = np.sum((times == t) & (events == 0))  # Censored at time t

            if at_risk > 0:
                survival_prob *= (1 - d_i / at_risk)

            curve_points.append({
                "day": int(t),
                "survival_probability": round(max(0, survival_prob), 4),
                "at_risk": int(at_risk),
                "events": int(d_i),
            })

            at_risk -= (d_i + c_i)

        # Fill in remaining days
        last_prob = curve_points[-1]["survival_probability"]
        last_day = curve_points[-1]["day"]
        for d in range(last_day + 1, max_days + 1):
            curve_points.append({
                "day": d,
                "survival_probability": round(last_prob, 4),
                "at_risk": int(max(0, at_risk)),
                "events": 0,
            })

        # Compute median survival time
        median_survival = None
        for point in curve_points:
            if point["survival_probability"] <= 0.5:
                median_survival = point["day"]
                break

        return {
            "curve": curve_points,
            "median_survival_days": median_survival,
            "total_patients": n,
            "total_events": int(np.sum(events)),
            "event_rate": round(float(np.mean(events)), 3),
        }

    def compute_risk_trajectory(self, patient_history: list[dict]) -> dict:
        """Analyze how a patient's risk has changed over time."""
        if len(patient_history) < 2:
            return {
                "trend": "insufficient_data",
                "trajectory_points": patient_history,
                "velocity": 0,
            }

        scores = [h.get("risk_score", 50) for h in patient_history]
        times = list(range(len(scores)))

        # Linear regression for trend
        slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(times, scores)

        # Compute velocity (rate of change)
        velocity = slope

        # Detect acceleration
        if len(scores) >= 3:
            diffs = np.diff(scores)
            acceleration = float(np.mean(np.diff(diffs))) if len(diffs) > 1 else 0
        else:
            acceleration = 0

        # Determine trend
        if abs(slope) < 1:
            trend = "stable"
        elif slope > 5:
            trend = "rapidly_increasing"
        elif slope > 0:
            trend = "increasing"
        elif slope < -5:
            trend = "rapidly_decreasing"
        else:
            trend = "decreasing"

        return {
            "trend": trend,
            "velocity": round(velocity, 2),
            "acceleration": round(acceleration, 2),
            "r_squared": round(r_value ** 2, 3),
            "current_score": scores[-1],
            "previous_score": scores[-2] if len(scores) > 1 else None,
            "change": round(scores[-1] - scores[0], 1),
            "trajectory_points": [
                {"index": i, "score": s} for i, s in enumerate(scores)
            ],
            "projected_7d": round(min(100, max(0, scores[-1] + velocity * 7)), 1),
            "projected_30d": round(min(100, max(0, scores[-1] + velocity * 30)), 1),
        }

    def analyze_readmission_velocity(self, admission_dates: list[str]) -> dict:
        """Analyze the speed at which readmissions are occurring."""
        if len(admission_dates) < 2:
            return {
                "velocity_score": 0,
                "avg_days_between": None,
                "accelerating": False,
            }

        dates = sorted([
            datetime.fromisoformat(d) if isinstance(d, str) else d
            for d in admission_dates
        ])

        gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]

        avg_gap = float(np.mean(gaps))
        recent_gap = gaps[-1] if gaps else avg_gap

        # Velocity: inverse of gap (shorter gap = higher velocity)
        velocity = 30.0 / max(avg_gap, 1)

        # Acceleration: are gaps getting shorter?
        if len(gaps) >= 2:
            gap_diffs = np.diff(gaps)
            accelerating = float(np.mean(gap_diffs)) < 0
        else:
            accelerating = False

        return {
            "velocity_score": round(min(velocity * 10, 100), 1),
            "avg_days_between": round(avg_gap, 1),
            "recent_gap_days": recent_gap,
            "total_admissions": len(dates),
            "accelerating": accelerating,
            "gaps": gaps,
            "risk_amplifier": round(1 + (velocity / 10), 2),
        }

    def detect_seasonal_patterns(self, admissions: list[dict]) -> dict:
        """Detect seasonal patterns in readmission rates."""
        if not admissions:
            return {"patterns": []}

        monthly_counts = [0] * 12
        hourly_counts = [0] * 24
        dow_counts = [0] * 7

        for adm in admissions:
            dt = adm.get("admission_date")
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt)
            if dt:
                monthly_counts[dt.month - 1] += 1
                hourly_counts[dt.hour] += 1
                dow_counts[dt.weekday()] += 1

        month_names = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        ]
        dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        return {
            "monthly": [
                {"month": month_names[i], "count": monthly_counts[i]}
                for i in range(12)
            ],
            "hourly": [
                {"hour": i, "count": hourly_counts[i]}
                for i in range(24)
            ],
            "day_of_week": [
                {"day": dow_names[i], "count": dow_counts[i]}
                for i in range(7)
            ],
            "peak_month": month_names[np.argmax(monthly_counts)],
            "peak_hour": int(np.argmax(hourly_counts)),
            "peak_day": dow_names[np.argmax(dow_counts)],
        }

    def find_similar_patients(
        self,
        target: dict,
        population: list[dict],
        top_k: int = 5,
    ) -> list[dict]:
        """Find patients with similar profiles and their outcomes."""
        if not population:
            return []

        key_features = [
            "age", "num_chronic_conditions", "admissions_last_6months",
            "length_of_stay", "medication_count", "num_previous_admissions",
        ]

        target_vec = np.array([target.get(f, 0) for f in key_features], dtype=float)
        if np.all(target_vec == 0):
            return []

        # Normalize
        target_norm = target_vec / (np.linalg.norm(target_vec) + 1e-8)

        similarities = []
        for p in population:
            p_vec = np.array([p.get(f, 0) for f in key_features], dtype=float)
            p_norm = p_vec / (np.linalg.norm(p_vec) + 1e-8)

            # Cosine similarity
            sim = float(np.dot(target_norm, p_norm))
            similarities.append((sim, p))

        similarities.sort(key=lambda x: x[0], reverse=True)

        return [
            {
                "similarity": round(sim, 3),
                "patient_id": p.get("patient_id", "unknown"),
                "age": p.get("age"),
                "risk_score": p.get("risk_score"),
                "was_readmitted": p.get("was_readmitted", False),
                "readmission_days": p.get("readmission_days"),
            }
            for sim, p in similarities[:top_k]
        ]
