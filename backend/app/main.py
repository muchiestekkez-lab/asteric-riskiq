"""
Asteric RiskIQ - Production Application

Hospital Readmission Prediction AI Engine
For authorized partner hospitals only.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings, MODEL_DIR
from app.database import init_db, bootstrap_default_hospital
from app.models.ensemble_engine import EnsembleEngine
from app.models.explainability import ExplainabilityEngine
from app.models.anomaly_detection import AnomalyDetector
from app.models.temporal_analysis import TemporalAnalyzer
from app.models.nlp_engine import ClinicalNLPEngine
from app.services.intervention_engine import InterventionEngine
from app.api.routes import router
from app.api.websocket_manager import ws_manager

# Global AI engine instances (shared across requests)
ensemble = EnsembleEngine()
explainer = ExplainabilityEngine(ensemble)
anomaly_detector = AnomalyDetector()
temporal_analyzer = TemporalAnalyzer()
nlp_engine = ClinicalNLPEngine()
intervention_engine = InterventionEngine()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    logger.info("=" * 60)
    logger.info("  ASTERIC RISKIQ - Readmission Prediction AI")
    logger.info("  Production System for Partner Hospitals")
    logger.info("  Version: 1.0.0")
    logger.info("=" * 60)

    # Initialize database
    init_db()

    # Bootstrap default hospital on first run
    boot = bootstrap_default_hospital()

    # Try to load pre-trained models
    if ensemble.load():
        logger.info("Pre-trained AI models loaded successfully")
        explainer.ensemble = ensemble
    else:
        logger.info("No pre-trained models found. Models will train when sufficient patient data is available.")

    logger.info("=" * 60)
    if boot:
        logger.info(f"  ACCESS CODE: {boot['access_code']}")
        logger.info(f"  Use this code to login at the frontend")
    logger.info(f"  API: http://{settings.host}:{settings.port}/docs")
    logger.info(f"  System ready.")
    logger.info("=" * 60)

    yield

    logger.info("Asteric RiskIQ shutting down...")


app = FastAPI(
    title="Asteric RiskIQ",
    description="Hospital Readmission Prediction AI - Partner Access Only",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


# WebSocket endpoint
@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@app.get("/")
async def root():
    return {
        "name": "Asteric RiskIQ",
        "version": "1.0.0",
        "status": "running",
        "access": "Partner hospitals only. Login with your access code.",
    }
