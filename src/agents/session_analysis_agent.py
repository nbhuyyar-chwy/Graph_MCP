"""
SessionAnalysisAgent - Intelligent CSV processing and behavioral analysis.

This agent processes Alexander's session CSV data to create structured
Session nodes with behavioral insights and importance scoring.
"""

import csv
import json
import logging
import time
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from pathlib import Path
import pandas as pd

from ..models.sessions import (
    Session, SessionEvent, SessionSummary, SessionAnalysisResult,
    SessionImportance, SessionChannel, EventCategory
)
from ..models.base import safe_float, safe_int
from ..database.queries import QueryBuilder


logger = logging.getLogger(__name__)


class SessionProcessor:
    """Core processor for converting CSV rows to Session objects."""
    
    def __init__(self):
        """Initialize the session processor."""
        self.event_importance_weights = {
            # Critical events (high business value)
            'Order Completed': 50,
            'Purchase': 50,
            'Payment Processed': 50,
            'Vet Appointment Booked': 45,
            'Prescription Ordered': 40,
            'Autoship Created': 35,
            
            # Significant events (medium business value)
            'Product Added': 25,
            'Checkout Started': 25,
            'Cart Updated': 20,
            'Account Created': 30,
            'Profile Updated': 20,
            'Review Submitted': 15,
            
            # Moderate events (engagement indicators)
            'Product Viewed': 5,
            'Search Performed': 8,
            'Category Browsed': 3,
            'Video Watched': 10,
            'Content Engaged': 7,
            
            # Low events (basic navigation)
            'Page Viewed': 1,
            'Button Clicked': 2,
            'Link Clicked': 2,
            'Scroll Reached': 1
        }
        
        self.vet_keywords = [
            'vet', 'veterinary', 'appointment', 'health', 'medical',
            'prescription', 'medication', 'treatment', 'exam', 'checkup'
        ]
        
        self.product_keywords = [
            'product', 'item', 'add to cart', 'purchase', 'buy',
            'cart', 'checkout', 'order', 'review', 'rating'
        ]
        
        self.engagement_keywords = [
            'search', 'filter', 'compare', 'video', 'content',
            'article', 'guide', 'tutorial', 'review'
        ]
    
    def parse_csv_row(self, row: Dict[str, str]) -> Optional[SessionEvent]:
        """Parse a single CSV row into a SessionEvent."""
        try:
            event_id = row.get('EVENT_ID', '')
            event_name = row.get('EVENT_NAME', '')
            event_timestamp_str = row.get('EVENT_TIMESTAMP', '')
            
            if not all([event_id, event_name, event_timestamp_str]):
                return None
            
            # Parse timestamp
            try:
                event_timestamp = datetime.fromisoformat(
                    event_timestamp_str.replace('Z', '+00:00')
                )
            except (ValueError, AttributeError):
                logger.warning(f"Invalid timestamp format: {event_timestamp_str}")
                return None
            
            # Determine event category
            event_category = self._categorize_event(event_name, row)
            
            # Extract additional properties
            properties = {}
            for key, value in row.items():
                if key.startswith('PROPERTIES') or key in ['PAGE_TYPE', 'REVENUE', 'PRODUCT_SKU']:
                    if value:
                        properties[key.lower()] = value
            
            return SessionEvent(
                event_id=event_id,
                event_name=event_name,
                event_timestamp=event_timestamp,
                event_category=event_category,
                page_type=row.get('PAGE_TYPE'),
                product_sku=row.get('PAGE_PRODUCT_SKU'),
                revenue=safe_float(row.get('REVENUE')),
                properties=properties if properties else None
            )
            
        except Exception as e:
            logger.error(f"Error parsing CSV row: {e}")
            return None
    
    def _categorize_event(self, event_name: str, row: Dict[str, str]) -> Optional[EventCategory]:
        """Categorize an event based on its name and context."""
        event_lower = event_name.lower()
        
        # Check for ecommerce events
        if any(keyword in event_lower for keyword in ['purchase', 'order', 'cart', 'checkout', 'payment']):
            return EventCategory.ECOMMERCE
        
        # Check for vet care events
        if any(keyword in event_lower for keyword in self.vet_keywords):
            return EventCategory.VET_CARE
        
        # Check for product events
        if any(keyword in event_lower for keyword in self.product_keywords):
            return EventCategory.PRODUCT
        
        # Check for account events
        if any(keyword in event_lower for keyword in ['login', 'register', 'account', 'profile']):
            return EventCategory.ACCOUNT
        
        # Check for conversion events
        if any(keyword in event_lower for keyword in ['conversion', 'goal', 'complete', 'submit']):
            return EventCategory.CONVERSION
        
        # Check for engagement events
        if any(keyword in event_lower for keyword in self.engagement_keywords):
            return EventCategory.ENGAGEMENT
        
        # Default to navigation
        return EventCategory.NAVIGATION
    
    def group_events_by_session(self, events: List[SessionEvent]) -> Dict[str, List[SessionEvent]]:
        """Group events by session ID from their properties or timestamp proximity."""
        # Since we need to group by session, we'll need to extract session info
        # For now, group by time windows (30-minute sessions)
        sessions = defaultdict(list)
        
        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.event_timestamp)
        
        current_session_id = None
        current_session_start = None
        session_counter = 1
        
        for event in sorted_events:
            # Start new session if no current session or gap > 30 minutes
            if (current_session_start is None or 
                (event.event_timestamp - current_session_start).total_seconds() > 1800):  # 30 minutes
                
                current_session_id = f"session_{session_counter}_{event.event_timestamp.strftime('%Y%m%d_%H%M')}"
                current_session_start = event.event_timestamp
                session_counter += 1
            
            sessions[current_session_id].append(event)
        
        return dict(sessions)


