#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具模块
"""

from .async_client import (
    AsyncAPIClient,
    RequestCache,
    RateLimiter,
    cached,
    get_global_cache
)

from .error_handler import (
    WebnovelError,
    ProjectNotFoundError,
    ChapterNotFoundError,
    StorySystemError,
    RAGError,
    BackupError,
    ValidationError,
    ErrorHandler,
    error_handler,
    safe_execute,
    get_error_handler,
    set_error_handler
)

__all__ = [
    'AsyncAPIClient',
    'RequestCache',
    'RateLimiter',
    'cached',
    'get_global_cache',
    'WebnovelError',
    'ProjectNotFoundError',
    'ChapterNotFoundError',
    'StorySystemError',
    'RAGError',
    'BackupError',
    'ValidationError',
    'ErrorHandler',
    'error_handler',
    'safe_execute',
    'get_error_handler',
    'set_error_handler'
]
