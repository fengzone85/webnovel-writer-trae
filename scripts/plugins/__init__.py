#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插件模块
"""

from .plugin_system import (
    Plugin,
    PluginInfo,
    PluginManager,
    HookType,
    get_plugin_manager,
    hook
)

__all__ = [
    'Plugin',
    'PluginInfo',
    'PluginManager',
    'HookType',
    'get_plugin_manager',
    'hook'
]
