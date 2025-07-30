"""Customer management tools for comprehensive customer data retrieval."""

import json
import logging
import re
from typing import Any, Dict, List
from datetime import datetime

from mcp.types import TextContent, Tool
from neo4j import GraphDatabase

from .base import ConnectionRequiredTool, create_tool_schema

logger = logging.getLogger(__name__)


class GetCustomerTagsTool(ConnectionRequiredTool):
    """Tool for getting AI-generated user intent tags for a customer."""
    
    def __init__(self, connection):
        """Initialize customer tags tool."""
        super().__init__(
            name="get_customer_tags",
            description="Get AI-generated user intent tags for a specific customer",
            connection=connection
        )
    
    def get_schema(self) -> Tool:
        """Get the tool schema."""
        return create_tool_schema(
            name=self.name,
            description=self.description,
            properties={
                "customer_id": {
                    "type": "string",
                    "description": "The customer ID to get tags for"
                }
            },
            required=["customer_id"]
        )
    
    async def _execute_with_connection(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get customer's AI-generated tags."""
        customer_id = arguments["customer_id"]
        
        query = """
        MATCH (c:Customer {customer_id: $customer_id})
        RETURN c.customer_full_name as name,
               c.ai_user_intent_tags as tags,
               c.ai_analysis_date as analysis_date
        """
        
        try:
            records, _ = await self.connection.execute_query(query, {"customer_id": customer_id})
            
            if not records:
                return self._format_error_response(f"Customer {customer_id} not found")
            
            record = records[0]
            result = {
                "customer_id": customer_id,
                "customer_name": record.get("name"),
                "intent_tags": record.get("tags", []),
                "analysis_date": record.get("analysis_date"),
                "total_tags": len(record.get("tags", []))
            }
            
            return self._format_success_response(result)
            
        except Exception as e:
            logger.error(f"Error getting customer tags: {e}")
            return self._format_error_response(str(e))


class GetCustomerLikesTool(ConnectionRequiredTool):
    """Tool for getting AI-generated customer likes/preferences."""
    
    def __init__(self, connection):
        """Initialize customer likes tool."""
        super().__init__(
            name="get_customer_likes",
            description="Get AI-generated likes and preferences for a specific customer",
            connection=connection
        )
    
    def get_schema(self) -> Tool:
        """Get the tool schema."""
        return create_tool_schema(
            name=self.name,
            description=self.description,
            properties={
                "customer_id": {
                    "type": "string",
                    "description": "The customer ID to get likes for"
                }
            },
            required=["customer_id"]
        )
    
    async def _execute_with_connection(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get customer's AI-generated likes."""
        customer_id = arguments["customer_id"]
        
        query = """
        MATCH (c:Customer {customer_id: $customer_id})
        RETURN c.customer_full_name as name,
               c.ai_likes as likes,
               c.ai_analysis_date as analysis_date
        """
        
        try:
            records, _ = await self.connection.execute_query(query, {"customer_id": customer_id})
            
            if not records:
                return self._format_error_response(f"Customer {customer_id} not found")
            
            record = records[0]
            result = {
                "customer_id": customer_id,
                "customer_name": record.get("name"),
                "likes": record.get("likes", []),
                "analysis_date": record.get("analysis_date"),
                "total_likes": len(record.get("likes", []))
            }
            
            return self._format_success_response(result)
            
        except Exception as e:
            logger.error(f"Error getting customer likes: {e}")
            return self._format_error_response(str(e))


class GetCustomerDislikesTool(ConnectionRequiredTool):
    """Tool for getting AI-generated customer dislikes."""
    
    def __init__(self, connection):
        """Initialize customer dislikes tool."""
        super().__init__(
            name="get_customer_dislikes",
            description="Get AI-generated dislikes for a specific customer",
            connection=connection
        )
    
    def get_schema(self) -> Tool:
        """Get the tool schema."""
        return create_tool_schema(
            name=self.name,
            description=self.description,
            properties={
                "customer_id": {
                    "type": "string",
                    "description": "The customer ID to get dislikes for"
                }
            },
            required=["customer_id"]
        )
    
    async def _execute_with_connection(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get customer's AI-generated dislikes."""
        customer_id = arguments["customer_id"]
        
        query = """
        MATCH (c:Customer {customer_id: $customer_id})
        RETURN c.customer_full_name as name,
               c.ai_dislikes as dislikes,
               c.ai_analysis_date as analysis_date
        """
        
        try:
            records, _ = await self.connection.execute_query(query, {"customer_id": customer_id})
            
            if not records:
                return self._format_error_response(f"Customer {customer_id} not found")
            
            record = records[0]
            result = {
                "customer_id": customer_id,
                "customer_name": record.get("name"),
                "dislikes": record.get("dislikes", []),
                "analysis_date": record.get("analysis_date"),
                "total_dislikes": len(record.get("dislikes", []))
            }
            
            return self._format_success_response(result)
            
        except Exception as e:
            logger.error(f"Error getting customer dislikes: {e}")
            return self._format_error_response(str(e))


class GetCustomerProductsTool(ConnectionRequiredTool):
    """Tool for getting customer's products organized by category."""
    
    def __init__(self, connection):
        """Initialize customer products tool."""
        super().__init__(
            name="get_customer_products",
            description="Get customer's purchase data organized by product categories",
            connection=connection
        )
    
    def get_schema(self) -> Tool:
        """Get the tool schema."""
        return create_tool_schema(
            name=self.name,
            description=self.description,
            properties={
                "customer_id": {
                    "type": "string",
                    "description": "The customer ID to get products for"
                },
                "limit_orders": {
                    "type": "integer",
                    "description": "Maximum number of sample orders per category (default: 5)",
                    "default": 5
                }
            },
            required=["customer_id"]
        )
    
    async def _execute_with_connection(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get customer's products by category."""
        customer_id = arguments["customer_id"]
        limit_orders = arguments.get("limit_orders", 5)
        
        query = """
        MATCH (c:Customer {customer_id: $customer_id})-[:HIS_PRODUCTS]->(hp:HisProducts)
        -[:HAS_CATEGORY]->(cp:CategoryProducts)-[:BOUGHT]->(o:Order)
        WITH c, hp, cp, 
             collect({
                 order_id: o.order_id,
                 net_sales: o.net_sales,
                 created_at: o.created_at
             })[0..$limit_orders] as sample_orders
        RETURN c.customer_full_name as name,
               hp.name as hub_name,
               hp.total_categories as total_categories,
               hp.total_orders as total_orders,
               hp.total_spent as total_spent,
               collect({
                   category: cp.category,
                   display_name: cp.display_name,
                   category_orders: cp.total_orders,
                   category_spent: cp.total_spent,
                   sample_orders: sample_orders
               }) as categories
        """
        
        try:
            records, _ = await self.connection.execute_query(query, {
                "customer_id": customer_id,
                "limit_orders": limit_orders
            })
            
            if not records:
                return self._format_error_response(f"Customer {customer_id} not found or has no product data")
            
            record = records[0]
            result = {
                "customer_id": customer_id,
                "customer_name": record.get("name"),
                "products_hub": {
                    "name": record.get("hub_name"),
                    "total_categories": record.get("total_categories"),
                    "total_orders": record.get("total_orders"),
                    "total_spent": record.get("total_spent")
                },
                "categories": record.get("categories", []),
                "categories_count": len(record.get("categories", []))
            }
            
            return self._format_success_response(result)
            
        except Exception as e:
            logger.error(f"Error getting customer products: {e}")
            return self._format_error_response(str(e))


class GetCustomerPetsTool(ConnectionRequiredTool):
    """Tool for getting customer's pets organized by type."""
    
    def __init__(self, connection):
        """Initialize customer pets tool."""
        super().__init__(
            name="get_customer_pets",
            description="Get customer's pets organized by pet types",
            connection=connection
        )
    
    def get_schema(self) -> Tool:
        """Get the tool schema."""
        return create_tool_schema(
            name=self.name,
            description=self.description,
            properties={
                "customer_id": {
                    "type": "string",
                    "description": "The customer ID to get pets for"
                }
            },
            required=["customer_id"]
        )
    
    async def _execute_with_connection(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get customer's pets by type."""
        customer_id = arguments["customer_id"]
        
        query = """
        MATCH (c:Customer {customer_id: $customer_id})-[:HIS_PETS]->(hp:HisPets)
        -[:HAS_PET_TYPE]->(ptc:PetTypeCategory)-[:HAS_PET]->(p:Pet)
        WITH c, hp, ptc,
             collect({
                 pet_id: p.petprofile_id,
                 pet_name: p.petprofile_petname,
                 breed: p.petprofile_petbreed_description,
                 birthday: p.petprofile_birthday,
                 weight: p.petprofile_weight,
                 medication: p.petprofile_medication_list
             }) as pets
        RETURN c.customer_full_name as name,
               hp.name as hub_name,
               hp.total_pet_types as total_pet_types,
               hp.total_pets as total_pets,
               collect({
                   pet_type: ptc.pet_type,
                   display_name: ptc.display_name,
                   total_pets: ptc.total_pets,
                   pets: pets
               }) as pet_categories
        """
        
        try:
            records, _ = await self.connection.execute_query(query, {"customer_id": customer_id})
            
            if not records:
                return self._format_error_response(f"Customer {customer_id} not found or has no pet data")
            
            record = records[0]
            result = {
                "customer_id": customer_id,
                "customer_name": record.get("name"),
                "pets_hub": {
                    "name": record.get("hub_name"),
                    "total_pet_types": record.get("total_pet_types"),
                    "total_pets": record.get("total_pets")
                },
                "pet_categories": record.get("pet_categories", []),
                "categories_count": len(record.get("pet_categories", []))
            }
            
            return self._format_success_response(result)
            
        except Exception as e:
            logger.error(f"Error getting customer pets: {e}")
            return self._format_error_response(str(e))


class GetCustomerWebDataTool(ConnectionRequiredTool):
    """Tool for getting customer's web session data."""
    
    def __init__(self, connection):
        """Initialize customer web data tool."""
        super().__init__(
            name="get_customer_web_data",
            description="Get customer's web session data and activity",
            connection=connection
        )
    
    def get_schema(self) -> Tool:
        """Get the tool schema."""
        return create_tool_schema(
            name=self.name,
            description=self.description,
            properties={
                "customer_id": {
                    "type": "string",
                    "description": "The customer ID to get web data for"
                },
                "limit_sessions": {
                    "type": "integer",
                    "description": "Maximum number of sessions to return (default: 10)",
                    "default": 10
                }
            },
            required=["customer_id"]
        )
    
    async def _execute_with_connection(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get customer's web data."""
        customer_id = arguments["customer_id"]
        limit_sessions = arguments.get("limit_sessions", 10)
        
        query = """
        MATCH (c:Customer {customer_id: $customer_id})-[:HAS_WEB_DATA]->(wd:WebData)
        OPTIONAL MATCH (wd)-[:HAS_SESSION]->(s:Session)
        WITH c, wd, 
             collect({
                 session_date: s.session_date,
                 event_count: s.event_count,
                 importance_score: s.importance_score,
                 session_summary: s.session_summary,
                 created_at: s.created_at
             })[0..$limit_sessions] as sessions
        RETURN c.customer_full_name as name,
               wd.created_at as web_data_created,
               count(sessions) as total_sessions,
               sessions
        """
        
        try:
            records, _ = await self.connection.execute_query(query, {
                "customer_id": customer_id,
                "limit_sessions": limit_sessions
            })
            
            if not records:
                return self._format_error_response(f"Customer {customer_id} not found or has no web data")
            
            record = records[0]
            result = {
                "customer_id": customer_id,
                "customer_name": record.get("name"),
                "web_data_created": record.get("web_data_created"),
                "total_sessions": record.get("total_sessions"),
                "sessions": record.get("sessions", []),
                "sessions_returned": len(record.get("sessions", []))
            }
            
            return self._format_success_response(result)
            
        except Exception as e:
            logger.error(f"Error getting customer web data: {e}")
            return self._format_error_response(str(e))


class GetCustomerProfileTool(ConnectionRequiredTool):
    """Tool for getting complete customer profile including AI insights."""
    
    def __init__(self, connection):
        """Initialize customer profile tool."""
        super().__init__(
            name="get_customer_profile",
            description="Get comprehensive customer profile including AI insights and summary",
            connection=connection
        )
    
    def get_schema(self) -> Tool:
        """Get the tool schema."""
        return create_tool_schema(
            name=self.name,
            description=self.description,
            properties={
                "customer_id": {
                    "type": "string",
                    "description": "The customer ID to get profile for"
                }
            },
            required=["customer_id"]
        )
    
    async def _execute_with_connection(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get customer's complete profile."""
        customer_id = arguments["customer_id"]
        
        query = """
        MATCH (c:Customer {customer_id: $customer_id})
        RETURN c.customer_full_name as name,
               c.customer_email_address as email,
               c.customer_registration_dttm as registration_date,
               c.customer_preferred_food_brands as preferred_brands,
               c.customer_autoship_active_flag as has_autoship,
               c.gross_average_order_value as avg_order_value,
               c.customer_repeat as is_repeat_customer,
               c.ai_likes as likes,
               c.ai_dislikes as dislikes,
               c.ai_user_intent_tags as intent_tags,
               c.ai_about_user as about_user,
               c.ai_analysis_date as analysis_date,
               c.created_at as profile_created
        """
        
        try:
            records, _ = await self.connection.execute_query(query, {"customer_id": customer_id})
            
            if not records:
                return self._format_error_response(f"Customer {customer_id} not found")
            
            record = records[0]
            result = {
                "customer_id": customer_id,
                "basic_info": {
                    "name": record.get("name"),
                    "email": record.get("email"),
                    "registration_date": record.get("registration_date"),
                    "preferred_brands": record.get("preferred_brands"),
                    "has_autoship": record.get("has_autoship"),
                    "avg_order_value": record.get("avg_order_value"),
                    "is_repeat_customer": record.get("is_repeat_customer"),
                    "profile_created": record.get("profile_created")
                },
                "ai_insights": {
                    "likes": record.get("likes", []),
                    "dislikes": record.get("dislikes", []),
                    "intent_tags": record.get("intent_tags", []),
                    "about_user": record.get("about_user"),
                    "analysis_date": record.get("analysis_date")
                }
            }
            
            return self._format_success_response(result)
            
        except Exception as e:
            logger.error(f"Error getting customer profile: {e}")
            return self._format_error_response(str(e))


class AddCustomerTool(ConnectionRequiredTool):
    """Tool for adding a new customer with tab-separated data."""
    
    def __init__(self, connection):
        """Initialize add customer tool."""
        super().__init__(
            name="add_customer",
            description="Add a new customer with comprehensive data from tab-separated headers and values",
            connection=connection
        )
    
    def get_schema(self) -> Tool:
        """Get the tool schema."""
        return create_tool_schema(
            name=self.name,
            description=self.description,
            properties={
                "headers": {
                    "type": "string",
                    "description": "Tab-separated headers (column names)"
                },
                "data": {
                    "type": "string",
                    "description": "Tab-separated data values corresponding to headers"
                }
            },
            required=["headers", "data"]
        )
    
    def _sanitize_property_name(self, name: str) -> str:
        """Convert column name to valid Neo4j property name."""
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())
        if sanitized and not sanitized[0].isalpha():
            sanitized = 'prop_' + sanitized
        return sanitized
    
    def _infer_data_type_and_convert(self, value: str, column_name: str):
        """Infer data type and convert value."""
        if value is None or value == '':
            return None
        
        value_str = str(value).strip()
        column_lower = column_name.lower()
        
        # Date/DateTime fields
        if any(keyword in column_lower for keyword in ['dttm', 'date', 'birthday']):
            if value_str and value_str != 'null':
                try:
                    if len(value_str) >= 19:  # Full datetime
                        dt = datetime.strptime(value_str[:19], '%Y-%m-%d %H:%M:%S')
                        return dt.isoformat()
                    elif len(value_str) >= 10:  # Date only
                        return value_str[:10]
                except:
                    pass
        
        # Boolean fields
        if any(keyword in column_lower for keyword in ['flag', 'active']):
            if value_str.lower() in ['true', 'false']:
                return value_str.lower() == 'true'
        
        # Numeric fields
        if any(keyword in column_lower for keyword in ['count', 'id', 'key', 'value', 'weight', 'score', 'nps']):
            try:
                if '.' in value_str:
                    return float(value_str)
                else:
                    return int(value_str)
            except ValueError:
                pass
        
        return value_str
    
    async def _execute_with_connection(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Add new customer."""
        headers_str = arguments["headers"]
        data_str = arguments["data"]
        
        try:
            # Parse data
            header_list = headers_str.strip().split('\t')
            data_list = data_str.strip().split('\t')
            
            if len(header_list) != len(data_list):
                return self._format_error_response(
                    f"Headers count ({len(header_list)}) doesn't match data count ({len(data_list)})"
                )
            
            # Process data
            processed_data = {}
            for i, header in enumerate(header_list):
                if i < len(data_list):
                    original_value = data_list[i].strip() if data_list[i].strip() else None
                    prop_name = self._sanitize_property_name(header)
                    processed_value = self._infer_data_type_and_convert(original_value, header)
                    processed_data[prop_name] = processed_value
            
            customer_id = processed_data.get('customer_id')
            if not customer_id:
                return self._format_error_response("Customer ID is required")
            
            # Check if customer exists
            check_query = "MATCH (c:Customer {customer_id: $customer_id}) RETURN c.customer_id as existing_id"
            existing_records, _ = await self.connection.execute_query(check_query, {"customer_id": str(customer_id)})
            
            if existing_records:
                # Update existing customer
                set_clauses = []
                for prop_name, value in processed_data.items():
                    if value is not None:
                        set_clauses.append(f"c.{prop_name} = ${prop_name}")
                
                update_query = f"""
                MATCH (c:Customer {{customer_id: $customer_id}})
                SET {', '.join(set_clauses)}, c.updated_at = datetime()
                RETURN c.customer_id as updated_id, c.customer_full_name as name
                """
                
                records, _ = await self.connection.execute_query(update_query, processed_data)
                if records:
                    result = {
                        "action": "updated",
                        "customer_id": records[0]["updated_id"],
                        "customer_name": records[0]["name"],
                        "properties_processed": len(processed_data)
                    }
                    return self._format_success_response(result)
            else:
                # Create new customer
                property_assignments = []
                for prop_name, value in processed_data.items():
                    if value is not None:
                        property_assignments.append(f"{prop_name}: ${prop_name}")
                
                create_query = f"""
                CREATE (c:Customer {{
                    {', '.join(property_assignments)},
                    created_at: datetime()
                }})
                RETURN c.customer_id as created_id, c.customer_full_name as name
                """
                
                records, _ = await self.connection.execute_query(create_query, processed_data)
                if records:
                    result = {
                        "action": "created",
                        "customer_id": records[0]["created_id"],
                        "customer_name": records[0]["name"],
                        "properties_processed": len(processed_data)
                    }
                    return self._format_success_response(result)
            
            return self._format_error_response("Failed to create or update customer")
            
        except Exception as e:
            logger.error(f"Error adding customer: {e}")
            return self._format_error_response(str(e))


class AddCustomerPetTool(ConnectionRequiredTool):
    """Tool for adding a pet profile and creating hierarchical structure."""
    
    def __init__(self, connection):
        """Initialize add customer pet tool."""
        super().__init__(
            name="add_customer_pet",
            description="Add a pet profile and create hierarchical pet structure for customer",
            connection=connection
        )
    
    def get_schema(self) -> Tool:
        """Get the tool schema."""
        return create_tool_schema(
            name=self.name,
            description=self.description,
            properties={
                "headers": {
                    "type": "string",
                    "description": "Tab-separated pet profile headers"
                },
                "data": {
                    "type": "string",
                    "description": "Tab-separated pet profile data"
                },
                "create_hierarchy": {
                    "type": "boolean",
                    "description": "Whether to create hierarchical pet structure (default: true)",
                    "default": True
                }
            },
            required=["headers", "data"]
        )
    
    def _sanitize_property_name(self, name: str) -> str:
        """Convert column name to valid Neo4j property name."""
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())
        if sanitized and not sanitized[0].isalpha():
            sanitized = 'prop_' + sanitized
        return sanitized
    
    def _infer_data_type_and_convert(self, value: str, column_name: str):
        """Infer data type and convert value."""
        if value is None or value == '':
            return None
        
        value_str = str(value).strip()
        column_lower = column_name.lower()
        
        # Date/DateTime fields
        if any(keyword in column_lower for keyword in ['dttm', 'date', 'birthday']):
            if value_str and value_str != 'null':
                try:
                    if len(value_str) >= 19:  # Full datetime
                        dt = datetime.strptime(value_str[:19], '%Y-%m-%d %H:%M:%S')
                        return dt.isoformat()
                    elif len(value_str) >= 10:  # Date only
                        return value_str[:10]
                except:
                    pass
        
        # Boolean fields
        if any(keyword in column_lower for keyword in ['flag', 'active', 'estimated', 'adopted']):
            if value_str.lower() in ['true', 'false']:
                return value_str.lower() == 'true'
        
        # Numeric fields
        if any(keyword in column_lower for keyword in ['count', 'id', 'weight', 'metric']):
            try:
                if '.' in value_str:
                    return float(value_str)
                else:
                    return int(value_str)
            except ValueError:
                pass
        
        return value_str
    
    async def _execute_with_connection(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Add pet and create hierarchy."""
        headers_str = arguments["headers"]
        data_str = arguments["data"]
        create_hierarchy = arguments.get("create_hierarchy", True)
        
        try:
            # Parse data
            header_list = headers_str.strip().split('\t')
            data_list = data_str.strip().split('\t')
            
            if len(header_list) != len(data_list):
                return self._format_error_response(
                    f"Headers count ({len(header_list)}) doesn't match data count ({len(data_list)})"
                )
            
            # Process data
            processed_data = {}
            for i, header in enumerate(header_list):
                if i < len(data_list):
                    original_value = data_list[i].strip() if data_list[i].strip() else None
                    prop_name = self._sanitize_property_name(header)
                    processed_value = self._infer_data_type_and_convert(original_value, header)
                    processed_data[prop_name] = processed_value
            
            pet_id = processed_data.get('petprofile_id')
            customer_id = processed_data.get('petprofile_customer_id')
            pet_type = processed_data.get('petprofile_pettype_description')
            
            if not all([pet_id, customer_id, pet_type]):
                return self._format_error_response("Pet ID, Customer ID, and Pet Type are required")
            
            # Create or update pet
            check_query = "MATCH (p:Pet {petprofile_id: $petprofile_id}) RETURN p.petprofile_id as existing_id"
            existing_records, _ = await self.connection.execute_query(check_query, {"petprofile_id": str(pet_id)})
            
            pet_action = "updated" if existing_records else "created"
            
            if existing_records:
                # Update pet
                set_clauses = []
                for prop_name, value in processed_data.items():
                    if value is not None:
                        set_clauses.append(f"p.{prop_name} = ${prop_name}")
                
                update_query = f"""
                MATCH (p:Pet {{petprofile_id: $petprofile_id}})
                SET {', '.join(set_clauses)}, p.updated_at = datetime()
                RETURN p.petprofile_id as pet_id, p.petprofile_petname as pet_name
                """
                
                records, _ = await self.connection.execute_query(update_query, processed_data)
            else:
                # Create pet
                property_assignments = []
                for prop_name, value in processed_data.items():
                    if value is not None:
                        property_assignments.append(f"{prop_name}: ${prop_name}")
                
                create_query = f"""
                CREATE (p:Pet {{
                    {', '.join(property_assignments)},
                    created_at: datetime()
                }})
                RETURN p.petprofile_id as pet_id, p.petprofile_petname as pet_name
                """
                
                records, _ = await self.connection.execute_query(create_query, processed_data)
            
            if not records:
                return self._format_error_response("Failed to create or update pet")
            
            pet_record = records[0]
            result = {
                "pet_action": pet_action,
                "pet_id": pet_record["pet_id"],
                "pet_name": pet_record["pet_name"],
                "customer_id": customer_id,
                "pet_type": pet_type
            }
            
            # Create hierarchical structure if requested
            if create_hierarchy:
                # Create or get His Pets hub
                hub_query = """
                MATCH (c:Customer {customer_id: $customer_id})
                MERGE (hp:HisPets {customer_id: $customer_id})
                ON CREATE SET hp.name = "His Pets",
                             hp.description = "Central hub for all pet types",
                             hp.created_at = datetime(),
                             hp.total_pet_types = 0,
                             hp.total_pets = 0
                MERGE (c)-[:HIS_PETS]->(hp)
                RETURN hp.name as hub_name
                """
                
                hub_records, _ = await self.connection.execute_query(hub_query, {"customer_id": str(customer_id)})
                
                if hub_records:
                    # Create or get pet type category
                    category_query = """
                    MATCH (hp:HisPets {customer_id: $customer_id})
                    MERGE (ptc:PetTypeCategory {customer_id: $customer_id, pet_type: $pet_type})
                    ON CREATE SET ptc.category_name = $pet_type,
                                 ptc.display_name = $pet_type + " Pets",
                                 ptc.created_at = datetime(),
                                 ptc.total_pets = 0
                    MERGE (hp)-[:HAS_PET_TYPE]->(ptc)
                    RETURN ptc.display_name as category_name
                    """
                    
                    category_records, _ = await self.connection.execute_query(category_query, {
                        "customer_id": str(customer_id),
                        "pet_type": pet_type
                    })
                    
                    if category_records:
                        # Link pet to category
                        link_query = """
                        MATCH (ptc:PetTypeCategory {customer_id: $customer_id, pet_type: $pet_type})
                        MATCH (p:Pet {petprofile_id: $pet_id})
                        MERGE (ptc)-[:HAS_PET]->(p)
                        SET ptc.total_pets = ptc.total_pets + 1
                        WITH ptc
                        MATCH (hp:HisPets {customer_id: $customer_id})
                        SET hp.total_pets = hp.total_pets + 1
                        RETURN "linked" as status
                        """
                        
                        link_records, _ = await self.connection.execute_query(link_query, {
                            "customer_id": str(customer_id),
                            "pet_type": pet_type,
                            "pet_id": str(pet_id)
                        })
                        
                        result["hierarchy_created"] = bool(link_records)
                        result["category_name"] = category_records[0]["category_name"]
            
            return self._format_success_response(result)
            
        except Exception as e:
            logger.error(f"Error adding customer pet: {e}")
            return self._format_error_response(str(e)) 