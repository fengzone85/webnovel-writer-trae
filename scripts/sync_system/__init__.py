# -*- coding: utf-8 -*-
"""
Webnovel Writer Sync System
自动化定时任务系统

用于定期同步原项目文档更新，保持版本号对齐
"""

__version__ = "1.0.0"
__author__ = "Webnovel Writer Team"

from .sync_scheduler import SyncScheduler, SyncStatus, SyncResult, SyncState
from .compatibility_tester import CompatibilityTester, TestStatus, TestSuiteResult
from .dependency_manager import DependencyManager, DependencyStatus, DependencyReport
from .notification import NotificationManager, NotificationType, NotificationChannel
from .sync_system import SyncSystem

__all__ = [
    'SyncScheduler',
    'SyncStatus',
    'SyncResult',
    'SyncState',
    'CompatibilityTester',
    'TestStatus',
    'TestSuiteResult',
    'DependencyManager',
    'DependencyStatus',
    'DependencyReport',
    'NotificationManager',
    'NotificationType',
    'NotificationChannel',
    'SyncSystem',
]
