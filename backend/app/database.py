"""
Asteric RiskIQ - Database Layer (SQLite)

Persistent storage for:
- Partner hospitals and access codes
- Patient records
- Risk assessments
- Alerts
- Audit logs
"""

import sqlite3
import json
import os
import secrets
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from loguru import logger

from app.config import DATA_DIR

DB_PATH = DATA_DIR / "asteric_riskiq.db"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize all database tables."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS hospitals (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            access_code_hash TEXT NOT NULL,
            email TEXT NOT NULL,
            address TEXT,
            city TEXT,
            state TEXT,
            country TEXT DEFAULT 'US',
            contact_name TEXT,
            contact_phone TEXT,
            is_active INTEGER DEFAULT 1,
            max_users INTEGER DEFAULT 50,
            created_at TEXT NOT NULL,
            last_login_at TEXT,
            settings TEXT DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            hospital_id TEXT NOT NULL,
            device_info TEXT,
            ip_address TEXT,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (hospital_id) REFERENCES hospitals(id)
        );

        CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY,
            hospital_id TEXT NOT NULL,
            mrn TEXT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            date_of_birth TEXT,
            age INTEGER,
            gender TEXT,
            insurance TEXT,
            diagnosis_code TEXT,
            diagnosis_name TEXT,
            chronic_conditions TEXT DEFAULT '[]',
            admission_date TEXT,
            discharge_date TEXT,
            length_of_stay INTEGER,
            ward TEXT,
            num_previous_admissions INTEGER DEFAULT 0,
            admissions_last_6months INTEGER DEFAULT 0,
            medication_count INTEGER DEFAULT 0,
            missed_appointments INTEGER DEFAULT 0,
            bp_systolic REAL,
            bp_diastolic REAL,
            heart_rate REAL,
            temperature REAL,
            oxygen_saturation REAL,
            respiratory_rate REAL,
            bmi REAL,
            hemoglobin REAL,
            wbc_count REAL,
            creatinine REAL,
            glucose REAL,
            bun REAL,
            sodium REAL,
            potassium REAL,
            smoking_status TEXT DEFAULT 'unknown',
            alcohol_use TEXT DEFAULT 'unknown',
            lives_alone INTEGER DEFAULT 0,
            has_caregiver INTEGER DEFAULT 1,
            transportation_access INTEGER DEFAULT 1,
            housing_stable INTEGER DEFAULT 1,
            clinical_notes TEXT,
            discharge_hour INTEGER,
            is_weekend_discharge INTEGER DEFAULT 0,
            status TEXT DEFAULT 'admitted',
            risk_score REAL,
            risk_level TEXT,
            risk_horizons TEXT DEFAULT '{}',
            last_scored_at TEXT,
            was_readmitted INTEGER,
            readmission_date TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            created_by TEXT,
            FOREIGN KEY (hospital_id) REFERENCES hospitals(id)
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id TEXT PRIMARY KEY,
            hospital_id TEXT NOT NULL,
            patient_id TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            priority TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL,
            acknowledged_at TEXT,
            acknowledged_by TEXT,
            resolved_at TEXT,
            resolved_by TEXT,
            FOREIGN KEY (hospital_id) REFERENCES hospitals(id),
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_id TEXT NOT NULL,
            action TEXT NOT NULL,
            entity_type TEXT,
            entity_id TEXT,
            details TEXT,
            ip_address TEXT,
            timestamp TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS model_state (
            hospital_id TEXT PRIMARY KEY,
            is_trained INTEGER DEFAULT 0,
            training_samples INTEGER DEFAULT 0,
            last_trained_at TEXT,
            metrics TEXT DEFAULT '{}',
            FOREIGN KEY (hospital_id) REFERENCES hospitals(id)
        );

        CREATE INDEX IF NOT EXISTS idx_patients_hospital ON patients(hospital_id);
        CREATE INDEX IF NOT EXISTS idx_patients_status ON patients(hospital_id, status);
        CREATE INDEX IF NOT EXISTS idx_patients_risk ON patients(hospital_id, risk_level);
        CREATE INDEX IF NOT EXISTS idx_alerts_hospital ON alerts(hospital_id);
        CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(hospital_id, status);
        CREATE INDEX IF NOT EXISTS idx_sessions_hospital ON sessions(hospital_id);
        CREATE INDEX IF NOT EXISTS idx_audit_hospital ON audit_log(hospital_id);
    """)

    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {DB_PATH}")


# --- Hospital Management ---

def hash_access_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def generate_access_code() -> str:
    """Generate a 12-character alphanumeric access code."""
    return secrets.token_hex(6).upper()  # e.g. "A3F9B2C1D4E5"


def create_hospital(
    name: str,
    email: str,
    address: str = "",
    city: str = "",
    state: str = "",
    contact_name: str = "",
    contact_phone: str = "",
) -> dict:
    """Register a new partner hospital and generate access code."""
    conn = get_db()
    hospital_id = f"HOSP-{secrets.token_hex(4).upper()}"
    access_code = generate_access_code()
    now = datetime.now().isoformat()

    conn.execute(
        """INSERT INTO hospitals (id, name, access_code_hash, email, address, city, state,
           contact_name, contact_phone, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (hospital_id, name, hash_access_code(access_code), email, address, city, state,
         contact_name, contact_phone, now)
    )
    conn.execute(
        "INSERT INTO model_state (hospital_id) VALUES (?)",
        (hospital_id,)
    )
    conn.commit()
    conn.close()

    logger.info(f"Hospital registered: {name} ({hospital_id})")

    return {
        "hospital_id": hospital_id,
        "name": name,
        "access_code": access_code,
        "email": email,
    }


