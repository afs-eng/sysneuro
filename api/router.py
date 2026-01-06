from ninja import NinjaAPI
from backend.apps.patients.api import router as patients_router
from backend.apps.assessments.api import router as sessions_router

api = NinjaAPI(title="Neuro API", version="0.1.0")

api.add_router("/patients", patients_router)
api.add_router("/sessions", sessions_router)
