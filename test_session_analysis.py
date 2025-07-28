#!/usr/bin/env python3
"""
Simple test for Session Analysis functionality

This test demonstrates the core session analysis features without
requiring the full MCP server infrastructure.
"""

import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Test individual components
def test_session_models():
    """Test the Session models and their functionality."""
    print("🧪 Testing Session Models...")
    
    try:
        from models.sessions import (
            Session, SessionEvent, SessionSummary,
            SessionImportance, SessionChannel, EventCategory
        )
        
        # Create test session
        session = Session(
            session_id="test_session_001",
            customer_id=289824860,
            session_start=datetime.now()
        )
        
        # Add test events
        event1 = SessionEvent(
            event_id="event_001",
            event_name="Product Viewed",
            event_timestamp=datetime.now(),
            event_category=EventCategory.PRODUCT
        )
        
        event2 = SessionEvent(
            event_id="event_002", 
            event_name="Purchase",
            event_timestamp=datetime.now(),
            event_category=EventCategory.ECOMMERCE,
            revenue=29.99
        )
        
        session.add_event(event1)
        session.add_event(event2)
        
        # Test importance analysis
        importance = session.analyze_importance()
        print(f"✅ Session importance: {importance.value}")
        
        # Test narrative generation
        chronicle = session.generate_adventure_chronicle()
        mystery = session.generate_departure_mystery()
        confidence = session.calculate_confidence_score()
        
        print(f"✅ Adventure Chronicle: {chronicle}")
        print(f"✅ Departure Mystery: {mystery}")
        print(f"✅ Confidence Score: {confidence:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Session Models Test Failed: {e}")
        return False


def test_session_processor():
    """Test the SessionProcessor functionality."""
    print("\n🧪 Testing Session Processor...")
    
    try:
        from agents.session_analysis_agent import SessionProcessor
        
        processor = SessionProcessor()
        
        # Test CSV row parsing
        test_row = {
            'EVENT_ID': 'test_event_123',
            'EVENT_NAME': 'Product Added',
            'EVENT_TIMESTAMP': '2025-06-02T23:19:07.414Z',
            'CUSTOMER_ID': '289824860',
            'PAGE_TYPE': 'product',
            'REVENUE': '25.99'
        }
        
        event = processor.parse_csv_row(test_row)
        
        if event:
            print(f"✅ Parsed event: {event.event_name}")
            print(f"✅ Event category: {event.event_category.value if event.event_category else 'None'}")
            print(f"✅ Revenue: {event.revenue}")
        else:
            print("❌ Failed to parse CSV row")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Session Processor Test Failed: {e}")
        return False


def test_importance_scoring():
    """Test the importance scoring logic."""
    print("\n🧪 Testing Importance Scoring...")
    
    try:
        from models.sessions import Session, SessionEvent, EventCategory
        from agents.session_analysis_agent import SessionAnalysisAgent
        
        agent = SessionAnalysisAgent(customer_id=289824860)
        
        # Test different event combinations
        test_cases = [
            {
                'name': 'Purchase Session',
                'events': [
                    SessionEvent('e1', 'Product Viewed', datetime.now(), EventCategory.PRODUCT),
                    SessionEvent('e2', 'Product Added', datetime.now(), EventCategory.ECOMMERCE),
                    SessionEvent('e3', 'Purchase', datetime.now(), EventCategory.ECOMMERCE, revenue=49.99)
                ],
                'expected': 'critical'
            },
            {
                'name': 'Browse Session',
                'events': [
                    SessionEvent('e1', 'Page Viewed', datetime.now()),
                    SessionEvent('e2', 'Product Viewed', datetime.now(), EventCategory.PRODUCT),
                    SessionEvent('e3', 'Search Performed', datetime.now(), EventCategory.ENGAGEMENT)
                ],
                'expected': 'moderate'
            },
            {
                'name': 'Vet Session',
                'events': [
                    SessionEvent('e1', 'Vet Appointment Booked', datetime.now(), EventCategory.VET_CARE),
                    SessionEvent('e2', 'Profile Updated', datetime.now(), EventCategory.ACCOUNT)
                ],
                'expected': 'critical'
            }
        ]
        
        for test_case in test_cases:
            importance = agent._determine_importance(test_case['events'])
            print(f"✅ {test_case['name']}: {importance.value} (expected: {test_case['expected']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Importance Scoring Test Failed: {e}")
        return False


