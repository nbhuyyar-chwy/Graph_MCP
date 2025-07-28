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
    
    # ========================================
    # SESSION QUERIES - New Dimension
    # ========================================
    
    @staticmethod
    def get_user_sessions(
        customer_id: Optional[int] = None,
        username: Optional[str] = None,
        importance_level: Optional[str] = None,
        limit: int = 50
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Get sessions for a specific user with optional filters.
        
        Args:
            customer_id: Customer ID to filter by
            username: Username to filter by  
            importance_level: Session importance level filter
            limit: Maximum number of sessions to return
            
        Returns:
            Tuple of (query, parameters)
        """
        conditions = []
        parameters = {"limit": limit}
        
        if customer_id:
            conditions.append("s.customer_id = $customer_id")
            parameters["customer_id"] = customer_id
        elif username:
            conditions.append("u.username = $username")
            parameters["username"] = username
            
        if importance_level:
            conditions.append("s.importance_level = $importance_level")
            parameters["importance_level"] = importance_level
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"""
        MATCH (u:User)-[:HAS_SESSION]->(s:Session)
        {where_clause}
        RETURN s.session_id as session_id, s.customer_id as customer_id,
               s.session_start as session_start, s.session_end as session_end,
               s.channel_grouping as channel, s.importance_level as importance,
               s.confidence_score as confidence, s.adventure_chronicle as chronicle,
               s.departure_mystery as departure_reason,
               u.username as username
        ORDER BY s.session_start DESC
        LIMIT $limit
        """
        
        return query, parameters
    
    @staticmethod
    def get_session_details(session_id: str) -> Tuple[str, Dict[str, Any]]:
        """
        Get detailed information for a specific session including events.
        
        Args:
            session_id: Session ID to retrieve
            
        Returns:
            Tuple of (query, parameters)
        """
        query = """
        MATCH (u:User)-[:HAS_SESSION]->(s:Session {session_id: $session_id})
        OPTIONAL MATCH (s)-[:HAS_EVENT]->(e:SessionEvent)
        RETURN s.session_id as session_id, s.customer_id as customer_id,
               s.session_start as session_start, s.session_end as session_end,
               s.channel_grouping as channel, s.importance_level as importance,
               s.confidence_score as confidence, s.adventure_chronicle as chronicle,
               s.departure_mystery as departure_reason, s.is_bot as is_bot,
               s.is_authenticated as is_authenticated,
               u.username as username,
               collect({
                   event_id: e.event_id,
                   event_name: e.event_name,
                   event_timestamp: e.event_timestamp,
                   event_category: e.event_category,
                   page_type: e.page_type,
                   revenue: e.revenue
               }) as events
        """
        return query, {"session_id": session_id}
    
    @staticmethod
    def get_session_analytics(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        customer_id: Optional[int] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Get session analytics and behavioral insights.
        
        Args:
            start_date: Optional start date filter (YYYY-MM-DD)
            end_date: Optional end date filter (YYYY-MM-DD)
            customer_id: Optional customer ID filter
            
        Returns:
            Tuple of (query, parameters)
        """
        conditions = []
        parameters = {}
        
        if start_date:
            conditions.append("s.session_start >= datetime($start_date)")
            parameters["start_date"] = start_date
            
        if end_date:
            conditions.append("s.session_start <= datetime($end_date)")
            parameters["end_date"] = end_date
            
        if customer_id:
            conditions.append("s.customer_id = $customer_id")
            parameters["customer_id"] = customer_id
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"""
        MATCH (u:User)-[:HAS_SESSION]->(s:Session)
        {where_clause}
        RETURN 
            count(s) as total_sessions,
            count(DISTINCT s.customer_id) as unique_customers,
            avg(duration.inMinutes(s.session_start, s.session_end)) as avg_duration_minutes,
            count(CASE WHEN s.importance_level = 'critical' THEN 1 END) as critical_sessions,
            count(CASE WHEN s.importance_level = 'significant' THEN 1 END) as significant_sessions,
            count(CASE WHEN s.importance_level = 'moderate' THEN 1 END) as moderate_sessions,
            count(CASE WHEN s.importance_level = 'low' THEN 1 END) as low_sessions,
            avg(s.confidence_score) as avg_confidence,
            collect(DISTINCT s.channel_grouping) as channels_used
        """
        
        return query, parameters
    
    @staticmethod
    def get_session_journey(
        customer_id: int,
        limit: int = 20
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Get session journey for a customer showing session sequence.
        
        Args:
            customer_id: Customer ID to analyze
            limit: Maximum number of sessions in journey
            
        Returns:
            Tuple of (query, parameters)
        """
        query = """
        MATCH (u:User)-[:HAS_SESSION]->(s:Session {customer_id: $customer_id})
        OPTIONAL MATCH (s)-[:NEXT_SESSION]->(next_s:Session)
        OPTIONAL MATCH (prev_s:Session)-[:NEXT_SESSION]->(s)
        RETURN s.session_id as session_id, s.session_start as session_start,
               s.importance_level as importance, s.adventure_chronicle as chronicle,
               s.channel_grouping as channel, s.confidence_score as confidence,
               next_s.session_id as next_session_id,
               prev_s.session_id as previous_session_id,
               duration.inMinutes(s.session_start, s.session_end) as duration_minutes
        ORDER BY s.session_start ASC
        LIMIT $limit
        """
        return query, {"customer_id": customer_id, "limit": limit}
    
    @staticmethod
    def get_important_sessions(
        importance_levels: List[str] = None,
        min_confidence: float = 0.7,
        limit: int = 100
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Get sessions marked as important with high confidence.
        
        Args:
            importance_levels: List of importance levels to include
            min_confidence: Minimum confidence score
            limit: Maximum number of sessions to return
            
        Returns:
            Tuple of (query, parameters)
        """
        parameters = {"min_confidence": min_confidence, "limit": limit}
        
        if importance_levels:
            importance_filter = "s.importance_level IN $importance_levels AND"
            parameters["importance_levels"] = importance_levels
        else:
            importance_filter = "s.importance_level IN ['critical', 'significant'] AND"
        
        query = f"""
        MATCH (u:User)-[:HAS_SESSION]->(s:Session)
        WHERE {importance_filter} s.confidence_score >= $min_confidence
        RETURN s.session_id as session_id, s.customer_id as customer_id,
               s.session_start as session_start, s.importance_level as importance,
               s.confidence_score as confidence, s.adventure_chronicle as chronicle,
               s.departure_mystery as departure_reason, s.channel_grouping as channel,
               u.username as username,
               duration.inMinutes(s.session_start, s.session_end) as duration_minutes
        ORDER BY s.confidence_score DESC, s.session_start DESC
        LIMIT $limit
        """
        
        return query, parameters
    
    @staticmethod
    def find_similar_sessions(
        session_id: str,
        similarity_threshold: float = 0.7,
        limit: int = 10
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Find sessions similar to a given session based on behavior patterns.
        
        Args:
            session_id: Reference session ID
            similarity_threshold: Minimum similarity score
            limit: Maximum number of similar sessions
            
        Returns:
            Tuple of (query, parameters)
        """
        query = """
        MATCH (ref:Session {session_id: $session_id})
        MATCH (u:User)-[:HAS_SESSION]->(s:Session)
        WHERE s.session_id <> $session_id
        AND s.importance_level = ref.importance_level
        AND s.channel_grouping = ref.channel_grouping
        AND abs(duration.inMinutes(s.session_start, s.session_end) - 
                duration.inMinutes(ref.session_start, ref.session_end)) <= 30
        RETURN s.session_id as session_id, s.customer_id as customer_id,
               s.session_start as session_start, s.importance_level as importance,
               s.adventure_chronicle as chronicle, s.confidence_score as confidence,
               u.username as username,
               duration.inMinutes(s.session_start, s.session_end) as duration_minutes
        ORDER BY s.confidence_score DESC, s.session_start DESC
        LIMIT $limit
        """
        return query, {"session_id": session_id, "limit": limit}
    
    @staticmethod
    def create_session_node(session_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Create a new session node in the database.
        
        Args:
            session_data: Dictionary containing session information
            
        Returns:
            Tuple of (query, parameters)
        """
        query = """
        MERGE (u:User {customer_id: $customer_id})
        CREATE (s:Session {
            session_id: $session_id,
            customer_id: $customer_id,
            anonymous_id: $anonymous_id,
            session_start: datetime($session_start),
            session_end: datetime($session_end),
            session_date: date($session_date),
            channel_grouping: $channel_grouping,
            is_bot: $is_bot,
            is_authenticated: $is_authenticated,
            adventure_chronicle: $adventure_chronicle,
            departure_mystery: $departure_mystery,
            importance_level: $importance_level,
            confidence_score: $confidence_score
        })
        CREATE (u)-[:HAS_SESSION]->(s)
        RETURN s.session_id as created_session_id
        """
        return query, session_data 