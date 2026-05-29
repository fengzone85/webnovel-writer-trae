#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插件系统
允许扩展功能模块
"""

import os
import sys
import importlib
import inspect
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class HookType(Enum):
    """钩子类型"""
    PRE_INIT = "pre_init"
    POST_INIT = "post_init"
    PRE_WRITE = "pre_write"
    POST_WRITE = "post_write"
    PRE_REVIEW = "pre_review"
    POST_REVIEW = "post_review"
    PRE_COMMIT = "pre_commit"
    POST_COMMIT = "post_commit"
    ON_ERROR = "on_error"


@dataclass
class PluginInfo:
    """插件信息"""
    name: str
    version: str
    author: str
    description: str
    hooks: List[HookType] = field(default_factory=list)
    commands: List[str] = field(default_factory=list)
    enabled: bool = True


class Plugin:
    """插件基类"""

    info: PluginInfo = None

    def __init__(self):
        self.enabled = True

    def on_load(self):
        """加载时调用"""
        pass

    def on_unload(self):
        """卸载时调用"""
        pass

    def execute(self, hook: HookType, *args, **kwargs) -> Any:
        """执行钩子"""
        return None


class PluginManager:
    """插件管理器"""

    def __init__(self, plugin_dir: Optional[Path] = None):
        self.plugin_dir = plugin_dir or Path(__file__).parent / "plugins"
        self.plugins: Dict[str, Plugin] = {}
        self.hooks: Dict[HookType, List[Callable]] = {
            hook_type: [] for hook_type in HookType
        }

    def register_hook(self, hook_type: HookType, callback: Callable):
        """注册钩子回调"""
        if hook_type not in self.hooks:
            self.hooks[hook_type] = []
        self.hooks[hook_type].append(callback)

    def unregister_hook(self, hook_type: HookType, callback: Callable):
        """注销钩子回调"""
        if hook_type in self.hooks and callback in self.hooks[hook_type]:
            self.hooks[hook_type].remove(callback)

    def trigger_hook(self, hook_type: HookType, *args, **kwargs) -> List[Any]:
        """触发钩子"""
        results = []
        if hook_type in self.hooks:
            for callback in self.hooks[hook_type]:
                try:
                    result = callback(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    print(f"Hook error in {callback.__name__}: {e}")
        return results

    def load_plugin(self, plugin_path: Path) -> Optional[Plugin]:
        """加载插件"""
        try:
            spec = importlib.util.spec_from_file_location(plugin_path.stem, plugin_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[plugin_path.stem] = module
                spec.loader.exec_module(module)

                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, Plugin) and obj != Plugin:
                        plugin = obj()
                        self.plugins[plugin.info.name] = plugin
                        plugin.on_load()
                        return plugin
        except Exception as e:
            print(f"Failed to load plugin {plugin_path}: {e}")
        return None

    def load_plugins(self):
        """加载所有插件"""
        if not self.plugin_dir.exists():
            return

        for plugin_file in self.plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue
            self.load_plugin(plugin_file)

    def unload_plugin(self, name: str) -> bool:
        """卸载插件"""
        if name in self.plugins:
            plugin = self.plugins[name]
            plugin.on_unload()
            del self.plugins[name]
            return True
        return False

    def get_plugin(self, name: str) -> Optional[Plugin]:
        """获取插件"""
        return self.plugins.get(name)

    def list_plugins(self) -> List[PluginInfo]:
        """列出所有插件"""
        return [p.info for p in self.plugins.values()]

    def enable_plugin(self, name: str):
        """启用插件"""
        if name in self.plugins:
            self.plugins[name].enabled = True

    def disable_plugin(self, name: str):
        """禁用插件"""
        if name in self.plugins:
            self.plugins[name].enabled = False


_global_plugin_manager: Optional[PluginManager] = None

def get_plugin_manager() -> PluginManager:
    """获取全局插件管理器"""
    global _global_plugin_manager
    if _global_plugin_manager is None:
        _global_plugin_manager = PluginManager()
    return _global_plugin_manager


def hook(hook_type: HookType):
    """钩子装饰器"""
    def decorator(func: Callable) -> Callable:
        pm = get_plugin_manager()
        pm.register_hook(hook_type, func)
        return func
    return decorator
