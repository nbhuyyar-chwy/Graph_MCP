"""Session data models for the pet care database with behavioral analysis."""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import json

from .base import (
    BaseModel, 
    validate_required_field, 
    validate_positive_number,
    parse_date_string,
    safe_float,
    safe_int
)


class SessionImportance(Enum):
    """Session importance levels based on user behavior."""
    CRITICAL = "critical"          # High-value actions: purchases, vet bookings, returns
    SIGNIFICANT = "significant"    # Product research, account updates, cart activity
    MODERATE = "moderate"          # General browsing, search, content viewing
    LOW = "low"                   # Basic navigation, bounce sessions


class SessionChannel(Enum):
    """Session acquisition channels."""
    DIRECT = "Direct"
    ORGANIC_SEARCH = "Organic Search"
    PAID_SEARCH = "Paid Search"
    SOCIAL = "Social"
    EMAIL = "Email"
    REFERRAL = "Referral"
    DISPLAY = "Display"
    OTHER = "Other"


class EventCategory(Enum):
    """Event categories for session analysis."""
    ECOMMERCE = "ecommerce"        # Purchase, cart, checkout events
    ENGAGEMENT = "engagement"      # Page views, content interaction
    CONVERSION = "conversion"      # Goal completions, form submissions
    NAVIGATION = "navigation"      # Site browsing, search
    ACCOUNT = "account"           # Login, registration, profile updates
    VET_CARE = "vet_care"        # Vet-related interactions
    PRODUCT = "product"          # Product views, reviews, recommendations


