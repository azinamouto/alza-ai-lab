from fastapi import FastAPI

from app.api.auditor import router as auditor_router


app = FastAPI(
    title="ALZA AI Lab",
    description="Local AI Data Quality and Anomaly Detection Server",
    version="0.3.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "ALZA AI Lab",
        "version": "0.3.0",
    }


app.include_router(auditor_router)