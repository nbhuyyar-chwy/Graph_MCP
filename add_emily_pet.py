#!/usr/bin/env python3
"""
Add Emily's Pet Profile (Lucy) to Neo4j
=======================================

This script parses pet profile data and adds it to the Neo4j database
with proper data type conversions and creates the OWNS_PET relationship.
"""

import logging
import os
import re
from neo4j import GraphDatabase
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def sanitize_property_name(name: str) -> str:
    """Convert CSV column name to valid Neo4j property name."""
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())
    if sanitized and not sanitized[0].isalpha():
        sanitized = 'prop_' + sanitized
    return sanitized


def infer_data_type_and_convert(value: str, column_name: str):
    """Infer data type from column name and value, return processed_value."""
    if value is None or value == '':
        return None
    
    value_str = str(value).strip()
    column_lower = column_name.lower()
    
    # Date/DateTime fields
    if any(keyword in column_lower for keyword in ['dttm', 'date', 'birthday']):
        if value_str and value_str != 'null':
            try:
                # Try parsing various date formats
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
    
    # Default to string
    return value_str


def add_emily_pet():
    """Add Emily's pet profile to Neo4j."""
    
    # Raw pet profile data
    headers = """PETPROFILE_ID	PETPROFILE_CUSTOMER_ID	PETPROFILE_MASTER_ID	PETPROFILE_CUSTOMER_MASTER_ID	PETPROFILE_SUBMITTER_ID	PETPROFILE_SUBMITTER_TYPE	PETPROFILE_SUBMITTER_LOGON	PETPROFILE_SUBMITTER_REGISTRATION_DTTM	PETPROFILE_PETNAME	PETPROFILE_PETTYPE_ID	PETPROFILE_PETTYPE_DESCRIPTION	PETPROFILE_PETBREED_ID	PETPROFILE_PETBREED_DESCRIPTION	PETPROFILE_PETBREED_SIZE_TYPE	PETPROFILE_GENDER	PETPROFILE_WEIGHT_TYPE	PETPROFILE_WEIGHT	PETPROFILE_SIZE_TYPE	PETPROFILE_BIRTHDAY	PETPROFILE_BIRTHDAY_ESTIMATED	PETPROFILE_LIFESTAGE	PETPROFILE_ADOPTED	PETPROFILE_ADOPTION_DTTM	PETPROFILE_STATUS	PETPROFILE_STATUS_REASON	PETPROFILE_CREATED_DTTM	PETPROFILE_UPDATED_DTTM	PETPROFILE_PET_ALLERGY_COUNT	PETPROFILE_PET_PHOTO_COUNT	PETPROFILE_LAST_ADDED_DTTM	DW_CREATE_DTTM	DW_UPDATE_DTTM	PETPROFILE_PETPHOTO_URL	PETPROFILE_MED_CONDITION_LIST	PETPROFILE_MEDICATION_LIST	PETPROFILE_FIRST_BIRTHDAY	PETPROFILE_SEVEN_BIRTHDAY	DW_SITE_ID	PETPROFILE_WEIGHT_UOM	PETPROFILE_WEIGHT_METRIC	PETPROFILE_WEIGHT_METRIC_UOM"""
    
    data = """132902163	949033726	132902163	132902132	949033726	R		2024-11-28 04:54:03.000	Lucy	1	Dog	495	Miniature Poodle	XS	FMLE		9	XS	2023-07-20	TRUE	A	TRUE	2024-11-16 05:00:00.000	1		2024-11-28 04:55:34.276	2025-06-12 15:30:22.206	0.00	1.00	2024-12-07 23:21:48.560	2025-07-29 19:41:16.200	2025-07-29 19:41:16.200	//image.chewy.com/catalog/petprofile/949033726/3334D190305371E51F2CAFED42EDC75E		Simparica	2024-07-20	2030-07-20	10	LBR	4.08	KG"""
    
    # Parse the data
    header_list = headers.strip().split('\t')
    data_list = data.strip().split('\t')
    
    logger.info("🚀 Adding Emily's pet profile (Lucy) to Neo4j")
    logger.info(f"   📋 Processing {len(header_list)} pet properties")
    
    # Create processed data dictionary
    processed_data = {}
    for i, header in enumerate(header_list):
        if i < len(data_list):
            original_value = data_list[i].strip() if data_list[i].strip() else None
            prop_name = sanitize_property_name(header)
            processed_value = infer_data_type_and_convert(original_value, header)
            processed_data[prop_name] = processed_value
    
    # Log key information
    logger.info(f"   🐕 Pet: {processed_data.get('petprofile_petname', 'Unknown')}")
    logger.info(f"   🐾 Type: {processed_data.get('petprofile_pettype_description', 'Unknown')}")
    logger.info(f"   🏷️ Breed: {processed_data.get('petprofile_petbreed_description', 'Unknown')}")
    logger.info(f"   👤 Owner ID: {processed_data.get('petprofile_customer_id', 'Unknown')}")
    
    # Connect to Neo4j and insert
    try:
        driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
        )
        
        with driver.session() as session:
            # Check if pet already exists
            check_query = "MATCH (p:Pet {petprofile_id: $petprofile_id}) RETURN p.petprofile_id as existing_id"
            check_result = session.run(check_query, petprofile_id=str(processed_data.get('petprofile_id')))
            existing = check_result.single()
            
            if existing:
                logger.warning(f"   ⚠️  Pet {processed_data.get('petprofile_id')} already exists!")
                logger.info("   🔄 Updating existing pet...")
                
                # Update existing pet
                set_clauses = []
                for prop_name, value in processed_data.items():
                    if value is not None:
                        set_clauses.append(f"p.{prop_name} = ${prop_name}")
                
                update_query = f"""
                MATCH (p:Pet {{petprofile_id: $petprofile_id}})
                SET {', '.join(set_clauses)}, p.updated_at = datetime()
                RETURN p.petprofile_id as updated_id, p.petprofile_petname as pet_name
                """
                
                result = session.run(update_query, **processed_data)
                record = result.single()
                
                if record:
                    logger.info(f"   ✅ Updated pet {record['pet_name']} (ID: {record['updated_id']})")
                else:
                    logger.error("   ❌ Failed to update pet")
            else:
                # Create new pet
                property_assignments = []
                for prop_name, value in processed_data.items():
                    if value is not None:
                        property_assignments.append(f"{prop_name}: ${prop_name}")
                
                create_query = f"""
                CREATE (p:Pet {{
                    {', '.join(property_assignments)},
                    created_at: datetime()
                }})
                RETURN p.petprofile_id as created_id, p.petprofile_petname as pet_name
                """
                
                result = session.run(create_query, **processed_data)
                record = result.single()
                
                if record:
                    logger.info(f"   ✅ Created new pet {record['pet_name']} (ID: {record['created_id']})")
                else:
                    logger.error("   ❌ Failed to create pet")
            
            # Create OWNS_PET relationship between customer and pet
            logger.info("🔗 Creating OWNS_PET relationship...")
            
            relationship_query = """
            MATCH (c:Customer {customer_id: $customer_id})
            MATCH (p:Pet {petprofile_id: $petprofile_id})
            MERGE (c)-[r:OWNS_PET]->(p)
            ON CREATE SET r.created_at = datetime()
            ON MATCH SET r.updated_at = datetime()
            RETURN c.customer_full_name as owner_name, p.petprofile_petname as pet_name
            """
            
            rel_result = session.run(relationship_query,
                                   customer_id=str(processed_data.get('petprofile_customer_id')),
                                   petprofile_id=str(processed_data.get('petprofile_id')))
            rel_record = rel_result.single()
            
            if rel_record:
                logger.info(f"   ✅ {rel_record['owner_name']} now owns {rel_record['pet_name']}")
            else:
                logger.warning("   ⚠️  Could not create ownership relationship - check if customer exists")
        
        driver.close()
        logger.info("🎉 Pet addition process completed!")
        
        # Summary of what was added
        logger.info("📊 Summary:")
        logger.info(f"   🐕 Pet: {processed_data.get('petprofile_petname')} ({processed_data.get('petprofile_pettype_description')})")
        logger.info(f"   🏷️ Breed: {processed_data.get('petprofile_petbreed_description')}")
        logger.info(f"   🎂 Birthday: {processed_data.get('petprofile_birthday')}")
        logger.info(f"   ⚖️ Weight: {processed_data.get('petprofile_weight')} lbs")
        logger.info(f"   💊 Medication: {processed_data.get('petprofile_medication_list')}")
        
    except Exception as e:
        logger.error(f"❌ Failed to add pet: {e}")
        raise


if __name__ == "__main__":
    add_emily_pet()
