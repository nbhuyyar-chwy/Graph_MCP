"""Data models for the pet care database entities."""

from .base import BaseModel, Gender, Species, InteractionType, ValidationError
from .users import User, UserSummary
from .pets import Pet, PetHealthSummary, PetSearchCriteria
from .vets import Vet, VetVisit, Medication, VetWorkloadSummary, MedicalHistory
from .products import Product, ProductInteraction, ProductRating, PopularProduct, ProductSearchCriteria

__all__ = [
    # Base types
    "BaseModel", "Gender", "Species", "InteractionType", "ValidationError",
    
    # User models
    "User", "UserSummary",
    
    # Pet models
    "Pet", "PetHealthSummary", "PetSearchCriteria",
    
    # Vet/Medical models
    "Vet", "VetVisit", "Medication", "VetWorkloadSummary", "MedicalHistory",
    
    # Product models
    "Product", "ProductInteraction", "ProductRating", "PopularProduct", "ProductSearchCriteria",
] 