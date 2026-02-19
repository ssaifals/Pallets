# models.py
from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Boolean, 
    Text, Numeric, CheckConstraint, Index, Float
)
from sqlalchemy.orm import declarative_base, relationship, validates
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
import uuid

Base = declarative_base()


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



class Location(Base):
    """The 'Bank Account' (Base or Station)"""
    __tablename__ = 'locations'
    
    code = Column(String(20), primary_key=True)  
    name = Column(String(100), nullable=False)
    location_type = Column(String(50), default=LocationType.FORWARD_OPERATING_BASE)
    
   
    contact_person = Column(String(100), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    coordinates = Column(String(100), nullable=True) 
    
    
    is_restricted = Column(Boolean, default=True)
    classification_level = Column(String(20), default="UNCLASSIFIED")
    
    
    region = Column(String(50))
    timezone = Column(String(50), default="UTC")
    
    
    max_capacity = Column(Integer, default=1000)
    current_stock = Column(Integer, default=0) 
    operational_status = Column(String(20), default="ACTIVE")
    
   
    inventory_balances = relationship("InventoryBalance", back_populates="location", 
                                    cascade="all, delete-orphan")
    outgoing_movements = relationship("PalletMovement", 
                                     foreign_keys="PalletMovement.from_location_code",
                                     back_populates="from_location")
    incoming_movements = relationship("PalletMovement",
                                     foreign_keys="PalletMovement.to_location_code",
                                     back_populates="to_location")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_location_region', 'region'),
        Index('idx_location_status', 'operational_status'),
    )
    
    @validates('code')
    def validate_code(self, key, code):
        if not code or len(code) < 3:
            raise ValueError("Location code must be at least 3 characters")
        return code.upper()

class AssetType(Base):
    """Catalog of allowable items (Pallets, Containers, etc.)"""
    __tablename__ = 'asset_types'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False) 
    name = Column(String(100), nullable=False)
    category = Column(String(50))
    weight_kg = Column(Float, default=0.0)
    dimensions = Column(String(50))
    requires_special_handling = Column(Boolean, default=False)

class InventoryBalance(Base):
    """The 'Current Balance' - SINGLE SOURCE OF TRUTH"""
    __tablename__ = 'inventory_balances'
    
    id = Column(Integer, primary_key=True, index=True)
    location_code = Column(String(20), ForeignKey('locations.code', ondelete="CASCADE"), 
                          nullable=False, index=True)
    
    pallet_type = Column(String(30), default="108x88_STD", index=True)
    
    quantity = Column(Integer, default=0, nullable=False)
    quantity_allocated = Column(Integer, default=0)
    quantity_available = Column(Integer, default=0)
    
    unit_value_usd = Column(Numeric(10, 2), default=0.00)
    total_value_usd = Column(Numeric(12, 2), default=0.00)
    
    last_movement_id = Column(Integer, ForeignKey('pallet_movements.id'), nullable=True)
    last_movement_date = Column(DateTime, nullable=True)
    
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    location = relationship("Location", back_populates="inventory_balances")
    last_movement = relationship("PalletMovement", foreign_keys=[last_movement_id])
    
    __table_args__ = (
        Index('idx_inventory_location_type', 'location_code', 'pallet_type', unique=True),
        Index('idx_inventory_quantity', 'quantity'),
    )
    
    def update_available_quantity(self):
        self.quantity_available = max(0, self.quantity - self.quantity_allocated)
        return self.quantity_available

class PalletMovement(Base):
    """The 'Transaction' - IMMUTABLE RECORD"""
    __tablename__ = 'pallet_movements'
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    
    reference_id = Column(String(100), index=True)
    mission_id = Column(String(50), index=True)
    movement_date = Column(DateTime, default=datetime.utcnow, index=True)
    expected_arrival_date = Column(DateTime, nullable=True)
    actual_arrival_date = Column(DateTime, nullable=True)
    
    from_location_code = Column(String(20), ForeignKey('locations.code'), nullable=False, index=True)
    to_location_code = Column(String(20), ForeignKey('locations.code'), nullable=False, index=True)
    
    quantity = Column(Integer, nullable=False)
    
    status = Column(String(20), default=MovementStatus.PENDING, index=True)
    movement_type = Column(String(20), default=MovementType.DEPLOYMENT, index=True)
    priority = Column(String(20), default="Normal") 
    
    declared_value_usd = Column(Numeric(12, 2), nullable=True)
    transportation_cost_usd = Column(Numeric(10, 2), nullable=True)
    
    notes = Column(Text, nullable=True)
    source_file = Column(String(255), nullable=True)
    source_file_row = Column(Integer, nullable=True)
    
    is_reconciled = Column(Boolean, default=False)
    has_discrepancy = Column(Boolean, default=False)
    discrepancy_notes = Column(Text, nullable=True)
    
    entered_by = Column(String(100), nullable=True)
    confirmed_by = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    from_location = relationship("Location", foreign_keys=[from_location_code], 
                                back_populates="outgoing_movements")
    to_location = relationship("Location", foreign_keys=[to_location_code], 
                              back_populates="incoming_movements")
    
    __table_args__ = (
        Index('idx_movement_dates', 'movement_date', 'expected_arrival_date'),
        Index('idx_movement_locations', 'from_location_code', 'to_location_code'),
        CheckConstraint('quantity > 0', name='positive_quantity'),
        CheckConstraint('from_location_code != to_location_code', name='different_locations'),
    )
    
    @validates('quantity')
    def validate_quantity(self, key, quantity):
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        return quantity

class LedgerAuditLog(Base):
    """Immutable audit log for balance changes"""
    __tablename__ = 'ledger_audit_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    movement_id = Column(Integer, ForeignKey('pallet_movements.id'), index=True)
    
    debit_location_code = Column(String(20), ForeignKey('locations.code'), nullable=True)
    credit_location_code = Column(String(20), ForeignKey('locations.code'), nullable=True)
    
    quantity = Column(Integer, nullable=False)
    
    
    user_id = Column(String(50), nullable=True) 
    action = Column(String(50), nullable=True)  
    table_name = Column(String(50), nullable=True) 
    record_id = Column(String(100), nullable=True) 
    details = Column(Text, nullable=True) 
    
    debit_balance_before = Column(Integer, nullable=True)
    debit_balance_after = Column(Integer, nullable=True)
    credit_balance_before = Column(Integer, nullable=True)
    credit_balance_after = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    movement = relationship("PalletMovement")
    debit_location = relationship("Location", foreign_keys=[debit_location_code])
    credit_location = relationship("Location", foreign_keys=[credit_location_code])

class ReconciliationReport(Base):
    """Reports generated from Excel uploads"""
    __tablename__ = 'reconciliation_reports'
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    
    report_name = Column(String(255), nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    source_filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), unique=True)
    
    total_movements = Column(Integer, default=0)
    successful_movements = Column(Integer, default=0)
    failed_movements = Column(Integer, default=0)
    discrepancies_found = Column(Integer, default=0)
    
    status = Column(String(50), default="PROCESSING")
    processing_errors = Column(Text, nullable=True)
    
    processed_by = Column(String(100))
    processed_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    movements = relationship("PalletMovement", secondary="report_movements", viewonly=True)

class ReportMovement(Base):
    __tablename__ = 'report_movements'
    
    report_id = Column(Integer, ForeignKey('reconciliation_reports.id'), primary_key=True)
    movement_id = Column(Integer, ForeignKey('pallet_movements.id'), primary_key=True)
    added_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    """Authentication and Role Management"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String) 
    role = Column(String, default="Viewer") 
    last_login = Column(DateTime, default=datetime.utcnow)