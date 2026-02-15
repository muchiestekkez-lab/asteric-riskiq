"""
Asteric RiskIQ - Anomaly Detection Engine

Detects unusual patient patterns using:
- Isolation Forest for multivariate anomaly detection
- Statistical outlier detection for individual features
- Pattern deviation scoring
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import Optional
from loguru import logger

from app.config import settings


class AnomalyDetector:
    """Detects anomalous patient profiles that need special attention."""

    def __init__(self):
        self.model = IsolationForest(
            n_estimators=200,
            contamination=settings.anomaly_contamination,
            max_features=0.8,
            random_state=42,
            n_jobs=-1,
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.feature_names: list[str] = []
        self.feature_stats: dict = {}

    def fit(self, X: pd.DataFrame):
        """Fit anomaly detector on normal patient data."""
        self.feature_names = list(X.columns)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_fitted = True

        # Store feature statistics for individual outlier detection
        for col in X.columns:
            self.feature_stats[col] = {
                "mean": float(X[col].mean()),
                "std": float(X[col].std()),
                "q1": float(X[col].quantile(0.25)),
                "q3": float(X[col].quantile(0.75)),
                "median": float(X[col].median()),
            }

        logger.info(f"Anomaly detector fitted on {len(X)} samples")

    def detect(self, features: dict) -> dict:
        """Detect anomalies in a single patient's features."""
        if not self.is_fitted:
            return {"is_anomaly": False, "score": 0.0, "anomalous_features": []}

        X = pd.DataFrame([features])[self.feature_names]
        X_scaled = self.scaler.transform(X)

        # Isolation Forest score (-1 = anomaly, 1 = normal)
        raw_score = self.model.decision_function(X_scaled)[0]
        prediction = self.model.predict(X_scaled)[0]

        # Normalize score to 0-1 (higher = more anomalous)
        anomaly_score = max(0, min(1, 0.5 - raw_score))

        # Find which features are anomalous
        anomalous_features = []
        for col in self.feature_names:
            if col not in self.feature_stats:
                continue
            stats = self.feature_stats[col]
            val = float(X.iloc[0][col])
            iqr = stats["q3"] - stats["q1"]

            if iqr > 0:
                z_score = abs(val - stats["mean"]) / max(stats["std"], 0.001)
                is_outlier = (val < stats["q1"] - 2.0 * iqr) or (val > stats["q3"] + 2.0 * iqr)

                if is_outlier or z_score > 2.5:
                    direction = "high" if val > stats["mean"] else "low"
                    anomalous_features.append({
                        "feature": col,
                        "value": round(val, 2),
                        "expected_range": f"{round(stats['q1'], 2)} - {round(stats['q3'], 2)}",
                        "z_score": round(z_score, 2),
                        "direction": direction,
                        "severity": "high" if z_score > 3.5 else "medium" if z_score > 2.5 else "low",
                    })

        anomalous_features.sort(key=lambda x: x["z_score"], reverse=True)

        return {
            "is_anomaly": prediction == -1,
            "anomaly_score": round(anomaly_score, 3),
            "anomalous_features": anomalous_features[:10],
            "total_anomalous_features": len(anomalous_features),
            "alert_level": (
                "critical" if anomaly_score > 0.8
                else "warning" if anomaly_score > 0.5
                else "info" if anomaly_score > 0.3
                else "none"
            ),
        }

    def batch_detect(self, X: pd.DataFrame) -> list[dict]:
        """Detect anomalies in a batch of patients."""
        results = []
        for idx in range(len(X)):
            features = X.iloc[idx].to_dict()
            results.append(self.detect(features))
        return results
