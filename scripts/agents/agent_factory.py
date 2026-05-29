#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent 工厂模块
创建和管理 Agent 实例
"""

from typing import Dict, Any, Optional, Type
from pathlib import Path
import importlib
import inspect


class AgentFactory:
    """Agent 工厂"""

    _agents: Dict[str, Type] = {}
    _instances: Dict[str, Any] = {}

    @classmethod
    def register(cls, name: str, agent_class: Type):
        """注册 Agent"""
        cls._agents[name] = agent_class

    @classmethod
    def create(cls, name: str, **kwargs) -> Any:
        """创建 Agent 实例"""
        if name not in cls._agents:
            raise ValueError(f"Unknown agent: {name}")

        if name not in cls._instances:
            cls._instances[name] = cls._agents[name](**kwargs)

        return cls._instances[name]

    @classmethod
    def get(cls, name: str) -> Any:
        """获取 Agent 实例"""
        if name not in cls._instances:
            return cls.create(name)
        return cls._instances[name]

    @classmethod
    def list_agents(cls) -> list:
        """列出所有注册的 Agent"""
        return list(cls._agents.keys())

    @classmethod
    def reset(cls):
        """重置所有实例"""
        cls._instances.clear()

    @classmethod
    def load_agents_from_module(cls, module_path: str):
        """从模块加载 Agent"""
        try:
            module = importlib.import_module(module_path)

            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and hasattr(obj, 'run') and name.endswith('Agent'):
                    cls.register(name.lower().replace('agent', ''), obj)

        except ImportError:
            pass


class AgentBase:
    """Agent 基类"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.name = self.__class__.__name__
        self.initialized = False

    def initialize(self):
        """初始化 Agent"""
        self.initialized = True

    def run(self, *args, **kwargs) -> Dict[str, Any]:
        """运行 Agent"""
        raise NotImplementedError

    def validate_input(self, *args, **kwargs) -> bool:
        """验证输入"""
        return True

    def get_info(self) -> Dict[str, Any]:
        """获取 Agent 信息"""
        return {
            "name": self.name,
            "initialized": self.initialized,
            "config": self.config
        }


class ContextAgent(AgentBase):
    """Context Agent - 创作任务书生成"""

    def run(self, volume: int, chapter: Optional[int] = None, **kwargs) -> Dict[str, Any]:
        """生成创作任务书"""
        return {
            "status": "success",
            "agent": self.name,
            "task": "Generate writing context",
            "volume": volume,
            "chapter": chapter
        }


class DataAgent(AgentBase):
    """Data Agent - 事件提取与状态更新"""

    def run(self, chapter_path: str, **kwargs) -> Dict[str, Any]:
        """提取事件"""
        return {
            "status": "success",
            "agent": self.name,
            "task": "Extract events",
            "chapter": chapter_path
        }


class ReviewerAgent(AgentBase):
    """Reviewer Agent - 六维审查"""

    def run(self, chapter_path: str, dimensions: Optional[list] = None, **kwargs) -> Dict[str, Any]:
        """执行六维审查"""
        if dimensions is None:
            dimensions = [
                "highpoint",
                "consistency",
                "pacing",
                "ooc",
                "continuity",
                "reader_pull"
            ]

        return {
            "status": "success",
            "agent": self.name,
            "task": "Six-dimensional review",
            "chapter": chapter_path,
            "dimensions": dimensions,
            "results": {}
        }


class DeconstructionAgent(AgentBase):
    """Deconstruction Agent - 参考作品拆解"""

    def run(self, source_path: str, analysis_type: str = "all", **kwargs) -> Dict[str, Any]:
        """拆解参考作品"""
        return {
            "status": "success",
            "agent": self.name,
            "task": "Deconstruct reference",
            "source": source_path,
            "analysis_type": analysis_type
        }


class PlotAgent(AgentBase):
    """Plot Agent - 情节生成"""

    def run(self, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """生成情节"""
        return {
            "status": "success",
            "agent": self.name,
            "task": "Generate plot",
            "context": context
        }


class CharacterAgent(AgentBase):
    """Character Agent - 角色生成"""

    def run(self, character_type: str, **kwargs) -> Dict[str, Any]:
        """生成角色"""
        return {
            "status": "success",
            "agent": self.name,
            "task": "Generate character",
            "type": character_type
        }


class WorldBuildingAgent(AgentBase):
    """WorldBuilding Agent - 世界观构建"""

    def run(self, genre: str, **kwargs) -> Dict[str, Any]:
        """构建世界观"""
        return {
            "status": "success",
            "agent": self.name,
            "task": "World building",
            "genre": genre
        }


class EditorAgent(AgentBase):
    """Editor Agent - 文笔润色"""

    def run(self, text: str, style: str = "default", **kwargs) -> Dict[str, Any]:
        """润色文本"""
        return {
            "status": "success",
            "agent": self.name,
            "task": "Edit text",
            "original_length": len(text),
            "style": style
        }


def register_default_agents():
    """注册默认 Agent"""
    agents = [
        ContextAgent,
        DataAgent,
        ReviewerAgent,
        DeconstructionAgent,
        PlotAgent,
        CharacterAgent,
        WorldBuildingAgent,
        EditorAgent
    ]

    for agent_class in agents:
        name = agent_class.__name__.lower().replace('agent', '')
        AgentFactory.register(name, agent_class)


register_default_agents()