@dataclass
class SessionEvent:
    """Individual event within a session."""
    event_id: str
    event_name: str
    event_timestamp: datetime
    event_category: Optional[EventCategory] = None
    page_type: Optional[str] = None
    product_sku: Optional[str] = None
    revenue: Optional[float] = None
    properties: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate event data."""
        validate_required_field(self.event_id, "event_id")
        validate_required_field(self.event_name, "event_name")


@dataclass
class SessionSummary:
    """Smart session summary with behavioral insights."""
    
    # Core session metrics
    total_events: int = 0
    unique_pages: int = 0
    time_spent_minutes: float = 0.0
    bounce_rate: bool = False
    
    # Behavioral indicators
    purchase_intent_score: float = 0.0      # 0-1 based on cart/checkout activity
    engagement_depth: float = 0.0           # 0-1 based on content interaction
    vet_care_interest: float = 0.0          # 0-1 based on vet-related activity
    
    # Key activities (cool names!)
    digital_footprint: List[str] = field(default_factory=list)        # Top page types visited
    mission_accomplished: Optional[str] = None                         # Primary goal achieved
    journey_highlights: List[str] = field(default_factory=list)       # Key interaction points
    curiosity_signals: List[str] = field(default_factory=list)        # Search terms, product views
    
    # Conversion tracking
    revenue_generated: float = 0.0
    items_purchased: int = 0
    cart_abandonment: bool = False
    
    # Technical metadata
    device_category: Optional[str] = None
    browser: Optional[str] = None
    is_mobile: bool = False


@dataclass
class Session(BaseModel):
    """Session model representing a user's website session with behavioral analysis."""
    
    # Core identifiers
    session_id: str
    session_start: datetime  # Required field moved before optional ones
    customer_id: Optional[int] = None
    anonymous_id: Optional[str] = None
    
    # Temporal data
    session_end: Optional[datetime] = None
    session_date: Optional[date] = None
    
    # Session characteristics
    channel_grouping: Optional[SessionChannel] = None
    is_bot: bool = False
    is_authenticated: bool = False
    
    # Behavioral analysis (the cool summary fields!)
    adventure_chronicle: Optional[str] = None           # What user did in narrative form
    departure_mystery: Optional[str] = None             # Why user likely left/completed
    importance_level: SessionImportance = SessionImportance.LOW
    confidence_score: float = 0.0                       # 0-1 confidence in analysis
    
    # Session summary and events
    session_summary: Optional[SessionSummary] = None
    events: List[SessionEvent] = field(default_factory=list)
    
    # Relationships
    previous_session_id: Optional[str] = None
    next_session_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate session data after initialization."""
        validate_required_field(self.session_id, "session_id")
        
        # Parse session date if not provided
        if not self.session_date and self.session_start:
            self.session_date = self.session_start.date()
    
    def add_event(self, event: SessionEvent) -> None:
        """Add an event to this session."""
        self.events.append(event)
        
        # Update session end time if this event is later
        if not self.session_end or event.event_timestamp > self.session_end:
            self.session_end = event.event_timestamp
    
    def calculate_duration_minutes(self) -> float:
        """Calculate session duration in minutes."""
        if not self.session_end:
            return 0.0
        
        duration = self.session_end - self.session_start
        return duration.total_seconds() / 60.0
    
    def analyze_importance(self) -> SessionImportance:
        """Analyze and set session importance based on events and behavior."""
        if not self.events:
            return SessionImportance.LOW
        
        # Score based on event types and outcomes
        importance_score = 0.0
        revenue_events = False
        vet_events = False
        high_engagement = False
        
        for event in self.events:
            # Critical indicators
            if event.event_name in ['Order Completed', 'Purchase', 'Vet Appointment Booked']:
                importance_score += 50
                revenue_events = True
            elif event.event_name in ['Product Added', 'Checkout Started']:
                importance_score += 25
            elif 'vet' in event.event_name.lower() or 'appointment' in event.event_name.lower():
                importance_score += 30
                vet_events = True
            elif event.event_name in ['Product Viewed', 'Search Performed']:
                importance_score += 5
            elif event.event_name in ['Page Viewed']:
                importance_score += 1
        
        # Adjust for engagement depth
        if len(self.events) > 20:
            high_engagement = True
            importance_score += 15
        elif len(self.events) > 10:
            importance_score += 8
        
        # Determine importance level
        if importance_score >= 50 or revenue_events:
            return SessionImportance.CRITICAL
        elif importance_score >= 25 or vet_events or high_engagement:
            return SessionImportance.SIGNIFICANT
        elif importance_score >= 10:
            return SessionImportance.MODERATE
        else:
            return SessionImportance.LOW
    
    def generate_adventure_chronicle(self) -> str:
        """Generate narrative description of user's session journey."""
        if not self.events:
            return "A brief encounter with our digital realm - no significant activity detected."
        
        # Categorize events
        page_views = [e for e in self.events if 'Page' in e.event_name or 'Viewed' in e.event_name]
        searches = [e for e in self.events if 'Search' in e.event_name]
        products = [e for e in self.events if 'Product' in e.event_name]
        cart_events = [e for e in self.events if 'Cart' in e.event_name or 'Add' in e.event_name]
        purchases = [e for e in self.events if 'Purchase' in e.event_name or 'Order' in e.event_name]
        
        chronicle = []
        
        # Entry narrative
        channel = self.channel_grouping.value if self.channel_grouping else "unknown means"
        chronicle.append(f"User embarked on a digital journey via {channel}")
        
        # Activity narrative
        if searches:
            chronicle.append(f"conducted {len(searches)} search expeditions")
        if products:
            chronicle.append(f"explored {len(products)} product territories")
        if cart_events:
            chronicle.append(f"gathered {len(cart_events)} items for potential acquisition")
        if purchases:
            chronicle.append(f"successfully completed {len(purchases)} purchase missions")
        
        # Engagement level
        duration = self.calculate_duration_minutes()
        if duration > 30:
            chronicle.append(f"spending {duration:.1f} minutes in deep exploration")
        elif duration > 5:
            chronicle.append(f"browsing for {duration:.1f} focused minutes")
        else:
            chronicle.append("making a swift reconnaissance")
        
        return " - ".join(chronicle) + "."
    
    def generate_departure_mystery(self) -> str:
        """Generate hypothesis about why user ended the session."""
        if not self.events:
            return "Departed as quickly as they arrived - perhaps lost or disinterested."
        
        last_events = self.events[-3:] if len(self.events) >= 3 else self.events
        last_event_names = [e.event_name for e in last_events]
        
        # Purchase completion
        if any('Purchase' in name or 'Order' in name for name in last_event_names):
            return "Mission accomplished! Successfully completed their purchase and departed satisfied."
        
        # Cart abandonment
        if any('Cart' in name or 'Checkout' in name for name in last_event_names):
            return "Hesitation at the final frontier - left with items in cart, perhaps to return later."
        
        # Product research
        if any('Product' in name for name in last_event_names):
            return "Gathering intelligence on products - likely comparing options before making a decision."
        
        # Search behavior
        if any('Search' in name for name in last_event_names):
            return "Still seeking the perfect solution - departed mid-quest, possibly to continue elsewhere."
        
        # General browsing
        if any('Page' in name for name in last_event_names):
            return "Casual exploration concluded - either found what they needed or lost interest."
        
        return "Mysterious departure - their digital footsteps fade without clear resolution."
    
    def calculate_confidence_score(self) -> float:
        """Calculate confidence in the session analysis (0-1)."""
        if not self.events:
            return 0.1
        
        confidence = 0.0
        
        # More events = higher confidence
        event_confidence = min(len(self.events) / 20.0, 0.4)  # Max 0.4 from event count
        confidence += event_confidence
        
        # Longer sessions = higher confidence
        duration = self.calculate_duration_minutes()
        duration_confidence = min(duration / 30.0, 0.3)  # Max 0.3 from duration
        confidence += duration_confidence
        
        # Clear outcomes = higher confidence
        has_purchase = any('Purchase' in e.event_name for e in self.events)
        has_clear_goal = any(keyword in e.event_name for e in self.events 
                           for keyword in ['Search', 'Product', 'Cart', 'Checkout'])
        
        if has_purchase:
            confidence += 0.3
        elif has_clear_goal:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    @classmethod
    def from_neo4j_record(cls, record: Dict[str, Any]) -> 'Session':
        """Create Session instance from Neo4j record."""
        # Parse datetime strings
        session_start = None
        if record.get("session_start"):
            session_start = datetime.fromisoformat(record["session_start"].replace('Z', '+00:00'))
        
        session_end = None
        if record.get("session_end"):
            session_end = datetime.fromisoformat(record["session_end"].replace('Z', '+00:00'))
        
        # Parse channel grouping
        channel_grouping = None
        if record.get("channel_grouping"):
            try:
                channel_grouping = SessionChannel(record["channel_grouping"])
            except ValueError:
                channel_grouping = SessionChannel.OTHER
        
        # Parse importance level
        importance_level = SessionImportance.LOW
        if record.get("importance_level"):
            try:
                importance_level = SessionImportance(record["importance_level"])
            except ValueError:
                pass
        
        return cls(
            session_id=record.get("session_id", ""),
            customer_id=safe_int(record.get("customer_id")),
            anonymous_id=record.get("anonymous_id"),
            session_start=session_start,
            session_end=session_end,
            session_date=parse_date_string(record.get("session_date")),
            channel_grouping=channel_grouping,
            is_bot=record.get("is_bot", False),
            is_authenticated=record.get("is_authenticated", False),
            adventure_chronicle=record.get("adventure_chronicle"),
            departure_mystery=record.get("departure_mystery"),
            importance_level=importance_level,
            confidence_score=safe_float(record.get("confidence_score")) or 0.0
        )


@dataclass  
class SessionAnalysisResult:
    """Result of session analysis with processing metadata."""
    
    session: Session
    processing_time_ms: float
    events_processed: int
    analysis_confidence: float
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        """Check if analysis result is valid."""
        return len(self.errors) == 0 and self.session.session_id
    
    @property
    def quality_score(self) -> float:
        """Overall quality score for the analysis (0-1)."""
        base_score = self.analysis_confidence
        
        # Penalty for warnings/errors
        warning_penalty = len(self.warnings) * 0.05
        error_penalty = len(self.errors) * 0.2
        
        return max(0.0, base_score - warning_penalty - error_penalty) 