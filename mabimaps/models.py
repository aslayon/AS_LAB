from pydantic import BaseModel
from typing import Optional

# Pydantic 모델 정의
class ReportData(BaseModel):
    itemName: str
    acquireMethod: str
    acquisition_condition: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    markerId: Optional[int] = None

class MarkerLocation(BaseModel):
    lat: float
    lng: float
