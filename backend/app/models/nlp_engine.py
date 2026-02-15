"""
Asteric RiskIQ - Clinical NLP Engine

Extracts risk signals from clinical notes using:
- Keyword & pattern extraction
- Sentiment/concern scoring
- Medication mention detection
- Social determinant extraction
- Discharge readiness assessment
"""

import re
from typing import Optional
from loguru import logger


# Risk-associated clinical terms
RISK_KEYWORDS = {
    "high_risk": [
        "non-compliant", "noncompliant", "non-adherent", "nonadherent",
        "against medical advice", "AMA", "refused", "declined treatment",
        "frequent flyer", "recurrent admission", "readmission",
        "unstable", "deteriorating", "worsening", "critical",
        "sepsis", "septic", "acute", "exacerbation",
        "fall risk", "high fall risk", "confusion", "altered mental status",
        "substance abuse", "alcohol abuse", "drug use",
        "homeless", "no fixed address", "shelter",
        "lives alone", "no support", "no caregiver",
        "poor prognosis", "end stage", "terminal",
        "multiple comorbidities", "polypharmacy",
    ],
    "medium_risk": [
        "follow-up needed", "close monitoring", "watch closely",
        "borderline", "marginal", "guarded",
        "limited mobility", "requires assistance",
        "partial compliance", "inconsistent",
        "anxiety", "depression", "mood disorder",
        "obesity", "overweight", "malnourished",
        "financial concerns", "insurance issues",
        "transportation issues", "access barriers",
    ],
    "protective": [
        "stable", "improving", "resolved", "recovered",
        "compliant", "adherent", "motivated",
        "strong support", "family present", "caregiver available",
        "independent", "self-care", "ambulatory",
        "well-nourished", "good appetite",
        "follow-up scheduled", "appointment confirmed",
    ],
}

MEDICATION_PATTERNS = [
    r'\b(metformin|insulin|glipizide|sitagliptin)\b',  # Diabetes
    r'\b(lisinopril|losartan|amlodipine|metoprolol|atenolol)\b',  # Cardiac
    r'\b(furosemide|lasix|spironolactone|hydrochlorothiazide)\b',  # Diuretics
    r'\b(warfarin|coumadin|eliquis|xarelto|apixaban)\b',  # Anticoagulants
    r'\b(prednisone|dexamethasone|methylprednisolone)\b',  # Steroids
    r'\b(morphine|oxycodone|hydrocodone|fentanyl)\b',  # Opioids
    r'\b(albuterol|ipratropium|fluticasone|budesonide)\b',  # Respiratory
    r'\b(sertraline|fluoxetine|citalopram|escitalopram)\b',  # Antidepressants
    r'\b(gabapentin|pregabalin|carbamazepine)\b',  # Neurological
]

SOCIAL_PATTERNS = {
    "lives_alone": [r'lives?\s+alone', r'no\s+(?:family|support)', r'single\s+(?:person|household)'],
    "homeless": [r'homeless', r'no\s+fixed\s+address', r'shelter', r'unhoused'],
    "substance_use": [r'substance\s+(?:use|abuse)', r'alcohol\s+(?:use|abuse|dependence)', r'drug\s+use', r'IVDU'],
    "financial_hardship": [r'financial\s+(?:concerns?|hardship|difficulty)', r'unable\s+to\s+afford', r'uninsured'],
    "transportation": [r'transportation\s+(?:issues?|barriers?|difficulty)', r'no\s+(?:ride|transport)'],
    "language_barrier": [r'language\s+barrier', r'interpreter\s+needed', r'limited\s+english'],
    "cognitive_impairment": [r'cognitive\s+(?:impairment|decline)', r'dementia', r'confusion', r'altered\s+mental'],
}


