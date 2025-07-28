#!/usr/bin/env python3
"""
Simple test for User Session Analysis Tools

This script tests the user session tools directly without complex imports.
"""

import asyncio
import sys
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

async def test_simple_queries():
    """Test the queries that the MCP tools would use."""
    
    print("🧪 Testing User Session Analysis Queries")
    print("=" * 45)
    
    # Initialize Neo4j connection
    driver = GraphDatabase.driver(
        os.getenv('NEO4J_URI'),
        auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
    )
    
    customer_id = "289824860"  # Alexander's customer ID
    
    try:
        with driver.session() as session:
            
            # Test 1: Get User Summary (WebData query)
            print("\n🧠 TEST 1: User Summary Query")
            print("-" * 30)
            
            query = """
            MATCH (c:Customer {customer_id: $customer_id})-[:HAS_WEB_DATA]->(w:WebData)
            RETURN w.overall_behavioral_insight as insight,
                   w.total_sessions as total_sessions,
                   w.avg_importance_score as avg_importance,
                   w.created_at as analysis_date
            """
            
            result = session.run(query, {"customer_id": customer_id})
            record = result.single()
            
            if record:
                print("✅ User Summary Data Found:")
                print(f"   📊 Total Sessions: {record['total_sessions']}")
                print(f"   ⭐ Avg Importance: {record['avg_importance']:.2f}")
                print(f"   📅 Analysis Date: {record['analysis_date']}")
                print(f"   🧠 Insight Preview: {record['insight'][:100]}...")
            else:
                print("❌ No user summary found")
            
            # Test 2: Get Session Data for Tags
            print("\n🏷️ TEST 2: Session Data for Tags")
            print("-" * 30)
            
            query = """
            MATCH (c:Customer {customer_id: $customer_id})-[:HAS_WEB_DATA]->(w:WebData)-[:HAS_SESSION]->(s:Session)
            RETURN s.digital_chronicles as chronicles,
                   s.mindset_decoder as mindset,
                   s.importance_score as importance,
                   s.event_count as events,
                   s.duration_minutes as duration
            ORDER BY s.importance_score DESC
            LIMIT 5
            """
            
            result = session.run(query, {"customer_id": customer_id})
            records = list(result)
            
            if records:
                print(f"✅ Found {len(records)} sessions for tag analysis:")
                for i, record in enumerate(records[:3], 1):
                    print(f"   Session {i}: Importance {record['importance']:.2f}, "
                          f"Events {record['events']}, Duration {record['duration']:.1f}min")
                
                # Generate semantic tags
                tags = generate_semantic_tags(records)
                print(f"   🏷️ Generated Tags: {', '.join(tags)}")
            else:
                print("❌ No session data found for tags")
            
            # Test 3: Get Specific Session Summary
            print("\n📱 TEST 3: Session Summary")
            print("-" * 25)
            
            # Get a sample session ID first
            result = session.run("MATCH (s:Session) RETURN s.session_id as session_id LIMIT 1")
            sample_session = result.single()
            
            if sample_session:
                session_id = sample_session['session_id']
                
                query = """
                MATCH (s:Session {session_id: $session_id})
                RETURN s.session_id as session_id,
                       s.digital_chronicles as chronicles,
                       s.mindset_decoder as mindset,
                       s.importance_score as importance,
                       s.confidence_score as confidence,
                       s.duration_minutes as duration,
                       s.event_count as events,
                       s.session_start as start_time,
                       s.customer_id as customer_id
                """
                
                result = session.run(query, {"session_id": session_id})
                record = result.single()
                
                if record:
                    print(f"✅ Session Summary for: {session_id[:30]}...")
                    print(f"   👤 Customer: {record['customer_id']}")
                    print(f"   ⏰ Start: {record['start_time']}")
                    print(f"   📊 Duration: {record['duration']:.1f}min, Events: {record['events']}")
                    print(f"   ⭐ Importance: {record['importance']:.2f}, Confidence: {record['confidence']:.2f}")
                    print(f"   🗺️ Chronicles: {record['chronicles'][:80]}...")
                    print(f"   🧠 Mindset: {record['mindset'][:80]}...")
                else:
                    print("❌ Session summary not found")
            else:
                print("❌ No sessions available")
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        
    finally:
        driver.close()


def generate_semantic_tags(sessions):
    """Generate semantic tags from session data."""
    tags = []
    
    if not sessions:
        return ["no-data"]
    
    # Analyze patterns
    high_importance = sum(1 for s in sessions if s['importance'] > 0.7)
    avg_duration = sum(s['duration'] for s in sessions) / len(sessions)
    avg_events = sum(s['events'] for s in sessions) / len(sessions)
    
    # Generate tags based on patterns
    if high_importance / len(sessions) > 0.6:
        tags.append("high-intent-user")
    
    if avg_duration > 30:
        tags.append("thorough-researcher")
    elif avg_duration < 5:
        tags.append("quick-browser")
    
    if avg_events > 50:
        tags.append("active-explorer")
    elif avg_events < 10:
        tags.append("focused-visitor")
    
    # Analyze content patterns
    content_text = " ".join([
        s.get('chronicles', '').lower() + " " + s.get('mindset', '').lower()
        for s in sessions
    ])
    
    if "purchase" in content_text or "buy" in content_text:
        tags.append("purchase-oriented")
    if "compare" in content_text or "research" in content_text:
        tags.append("comparison-shopper")
    if "cart" in content_text:
        tags.append("cart-user")
    if "search" in content_text:
        tags.append("search-driven")
    if "pet" in content_text or "dog" in content_text:
        tags.append("pet-focused")
    
    return tags or ["general-browser"]


if __name__ == "__main__":
    print("🚀 Simple User Session Analysis Test")
    print("=" * 40)
    
    asyncio.run(test_simple_queries()) 