def verify_access_code(access_code: str) -> Optional[dict]:
    """Verify an access code and return hospital info."""
    conn = get_db()
    code_hash = hash_access_code(access_code.strip().upper())

    row = conn.execute(
        "SELECT * FROM hospitals WHERE access_code_hash = ? AND is_active = 1",
        (code_hash,)
    ).fetchone()

    if row:
        hospital = dict(row)
        conn.execute(
            "UPDATE hospitals SET last_login_at = ? WHERE id = ?",
            (datetime.now().isoformat(), hospital["id"])
        )
        conn.commit()
        conn.close()
        return hospital

    conn.close()
    return None


def create_session(hospital_id: str, device_info: str = "", ip_address: str = "") -> str:
    """Create a session token for a hospital."""
    conn = get_db()
    token = secrets.token_urlsafe(48)
    now = datetime.now()
    expires = now + timedelta(hours=12)

    conn.execute(
        """INSERT INTO sessions (token, hospital_id, device_info, ip_address, created_at, expires_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (token, hospital_id, device_info, ip_address, now.isoformat(), expires.isoformat())
    )
    conn.commit()
    conn.close()
    return token


def validate_session(token: str) -> Optional[dict]:
    """Validate a session token and return hospital info."""
    conn = get_db()
    row = conn.execute(
        """SELECT s.*, h.name as hospital_name, h.id as hospital_id
           FROM sessions s JOIN hospitals h ON s.hospital_id = h.id
           WHERE s.token = ? AND s.is_active = 1 AND s.expires_at > ?""",
        (token, datetime.now().isoformat())
    ).fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def invalidate_session(token: str):
    conn = get_db()
    conn.execute("UPDATE sessions SET is_active = 0 WHERE token = ?", (token,))
    conn.commit()
    conn.close()


# --- Patient Operations ---

def add_patient(hospital_id: str, data: dict) -> dict:
    """Add a new patient record."""
    conn = get_db()
    patient_id = f"PT-{secrets.token_hex(4).upper()}"
    now = datetime.now().isoformat()

    chronic = data.get("chronic_conditions", [])
    if isinstance(chronic, list):
        chronic = json.dumps(chronic)

    # Handle was_readmitted: can be True/False/None
    was_readmitted = data.get("was_readmitted")
    if was_readmitted is True:
        was_readmitted = 1
    elif was_readmitted is False:
        was_readmitted = 0
    else:
        was_readmitted = None

    conn.execute(
        """INSERT INTO patients (
            id, hospital_id, mrn, first_name, last_name, date_of_birth, age, gender,
            insurance, diagnosis_code, diagnosis_name, chronic_conditions,
            admission_date, discharge_date, length_of_stay, ward,
            num_previous_admissions, admissions_last_6months,
            medication_count, missed_appointments,
            bp_systolic, bp_diastolic, heart_rate, temperature,
            oxygen_saturation, respiratory_rate, bmi,
            hemoglobin, wbc_count, creatinine, glucose, bun, sodium, potassium,
            smoking_status, alcohol_use,
            lives_alone, has_caregiver, transportation_access, housing_stable,
            clinical_notes, discharge_hour, is_weekend_discharge,
            status, was_readmitted, created_at, updated_at, created_by
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?
        )""",
        (
            patient_id, hospital_id,
            data.get("mrn", ""),
            data.get("first_name", ""),
            data.get("last_name", ""),
            data.get("date_of_birth", ""),
            data.get("age", 0),
            data.get("gender", ""),
            data.get("insurance", ""),
            data.get("diagnosis_code", ""),
            data.get("diagnosis_name", ""),
            chronic,
            data.get("admission_date", ""),
            data.get("discharge_date", ""),
            data.get("length_of_stay", 0),
            data.get("ward", ""),
            data.get("num_previous_admissions", 0),
            data.get("admissions_last_6months", 0),
            data.get("medication_count", 0),
            data.get("missed_appointments", 0),
            data.get("bp_systolic"),
            data.get("bp_diastolic"),
            data.get("heart_rate"),
            data.get("temperature"),
            data.get("oxygen_saturation"),
            data.get("respiratory_rate"),
            data.get("bmi"),
            data.get("hemoglobin"),
            data.get("wbc_count"),
            data.get("creatinine"),
            data.get("glucose"),
            data.get("bun"),
            data.get("sodium"),
            data.get("potassium"),
            data.get("smoking_status", "unknown"),
            data.get("alcohol_use", "unknown"),
            int(data.get("lives_alone", False)),
            int(data.get("has_caregiver", True)),
            int(data.get("transportation_access", True)),
            int(data.get("housing_stable", True)),
            data.get("clinical_notes", ""),
            data.get("discharge_hour"),
            int(data.get("is_weekend_discharge", False)),
            data.get("status", "discharged"),
            was_readmitted,
            now, now,
            data.get("created_by", "system"),
        )
    )
    conn.commit()
    conn.close()

    return {"patient_id": patient_id, "status": "created"}


def get_patients_for_hospital(
    hospital_id: str,
    status: Optional[str] = None,
    risk_filter: Optional[str] = None,
    ward_filter: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "risk_score",
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Get patients for a hospital with filters."""
    conn = get_db()

    query = "SELECT * FROM patients WHERE hospital_id = ?"
    params: list = [hospital_id]

    if status and status != "all":
        query += " AND status = ?"
        params.append(status)

    if risk_filter and risk_filter != "all":
        query += " AND risk_level = ?"
        params.append(risk_filter)

    if ward_filter and ward_filter != "all":
        query += " AND ward = ?"
        params.append(ward_filter)

    if search:
        query += " AND (first_name LIKE ? OR last_name LIKE ? OR id LIKE ? OR diagnosis_name LIKE ? OR mrn LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s, s, s])

    # Count total
    count_query = query.replace("SELECT *", "SELECT COUNT(*)")
    total = conn.execute(count_query, params).fetchone()[0]

    # Sort
    sort_map = {
        "risk_score": "risk_score DESC",
        "name": "last_name ASC, first_name ASC",
        "age": "age DESC",
        "discharge_date": "discharge_date DESC",
        "admission_date": "admission_date DESC",
    }
    query += f" ORDER BY {sort_map.get(sort_by, 'risk_score DESC NULLS LAST')}"
    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    conn.close()

    patients = []
    for row in rows:
        p = dict(row)
        p["chronic_conditions"] = json.loads(p.get("chronic_conditions") or "[]")
        p["risk_horizons"] = json.loads(p.get("risk_horizons") or "{}")
        p["name"] = f"{p['first_name']} {p['last_name']}"
        p["patient_id"] = p["id"]
        p["diagnosis"] = p.get("diagnosis_name", "")
        patients.append(p)

    return {"patients": patients, "total": total, "limit": limit, "offset": offset}


def get_patient_by_id(hospital_id: str, patient_id: str) -> Optional[dict]:
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM patients WHERE id = ? AND hospital_id = ?",
        (patient_id, hospital_id)
    ).fetchone()
    conn.close()

    if row:
        p = dict(row)
        p["chronic_conditions"] = json.loads(p.get("chronic_conditions") or "[]")
        p["risk_horizons"] = json.loads(p.get("risk_horizons") or "{}")
        p["name"] = f"{p['first_name']} {p['last_name']}"
        p["patient_id"] = p["id"]
        return p
    return None


