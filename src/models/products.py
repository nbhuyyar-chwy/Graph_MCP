"""Product data models for the pet care database."""

from dataclasses import dataclass
import datetime
from typing import Any, Dict, List, Optional

from .base import (
    BaseModel, InteractionType, ValidationError,
    validate_required_field, validate_rating,
    parse_date_string, safe_float, safe_int
)


@dataclass
class Product(BaseModel):
    """Product model representing a product item."""
    
    product_name: str = ""
    brand: Optional[str] = None
    category: Optional[str] = None
    attributes: Optional[str] = None
    
    def __post_init__(self):
        """Validate product data after initialization."""
        validate_required_field(self.product_name, "product_name")
    
    @classmethod
    def from_neo4j_record(cls, record: Dict[str, Any]) -> 'Product':
        """Create Product instance from Neo4j record."""
        return cls(
            product_name=record.get("product_name") or record.get("product", ""),
            brand=record.get("brand"),
            category=record.get("category"),
            attributes=record.get("attributes")
        )


@dataclass
class ProductInteraction(BaseModel):
    """ProductInteraction model representing interaction with a product."""
    
    interaction_date: Optional[datetime.date] = None
    interaction_type: Optional[str] = None
    quantity: Optional[int] = None
    feedback: Optional[str] = None
    rating: Optional[float] = None
    notes: Optional[str] = None
    product: Optional[Product] = None
    pet_name: Optional[str] = None
    owner_username: Optional[str] = None
    
    def __post_init__(self):
        """Validate interaction data after initialization."""
        if self.rating is not None:
            validate_rating(self.rating, "rating")
        
        if self.quantity is not None and self.quantity <= 0:
            raise ValidationError("quantity", self.quantity, "Must be positive")
    
    @classmethod
    def from_neo4j_record(cls, record: Dict[str, Any]) -> 'ProductInteraction':
        """Create ProductInteraction instance from Neo4j record."""
        product = None
        if record.get("product_name"):
            product = Product(
                product_name=record.get("product_name", ""),
                brand=record.get("brand"),
                category=record.get("category"),
                attributes=record.get("attributes")
            )
        
        return cls(
            interaction_date=parse_date_string(record.get("interaction_date") or record.get("date")),
            interaction_type=record.get("interaction_type"),
            quantity=safe_int(record.get("quantity")),
            feedback=record.get("feedback"),
            rating=safe_float(record.get("rating")),
            notes=record.get("notes"),
            product=product,
            pet_name=record.get("pet_name"),
            owner_username=record.get("owner")
        )


@dataclass
class ProductRating(BaseModel):
    """Product rating summary model."""
    
    product: Product
    avg_rating: float = 0.0
    total_interactions: int = 0
    interaction_types: Optional[List[str]] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.interaction_types is None:
            self.interaction_types = []
    
    @property
    def rating_stars(self) -> str:
        """Get star representation of rating."""
        full_stars = int(self.avg_rating)
        half_star = 1 if (self.avg_rating - full_stars) >= 0.5 else 0
        empty_stars = 5 - full_stars - half_star
        
        return "★" * full_stars + "☆" * half_star + "☆" * empty_stars
    
    @classmethod
    def from_neo4j_record(cls, record: Dict[str, Any]) -> 'ProductRating':
        """Create ProductRating instance from Neo4j record."""
        product = Product.from_neo4j_record(record)
        return cls(
            product=product,
            avg_rating=safe_float(record.get("avg_rating")) or 0.0,
            total_interactions=safe_int(record.get("total_interactions")) or 0,
            interaction_types=record.get("interaction_types", [])
        )


@dataclass
class PopularProduct(BaseModel):
    """Popular product model with interaction statistics."""
    
    product: Product
    interaction_count: int = 0
    avg_rating: Optional[float] = None
    interaction_types: Optional[List[str]] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.interaction_types is None:
            self.interaction_types = []
    
    @property
    def popularity_score(self) -> float:
        """Calculate popularity score based on interactions and rating."""
        base_score = self.interaction_count
        if self.avg_rating:
            # Boost score based on rating (1-5 scale)
            rating_multiplier = self.avg_rating / 5.0
            base_score *= (1 + rating_multiplier)
        return round(base_score, 2)
    
    @classmethod
    def from_neo4j_record(cls, record: Dict[str, Any]) -> 'PopularProduct':
        """Create PopularProduct instance from Neo4j record."""
        product = Product.from_neo4j_record(record)
        return cls(
            product=product,
            interaction_count=safe_int(record.get("interaction_count")) or 0,
            avg_rating=safe_float(record.get("avg_rating")),
            interaction_types=record.get("interaction_types", [])
        )


@dataclass
class ProductSearchCriteria:
    """Search criteria for finding product interactions."""
    
    product_name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    interaction_type: Optional[str] = None
    min_rating: Optional[float] = None
    max_rating: Optional[float] = None
    start_date: Optional[str] = None  # YYYY-MM-DD format
    end_date: Optional[str] = None    # YYYY-MM-DD format
    pet_name: Optional[str] = None
    owner_username: Optional[str] = None
    
    def validate(self) -> None:
        """Validate search criteria."""
        if self.min_rating is not None:
            validate_rating(self.min_rating, "min_rating")
        
        if self.max_rating is not None:
            validate_rating(self.max_rating, "max_rating")
        
        if (self.min_rating is not None and self.max_rating is not None 
            and self.min_rating > self.max_rating):
            raise ValidationError("rating_range", f"{self.min_rating}-{self.max_rating}", 
                                "Min rating cannot be greater than max rating")
        
        # Validate date format
        if self.start_date:
            try:
                datetime.datetime.strptime(self.start_date, "%Y-%m-%d")
            except ValueError:
                raise ValidationError("start_date", self.start_date, "Must be in YYYY-MM-DD format")
        
        if self.end_date:
            try:
                datetime.datetime.strptime(self.end_date, "%Y-%m-%d")
            except ValueError:
                raise ValidationError("end_date", self.end_date, "Must be in YYYY-MM-DD format")
        
        if (self.start_date and self.end_date and self.start_date > self.end_date):
            raise ValidationError("date_range", f"{self.start_date} to {self.end_date}", 
                                "Start date cannot be after end date")
    
    def to_query_parameters(self) -> Dict[str, Any]:
        """Convert criteria to query parameters."""
        self.validate()
        params = {}
        
        if self.product_name:
            params["product_name"] = self.product_name
        if self.brand:
            params["brand"] = self.brand
        if self.category:
            params["category"] = self.category
        if self.interaction_type:
            params["interaction_type"] = self.interaction_type
        if self.min_rating is not None:
            params["min_rating"] = self.min_rating
        if self.max_rating is not None:
            params["max_rating"] = self.max_rating
        if self.start_date:
            params["start_date"] = self.start_date
        if self.end_date:
            params["end_date"] = self.end_date
        if self.pet_name:
            params["pet_name"] = self.pet_name
        if self.owner_username:
            params["owner_username"] = self.owner_username
        
        return params 