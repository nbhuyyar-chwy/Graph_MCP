#!/usr/bin/env python3
"""
Order Processing Script for Matt (Customer ID: 6180005)

This script processes Matt's order data and creates a Neo4j graph structure:
Customer -> HIS_PRODUCTS -> Category Products (Dog Products, Cat Products, etc.) -> BOUGHT -> Order

The script uses the CATEGORY_LEVEL1_LIST column to determine which category product nodes
each order should be connected to.
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
CSV_FILE = "data/orders/order_cust_id_ 6180005.csv"

class MattOrderProcessor:
    """Processes Matt's orders and creates the Neo4j graph structure"""
    
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
        MATCH (c:Customer {customer_id: $customer_id})-[:HIS_PRODUCTS]->(cp:CategoryProducts)
        OPTIONAL MATCH (cp)-[:BOUGHT]->(o:Order)
        DETACH DELETE cp, o
        """
        
        with self.neo4j_driver.session() as session:
            session.run(query, customer_id=self.customer_id)
            logger.info("🧹 Cleared existing order data")
    
    def create_category_products_nodes(self, categories: Set[str]):
        """Create CategoryProducts nodes for each unique category"""
        logger.info(f"🏷️ Creating {len(categories)} category product nodes...")
        
        for category in categories:
            # Sanitize category name for node creation
            category_name = category.replace(" ", "_").replace("/", "_")
            
            query = """
            MATCH (c:Customer {customer_id: $customer_id})
            
            MERGE (cp:CategoryProducts {
                customer_id: $customer_id,
                category: $category,
                category_name: $category_name
            })
            ON CREATE SET 
                cp.created_at = datetime(),
                cp.product_count = 0
            
            MERGE (c)-[:HIS_PRODUCTS]->(cp)
            
            RETURN cp.category as created_category
            """
            
            with self.neo4j_driver.session() as session:
                result = session.run(query, {
                    'customer_id': self.customer_id,
                    'category': category,
                    'category_name': category_name
                })
                record = result.single()
                if record:
                    logger.info(f"   ✅ Created: {record['created_category']} Products")
    
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
        
        # Prepare order data with proper type conversion
        order_params = {
            'order_id': str(order_data.get('ORDER_ID', '')),
            'customer_id': self.customer_id,
            'order_date_est': parse_date(order_data.get('ORDER_DATE_EST')),
            'business_channel': str(order_data.get('BUSINESS_CHANNEL', '')),
            'shipped_flag': bool(order_data.get('SHIPPED_FLAG', False)),
            'ship_date_est': parse_date(order_data.get('SHIP_DATE_EST')),
            'order_items': int(order_data.get('ORDER_ITEMS', 0)) if order_data.get('ORDER_ITEMS') else 0,
            'units_sold': int(order_data.get('UNITS_SOLD', 0)) if order_data.get('UNITS_SOLD') else 0,
            'net_sales': float(order_data.get('NET_SALES', 0.0)) if order_data.get('NET_SALES') else 0.0,
            'gross_sales': float(order_data.get('GROSS_SALES', 0.0)) if order_data.get('GROSS_SALES') else 0.0,
            'discounts': float(order_data.get('DISCOUNTS', 0.0)) if order_data.get('DISCOUNTS') else 0.0,
            'gross_profit': float(order_data.get('GROSS_PROFIT', 0.0)) if order_data.get('GROSS_PROFIT') else 0.0,
            'contribution_profit': float(order_data.get('CONTRIBUTION_PROFIT', 0.0)) if order_data.get('CONTRIBUTION_PROFIT') else 0.0,
            'order_rank': int(order_data.get('ORDER_RANK', 0)) if order_data.get('ORDER_RANK') else 0,
            'first_order': bool(order_data.get('FIRST_ORDER', False)),
            'first_autoship_order': bool(order_data.get('FIRST_AUTOSHIP_ORDER', False)),
            'channel': str(order_data.get('CHANNEL', '')),
            'campaign': str(order_data.get('CAMPAIGN', '')),
            'network': str(order_data.get('NETWORK', '')),
            'sku_list': str(order_data.get('SKU_LIST', '')),
            'mc1_list': str(order_data.get('MC1_LIST', '')),
            'brand_list': str(order_data.get('BRAND_LIST', '')),
            'category_level1_list': str(order_data.get('CATEGORY_LEVEL1_LIST', '')),
            'pet_type': str(order_data.get('PET_TYPE', '')),
            'has_consumables': bool(order_data.get('HAS_CONSUMABLES', False)),
            'has_hardgoods': bool(order_data.get('HAS_HARDGOODS', False)),
            'has_healthcare': bool(order_data.get('HAS_HEALTHCARE', False)),
            'has_food': bool(order_data.get('HAS_FOOD', False)),
            'net_sales_consumables': float(order_data.get('NET_SALES_CONSUMABLES', 0.0)) if order_data.get('NET_SALES_CONSUMABLES') else 0.0,
            'net_sales_hardgoods': float(order_data.get('NET_SALES_HARDGOODS', 0.0)) if order_data.get('NET_SALES_HARDGOODS') else 0.0,
            'net_sales_healthcare': float(order_data.get('NET_SALES_HEALTHCARE', 0.0)) if order_data.get('NET_SALES_HEALTHCARE') else 0.0,
            'net_sales_food': float(order_data.get('NET_SALES_FOOD', 0.0)) if order_data.get('NET_SALES_FOOD') else 0.0,
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
    
    def link_order_to_categories(self, order_id: str, categories: List[str]):
        """Link an order to its appropriate category product nodes"""
        for category in categories:
            query = """
            MATCH (cp:CategoryProducts {customer_id: $customer_id, category: $category})
            MATCH (o:Order {order_id: $order_id})
            
            MERGE (cp)-[:BOUGHT]->(o)
            
            // Update product count
            SET cp.product_count = cp.product_count + 1
            
            RETURN cp.category as linked_category, o.order_id as linked_order
            """
            
            with self.neo4j_driver.session() as session:
                result = session.run(query, {
                    'customer_id': self.customer_id,
                    'category': category,
                    'order_id': order_id
                })
                record = result.single()
                if record:
                    logger.debug(f"   🔗 Linked {category} -> Order {order_id}")
    
    def process_orders(self):
        """Main method to process all orders"""
        logger.info("🚀 Starting Matt's Order Processing")
        logger.info("=" * 50)
        logger.info(f"   👤 Customer ID: {self.customer_id}")
        logger.info(f"   📄 CSV File: {self.csv_file}")
        
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
        
        # Step 3: Create category product nodes
        logger.info("🏷️ Step 3: Creating category product nodes...")
        self.create_category_products_nodes(all_categories)
        
        # Step 4: Process each order
        logger.info(f"📦 Step 4: Processing {len(orders_data)} orders...")
        
        success_count = 0
        failure_count = 0
        
        for i, order_info in enumerate(orders_data, 1):
            try:
                row_data = order_info['row_data']
                categories = order_info['categories']
                order_id = row_data.get('ORDER_ID')
                
                # Create order node
                created_order = self.create_order_node(row_data)
                
                if created_order:
                    # Link to category products
                    self.link_order_to_categories(order_id, categories)
                    success_count += 1
                    
                    # Progress logging
                    if i % 50 == 0:
                        logger.info(f"   📊 Progress: {i}/{len(orders_data)} | ✅ Success: {success_count} | ❌ Failed: {failure_count}")
                else:
                    failure_count += 1
                    logger.warning(f"   ❌ Failed to create order: {order_id}")
                    
            except Exception as e:
                failure_count += 1
                logger.error(f"   ❌ Error processing order {i}: {e}")
        
        # Final summary
        logger.info("🎉 Order Processing Complete!")
        logger.info("=" * 50)
        logger.info(f"📊 FINAL SUMMARY:")
        logger.info(f"   ✅ Orders processed successfully: {success_count}")
        logger.info(f"   ❌ Orders failed: {failure_count}")
        logger.info(f"   🏷️ Categories created: {len(all_categories)}")
        logger.info(f"   📈 Success rate: {success_count/len(orders_data)*100:.1f}%")
        logger.info("=" * 50)
        
        self.categories_found = all_categories
        self.orders_processed = success_count
    
    def verify_graph_structure(self):
        """Verify the created graph structure"""
        logger.info("🔍 Verifying graph structure...")
        
        query = """
        MATCH (c:Customer {customer_id: $customer_id})-[:HIS_PRODUCTS]->(cp:CategoryProducts)-[:BOUGHT]->(o:Order)
        RETURN c.customer_id as customer,
               cp.category as category,
               count(o) as order_count,
               sum(o.net_sales) as total_sales
        ORDER BY category
        """
        
        with self.neo4j_driver.session() as session:
            result = session.run(query, customer_id=self.customer_id)
            
            print("📋 Graph Structure Verification:")
            total_orders = 0
            total_sales = 0.0
            
            for record in result:
                order_count = record['order_count']
                sales = record['total_sales'] or 0.0
                total_orders += order_count
                total_sales += sales
                
                print(f"   🏷️ {record['category']} Products: {order_count} orders, ${sales:.2f}")
            
            print(f"   📊 Total: {total_orders} orders, ${total_sales:.2f}")
    
    def close(self):
        """Close Neo4j connection"""
        if self.neo4j_driver:
            self.neo4j_driver.close()

def main():
    """Main execution function"""
    processor = MattOrderProcessor()
    
    try:
        processor.process_orders()
        processor.verify_graph_structure()
        
    except Exception as e:
        logger.error(f"❌ Processing failed: {e}")
        raise
    finally:
        processor.close()

if __name__ == "__main__":
    main() 