def update_patient_risk(patient_id: str, risk_score: float, risk_level: str, horizons: dict):
    conn = get_db()
    conn.execute(
        """UPDATE patients SET risk_score = ?, risk_level = ?, risk_horizons = ?,
           last_scored_at = ?, updated_at = ? WHERE id = ?""",
        (risk_score, risk_level, json.dumps(horizons),
         datetime.now().isoformat(), datetime.now().isoformat(), patient_id)
    )
    conn.commit()
    conn.close()


def update_patient(hospital_id: str, patient_id: str, data: dict):
    conn = get_db()
    sets = []
    params = []
    for key, val in data.items():
        if key in ("id", "hospital_id", "created_at"):
            continue
        if key == "chronic_conditions" and isinstance(val, list):
            val = json.dumps(val)
        sets.append(f"{key} = ?")
        params.append(val)

    sets.append("updated_at = ?")
    params.append(datetime.now().isoformat())
    params.extend([patient_id, hospital_id])

    conn.execute(
        f"UPDATE patients SET {', '.join(sets)} WHERE id = ? AND hospital_id = ?",
        params
    )
    conn.commit()
    conn.close()


def delete_patient(hospital_id: str, patient_id: str):
    conn = get_db()
    conn.execute("DELETE FROM alerts WHERE patient_id = ? AND hospital_id = ?", (patient_id, hospital_id))
    conn.execute("DELETE FROM patients WHERE id = ? AND hospital_id = ?", (patient_id, hospital_id))
    conn.commit()
    conn.close()


