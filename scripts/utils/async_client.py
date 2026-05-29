#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步API客户端模块
用于提高RAG检索性能
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from functools import wraps

class AsyncAPIClient:
    """异步API客户端"""

    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_with_semaphore(self, coro):
        """使用信号量控制并发"""
        async with self.semaphore:
            return await coro

    async def batch_fetch(self, coros: List[any]) -> List[Any]:
        """批量获取"""
        tasks = [self.fetch_with_semaphore(coro) for coro in coros]
        return await asyncio.gather(*tasks, return_exceptions=True)


class RequestCache:
    """请求缓存"""

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.cache: Dict[str, tuple] = {}
        self.max_size = max_size
        self.ttl = ttl

    def _make_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return "|".join(key_parts)

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value: Any):
        """设置缓存"""
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]

        self.cache[key] = (value, time.time())

    def clear(self):
        """清空缓存"""
        self.cache.clear()

    def size(self) -> int:
        """获取缓存大小"""
        return len(self.cache)


def cached(cache: RequestCache, *arg_indices):
    """缓存装饰器

    Args:
        cache: RequestCache 实例
        arg_indices: 要包含在缓存键中的参数索引
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            key_parts = [func.__name__]
            for i in arg_indices:
                if i < len(args):
                    key_parts.append(str(args[i]))
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")
            cache_key = "|".join(key_parts)

            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            result = await func(*args, **kwargs)
            cache.set(cache_key, result)
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            key_parts = [func.__name__]
            for i in arg_indices:
                if i < len(args):
                    key_parts.append(str(args[i]))
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")
            cache_key = "|".join(key_parts)

            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class RateLimiter:
    """速率限制器"""

    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self.calls: List[float] = []

    def is_allowed(self) -> bool:
        """检查是否允许调用"""
        now = time.time()
        self.calls = [t for t in self.calls if now - t < self.period]

        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        return False

    def wait_time(self) -> float:
        """获取需要等待的时间"""
        if len(self.calls) < self.max_calls:
            return 0

        now = time.time()
        oldest_in_window = [t for t in self.calls if now - t < self.period]

        if not oldest_in_window:
            return 0

        return self.period - (now - min(oldest_in_window))


_global_cache = RequestCache()

def get_global_cache() -> RequestCache:
    """获取全局缓存实例"""
    return _global_cache
