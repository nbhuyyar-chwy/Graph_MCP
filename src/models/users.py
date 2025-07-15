"""User data models for the pet care database."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .base import BaseModel, validate_required_field


@dataclass
class User(BaseModel):
    """User model representing a pet owner."""
    
    id: Optional[int] = None
    username: str = ""
    
    def __post_init__(self):
        """Validate user data after initialization."""
        validate_required_field(self.username, "username")
    
    @classmethod
    def from_neo4j_record(cls, record: Dict[str, Any]) -> 'User':
        """Create User instance from Neo4j record."""
        return cls(
            id=record.get("id"),
            username=record.get("username", "")
        )


@dataclass
class UserSummary(BaseModel):
    """Summary model for user with basic statistics."""
    
    user: User
    total_pets: int = 0
    total_vet_visits: int = 0
    total_medications: int = 0
    total_product_interactions: int = 0
    
    @classmethod
    def from_neo4j_record(cls, record: Dict[str, Any]) -> 'UserSummary':
        """Create UserSummary instance from Neo4j record."""
        user = User.from_neo4j_record(record)
        return cls(
            user=user,
            total_pets=record.get("total_pets", 0),
            total_vet_visits=record.get("total_vet_visits", 0),
            total_medications=record.get("total_medications", 0),
            total_product_interactions=record.get("total_product_interactions", 0)
        ) 