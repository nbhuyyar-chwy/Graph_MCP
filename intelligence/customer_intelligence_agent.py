#!/usr/bin/env python3
"""
Customer Intelligence Agent
==========================

This agent analyzes all available customer data (pets, orders, sessions) 
and uses OpenAI to generate intelligent insights about the customer's:
- Likes
- Dislikes  
- User intent tags
- About user (summary)

The agent gathers data from the hierarchical structure and updates the customer node.
"""

import logging
import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv
from datetime import datetime
import openai

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Setup OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')


class CustomerIntelligenceAgent:
    """AI agent for analyzing customer data and generating insights."""
    
    def __init__(self, customer_id: str):
        """Initialize the intelligence agent."""
        self.customer_id = customer_id
        self.neo4j_driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
        )
        self.customer_data = {}
        self.insights = {}
    
    def __del__(self):
        """Clean up Neo4j driver."""
        if hasattr(self, 'neo4j_driver') and self.neo4j_driver:
            self.neo4j_driver.close()
    
    def gather_customer_data(self):
        """Gather all available data for the customer from Neo4j."""
        logger.info(f"📊 Gathering all data for customer {self.customer_id}...")
        
        with self.neo4j_driver.session() as session:
            
            # 1. Get basic customer information
            customer_query = """
            MATCH (c:Customer {customer_id: $customer_id})
            RETURN c.customer_full_name as name,
                   c.customer_email_address as email,
                   c.customer_registration_dttm as registration_date,
                   c.customer_preferred_food_brands as preferred_brands,
                   c.customer_autoship_active_flag as has_autoship,
                   c.gross_average_order_value as avg_order_value,
                   c.customer_repeat as is_repeat_customer
            """
            
            customer_result = session.run(customer_query, customer_id=self.customer_id)
            customer_record = customer_result.single()
            
            if customer_record:
                self.customer_data['basic_info'] = dict(customer_record)
                logger.info(f"   ✅ Basic info for {customer_record['name']}")
            else:
                logger.error(f"   ❌ Customer {self.customer_id} not found")
                return False
            
            # 2. Get pet data through hierarchy
            pets_query = """
            MATCH (c:Customer {customer_id: $customer_id})-[:HIS_PETS]->(hp:HisPets)
            -[:HAS_PET_TYPE]->(ptc:PetTypeCategory)-[:HAS_PET]->(p:Pet)
            RETURN ptc.pet_type as pet_type,
                   collect({
                       name: p.petprofile_petname,
                       breed: p.petprofile_petbreed_description,
                       age: p.petprofile_birthday,
                       medication: p.petprofile_medication_list,
                       weight: p.petprofile_weight
                   }) as pets
            """
            
            pets_result = session.run(pets_query, customer_id=self.customer_id)
            pets_data = []
            
            for record in pets_result:
                pets_data.append({
                    'type': record['pet_type'],
                    'pets': record['pets']
                })
            
            self.customer_data['pets'] = pets_data
            total_pets = sum(len(category['pets']) for category in pets_data)
            logger.info(f"   ✅ Found {total_pets} pets across {len(pets_data)} categories")
            
            # 3. Get order data through hierarchy
            orders_query = """
            MATCH (c:Customer {customer_id: $customer_id})-[:HIS_PRODUCTS]->(hp:HisProducts)
            -[:HAS_CATEGORY]->(cp:CategoryProducts)-[:BOUGHT]->(o:Order)
            RETURN cp.category as category,
                   cp.total_orders as category_orders,
                   cp.total_spent as category_spent,
                   collect({
                       order_id: o.order_id,
                       net_sales: o.net_sales,
                       order_date: o.order_date
                   })[0..5] as sample_orders
            ORDER BY cp.total_spent DESC
            """
            
            orders_result = session.run(orders_query, customer_id=self.customer_id)
            orders_data = []
            
            for record in orders_result:
                orders_data.append({
                    'category': record['category'],
                    'total_orders': record['category_orders'],
                    'total_spent': record['category_spent'],
                    'sample_orders': record['sample_orders']
                })
            
            self.customer_data['orders'] = orders_data
            total_spent = sum(category['total_spent'] or 0 for category in orders_data)
            logger.info(f"   ✅ Found orders in {len(orders_data)} categories, total spent: ${total_spent:.2f}")
            
            # 4. Get session data
            sessions_query = """
            MATCH (c:Customer {customer_id: $customer_id})-[:HAS_WEB_DATA]->(wd:WebData)-[:HAS_SESSION]->(s:Session)
            RETURN count(s) as total_sessions,
                   collect({
                       session_date: s.session_date,
                       event_count: s.event_count,
                       session_summary: s.session_summary,
                       importance_score: s.importance_score
                   })[0..10] as sample_sessions
            """
            
            sessions_result = session.run(sessions_query, customer_id=self.customer_id)
            sessions_record = sessions_result.single()
            
            if sessions_record:
                self.customer_data['sessions'] = {
                    'total_sessions': sessions_record['total_sessions'],
                    'sample_sessions': sessions_record['sample_sessions']
                }
                logger.info(f"   ✅ Found {sessions_record['total_sessions']} sessions")
            
            return True
    
    def generate_insights_with_openai(self):
        """Use OpenAI to analyze customer data and generate insights."""
        logger.info("🤖 Generating AI insights...")
        
        # Prepare context for OpenAI
        context = f"""
        Analyze this customer data and provide insights about their preferences, behavior, and intent.

        CUSTOMER: {self.customer_data.get('basic_info', {}).get('name', 'Unknown')}
        EMAIL: {self.customer_data.get('basic_info', {}).get('email', 'Unknown')}
        
        BASIC INFO:
        - Registration: {self.customer_data.get('basic_info', {}).get('registration_date', 'Unknown')}
        - Preferred Brands: {self.customer_data.get('basic_info', {}).get('preferred_brands', 'None')}
        - Has Autoship: {self.customer_data.get('basic_info', {}).get('has_autoship', False)}
        - Average Order Value: ${self.customer_data.get('basic_info', {}).get('avg_order_value', 0)}
        - Repeat Customer: {self.customer_data.get('basic_info', {}).get('is_repeat_customer', False)}
        
        PETS:
        {json.dumps(self.customer_data.get('pets', []), indent=2)}
        
        PURCHASE BEHAVIOR:
        {json.dumps(self.customer_data.get('orders', []), indent=2)}
        
        WEBSITE ACTIVITY:
        - Total Sessions: {self.customer_data.get('sessions', {}).get('total_sessions', 0)}
        - Sample Sessions: {json.dumps(self.customer_data.get('sessions', {}).get('sample_sessions', []), indent=2)}
        
        Based on this comprehensive data, provide a JSON response with these exact fields:
        1. "likes": List of 3-5 things the customer clearly likes (products, brands, activities)
        2. "dislikes": List of 2-3 things the customer might dislike or avoid
        3. "user_intent_tags": List of 5-7 short tags describing their shopping intent and behavior
        4. "about_user": A 2-3 sentence summary describing this customer's profile and behavior
        
        Focus on actionable insights for personalization and marketing.
        """
        
        try:
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert customer intelligence analyst for a pet products company. Analyze customer data and provide actionable insights in valid JSON format."},
                    {"role": "user", "content": context}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Parse the response
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response (handle potential markdown formatting)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            self.insights = json.loads(response_text)
            
            logger.info("   ✅ AI insights generated successfully")
            logger.info(f"   🎯 Intent tags: {', '.join(self.insights.get('user_intent_tags', []))}")
            
            return True
            
        except Exception as e:
            logger.error(f"   ❌ Failed to generate insights: {e}")
            return False
    
    def update_customer_node(self):
        """Update the customer node with generated insights."""
        logger.info("💾 Updating customer node with AI insights...")
        
        update_query = """
        MATCH (c:Customer {customer_id: $customer_id})
        SET c.ai_likes = $likes,
            c.ai_dislikes = $dislikes,
            c.ai_user_intent_tags = $user_intent_tags,
            c.ai_about_user = $about_user,
            c.ai_analysis_date = datetime(),
            c.ai_analysis_version = "v1.0"
        RETURN c.customer_full_name as name
        """
        
        with self.neo4j_driver.session() as session:
            result = session.run(update_query,
                               customer_id=self.customer_id,
                               likes=self.insights.get('likes', []),
                               dislikes=self.insights.get('dislikes', []),
                               user_intent_tags=self.insights.get('user_intent_tags', []),
                               about_user=self.insights.get('about_user', ''))
            
            record = result.single()
            if record:
                logger.info(f"   ✅ Updated {record['name']} with AI insights")
                return True
            else:
                logger.error("   ❌ Failed to update customer node")
                return False
    
    def display_insights(self):
        """Display the generated insights."""
        logger.info("🎯 Generated Customer Intelligence Report:")
        logger.info("=" * 60)
        logger.info(f"Customer: {self.customer_data.get('basic_info', {}).get('name', 'Unknown')}")
        logger.info("")
        
        logger.info("👍 LIKES:")
        for like in self.insights.get('likes', []):
            logger.info(f"   • {like}")
        
        logger.info("\n👎 DISLIKES:")
        for dislike in self.insights.get('dislikes', []):
            logger.info(f"   • {dislike}")
        
        logger.info("\n🏷️ INTENT TAGS:")
        logger.info(f"   {', '.join(self.insights.get('user_intent_tags', []))}")
        
        logger.info("\n📋 ABOUT USER:")
        logger.info(f"   {self.insights.get('about_user', 'No summary available')}")
        
        logger.info("=" * 60)
    
    def analyze_customer(self):
        """Main method to run complete customer intelligence analysis."""
        logger.info("🚀 Starting Customer Intelligence Analysis")
        logger.info(f"   🎯 Target: Customer ID {self.customer_id}")
        logger.info("=" * 60)
        
        try:
            # Step 1: Gather data
            if not self.gather_customer_data():
                return False
            
            # Step 2: Generate insights
            if not self.generate_insights_with_openai():
                return False
            
            # Step 3: Update customer node
            if not self.update_customer_node():
                return False
            
            # Step 4: Display results
            self.display_insights()
            
            logger.info("�� Customer Intelligence Analysis Completed Successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            return False


def analyze_matt():
    """Analyze Matt (Customer ID: 6180005)."""
    agent = CustomerIntelligenceAgent("6180005")
    return agent.analyze_customer()


if __name__ == "__main__":
    analyze_matt()
