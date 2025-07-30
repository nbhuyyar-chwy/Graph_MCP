# Session Analysis System

## Overview

The Session Analysis System adds a powerful new dimension to the pet care graph database by analyzing user behavioral sessions with intelligent importance scoring and narrative insights.

## 🎯 Key Features

### Session Models
- **Session**: Core session entity with behavioral analysis
- **SessionEvent**: Individual events within sessions  
- **SessionSummary**: Smart behavioral insights
- **SessionAnalysisResult**: Analysis metadata and quality scoring

### Cool Field Names (Adventure & Mystery)
- **`adventure_chronicle`**: Narrative description of what the user did
- **`departure_mystery`**: Hypothesis about why the user left
- **`digital_footprint`**: Pages/areas visited
- **`mission_accomplished`**: Primary goal achieved
- **`journey_highlights`**: Key interaction points
- **`curiosity_signals`**: Search terms and interests

### Importance Levels
- **CRITICAL**: High-value actions (purchases, vet bookings, returns)
- **SIGNIFICANT**: Product research, account updates, cart activity  
- **MODERATE**: General browsing, search, content viewing
- **LOW**: Basic navigation, bounce sessions

## 🚀 Quick Start

### 1. Analyze Alexander's Sessions

```bash
# Basic analysis
python analyze_alexander_sessions.py

# Limit processing for testing
python analyze_alexander_sessions.py --max-rows 1000

# Custom output file
python analyze_alexander_sessions.py --output my_analysis.json
```

### 2. Use the Session Analysis Agent

```python
from src.agents.session_analysis_agent import SessionAnalysisAgent

# Initialize for Alexander (customer ID: 289824860)
agent = SessionAnalysisAgent(customer_id=289824860)

# Process CSV file
results = agent.process_csv_file(
    csv_file_path="data_session/AlexanderSessionsShort.csv",
    max_rows=5000  # Optional limit
)

# Save results
agent.save_analysis_results(results, "analysis_output.json")
```

### 3. Create Database Nodes

```python
from src.database.queries import QueryBuilder
from src.database.connection import Neo4jConnection

# Generate session templates
templates = agent.generate_session_templates(results)

# Create session nodes in database
query_builder = QueryBuilder()
connection = Neo4jConnection()

for template in templates:
    query, params = query_builder.create_session_node(template)
    connection.execute_query(query, params)
```

## 📊 Importance Scoring Logic

### Scoring Criteria

**Event-Based Scoring:**
- Order Completed: +50 points
- Vet Appointment Booked: +45 points  
- Product Added to Cart: +25 points
- Product Viewed: +5 points
- Page Viewed: +1 point

**Behavioral Bonuses:**
- High engagement (20+ events): +15 points
- Long session (30+ minutes): +10 points
- Revenue generation: +up to 50 points
- Vet-related activity: +20 points

**Thresholds:**
- CRITICAL: 40+ points
- SIGNIFICANT: 20+ points  
- MODERATE: 8+ points
- LOW: 0+ points

### Confidence Scoring (0-1)

```python
confidence = min(1.0, 
    event_confidence +      # Based on event count (max 0.4)
    duration_confidence +   # Based on session length (max 0.3)  
    outcome_confidence      # Based on clear goals (max 0.3)
)
```

## 🔗 Graph Relationships

### User → Session
```cypher
(u:User)-[:HAS_SESSION]->(s:Session)
```

### Session → Session (Temporal)
```cypher
(s1:Session)-[:NEXT_SESSION]->(s2:Session)
```

### Session → Events
```cypher
(s:Session)-[:HAS_EVENT]->(e:SessionEvent)
```

## 📈 Query Examples

### Get Important Sessions
```cypher
MATCH (u:User)-[:HAS_SESSION]->(s:Session)
WHERE s.importance_level IN ['critical', 'significant']
  AND s.confidence_score >= 0.7
RETURN s.session_id, s.adventure_chronicle, s.departure_mystery
ORDER BY s.confidence_score DESC
```

### Session Journey Analysis
```cypher
MATCH (u:User {customer_id: 289824860})-[:HAS_SESSION]->(s:Session)
OPTIONAL MATCH (s)-[:NEXT_SESSION]->(next:Session)
RETURN s.session_start, s.importance_level, s.adventure_chronicle,
       next.session_id as next_session
ORDER BY s.session_start ASC
```

