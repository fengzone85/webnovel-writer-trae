#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Context Agent - 创作任务书生成模块
负责构建写作上下文和约束条件
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

class ContextAgent:
    """上下文代理 - 生成创作任务书"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        self.story_system_path = self.project_path / ".story-system"
        self.webnovel_path = self.project_path / ".webnovel"
        
        # 加载主设定
        self.master_setting = self._load_master_setting()
    
    def _load_master_setting(self) -> Dict[str, Any]:
        """加载主设定"""
        master_file = self.story_system_path / "MASTER_SETTING.json"
        if master_file.exists():
            with open(master_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _load_volume_contract(self, volume_num: int) -> Dict[str, Any]:
        """加载卷合同"""
        vol_file = self.story_system_path / "volumes" / f"volume_{volume_num:03d}.json"
        if vol_file.exists():
            with open(vol_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _load_runtime_contract(self, chapter_num: int) -> Dict[str, Any]:
        """加载运行时合同"""
        contract_file = self.story_system_path / "reviews" / f"ch{chapter_num}_contract.json"
        if contract_file.exists():
            with open(contract_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _load_chapter_content(self, chapter_num: int) -> str:
        """加载章节内容"""
        chapter_file = self.project_path / "章节" / f"Ch{chapter_num:03d}.md"
        if chapter_file.exists():
            with open(chapter_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def _load_memory(self) -> Dict[str, Any]:
        """加载长期记忆"""
        memory_file = self.webnovel_path / "memory_scratchpad.json"
        if memory_file.exists():
            with open(memory_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "characters": {},
            "locations": {},
            "events": [],
            "hooks": [],
            "cool_points": [],
            "foreshadowings": []
        }
    
    def generate_writing_task(self, chapter_num: int) -> Dict[str, Any]:
        """生成创作任务书"""
        volume_num = (chapter_num - 1) // 10 + 1
        
        # 加载必要数据
        volume_contract = self._load_volume_contract(volume_num)
        runtime_contract = self._load_runtime_contract(chapter_num)
        memory = self._load_memory()
        
        # 获取前几章信息
        previous_chapters = self._get_previous_chapters(chapter_num)
        
        # 获取角色信息
        characters = self._get_characters_info(memory)
        
        # 获取当前卷信息
        volume_info = {
            "volume": volume_num,
            "title": volume_contract.get("title", f"第{volume_num}卷"),
            "summary": volume_contract.get("summary", "")
        }
        
        # 获取章节大纲
        chapter_outline = self._get_chapter_outline(volume_contract, chapter_num)
        
        # 构建创作任务书
        task = {
            "id": f"task_{chapter_num}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "chapter": chapter_num,
            "timestamp": datetime.now().isoformat(),
            "project_name": self.master_setting.get("project_name", "Untitled"),
            "genre": self.master_setting.get("genre", "unknown"),
            
            # 卷信息
            "volume": volume_info,
            
            # 章节大纲
            "outline": chapter_outline,
            
            # 约束条件
            "constraints": {
                "strand_ratio": runtime_contract.get("constraints", {}).get("strand_ratio", {
                    "quest": 0.6,
                    "fire": 0.2,
                    "constellation": 0.2
                }),
                "word_count": {
                    "min": 2000,
                    "max": 5000
                },
                "hooks_required": True,
                "cool_points_min": 1,
                "antipatterns": self.master_setting.get("antipatterns", [])
            },
            
            # 上下文信息
            "context": {
                "previous_chapters": previous_chapters,
                "current_chapter": chapter_num,
                "next_chapter": chapter_num + 1
            },
            
            # 角色信息
            "characters": characters,
            
            # 记忆信息
            "memory": {
                "recent_events": memory.get("events", [])[-10:] if memory.get("events") else [],
                "active_hooks": memory.get("hooks", []),
                "foreshadowings": memory.get("foreshadowings", [])
            },
            
            # 写作指导
            "writing_guide": self._generate_writing_guide(chapter_num, chapter_outline, runtime_contract),
            
            # 追读力策略
            "reader_pull_strategy": self._generate_reader_pull_strategy(chapter_num)
        }
        
        # 保存任务书
        task_file = self.webnovel_path / f"task_{chapter_num}.json"
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task, f, ensure_ascii=False, indent=2)
        
        return task
    
    def _get_previous_chapters(self, chapter_num: int) -> List[Dict[str, Any]]:
        """获取前几章信息"""
        previous = []
        for i in range(max(1, chapter_num - 3), chapter_num):
            content = self._load_chapter_content(i)
            if content:
                previous.append({
                    "chapter": i,
                    "summary": content[:100] + "..." if len(content) > 100 else content
                })
        return previous
    
    def _get_characters_info(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """获取角色信息"""
        return memory.get("characters", {})
    
    def _get_chapter_outline(self, volume_contract: Dict[str, Any], chapter_num: int) -> Dict[str, Any]:
        """获取章节大纲"""
        chapters = volume_contract.get("chapters", [])
        for ch in chapters:
            if ch.get("chapter") == chapter_num:
                return {
                    "title": ch.get("title", f"第{chapter_num}章"),
                    "summary": ch.get("summary", ""),
                    "quest_ratio": ch.get("quest_ratio", 0.6),
                    "fire_ratio": ch.get("fire_ratio", 0.2),
                    "constellation_ratio": ch.get("constellation_ratio", 0.2)
                }
        return {"title": f"第{chapter_num}章", "summary": ""}
    
    def _generate_writing_guide(self, chapter_num: int, outline: Dict[str, Any], runtime_contract: Dict[str, Any]) -> Dict[str, Any]:
        """生成写作指导"""
        guide = {
            "chapter_type": self._determine_chapter_type(chapter_num),
            "suggested_structure": self._get_structure_suggestion(outline),
            "key_points": [],
            "avoid_points": []
        }
        
        # 根据章节类型生成指导
        if guide["chapter_type"] == "opening":
            guide["key_points"] = [
                "建立故事背景和世界观",
                "介绍主要人物",
                "设置核心冲突的引子",
                "留下悬念吸引读者"
            ]
            guide["avoid_points"] = [
                "信息过载，一次性介绍太多设定",
                "节奏太慢，迟迟不进入主线"
            ]
        
        elif guide["chapter_type"] == "development":
            guide["key_points"] = [
                "推进主线剧情",
                "展现角色成长",
                "增加冲突和悬念",
                "适当插入爽点"
            ]
            guide["avoid_points"] = [
                "剧情拖沓，缺乏进展",
                "人物行为不符合设定"
            ]
        
        elif guide["chapter_type"] == "climax":
            guide["key_points"] = [
                "高潮冲突爆发",
                "主要悬念揭晓",
                "情感达到顶点",
                "为后续剧情铺垫"
            ]
            guide["avoid_points"] = [
                "虎头蛇尾，高潮不够激烈",
                "逻辑漏洞，情节不合理"
            ]
        
        elif guide["chapter_type"] == "transition":
            guide["key_points"] = [
                "平稳过渡剧情",
                "适当放松节奏",
                "埋下新的伏笔",
                "准备下一段剧情"
            ]
            guide["avoid_points"] = [
                "过渡过于突兀",
                "信息量过少，显得无聊"
            ]
        
        return guide
    
    def _determine_chapter_type(self, chapter_num: int) -> str:
        """判断章节类型"""
        if chapter_num == 1:
            return "opening"
        elif chapter_num % 10 == 0:  # 每卷最后一章
            return "climax"
        elif chapter_num % 5 == 0:  # 中间章节
            return "transition"
        else:
            return "development"
    
    def _get_structure_suggestion(self, outline: Dict[str, Any]) -> List[str]:
        """获取结构建议"""
        return [
            "开头：设置场景，引入冲突",
            "发展：逐步推进，增加紧张感",
            "高潮：核心冲突爆发",
            "结尾：留下悬念或伏笔"
        ]
    
    def _generate_reader_pull_strategy(self, chapter_num: int) -> Dict[str, Any]:
        """生成追读力策略"""
        return {
            "hook_type": "question" if chapter_num % 3 == 0 else "threat",
            "cool_point_target": 1,
            "debt_management": {
                "max_open_debts": 5,
                "required_resolutions": chapter_num % 10 == 5
            },
            "expectation_management": {
                "setup_next_chapter": True,
                "hint_future_events": True
            }
        }
    
    def get_context_packet(self, chapter_num: int) -> Dict[str, Any]:
        """获取上下文包（简化版）"""
        return {
            "task": self.generate_writing_task(chapter_num),
            "memory": self._load_memory(),
            "constraints": self._load_runtime_contract(chapter_num).get("constraints", {})
        }