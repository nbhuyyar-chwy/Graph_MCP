"""Pet data models for the pet care database."""

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional

from .base import (
    BaseModel, Gender, Species, ValidationError,
    validate_required_field, validate_positive_number, validate_enum_value,
    parse_date_string, safe_float, safe_int
)


@dataclass
class Pet(BaseModel):
    """Pet model representing an individual pet."""
    
    name: str = ""
    species: Optional[str] = None
    breed: Optional[str] = None
    birth_date: Optional[date] = None
    weight_kg: Optional[float] = None
    gender: Optional[str] = None
    color: Optional[str] = None
    microchip_id: Optional[str] = None
    owner_username: Optional[str] = None  # For convenience in queries
    
    def __post_init__(self):
        """Validate pet data after initialization."""
        validate_required_field(self.name, "name")
        
        if self.weight_kg is not None:
            validate_positive_number(self.weight_kg, "weight_kg")
        
        if self.gender is not None:
            validate_enum_value(self.gender, Gender, "gender")
        
        if self.species is not None:
            validate_enum_value(self.species, Species, "species")
    
    @property
    def age_years(self) -> Optional[float]:
        """Calculate pet's age in years."""
        if not self.birth_date:
            return None
        
        today = date.today()
        age_days = (today - self.birth_date).days
        return round(age_days / 365.25, 1)
    
    @classmethod
    def from_neo4j_record(cls, record: Dict[str, Any]) -> 'Pet':
        """Create Pet instance from Neo4j record."""
        return cls(
            name=record.get("pet_name") or record.get("name", ""),
            species=record.get("species"),
            breed=record.get("breed"),
            birth_date=parse_date_string(record.get("birth_date")),
            weight_kg=safe_float(record.get("weight") or record.get("weight_kg")),
            gender=record.get("gender"),
            color=record.get("color"),
            microchip_id=record.get("microchip_id"),
            owner_username=record.get("owner")
        )


@dataclass
class PetHealthSummary(BaseModel):
    """Health summary model for a pet."""
    
    pet: Pet
    total_vet_visits: int = 0
    total_medications: int = 0
    last_vet_visit: Optional[date] = None
    active_medications: Optional[List[str]] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.active_medications is None:
            self.active_medications = []
    
    @classmethod
    def from_neo4j_record(cls, record: Dict[str, Any]) -> 'PetHealthSummary':
        """Create PetHealthSummary instance from Neo4j record."""
        pet = Pet.from_neo4j_record(record)
        return cls(
            pet=pet,
            total_vet_visits=safe_int(record.get("total_vet_visits")) or 0,
            total_medications=safe_int(record.get("total_medications")) or 0,
            last_vet_visit=parse_date_string(record.get("last_vet_visit")),
            active_medications=record.get("active_medications", [])
        )


@dataclass
class PetSearchCriteria:
    """Search criteria for finding pets."""
    
    species: Optional[str] = None
    breed: Optional[str] = None
    min_weight: Optional[float] = None
    max_weight: Optional[float] = None
    gender: Optional[str] = None
    min_age_years: Optional[float] = None
    max_age_years: Optional[float] = None
    owner_username: Optional[str] = None
    
    def validate(self) -> None:
        """Validate search criteria."""
        if self.min_weight is not None and self.min_weight <= 0:
            raise ValidationError("min_weight", self.min_weight, "Must be positive")
        
        if self.max_weight is not None and self.max_weight <= 0:
            raise ValidationError("max_weight", self.max_weight, "Must be positive")
        
        if (self.min_weight is not None and self.max_weight is not None 
            and self.min_weight > self.max_weight):
            raise ValidationError("weight_range", f"{self.min_weight}-{self.max_weight}", 
                                "Min weight cannot be greater than max weight")
        
        if self.min_age_years is not None and self.min_age_years < 0:
            raise ValidationError("min_age_years", self.min_age_years, "Must be non-negative")
        
        if self.max_age_years is not None and self.max_age_years < 0:
            raise ValidationError("max_age_years", self.max_age_years, "Must be non-negative")
        
        if (self.min_age_years is not None and self.max_age_years is not None 
            and self.min_age_years > self.max_age_years):
            raise ValidationError("age_range", f"{self.min_age_years}-{self.max_age_years}", 
                                "Min age cannot be greater than max age")
    
    def to_query_parameters(self) -> Dict[str, Any]:
        """Convert criteria to query parameters."""
        self.validate()
        params = {}
        
        if self.species:
            params["species"] = self.species
        if self.breed:
            params["breed"] = self.breed
        if self.min_weight is not None:
            params["min_weight"] = self.min_weight
        if self.max_weight is not None:
            params["max_weight"] = self.max_weight
        if self.gender:
            params["gender"] = self.gender
        if self.owner_username:
            params["owner_username"] = self.owner_username
        
        return params 