def get_patient_count(hospital_id: str) -> int:
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM patients WHERE hospital_id = ?", (hospital_id,)).fetchone()[0]
    conn.close()
    return count


def get_dashboard_stats_db(hospital_id: str) -> dict:
    conn = get_db()

    total = conn.execute("SELECT COUNT(*) FROM patients WHERE hospital_id = ?", (hospital_id,)).fetchone()[0]

    risk_counts = {}
    for level in ("critical", "high", "medium", "low"):
        c = conn.execute(
            "SELECT COUNT(*) FROM patients WHERE hospital_id = ? AND risk_level = ?",
            (hospital_id, level)
        ).fetchone()[0]
        risk_counts[level] = c

    avg_risk = conn.execute(
        "SELECT AVG(risk_score) FROM patients WHERE hospital_id = ? AND risk_score IS NOT NULL",
        (hospital_id,)
    ).fetchone()[0] or 0

    median_row = conn.execute(
        """SELECT risk_score FROM patients WHERE hospital_id = ? AND risk_score IS NOT NULL
           ORDER BY risk_score LIMIT 1 OFFSET (
               SELECT COUNT(*)/2 FROM patients WHERE hospital_id = ? AND risk_score IS NOT NULL
           )""",
        (hospital_id, hospital_id)
    ).fetchone()
    median_risk = median_row[0] if median_row else 0

    # Ward breakdown
    wards = {}
    ward_rows = conn.execute(
        """SELECT ward, COUNT(*) as cnt, AVG(risk_score) as avg_r,
           SUM(CASE WHEN risk_level IN ('high','critical') THEN 1 ELSE 0 END) as high_cnt
           FROM patients WHERE hospital_id = ? AND ward IS NOT NULL AND ward != ''
           GROUP BY ward""",
        (hospital_id,)
    ).fetchall()
    for wr in ward_rows:
        wards[wr["ward"]] = {
            "count": wr["cnt"],
            "avg_risk": round(wr["avg_r"] or 0, 1),
            "high_risk_count": wr["high_cnt"],
        }

    # Age distribution
    age_dist = {}
    for label, lo, hi in [("18-30",18,30),("31-45",31,45),("46-60",46,60),("61-75",61,75),("76+",76,200)]:
        c = conn.execute(
            "SELECT COUNT(*) FROM patients WHERE hospital_id = ? AND age >= ? AND age <= ?",
            (hospital_id, lo, hi)
        ).fetchone()[0]
        age_dist[label] = c

    # Top diagnoses
    dx_rows = conn.execute(
        """SELECT diagnosis_name, COUNT(*) as cnt FROM patients
           WHERE hospital_id = ? AND diagnosis_name IS NOT NULL AND diagnosis_name != ''
           GROUP BY diagnosis_name ORDER BY cnt DESC LIMIT 10""",
        (hospital_id,)
    ).fetchall()
    top_dx = [{"name": r["diagnosis_name"], "count": r["cnt"]} for r in dx_rows]

    # Readmission rate
    discharged = conn.execute(
        "SELECT COUNT(*) FROM patients WHERE hospital_id = ? AND status = 'discharged'",
        (hospital_id,)
    ).fetchone()[0]
    readmitted = conn.execute(
        "SELECT COUNT(*) FROM patients WHERE hospital_id = ? AND was_readmitted = 1",
        (hospital_id,)
    ).fetchone()[0]
    readmission_rate = round((readmitted / max(discharged, 1)) * 100, 1)

    conn.close()

    return {
        "total_patients": total,
        "average_risk_score": round(avg_risk, 1),
        "median_risk_score": round(median_risk, 1),
        "high_risk_count": risk_counts.get("critical", 0) + risk_counts.get("high", 0),
        "risk_distribution": risk_counts,
        "ward_breakdown": wards,
        "age_distribution": age_dist,
        "top_diagnoses": top_dx,
        "readmission_rate": readmission_rate,
    }


