#!/usr/bin/env python3
"""
Improved Order Processing Script for Matt (Customer ID: 6180005)

This script creates an improved Neo4j graph structure:
Customer → HIS_PRODUCTS → [His Products Hub] → HAS_CATEGORY → Category Products → BOUGHT → Order

The "His Products" node acts as a central hub for all of Matt's product categories.
"""

import os
import json
import csv
import logging
from typing import Dict, List, Set, Any
from datetime import datetime
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
CUSTOMER_ID = "6180005"  # Matt's customer ID
CSV_FILE = "data_orders/order_cust_id_ 6180005.csv"

class ImprovedMattOrderProcessor:
    """Processes Matt's orders and creates the improved Neo4j graph structure"""
    
    def __init__(self):
        """Initialize the order processor"""
        self.customer_id = CUSTOMER_ID
        self.csv_file = CSV_FILE
        self.neo4j_driver = self._initialize_neo4j()
        self.categories_found = set()
        self.orders_processed = 0
        
    def _initialize_neo4j(self):
        """Initialize Neo4j connection"""
        return GraphDatabase.driver(
            os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
            auth=(
                os.getenv('NEO4J_USERNAME', 'neo4j'),
                os.getenv('NEO4J_PASSWORD', 'password')
            )
        )
    
    def parse_category_list(self, category_str: str) -> List[str]:
        """Parse the CATEGORY_LEVEL1_LIST JSON string into a list of categories"""
        try:
            if not category_str or category_str.strip() == '':
                return []
            
            categories = json.loads(category_str)
            if isinstance(categories, list):
                return [str(cat).strip() for cat in categories if cat and str(cat).strip()]
            else:
                return [str(categories).strip()] if categories else []
                
        except json.JSONDecodeError:
            # If not valid JSON, try to handle as string
            logger.warning(f"Could not parse categories as JSON: {category_str}")
            return [category_str.strip()] if category_str.strip() else []
    
    def clear_existing_order_data(self):
        """Clear existing order-related data for this customer"""
        query = """
        MATCH (c:Customer {customer_id: $customer_id})-[:HIS_PRODUCTS]->(hp:HisProducts)
        OPTIONAL MATCH (hp)-[:HAS_CATEGORY]->(cp:CategoryProducts)
        OPTIONAL MATCH (cp)-[:BOUGHT]->(o:Order)
        DETACH DELETE hp, cp, o
        """
        
        with self.neo4j_driver.session() as session:
            session.run(query, customer_id=self.customer_id)
            logger.info("🧹 Cleared existing order data")
    
    def create_his_products_hub(self):
        """Create the central 'His Products' hub node"""
        logger.info("🏢 Creating central 'His Products' hub...")
        
        query = """
        MATCH (c:Customer {customer_id: $customer_id})
        
        CREATE (hp:HisProducts {
            customer_id: $customer_id,
            name: "His Products",
            description: "Central hub for all product categories",
            created_at: datetime(),
            total_categories: 0,
            total_orders: 0,
            total_spent: 0.0
        })
        
        CREATE (c)-[:HIS_PRODUCTS]->(hp)
        
        RETURN hp.name as created_hub
        """
        
        with self.neo4j_driver.session() as session:
            result = session.run(query, customer_id=self.customer_id)
            record = result.single()
            if record:
                logger.info(f"   ✅ Created: {record['created_hub']} hub")
    
    def create_category_products_nodes(self, categories: Set[str]):
        """Create CategoryProducts nodes for each unique category under the His Products hub"""
        logger.info(f"🏷️ Creating {len(categories)} category product nodes...")
        
        for category in categories:
            # Sanitize category name for node creation
            category_name = category.replace(" ", "_").replace("/", "_").replace("&", "and")
            
            query = """
            MATCH (hp:HisProducts {customer_id: $customer_id})
            
            CREATE (cp:CategoryProducts {
                customer_id: $customer_id,
                category: $category,
                category_name: $category_name,
                display_name: $category + " Products",
                created_at: datetime(),
                product_count: 0,
                total_orders: 0,
                total_spent: 0.0
            })
            
            CREATE (hp)-[:HAS_CATEGORY]->(cp)
            
            RETURN cp.display_name as created_category
            """
            
            with self.neo4j_driver.session() as session:
                result = session.run(query, {
                    'customer_id': self.customer_id,
                    'category': category,
                    'category_name': category_name
                })
                record = result.single()
                if record:
                    logger.info(f"   ✅ Created: {record['created_category']}")
    
    def create_order_node(self, order_data: Dict[str, Any]) -> str:
        """Create an Order node with all order details"""
        
        # Convert date strings to Neo4j datetime format
        def parse_date(date_str):
            if date_str and str(date_str).strip() and str(date_str) != 'nan':
                try:
                    return datetime.strptime(str(date_str), '%Y-%m-%d').isoformat()
                except:
                    return None
            return None
        
        # Helper function to safely convert to float
        def safe_float(value):
            try:
                return float(value) if value and str(value) != 'nan' else 0.0
            except:
                return 0.0
        
        # Helper function to safely convert to int
        def safe_int(value):
            try:
                return int(float(value)) if value and str(value) != 'nan' else 0
            except:
                return 0
        
        # Helper function to safely convert to bool
        def safe_bool(value):
            try:
                return bool(int(float(value))) if value and str(value) not in ['nan', ''] else False
            except:
                return False
        
        # Prepare order data with proper type conversion
        order_params = {
            'order_id': str(order_data.get('ORDER_ID', '')),
            'customer_id': self.customer_id,
            'order_date_est': parse_date(order_data.get('ORDER_DATE_EST')),
            'business_channel': str(order_data.get('BUSINESS_CHANNEL', '')),
            'shipped_flag': safe_bool(order_data.get('SHIPPED_FLAG')),
            'ship_date_est': parse_date(order_data.get('SHIP_DATE_EST')),
            'order_items': safe_int(order_data.get('ORDER_ITEMS')),
            'units_sold': safe_int(order_data.get('UNITS_SOLD')),
            'net_sales': safe_float(order_data.get('NET_SALES')),
            'gross_sales': safe_float(order_data.get('GROSS_SALES')),
            'discounts': safe_float(order_data.get('DISCOUNTS')),
            'gross_profit': safe_float(order_data.get('GROSS_PROFIT')),
            'contribution_profit': safe_float(order_data.get('CONTRIBUTION_PROFIT')),
            'order_rank': safe_int(order_data.get('ORDER_RANK')),
            'first_order': safe_bool(order_data.get('FIRST_ORDER')),
            'first_autoship_order': safe_bool(order_data.get('FIRST_AUTOSHIP_ORDER')),
            'channel': str(order_data.get('CHANNEL', '')),
            'campaign': str(order_data.get('CAMPAIGN', '')),
            'network': str(order_data.get('NETWORK', '')),
            'sku_list': str(order_data.get('SKU_LIST', '')),
            'mc1_list': str(order_data.get('MC1_LIST', '')),
            'brand_list': str(order_data.get('BRAND_LIST', '')),
            'category_level1_list': str(order_data.get('CATEGORY_LEVEL1_LIST', '')),
            'pet_type': str(order_data.get('PET_TYPE', '')),
            'has_consumables': safe_bool(order_data.get('HAS_CONSUMABLES')),
            'has_hardgoods': safe_bool(order_data.get('HAS_HARDGOODS')),
            'has_healthcare': safe_bool(order_data.get('HAS_HEALTHCARE')),
            'has_food': safe_bool(order_data.get('HAS_FOOD')),
            'net_sales_consumables': safe_float(order_data.get('NET_SALES_CONSUMABLES')),
            'net_sales_hardgoods': safe_float(order_data.get('NET_SALES_HARDGOODS')),
            'net_sales_healthcare': safe_float(order_data.get('NET_SALES_HEALTHCARE')),
            'net_sales_food': safe_float(order_data.get('NET_SALES_FOOD')),
            'created_at': datetime.now().isoformat()
        }
        
        query = """
        CREATE (o:Order {
            order_id: $order_id,
            customer_id: $customer_id,
            order_date_est: datetime($order_date_est),
            business_channel: $business_channel,
            shipped_flag: $shipped_flag,
            ship_date_est: datetime($ship_date_est),
            order_items: $order_items,
            units_sold: $units_sold,
            net_sales: $net_sales,
            gross_sales: $gross_sales,
            discounts: $discounts,
            gross_profit: $gross_profit,
            contribution_profit: $contribution_profit,
            order_rank: $order_rank,
            first_order: $first_order,
            first_autoship_order: $first_autoship_order,
            channel: $channel,
            campaign: $campaign,
            network: $network,
            sku_list: $sku_list,
            mc1_list: $mc1_list,
            brand_list: $brand_list,
            category_level1_list: $category_level1_list,
            pet_type: $pet_type,
            has_consumables: $has_consumables,
            has_hardgoods: $has_hardgoods,
            has_healthcare: $has_healthcare,
            has_food: $has_food,
            net_sales_consumables: $net_sales_consumables,
            net_sales_hardgoods: $net_sales_hardgoods,
            net_sales_healthcare: $net_sales_healthcare,
            net_sales_food: $net_sales_food,
            created_at: datetime($created_at)
        })
        RETURN o.order_id as created_order
        """
        
        with self.neo4j_driver.session() as session:
            result = session.run(query, order_params)
            record = result.single()
            return record['created_order'] if record else None
    
    def link_order_to_categories(self, order_id: str, categories: List[str], net_sales: float):
        """Link an order to its appropriate category product nodes"""
        for category in categories:
            query = """
            MATCH (cp:CategoryProducts {customer_id: $customer_id, category: $category})
            MATCH (o:Order {order_id: $order_id})
            
            MERGE (cp)-[:BOUGHT]->(o)
            
            // Update category product statistics
            SET cp.product_count = cp.product_count + 1,
                cp.total_orders = cp.total_orders + 1,
                cp.total_spent = cp.total_spent + $net_sales
            
            RETURN cp.category as linked_category, o.order_id as linked_order
            """
            
            with self.neo4j_driver.session() as session:
                result = session.run(query, {
                    'customer_id': self.customer_id,
                    'category': category,
                    'order_id': order_id,
                    'net_sales': net_sales
                })
                record = result.single()
                if record:
                    logger.debug(f"   🔗 Linked {category} -> Order {order_id}")
    
    def update_his_products_statistics(self, total_categories: int, total_orders: int, total_spent: float):
        """Update the His Products hub with summary statistics"""
        query = """
        MATCH (hp:HisProducts {customer_id: $customer_id})
        SET hp.total_categories = $total_categories,
            hp.total_orders = $total_orders,
            hp.total_spent = $total_spent,
            hp.updated_at = datetime()
        RETURN hp.name as updated_hub
        """
        
        with self.neo4j_driver.session() as session:
            result = session.run(query, {
                'customer_id': self.customer_id,
                'total_categories': total_categories,
                'total_orders': total_orders,
                'total_spent': total_spent
            })
            record = result.single()
            if record:
                logger.info(f"   📊 Updated {record['updated_hub']} statistics")
    
    def process_orders(self):
        """Main method to process all orders with improved structure"""
        logger.info("🚀 Starting Matt's Improved Order Processing")
        logger.info("=" * 55)
        logger.info(f"   👤 Customer ID: {self.customer_id}")
        logger.info(f"   📄 CSV File: {self.csv_file}")
        logger.info("   🏗️ Structure: Customer → HIS_PRODUCTS → His Products Hub → HAS_CATEGORY → Category Products → BOUGHT → Orders")
        
        # Step 1: Read CSV and collect all categories
        logger.info("📊 Step 1: Reading CSV and collecting categories...")
        
        orders_data = []
        all_categories = set()
        
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    # Parse categories for this order
                    categories = self.parse_category_list(row.get('CATEGORY_LEVEL1_LIST', ''))
                    
                    if categories:  # Only process orders with categories
                        orders_data.append({
                            'row_data': row,
                            'categories': categories
                        })
                        all_categories.update(categories)
                        
                        if len(orders_data) <= 5:  # Log first few orders
                            logger.info(f"   🛍️ Order {row.get('ORDER_ID')}: {categories}")
            
            logger.info(f"✅ Found {len(orders_data)} orders with {len(all_categories)} unique categories")
            logger.info(f"   Categories: {sorted(all_categories)}")
            
        except Exception as e:
            logger.error(f"❌ Failed to read CSV: {e}")
            return
        
        # Step 2: Clear existing data
        logger.info("🗑️ Step 2: Clearing existing order data...")
        self.clear_existing_order_data()
        
        # Step 3: Create the central His Products hub
        logger.info("🏢 Step 3: Creating His Products hub...")
        self.create_his_products_hub()
        
        # Step 4: Create category product nodes
        logger.info("🏷️ Step 4: Creating category product nodes...")
        self.create_category_products_nodes(all_categories)
        
        # Step 5: Process each order
        logger.info(f"📦 Step 5: Processing {len(orders_data)} orders...")
        
        success_count = 0
        failure_count = 0
        total_spent = 0.0
        
        for i, order_info in enumerate(orders_data, 1):
            try:
                row_data = order_info['row_data']
                categories = order_info['categories']
                order_id = row_data.get('ORDER_ID')
                net_sales = float(row_data.get('NET_SALES', 0.0)) if row_data.get('NET_SALES') else 0.0
                
                # Create order node
                created_order = self.create_order_node(row_data)
                
                if created_order:
                    # Link to category products
                    self.link_order_to_categories(order_id, categories, net_sales)
                    success_count += 1
                    total_spent += net_sales
                    
                    # Progress logging
                    if i % 50 == 0:
                        logger.info(f"   📊 Progress: {i}/{len(orders_data)} | ✅ Success: {success_count} | ❌ Failed: {failure_count}")
                else:
                    failure_count += 1
                    logger.warning(f"   ❌ Failed to create order: {order_id}")
                    
            except Exception as e:
                failure_count += 1
                logger.error(f"   ❌ Error processing order {i}: {e}")
        
        # Step 6: Update His Products hub statistics
        logger.info("📊 Step 6: Updating His Products hub statistics...")
        self.update_his_products_statistics(len(all_categories), success_count, total_spent)
        
        # Final summary
        logger.info("🎉 Improved Order Processing Complete!")
        logger.info("=" * 55)
        logger.info(f"📊 FINAL SUMMARY:")
        logger.info(f"   ✅ Orders processed successfully: {success_count}")
        logger.info(f"   ❌ Orders failed: {failure_count}")
        logger.info(f"   🏷️ Categories created: {len(all_categories)}")
        logger.info(f"   💰 Total spent: ${total_spent:.2f}")
        logger.info(f"   📈 Success rate: {success_count/len(orders_data)*100:.1f}%")
        logger.info("=" * 55)
        
        self.categories_found = all_categories
        self.orders_processed = success_count
    
    def verify_improved_graph_structure(self):
        """Verify the improved graph structure"""
        logger.info("🔍 Verifying improved graph structure...")
        
        # Check the full path structure
        query = """
        MATCH path = (c:Customer {customer_id: $customer_id})-[:HIS_PRODUCTS]->(hp:HisProducts)-[:HAS_CATEGORY]->(cp:CategoryProducts)-[:BOUGHT]->(o:Order)
        RETURN c.customer_id as customer,
               hp.name as hub_name,
               hp.total_categories as hub_categories,
               hp.total_orders as hub_orders,
               hp.total_spent as hub_spent,
               cp.category as category,
               count(o) as order_count,
               sum(o.net_sales) as total_sales
        ORDER BY category
        """
        
        with self.neo4j_driver.session() as session:
            result = session.run(query, customer_id=self.customer_id)
            
            print("📋 Improved Graph Structure Verification:")
            print(f"   🏗️ Customer → HIS_PRODUCTS → His Products Hub → HAS_CATEGORY → Category Products → BOUGHT → Orders")
            print()
            
            total_orders = 0
            total_sales = 0.0
            hub_info_shown = False
            
            for record in result:
                if not hub_info_shown:
                    print(f"   🏢 Hub: {record['hub_name']}")
                    print(f"      📊 Total Categories: {record['hub_categories']}")
                    print(f"      📦 Total Orders: {record['hub_orders']}")
                    print(f"      💰 Total Spent: ${record['hub_spent']:.2f}")
                    print()
                    hub_info_shown = True
                
                order_count = record['order_count']
                sales = record['total_sales'] or 0.0
                total_orders += order_count
                total_sales += sales
                
                print(f"   🏷️ {record['category']} Products: {order_count} orders, ${sales:.2f}")
            
            print(f"\n   📊 Verification Total: {total_orders} orders, ${total_sales:.2f}")
    
    def close(self):
        """Close Neo4j connection"""
        if self.neo4j_driver:
            self.neo4j_driver.close()

def main():
    """Main execution function"""
    processor = ImprovedMattOrderProcessor()
    
    try:
        processor.process_orders()
        processor.verify_improved_graph_structure()
        
    except Exception as e:
        logger.error(f"❌ Processing failed: {e}")
        raise
    finally:
        processor.close()

if __name__ == "__main__":
    main() 