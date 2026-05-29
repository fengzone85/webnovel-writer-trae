#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
长期记忆索引模块
用于加速记忆检索和冲突检测
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime

class MemoryIndex:
    """记忆索引 - 加速检索"""

    def __init__(self, memory_data: Dict[str, Any]):
        self.memory_data = memory_data
        self._build_index()

    def _build_index(self):
        """构建索引"""
        self.char_index = {}
        self.event_index = defaultdict(list)
        self.hook_index = defaultdict(list)
        self.location_index = defaultdict(list)
        self.timeline_index = []

        characters = self.memory_data.get("characters", {})
        for char_id, char_data in characters.items():
            self._index_character(char_id, char_data)

        events = self.memory_data.get("events", [])
        for event in events:
            self._index_event(event)

        hooks = self.memory_data.get("hooks", [])
        for hook in hooks:
            self._index_hook(hook)

        locations = self.memory_data.get("locations", {})
        for loc_id, loc_data in locations.items():
            self._index_location(loc_id, loc_data)

    def _index_character(self, char_id: str, char_data: Any):
        """索引角色"""
        if isinstance(char_data, dict):
            name = char_data.get("name", char_id)
            aliases = char_data.get("aliases", [])
            self.char_index[name] = char_id
            for alias in aliases:
                self.char_index[alias] = char_id

    def _index_event(self, event: Any):
        """索引事件"""
        if isinstance(event, dict):
            event_type = event.get("type", "unknown")
            chapter = event.get("chapter", 0)
            self.event_index[event_type].append(event)
            if chapter > 0:
                self.timeline_index.append((chapter, event))

    def _index_hook(self, hook: Any):
        """索引钩子"""
        if isinstance(hook, dict):
            hook_type = hook.get("type", "unknown")
            status = hook.get("status", "pending")
            key = f"{hook_type}_{status}"
            self.hook_index[key].append(hook)

    def _index_location(self, loc_id: str, loc_data: Any):
        """索引地点"""
        if isinstance(loc_data, dict):
            name = loc_data.get("name", loc_id)
            self.location_index[name] = loc_id

    def search_characters(self, keyword: str) -> List[str]:
        """搜索角色"""
        results = []
        keyword_lower = keyword.lower()
        for name, char_id in self.char_index.items():
            if keyword_lower in name.lower():
                results.append(char_id)
        return list(set(results))

    def search_events(self, keyword: str) -> List[Dict]:
        """搜索事件"""
        results = []
        keyword_lower = keyword.lower()
        for event_list in self.event_index.values():
            for event in event_list:
                event_str = json.dumps(event, ensure_ascii=False).lower()
                if keyword_lower in event_str:
                    results.append(event)
        return results

    def get_events_by_chapter(self, chapter: int) -> List[Dict]:
        """获取指定章节的事件"""
        return [e for ch, e in self.timeline_index if ch == chapter]

    def get_timeline(self, start_chapter: int = 1, end_chapter: Optional[int] = None) -> List[Tuple[int, Dict]]:
        """获取时间线"""
        if end_chapter:
            return [(ch, e) for ch, e in self.timeline_index if start_chapter <= ch <= end_chapter]
        return [(ch, e) for ch, e in self.timeline_index if ch >= start_chapter]

    def get_pending_hooks(self, hook_type: Optional[str] = None) -> List[Dict]:
        """获取待兑现钩子"""
        if hook_type:
            return self.hook_index.get(f"{hook_type}_pending", [])
        results = []
        for key, hooks in self.hook_index.items():
            if key.endswith("_pending"):
                results.extend(hooks)
        return results

    def get_character_events(self, char_name: str) -> List[Dict]:
        """获取角色相关事件"""
        char_ids = self.search_characters(char_name)
        results = []
        for event_list in self.event_index.values():
            for event in event_list:
                if any(char_id in str(event.get("participants", [])) for char_id in char_ids):
                    results.append(event)
        return results