class ClinicalNLPEngine:
    """Extract clinical risk signals from unstructured text."""

    def analyze_notes(self, text: str) -> dict:
        """Comprehensive analysis of clinical notes."""
        if not text or not text.strip():
            return {
                "risk_score_modifier": 0,
                "risk_keywords_found": [],
                "protective_keywords_found": [],
                "medications_mentioned": [],
                "social_factors": {},
                "discharge_readiness": "unknown",
                "concern_level": "none",
                "summary": "No clinical notes available",
            }

        text_lower = text.lower()

        # Keyword analysis
        risk_keywords = self._find_keywords(text_lower, "high_risk")
        medium_keywords = self._find_keywords(text_lower, "medium_risk")
        protective_keywords = self._find_keywords(text_lower, "protective")

        # Medication extraction
        medications = self._extract_medications(text_lower)

        # Social determinant extraction
        social_factors = self._extract_social_factors(text_lower)

        # Compute risk modifier
        high_count = len(risk_keywords)
        medium_count = len(medium_keywords)
        protective_count = len(protective_keywords)

        risk_modifier = (high_count * 5 + medium_count * 2 - protective_count * 3)
        risk_modifier = max(-15, min(25, risk_modifier))

        # Concern level
        if high_count >= 3:
            concern_level = "critical"
        elif high_count >= 1:
            concern_level = "high"
        elif medium_count >= 2:
            concern_level = "moderate"
        elif medium_count >= 1:
            concern_level = "low"
        else:
            concern_level = "none"

        # Discharge readiness
        discharge_readiness = self._assess_discharge_readiness(
            text_lower, risk_keywords, protective_keywords
        )

        # Generate summary
        summary = self._generate_summary(
            risk_keywords, medium_keywords, protective_keywords,
            medications, social_factors, concern_level,
        )

        return {
            "risk_score_modifier": risk_modifier,
            "risk_keywords_found": risk_keywords,
            "medium_risk_keywords": medium_keywords,
            "protective_keywords_found": protective_keywords,
            "medications_mentioned": medications,
            "social_factors": social_factors,
            "discharge_readiness": discharge_readiness,
            "concern_level": concern_level,
            "summary": summary,
            "nlp_confidence": round(min(1.0, (high_count + medium_count + protective_count) / 5), 2),
        }

    def _find_keywords(self, text: str, category: str) -> list[str]:
        """Find matching keywords in text."""
        found = []
        for keyword in RISK_KEYWORDS.get(category, []):
            if keyword.lower() in text:
                found.append(keyword)
        return list(set(found))

    def _extract_medications(self, text: str) -> list[str]:
        """Extract medication mentions from text."""
        medications = set()
        for pattern in MEDICATION_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            medications.update(m.lower() for m in matches)
        return sorted(list(medications))

    def _extract_social_factors(self, text: str) -> dict:
        """Extract social determinant mentions."""
        factors = {}
        for factor_name, patterns in SOCIAL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    factors[factor_name] = True
                    break
        return factors

    def _assess_discharge_readiness(
        self,
        text: str,
        risk_keywords: list,
        protective_keywords: list,
    ) -> str:
        """Assess patient's readiness for discharge."""
        ready_signals = [
            "ready for discharge", "cleared for discharge",
            "stable for discharge", "discharge appropriate",
            "medically stable", "goals met",
        ]
        not_ready_signals = [
            "not ready", "not stable", "requires further",
            "needs monitoring", "continue observation",
            "defer discharge", "delay discharge",
        ]

        ready_count = sum(1 for s in ready_signals if s in text)
        not_ready_count = sum(1 for s in not_ready_signals if s in text)

        if not_ready_count > 0 or len(risk_keywords) >= 3:
            return "not_ready"
        elif ready_count > 0 and len(risk_keywords) == 0:
            return "ready"
        elif len(protective_keywords) > len(risk_keywords):
            return "likely_ready"
        else:
            return "uncertain"

    def _generate_summary(
        self,
        risk_kw: list,
        medium_kw: list,
        protective_kw: list,
        medications: list,
        social_factors: dict,
        concern_level: str,
    ) -> str:
        """Generate a concise NLP analysis summary."""
        parts = []

        if risk_kw:
            parts.append(f"High-risk indicators: {', '.join(risk_kw[:3])}")
        if medium_kw:
            parts.append(f"Moderate concerns: {', '.join(medium_kw[:3])}")
        if protective_kw:
            parts.append(f"Protective factors noted: {', '.join(protective_kw[:3])}")
        if social_factors:
            parts.append(f"Social concerns: {', '.join(social_factors.keys())}")
        if medications:
            parts.append(f"Key medications: {', '.join(medications[:5])}")

        if not parts:
            return "No significant risk signals detected in clinical notes."

        return " | ".join(parts)
