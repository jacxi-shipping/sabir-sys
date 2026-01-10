"""
Global Search Manager for Egg Farm Management System
"""
import logging
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from egg_farm_system.config import DATA_DIR
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import (
    Farm, Shed, Flock, EggProduction, Party, Sale, Purchase, Expense,
    RawMaterial, FinishedFeed
)

logger = logging.getLogger(__name__)


class GlobalSearchManager:
    """Manages global search across all modules"""
    
    def __init__(self):
        self.session = DatabaseManager.get_session()
        self.history_file = DATA_DIR / "search_history.json"
    
    def search(self, query: str, modules: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search across all or specified modules
        
        Args:
            query: Search query string
            modules: List of module names to search (None = all modules)
            
        Returns:
            Dictionary mapping module names to search results
        """
        if not query or len(query.strip()) < 2:
            return {}
        
        # Save search query to history
        self.save_search(query)
        
        query_lower = query.lower().strip()
        results = {}
        
        # Define which modules to search
        search_modules = modules if modules else [
            'farms', 'sheds', 'flocks', 'parties', 'sales', 'purchases',
            'expenses', 'productions', 'materials', 'feeds'
        ]
        
        try:
            if 'farms' in search_modules:
                results['farms'] = self._search_farms(query_lower)
            
            if 'sheds' in search_modules:
                results['sheds'] = self._search_sheds(query_lower)
            
            if 'flocks' in search_modules:
                results['flocks'] = self._search_flocks(query_lower)
            
            if 'parties' in search_modules:
                results['parties'] = self._search_parties(query_lower)
            
            if 'sales' in search_modules:
                results['sales'] = self._search_sales(query_lower)
            
            if 'purchases' in search_modules:
                results['purchases'] = self._search_purchases(query_lower)
            
            if 'expenses' in search_modules:
                results['expenses'] = self._search_expenses(query_lower)
            
            if 'productions' in search_modules:
                results['productions'] = self._search_productions(query_lower)
            
            if 'materials' in search_modules:
                results['materials'] = self._search_materials(query_lower)
            
            if 'feeds' in search_modules:
                results['feeds'] = self._search_feeds(query_lower)
        
        except Exception as e:
            logger.error(f"Error in global search: {e}")
        
        return results
    
    def _search_farms(self, query: str) -> List[Dict[str, Any]]:
        """Search farms"""
        farms = self.session.query(Farm).filter(
            Farm.name.ilike(f"%{query}%")
        ).limit(20).all()
        
        return [{
            'id': f.id,
            'type': 'farm',
            'title': f.name,
            'subtitle': f.location or '',
            'data': f
        } for f in farms]
    
    def _search_sheds(self, query: str) -> List[Dict[str, Any]]:
        """Search sheds"""
        sheds = self.session.query(Shed).join(Farm).filter(
            Shed.name.ilike(f"%{query}%") | Farm.name.ilike(f"%{query}%")
        ).limit(20).all()
        
        return [{
            'id': s.id,
            'type': 'shed',
            'title': s.name,
            'subtitle': f"Farm: {s.farm.name}",
            'data': s
        } for s in sheds]
    
    def _search_flocks(self, query: str) -> List[Dict[str, Any]]:
        """Search flocks"""
        flocks = self.session.query(Flock).join(Shed).join(Farm).filter(
            Flock.name.ilike(f"%{query}%")
        ).limit(20).all()
        
        return [{
            'id': f.id,
            'type': 'flock',
            'title': f.name,
            'subtitle': f"Shed: {f.shed.name}, Farm: {f.shed.farm.name}",
            'data': f
        } for f in flocks]
    
    def _search_parties(self, query: str) -> List[Dict[str, Any]]:
        """Search parties"""
        parties = self.session.query(Party).filter(
            Party.name.ilike(f"%{query}%") |
            (Party.phone.isnot(None) & Party.phone.ilike(f"%{query}%"))
        ).limit(20).all()
        
        return [{
            'id': p.id,
            'type': 'party',
            'title': p.name,
            'subtitle': p.phone or p.address or '',
            'data': p
        } for p in parties]
    
    def _search_sales(self, query: str) -> List[Dict[str, Any]]:
        """Search sales"""
        sales = self.session.query(Sale).join(Party).filter(
            Party.name.ilike(f"%{query}%") |
            Sale.notes.ilike(f"%{query}%")
        ).order_by(Sale.date.desc()).limit(20).all()
        
        return [{
            'id': s.id,
            'type': 'sale',
            'title': f"Sale to {s.party.name}",
            'subtitle': f"{s.quantity} eggs on {s.date.strftime('%Y-%m-%d')}",
            'data': s
        } for s in sales]
    
    def _search_purchases(self, query: str) -> List[Dict[str, Any]]:
        """Search purchases"""
        from egg_farm_system.database.models import RawMaterial
        purchases = self.session.query(Purchase).join(Party).join(RawMaterial).filter(
            Party.name.ilike(f"%{query}%") |
            RawMaterial.name.ilike(f"%{query}%") |
            (Purchase.notes.isnot(None) & Purchase.notes.ilike(f"%{query}%"))
        ).order_by(Purchase.date.desc()).limit(20).all()
        
        return [{
            'id': p.id,
            'type': 'purchase',
            'title': f"Purchase: {p.material.name if p.material else 'Unknown'}",
            'subtitle': f"From {p.party.name} on {p.date.strftime('%Y-%m-%d')}",
            'data': p
        } for p in purchases]
    
    def _search_expenses(self, query: str) -> List[Dict[str, Any]]:
        """Search expenses"""
        expenses = self.session.query(Expense).filter(
            Expense.category.ilike(f"%{query}%") |
            Expense.notes.ilike(f"%{query}%")
        ).order_by(Expense.date.desc()).limit(20).all()
        
        return [{
            'id': e.id,
            'type': 'expense',
            'title': f"{e.category}: {e.amount_afg:.0f} AFG",
            'subtitle': f"Date: {e.date.strftime('%Y-%m-%d')}",
            'data': e
        } for e in expenses]
    
    def _search_productions(self, query: str) -> List[Dict[str, Any]]:
        """Search egg productions"""
        # Search by date or shed name
        productions = self.session.query(EggProduction).join(Shed).join(Farm).filter(
            Shed.name.ilike(f"%{query}%") |
            Farm.name.ilike(f"%{query}%")
        ).order_by(EggProduction.date.desc()).limit(20).all()
        
        return [{
            'id': p.id,
            'type': 'production',
            'title': f"Production: {p.shed.name}",
            'subtitle': f"{p.small_count + p.medium_count + p.large_count} eggs on {p.date.strftime('%Y-%m-%d')}",
            'data': p
        } for p in productions]
    
    def _search_materials(self, query: str) -> List[Dict[str, Any]]:
        """Search raw materials"""
        materials = self.session.query(RawMaterial).filter(
            RawMaterial.name.ilike(f"%{query}%")
        ).limit(20).all()
        
        return [{
            'id': m.id,
            'type': 'material',
            'title': m.name,
            'subtitle': f"Stock: {m.current_stock:.2f} {m.unit}",
            'data': m
        } for m in materials]
    
    def _search_feeds(self, query: str) -> List[Dict[str, Any]]:
        """Search finished feeds"""
        feeds = self.session.query(FinishedFeed).filter(
            FinishedFeed.feed_type.ilike(f"%{query}%")
        ).limit(20).all()
        
        return [{
            'id': f.id,
            'type': 'feed',
            'title': f.feed_type.value,
            'subtitle': f"Stock: {f.current_stock:.2f} kg",
            'data': f
        } for f in feeds]
    
    def get_search_history(self, limit: int = 10) -> List[str]:
        """Get recent search history"""
        try:
            if not self.history_file.exists():
                return []
            
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
                return history[:limit]
        except Exception as e:
            logger.error(f"Error reading search history: {e}")
            return []
    
    def save_search(self, query: str):
        """Save search to history"""
        if not query or len(query.strip()) < 2:
            return
            
        try:
            query = query.strip()
            history = self.get_search_history(limit=50) # Get more to filter
            
            # Remove if exists (to move to top)
            if query in history:
                history.remove(query)
            
            # Add to top
            history.insert(0, query)
            
            # Keep max 50
            history = history[:50]
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error saving search history: {e}")
    
    def close(self):
        """Close database session"""
        if self.session:
            self.session.close()

