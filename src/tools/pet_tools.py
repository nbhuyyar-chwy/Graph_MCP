"""Pet-specific tools for Neo4j database operations."""

from typing import Any, Dict, List

from mcp.types import TextContent, Tool

from .base import ConnectionRequiredTool, create_tool_schema
from ..database.queries import QueryBuilder
from ..models import Pet, PetSummary, ProductInteraction, VetVisit, MedicalHistory, PetHealthSummary


class GetUserPetsTool(ConnectionRequiredTool):
    """Tool for getting all pets owned by a specific user."""
    
    def __init__(self, connection):
        """Initialize user pets tool."""
        super().__init__(
            name="get_user_pets",
            description="Get all pets owned by a specific user",
            connection=connection
        )
    
    def get_schema(self) -> Tool:
        """Get the tool schema."""
        return create_tool_schema(
            name=self.name,
            description=self.description,
            properties={
                "username": {
                    "type": "string",
                    "description": "The username to find pets for"
                }
            },
            required=["username"]
        )
    
    async def _execute_with_connection(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get user's pets."""
        username = arguments["username"]
        
        try:
            query, params = QueryBuilder.get_user_pets(username)
            records = await self.connection.execute_read_query(query, params)
            
            # Convert to Pet models
            pets = [Pet.from_neo4j_record(record) for record in records]
            pets_data = [pet.to_dict() for pet in pets]
            
            result = {
                "username": username,
                "total_pets": len(pets),
                "pets": pets_data
            }
            
            return self._format_success_response(result)
            
        except Exception as e:
            return self._format_error_response(f"Error getting user pets: {str(e)}")


class GetPetMedicalHistoryTool(ConnectionRequiredTool):
    """Tool for getting complete medical history for a pet."""
    
    def __init__(self, connection):
        """Initialize pet medical history tool."""
        super().__init__(
            name="get_pet_medical_history",
            description="Get complete medical history for a specific pet",
            connection=connection
        )
    
    def get_schema(self) -> Tool:
        """Get the tool schema."""
        return create_tool_schema(
            name=self.name,
            description=self.description,
            properties={
                "pet_name": {
                    "type": "string",
                    "description": "The name of the pet"
                },
                "owner_username": {
                    "type": "string",
                    "description": "The username of the pet owner (optional for more specific search)"
                }
            },
            required=["pet_name"]
        )
    
    async def _execute_with_connection(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get pet's medical history."""
        pet_name = arguments["pet_name"]
        owner_username = arguments.get("owner_username")
        
        try:
            query, params = QueryBuilder.get_pet_medical_history(pet_name, owner_username)
            records = await self.connection.execute_read_query(query, params)
            
            if not records:
                return self._format_error_response(f"Pet '{pet_name}' not found")
            
            # Convert to MedicalHistory model
            medical_history = MedicalHistory.from_neo4j_record(records[0])
            
            return self._format_success_response(medical_history.to_dict())
            
        except Exception as e:
            return self._format_error_response(f"Error getting medical history: {str(e)}")


class SearchPetsByCriteriaTool(ConnectionRequiredTool):
    """Tool for searching pets by various criteria."""
    
    def __init__(self, connection):
        """Initialize pet search tool."""
        super().__init__(
            name="search_pets_by_criteria",
            description="Search for pets based on various criteria",
            connection=connection
        )
    
    def get_schema(self) -> Tool:
        """Get the tool schema."""
        return create_tool_schema(
            name=self.name,
            description=self.description,
            properties={
                "species": {
                    "type": "string",
                    "description": "Pet species (optional)"
                },
                "breed": {
                    "type": "string",
                    "description": "Pet breed (optional)"
                },
                "min_weight": {
                    "type": "number",
                    "description": "Minimum weight in kg (optional)"
                },
                "max_weight": {
                    "type": "number",
                    "description": "Maximum weight in kg (optional)"
                },
                "gender": {
                    "type": "string",
                    "description": "Pet gender (optional)"
                }
            }
        )
    
    async def _execute_with_connection(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Search pets by criteria."""
        try:
            query, params = QueryBuilder.search_pets_by_criteria(
                species=arguments.get("species"),
                breed=arguments.get("breed"),
                min_weight=arguments.get("min_weight"),
                max_weight=arguments.get("max_weight"),
                gender=arguments.get("gender")
            )
            
            records = await self.connection.execute_read_query(query, params)
            
            # Convert to Pet models
            pets = [Pet.from_neo4j_record(record) for record in records]
            pets_data = [pet.to_dict() for pet in pets]
            
            result = {
                "search_criteria": {k: v for k, v in arguments.items() if v is not None},
                "total_found": len(pets),
                "pets": pets_data
            }
            
            return self._format_success_response(result)
            
        except Exception as e:
            return self._format_error_response(f"Error searching pets: {str(e)}")


class GetPetHealthOverviewTool(ConnectionRequiredTool):
    """Tool for getting health overview for a specific pet."""
    
    def __init__(self, connection):
        """Initialize pet health overview tool."""
        super().__init__(
            name="get_pet_health_overview",
            description="Get health overview for a specific pet",
            connection=connection
        )
    
    def get_schema(self) -> Tool:
        """Get the tool schema."""
        return create_tool_schema(
            name=self.name,
            description=self.description,
            properties={
                "pet_name": {
                    "type": "string",
                    "description": "The name of the pet"
                }
            },
            required=["pet_name"]
        )
    
    async def _execute_with_connection(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get pet's health overview."""
        pet_name = arguments["pet_name"]
        
        try:
            query, params = QueryBuilder.get_pet_health_overview(pet_name)
            records = await self.connection.execute_read_query(query, params)
            
            if not records:
                return self._format_error_response(f"Pet '{pet_name}' not found")
            
            # Convert to PetHealthSummary model
            health_summary = PetHealthSummary.from_neo4j_record(records[0])
            
            return self._format_success_response(health_summary.to_dict())
            
        except Exception as e:
            return self._format_error_response(f"Error getting health overview: {str(e)}")


class GetPetsWithActiveMedicationsTool(ConnectionRequiredTool):
    """Tool for getting pets currently on medication."""
    
    def __init__(self, connection):
        """Initialize active medications tool."""
        super().__init__(
            name="get_pets_with_active_medications",
            description="Get pets currently on medication",
            connection=connection
        )
    
    def get_schema(self) -> Tool:
        """Get the tool schema."""
        return create_tool_schema(
            name=self.name,
            description=self.description,
            properties={}
        )
    
    async def _execute_with_connection(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get pets with active medications."""
        try:
            query, params = QueryBuilder.get_pets_with_active_medications()
            records = await self.connection.execute_read_query(query, params)
            
            result = {
                "total_pets_on_medication": len(records),
                "pets_with_medications": records
            }
            
            return self._format_success_response(result)
            
        except Exception as e:
            return self._format_error_response(f"Error getting pets with medications: {str(e)}")


class GetProductInteractionsTool(ConnectionRequiredTool):
    """Tool for getting product interaction data with optional filters."""
    
    def __init__(self, connection):
        """Initialize product interactions tool."""
        super().__init__(
            name="get_product_interactions",
            description="Get product interaction data with optional filters",
            connection=connection
        )
    
    def get_schema(self) -> Tool:
        """Get the tool schema."""
        return create_tool_schema(
            name=self.name,
            description=self.description,
            properties={
                "product_name": {
                    "type": "string",
                    "description": "Filter by product name (optional)"
                },
                "interaction_type": {
                    "type": "string",
                    "description": "Filter by interaction type (optional)"
                },
                "min_rating": {
                    "type": "number",
                    "description": "Minimum rating filter (1-5, optional)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 50)"
                }
            }
        )
    
    async def _execute_with_connection(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get product interactions with filters."""
        try:
            product_name = arguments.get("product_name")
            interaction_type = arguments.get("interaction_type")
            min_rating = arguments.get("min_rating")
            limit = arguments.get("limit", 50)
            
            query, params = QueryBuilder.get_product_interactions(
                product_name=product_name,
                interaction_type=interaction_type,
                min_rating=min_rating
            )
            
            # Add limit to query
            if limit:
                query += f" LIMIT {limit}"
            
            records = await self.connection.execute_read_query(query, params)
            
            # Convert to ProductInteraction models
            interactions = [ProductInteraction.from_neo4j_record(record) for record in records]
            interactions_data = [interaction.to_dict() for interaction in interactions]
            
            result = {
                "search_filters": {k: v for k, v in arguments.items() if v is not None},
                "total_found": len(interactions),
                "product_interactions": interactions_data
            }
            
            return self._format_success_response(result)
            
        except Exception as e:
            return self._format_error_response(f"Error getting product interactions: {str(e)}")


class GetVetAppointmentsTool(ConnectionRequiredTool):
    """Tool for getting vet appointments with optional filters."""
    
    def __init__(self, connection):
        """Initialize vet appointments tool."""
        super().__init__(
            name="get_vet_appointments",
            description="Get vet appointments with optional filters",
            connection=connection
        )
    
    def get_schema(self) -> Tool:
        """Get the tool schema."""
        return create_tool_schema(
            name=self.name,
            description=self.description,
            properties={
                "vet_name": {
                    "type": "string",
                    "description": "Filter by vet name (optional)"
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date filter in YYYY-MM-DD format (optional)"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date filter in YYYY-MM-DD format (optional)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 50)"
                }
            }
        )
    
    async def _execute_with_connection(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get vet appointments with filters."""
        try:
            vet_name = arguments.get("vet_name")
            start_date = arguments.get("start_date")
            end_date = arguments.get("end_date")
            limit = arguments.get("limit", 50)
            
            query, params = QueryBuilder.get_vet_appointments(
                vet_name=vet_name,
                start_date=start_date,
                end_date=end_date
            )
            
            # Add limit to query
            if limit:
                query += f" LIMIT {limit}"
            
            records = await self.connection.execute_read_query(query, params)
            
            # Convert to VetVisit models
            appointments = [VetVisit.from_neo4j_record(record) for record in records]
            appointments_data = [appointment.to_dict() for appointment in appointments]
            
            result = {
                "search_filters": {k: v for k, v in arguments.items() if v is not None},
                "total_found": len(appointments),
                "vet_appointments": appointments_data
            }
            
            return self._format_success_response(result)
            
        except Exception as e:
            return self._format_error_response(f"Error getting vet appointments: {str(e)}") 