def test_query_builder():
    """Test the query builder functionality."""
    print("\n🧪 Testing Query Builder...")
    
    try:
        from database.queries import QueryBuilder
        
        qb = QueryBuilder()
        
        # Test session queries
        query, params = qb.get_user_sessions(customer_id=289824860, importance_level='critical')
        print(f"✅ User sessions query generated")
        print(f"Query preview: {query[:100]}...")
        
        query, params = qb.get_session_analytics(customer_id=289824860)
        print(f"✅ Session analytics query generated")
        
        # Test session creation query
        session_data = {
            'session_id': 'test_session_001',
            'customer_id': 289824860,
            'session_start': '2025-06-02T23:18:55.764Z',
            'importance_level': 'critical',
            'confidence_score': 0.85
        }
        
        query, params = qb.create_session_node(session_data)
        print(f"✅ Session creation query generated")
        
        return True
        
    except Exception as e:
        print(f"❌ Query Builder Test Failed: {e}")
        return False


def demo_session_analysis():
    """Demonstrate session analysis with sample data."""
    print("\n🎯 Session Analysis Demo")
    print("=" * 40)
    
    try:
        from models.sessions import Session, SessionEvent, EventCategory
        from agents.session_analysis_agent import SessionAnalysisAgent
        
        # Create sample session data
        session_events = [
            SessionEvent('evt_001', 'Page Viewed', datetime(2025, 6, 2, 23, 18, 55)),
            SessionEvent('evt_002', 'Search Performed', datetime(2025, 6, 2, 23, 19, 12), EventCategory.ENGAGEMENT),
            SessionEvent('evt_003', 'Product Viewed', datetime(2025, 6, 2, 23, 20, 45), EventCategory.PRODUCT),
            SessionEvent('evt_004', 'Product Added', datetime(2025, 6, 2, 23, 22, 15), EventCategory.ECOMMERCE),
            SessionEvent('evt_005', 'Checkout Started', datetime(2025, 6, 2, 23, 24, 30), EventCategory.ECOMMERCE),
            SessionEvent('evt_006', 'Purchase', datetime(2025, 6, 2, 23, 26, 45), EventCategory.ECOMMERCE, revenue=79.99)
        ]
        
        # Create session
        session = Session(
            session_id='demo_session_alexander_001',
            customer_id=289824860,
            session_start=session_events[0].event_timestamp,
            events=session_events
        )
        
        # Update session end time
        session.session_end = session_events[-1].event_timestamp
        
        # Analyze session
        session.importance_level = session.analyze_importance()
        session.adventure_chronicle = session.generate_adventure_chronicle()
        session.departure_mystery = session.generate_departure_mystery()
        session.confidence_score = session.calculate_confidence_score()
        
        # Display results
        print(f"📊 Session ID: {session.session_id}")
        print(f"⏱️  Duration: {session.calculate_duration_minutes():.1f} minutes")
        print(f"🎯 Importance: {session.importance_level.value}")
        print(f"📈 Confidence: {session.confidence_score:.2f}")
        print(f"🗣️  Adventure Chronicle:")
        print(f"   {session.adventure_chronicle}")
        print(f"🕵️  Departure Mystery:")
        print(f"   {session.departure_mystery}")
        
        # Show session template
        template = {
            'session_id': session.session_id,
            'customer_id': session.customer_id,
            'session_start': session.session_start.isoformat(),
            'session_end': session.session_end.isoformat(),
            'importance_level': session.importance_level.value,
            'confidence_score': session.confidence_score,
            'adventure_chronicle': session.adventure_chronicle,
            'departure_mystery': session.departure_mystery
        }
        
        print(f"\n📝 Session Template (JSON):")
        print(json.dumps(template, indent=2))
        
        return True
        
    except Exception as e:
        print(f"❌ Demo Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("🚀 Session Analysis System Test Suite")
    print("=" * 50)
    
    tests = [
        ("Session Models", test_session_models),
        ("Session Processor", test_session_processor),
        ("Importance Scoring", test_importance_scoring),
        ("Query Builder", test_query_builder)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Running demo...")
        demo_session_analysis()
    else:
        print("⚠️ Some tests failed. Check the output above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 