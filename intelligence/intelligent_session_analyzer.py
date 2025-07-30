#!/usr/bin/env python3
"""
Intelligent Session Analyzer with OpenAI-powered behavioral insights.

This module implements a complete session analysis pipeline that:
1. Processes CSV session data row-by-row
2. Uses AI agents to determine session importance and generate insights
3. Creates a Neo4j graph structure: Customer → WebData → Session
4. Adds cool field names: digital_chronicles & mindset_decoder

Author: AI Assistant
Created: 2025
"""

import os
import csv
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass
from dotenv import load_dotenv

# Third-party imports
from neo4j import GraphDatabase
import openai

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_CUSTOMER_ID = "289824860"
IMPORTANCE_THRESHOLD = 0.4  # Lowered threshold for more inclusive sessions
MIN_EVENTS_PER_SESSION = 2
AI_MODEL = "gpt-3.5-turbo"


@dataclass
class SessionEvent:
    """Represents an individual event within a user session."""
    event_id: str
    event_name: str
    event_type: str
    timestamp: datetime
    page_type: Optional[str] = None
    product_sku: Optional[str] = None
    revenue: float = 0.0
    event_category: Optional[str] = None


@dataclass
class SessionAnalysis:
    """Complete session analysis with AI-generated insights."""
    session_id: str
    customer_id: str
    session_start: datetime
    session_end: datetime
    events: List[SessionEvent]
    event_count: int
    duration_minutes: float
    importance_score: float
    confidence_score: float
    # Cool field names for AI insights
    digital_chronicles: str  # What the user did (session summary)
    mindset_decoder: str     # Why they did it (psychological reasoning)