### Session Analytics
```cypher
MATCH (u:User)-[:HAS_SESSION]->(s:Session)
WHERE s.session_start >= datetime('2025-06-01T00:00:00Z')
RETURN 
    count(s) as total_sessions,
    avg(s.confidence_score) as avg_confidence,
    count(CASE WHEN s.importance_level = 'critical' THEN 1 END) as critical_sessions
```

## 🎯 Behavioral Insights

### Adventure Chronicles (Examples)
- *"User embarked on a digital journey via Direct - conducted 3 search expeditions - explored 8 product territories - gathered 2 items for potential acquisition - browsing for 12.3 focused minutes."*

- *"User embarked on a digital journey via Organic Search - successfully completed 1 purchase missions - spending 45.2 minutes in deep exploration."*

### Departure Mysteries (Examples)
- *"Mission accomplished! Successfully completed their purchase and departed satisfied."*
- *"Hesitation at the final frontier - left with items in cart, perhaps to return later."*
- *"Still seeking the perfect solution - departed mid-quest, possibly to continue elsewhere."*

## 🛠️ Configuration

### Custom Importance Weights
```python
agent.processor.event_importance_weights.update({
    'Custom Event': 30,
    'Special Action': 25
})
```

### Custom Thresholds  
```python
agent.importance_thresholds = {
    SessionImportance.CRITICAL: 50,
    SessionImportance.SIGNIFICANT: 25,
    SessionImportance.MODERATE: 10,
    SessionImportance.LOW: 0
}
```

### Custom Keywords
```python
agent.processor.vet_keywords.extend(['wellness', 'checkup'])
agent.processor.product_keywords.extend(['wishlist', 'compare'])
```

## 📝 Output Format

### Analysis JSON Structure
```json
{
  "analysis_metadata": {
    "customer_id": 289824860,
    "total_sessions_analyzed": 45,
    "important_sessions": 12,
    "analysis_timestamp": "2025-01-02T10:30:00Z",
    "avg_confidence_score": 0.73
  },
  "sessions": [
    {
      "session_id": "session_289824860_20250602_23",
      "customer_id": 289824860,
      "session_start": "2025-06-02T23:18:55.764Z",
      "session_end": "2025-06-02T23:45:12.123Z",
      "importance_level": "critical",
      "confidence_score": 0.85,
      "adventure_chronicle": "User embarked on a digital journey...",
      "departure_mystery": "Mission accomplished! Successfully...",
      "analysis_metadata": {
        "processing_time_ms": 156.7,
        "events_processed": 23,
        "quality_score": 0.91
      }
    }
  ]
}
```

## 🔧 Advanced Usage

### Custom Event Processing
```python
class CustomSessionProcessor(SessionProcessor):
    def _categorize_event(self, event_name, row):
        # Custom categorization logic
        if 'subscription' in event_name.lower():
            return EventCategory.ECOMMERCE
        return super()._categorize_event(event_name, row)

agent = SessionAnalysisAgent()
agent.processor = CustomSessionProcessor()
```

### Batch Processing
```python
# Process multiple CSV files
csv_files = ['session1.csv', 'session2.csv', 'session3.csv']
all_results = []

for csv_file in csv_files:
    results = agent.process_csv_file(csv_file, max_rows=1000)
    all_results.extend(results)

# Combine and save
agent.save_analysis_results(all_results, 'combined_analysis.json')
```

## 🚨 Error Handling

The system includes comprehensive error handling:
- Invalid CSV formats
- Missing required fields
- Timestamp parsing errors
- Memory management for large files
- Validation of analysis results

Check the `session_analysis.log` file for detailed processing logs.

## 📚 API Reference

### SessionAnalysisAgent
- `process_csv_file(csv_file_path, max_rows=None)`
- `save_analysis_results(results, output_file)`
- `generate_session_templates(results)`

### Session Model
- `analyze_importance()` → SessionImportance
- `generate_adventure_chronicle()` → str
- `generate_departure_mystery()` → str
- `calculate_confidence_score()` → float
- `calculate_duration_minutes()` → float

### QueryBuilder (Session Methods)
- `get_user_sessions(customer_id, importance_level, limit)`
- `get_session_details(session_id)`
- `get_session_analytics(start_date, end_date)`
- `get_session_journey(customer_id, limit)`
- `create_session_node(session_data)`

---

*Built with ❤️ for behavioral analysis and graph-based insights* 