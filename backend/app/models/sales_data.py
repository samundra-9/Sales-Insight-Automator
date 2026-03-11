
from pydantic import BaseModel
from typing import Dict, List, Any, Optional

class Anomaly(BaseModel):
    type: str
    description: str
    severity: str

class AISummaryOutput(BaseModel):
    executive_summary: str
    key_insights: List[str]
    warnings_anomalies: List[str]
    detected_anomalies: Optional[List[Anomaly]] = None # New field for detected anomalies

class SalesSummary(BaseModel):
    analytics: Dict[str, Any]
    ai_summary: AISummaryOutput
