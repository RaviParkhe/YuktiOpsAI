from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from src.config import SeverityLevel


class FindingCategory(str, Enum):
    BUG_RISK = "BUG_RISK"
    SECURITY_VULNERABILITY = "SECURITY_VULNERABILITY"
    CODE_QUALITY = "CODE_QUALITY"
    PERFORMANCE = "PERFORMANCE"
    CI_FAILURE = "CI_FAILURE"


class CIStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    UNKNOWN = "UNKNOWN"


class AnalysisRunStatus(str, Enum):
    QUEUED = "QUEUED"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class FindingBase(BaseModel):
    title: str = Field(..., max_length=200, description="Short summary of the finding")
    category: FindingCategory = Field(..., description="Logical agent category")
    severity: SeverityLevel = Field(..., description="Assessed severity level")
    file_path: Optional[str] = Field(None, description="Affected file path")
    line_number: Optional[int] = Field(None, description="Target line number in the diff")
    description: str = Field(..., description="Detailed explanation of the issue")
    recommendation: Optional[str] = Field(None, description="Suggested remedy or mitigation")
    fingerprint: Optional[str] = Field(None, description="Deterministic hash for deduplication")


class FindingCreate(FindingBase):
    pass


class FindingResponse(FindingBase):
    id: str
    run_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PRAnalysisRequest(BaseModel):
    repo_owner: str = Field(..., description="GitHub repository owner/organization")
    repo_name: str = Field(..., description="GitHub repository name")
    pr_number: int = Field(..., description="Pull Request number")
    commit_sha: Optional[str] = Field(None, description="Head commit SHA to analyze")
    installation_id: Optional[int] = Field(None, description="GitHub App installation ID")


class PRAnalysisResponse(BaseModel):
    run_id: str
    repo_full_name: str
    pr_number: int
    commit_sha: str
    status: AnalysisRunStatus
    ci_status: CIStatus
    total_findings: int
    highest_severity: SeverityLevel
    findings: List[FindingResponse] = []
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
