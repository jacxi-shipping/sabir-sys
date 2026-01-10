"""
Performance monitoring and profiling utilities
"""
import logging
import time
from functools import wraps
from datetime import datetime
from typing import Dict, List, Any, Callable
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Track performance metrics"""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.start_times: Dict[str, float] = {}
    
    def start(self, operation: str):
        """Start timing an operation"""
        self.start_times[operation] = time.perf_counter()
    
    def end(self, operation: str) -> float:
        """End timing and record duration"""
        if operation not in self.start_times:
            return 0
        
        duration = time.perf_counter() - self.start_times[operation]
        
        if operation not in self.metrics:
            self.metrics[operation] = []
        
        self.metrics[operation].append(duration)
        del self.start_times[operation]
        
        return duration
    
    def get_stats(self, operation: str) -> Dict[str, float]:
        """Get statistics for an operation"""
        if operation not in self.metrics or not self.metrics[operation]:
            return {}
        
        times = self.metrics[operation]
        return {
            'count': len(times),
            'total': sum(times),
            'min': min(times),
            'max': max(times),
            'avg': sum(times) / len(times)
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all operations"""
        return {op: self.get_stats(op) for op in self.metrics}
    
    def reset(self):
        """Reset all metrics"""
        self.metrics.clear()
        self.start_times.clear()
    
    def print_report(self):
        """Print performance report"""
        print("\\n" + "="*60)
        print("PERFORMANCE REPORT")
        print("="*60)
        
        for operation, stats in self.get_all_stats().items():
            if stats:
                print(f"\\n{operation}:")
                print(f"  Count:   {stats['count']}")
                print(f"  Total:   {stats['total']:.3f}s")
                print(f"  Average: {stats['avg']:.3f}s")
                print(f"  Min:     {stats['min']:.3f}s")
                print(f"  Max:     {stats['max']:.3f}s")
        
        print("\\n" + "="*60)


class QueryProfiler:
    """Profile database queries"""
    
    def __init__(self):
        self.queries: List[Dict[str, Any]] = []
        self.slow_query_threshold = 0.1  # 100ms
    
    def record_query(self, query: str, duration: float):
        """Record a query execution"""
        entry = {
            'timestamp': datetime.utcnow(),
            'query': query,
            'duration': duration,
            'is_slow': duration > self.slow_query_threshold
        }
        self.queries.append(entry)
        
        if entry['is_slow']:
            logger.warning(f"Slow query detected ({duration:.3f}s): {query[:100]}")
    
    def get_slow_queries(self) -> List[Dict[str, Any]]:
        """Get all slow queries"""
        return [q for q in self.queries if q['is_slow']]
    
    def get_top_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get slowest queries"""
        sorted_queries = sorted(self.queries, key=lambda x: x['duration'], reverse=True)
        return sorted_queries[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get query statistics"""
        if not self.queries:
            return {}
        
        durations = [q['duration'] for q in self.queries]
        return {
            'total_queries': len(self.queries),
            'slow_queries': len(self.get_slow_queries()),
            'total_time': sum(durations),
            'avg_time': sum(durations) / len(durations),
            'min_time': min(durations),
            'max_time': max(durations)
        }
    
    def reset(self):
        """Clear all records"""
        self.queries.clear()


class UIPerformanceMonitor:
    """Monitor UI component performance"""
    
    def __init__(self):
        self.render_times: Dict[str, List[float]] = {}
        self.interaction_times: Dict[str, List[float]] = {}
    
    def record_render_time(self, component: str, duration: float):
        """Record component render time"""
        if component not in self.render_times:
            self.render_times[component] = []
        
        self.render_times[component].append(duration)
        
        # Warn if slow
        if duration > 0.5:  # 500ms
            logger.warning(f"Slow render detected for {component}: {duration:.3f}s")
    
    def record_interaction_time(self, action: str, duration: float):
        """Record user interaction time"""
        if action not in self.interaction_times:
            self.interaction_times[action] = []
        
        self.interaction_times[action].append(duration)
        
        # Warn if slow
        if duration > 1.0:  # 1 second
            logger.warning(f"Slow interaction detected for {action}: {duration:.3f}s")
    
    def get_render_stats(self, component: str) -> Dict[str, float]:
        """Get render statistics"""
        if component not in self.render_times:
            return {}
        
        times = self.render_times[component]
        return {
            'count': len(times),
            'avg': sum(times) / len(times),
            'min': min(times),
            'max': max(times)
        }


def profile_operation(operation_name: str):
    """
    Decorator to profile an operation
    
    Example:
        @profile_operation("load_sales")
        def get_sales(start_date, end_date):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            metrics = PerformanceMetrics()
            metrics.start(operation_name)
            
            try:
                result = func(*args, **kwargs)
                duration = metrics.end(operation_name)
                logger.info(f"{operation_name} completed in {duration:.3f}s")
                return result
            except Exception as e:
                logger.error(f"{operation_name} failed: {e}")
                raise
        
        return wrapper
    
    return decorator


@contextmanager
def measure_time(operation: str):
    """
    Context manager to measure operation time
    
    Example:
        with measure_time("data_processing"):
            process_data()
    """
    start = time.perf_counter()
    logger.info(f"Starting: {operation}")
    
    try:
        yield
    finally:
        duration = time.perf_counter() - start
        logger.info(f"Completed: {operation} ({duration:.3f}s)")


class BatchOperationOptimizer:
    """Optimize batch operations"""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self.metrics = PerformanceMetrics()
    
    def process_batch(self, items: List[Any], processor: Callable) -> List[Any]:
        """
        Process items in batches
        
        Args:
            items: Items to process
            processor: Function to process each item
        
        Returns:
            Processed items
        """
        results = []
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            
            self.metrics.start(f"batch_{batch_num}")
            
            try:
                batch_results = [processor(item) for item in batch]
                results.extend(batch_results)
                
                duration = self.metrics.end(f"batch_{batch_num}")
                logger.debug(f"Processed batch {batch_num} in {duration:.3f}s")
            except Exception as e:
                logger.error(f"Error processing batch {batch_num}: {e}")
                raise
        
        return results
    
    def get_performance_report(self) -> Dict[str, Dict]:
        """Get performance report for all batches"""
        return self.metrics.get_all_stats()


# Global instances
performance_metrics = PerformanceMetrics()
query_profiler = QueryProfiler()
ui_monitor = UIPerformanceMonitor()
