#!/usr/bin/env python3
"""
Runner script for Intelligent Session Analysis
"""

import sys
import os
from intelligent_session_analyzer import CorrectSessionAnalyzer

def main():
    print("🤖 Intelligent Session Analyzer")
    print("=" * 50)
    
    # Check if OpenAI API key is set
    if not os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY') == 'your_openai_api_key_here':
        print("❌ Please set your OPENAI_API_KEY in the .env file")
        print("   Edit .env and replace 'your_openai_api_key_here' with your actual OpenAI API key")
        sys.exit(1)
    
    print("✅ Environment setup complete")
    print("\n🚀 Starting analysis...")
    
    try:
        analyzer = CorrectSessionAnalyzer()
        sessions = analyzer.run_analysis()
        
        print(f"\n🎉 Analysis Complete!")
        print(f"📊 Created {len(sessions)} intelligent session nodes in Neo4j")
        
        # Show sample insights
        if sessions:
            print(f"\n🔍 Sample Insight:")
            sample = sessions[0]
            print(f"   Session: {sample.session_id[:30]}...")
            print(f"   Digital Chronicles: {sample.digital_chronicles[:100]}...")
            print(f"   Mindset Decoder: {sample.mindset_decoder[:100]}...")
            print(f"   Importance: {sample.importance_score:.2f}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 