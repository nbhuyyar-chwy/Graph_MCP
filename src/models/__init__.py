"""
Data models for the pet care database.

This package contains all data models and schemas used throughout
the application for representing pets, users, vets, products,
medications, visits, and sessions.
"""

from .base import (
    BaseModel,
    Gender,
    InteractionType,
    Species,
    ValidationError,
    validate_required_field,
    validate_positive_number,
    validate_rating,
    validate_date,
    validate_enum_value,
    parse_date_string,
    safe_float,
    safe_int
)

from .pets import Pet, PetSummary, PetHealthSummary
from .users import User, UserSummary  
from .vets import Vet, VetVisit, Medication, VetWorkloadSummary, MedicalHistory
from .products import Product, ProductInteraction
from .sessions import (
    Session, 
    SessionEvent, 
    SessionSummary, 
    SessionAnalysisResult,
    SessionImportance,
    SessionChannel,
    EventCategory
)

__all__ = [
    # Base types
    "BaseModel",
    "Gender", 
    "InteractionType",
    "Species",
    "ValidationError",
    "validate_required_field",
    "validate_positive_number", 
    "validate_rating",
    "validate_date",
    "validate_enum_value",
    "parse_date_string",
    "safe_float",
    "safe_int",
    
    # Pet models
    "Pet",
    "PetSummary",
    "PetHealthSummary",
    
    # User models  
    "User",
    "UserSummary",
    
    # Vet models
    "Vet",
    "VetVisit", 
    "Medication",
    "VetWorkloadSummary",
    "MedicalHistory",
    
    # Product models
    "Product",
    "ProductInteraction", 
    
    # Session models
    "Session",
    "SessionEvent",
    "SessionSummary", 
    "SessionAnalysisResult",
    "SessionImportance",
    "SessionChannel",
    "EventCategory"
] 