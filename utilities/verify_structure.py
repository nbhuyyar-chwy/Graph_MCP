#!/usr/bin/env python3
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'),
    auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
)

with driver.session() as session:
    print('🎯 CORRECT GRAPH STRUCTURE VERIFICATION')
    print('=' * 50)
    
    # Verify User → WebData → Session structure
    result = session.run('''
        MATCH (u:User {customer_id: 289824860})-[:HAS_WEB_DATA]->(w:WebData)-[:HAS_SESSION]->(s:Session)
        RETURN u.username as user,
               w.total_sessions as webdata_sessions,
               w.total_revenue as webdata_revenue,
               w.overall_behavioral_insight[0..100] as insight_preview,
               count(s) as linked_sessions
    ''')
    
    record = result.single()
    if record:
        print(f'👤 User: {record["user"]}')
        print(f'🕸️  WebData Sessions: {record["webdata_sessions"]}')
        print(f'💰 WebData Revenue: ${record["webdata_revenue"]:.2f}')
        print(f'🧠 Overall Insight Preview: {record["insight_preview"]}...')
        print(f'🔗 Linked Sessions: {record["linked_sessions"]}')
    
    print('\n🔍 SESSION FIELDS VERIFICATION')
    print('-' * 40)
    
    # Check Session nodes have correct fields
    result = session.run('''
        MATCH (s:Session)
        RETURN s.session_id as session_id,
               s.digital_chronicles[0..80] as summary_preview,
               s.mindset_decoder[0..80] as reasoning_preview,
               s.importance_score as importance,
               s.total_revenue as revenue
        LIMIT 3
    ''')
    
    for i, record in enumerate(result, 1):
        print(f'\n📝 Session {i}: {record["session_id"][:25]}...')
        print(f'   💰 Revenue: ${record["revenue"]:.2f}')
        print(f'   ⭐ Importance: {record["importance"]}')
        print(f'   🗺️  Digital Chronicles: {record["summary_preview"]}...')
        print(f'   🧬 Mindset Decoder: {record["reasoning_preview"]}...')
    
    print('\n📊 COMPLETE STRUCTURE SUMMARY')
    print('-' * 35)
    
    # Get complete stats
    result = session.run('''
        MATCH (u:User)-[:HAS_WEB_DATA]->(w:WebData)-[:HAS_SESSION]->(s:Session)
        RETURN count(DISTINCT u) as users,
               count(DISTINCT w) as webdata_nodes,
               count(s) as sessions,
               avg(s.importance_score) as avg_importance,
               sum(s.total_revenue) as total_revenue
    ''')
    
    record = result.single()
    print(f'   👥 Users: {record["users"]}')
    print(f'   🕸️  WebData nodes: {record["webdata_nodes"]}')
    print(f'   📝 Sessions: {record["sessions"]}')
    print(f'   ⭐ Avg Importance: {record["avg_importance"]:.2f}')
    print(f'   💰 Total Revenue: ${record["total_revenue"]:.2f}')

    print('\n🔍 FULL SESSION EXAMPLE')
    print('-' * 25)
    
    # Get one complete session example
    result = session.run('''
        MATCH (s:Session)
        WHERE s.total_revenue > 0
        RETURN s.session_id as session_id,
               s.digital_chronicles as summary,
               s.mindset_decoder as reasoning,
               s.importance_score as importance,
               s.confidence_score as confidence,
               s.total_revenue as revenue,
               s.event_count as events,
               s.duration_minutes as duration
        LIMIT 1
    ''')
    
    record = result.single()
    if record:
        print(f'🆔 Session: {record["session_id"]}')
        print(f'💰 Revenue: ${record["revenue"]:.2f}')
        print(f'📊 Events: {record["events"]} | Duration: {record["duration"]:.1f}min')
        print(f'⭐ Importance: {record["importance"]} | Confidence: {record["confidence"]}')
        print(f'\n🗺️  DIGITAL CHRONICLES:')
        print(f'   {record["summary"]}')
        print(f'\n🧬 MINDSET DECODER:')
        print(f'   {record["reasoning"]}')

driver.close() 