"""
UI performance optimization utilities including lazy loading and pagination
"""
from egg_farm_system.utils.i18n import tr

import logging
from typing import List, Dict, Any, Callable, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PaginationHelper:
    """Helper class for paginating large datasets"""
    
    def __init__(self, total_items: int, page_size: int = 50):
        """
        Initialize pagination
        
        Args:
            total_items: Total number of items
            page_size: Items per page
        """
        self.total_items = total_items
        self.page_size = page_size
        self.current_page = 1
    
    @property
    def total_pages(self) -> int:
        """Get total number of pages"""
        return (self.total_items + self.page_size - 1) // self.page_size
    
    @property
    def has_next(self) -> bool:
        """Check if there's a next page"""
        return self.current_page < self.total_pages
    
    @property
    def has_previous(self) -> bool:
        """Check if there's a previous page"""
        return self.current_page > 1
    
    def get_page(self, page_num: int) -> tuple:
        """
        Get page bounds for slicing
        
        Returns:
            (start_index, end_index)
        """
        if page_num < 1 or page_num > self.total_pages:
            raise ValueError(f"Page {page_num} out of range (1-{self.total_pages})")
        
        self.current_page = page_num
        start = (page_num - 1) * self.page_size
        end = min(start + self.page_size, self.total_items)
        return start, end
    
    def next_page(self) -> Optional[tuple]:
        """Get next page bounds"""
        if self.has_next:
            return self.get_page(self.current_page + 1)
        return None
    
    def previous_page(self) -> Optional[tuple]:
        """Get previous page bounds"""
        if self.has_previous:
            return self.get_page(self.current_page - 1)
        return None
    
    def get_page_info(self) -> Dict[str, Any]:
        """Get pagination information"""
        start, end = self.get_page(self.current_page)
        return {
            'current_page': self.current_page,
            'total_pages': self.total_pages,
            'page_size': self.page_size,
            'total_items': self.total_items,
            'start_index': start,
            'end_index': end,
            'items_on_page': end - start,
            'has_next': self.has_next,
            'has_previous': self.has_previous
        }


class LazyDataLoader:
    """Lazy loader for table data"""
    
    def __init__(self, data_source: Callable, page_size: int = 50):
        """
        Initialize lazy loader
        
        Args:
            data_source: Callable that returns (total_count, items_for_page)
                        Signature: (page_num, page_size) -> (int, List)
            page_size: Items per page
        """
        self.data_source = data_source
        self.page_size = page_size
        self.total_count = 0
        self.pagination = None
        self._load_count()
    
    def _load_count(self):
        """Load total count"""
        try:
            # Call data source with page 1, page size 1 to get total count
            self.total_count, _ = self.data_source(1, 1)
            self.pagination = PaginationHelper(self.total_count, self.page_size)
        except Exception as e:
            logger.error(f"Error loading count: {e}")
            self.total_count = 0
            self.pagination = PaginationHelper(0, self.page_size)
    
    def load_page(self, page_num: int) -> List[Any]:
        """Load specific page"""
        try:
            _, items = self.data_source(page_num, self.page_size)
            return items
        except Exception as e:
            logger.error(f"Error loading page {page_num}: {e}")
            return []
    
    def get_page_info(self) -> Dict[str, Any]:
        """Get pagination info"""
        return self.pagination.get_page_info() if self.pagination else {}
    
    def load_all(self) -> List[Any]:
        """Load all items (use with caution for large datasets)"""
        all_items = []
        for page in range(1, self.pagination.total_pages + 1):
            items = self.load_page(page)
            all_items.extend(items)
        return all_items


class TableDataCache:
    """Cache for table data with pagination"""
    
    def __init__(self, page_size: int = 50, max_cached_pages: int = 5):
        """
        Initialize cache
        
        Args:
            page_size: Items per page
            max_cached_pages: Maximum pages to keep in memory
        """
        self.page_size = page_size
        self.max_cached_pages = max_cached_pages
        self.cache: Dict[int, List[Any]] = {}
        self.cache_timestamps: Dict[int, datetime] = {}
    
    def put(self, page_num: int, data: List[Any]):
        """Cache page data"""
        # Remove oldest page if cache is full
        if len(self.cache) >= self.max_cached_pages:
            oldest_page = min(self.cache_timestamps, key=self.cache_timestamps.get)
            del self.cache[oldest_page]
            del self.cache_timestamps[oldest_page]
        
        self.cache[page_num] = data
        self.cache_timestamps[page_num] = datetime.utcnow()
    
    def get(self, page_num: int) -> Optional[List[Any]]:
        """Get cached page data"""
        return self.cache.get(page_num)
    
    def has(self, page_num: int) -> bool:
        """Check if page is cached"""
        return page_num in self.cache
    
    def clear(self):
        """Clear cache"""
        self.cache.clear()
        self.cache_timestamps.clear()


