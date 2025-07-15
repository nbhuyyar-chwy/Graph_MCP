"""Vet and medical data models for the pet care database."""

from dataclasses import dataclass
import datetime
from typing import Any, Dict, List, Optional

from .base import (
    BaseModel, ValidationError,
    validate_required_field, validate_positive_number,
    parse_date_string, safe_int
)


@dataclass
class Vet(BaseModel):
    """Vet model representing a veterinarian."""
    
    name: str = ""
    clinic: Optional[str] = None
    
    def __post_init__(self):
        """Validate vet data after initialization."""
        validate_required_field(self.name, "name")
    
    @classmethod
    def from_neo4j_record(cls, record: Dict[str, Any]) -> 'Vet':
        """Create Vet instance from Neo4j record."""
        return cls(
            name=record.get("vet_name") or record.get("name", ""),
            clinic=record.get("clinic")
        )


@dataclass
class VetVisit(BaseModel):
    """VetVisit model representing a medical visit."""
    
    visit_date: Optional[datetime.date] = None
    reason: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    follow_up_date: Optional[datetime.date] = None
    notes: Optional[str] = None
    vet: Optional[Vet] = None
    pet_name: Optional[str] = None
    owner_username: Optional[str] = None
    
    @classmethod
    def from_neo4j_record(cls, record: Dict[str, Any]) -> 'VetVisit':
        """Create VetVisit instance from Neo4j record."""
        vet = None
        if record.get("vet_name"):
            vet = Vet(
                name=record.get("vet_name", ""),
                clinic=record.get("clinic")
            )
        
        return cls(
            visit_date=parse_date_string(record.get("visit_date") or record.get("date")),
            reason=record.get("reason"),
            diagnosis=record.get("diagnosis"),
            treatment=record.get("treatment"),
            follow_up_date=parse_date_string(record.get("follow_up_date")),
            notes=record.get("notes"),
            vet=vet,
            pet_name=record.get("pet_name"),
            owner_username=record.get("owner")
        )


@dataclass
class Medication(BaseModel):
    """Medication model representing prescribed treatment."""
    
    medication_name: str = ""
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    start_date: Optional[datetime.date] = None
    duration_days: Optional[int] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    pet_name: Optional[str] = None
    owner_username: Optional[str] = None
    
    def __post_init__(self):
        """Validate medication data after initialization."""
        validate_required_field(self.medication_name, "medication_name")
        
        if self.duration_days is not None:
            validate_positive_number(self.duration_days, "duration_days")
    
    @property
    def is_active(self) -> bool:
        """Check if medication is currently active."""
        if not self.start_date or not self.duration_days:
            return False
        
        end_date = self.start_date + datetime.timedelta(days=self.duration_days)
        return datetime.date.today() <= end_date
    
    @property
    def end_date(self) -> Optional[datetime.date]:
        """Calculate medication end date."""
        if not self.start_date or not self.duration_days:
            return None
        
        return self.start_date + datetime.timedelta(days=self.duration_days)
    
    @classmethod
    def from_neo4j_record(cls, record: Dict[str, Any]) -> 'Medication':
        """Create Medication instance from Neo4j record."""
        return cls(
            medication_name=record.get("medication_name") or record.get("medication", ""),
            dosage=record.get("dosage"),
            frequency=record.get("frequency"),
            start_date=parse_date_string(record.get("start_date")),
            duration_days=safe_int(record.get("duration_days")),
            reason=record.get("reason"),
            notes=record.get("notes"),
            pet_name=record.get("pet_name"),
            owner_username=record.get("owner")
        )


@dataclass
class VetWorkloadSummary(BaseModel):
    """Summary model for vet workload statistics."""
    
    vet: Vet
    total_visits: int = 0
    first_visit: Optional[datetime.date] = None
    last_visit: Optional[datetime.date] = None
    
    @classmethod
    def from_neo4j_record(cls, record: Dict[str, Any]) -> 'VetWorkloadSummary':
        """Create VetWorkloadSummary instance from Neo4j record."""
        vet = Vet.from_neo4j_record(record)
        return cls(
            vet=vet,
            total_visits=safe_int(record.get("total_visits")) or 0,
            first_visit=parse_date_string(record.get("first_visit")),
            last_visit=parse_date_string(record.get("last_visit"))
        )


@dataclass
class MedicalHistory(BaseModel):
    """Complete medical history for a pet."""
    
    pet_name: str
    species: Optional[str] = None
    breed: Optional[str] = None
    owner_username: Optional[str] = None
    vet_visits: Optional[List[VetVisit]] = None
    medications: Optional[List[Medication]] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.vet_visits is None:
            self.vet_visits = []
        if self.medications is None:
            self.medications = []
    
    @property
    def active_medications(self) -> List[Medication]:
        """Get currently active medications."""
        if not self.medications:
            return []
        return [med for med in self.medications if med.is_active]
    
    def recent_visits(self, days: int = 30) -> List[VetVisit]:
        """Get recent vet visits within specified days."""
        if not self.vet_visits:
            return []
        
        cutoff_date = datetime.date.today() - datetime.timedelta(days=days)
        return [visit for visit in self.vet_visits 
                if visit.visit_date and visit.visit_date >= cutoff_date]
    
    @classmethod
    def from_neo4j_record(cls, record: Dict[str, Any]) -> 'MedicalHistory':
        """Create MedicalHistory instance from Neo4j record."""
        vet_visits = []
        medications = []
        
        # Parse vet visits if present
        if record.get("vet_visits"):
            for visit_data in record["vet_visits"]:
                if visit_data.get("visit_date"):  # Skip empty visits
                    vet_visits.append(VetVisit.from_neo4j_record(visit_data))
        
        # Parse medications if present
        if record.get("medications"):
            for med_data in record["medications"]:
                if med_data.get("medication_name"):  # Skip empty medications
                    medications.append(Medication.from_neo4j_record(med_data))
        
        return cls(
            pet_name=record.get("pet_name", ""),
            species=record.get("species"),
            breed=record.get("breed"),
            owner_username=record.get("owner"),
            vet_visits=vet_visits,
            medications=medications
        ) 