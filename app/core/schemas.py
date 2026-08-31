from typing import Any, Literal

from pydantic import BaseModel, Field


Severity = Literal["WARNING", "ERROR"]
AuditStatus = Literal["PASS", "WARNING", "REVIEW_REQUIRED"]


class ColumnProfile(BaseModel):
    name: str
    dtype: str
    missing: int = Field(ge=0)
    missing_percentage: float = Field(ge=0, le=100)
    unique_values: int = Field(ge=0)


class DatasetProfile(BaseModel):
    dataset: str
    rows: int = Field(ge=0)
    columns: int = Field(ge=0)
    duplicate_rows: int = Field(ge=0)
    column_profiles: list[ColumnProfile]


class ColumnRule(BaseModel):
    column: str
    expected_dtype: str | None = None
    required: bool = False
    nullable: bool = True
    minimum: float | int | None = None
    maximum: float | int | None = None
    allowed_values: list[Any] | None = None
    unique: bool = False
    severity: Severity | None = None
    include_in_ml: bool | None = None


class AuditIssue(BaseModel):
    type: str
    column: str | None = None
    row: int | None = None
    value: Any = None
    count: int | None = None
    severity: Severity
    message: str


class MLAnomaly(BaseModel):
    type: Literal["ML_ANOMALY"] = "ML_ANOMALY"
    row: int
    anomaly_score: float
    severity: Literal["WARNING"] = "WARNING"
    message: str


class MLAnalysis(BaseModel):
    model: str
    anomalies_detected: int = Field(ge=0)
    anomalies: list[MLAnomaly]


class AuditSummary(BaseModel):
    total_issues: int = Field(ge=0)
    errors: int = Field(ge=0)
    warnings: int = Field(ge=0)
    ml_anomalies: int = Field(ge=0)
    status: AuditStatus


class AuditReport(BaseModel):
    dataset: str
    profile: DatasetProfile
    summary: AuditSummary
    issues: list[AuditIssue]
    ml_analysis: MLAnalysis