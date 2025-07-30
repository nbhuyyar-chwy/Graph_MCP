#!/usr/bin/env python3
"""
Matt's Pet Profile Processor - Improved Structure
=================================================

Creates an improved hierarchical structure for Matt's pet data:
Customer → HIS_PETS → His Pets Hub → HAS_PET_TYPE → Pet Type Categories → HAS_PET → Individual Pets

Structure:
Matt (Customer 6180005) 
    ↓ HIS_PETS
    🏢 His Pets Hub (Central Node)
        ↓ HAS_PET_TYPE  
        ├── Horse Pets ──HAS_PET──→ [individual horse pets]
        ├── Cat Pets ──HAS_PET──→ [individual cat pets]
        ├── Dog Pets ──HAS_PET──→ [individual dog pets]
        └── etc.
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


class MattPetProcessor:
    """Processes Matt's pet data into improved hierarchical structure."""
    
    def __init__(self, customer_id: str = "6180005"):
        """Initialize the pet processor."""
        self.customer_id = customer_id
        self.neo4j_driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
        )
        self.stats = {
            'pets_processed': 0,
            'pets_failed': 0,
            'pet_types_created': 0,
            'total_relationships': 0
        }
    
    def __del__(self):
        """Clean up Neo4j driver."""
        if hasattr(self, 'neo4j_driver') and self.neo4j_driver:
            self.neo4j_driver.close()
    
    def get_existing_pets(self):
        """Get all existing pets for this customer."""
        logger.info("📊 Step 1: Analyzing existing pets...")
        
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
            result = session.run(query, customer_id=self.customer_id)
            
            for record in result:
                pet_data = {
                    'pet_id': record['pet_id'],
                    'pet_name': record['pet_name'],
                    'pet_type': record['pet_type'],
                    'pet_node': dict(record['p'])
                }
                pets_data.append(pet_data)
                pet_types[record['pet_type']] += 1
                
                logger.info(f"    🐾 Pet {record['pet_id']}: {record['pet_name']} ({record['pet_type']})")
        
        logger.info(f"✅ Found {len(pets_data)} pets with {len(pet_types)} unique types")
        logger.info(f"    Types: {dict(pet_types)}")
        
        return pets_data, pet_types
    
    def clear_existing_pet_structure(self):
        """Clear existing pet hub structure for this customer."""
        logger.info("🗑️ Step 2: Clearing existing pet structure...")
        
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
        
        with self.neo4j_driver.session() as session:
            for i, query in enumerate(cleanup_queries, 1):
                try:
                    result = session.run(query, customer_id=self.customer_id)
                    summary = result.consume()
                    logger.info(f'   ✅ Cleanup step {i}: Deleted {summary.counters.nodes_deleted} nodes, {summary.counters.relationships_deleted} relationships')
                except Exception as e:
                    logger.info(f'   ⚠️  Cleanup step {i}: {e}')
        
        logger.info("🧹 Cleared existing pet structure")
    
    def create_his_pets_hub(self):
        """Create the central 'His Pets' hub node."""
        logger.info("🏢 Step 3: Creating His Pets hub...")
        logger.info("🏢 Creating central 'His Pets' hub...")
        
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
            result = session.run(query, customer_id=self.customer_id)
            record = result.single()
            if record:
                logger.info(f"   ✅ Created: {record['created_hub']} hub")
    
    def create_pet_type_categories(self, pet_types):
        """Create PetTypeCategory nodes for each pet type."""
        logger.info("🏷️ Step 4: Creating pet type category nodes...")
        logger.info(f"🏷️ Creating {len(pet_types)} pet type category nodes...")
        
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
                                   customer_id=self.customer_id,
                                   pet_type=pet_type)
                record = result.single()
                if record:
                    logger.info(f"   ✅ Created: {record['created_category']} ({count} pets)")
                    self.stats['pet_types_created'] += 1
    
    def link_pets_to_categories(self, pets_data):
        """Link existing pets to their respective pet type categories."""
        logger.info("📦 Step 5: Linking pets to categories...")
        
        success_count = 0
        failed_count = 0
        
        for i, pet_data in enumerate(pets_data, 1):
            try:
                # Link pet to its pet type category
                query = """
                MATCH (ptc:PetTypeCategory {customer_id: $customer_id, pet_type: $pet_type})
                MATCH (p:Pet {petprofile_id: $pet_id})
                
                MERGE (ptc)-[:HAS_PET]->(p)
                
                // Update category statistics
                SET ptc.total_pets = ptc.total_pets + 1
                
                RETURN ptc.pet_type as linked_category, p.petprofile_petname as linked_pet
                """
                
                with self.neo4j_driver.session() as session:
                    result = session.run(query,
                                       customer_id=self.customer_id,
                                       pet_type=pet_data['pet_type'],
                                       pet_id=pet_data['pet_id'])
                    
                    record = result.single()
                    if record:
                        success_count += 1
                        self.stats['total_relationships'] += 1
                        
                        if i % 5 == 0 or i == len(pets_data):
                            logger.info(f"    📊 Progress: {i}/{len(pets_data)} | ✅ Success: {success_count} | ❌ Failed: {failed_count}")
                    else:
                        failed_count += 1
                        logger.warning(f"    ⚠️  Failed to link pet {pet_data['pet_id']}")
                        
            except Exception as e:
                failed_count += 1
                logger.error(f"    ❌ Error linking pet {pet_data['pet_id']}: {e}")
        
        self.stats['pets_processed'] = success_count
        self.stats['pets_failed'] = failed_count
    
    def update_his_pets_statistics(self, pet_types):
        """Update the His Pets hub with aggregated statistics."""
        logger.info("📊 Step 6: Updating His Pets hub statistics...")
        
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
                               customer_id=self.customer_id,
                               total_pet_types=total_pet_types,
                               total_pets=total_pets)
            record = result.single()
            if record:
                logger.info(f"    📊 Updated His Pets statistics: {record['pet_types']} types, {record['pets']} pets")
    
    def verify_improved_graph_structure(self):
        """Verify the created graph structure."""
        logger.info("🔍 Verifying improved pet graph structure...")
        
        print("📋 Improved Pet Graph Structure Verification:")
        print("   🏗️ Customer → HIS_PETS → His Pets Hub → HAS_PET_TYPE → Pet Type Categories → HAS_PET → Individual Pets")
        print()
        
        # Get hub information
        hub_query = """
        MATCH (c:Customer {customer_id: $customer_id})-[:HIS_PETS]->(hp:HisPets)
        RETURN hp.name as hub_name,
               hp.total_pet_types as total_types,
               hp.total_pets as total_pets
        """
        
        with self.neo4j_driver.session() as session:
            result = session.run(hub_query, customer_id=self.customer_id)
            hub_record = result.single()
            
            if hub_record:
                print(f"   🏢 Hub: {hub_record['hub_name']}")
                print(f"      📊 Total Pet Types: {hub_record['total_types']}")
                print(f"      🐾 Total Pets: {hub_record['total_pets']}")
                print()
            
            # Get category details
            category_query = """
            MATCH (hp:HisPets {customer_id: $customer_id})-[:HAS_PET_TYPE]->(ptc:PetTypeCategory)
            OPTIONAL MATCH (ptc)-[:HAS_PET]->(p:Pet)
            RETURN ptc.display_name as category_name,
                   ptc.total_pets as category_count,
                   count(p) as actual_count
            ORDER BY ptc.pet_type
            """
            
            result = session.run(category_query, customer_id=self.customer_id)
            verification_total = 0
            
            for record in result:
                print(f"   🏷️ {record['category_name']}: {record['actual_count']} pets")
                verification_total += record['actual_count']
            
            print(f"\n   �� Verification Total: {verification_total} pets")
    
    def process_pets(self):
        """Main processing workflow."""
        logger.info("🚀 Starting Matt's Improved Pet Processing")
        logger.info("=======================================================")
        logger.info(f"   👤 Customer ID: {self.customer_id}")
        logger.info("   🏗️ Structure: Customer → HIS_PETS → His Pets Hub → HAS_PET_TYPE → Pet Type Categories → HAS_PET → Individual Pets")
        
        try:
            # Step 1: Get existing pets
            pets_data, pet_types = self.get_existing_pets()
            
            if not pets_data:
                logger.error("❌ No pets found for this customer")
                return
            
            # Step 2: Clear existing structure
            self.clear_existing_pet_structure()
            
            # Step 3: Create His Pets hub
            self.create_his_pets_hub()
            
            # Step 4: Create pet type categories
            self.create_pet_type_categories(pet_types)
            
            # Step 5: Link pets to categories
            self.link_pets_to_categories(pets_data)
            
            # Step 6: Update hub statistics
            self.update_his_pets_statistics(pet_types)
            
            # Final summary
            logger.info("🎉 Improved Pet Processing Complete!")
            logger.info("=======================================================")
            logger.info("📊 FINAL SUMMARY:")
            logger.info(f"   ✅ Pets processed successfully: {self.stats['pets_processed']}")
            logger.info(f"   ❌ Pets failed: {self.stats['pets_failed']}")
            logger.info(f"   🏷️ Pet types created: {self.stats['pet_types_created']}")
            logger.info(f"   🔗 Total relationships: {self.stats['total_relationships']}")
            logger.info(f"   📈 Success rate: {(self.stats['pets_processed'] / len(pets_data) * 100):.1f}%")
            logger.info("=======================================================")
            
            # Verify structure
            self.verify_improved_graph_structure()
            
        except Exception as e:
            logger.error(f"❌ Pet processing failed: {e}")
            raise


if __name__ == "__main__":
    processor = MattPetProcessor()
    processor.process_pets()