class ConflictDetector:
    """记忆冲突检测器"""

    def __init__(self, memory_data: Dict[str, Any]):
        self.memory = memory_data
        self.conflicts = []

    def detect_all_conflicts(self) -> List[Dict[str, Any]]:
        """检测所有冲突"""
        self.conflicts = []

        self._check_character_conflicts()
        self._check_timeline_conflicts()
        self._check_location_conflicts()
        self._check_ability_conflicts()

        return self.conflicts

    def _check_character_conflicts(self):
        """检测角色冲突"""
        characters = self.memory.get("characters", {})

        for char_id, char_data in characters.items():
            if not isinstance(char_data, dict):
                continue

            abilities = char_data.get("abilities", [])
            for ability in abilities:
                ability_name = ability.get("name", "").lower()
                ability_level = ability.get("level", 0)

                for other_id, other_data in characters.items():
                    if other_id == char_id or not isinstance(other_data, dict):
                        continue

                    other_abilities = other_data.get("abilities", [])
                    for other_ability in other_abilities:
                        if other_ability.get("name", "").lower() == ability_name:
                            level_diff = abs(other_ability.get("level", 0) - ability_level)
                            if level_diff > 10:
                                self.conflicts.append({
                                    "type": "character_ability_conflict",
                                    "severity": "warning",
                                    "character1": char_id,
                                    "character2": other_id,
                                    "ability": ability_name,
                                    "levels": [ability_level, other_ability.get("level", 0)],
                                    "message": f"角色 {char_id} 和 {other_id} 的 {ability_name} 能力等级差异过大"
                                })

    def _check_timeline_conflicts(self):
        """检测时间线冲突"""
        events = self.memory.get("events", [])
        events_sorted = sorted(events, key=lambda e: e.get("chapter", 0) if isinstance(e, dict) else 0)

        for i, event in enumerate(events_sorted):
            if not isinstance(event, dict):
                continue

            event_ch = event.get("chapter", 0)
            event_time = event.get("timestamp", "")

            for other_event in events_sorted[i+1:]:
                if not isinstance(other_event, dict):
                    continue

                other_ch = other_event.get("chapter", 0)

                if event_ch > other_ch and event_time > other_event.get("timestamp", ""):
                    self.conflicts.append({
                        "type": "timeline_conflict",
                        "severity": "error",
                        "event1": event,
                        "event2": other_event,
                        "message": f"事件时间顺序与章节顺序矛盾"
                    })

    def _check_location_conflicts(self):
        """检测地点冲突"""
        events = self.memory.get("events", [])

        for i, event in enumerate(events):
            if not isinstance(event, dict):
                continue

            location1 = event.get("location", "")
            chapter1 = event.get("chapter", 0)

            for other_event in events[i+1:]:
                if not isinstance(other_event, dict):
                    continue

                chapter2 = other_event.get("chapter", 0)
                chapter_diff = abs(chapter1 - chapter2)

                if chapter_diff > 5 and event.get("location", "") == other_event.get("location", ""):
                    continue

                if chapter_diff <= 3 and location1 != other_event.get("location", ""):
                    pass

    def _check_ability_conflicts(self):
        """检测能力设定冲突"""
        characters = self.memory.get("characters", {})

        for char_id, char_data in characters.items():
            if not isinstance(char_data, dict):
                continue

            abilities = char_data.get("abilities", [])
            ability_names = [a.get("name", "").lower() for a in abilities]

            if len(ability_names) != len(set(ability_names)):
                self.conflicts.append({
                    "type": "duplicate_ability",
                    "severity": "error",
                    "character": char_id,
                    "message": f"角色 {char_id} 有重复的能力设定"
                })

    def check_new_event(self, new_event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检测新事件与现有记忆的冲突"""
        conflicts = []
        chapter = new_event.get("chapter", 0)
        location = new_event.get("location", "")
        participants = new_event.get("participants", [])

        events = self.memory.get("events", [])
        for event in events:
            if not isinstance(event, dict):
                continue

            if chapter == event.get("chapter", 0):
                if location and location != event.get("location", ""):
                    conflicts.append({
                        "type": "location_conflict",
                        "severity": "warning",
                        "existing_event": event,
                        "new_event": new_event,
                        "message": f"章节 {chapter} 中存在地点矛盾"
                    })

            if any(p in participants for p in event.get("participants", [])):
                time_diff = abs((chapter or 0) - (event.get("chapter", 0) or 0))
                if time_diff > 10:
                    conflicts.append({
                        "type": "participant_timeline_conflict",
                        "severity": "warning",
                        "existing_event": event,
                        "new_event": new_event,
                        "message": f"角色时间线矛盾"
                    })

        return conflicts


def create_memory_index(memory_file: Path) -> Optional[MemoryIndex]:
    """从文件创建记忆索引"""
    if not memory_file.exists():
        return None

    try:
        with open(memory_file, 'r', encoding='utf-8') as f:
            memory_data = json.load(f)
        return MemoryIndex(memory_data)
    except Exception as e:
        print(f"Error creating memory index: {e}")
        return None


if __name__ == "__main__":
    test_memory = {
        "characters": {
            "char1": {"name": "张三", "abilities": [{"name": "火球术", "level": 10}]},
            "char2": {"name": "李四", "abilities": [{"name": "火球术", "level": 50}]}
        },
        "events": [
            {"type": "战斗", "chapter": 1, "location": "森林"},
            {"type": "战斗", "chapter": 2, "location": "城市"}
        ],
        "hooks": [],
        "locations": {}
    }

    detector = ConflictDetector(test_memory)
    conflicts = detector.detect_all_conflicts()
    print(f"检测到 {len(conflicts)} 个冲突")
    for c in conflicts:
        print(f"  - {c.get('message')}")
