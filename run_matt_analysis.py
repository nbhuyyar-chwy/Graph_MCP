#!/usr/bin/env python3
"""
Runner script for Matt's Intelligent Session Analysis
"""

import sys
import os
from intelligent_session_analyzer import CorrectSessionAnalyzer

def main():
    print("🤖 Matt's Intelligent Session Analyzer")
    print("=" * 50)
    
    # Check if OpenAI API key is set
    if not os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY') == 'your_openai_api_key_here':
        print("❌ Please set your OPENAI_API_KEY in the .env file")
        print("   Edit .env and replace 'your_openai_api_key_here' with your actual OpenAI API key")
        sys.exit(1)
    
    print("✅ Environment setup complete")
    print("\n🚀 Starting Matt's analysis...")
    print(f"👤 Customer ID: 6180005")
    print(f"📄 CSV File: data_session/MattSessionShort.csv")
    print("🎯 INCLUDING ALL SESSIONS (importance threshold = 0.0)")
    
    try:
        # Create analyzer with Matt's customer ID
        analyzer = CorrectSessionAnalyzer(customer_id="6180005")
        
        # Override thresholds to include ALL sessions
        import intelligent_session_analyzer
        intelligent_session_analyzer.IMPORTANCE_THRESHOLD = 0.0  # Include all sessions
        intelligent_session_analyzer.MIN_EVENTS_PER_SESSION = 1  # Include single events
        
        # Run analysis with Matt's CSV file
        sessions = analyzer.run_analysis(csv_path="data_session/MattSessionShort.csv")
        
        print(f"\n🎉 Matt's Analysis Complete!")
        print(f"📊 Created {len(sessions)} intelligent session nodes in Neo4j")
        
        # Show sample insights for Matt
        if sessions:
            print(f"\n🔍 Sample Insight for Matt:")
            sample = sessions[0]
            print(f"   Session: {sample.session_id[:30]}...")
            print(f"   Digital Chronicles: {sample.digital_chronicles[:100]}...")
            print(f"   Mindset Decoder: {sample.mindset_decoder[:100]}...")
            print(f"   Importance: {sample.importance_score:.2f}")
            
        # Show summary statistics
        if sessions:
            avg_importance = sum(s.importance_score for s in sessions) / len(sessions)
            avg_confidence = sum(s.confidence_score for s in sessions) / len(sessions)
            total_events = sum(s.event_count for s in sessions)
            total_duration = sum(s.duration_minutes for s in sessions)
            
            print(f"\n📈 Matt's Session Analytics:")
            print(f"   Average Importance Score: {avg_importance:.2f}")
            print(f"   Average Confidence Score: {avg_confidence:.2f}")
            print(f"   Total Events Analyzed: {total_events:,}")
            print(f"   Total Time Analyzed: {total_duration:.1f} minutes")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 