from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ProposalStatus(str, Enum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class ProposalResponse(BaseModel):
    id: str
    run_id: str
    finding_id: Optional[str] = None
    title: str = Field(..., description="Summary of the proposed change")
    description: str = Field(..., description="Rationale for the proposed change")
    diff_patch: str = Field(..., description="Proposed bounded git diff patch")
    target_branch: str = Field(..., description="Branch or PR head the fix targets")
    status: ProposalStatus = Field(default=ProposalStatus.PROPOSED)
    github_draft_pr_url: Optional[str] = Field(None, description="URL of created draft PR upon approval")
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProposalApprovalRequest(BaseModel):
    reviewer_id: str = Field(..., description="Identity or username of the approving human")
    comments: Optional[str] = Field(None, description="Optional approval notes or feedback")
    create_draft_pr: bool = Field(
        default=True,
        description="Whether to execute GitHub App action to create a Draft PR for this proposal",
    )


class ProposalRejectionRequest(BaseModel):
    reviewer_id: str = Field(..., description="Identity or username of the rejecting human")
    reason: str = Field(..., min_length=3, description="Reason for rejection")