class SessionAnalysisAgent:
    """Intelligent agent for analyzing session data and creating behavioral insights."""
    
    def __init__(self, customer_id: int = 289824860):
        """
        Initialize the session analysis agent.
        
        Args:
            customer_id: Customer ID to analyze (defaults to Alexander's ID)
        """
        self.customer_id = customer_id
        self.processor = SessionProcessor()
        self.logger = logging.getLogger(f"{__name__}.{customer_id}")
        
        # Analysis configuration
        self.min_events_for_analysis = 3
        self.session_timeout_minutes = 30
        self.importance_thresholds = {
            SessionImportance.CRITICAL: 40,
            SessionImportance.SIGNIFICANT: 20,
            SessionImportance.MODERATE: 8,
            SessionImportance.LOW: 0
        }
    
    def process_csv_file(self, csv_file_path: str, max_rows: Optional[int] = None) -> List[SessionAnalysisResult]:
        """
        Process a CSV file and create session analysis results.
        
        Args:
            csv_file_path: Path to the CSV file
            max_rows: Optional limit on number of rows to process
            
        Returns:
            List of session analysis results
        """
        start_time = time.time()
        self.logger.info(f"🚀 Starting analysis of {csv_file_path}")
        
        try:
            # Read and process CSV
            events = self._read_csv_events(csv_file_path, max_rows)
            if not events:
                self.logger.warning("No valid events found in CSV")
                return []
            
            # Group events into sessions
            session_groups = self._group_events_by_session_id(events)
            self.logger.info(f"📊 Found {len(session_groups)} unique sessions")
            
            # Analyze each session
            results = []
            for session_id, session_events in session_groups.items():
                if len(session_events) >= self.min_events_for_analysis:
                    result = self._analyze_session(session_id, session_events)
                    if result and result.is_valid:
                        results.append(result)
            
            # Filter for important sessions only
            important_results = [r for r in results if r.session.importance_level in 
                               [SessionImportance.CRITICAL, SessionImportance.SIGNIFICANT]]
            
            processing_time = (time.time() - start_time) * 1000
            self.logger.info(f"✅ Analysis complete in {processing_time:.1f}ms")
            self.logger.info(f"📈 Processed {len(results)} sessions, {len(important_results)} marked as important")
            
            return important_results
            
        except Exception as e:
            self.logger.error(f"❌ Error processing CSV file: {e}")
            return []
    
    def _read_csv_events(self, csv_file_path: str, max_rows: Optional[int] = None) -> List[SessionEvent]:
        """Read and parse events from CSV file."""
        events = []
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for i, row in enumerate(reader):
                    if max_rows and i >= max_rows:
                        break
                    
                    # Filter for our customer ID
                    if row.get('CUSTOMER_ID') == str(self.customer_id):
                        event = self.processor.parse_csv_row(row)
                        if event:
                            events.append(event)
                
                self.logger.info(f"📖 Read {len(events)} events for customer {self.customer_id}")
                return events
                
        except Exception as e:
            self.logger.error(f"❌ Error reading CSV: {e}")
            return []
    
    def _group_events_by_session_id(self, events: List[SessionEvent]) -> Dict[str, List[SessionEvent]]:
        """Group events by actual session ID from CSV."""
        sessions = defaultdict(list)
        
        # Sort events by timestamp first
        sorted_events = sorted(events, key=lambda e: e.event_timestamp)
        
        # Try to extract session ID from properties or use time-based grouping
        for event in sorted_events:
            session_id = None
            
            # Look for session ID in properties
            if event.properties:
                session_id = event.properties.get('session_id')
            
            # If no session ID found, create time-based sessions
            if not session_id:
                # Group into 30-minute sessions
                session_key = event.event_timestamp.strftime('%Y%m%d_%H') + f"_{event.event_timestamp.minute // 30}"
                session_id = f"session_{self.customer_id}_{session_key}"
            
            sessions[session_id].append(event)
        
        return dict(sessions)
    
    def _analyze_session(self, session_id: str, events: List[SessionEvent]) -> Optional[SessionAnalysisResult]:
        """Analyze a single session and create results."""
        start_time = time.time()
        
        try:
            # Sort events by timestamp
            sorted_events = sorted(events, key=lambda e: e.event_timestamp)
            
            # Create session object
            session = Session(
                session_id=session_id,
                customer_id=self.customer_id,
                session_start=sorted_events[0].event_timestamp,
                session_end=sorted_events[-1].event_timestamp,
                events=sorted_events
            )
            
            # Analyze importance
            session.importance_level = self._determine_importance(sorted_events)
            
            # Generate behavioral insights
            session.adventure_chronicle = session.generate_adventure_chronicle()
            session.departure_mystery = session.generate_departure_mystery()
            session.confidence_score = session.calculate_confidence_score()
            
            # Determine channel (simplified)
            session.channel_grouping = self._determine_channel(sorted_events)
            
            # Create session summary
            session.session_summary = self._create_session_summary(sorted_events)
            
            processing_time = (time.time() - start_time) * 1000
            
            return SessionAnalysisResult(
                session=session,
                processing_time_ms=processing_time,
                events_processed=len(events),
                analysis_confidence=session.confidence_score,
                warnings=[],
                errors=[]
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing session {session_id}: {e}")
            return SessionAnalysisResult(
                session=Session(session_id=session_id, customer_id=self.customer_id, 
                               session_start=datetime.now()),
                processing_time_ms=0,
                events_processed=0,
                analysis_confidence=0.0,
                errors=[str(e)]
            )
    
    def _determine_importance(self, events: List[SessionEvent]) -> SessionImportance:
        """Determine session importance based on events."""
        total_score = 0
        
        # Score based on event types
        event_names = [e.event_name for e in events]
        event_categories = [e.event_category for e in events if e.event_category]
        
        for event in events:
            # Direct event scoring
            if event.event_name in self.processor.event_importance_weights:
                total_score += self.processor.event_importance_weights[event.event_name]
            
            # Category bonuses
            if event.event_category == EventCategory.ECOMMERCE:
                total_score += 15
            elif event.event_category == EventCategory.VET_CARE:
                total_score += 20
            elif event.event_category == EventCategory.PRODUCT:
                total_score += 5
            
            # Revenue bonus
            if event.revenue and event.revenue > 0:
                total_score += min(event.revenue, 50)  # Cap at 50 points
        
        # Engagement bonuses
        if len(events) > 20:
            total_score += 15  # High engagement
        elif len(events) > 10:
            total_score += 8   # Medium engagement
        
        # Session duration bonus
        if len(events) > 1:
            duration_minutes = (events[-1].event_timestamp - events[0].event_timestamp).total_seconds() / 60
            if duration_minutes > 30:
                total_score += 10
            elif duration_minutes > 10:
                total_score += 5
        
        # Determine importance level
        if total_score >= self.importance_thresholds[SessionImportance.CRITICAL]:
            return SessionImportance.CRITICAL
        elif total_score >= self.importance_thresholds[SessionImportance.SIGNIFICANT]:
            return SessionImportance.SIGNIFICANT
        elif total_score >= self.importance_thresholds[SessionImportance.MODERATE]:
            return SessionImportance.MODERATE
        else:
            return SessionImportance.LOW
    
    def _determine_channel(self, events: List[SessionEvent]) -> SessionChannel:
        """Determine acquisition channel from events."""
        # Look for channel info in event properties
        for event in events:
            if event.properties:
                channel = event.properties.get('channel_grouping', '').lower()
                if 'organic' in channel:
                    return SessionChannel.ORGANIC_SEARCH
                elif 'paid' in channel:
                    return SessionChannel.PAID_SEARCH
                elif 'social' in channel:
                    return SessionChannel.SOCIAL
                elif 'email' in channel:
                    return SessionChannel.EMAIL
                elif 'referral' in channel:
                    return SessionChannel.REFERRAL
                elif 'direct' in channel:
                    return SessionChannel.DIRECT
        
        # Default to direct if no channel found
        return SessionChannel.DIRECT
    
    def _create_session_summary(self, events: List[SessionEvent]) -> SessionSummary:
        """Create a detailed session summary."""
        page_types = set()
        product_skus = set()
        total_revenue = 0.0
        cart_events = 0
        purchase_events = 0
        
        for event in events:
            if event.page_type:
                page_types.add(event.page_type)
            if event.product_sku:
                product_skus.add(event.product_sku)
            if event.revenue:
                total_revenue += event.revenue
            if 'cart' in event.event_name.lower():
                cart_events += 1
            if 'purchase' in event.event_name.lower() or 'order' in event.event_name.lower():
                purchase_events += 1
        
        # Calculate duration
        duration_minutes = 0.0
        if len(events) > 1:
            duration_minutes = (events[-1].event_timestamp - events[0].event_timestamp).total_seconds() / 60
        
        # Create summary
        summary = SessionSummary(
            total_events=len(events),
            unique_pages=len(page_types),
            time_spent_minutes=duration_minutes,
            bounce_rate=len(events) <= 1,
            revenue_generated=total_revenue,
            items_purchased=purchase_events,
            cart_abandonment=cart_events > 0 and purchase_events == 0,
            digital_footprint=list(page_types)[:5],  # Top 5 page types
        )
        
        # Calculate behavioral scores
        if cart_events > 0 or purchase_events > 0:
            summary.purchase_intent_score = min(1.0, (cart_events + purchase_events * 2) / 10)
        
        if len(events) > 5:
            summary.engagement_depth = min(1.0, len(events) / 20)
        
        # Look for vet-related activity
        vet_events = sum(1 for e in events if any(keyword in e.event_name.lower() 
                        for keyword in self.processor.vet_keywords))
        if vet_events > 0:
            summary.vet_care_interest = min(1.0, vet_events / 5)
        
        return summary
    
    def generate_session_templates(self, results: List[SessionAnalysisResult]) -> List[Dict[str, Any]]:
        """Generate session templates suitable for database insertion."""
        templates = []
        
        for result in results:
            session = result.session
            
            template = {
                'session_id': session.session_id,
                'customer_id': session.customer_id,
                'anonymous_id': session.anonymous_id,
                'session_start': session.session_start.isoformat(),
                'session_end': session.session_end.isoformat() if session.session_end else None,
                'session_date': session.session_date.isoformat() if session.session_date else None,
                'channel_grouping': session.channel_grouping.value if session.channel_grouping else None,
                'is_bot': session.is_bot,
                'is_authenticated': session.is_authenticated,
                'adventure_chronicle': session.adventure_chronicle,
                'departure_mystery': session.departure_mystery,
                'importance_level': session.importance_level.value,
                'confidence_score': session.confidence_score,
                'analysis_metadata': {
                    'processing_time_ms': result.processing_time_ms,
                    'events_processed': result.events_processed,
                    'analysis_confidence': result.analysis_confidence,
                    'quality_score': result.quality_score
                }
            }
            
            templates.append(template)
        
        return templates
    
    def save_analysis_results(self, results: List[SessionAnalysisResult], output_file: str) -> None:
        """Save analysis results to a JSON file."""
        try:
            templates = self.generate_session_templates(results)
            
            output_data = {
                'analysis_metadata': {
                    'customer_id': self.customer_id,
                    'total_sessions_analyzed': len(results),
                    'important_sessions': len([r for r in results if r.session.importance_level in 
                                             [SessionImportance.CRITICAL, SessionImportance.SIGNIFICANT]]),
                    'analysis_timestamp': datetime.now().isoformat(),
                    'avg_confidence_score': sum(r.analysis_confidence for r in results) / len(results) if results else 0
                },
                'sessions': templates
            }
            
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2, default=str)
            
            self.logger.info(f"💾 Saved {len(templates)} session templates to {output_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Error saving results: {e}") 