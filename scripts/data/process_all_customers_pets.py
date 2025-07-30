#!/usr/bin/env python3
"""
All Customers Pet Hierarchy Processor
====================================

Applies the improved hierarchical structure to ALL customers with pets:
Customer → HIS_PETS → His Pets Hub → HAS_PET_TYPE → Pet Type Categories → HAS_PET → Individual Pets

This script:
1. Finds all customers who have pets
2. Creates hierarchical structure for each customer
3. Disconnects old direct OWNS_PET relationships
4. Provides comprehensive logging and statistics
"""

import logging
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from datetime import datetime
from collections import defaultdict

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AllCustomersPetProcessor:
    """Processes all customers' pet data into improved hierarchical structure."""
    
    def __init__(self):
        """Initialize the processor."""
        self.neo4j_driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
        )
        self.global_stats = {
            'customers_processed': 0,
            'customers_failed': 0,
            'total_pets_processed': 0,
            'total_pet_types_created': 0,
            'total_relationships_created': 0,
            'direct_relationships_removed': 0
        }
    
    def __del__(self):
        """Clean up Neo4j driver."""
        if hasattr(self, 'neo4j_driver') and self.neo4j_driver:
            self.neo4j_driver.close()
    
    def get_all_customers_with_pets(self):
        """Get all customers who have pets."""
        logger.info("📊 Step 1: Finding all customers with pets...")
        
        query = """
        MATCH (c:Customer)-[:OWNS_PET]->(p:Pet)
        WITH c, count(p) as pet_count, 
             collect(DISTINCT p.petprofile_pettype_description) as pet_types
        RETURN c.customer_id as customer_id,
               pet_count,
               pet_types
        ORDER BY pet_count DESC
        """
        
        customers_data = []
        
        with self.neo4j_driver.session() as session:
            result = session.run(query)
            
            for record in result:
                customer_data = {
                    'customer_id': record['customer_id'],
                    'pet_count': record['pet_count'],
                    'pet_types': record['pet_types']
                }
                customers_data.append(customer_data)
                
                logger.info(f"    👤 Customer {record['customer_id']}: {record['pet_count']} pets, types: {record['pet_types']}")
        
        logger.info(f"✅ Found {len(customers_data)} customers with pets")
        total_pets = sum(c['pet_count'] for c in customers_data)
        logger.info(f"    📊 Total pets to process: {total_pets}")
        
        return customers_data
    
    def get_customer_pets(self, customer_id):
        """Get all pets for a specific customer."""
        query = """
        MATCH (c:Customer {customer_id: $customer_id})-[:OWNS_PET]->(p:Pet)
        RETURN p.petprofile_id as pet_id,
               p.petprofile_petname as pet_name,
               p.petprofile_pettype_description as pet_type,
               p
        ORDER BY p.petprofile_pettype_description, p.petprofile_petname
        """
        
        pets_data = []
        pet_types = defaultdict(int)
        
        with self.neo4j_driver.session() as session:
            result = session.run(query, customer_id=customer_id)
            
            for record in result:
                pet_data = {
                    'pet_id': record['pet_id'],
                    'pet_name': record['pet_name'],
                    'pet_type': record['pet_type'],
                    'pet_node': dict(record['p'])
                }
                pets_data.append(pet_data)
                pet_types[record['pet_type']] += 1
        
        return pets_data, pet_types
    
    def clear_existing_pet_structure(self, customer_id):
        """Clear existing pet hub structure for a customer."""
        cleanup_queries = [
            # Delete old PetTypeCategories and relationships from previous structure
            """
            MATCH (c:Customer {customer_id: $customer_id})-[:HIS_PETS]->(ptc:PetTypeCategory)
            OPTIONAL MATCH (ptc)-[:HAS_PET]->(p:Pet)
            // Remove relationships but keep the pets
            DETACH DELETE ptc
            """,
            
            # Delete any existing HisPets nodes for this customer
            """
            MATCH (hp:HisPets {customer_id: $customer_id})
            DETACH DELETE hp
            """
        ]
        
        nodes_deleted = 0
        relationships_deleted = 0
        
        with self.neo4j_driver.session() as session:
            for query in cleanup_queries:
                try:
                    result = session.run(query, customer_id=customer_id)
                    summary = result.consume()
                    nodes_deleted += summary.counters.nodes_deleted
                    relationships_deleted += summary.counters.relationships_deleted
                except Exception as e:
                    logger.warning(f'   ⚠️  Cleanup issue for customer {customer_id}: {e}')
        
        return nodes_deleted, relationships_deleted
    
    def create_his_pets_hub(self, customer_id):
        """Create the central 'His Pets' hub node."""
        query = """
        MATCH (c:Customer {customer_id: $customer_id})
        
        CREATE (hp:HisPets {
            customer_id: $customer_id,
            name: "His Pets",
            description: "Central hub for all pet types",
            created_at: datetime(),
            total_pet_types: 0,
            total_pets: 0
        })
        
        CREATE (c)-[:HIS_PETS]->(hp)
        
        RETURN hp.name as created_hub
        """
        
        with self.neo4j_driver.session() as session:
            result = session.run(query, customer_id=customer_id)
            record = result.single()
            return bool(record)
    
    def create_pet_type_categories(self, customer_id, pet_types):
        """Create PetTypeCategory nodes for each pet type."""
        categories_created = 0
        
        for pet_type, count in pet_types.items():
            query = """
            MATCH (hp:HisPets {customer_id: $customer_id})
            
            CREATE (ptc:PetTypeCategory {
                customer_id: $customer_id,
                pet_type: $pet_type,
                category_name: $pet_type,
                display_name: $pet_type + " Pets",
                created_at: datetime(),
                total_pets: 0
            })
            
            CREATE (hp)-[:HAS_PET_TYPE]->(ptc)
            
            RETURN ptc.display_name as created_category
            """
            
            with self.neo4j_driver.session() as session:
                result = session.run(query, 
                                   customer_id=customer_id,
                                   pet_type=pet_type)
                record = result.single()
                if record:
                    categories_created += 1
        
        return categories_created
    
    def link_pets_to_categories(self, customer_id, pets_data):
        """Link existing pets to their respective pet type categories."""
        success_count = 0
        failed_count = 0
        
        for pet_data in pets_data:
            try:
                query = """
                MATCH (ptc:PetTypeCategory {customer_id: $customer_id, pet_type: $pet_type})
                MATCH (p:Pet {petprofile_id: $pet_id})
                
                MERGE (ptc)-[:HAS_PET]->(p)
                
                // Update category statistics
                SET ptc.total_pets = ptc.total_pets + 1
                
                RETURN ptc.pet_type as linked_category
                """
                
                with self.neo4j_driver.session() as session:
                    result = session.run(query,
                                       customer_id=customer_id,
                                       pet_type=pet_data['pet_type'],
                                       pet_id=pet_data['pet_id'])
                    
                    record = result.single()
                    if record:
                        success_count += 1
                    else:
                        failed_count += 1
                        
            except Exception as e:
                failed_count += 1
                logger.error(f"    ❌ Error linking pet {pet_data['pet_id']} for customer {customer_id}: {e}")
        
        return success_count, failed_count
    
    def update_his_pets_statistics(self, customer_id, pet_types):
        """Update the His Pets hub with aggregated statistics."""
        total_pets = sum(pet_types.values())
        total_pet_types = len(pet_types)
        
        query = """
        MATCH (hp:HisPets {customer_id: $customer_id})
        SET hp.total_pet_types = $total_pet_types,
            hp.total_pets = $total_pets,
            hp.updated_at = datetime()
        RETURN hp.total_pet_types as pet_types, hp.total_pets as pets
        """
        
        with self.neo4j_driver.session() as session:
            result = session.run(query,
                               customer_id=customer_id,
                               total_pet_types=total_pet_types,
                               total_pets=total_pets)
            record = result.single()
            return bool(record)
    
    def process_single_customer(self, customer_data):
        """Process a single customer's pets."""
        customer_id = customer_data['customer_id']
        
        try:
            # Get customer's pets
            pets_data, pet_types = self.get_customer_pets(customer_id)
            
            if not pets_data:
                logger.warning(f"    ⚠️  No pets found for customer {customer_id}")
                return False
            
            # Clear existing structure
            self.clear_existing_pet_structure(customer_id)
            
            # Create His Pets hub
            if not self.create_his_pets_hub(customer_id):
                logger.error(f"    ❌ Failed to create hub for customer {customer_id}")
                return False
            
            # Create pet type categories
            categories_created = self.create_pet_type_categories(customer_id, pet_types)
            
            # Link pets to categories
            success_count, failed_count = self.link_pets_to_categories(customer_id, pets_data)
            
            # Update hub statistics
            self.update_his_pets_statistics(customer_id, pet_types)
            
            # Update global stats
            self.global_stats['total_pets_processed'] += success_count
            self.global_stats['total_pet_types_created'] += categories_created
            self.global_stats['total_relationships_created'] += success_count
            
            logger.info(f"    ✅ Customer {customer_id}: {success_count}/{len(pets_data)} pets, {categories_created} categories")
            return True
            
        except Exception as e:
            logger.error(f"    ❌ Failed to process customer {customer_id}: {e}")
            return False
    
    def disconnect_all_direct_relationships(self):
        """Remove all direct OWNS_PET relationships."""
        logger.info("🧹 Step 3: Disconnecting all direct OWNS_PET relationships...")
        
        query = """
        MATCH ()-[r:OWNS_PET]->()
        DELETE r
        RETURN count(r) as deleted_relationships
        """
        
        with self.neo4j_driver.session() as session:
            result = session.run(query)
            record = result.single()
            
            if record:
                deleted_count = record['deleted_relationships']
                self.global_stats['direct_relationships_removed'] = deleted_count
                logger.info(f"   ✅ Removed {deleted_count} direct OWNS_PET relationships")
                return deleted_count
        
        return 0
    
    def verify_final_structure(self):
        """Verify the final hierarchical structure."""
        logger.info("🔍 Step 4: Verifying final structure...")
        
        verification_queries = [
            # Count customers with hierarchical pet structure
            """
            MATCH (c:Customer)-[:HIS_PETS]->(hp:HisPets)
            RETURN count(DISTINCT c) as customers_with_hubs
            """,
            
            # Count total pet type categories
            """
            MATCH (ptc:PetTypeCategory)
            RETURN count(ptc) as total_categories
            """,
            
            # Count pets accessible via hierarchy
            """
            MATCH (c:Customer)-[:HIS_PETS]->(hp:HisPets)-[:HAS_PET_TYPE]->(ptc:PetTypeCategory)-[:HAS_PET]->(p:Pet)
            RETURN count(p) as pets_via_hierarchy
            """,
            
            # Check for remaining direct relationships
            """
            MATCH ()-[r:OWNS_PET]->()
            RETURN count(r) as remaining_direct
            """
        ]
        
        with self.neo4j_driver.session() as session:
            for i, query in enumerate(verification_queries):
                result = session.run(query)
                record = result.single()
                
                if i == 0 and record:
                    logger.info(f"   📊 Customers with pet hubs: {record['customers_with_hubs']}")
                elif i == 1 and record:
                    logger.info(f"   📊 Total pet type categories: {record['total_categories']}")
                elif i == 2 and record:
                    logger.info(f"   📊 Pets accessible via hierarchy: {record['pets_via_hierarchy']}")
                elif i == 3 and record:
                    logger.info(f"   📊 Remaining direct relationships: {record['remaining_direct']}")
    
    def process_all_customers(self):
        """Main processing workflow for all customers."""
        logger.info("🚀 Starting All Customers Pet Hierarchy Processing")
        logger.info("=" * 70)
        logger.info("   🏗️ Structure: Customer → HIS_PETS → His Pets Hub → HAS_PET_TYPE → Pet Type Categories → HAS_PET → Individual Pets")
        
        try:
            # Step 1: Get all customers with pets
            customers_data = self.get_all_customers_with_pets()
            
            if not customers_data:
                logger.error("❌ No customers with pets found")
                return
            
            # Step 2: Process each customer
            logger.info("🔧 Step 2: Processing each customer...")
            
            for i, customer_data in enumerate(customers_data, 1):
                logger.info(f"📦 Processing customer {i}/{len(customers_data)}: {customer_data['customer_id']}")
                
                if self.process_single_customer(customer_data):
                    self.global_stats['customers_processed'] += 1
                else:
                    self.global_stats['customers_failed'] += 1
                
                # Progress update every 10 customers
                if i % 10 == 0 or i == len(customers_data):
                    logger.info(f"    📊 Progress: {i}/{len(customers_data)} | ✅ Success: {self.global_stats['customers_processed']} | ❌ Failed: {self.global_stats['customers_failed']}")
            
            # Step 3: Disconnect old relationships
            self.disconnect_all_direct_relationships()
            
            # Step 4: Verify structure
            self.verify_final_structure()
            
            # Final summary
            logger.info("🎉 All Customers Pet Processing Complete!")
            logger.info("=" * 70)
            logger.info("📊 GLOBAL SUMMARY:")
            logger.info(f"   ✅ Customers processed successfully: {self.global_stats['customers_processed']}")
            logger.info(f"   ❌ Customers failed: {self.global_stats['customers_failed']}")
            logger.info(f"   🐾 Total pets processed: {self.global_stats['total_pets_processed']}")
            logger.info(f"   🏷️ Total pet type categories created: {self.global_stats['total_pet_types_created']}")
            logger.info(f"   🔗 Total hierarchical relationships created: {self.global_stats['total_relationships_created']}")
            logger.info(f"   🧹 Direct relationships removed: {self.global_stats['direct_relationships_removed']}")
            logger.info(f"   📈 Success rate: {(self.global_stats['customers_processed'] / len(customers_data) * 100):.1f}%")
            logger.info("=" * 70)
            
        except Exception as e:
            logger.error(f"❌ Processing failed: {e}")
            raise


if __name__ == "__main__":
    processor = AllCustomersPetProcessor()
    processor.process_all_customers() 