# --- Alerts ---

def add_alert(hospital_id: str, patient_id: str, alert_type: str, priority: str, message: str) -> str:
    conn = get_db()
    alert_id = f"ALT-{secrets.token_hex(4).upper()}"
    conn.execute(
        """INSERT INTO alerts (id, hospital_id, patient_id, alert_type, priority, message, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (alert_id, hospital_id, patient_id, alert_type, priority, message, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return alert_id


def get_alerts_db(hospital_id: str, status: Optional[str] = None, priority: Optional[str] = None, limit: int = 50):
    conn = get_db()
    query = """SELECT a.*, p.first_name, p.last_name, p.risk_score, p.risk_level, p.ward
               FROM alerts a JOIN patients p ON a.patient_id = p.id
               WHERE a.hospital_id = ?"""
    params: list = [hospital_id]

    if status:
        query += " AND a.status = ?"
        params.append(status)
    if priority:
        query += " AND a.priority = ?"
        params.append(priority)

    query += " ORDER BY CASE a.priority WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, a.created_at DESC"
    query += " LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()

    # Stats
    stats = {}
    for s in ("active", "acknowledged", "resolved"):
        stats[s] = conn.execute(
            "SELECT COUNT(*) FROM alerts WHERE hospital_id = ? AND status = ?",
            (hospital_id, s)
        ).fetchone()[0]
    stats["total"] = sum(stats.values())

    conn.close()

    alerts = []
    for r in rows:
        a = dict(r)
        a["patient_name"] = f"{a.pop('first_name', '')} {a.pop('last_name', '')}"
        a["alert_id"] = a["id"]
        a["patient_id"] = a["patient_id"]
        alerts.append(a)

    return {"alerts": alerts, "stats": stats}


def update_alert_status(hospital_id: str, alert_id: str, status: str, user: str = "staff"):
    conn = get_db()
    now = datetime.now().isoformat()
    if status == "acknowledged":
        conn.execute(
            "UPDATE alerts SET status = ?, acknowledged_at = ?, acknowledged_by = ? WHERE id = ? AND hospital_id = ?",
            (status, now, user, alert_id, hospital_id)
        )
    elif status == "resolved":
        conn.execute(
            "UPDATE alerts SET status = ?, resolved_at = ?, resolved_by = ? WHERE id = ? AND hospital_id = ?",
            (status, now, user, alert_id, hospital_id)
        )
    conn.commit()
    conn.close()


# --- Audit ---

def log_audit(hospital_id: str, action: str, entity_type: str = "", entity_id: str = "", details: str = "", ip: str = ""):
    conn = get_db()
    conn.execute(
        "INSERT INTO audit_log (hospital_id, action, entity_type, entity_id, details, ip_address, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (hospital_id, action, entity_type, entity_id, details, ip, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


# --- Bootstrap: create a default hospital for first use ---

def bootstrap_default_hospital():
    """Create a default hospital if none exist, for first-time setup."""
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM hospitals").fetchone()[0]
    conn.close()

    if count == 0:
        result = create_hospital(
            name="General Hospital (Partner)",
            email="admin@hospital.org",
            address="",
            city="",
            state="",
            contact_name="Administrator",
        )
        logger.info("=" * 50)
        logger.info("  FIRST-TIME SETUP")
        logger.info(f"  Hospital: {result['name']}")
        logger.info(f"  Access Code: {result['access_code']}")
        logger.info(f"  Share this code with hospital staff to login")
        logger.info("=" * 50)
        return result
    return None
