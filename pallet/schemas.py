# schemas.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum

class MovementStatus(str, Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    COMPLETED = "completed"
    EXCEPTION = "exception"
    CANCELLED = "cancelled"

class MovementType(str, Enum):
    DEPLOYMENT = "deployment"
    RETURN = "return"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"
    DAMAGED_WRITEOFF = "damaged_writeoff"

class LocationType(str, Enum):
    MAIN_BASE = "main_base"
    FORWARD_OPERATING_BASE = "forward_base"
    LOGISTICS_HUB = "logistics_hub"
    AIRFIELD = "airfield"
    STORAGE = "storage"



class LocationBase(BaseModel):
    code: str = Field(..., min_length=3, max_length=20, description="Location code (e.g., DXB-HQ)")
    name: str = Field(..., max_length=100)
    location_type: LocationType = Field(default=LocationType.FORWARD_OPERATING_BASE)
    
    
    max_capacity: Optional[int] = Field(1000, ge=0)
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    coordinates: Optional[str] = None 
    
    region: Optional[str] = None
    is_restricted: bool = True
    classification_level: str = "UNCLASSIFIED"
    operational_status: str = "ACTIVE"

class LocationCreate(LocationBase):
    pass

class LocationResponse(LocationBase):
    created_at: datetime
    updated_at: datetime
    current_stock: int = 0
    
    class Config:
        from_attributes = True

# ========== MOVEMENT SCHEMAS ==========

class MovementBase(BaseModel):
    from_location_code: str
    to_location_code: str
    quantity: int = Field(..., gt=0)
    mission_id: str
    movement_type: MovementType = Field(default=MovementType.DEPLOYMENT)
    status: MovementStatus = Field(default=MovementStatus.COMPLETED)
    priority: str = "Normal"  # Added Priority
    
    reference_id: Optional[str] = None
    movement_date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
    entered_by: Optional[str] = None
    confirmed_by: Optional[str] = None

class MovementCreate(MovementBase):
    @validator('from_location_code', 'to_location_code')
    def uppercase_codes(cls, v):
        return v.upper()

class MovementResponse(MovementBase):
    id: int
    uuid: str
    is_reconciled: bool
    has_discrepancy: bool
    created_at: datetime
    updated_at: datetime
    actual_arrival_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# ========== DASHBOARD SCHEMAS ==========

class DashboardSummary(BaseModel):
    total_pallets: int
    at_base: int
    deployed: int
    in_transit: int
    recent_movements: int
    pending_movements: int
    discrepancies: int
    last_updated: datetime

# ========== REPORT SCHEMAS ==========

class ReconciliationReportResponse(BaseModel):
    id: int
    uuid: str
    report_name: str
    period_start: datetime
    period_end: datetime
    source_filename: str
    total_movements: int
    successful_movements: int
    failed_movements: int
    discrepancies_found: int
    status: str
    processed_by: str
    processed_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class LedgerReport(BaseModel):
    period: dict
    summary: dict
    movements: List[dict]

# ========== BALANCE SCHEMAS ==========

class BalanceResponse(BaseModel):
    location_code: str
    location_name: str
    location_type: str
    quantity: int
    quantity_available: int
    quantity_allocated: int
    last_updated: datetime
    
    class Config:
        from_attributes = True