class SessionAgent:
    """
    AI Agent that analyzes individual sessions and generates insights.
    
    Responsibilities:
    - Determine session importance (0-1 scale)
    - Generate confidence scores
    - Create session summaries (digital_chronicles)
    - Provide behavioral reasoning (mindset_decoder)
    """
    
    def __init__(self, openai_client: openai.OpenAI):
        self.client = openai_client
        
    def analyze_session(self, session_data: Dict[str, Any]) -> Tuple[float, float, str, str]:
        """
        Analyze a session and generate AI insights.
        
        Args:
            session_data: Dictionary containing session information
            
        Returns:
            Tuple of (importance_score, confidence_score, summary, reasoning)
        """
        try:
            # Prepare event details for AI analysis
            event_details = self._prepare_event_context(session_data['events'])
            
            # Create AI prompt
            prompt = self._build_analysis_prompt(session_data, event_details)
            
            # Get AI response
            response = self.client.chat.completions.create(
                model=AI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            # Parse AI response
            result = json.loads(response.choices[0].message.content)
            
            return (
                result.get("importance_score", 0.5),
                result.get("confidence_score", 0.8),
                result.get("session_summary", "User engaged in browsing activities"),
                result.get("session_reasoning", "Standard customer exploration behavior")
            )
            
        except Exception as e:
            logger.warning(f"AI session analysis failed: {e}")
            return self._fallback_analysis(session_data)
    
    def _prepare_event_context(self, events: List[SessionEvent]) -> List[Dict[str, Any]]:
        """Prepare event data for AI analysis."""
        return [
            {
                "action": event.event_name,
                "page": event.page_type,
                "time": event.timestamp.strftime("%H:%M:%S"),
                "product": event.product_sku[:15] if event.product_sku else None
            }
            for event in events[:10]  # Limit to first 10 events for context
        ]
    
    def _build_analysis_prompt(self, session_data: Dict[str, Any], event_details: List[Dict]) -> str:
        """Build the AI analysis prompt."""
        return f"""
        Analyze this individual user session and provide insights:
        
        Session Details:
        - Duration: {session_data['duration_minutes']:.1f} minutes
        - Events: {session_data['event_count']}
        - Start: {session_data['session_start'].strftime('%Y-%m-%d %H:%M')}
        - Event sequence: {event_details}
        
        Provide analysis with these requirements:
        1. Importance score (0-1): How valuable/significant is this session?
        2. Confidence score (0-1): How confident are you in this analysis?
        3. Session summary: What did the user accomplish in this session? (be specific and creative)
        4. Session reasoning: Why did they behave this way? What motivated them?
        
        Focus on pet/ecommerce context. Be insightful and specific.
        
        Respond in JSON format:
        {{
            "importance_score": 0.85,
            "confidence_score": 0.92,
            "session_summary": "...",
            "session_reasoning": "..."
        }}
        """
    
    def _fallback_analysis(self, session_data: Dict[str, Any]) -> Tuple[float, float, str, str]:
        """Provide fallback analysis when AI fails."""
        if session_data['event_count'] > 15:
            return (
                0.7, 0.6,
                f"Conducted extensive exploration with {session_data['event_count']} interactions over {session_data['duration_minutes']:.1f} minutes",
                "Research-oriented behavior suggesting comparison shopping and careful consideration"
            )
        elif session_data['event_count'] > 5:
            return (
                0.5, 0.5,
                f"Moderate browsing session with {session_data['event_count']} page views over {session_data['duration_minutes']:.1f} minutes",
                "Standard exploration behavior with moderate engagement depth"
            )
        else:
            return (
                0.4, 0.5,
                f"Brief browsing session with {session_data['event_count']} page views",
                "Casual exploration behavior with limited engagement depth"
            )


class WebDataAgent:
    """
    AI Agent that creates overall web behavior insights for the WebData node.
    
    Responsibilities:
    - Aggregate session data across all sessions
    - Generate comprehensive behavioral profiles
    - Provide overall customer insights
    """
    
    def __init__(self, openai_client: openai.OpenAI):
        self.client = openai_client
        
    def generate_overall_insight(self, sessions: List[SessionAnalysis]) -> str:
        """
        Generate overall behavioral insight for WebData node.
        
        Args:
            sessions: List of analyzed sessions
            
        Returns:
            Comprehensive behavioral profile as string
        """
        try:
            # Aggregate session statistics
            stats = self._calculate_session_stats(sessions)
            
            # Create AI prompt for overall insight
            prompt = self._build_insight_prompt(stats)
            
            # Get AI response
            response = self.client.chat.completions.create(
                model=AI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.warning(f"AI overall insight generation failed: {e}")
            return self._fallback_insight(sessions)
    
    def _calculate_session_stats(self, sessions: List[SessionAnalysis]) -> Dict[str, Any]:
        """Calculate aggregated statistics from sessions."""
        total_sessions = len(sessions)
        avg_importance = sum(s.importance_score for s in sessions) / total_sessions if total_sessions > 0 else 0
        total_events = sum(s.event_count for s in sessions)
        high_value_sessions = len([s for s in sessions if s.event_count > 15])
        
        return {
            'total_sessions': total_sessions,
            'avg_importance': avg_importance,
            'total_events': total_events,
            'high_value_sessions': high_value_sessions,
            'date_range': (sessions[0].session_start, sessions[-1].session_start) if sessions else None
        }
    
    def _build_insight_prompt(self, stats: Dict[str, Any]) -> str:
        """Build the AI prompt for overall insights."""
        date_range = ""
        if stats['date_range']:
            date_range = f"- Date range: {stats['date_range'][0].strftime('%Y-%m-%d')} to {stats['date_range'][1].strftime('%Y-%m-%d')}"
        
        return f"""
        Create an overall behavioral profile for this customer based on their session data:
        
        Customer Web Behavior Summary:
        - Total sessions analyzed: {stats['total_sessions']}
        - Average session importance: {stats['avg_importance']:.2f}
        - Total interactions: {stats['total_events']}
        - High-engagement sessions: {stats['high_value_sessions']}
        {date_range}
        
        Create a comprehensive behavioral profile that captures:
        1. Overall engagement patterns
        2. Digital interaction style
        3. Customer personality insights
        4. Browsing behavior tendencies
        
        Make it insightful and professional for a pet ecommerce context.
        
        Respond with a single comprehensive paragraph (200-300 words).
        """
    
    def _fallback_insight(self, sessions: List[SessionAnalysis]) -> str:
        """Provide fallback insight when AI fails."""
        total_sessions = len(sessions)
        avg_importance = sum(s.importance_score for s in sessions) / total_sessions if total_sessions > 0 else 0
        
        return (
            f"Customer demonstrates consistent engagement with {total_sessions} sessions "
            f"showing {avg_importance:.1f} average session importance with varied browsing and "
            f"interaction behaviors typical of engaged pet owners."
        )


class CorrectSessionAnalyzer:
    """
    Main analyzer implementing the correct graph structure: Customer → WebData → Session.
    
    This class orchestrates the complete session analysis pipeline:
    1. CSV processing and event grouping
    2. AI-powered session analysis
    3. Neo4j graph creation with proper structure
    """
    
    def __init__(self, customer_id: str = DEFAULT_CUSTOMER_ID):
        self.customer_id = customer_id
        self._initialize_openai()
        self._initialize_agents()
        self._initialize_neo4j()
        
        logger.info("🎯 Correct Session Analyzer initialized")
    
    def _initialize_openai(self) -> None:
        """Initialize OpenAI client."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        openai.api_key = api_key
        self.openai_client = openai.OpenAI(api_key=api_key)
    
    def _initialize_agents(self) -> None:
        """Initialize AI agents."""
        self.session_agent = SessionAgent(self.openai_client)
        self.webdata_agent = WebDataAgent(self.openai_client)
    
    def _initialize_neo4j(self) -> None:
        """Initialize Neo4j connection."""
        self.neo4j_driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
            auth=(
                os.getenv('NEO4J_USERNAME', 'neo4j'),
                os.getenv('NEO4J_PASSWORD', 'password')
            )
        )
    
    def parse_csv_row(self, row: Dict[str, str]) -> Optional[SessionEvent]:
        """
        Parse a CSV row into a SessionEvent.
        
        Args:
            row: Dictionary representing a CSV row
            
        Returns:
            SessionEvent object or None if parsing fails
        """
        try:
            # Filter by customer ID
            if row.get('CUSTOMER_ID') != self.customer_id:
                return None
            
            # Parse timestamp
            timestamp_str = row.get('EVENT_TIMESTAMP', '')
            if not timestamp_str:
                return None
            
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            
            # Create SessionEvent
            return SessionEvent(
                event_id=row.get('EVENT_ID', ''),
                event_name=row.get('EVENT_NAME', ''),
                event_type=row.get('EVENT_TYPE', ''),
                timestamp=timestamp,
                page_type=row.get('PAGE_TYPE'),
                product_sku=row.get('PAGE_PRODUCT_SKU'),
                revenue=float(row.get('REVENUE', 0) or 0),
                event_category=row.get('EVENT_CATEGORY')
            )
            
        except Exception as e:
            logger.debug(f"Failed to parse row: {e}")
            return None
    
    def group_events_into_sessions(self, csv_path: str) -> Dict[str, List[SessionEvent]]:
        """
        Process CSV and group events by session ID.
        
        Args:
            csv_path: Path to the CSV file
            
        Returns:
            Dictionary mapping session IDs to lists of events
        """
        logger.info(f"📊 Processing CSV: {csv_path}")
        
        sessions = defaultdict(list)
        row_count = 0
        valid_events = 0
        customer_events = 0
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                logger.info(f"📋 CSV columns found: {list(reader.fieldnames)}")
                
                for row in reader:
                    row_count += 1
                    
                    # Progress logging with more details
                    if row_count % 5000 == 0:
                        logger.info(f"📈 Processed {row_count:,} rows | Found {len(sessions)} sessions | Valid events: {valid_events:,} | Customer events: {customer_events:,}")
                    
                    # Parse and group event
                    event = self.parse_csv_row(row)
                    if event:
                        valid_events += 1
                        if row.get('CUSTOMER_ID') == self.customer_id:
                            customer_events += 1
                            session_id = row.get('SESSION_ID', 
                                f"session_{self.customer_id}_{event.timestamp.strftime('%Y%m%d_%H')}")
                            sessions[session_id].append(event)
                            
                            # Log first few sessions found
                            if len(sessions) <= 5 and len(sessions[session_id]) == 1:
                                logger.info(f"🔍 Found new session: {session_id[:40]}... at {event.timestamp}")
            
            logger.info(f"✅ CSV Processing Complete!")
            logger.info(f"   📊 Total rows processed: {row_count:,}")
            logger.info(f"   ✅ Valid events parsed: {valid_events:,}")
            logger.info(f"   👤 Customer {self.customer_id} events: {customer_events:,}")
            logger.info(f"   📝 Unique sessions found: {len(sessions)}")
            
            # Log session size distribution
            session_sizes = [len(events) for events in sessions.values()]
            if session_sizes:
                logger.info(f"   📈 Session size stats: min={min(session_sizes)}, max={max(session_sizes)}, avg={sum(session_sizes)/len(session_sizes):.1f}")
            
            return dict(sessions)
            
        except Exception as e:
            logger.error(f"❌ Failed to process CSV: {e}")
            raise
    
    def analyze_sessions_with_ai(self, session_events: Dict[str, List[SessionEvent]]) -> List[SessionAnalysis]:
        """
        Analyze all sessions with AI to generate insights.
        
        Args:
            session_events: Dictionary of session ID to events
            
        Returns:
            List of analyzed sessions with AI insights
        """
        logger.info("🤖 Starting AI analysis of sessions...")
        logger.info(f"   📊 Total sessions to analyze: {len(session_events)}")
        logger.info(f"   🎯 Importance threshold: {IMPORTANCE_THRESHOLD}")
        logger.info(f"   📏 Minimum events per session: {MIN_EVENTS_PER_SESSION}")
        
        analyzed_sessions = []
        skipped_short = 0
        skipped_low_importance = 0
        ai_failures = 0
        session_count = 0
        
        for session_id, events in session_events.items():
            session_count += 1
            
            # Skip sessions with too few events
            if len(events) < MIN_EVENTS_PER_SESSION:
                skipped_short += 1
                if session_count <= 3:  # Log first few skips
                    logger.debug(f"⏭️  Skipping short session {session_id[:25]}... ({len(events)} events)")
                continue
            
            # Sort events by timestamp
            events.sort(key=lambda e: e.timestamp)
            
            # Prepare session data for AI analysis
            session_data = self._prepare_session_data(session_id, events)
            
            # Log detailed session info for first few
            if len(analyzed_sessions) < 3:
                logger.info(f"🔍 Analyzing session {len(analyzed_sessions)+1}: {session_id[:25]}...")
                logger.info(f"   ⏱️  Duration: {session_data['duration_minutes']:.1f} min | Events: {session_data['event_count']} | Start: {session_data['session_start'].strftime('%Y-%m-%d %H:%M')}")
            
            # Get AI analysis
            try:
                importance_score, confidence_score, summary, reasoning = \
                    self.session_agent.analyze_session(session_data)
                
                # Only include sessions above importance threshold
                if importance_score >= IMPORTANCE_THRESHOLD:
                    logger.info(f"📝 ✅ Session {len(analyzed_sessions)+1}: {session_id[:25]}... (importance: {importance_score:.2f}, confidence: {confidence_score:.2f})")
                    
                    # Create SessionAnalysis object
                    session_analysis = SessionAnalysis(
                        session_id=session_id,
                        customer_id=self.customer_id,
                        session_start=session_data['session_start'],
                        session_end=session_data['session_end'],
                        events=events,
                        event_count=session_data['event_count'],
                        duration_minutes=session_data['duration_minutes'],
                        importance_score=importance_score,
                        confidence_score=confidence_score,
                        digital_chronicles=summary,
                        mindset_decoder=reasoning
                    )
                    
                    analyzed_sessions.append(session_analysis)
                else:
                    skipped_low_importance += 1
                    logger.debug(f"⏭️  Skipping low importance session: {session_id[:25]}... (importance: {importance_score:.2f})")
                    
            except Exception as e:
                ai_failures += 1
                logger.warning(f"🤖 ❌ AI analysis failed for session {session_id[:25]}...: {e}")
            
            # Progress update every 10 sessions
            if session_count % 10 == 0:
                logger.info(f"📊 Progress: {session_count}/{len(session_events)} sessions processed | ✅ Important: {len(analyzed_sessions)} | ⏭️ Skipped: {skipped_short + skipped_low_importance} | ❌ Failures: {ai_failures}")
        
        logger.info(f"✅ AI analysis complete!")
        logger.info(f"   📊 Total sessions processed: {session_count}")
        logger.info(f"   ✅ Important sessions found: {len(analyzed_sessions)}")
        logger.info(f"   ⏭️  Skipped (too short): {skipped_short}")
        logger.info(f"   ⏭️  Skipped (low importance): {skipped_low_importance}")
        logger.info(f"   ❌ AI analysis failures: {ai_failures}")
        
        if analyzed_sessions:
            avg_importance = sum(s.importance_score for s in analyzed_sessions) / len(analyzed_sessions)
            avg_confidence = sum(s.confidence_score for s in analyzed_sessions) / len(analyzed_sessions)
            logger.info(f"   📈 Avg importance score: {avg_importance:.2f}")
            logger.info(f"   📈 Avg confidence score: {avg_confidence:.2f}")
        
        return analyzed_sessions
    
    def _prepare_session_data(self, session_id: str, events: List[SessionEvent]) -> Dict[str, Any]:
        """Prepare session data dictionary for analysis."""
        return {
            'session_id': session_id,
            'customer_id': self.customer_id,
            'session_start': events[0].timestamp,
            'session_end': events[-1].timestamp,
            'events': events,
            'event_count': len(events),
            'duration_minutes': (events[-1].timestamp - events[0].timestamp).total_seconds() / 60
        }
    
    def clear_existing_data(self) -> None:
        """Remove existing Session and WebData nodes for this customer."""
        with self.neo4j_driver.session() as session:
            query = """
            MATCH (c:Customer {customer_id: $customer_id})-[:HAS_WEB_DATA]->(w:WebData)
            OPTIONAL MATCH (w)-[:HAS_SESSION]->(s:Session)
            DETACH DELETE w, s
            """
            session.run(query, customer_id=self.customer_id)
            logger.info("🧹 Cleared existing WebData and Session nodes")
    
    def create_graph_structure(self, sessions: List[SessionAnalysis]) -> None:
        """
        Create the correct graph structure: Customer → WebData → Session.
        
        Args:
            sessions: List of analyzed sessions to add to graph
        """
        logger.info(f"🏗️ Creating correct graph structure with {len(sessions)} sessions...")
        
        with self.neo4j_driver.session() as neo4j_session:
            # Step 1: Generate overall web insight
            logger.info("🧠 Generating overall behavioral insight with AI...")
            overall_insight = self.webdata_agent.generate_overall_insight(sessions)
            logger.info(f"✅ Generated insight ({len(overall_insight)} characters)")
            
            # Step 2: Create User → WebData structure
            logger.info("🕸️ Creating WebData node...")
            self._create_webdata_node(neo4j_session, sessions, overall_insight)
            
            # Step 3: Create Session nodes
            logger.info(f"📝 Creating {len(sessions)} Session nodes...")
            success_count = 0
            failure_count = 0
            
            for i, session in enumerate(sessions, 1):
                try:
                    self._create_session_node(neo4j_session, session)
                    success_count += 1
                    
                    # Progress logging every 10 sessions
                    if i % 10 == 0:
                        logger.info(f"📊 Session creation progress: {i}/{len(sessions)} | ✅ Success: {success_count} | ❌ Failures: {failure_count}")
                        
                except Exception as e:
                    failure_count += 1
                    logger.error(f"❌ Failed to create session {i}/{len(sessions)} ({session.session_id[:25]}...): {e}")
            
            logger.info(f"✅ Graph structure creation complete!")
            logger.info(f"   📝 Sessions created: {success_count}/{len(sessions)}")
            if failure_count > 0:
                logger.warning(f"   ❌ Session creation failures: {failure_count}")
                
    def _create_webdata_node(self, session, sessions: List[SessionAnalysis], overall_insight: str) -> None:
        """Create WebData node linked to existing Customer with overall behavioral insight."""
        # Calculate aggregated statistics
        avg_importance = sum(s.importance_score for s in sessions) / len(sessions)
        
        webdata_query = """
        // Find existing Customer node (don't create new one)
        MATCH (c:Customer {customer_id: $customer_id})
        
        // Create WebData node with overall behavioral insight
        CREATE (w:WebData {
            customer_id: $customer_id,
            analysis_date: date(),
            total_sessions: $total_sessions,
            avg_importance_score: $avg_importance,
            overall_behavioral_insight: $overall_insight,
            created_at: datetime()
        })
        
        // Link Customer to WebData
        CREATE (c)-[:HAS_WEB_DATA]->(w)
        
        RETURN w.customer_id as created_webdata
        """
        
        params = {
            'customer_id': self.customer_id,
            'total_sessions': len(sessions),
            'avg_importance': avg_importance,
            'overall_insight': overall_insight
        }
        
        result = session.run(webdata_query, params)
        record = result.single()
        logger.info(f"✅ Created WebData node for customer: {record['created_webdata']}")
    
    def _create_session_node(self, session, analyzed_session: SessionAnalysis) -> None:
        """Create a single Session node with summary and reasoning fields."""
        session_query = """
        // Find the WebData node
        MATCH (w:WebData {customer_id: $customer_id})
        
        // Create Session node with summary and reasoning fields
        CREATE (s:Session {
            session_id: $session_id,
            customer_id: $customer_id,
            session_start: datetime($session_start),
            session_end: datetime($session_end),
            duration_minutes: $duration_minutes,
            event_count: $event_count,
            importance_score: $importance_score,
            confidence_score: $confidence_score,
            digital_chronicles: $digital_chronicles,
            mindset_decoder: $mindset_decoder,
            created_at: datetime()
        })
        
        // Link WebData to Session
        CREATE (w)-[:HAS_SESSION]->(s)
        
        RETURN s.session_id as created_session
        """
        
        params = {
            'customer_id': self.customer_id,
            'session_id': analyzed_session.session_id,
            'session_start': analyzed_session.session_start.isoformat(),
            'session_end': analyzed_session.session_end.isoformat(),
            'duration_minutes': analyzed_session.duration_minutes,
            'event_count': analyzed_session.event_count,
            'importance_score': analyzed_session.importance_score,
            'confidence_score': analyzed_session.confidence_score,
            'digital_chronicles': analyzed_session.digital_chronicles,
            'mindset_decoder': analyzed_session.mindset_decoder
        }
        
        result = session.run(session_query, params)
        record = result.single()
        return record['created_session']
    
    def run_analysis(self, csv_path: str = "data/sessions/AlexanderSessionsShort.csv") -> List[SessionAnalysis]:
        """
        Run the complete analysis pipeline with correct graph structure.
        
        Args:
            csv_path: Path to the CSV file to analyze
            
        Returns:
            List of analyzed sessions
        """
        try:
            logger.info("🚀 Starting Correct Session Analysis Pipeline")
            logger.info("=" * 50)
            logger.info(f"📋 Configuration:")
            logger.info(f"   👤 Customer ID: {self.customer_id}")
            logger.info(f"   📄 CSV File: {csv_path}")
            logger.info(f"   🎯 Importance Threshold: {IMPORTANCE_THRESHOLD}")
            logger.info(f"   📏 Min Events per Session: {MIN_EVENTS_PER_SESSION}")
            logger.info(f"   🤖 AI Model: {AI_MODEL}")
            logger.info("=" * 50)
            
            # Step 1: Clear existing data
            logger.info("🗑️ Step 1: Clearing existing data...")
            self.clear_existing_data()
            
            # Step 2: Process CSV and group into sessions
            logger.info("📊 Step 2: Processing CSV and grouping events...")
            session_events = self.group_events_into_sessions(csv_path)
            
            # Step 3: Analyze sessions with AI (get summary and reasoning)
            logger.info("🤖 Step 3: AI-powered session analysis...")
            analyzed_sessions = self.analyze_sessions_with_ai(session_events)
            
            # Step 4: Create correct graph structure
            logger.info("🏗️ Step 4: Creating graph structure...")
            self.create_graph_structure(analyzed_sessions)
            
            logger.info("🎉 Correct Session Analysis Complete!")
            logger.info("=" * 50)
            logger.info("📊 FINAL SUMMARY:")
            logger.info(f"   ✅ Important sessions analyzed: {len(analyzed_sessions)}")
            if analyzed_sessions:
                avg_importance = sum(s.importance_score for s in analyzed_sessions) / len(analyzed_sessions)
                avg_confidence = sum(s.confidence_score for s in analyzed_sessions) / len(analyzed_sessions)
                logger.info(f"   📈 Average importance score: {avg_importance:.2f}")
                logger.info(f"   📈 Average confidence score: {avg_confidence:.2f}")
            logger.info("=" * 50)
            
            return analyzed_sessions
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            raise
        finally:
            self.neo4j_driver.close()


def main() -> None:
    """Main execution function."""
    try:
        analyzer = CorrectSessionAnalyzer()
        sessions = analyzer.run_analysis()
        
        # Print summary
        logger.info("📊 SUMMARY:")
        logger.info(f"   Important sessions: {len(sessions)}")
        logger.info(f"   Avg importance: {sum(s.importance_score for s in sessions)/len(sessions):.2f}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise


if __name__ == "__main__":
    main() 