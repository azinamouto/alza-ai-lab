from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.auditor.service import audit_csv
from app.core.schemas import AuditReport


router = APIRouter(
    prefix="/api/v1",
    tags=["Auditor"],
)

MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post(
    "/audit",
    response_model=AuditReport,
)
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

        if not contents:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty.",
            )

        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="The uploaded file exceeds the 10 MB limit.",
            )

        with NamedTemporaryFile(
            delete=False,
            suffix=".csv",
        ) as temporary_file:
            temporary_file.write(contents)
            temporary_path = Path(temporary_file.name)

        result = audit_csv(str(temporary_path))

        result["dataset"] = file.filename
        result["profile"]["dataset"] = file.filename

        return AuditReport.model_validate(result)

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Audit failed: {str(exc)}",
        ) from exc

    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()