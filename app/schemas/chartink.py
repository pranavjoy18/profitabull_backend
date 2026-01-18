from pydantic import BaseModel
from typing import Optional


class ChartinkWebhookPayload(BaseModel):
    stocks: str
    trigger_prices: Optional[str] = None
    triggered_at: Optional[str] = None
    scan_name: str
    scan_url: str
    alert_name : str
    webhook_url : str
