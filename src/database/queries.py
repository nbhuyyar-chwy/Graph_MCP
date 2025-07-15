"""
Cypher query builders for the pet care database.

This module contains pre-built Cypher queries for common operations
on the pet care database schema.
"""

from typing import Any, Dict, List, Optional, Tuple


class QueryBuilder:
    """Builder class for constructing Cypher queries for the pet care database."""
    
    @staticmethod
    def get_user_pets(username: str) -> Tuple[str, Dict[str, Any]]:
        """
        Get all pets owned by a specific user.
        
        Args:
            username: The username to find pets for
            
        Returns:
            Tuple of (query, parameters)
        """
        query = """
        MATCH (u:User {username: $username})-[:OWNS]->(p:Pet)
        RETURN p.name as pet_name, p.species as species, p.breed as breed, 
               p.birth_date as birth_date, p.weight_kg as weight, p.gender as gender,
               p.color as color, p.microchip_id as microchip_id
        ORDER BY p.name
        """
        return query, {"username": username}
    
    @staticmethod
    def get_pet_medical_history(
        pet_name: str, 
        owner_username: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Get complete medical history for a pet.
        
        Args:
            pet_name: Name of the pet
            owner_username: Optional username for more specific search
            
        Returns:
            Tuple of (query, parameters)
        """
        if owner_username:
            query = """
            MATCH (u:User {username: $owner_username})-[:OWNS]->(p:Pet {name: $pet_name})
            OPTIONAL MATCH (p)-[:HAS_VISIT]->(v:VetVisit)-[:WITH_VET]->(vet:Vet)
            OPTIONAL MATCH (p)-[:HAS_MEDICATION]->(m:Medication)
            RETURN p.name as pet_name, p.species as species, p.breed as breed,
                   collect(DISTINCT {
                       visit_date: v.date,
                       reason: v.reason,
                       diagnosis: v.diagnosis,
                       treatment: v.treatment,
                       follow_up_date: v.follow_up_date,
                       notes: v.notes,
                       vet_name: vet.name,
                       clinic: vet.clinic
                   }) as vet_visits,
                   collect(DISTINCT {
                       medication_name: m.medication_name,
                       dosage: m.dosage,
                       frequency: m.frequency,
                       start_date: m.start_date,
                       duration_days: m.duration_days,
                       reason: m.reason,
                       notes: m.notes
                   }) as medications
            """
            parameters = {"pet_name": pet_name, "owner_username": owner_username}
        else:
            query = """
            MATCH (p:Pet {name: $pet_name})
            OPTIONAL MATCH (p)-[:HAS_VISIT]->(v:VetVisit)-[:WITH_VET]->(vet:Vet)
            OPTIONAL MATCH (p)-[:HAS_MEDICATION]->(m:Medication)
            RETURN p.name as pet_name, p.species as species, p.breed as breed,
                   collect(DISTINCT {
                       visit_date: v.date,
                       reason: v.reason,
                       diagnosis: v.diagnosis,
                       treatment: v.treatment,
                       follow_up_date: v.follow_up_date,
                       notes: v.notes,
                       vet_name: vet.name,
                       clinic: vet.clinic
                   }) as vet_visits,
                   collect(DISTINCT {
                       medication_name: m.medication_name,
                       dosage: m.dosage,
                       frequency: m.frequency,
                       start_date: m.start_date,
                       duration_days: m.duration_days,
                       reason: m.reason,
                       notes: m.notes
                   }) as medications
            """
            parameters = {"pet_name": pet_name}
        
        return query, parameters
    
    @staticmethod
    def get_vet_appointments(
        vet_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Get vet appointments with optional filters.
        
        Args:
            vet_name: Optional vet name filter
            start_date: Optional start date filter (YYYY-MM-DD)
            end_date: Optional end date filter (YYYY-MM-DD)
            
        Returns:
            Tuple of (query, parameters)
        """
        conditions = []
        parameters = {}
        
        if vet_name:
            conditions.append("vet.name CONTAINS $vet_name")
            parameters["vet_name"] = vet_name
        
        if start_date:
            conditions.append("v.date >= date($start_date)")
            parameters["start_date"] = start_date
            
        if end_date:
            conditions.append("v.date <= date($end_date)")
            parameters["end_date"] = end_date
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"""
        MATCH (p:Pet)-[:HAS_VISIT]->(v:VetVisit)-[:WITH_VET]->(vet:Vet),
              (u:User)-[:OWNS]->(p)
        {where_clause}
        RETURN v.date as visit_date, v.reason as reason, v.diagnosis as diagnosis,
               v.treatment as treatment, v.follow_up_date as follow_up_date,
               p.name as pet_name, p.species as species,
               u.username as owner,
               vet.name as vet_name, vet.clinic as clinic
        ORDER BY v.date DESC
        """
        
        return query, parameters
    
    @staticmethod
    def get_product_interactions(
        product_name: Optional[str] = None,
        interaction_type: Optional[str] = None,
        min_rating: Optional[float] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Get product interaction data with optional filters.
        
        Args:
            product_name: Optional product name filter
            interaction_type: Optional interaction type filter
            min_rating: Optional minimum rating filter
            
        Returns:
            Tuple of (query, parameters)
        """
        conditions = []
        parameters = {}
        
        if product_name:
            conditions.append("prod.product_name CONTAINS $product_name")
            parameters["product_name"] = product_name
        
        if interaction_type:
            conditions.append("pi.interaction_type = $interaction_type")
            parameters["interaction_type"] = interaction_type
            
        if min_rating is not None:
            conditions.append("pi.rating >= $min_rating")
            parameters["min_rating"] = min_rating
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"""
        MATCH (p:Pet)-[:INTERACTED_WITH]->(pi:ProductInteraction)-[:ABOUT_PRODUCT]->(prod:Product),
              (u:User)-[:OWNS]->(p)
        {where_clause}
        RETURN pi.date as interaction_date, pi.interaction_type as interaction_type,
               pi.quantity as quantity, pi.feedback as feedback, pi.rating as rating,
               pi.notes as notes,
               p.name as pet_name, p.species as species,
               u.username as owner,
               prod.product_name as product_name, prod.brand as brand, 
               prod.category as category, prod.attributes as attributes
        ORDER BY pi.date DESC
        """
        
        return query, parameters
    
    @staticmethod
    def search_pets_by_criteria(
        species: Optional[str] = None,
        breed: Optional[str] = None,
        min_weight: Optional[float] = None,
        max_weight: Optional[float] = None,
        gender: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Search pets by various criteria.
        
        Args:
            species: Optional species filter
            breed: Optional breed filter
            min_weight: Optional minimum weight filter
            max_weight: Optional maximum weight filter
            gender: Optional gender filter
            
        Returns:
            Tuple of (query, parameters)
        """
        conditions = []
        parameters = {}
        
        if species:
            conditions.append("p.species = $species")
            parameters["species"] = species
        
        if breed:
            conditions.append("p.breed CONTAINS $breed")
            parameters["breed"] = breed
            
        if min_weight is not None:
            conditions.append("p.weight_kg >= $min_weight")
            parameters["min_weight"] = min_weight
            
        if max_weight is not None:
            conditions.append("p.weight_kg <= $max_weight")
            parameters["max_weight"] = max_weight
            
        if gender:
            conditions.append("p.gender = $gender")
            parameters["gender"] = gender
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"""
        MATCH (u:User)-[:OWNS]->(p:Pet)
        {where_clause}
        RETURN p.name as pet_name, p.species as species, p.breed as breed,
               p.birth_date as birth_date, p.weight_kg as weight, p.gender as gender,
               p.color as color, p.microchip_id as microchip_id,
               u.username as owner
        ORDER BY p.name
        """
        
        return query, parameters
    
    @staticmethod
    def get_recent_vet_visits(days: int = 30) -> Tuple[str, Dict[str, Any]]:
        """
        Get recent vet visits within specified days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Tuple of (query, parameters)
        """
        query = """
        MATCH (p:Pet)-[:HAS_VISIT]->(v:VetVisit)-[:WITH_VET]->(vet:Vet),
              (u:User)-[:OWNS]->(p)
        WHERE v.date >= date() - duration({days: $days})
        RETURN v.date as visit_date, p.name as pet_name, u.username as owner,
               v.reason as reason, v.diagnosis as diagnosis, vet.name as vet_name
        ORDER BY v.date DESC
        """
        return query, {"days": days}
    
    @staticmethod
    def get_pets_with_active_medications() -> Tuple[str, Dict[str, Any]]:
        """
        Get pets currently on medication.
        
        Returns:
            Tuple of (query, parameters)
        """
        query = """
        MATCH (u:User)-[:OWNS]->(p:Pet)-[:HAS_MEDICATION]->(m:Medication)
        WHERE m.start_date <= date() AND 
              (m.start_date + duration({days: m.duration_days})) >= date()
        RETURN u.username as owner, p.name as pet_name, 
               m.medication_name as medication, m.dosage as dosage,
               m.frequency as frequency, m.reason as reason
        ORDER BY u.username, p.name
        """
        return query, {}
    
    @staticmethod
    def get_product_ratings() -> Tuple[str, Dict[str, Any]]:
        """
        Get average ratings for products.
        
        Returns:
            Tuple of (query, parameters)
        """
        query = """
        MATCH (p:Pet)-[:INTERACTED_WITH]->(pi:ProductInteraction)-[:ABOUT_PRODUCT]->(prod:Product)
        WHERE pi.rating IS NOT NULL
        RETURN prod.product_name as product, prod.brand as brand, 
               prod.category as category,
               avg(pi.rating) as avg_rating, count(pi) as total_interactions
        ORDER BY avg_rating DESC, total_interactions DESC
        """
        return query, {}
    
    @staticmethod
    def get_vet_workload() -> Tuple[str, Dict[str, Any]]:
        """
        Get vet workload statistics.
        
        Returns:
            Tuple of (query, parameters)
        """
        query = """
        MATCH (vet:Vet)<-[:WITH_VET]-(v:VetVisit)
        RETURN vet.name as vet_name, vet.clinic as clinic,
               count(v) as total_visits,
               min(v.date) as first_visit,
               max(v.date) as last_visit
        ORDER BY total_visits DESC
        """
        return query, {}
    
    @staticmethod
    def get_pets_needing_followup() -> Tuple[str, Dict[str, Any]]:
        """
        Get pets that need follow-up visits.
        
        Returns:
            Tuple of (query, parameters)
        """
        query = """
        MATCH (u:User)-[:OWNS]->(p:Pet)-[:HAS_VISIT]->(v:VetVisit)
        WHERE v.follow_up_date IS NOT NULL AND v.follow_up_date >= date()
        RETURN u.username as owner, p.name as pet_name,
               v.date as visit_date, v.follow_up_date as follow_up_date,
               v.reason as visit_reason, v.diagnosis as diagnosis
        ORDER BY v.follow_up_date ASC
        """
        return query, {}
    
    @staticmethod
    def get_popular_products(limit: int = 10) -> Tuple[str, Dict[str, Any]]:
        """
        Get most popular products by interaction count.
        
        Args:
            limit: Maximum number of products to return
            
        Returns:
            Tuple of (query, parameters)
        """
        query = """
        MATCH (p:Pet)-[:INTERACTED_WITH]->(pi:ProductInteraction)-[:ABOUT_PRODUCT]->(prod:Product)
        RETURN prod.product_name as product, prod.brand as brand,
               prod.category as category,
               count(pi) as interaction_count,
               avg(pi.rating) as avg_rating,
               collect(DISTINCT pi.interaction_type) as interaction_types
        ORDER BY interaction_count DESC
        LIMIT $limit
        """
        return query, {"limit": limit}
    
    @staticmethod
    def get_pet_health_overview(pet_name: str) -> Tuple[str, Dict[str, Any]]:
        """
        Get health overview for a specific pet.
        
        Args:
            pet_name: Name of the pet
            
        Returns:
            Tuple of (query, parameters)
        """
        query = """
        MATCH (u:User)-[:OWNS]->(p:Pet {name: $pet_name})
        OPTIONAL MATCH (p)-[:HAS_VISIT]->(v:VetVisit)
        OPTIONAL MATCH (p)-[:HAS_MEDICATION]->(m:Medication)
        RETURN p.name as pet_name, p.species as species, p.breed as breed,
               p.birth_date as birth_date, p.weight_kg as weight,
               u.username as owner,
               count(DISTINCT v) as total_vet_visits,
               count(DISTINCT m) as total_medications,
               max(v.date) as last_vet_visit
        """
        return query, {"pet_name": pet_name} 