class VirtualScrollingHelper:
    """Helper for virtual scrolling in large tables"""
    
    def __init__(self, item_height: int = 30, visible_items: int = 20):
        """
        Initialize virtual scrolling
        
        Args:
            item_height: Height of each item in pixels
            visible_items: Number of items visible at once
        """
        self.item_height = item_height
        self.visible_items = visible_items
        self.viewport_height = item_height * visible_items
        self.total_height = 0
        self.current_offset = 0
    
    def set_total_items(self, count: int):
        """Set total number of items"""
        self.total_height = count * self.item_height
    
    def get_visible_range(self, scroll_offset: int) -> tuple:
        """
        Get visible item range based on scroll offset
        
        Returns:
            (start_index, end_index)
        """
        self.current_offset = scroll_offset
        start_index = scroll_offset // self.item_height
        end_index = min(
            start_index + self.visible_items + 2,  # +2 for buffer
            self.total_height // self.item_height
        )
        return start_index, end_index
    
    def get_item_offset(self, item_index: int) -> int:
        """Get pixel offset for item"""
        return item_index * self.item_height


class IncrementalDataLoader:
    """Load data incrementally as user scrolls"""
    
    def __init__(self, data_source: Callable, initial_load: int = 50, increment: int = 25):
        """
        Initialize incremental loader
        
        Args:
            data_source: Callable that returns items
                        Signature: (offset, limit) -> List[items]
            initial_load: Initial items to load
            increment: Items to load on each scroll
        """
        self.data_source = data_source
        self.initial_load = initial_load
        self.increment = increment
        self.loaded_items: List[Any] = []
        self.total_available = 0
        self.is_complete = False
    
    def load_initial(self):
        """Load initial batch"""
        try:
            self.loaded_items = self.data_source(0, self.initial_load)
            return self.loaded_items
        except Exception as e:
            logger.error(f"Error loading initial data: {e}")
            return []
    
    def load_more(self) -> List[Any]:
        """Load more data on scroll"""
        if self.is_complete:
            return []
        
        try:
            offset = len(self.loaded_items)
            new_items = self.data_source(offset, self.increment)
            
            if not new_items or len(new_items) < self.increment:
                self.is_complete = True
            
            self.loaded_items.extend(new_items)
            return new_items
        except Exception as e:
            logger.error(f"Error loading more data: {e}")
            return []
    
    def reset(self):
        """Reset loader"""
        self.loaded_items.clear()
        self.is_complete = False


class FilteredTableHelper:
    """Helper for filtered table display"""
    
    def __init__(self, data_source: Callable, filter_fields: List[str]):
        """
        Initialize filtered table
        
        Args:
            data_source: Callable that returns all items
            filter_fields: Fields to allow filtering on
        """
        self.data_source = data_source
        self.filter_fields = filter_fields
        self.active_filters: Dict[str, str] = {}
        self.sort_column = None
        self.sort_order = 'asc'
    
    def set_filter(self, field: str, value: str):
        """Set filter value"""
        if field in self.filter_fields:
            self.active_filters[field] = value
        else:
            raise ValueError(f"Field {field} not in filter fields")
    
    def clear_filter(self, field: str = None):
        """Clear filter"""
        if field:
            self.active_filters.pop(field, None)
        else:
            self.active_filters.clear()
    
    def set_sort(self, column: str, order: str = 'asc'):
        """Set sort column and order"""
        self.sort_column = column
        self.sort_order = order
    
    def apply_filters(self, items: List[Dict]) -> List[Dict]:
        """Apply active filters and sort to items"""
        if not items:
            return items
        
        # Apply filters
        filtered = items
        for field, value in self.active_filters.items():
            filtered = [
                item for item in filtered
                if str(item.get(field, '')).lower().startswith(value.lower())
            ]
        
        # Apply sort
        if self.sort_column:
            filtered = sorted(
                filtered,
                key=lambda x: x.get(self.sort_column, ''),
                reverse=(self.sort_order == 'desc')
            )
        
        return filtered
    
    def get_filtered_data(self) -> List[Dict]:
        """Get filtered and sorted data"""
        all_items = self.data_source()
        return self.apply_filters(all_items)
