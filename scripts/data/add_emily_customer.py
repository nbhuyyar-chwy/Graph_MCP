#!/usr/bin/env python3
"""
Add Emily Dokken Customer to Neo4j
=================================

This script parses customer data and adds it to the Neo4j database
with proper data type conversions for dates, numbers, and booleans.
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
    
    # Default to string
    return value_str


def add_emily_customer():
    """Add Emily Dokken customer to Neo4j."""
    
    # Raw customer data
    headers = """CUSTOMER_KEY	CUSTOMER_ID	CUSTOMER_LOGON_ID	CUSTOMER_FULL_NAME	CUSTOMER_FIRST_NAME	CUSTOMER_LAST_NAME	CUSTOMER_REGISTRATION_DTTM	CUSTOMER_REGISTRATION_UPDATE_DTTM	CUSTOMER_REGISTRATION_CANCEL_DTTM	CUSTOMER_LAST_SESSION_DTTM	CUSTOMER_ORDER_FIRST_PLACED_DTTM	CUSTOMER_ORDER_LAST_PLACED_DTTM	CUSTOMER_REPEAT	CUSTOMER_REFERRAL_CODE	CUSTOMER_NPS	CUSTOMER_AUTOSHIP_TOTAL_COUNT	CUSTOMER_AUTOSHIP_CANCELED_COUNT	CUSTOMER_AUTOSHIP_ACTIVE_COUNT	CUSTOMER_AUTOSHIP_NEXT_DTTM	CUSTOMER_AUTOSHIP_LAST_CANCEL_DTTM	CUSTOMER_AUTOSHIP_LAST_CREATE_DTTM	CUSTOMER_SHIP_LAST_STATE	CUSTOMER_REFERRALS_COUNT	CUSTOMER_PREFERRED_FOOD_BRANDS	CUSTOMER_RECENT_PROMOTION_CODES	CUSTOMER_SHOPPING_CART_LAST_UPDATE_DTTM	CUSTOMER_SHOPPING_CART_ITEM_LIST	CUSTOMER_PETS	CUSTOMER_AUTOSHIP_ACTIVE_FLAG	CUSTOMER_TOP_CAT_PRODUCTS	CUSTOMER_TOP_DOG_PRODUCTS	CUSTOMER_ORDER_FIRST_SHIPPED_DTTM	CUSTOMER_TOP_PRODUCTS	CUSTOMER_ORDER_FIRST_PLACED_ORDER_ID	CUSTOMER_ORDER_FIRST_SHIPPED_ORDER_ID	CUSTOMER_ORDER_LAST_SHIPPED_DTTM	CUSTOMER_MULTIPLE_ACCOUNT_FLAG	CUSTOMER_ORDER_FIRST_AUTOREORDER_PLACED_DTTM	CUSTOMER_ORDER_FIRST_AUTOREORDER_SHIPPED_DTTM	CUSTOMER_GROUP_NAME	CUSTOMER_LAST_SHIPPED_ADDRESS_ID	GROSS_AVERAGE_ORDER_VALUE	NET_AVERAGE_ORDER_VALUE	CUSTOMER_ORDER_SHIPPED_CONSISTENCY	CUSTOMER_DIRECT_MAIL_UNSUBSCRIBED_FLAG	CUSTOMER_EMAIL_UNSUBSCRIBED_FLAG	CUSTOMER_PURCHASE_HISTORY_DESCRIPTION	CUSTOMER_PHARMACY_FIRST_ORDER_DESCRIPTION	CUSTOMER_PHARMACY_FLAG	CUSTOMER_PET_PROFILE_EXIST_FLAG	CUSTOMER_PREFERRED_FOOD_BRANDS_RX	CUSTOMER_ORDER_FIRST_PLACED_DTTM_RX	CUSTOMER_ORDER_FIRST_PLACED_ORDER_ID_RX	CUSTOMER_ORDER_LAST_PLACED_DTTM_RX	CUSTOMER_ORDER_FIRST_SHIPPED_DTTM_RX	CUSTOMER_ORDER_FIRST_SHIPPED_ORDER_ID_RX	CUSTOMER_ORDER_LAST_SHIPPED_DTTM_RX	CUSTOMER_ORDER_FIRST_AUTOREORDER_PLACED_DTTM_RX	CUSTOMER_ORDER_FIRST_AUTOREORDER_SHIPPED_DTTM_RX	CUSTOMER_ORDER_FIRST_PLACED_DTTM_NETWORK	CUSTOMER_ORDER_FIRST_PLACED_ORDER_ID_NETWORK	CUSTOMER_ORDER_LAST_PLACED_DTTM_NETWORK	CUSTOMER_ORDER_FIRST_SHIPPED_DTTM_NETWORK	CUSTOMER_ORDER_FIRST_SHIPPED_ORDER_ID_NETWORK	CUSTOMER_ORDER_LAST_SHIPPED_DTTM_NETWORK	CUSTOMER_ORDER_FIRST_AUTOREORDER_SHIPPED_DTTM_NETWORK	CUSTOMER_ACQUISITION_SEGMENT	CUSTOMER_TRANSITION_DESCRIPTION	CUSTOMER_ORDER_FIRST_SHIPPED_DTTM_RX_RETAIL	CUSTOMER_ORDER_FIRST_SHIPPED_DTTM_RX_PETSMART	CUSTOMER_ORDER_FIRST_AUTOREORDER_SHIPPED_DTTM_RX_RETAIL	CUSTOMER_ORDER_FIRST_AUTOREORDER_SHIPPED_DTTM_RX_PETSMART	CUSTOMER_ORDER_FIRST_SHIPPED_DTTM_RX_WHOLESALE	CUSTOMER_ORDER_FIRST_AUTOREORDER_SHIPPED_DTTM_RX_WHOLESALE	CUSTOMER_ORDER_FIRST_SHIPPED_DTTM_CHEWY_INC	CUSTOMER_ORDER_FIRST_AUTOREORDER_SHIPPED_DTTM_CHEWY_INC	CUSTOMER_ORDER_FIRST_SHIPPED_ORDER_ID_TOTAL_CHEWY_INC	CUSTOMER_MASTER_ID	CUSTOMER_STATUS	CUSTOMER_SHIP_METHOD	CUSTOMER_ORDER_FIRST_SHIPPED_CHEWYPRO_DTTM	CUSTOMER_ORDER_FIRST_AUTOREORDER_SHIPPED_CHEWYPRO_DTTM	CUSTOMER_EMAIL_ADDRESS	CUSTOMER_EMAIL_ADDRESS1	CUSTOMER_EMAIL_ADDRESS2	CUSTOMER_EMAIL_ADDRESS_SHA256_HASH_FACEBOOK	CUSTOMER_MARKETING_AUTHORIZATION_FLAG	CUSTOMER_ORDER_FIRST_SHIPPED_DTTM_HS	CUSTOMER_PETSCRIPTION_USER_ID	CUSTOMER_ORDER_FIRST_SHIPPED_DTTM_RX_VIRTUAL_CARE	CUSTOMER_ORDER_FIRST_SHIPPED_DTTM_CHEWY_WHOLESALE	CUSTOMER_FIRST_POLICY_DTTM	CUSTOMER_ACTIVE_POLICY_FLAG	APPLE_IDP_FLAG	APPLE_IDP_LINK_DATE	GOOGLE_IDP_FLAG	GOOGLE_IDP_LINK_DATE	CUSTOMER_INITIAL_IDP	CUSTOMER_CURRENT_ACCOUNT_TYPE	CUSTOMER_INITIAL_ACCOUNT_TYPE	CUSTOMER_INITIAL_REGISTRATION_DTTM	CUSTOMER_OTA_CONVERSION	CUSTOMER_RETURNING_ONETIME	CUSTOMER_RETURNING_REGULAR_REGISTRATION	CUSTOMER_ORDER_FIRST_SHIPPED_REGISTERED_DTTM	CUSTOMER_ORDER_FIRST_SHIPPED_ONE_TIME_DTTM	PERSON_ID	VETCARE_CUSTOMER_FIRST_APPOINTMENT_SCHEDULE_DTTM	VETCARE_CUSTOMER_FIRST_APPOINTMENT_DTTM	VETCARE_CUSTOMER_FIRST_VISIT_DTTM	VETCARE_CUSTOMER_FIRST_CHEWY_ORDER_PLACED_POST_FIRST_VISIT_DTTM	IS_VETCARE_CUSTOMER	CUSTOMER_VETCARE_MEMBERSHIP_ACTIVE_FLAG	MFA_PHONE_FLAG	HEALTH_CARE_PHONE_FLAG	LOYALTY_MEMBER_FLAG	CLINIC_USERS_FLAG"""
    
    data = """112845556450	949033726	emdokken@gmail.com	Emily Dokken			2024-11-28 04:54:03.000			2025-07-27 18:11:00.640	2025-01-10 05:00:00.000	2025-06-25 04:00:00.000	TRUE			1	0	1	2025-12-12 05:00:00.000		2025-01-10 05:00:00.000			Nutramax				Dog	TRUE		508862	2025-01-11 05:00:00.000	988878,508862	1616683321	1616683321	2025-06-25 04:00:00.000	TRUE	2025-01-10 23:49:14.131	2025-01-11 16:47:08.940		115214564	81.07	70.82	44.24	FALSE	FALSE	Chewy,Pharmacy	Chewy	TRUE	TRUE	Nutramax	2025-01-10 00:00:00.000	1616683321	2025-07-01 00:00:00.000	2025-01-13 00:00:00.000	1616683321	2025-07-02 00:00:00.000	2025-01-10 00:00:00.000	2025-01-13 00:00:00.000	2025-01-10 00:00:00.000	1616683321	2025-06-25 04:00:00.000	2025-01-11 16:47:08.940	1616683321	2025-07-02 00:00:00.000	2025-01-10 00:00:00.000	Chewy	Chewy to Pharmacy	2025-01-13 03:44:56.803		2025-01-13 03:44:56.803				2025-01-11 16:47:08.940	2025-01-11 16:47:08.940	1616683321	132902132	1				emdokken@gmail.com	emdokken@gmail.com		349d0a25bb139d6f4fde64b7f201d43510abecd7ce0780797b2f3a3b62896548	TRUE		12780351				FALSE	FALSE		TRUE	2024-11-28 04:54:03.676	Google	REGISTERED	REGISTERED		FALSE			2025-01-11 05:00:00.000		97e6facf-3909-34b6-9a79-88cee29718c0	2024-11-28 04:59:15.000	2024-11-29 19:30:00.000	2025-01-03 17:16:27.000	2025-01-10 23:49:14.131	TRUE	ACTIVE	FALSE	TRUE	FALSE	FALSE"""
    
    # Parse the data
    header_list = headers.strip().split('\t')
    data_list = data.strip().split('\t')
    
    logger.info("🚀 Adding Emily Dokken customer to Neo4j")
    logger.info(f"   📋 Processing {len(header_list)} customer properties")
    
    # Create processed data dictionary
    processed_data = {}
    for i, header in enumerate(header_list):
        if i < len(data_list):
            original_value = data_list[i].strip() if data_list[i].strip() else None
            prop_name = sanitize_property_name(header)
            processed_value = infer_data_type_and_convert(original_value, header)
            processed_data[prop_name] = processed_value
    
    # Log key information
    logger.info(f"   👤 Customer: {processed_data.get('customer_full_name', 'Unknown')}")
    logger.info(f"   📧 Email: {processed_data.get('customer_email_address', 'Unknown')}")
    logger.info(f"   🆔 Customer ID: {processed_data.get('customer_id', 'Unknown')}")
    
    # Connect to Neo4j and insert
    try:
        driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
        )
        
        # Check if customer already exists
        with driver.session() as session:
            check_query = "MATCH (c:Customer {customer_id: $customer_id}) RETURN c.customer_id as existing_id"
            check_result = session.run(check_query, customer_id=str(processed_data.get('customer_id')))
            existing = check_result.single()
            
            if existing:
                logger.warning(f"   ⚠️  Customer {processed_data.get('customer_id')} already exists!")
                logger.info("   🔄 Updating existing customer...")
                
                # Update existing customer
                # Build SET clauses for update
                set_clauses = []
                for prop_name, value in processed_data.items():
                    if value is not None:
                        set_clauses.append(f"c.{prop_name} = ${prop_name}")
                
                update_query = f"""
                MATCH (c:Customer {{customer_id: $customer_id}})
                SET {', '.join(set_clauses)}, c.updated_at = datetime()
                RETURN c.customer_id as updated_id
                """
                
                result = session.run(update_query, **processed_data)
                record = result.single()
                
                if record:
                    logger.info(f"   ✅ Updated customer {record['updated_id']}")
                else:
                    logger.error("   ❌ Failed to update customer")
            else:
                # Create new customer
                # Build property assignments for CREATE
                property_assignments = []
                for prop_name, value in processed_data.items():
                    if value is not None:
                        property_assignments.append(f"{prop_name}: ${prop_name}")
                
                create_query = f"""
                CREATE (c:Customer {{
                    {', '.join(property_assignments)},
                    created_at: datetime()
                }})
                RETURN c.customer_id as created_id
                """
                
                result = session.run(create_query, **processed_data)
                record = result.single()
                
                if record:
                    logger.info(f"   ✅ Created new customer {record['created_id']}")
                else:
                    logger.error("   ❌ Failed to create customer")
        
        driver.close()
        logger.info("🎉 Customer addition process completed!")
        
    except Exception as e:
        logger.error(f"❌ Failed to add customer: {e}")
        raise


if __name__ == "__main__":
    add_emily_customer()
