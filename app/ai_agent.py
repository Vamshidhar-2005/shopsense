"""
Milestone 4 Advanced Feature: Autonomous AI Strategic Agent Workflow.
Analyzes vendor store catalog inventory, sales velocity, customer spend tiers,
and generates proactive strategic advice for vendors.
"""
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from app import models, crud

class AutonomousStoreAgent:
    """Autonomous AI Agent that performs periodic strategic audits on vendor stores."""

    def __init__(self, vendor_id: int):
        self.vendor_id = vendor_id

    def execute_store_audit(self, db: Session) -> Dict[str, Any]:
        """Runs automated strategic audit and returns prioritized action items."""
        products = db.query(models.Product).filter(models.Product.vendor_id == self.vendor_id).all()
        orders = db.query(models.Order).filter(models.Order.vendor_id == self.vendor_id).all()
        customers_data = crud.get_customer_segmentation_analytics(db, self.vendor_id)

        action_items = []
        insights = []

        # 1. Stockout & Low Stock Alert Analysis
        out_of_stock = [p for p in products if p.stock == 0]
        low_stock = [p for p in products if 0 < p.stock < 5]
        high_stock = [p for p in products if p.stock > 50]

        if out_of_stock:
          for p in out_of_stock:
              action_items.append({
                  "severity": "CRITICAL",
                  "category": "INVENTORY_STOCKOUT",
                  "title": f"Restock Required: {p.name}",
                  "recommendation": f"Product '{p.name}' is completely out of stock (0 units). Restock at least 15 units to prevent lost customer orders.",
                  "impact_score": 95
              })

        if low_stock:
          for p in low_stock:
              action_items.append({
                  "severity": "HIGH",
                  "category": "LOW_STOCK_WARNING",
                  "title": f"Low Stock Warning: {p.name}",
                  "recommendation": f"Product '{p.name}' only has {p.stock} units remaining. Reorder suggested within 48 hours.",
                  "impact_score": 80
              })

        # 2. Overstock & Pricing Optimization Analysis
        if high_stock:
          for p in high_stock:
              suggested_discount = 15
              action_items.append({
                  "severity": "MEDIUM",
                  "category": "PRICE_PROMOTION",
                  "title": f"Promotion Opportunity: {p.name}",
                  "recommendation": f"High inventory level detected ({p.stock} units). Consider creating a {suggested_discount}% promotional discount to accelerate inventory turnover.",
                  "impact_score": 75
              })

        # 3. Customer VIP Engagement Opportunities
        vip_customers = [c for c in customers_data.get("customer_segments", []) if "VIP" in c.get("tier", "")]
        if vip_customers:
            insights.append(
                f"👑 VIP Customer Retention: You have {len(vip_customers)} VIP customers ({', '.join([c['name'] for c in vip_customers])}). Recommend sending exclusive discount codes."
            )
        else:
            insights.append("💡 Customer Loyalty: Offer bundle discounts to convert Regular buyers into VIP spenders.")

        # 4. Overall Strategic Summary
        total_valuation = sum(float(p.price) * p.stock for p in products)
        total_orders = len(orders)
        health_score = 100 - (len(out_of_stock) * 15) - (len(low_stock) * 5)
        health_score = max(min(health_score, 100), 40)

        return {
            "vendor_id": self.vendor_id,
            "agent_name": "Autonomous ShopSense Strategic AI Agent",
            "health_score": health_score,
            "total_inventory_valuation": round(total_valuation, 2),
            "total_active_listings": len(products),
            "total_orders_analyzed": total_orders,
            "action_items_count": len(action_items),
            "action_items": sorted(action_items, key=lambda x: x["impact_score"], reverse=True),
            "strategic_insights": insights,
            "executive_advice": f"Store operational health is rated at {health_score}/100. Priority focus should be addressing {len(out_of_stock)} out-of-stock items and running promotions on high-stock listings."
        }

def run_vendor_autonomous_audit(db: Session, vendor_id: int = 1) -> Dict[str, Any]:
    agent = AutonomousStoreAgent(vendor_id=vendor_id)
    return agent.execute_store_audit(db)
