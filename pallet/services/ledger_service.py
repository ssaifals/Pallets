# services/ledger_service.py
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, desc, text
from sqlalchemy.exc import IntegrityError
import pandas as pd
import hashlib
import json
import logging

# Import from the models file you just created
from models import (
    Location, InventoryBalance, PalletMovement, 
    LedgerAuditLog, ReconciliationReport, ReportMovement,
    AssetType, MovementStatus, MovementType, LocationType
)

logger = logging.getLogger(__name__)

class LedgerService:
    """Core ledger service implementing double-entry bookkeeping"""
    
    def __init__(self, db: Session):
        self.db = db

    # =========================================================
    # 🛠️ HELPER PROPERTIES
    # =========================================================
    @property
    def engine(self):
        """Exposes the SQLAlchemy engine for raw SQL queries."""
        return self.db.get_bind()

    def create_movement(self, data: dict) -> Tuple[bool, str]:
        """
        Adapter method for app.py to call record_movement easily.
        """
        try:
            return self.record_movement(
                mission_id=data.get('mission'),
                from_location_code=data.get('from'),
                to_location_code=data.get('to'),
                quantity=int(data.get('qty', 0)),
                movement_type=data.get('type', 'Deployment'),
                priority=data.get('priority', 'Normal'),
                notes=data.get('notes'),
                confirmed_by=data.get('confirmed', 'System')
            )
        except Exception as e:
            return False, str(e)

    # =========================================================
    # 📍 LOCATION MANAGEMENT
    # =========================================================
    
    def create_location(self, code: str, name: str, location_type: str = "forward_base", 
                       max_capacity: int = 1000, status: str = "active",
                       contact_person: str = None, contact_phone: str = None, 
                       coordinates: str = None) -> Tuple[bool, str]:
        """Create a new location with contact and map info."""
        try:
            location = Location(
                code=code.upper(),
                name=name,
                location_type=location_type,
                max_capacity=max_capacity,
                operational_status=status,
                contact_person=contact_person,
                contact_phone=contact_phone,
                coordinates=coordinates,
                current_stock=0
            )
            self.db.add(location)
            
            # Create Initial Ledger Balance
            balance = InventoryBalance(
                location_code=code.upper(),
                quantity=0,
                quantity_allocated=0,
                quantity_available=0
            )
            self.db.add(balance)
            
            self.db.commit()
            self._log_audit("CREATE", "locations", code, {"name": name})
            return True, "Location created successfully"
            
        except IntegrityError:
            self.db.rollback()
            return False, f"Location {code} already exists"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def get_locations(self, filters=None) -> List[Dict]:
        """Get locations as a list of dictionaries for UI."""
        query = self.db.query(Location)
        
        if filters:
            if filters.get('status') and filters['status'] != 'All':
                query = query.filter(Location.operational_status == filters['status'])
            if filters.get('location_type') and filters['location_type'] != 'All':
                query = query.filter(Location.location_type == filters['location_type'])
                
        locations = query.order_by(Location.code).all()
        
        result = []
        for loc in locations:
            result.append({
                "code": loc.code,
                "name": loc.name,
                "location_type": loc.location_type,
                "status": loc.operational_status,
                "current_stock": loc.current_stock if loc.current_stock is not None else 0,
                "max_capacity": loc.max_capacity,
                "contact_person": loc.contact_person,
                "coordinates": loc.coordinates
            })
        return result
    
    def get_location_balance(self, location_code: str) -> Optional[InventoryBalance]:
        return self.db.query(InventoryBalance).filter(
            InventoryBalance.location_code == location_code.upper()
        ).first()

    def update_location(self, code: str, data: dict):
        loc = self.db.query(Location).filter_by(code=code.upper()).first()
        if loc:
            for k, v in data.items():
                if hasattr(loc, k) and v is not None:
                    setattr(loc, k, v)
            self._log_audit("UPDATE", "locations", code, data)
            self.db.commit()
            return True
        return False

    def delete_location(self, code: str):
        moves = self.db.query(PalletMovement).filter(
            or_(PalletMovement.from_location_code == code, PalletMovement.to_location_code == code)
        ).count()
        
        if moves > 0:
            return False, f"Cannot delete: Has {moves} historical movements."
        
        self.db.query(InventoryBalance).filter_by(location_code=code).delete()
        self.db.query(Location).filter_by(code=code).delete()
        self.db.commit()
        return True, "Deleted successfully"

    # =========================================================
    # ✈️ LEDGER TRANSACTIONS
    # =========================================================
    
    def record_movement(self, 
                       mission_id: str,
                       from_location_code: str,
                       to_location_code: str,
                       quantity: int,
                       movement_type: str = MovementType.DEPLOYMENT,
                       priority: str = "Normal",
                       notes: str = None,
                       confirmed_by: str = "System",
                       reference_id: str = None,
                       movement_date: datetime = None) -> Tuple[bool, str]:
        """Record movement with Double-Entry Bookkeeping."""
        
        # 1. Basic Validations
        if not from_location_code or not to_location_code:
            return False, "Locations cannot be empty"

        if from_location_code.upper() == to_location_code.upper():
            return False, "Source and destination cannot be the same"
        
        if quantity <= 0:
            return False, "Quantity must be positive"

        # --- 🛠️ AUTO-FIX: Create 'SYSTEM' Location if missing ---
        for code in [from_location_code, to_location_code]:
            if code.upper() == "SYSTEM":
                sys_loc = self.db.query(Location).filter_by(code="SYSTEM").first()
                if not sys_loc:
                    try:
                        new_sys = Location(
                            code="SYSTEM", 
                            name="System Adjustment Account", 
                            location_type="Virtual", 
                            operational_status="active",
                            max_capacity=999999
                        )
                        self.db.add(new_sys)
                        self.db.add(InventoryBalance(location_code="SYSTEM", quantity=0))
                        self.db.commit()
                    except Exception as e:
                        self.db.rollback()
                        print(f"Failed to auto-create SYSTEM location: {e}")
        # ---------------------------------------------------
        
        # 2. Check Balances
        source_balance = self.get_location_balance(from_location_code)
        dest_balance = self.get_location_balance(to_location_code)
        
        # Auto-create destination balance if it doesn't exist yet
        if not dest_balance:
            loc_exists = self.db.query(Location).filter_by(code=to_location_code.upper()).first()
            if not loc_exists:
                return False, f"Destination {to_location_code} does not exist"
            
            dest_balance = InventoryBalance(location_code=to_location_code.upper(), quantity=0)
            self.db.add(dest_balance)
        
        if not source_balance:
            return False, f"Source location {from_location_code} not found or initialized"
        
        # 3. Check Stock (SYSTEM account is allowed to go negative)
        if from_location_code.upper() != "SYSTEM" and source_balance.quantity < quantity:
            return False, f"Insufficient stock at {from_location_code}. Available: {source_balance.quantity}"
        
        try:
            # 4. Create Movement Record
            movement = PalletMovement(
                from_location_code=from_location_code.upper(),
                to_location_code=to_location_code.upper(),
                quantity=quantity,
                mission_id=mission_id,
                movement_type=movement_type,
                priority=priority,
                reference_id=reference_id or f"MVT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                movement_date=movement_date or datetime.utcnow(),
                notes=notes,
                confirmed_by=confirmed_by,
                status=MovementStatus.COMPLETED
            )
            self.db.add(movement)
            self.db.flush()
            
            # 5. Update Ledger Balances
            source_balance_before = source_balance.quantity
            source_balance.quantity -= quantity
            source_balance.update_available_quantity() 
            
            dest_balance_before = dest_balance.quantity
            dest_balance.quantity += quantity
            dest_balance.update_available_quantity()
            
            # 6. Update Fast-Read Cache on Location Table
            if source_balance.location:
                source_balance.location.current_stock = source_balance.quantity
            if dest_balance.location:
                dest_balance.location.current_stock = dest_balance.quantity

            # 7. Create Audit Log
            audit_log = LedgerAuditLog(
                movement_id=movement.id,
                debit_location_code=from_location_code.upper(),
                credit_location_code=to_location_code.upper(),
                quantity=quantity,
                debit_balance_before=source_balance_before,
                debit_balance_after=source_balance.quantity,
                credit_balance_before=dest_balance_before,
                credit_balance_after=dest_balance.quantity,
                user_id=confirmed_by,
                action="MOVEMENT",
                table_name="movements"
            )
            self.db.add(audit_log)
            
            self.db.commit()
            return True, "Movement recorded successfully"
            
        except Exception as e:
            self.db.rollback()
            return False, str(e)
    
    def get_movements(self, limit=100, filters=None) -> List[Dict]:
        """Get recent movements with filtering."""
        query = self.db.query(PalletMovement)
        
        if filters:
            if filters.get('mission_id'):
                query = query.filter(PalletMovement.mission_id.ilike(f"%{filters['mission_id']}%"))
            
            if filters.get('status') and filters['status'] != 'All':
                query = query.filter(PalletMovement.status == filters['status'])
            
            if filters.get('start_date'):
                # PostgreSQL-safe date comparison
                start_dt = filters['start_date']
                if isinstance(start_dt, datetime): start_dt = start_dt.date()
                query = query.filter(func.date(PalletMovement.movement_date) >= start_dt)

            if filters.get('end_date'):
                end_dt = filters['end_date']
                if isinstance(end_dt, datetime): end_dt = end_dt.date()
                query = query.filter(func.date(PalletMovement.movement_date) <= end_dt)
        
        results = query.order_by(desc(PalletMovement.movement_date)).limit(limit).all()
        
        return [{
            "timestamp": m.movement_date, 
            "mission_id": m.mission_id,
            "from_location_code": m.from_location_code,
            "to_location_code": m.to_location_code,
            "quantity": m.quantity,
            "movement_type": m.movement_type,
            "status": m.status,
            "priority": m.priority,
            "confirmed_by": m.confirmed_by,
            "from_code": m.from_location_code,
            "to_code": m.to_location_code
        } for m in results]

    # =========================================================
    # 📥 EXCEL INGESTION
    # =========================================================
    
    def ingest_excel_file(self, 
                         file_path: str,
                         report_name: str,
                         period_start: datetime,
                         period_end: datetime,
                         processed_by: str) -> ReconciliationReport:
        try:
            # Requires 'openpyxl' installed
            df = pd.read_excel(file_path)
            
            # Simple hash for duplicate checking
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            existing = self.db.query(ReconciliationReport).filter_by(file_hash=file_hash).first()
            if existing:
                return existing
            
            report = ReconciliationReport(
                report_name=report_name,
                period_start=period_start,
                period_end=period_end,
                source_filename=file_path,
                file_hash=file_hash,
                processed_by=processed_by,
                status="PROCESSING"
            )
            self.db.add(report)
            self.db.flush()
            
            results = {"total": len(df), "success": 0, "failed": 0, "errors": []}
            
            for idx, row in df.iterrows():
                try:
                    # Using a nested transaction block so one fail doesn't kill the whole batch
                    with self.db.begin_nested():
                        # Normalize keys to lower case
                        row_dict = {str(k).lower().strip(): v for k, v in row.to_dict().items()}
                        
                        # Fuzzy match column names
                        date_col = next((k for k in row_dict if 'date' in k), None)
                        mission_col = next((k for k in row_dict if any(x in k for x in ['flight', 'mission'])), None)
                        from_col = next((k for k in row_dict if 'from' in k), None)
                        to_col = next((k for k in row_dict if 'to' in k), None)
                        qty_col = next((k for k in row_dict if any(x in k for x in ['qty', 'quantity'])), None)
                        
                        if not all([date_col, mission_col, from_col, to_col, qty_col]):
                            raise ValueError(f"Missing required columns. Found: {list(row_dict.keys())}")
                        
                        # Extract Values
                        mission = str(row_dict[mission_col]).strip()
                        f_loc = str(row_dict[from_col]).strip().upper()
                        t_loc = str(row_dict[to_col]).strip().upper()
                        qty = int(float(row_dict[qty_col]))
                        
                        # EXECUTE MOVEMENT
                        success, msg = self.create_movement({
                            "mission": mission,
                            "from": f_loc,
                            "to": t_loc,
                            "qty": qty,
                            "type": "Transfer",
                            "notes": "Excel Import",
                            "confirmed": processed_by
                        })
                        
                        if success:
                            results["success"] += 1
                        else:
                            # If logic failed (e.g. low stock), capture the error
                            raise ValueError(msg)

                except Exception as e:
                    results["failed"] += 1
                    err = f"Row {idx+2}: {str(e)}"
                    results["errors"].append(err)
            
            report.total_movements = results["total"]
            report.successful_movements = results["success"]
            report.failed_movements = results["failed"]
            report.status = "COMPLETED" if results["failed"] == 0 else "COMPLETED_WITH_ERRORS"
            report.completed_at = datetime.utcnow()
            if results["errors"]:
                report.processing_errors = "\n".join(results["errors"][:50])
            
            self.db.commit()
            return report
            
        except Exception as e:
            self.db.rollback()
            raise e

    # =========================================================
    # 📊 DASHBOARD METRICS
    # =========================================================
    
    def get_dashboard_summary(self) -> Dict:
        # Sum of all stock in physical locations (exclude SYSTEM)
        total_pallets = self.db.query(func.sum(InventoryBalance.quantity))\
            .filter(InventoryBalance.location_code != 'SYSTEM').scalar() or 0
        
        in_transit = self.db.query(func.sum(PalletMovement.quantity)).filter(
            PalletMovement.status == MovementStatus.IN_TRANSIT
        ).scalar() or 0
        
        # Count discrepancies
        discrepancies = self.db.query(PalletMovement).filter(PalletMovement.has_discrepancy == True).count()
        
        return {
            "total_pallets": total_pallets,
            "in_transit": in_transit,
            "discrepancies": discrepancies,
            "last_updated": datetime.utcnow()
        }
    
    def _log_audit(self, action, table, record_id, details):
        """Helper to create audit logs silently."""
        try:
            self.db.add(LedgerAuditLog(
                action=action, 
                table_name=table, 
                record_id=str(record_id),
                details=json.dumps(details, default=str),
                user_id="System",
                quantity=0
            ))
        except:
            pass