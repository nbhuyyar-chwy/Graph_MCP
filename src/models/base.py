"""
Base data models and common types for the pet care database.

This module defines common data structures and base classes
used throughout the application.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import json


class Gender(Enum):
    """Pet gender enumeration."""
    MALE = "Male"
    FEMALE = "Female"
    UNKNOWN = "Unknown"


class InteractionType(Enum):
    """Product interaction type enumeration."""
    PURCHASE = "Purchase"
    TRIAL = "Trial"
    REVIEW = "Review"
    RETURN = "Return"
    RECOMMENDATION = "Recommendation"


class Species(Enum):
    """Common pet species enumeration."""
    DOG = "Dog"
    CAT = "Cat"
    BIRD = "Bird"
    FISH = "Fish"
    RABBIT = "Rabbit"
    HAMSTER = "Hamster"
    GUINEA_PIG = "Guinea Pig"
    OTHER = "Other"


@dataclass
class BaseModel(ABC):
    """Base class for all data models."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, (date, datetime)):
                result[key] = value.isoformat()
            elif isinstance(value, Enum):
                result[key] = value.value
            elif isinstance(value, BaseModel):
                result[key] = value.to_dict()
            elif isinstance(value, list) and value and isinstance(value[0], BaseModel):
                result[key] = [item.to_dict() for item in value]
            else:
                result[key] = value
        return result
    
    def to_json(self) -> str:
        """Convert model to JSON string."""
        return json.dumps(self.to_dict(), default=str, indent=2)
    
    @classmethod
    @abstractmethod
    def from_neo4j_record(cls, record: Dict[str, Any]) -> 'BaseModel':
        """Create model instance from Neo4j record."""
        pass


@dataclass
class ValidationError(Exception):
    """Custom exception for validation errors."""
    field: str
    value: Any
    message: str
    
    def __str__(self) -> str:
        return f"Validation error for field '{self.field}' with value '{self.value}': {self.message}"


def validate_required_field(value: Any, field_name: str) -> None:
    """Validate that a required field has a value."""
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValidationError(field_name, value, "Field is required")


def validate_positive_number(value: Any, field_name: str) -> None:
    """Validate that a number is positive."""
    if not isinstance(value, (int, float)) or value <= 0:
        raise ValidationError(field_name, value, "Must be a positive number")


def validate_rating(value: Any, field_name: str) -> None:
    """Validate that a rating is between 1 and 5."""
    if not isinstance(value, (int, float)) or not (1 <= value <= 5):
        raise ValidationError(field_name, value, "Rating must be between 1 and 5")


def validate_date(value: Any, field_name: str) -> None:
    """Validate that a value is a valid date."""
    if value is not None and not isinstance(value, (date, datetime, str)):
        raise ValidationError(field_name, value, "Must be a valid date")


def validate_enum_value(value: Any, enum_class: Any, field_name: str) -> None:
    """Validate that a value is a valid enum value."""
    if value is not None:
        try:
            valid_values = [e.value for e in enum_class]
            if value not in valid_values:
                raise ValidationError(field_name, value, f"Must be one of: {', '.join(valid_values)}")
        except TypeError:
            # Not an enum class
            raise ValidationError(field_name, value, "Invalid enum class provided")


def parse_date_string(date_str: Optional[str]) -> Optional[date]:
    """Parse date string to date object."""
    if not date_str:
        return None
    
    try:
        if isinstance(date_str, str):
            return datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
        return date_str
    except (ValueError, TypeError):
        return None


def safe_float(value: Any) -> Optional[float]:
    """Safely convert value to float."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def safe_int(value: Any) -> Optional[int]:
    """Safely convert value to int."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None 