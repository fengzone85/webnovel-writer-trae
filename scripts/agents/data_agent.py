#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Agent - 事件提取与状态更新模块
负责从正文提取事件、状态变化、实体信息等
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

class DataAgent:
    """数据代理 - 提取事件和更新状态"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        self.story_system_path = self.project_path / ".story-system"
        self.webnovel_path = self.project_path / ".webnovel"
        
        # 实体识别模式
        self.entity_patterns = {
            "character": r"(【(?:\u4eba\u7269|\u89d2\u8272)】[^\n]+)",
            "location": r"(【(?:\u5730\u70b9|\u57ce\u5e02|\u5708\u56ed)】[^\n]+)",
            "organization": r"(【(?:\u5b97\u95e8|\u8054\u76df|\u90e8\u961f)】[^\n]+)",
            "item": r"(【(?:\u5b9d\u8d44|\u6b66\u5668|\u836f\u54c1)】[^\n]+)"
        }
        
        # 事件类型
        self.event_types = [
            "action",      # 动作事件
            "dialogue",    # 对话事件
            "combat",      # 战斗事件
            "discovery",   # 发现事件
            "decision",    # 决策事件
            "emotion",     # 情感事件
            "relationship",# 关系事件
            "power",       # 能力/实力变化
            "plot_twist"   # 剧情反转
        ]
    
    def extract_events(self, chapter_num: int, content: str) -> Dict[str, Any]:
        """从章节内容提取事件"""
        events = {
            "accepted_events": [],
            "state_deltas": {},
            "entity_deltas": {}
        }
        
        # 提取实体
        entities = self._extract_entities(content)
        events["entity_deltas"] = entities
        
        # 提取事件
        extracted_events = self._extract_event_instances(content)
        events["accepted_events"] = extracted_events
        
        # 提取状态变化
        state_changes = self._extract_state_changes(content)
        events["state_deltas"] = state_changes
        
        # 保存提取结果
        self._save_extraction(chapter_num, events)
        
        return events
    
    def _extract_entities(self, content: str) -> Dict[str, Any]:
        """提取实体信息"""
        entities = {
            "characters": [],
            "locations": [],
            "organizations": [],
            "items": [],
            "new_entities": [],
            "mentioned_entities": []
        }
        
        # 使用正则提取实体
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, content)
            for match in matches:
                entity_name = match.replace("【人物】", "").replace("【角色】", "").strip()
                entity_name = entity_name.replace("【地点】", "").replace("【城市】", "").replace("【庄园】", "").strip()
                entity_name = entity_name.replace("【宗门】", "").replace("【联盟】", "").replace("【部队】", "").strip()
                entity_name = entity_name.replace("【宝物】", "").replace("【武器】", "").replace("【药品】", "").strip()
                
                if entity_name:
                    entities[entity_type + "s"].append(entity_name)
                    entities["mentioned_entities"].append({
                        "type": entity_type,
                        "name": entity_name
                    })
        
        return entities
    
    def _extract_event_instances(self, content: str) -> List[Dict[str, Any]]:
        """提取事件实例"""
        events = []
        
        # 分割段落
        paragraphs = content.split('\n\n')
        
        for idx, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                continue
            
            event = self._analyze_paragraph(paragraph, idx)
            if event:
                events.append(event)
        
        return events
    
    def _analyze_paragraph(self, paragraph: str, index: int) -> Dict[str, Any]:
        """分析段落并识别事件"""
        event = {
            "id": f"event_{index}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "type": "action",
            "timestamp": datetime.now().isoformat(),
            "content": paragraph[:100],
            "characters": [],
            "location": "",
            "importance": "normal",
            "impact": "low"
        }
        
        # 识别事件类型
        if "说道" in paragraph or "问" in paragraph or "答" in paragraph:
            event["type"] = "dialogue"
        elif "战斗" in paragraph or "攻击" in paragraph or "对决" in paragraph:
            event["type"] = "combat"
            event["importance"] = "high"
            event["impact"] = "high"
        elif "发现" in paragraph or "知道了" in paragraph or "明白" in paragraph:
            event["type"] = "discovery"
            event["importance"] = "medium"
        elif "决定" in paragraph or "选择" in paragraph or "决心" in paragraph:
            event["type"] = "decision"
            event["importance"] = "medium"
        elif "高兴" in paragraph or "愤怒" in paragraph or "悲伤" in paragraph:
            event["type"] = "emotion"
        elif "修为" in paragraph or "境界" in paragraph or "实力" in paragraph:
            event["type"] = "power"
            event["importance"] = "high"
            event["impact"] = "high"
        elif "惊讶" in paragraph or "没想到" in paragraph or "反转" in paragraph:
            event["type"] = "plot_twist"
            event["importance"] = "high"
            event["impact"] = "high"
        
        # 提取角色
        for char_pattern in [r"【人物】([^\n]+)", r"【角色】([^\n]+)"]:
            matches = re.findall(char_pattern, paragraph)
            event["characters"].extend([m.strip() for m in matches])
        
        # 提取地点
        for loc_pattern in [r"【地点】([^\n]+)", r"【城市】([^\n]+)"]:
            matches = re.findall(loc_pattern, paragraph)
            if matches:
                event["location"] = matches[0].strip()
        
        return event
    
    def _extract_state_changes(self, content: str) -> Dict[str, Any]:
        """提取状态变化"""
        state_changes = {
            "character_states": {},
            "plot_states": {},
            "world_states": {}
        }
        
        # 检测实力变化
        power_patterns = [
            (r"突破到(.+?)境界", "境界提升"),
            (r"修为达到(.+?)", "修为提升"),
            (r"实力大增", "实力提升"),
            (r"获得了(.+?)", "获得物品")
        ]
        
        for pattern, change_type in power_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                state_changes["character_states"][match.strip()] = change_type
        
        # 检测剧情状态
        if "完结" in content or "结束" in content:
            state_changes["plot_states"]["arc_complete"] = True
        
        return state_changes
    
    def _save_extraction(self, chapter_num: int, events: Dict[str, Any]):
        """保存提取结果到提交记录"""
        commit_file = self.story_system_path / "commits" / f"chapter_{chapter_num:03d}.commit.json"
        
        if commit_file.exists():
            with open(commit_file, 'r', encoding='utf-8') as f:
                commit = json.load(f)
        else:
            commit = {}
        
        commit["events"] = events["accepted_events"]
        commit["state_deltas"] = events["state_deltas"]
        commit["entity_deltas"] = events["entity_deltas"]
        commit["extracted_at"] = datetime.now().isoformat()
        
        with open(commit_file, 'w', encoding='utf-8') as f:
            json.dump(commit, f, ensure_ascii=False, indent=2)
    
    def update_memory(self, chapter_num: int):
        """更新长期记忆"""
        # 读取提取结果
        commit_file = self.story_system_path / "commits" / f"chapter_{chapter_num:03d}.commit.json"
        if not commit_file.exists():
            return
        
        with open(commit_file, 'r', encoding='utf-8') as f:
            commit = json.load(f)
        
        # 加载现有记忆
        memory_file = self.webnovel_path / "memory_scratchpad.json"
        if memory_file.exists():
            with open(memory_file, 'r', encoding='utf-8') as f:
                memory = json.load(f)
        else:
            memory = {
                "characters": {},
                "locations": {},
                "events": [],
                "hooks": [],
                "cool_points": [],
                "foreshadowings": [],
                "last_updated": ""
            }
        
        # 更新角色记忆
        entities = commit.get("entity_deltas", {})
        for char in entities.get("characters", []):
            if char not in memory["characters"]:
                memory["characters"][char] = {
                    "first_appearance": chapter_num,
                    "last_appearance": chapter_num,
                    "appearances": [chapter_num]
                }
            else:
                memory["characters"][char]["last_appearance"] = chapter_num
                if chapter_num not in memory["characters"][char]["appearances"]:
                    memory["characters"][char]["appearances"].append(chapter_num)
        
        # 更新事件记忆
        events = commit.get("events", [])
        for event in events:
            memory["events"].append({
                "chapter": chapter_num,
                "event_type": event["type"],
                "content": event["content"],
                "importance": event["importance"]
            })
        
        # 限制记忆数量
        memory["events"] = memory["events"][-100:]
        
        # 更新时间戳
        memory["last_updated"] = datetime.now().isoformat()
        
        # 保存记忆
        with open(memory_file, 'w', encoding='utf-8') as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
    
    def analyze_chapter(self, chapter_num: int) -> Dict[str, Any]:
        """分析章节（综合方法）"""
        # 读取章节内容
        chapter_file = self.project_path / "章节" / f"Ch{chapter_num:03d}.md"
        if not chapter_file.exists():
            return {"status": "failed", "error": "章节文件不存在"}
        
        with open(chapter_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取事件
        events = self.extract_events(chapter_num, content)
        
        # 更新记忆
        self.update_memory(chapter_num)
        
        return {
            "status": "completed",
            "chapter": chapter_num,
            "events": events
        }