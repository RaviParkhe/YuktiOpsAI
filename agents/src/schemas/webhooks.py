from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class WebhookEventResponse(BaseModel):
    event_id: str = Field(..., description="Internal tracking ID for persisted webhook event")
    delivery_id: Optional[str] = Field(None, description="GitHub X-GitHub-Delivery header value")
    event_type: str = Field(..., description="GitHub event type (e.g. pull_request)")
    action: Optional[str] = Field(None, description="Event action (e.g. opened, synchronize)")
    status: str = Field(default="queued", description="Initial queue state")
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
