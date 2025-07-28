"""
User and Session Analysis Tools for MCP Server

These tools provide natural language summaries and semantic tags
for user behavior and individual sessions based on the graph structure:
Customer → WebData → Session
"""

import logging
from typing import Any, Dict, List
from mcp.types import Tool, TextContent

from ..database import Neo4jConnection
from .base import ConnectionRequiredTool

logger = logging.getLogger(__name__)


class GetUserSummaryTool(ConnectionRequiredTool):
    """Get natural language summary of user behavior and insights."""
    
    def __init__(self, connection: Neo4jConnection):
        super().__init__(
            name="get_user_summary",
            description="Returns a natural language summary of user behavior and tags",
            connection=connection
        )
    
    def get_schema(self) -> Tool:
        """Return the tool schema."""
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Customer ID to get summary for"
                    }
                },
                "required": ["customer_id"]
            }
        )
    
    async def _execute_with_connection(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute the get user summary tool with validated connection."""
        customer_id = arguments.get("customer_id")
        
        if not customer_id:
            return self._format_error_response("customer_id is required")
        
        try:
            # Get user summary from WebData node
            query = """
            MATCH (c:Customer {customer_id: $customer_id})-[:HAS_WEB_DATA]->(w:WebData)
            RETURN w.overall_behavioral_insight as insight,
                   w.total_sessions as total_sessions,
                   w.avg_importance_score as avg_importance,
                   w.created_at as analysis_date
            """
            
            result = await self.connection.execute_read_query(query, {"customer_id": customer_id})
            
            if not result:
                return [TextContent(type="text", text=f"No behavioral analysis found for customer {customer_id}")]
            
            record = result[0]
            insight = record.get("insight", "No insight available")
            total_sessions = record.get("total_sessions", 0)
            avg_importance = record.get("avg_importance", 0.0)
            analysis_date = record.get("analysis_date", "Unknown")
            
            summary = f"""🧠 **User Behavioral Summary for Customer {customer_id}**

📊 **Overview:**
• Total analyzed sessions: {total_sessions}
• Average importance score: {avg_importance:.2f}
• Analysis date: {analysis_date}

🎯 **Behavioral Insight:**
{insight}

✨ This summary combines insights from {total_sessions} user sessions analyzed by AI agents."""
            
            return [TextContent(type="text", text=summary)]
            
        except Exception as e:
            logger.error(f"Error getting user summary: {e}")
            return self._format_error_response(f"Error retrieving user summary: {str(e)}")


class GetUserTagsTool(ConnectionRequiredTool):
    """Get semantic labels and behavioral tags for a user."""
    
    def __init__(self, connection: Neo4jConnection):
        super().__init__(
            name="get_user_tags",
            description="Returns semantic labels (e.g., 'promo-clicker', 'window-shopper')",
            connection=connection
        )
    
    def get_schema(self) -> Tool:
        """Return the tool schema."""
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User/Customer ID to get tags for"
                    }
                },
                "required": ["user_id"]
            }
        )
    
    async def _execute_with_connection(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute the get user tags tool with validated connection."""
        user_id = arguments.get("user_id")
        
        if not user_id:
            return self._format_error_response("user_id is required")
        
        try:
            # Get behavioral patterns from sessions to generate semantic tags
            query = """
            MATCH (c:Customer {customer_id: $user_id})-[:HAS_WEB_DATA]->(w:WebData)-[:HAS_SESSION]->(s:Session)
            RETURN s.digital_chronicles as chronicles,
                   s.mindset_decoder as mindset,
                   s.importance_score as importance,
                   s.event_count as events,
                   s.duration_minutes as duration
            ORDER BY s.importance_score DESC
            """
            
            result = await self.connection.execute_read_query(query, {"user_id": user_id})
            
            if not result:
                return [TextContent(type="text", text=f"No session data found for user {user_id}")]
            
            # Analyze behavioral patterns to generate semantic tags
            tags = self._extract_semantic_tags(result)
            
            tags_text = "\n".join([f"• {tag}" for tag in tags])
            
            response = f"""🏷️ **Semantic Tags for User {user_id}**

Based on analysis of {len(result)} sessions:

{tags_text}

💡 These tags are derived from AI analysis of user behavior patterns across multiple sessions."""
            
            return [TextContent(type="text", text=response)]
            
        except Exception as e:
            logger.error(f"Error getting user tags: {e}")
            return self._format_error_response(f"Error retrieving user tags: {str(e)}")
    
    def _extract_semantic_tags(self, sessions: List[Dict]) -> List[str]:
        """Extract semantic tags from session data."""
        tags = []
        
        # Analyze session patterns
        high_importance_sessions = [s for s in sessions if s.get("importance", 0) > 0.7]
        total_sessions = len(sessions)
        avg_duration = sum(s.get("duration", 0) for s in sessions) / total_sessions if sessions else 0
        avg_events = sum(s.get("events", 0) for s in sessions) / total_sessions if sessions else 0
        
        # Generate behavioral tags based on patterns
        if len(high_importance_sessions) / total_sessions > 0.6:
            tags.append("high-intent-user")
        
        if avg_duration > 30:
            tags.append("thorough-researcher")
        elif avg_duration < 5:
            tags.append("quick-browser")
        
        if avg_events > 50:
            tags.append("active-explorer")
        elif avg_events < 10:
            tags.append("focused-visitor")
        
        # Analyze content patterns from chronicles and mindset
        content_patterns = []
        for session in sessions:
            chronicles = session.get("chronicles", "").lower()
            mindset = session.get("mindset", "").lower()
            content_patterns.extend([chronicles, mindset])
        
        content_text = " ".join(content_patterns)
        
        # Pattern-based semantic tags
        if "purchase" in content_text or "buy" in content_text:
            tags.append("purchase-oriented")
        if "compare" in content_text or "research" in content_text:
            tags.append("comparison-shopper")
        if "cart" in content_text:
            tags.append("cart-user")
        if "search" in content_text:
            tags.append("search-driven")
        if "price" in content_text or "discount" in content_text:
            tags.append("price-conscious")
        if "review" in content_text:
            tags.append("review-reader")
        if "pet" in content_text or "dog" in content_text or "cat" in content_text:
            tags.append("pet-focused")
        
        # Default tag if no specific patterns found
        if not tags:
            tags.append("general-browser")
        
        return tags


class GetSessionSummaryTool(ConnectionRequiredTool):
    """Get short natural language summary of a specific session."""
    
    def __init__(self, connection: Neo4jConnection):
        super().__init__(
            name="get_session_summary",
            description="Returns a short NL summary of the session (intent, friction, persona)",
            connection=connection
        )
    
    def get_schema(self) -> Tool:
        """Return the tool schema."""
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID to get summary for"
                    }
                },
                "required": ["session_id"]
            }
        )
    
    async def _execute_with_connection(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute the get session summary tool with validated connection."""
        session_id = arguments.get("session_id")
        
        if not session_id:
            return self._format_error_response("session_id is required")
        
        try:
            # Get session details
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
            
            result = await self.connection.execute_read_query(query, {"session_id": session_id})
            
            if not result:
                return [TextContent(type="text", text=f"Session {session_id} not found")]
            
            record = result[0]
            chronicles = record.get("chronicles", "No summary available")
            mindset = record.get("mindset", "No reasoning available")
            importance = record.get("importance", 0.0)
            confidence = record.get("confidence", 0.0)
            duration = record.get("duration", 0.0)
            events = record.get("events", 0)
            start_time = record.get("start_time", "Unknown")
            customer_id = record.get("customer_id", "Unknown")
            
            # Create formatted summary
            summary = f"""📱 **Session Summary: {session_id[:25]}...**

👤 **Customer:** {customer_id}
⏰ **Time:** {start_time} | Duration: {duration:.1f} min | Events: {events}
⭐ **Quality:** Importance {importance:.2f} | Confidence {confidence:.2f}

🗺️ **What Happened (Digital Chronicles):**
{chronicles}

🧠 **Why & Persona (Mindset Decoder):**
{mindset}

🎯 **Session Intent:** {"High-value interaction" if importance > 0.7 else "Moderate exploration" if importance > 0.4 else "Light browsing"}
"""
            
            return [TextContent(type="text", text=summary)]
            
        except Exception as e:
            logger.error(f"Error getting session summary: {e}")
            return self._format_error_response(f"Error retrieving session summary: {str(e)}") 