from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.auditor.service import audit_csv
from app.core.schemas import AuditReport


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


@app.post("/api/v1/audit", response_model=AuditReport)
async def audit_dataset(
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="A file is required.",
        )

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported.",
        )

    temporary_path = None

    try:
        contents = await file.read()

        with NamedTemporaryFile(
            delete=False,
            suffix=".csv",
        ) as temporary_file:
            temporary_file.write(contents)
            temporary_path = Path(temporary_file.name)

        result = audit_csv(str(temporary_path))

        # Preserve the original uploaded filename.
        result["dataset"] = file.filename
        result["profile"]["dataset"] = file.filename

        return AuditReport.model_validate(result)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Audit failed: {str(exc)}",
        ) from exc

    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()