#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Story System - 合同驱动架构核心模块
实现 Phase 1-5 完整合同链
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

class StorySystem:
    """Story System 合同驱动架构"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        self.story_system_path = self.project_path / ".story-system"
        self.webnovel_path = self.project_path / ".webnovel"
        
        # 初始化目录结构
        self._initialize_directories()
        
        # 加载主设定
        self.master_setting = self._load_master_setting()
    
    def _initialize_directories(self):
        """初始化 Story System 目录结构"""
        directories = [
            self.story_system_path / "volumes",
            self.story_system_path / "chapters",
            self.story_system_path / "commits",
            self.story_system_path / "reviews",
            self.story_system_path / "events",
            self.webnovel_path / "summaries"
        ]
        
        for dir_path in directories:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def _load_master_setting(self) -> Dict[str, Any]:
        """加载主设定合同"""
        master_file = self.story_system_path / "MASTER_SETTING.json"
        
        if master_file.exists():
            with open(master_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 返回默认设定
        return {
            "project_name": "Untitled",
            "genre": "unknown",
            "main_character": "",
            "golden_finger": "",
            "created_at": datetime.now().isoformat(),
            "version": "6.0.0",
            "strand_config": {
                "quest_ratio": 0.6,
                "fire_ratio": 0.2,
                "constellation_ratio": 0.2
            },
            "antipatterns": [],
            "hooks": {}
        }
    
    def _generate_contract_id(self) -> str:
        """生成唯一合同ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        hash_val = hashlib.md5(timestamp.encode()).hexdigest()[:8]
        return f"contract_{timestamp}_{hash_val}"
    
    # ================ Phase 1: 合同种子 ================
    
    def emit_contract_seed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成合同种子（Phase 1）"""
        seed = {
            "id": self._generate_contract_id(),
            "type": "seed",
            "version": "6.0.0",
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "checksum": self._calculate_checksum(data)
        }
        
        # 保存到 MASTER_SETTING.json
        self.master_setting.update(data)
        self.master_setting["last_updated"] = seed["timestamp"]
        
        with open(self.story_system_path / "MASTER_SETTING.json", 'w', encoding='utf-8') as f:
            json.dump(self.master_setting, f, ensure_ascii=False, indent=2)
        
        return seed
    
    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """计算数据校验和"""
        json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    # ================ Phase 2: 运行时合同 ================
    
    def emit_runtime_contracts(self, chapter_num: int) -> Dict[str, Any]:
        """生成运行时合同（Phase 2）"""
        volume_num = (chapter_num - 1) // 10 + 1
        
        # 读取卷合同
        volume_file = self.story_system_path / "volumes" / f"volume_{volume_num:03d}.json"
        if not volume_file.exists():
            return {"status": "failed", "error": f"卷合同不存在: volume_{volume_num:03d}.json"}
        
        with open(volume_file, 'r', encoding='utf-8') as f:
            volume_data = json.load(f)
        
        # 查找章节信息
        chapter_info = None
        for ch in volume_data.get("chapters", []):
            if ch["chapter"] == chapter_num:
                chapter_info = ch
                break
        
        if not chapter_info:
            return {"status": "failed", "error": f"章节 {chapter_num} 未在大纲中"}
        
        # 生成运行时合同
        runtime_contract = {
            "id": self._generate_contract_id(),
            "type": "runtime",
            "chapter": chapter_num,
            "volume": volume_num,
            "timestamp": datetime.now().isoformat(),
            "constraints": {
                "strand_ratio": {
                    "quest": chapter_info.get("quest_ratio", 0.6),
                    "fire": chapter_info.get("fire_ratio", 0.2),
                    "constellation": chapter_info.get("constellation_ratio", 0.2)
                },
                "word_count": {"min": 2000, "max": 5000},
                "hooks_required": True,
                "cool_points_min": 1
            },
            "context": {
                "previous_chapters": list(range(max(1, chapter_num - 3), chapter_num)),
                "next_chapter": chapter_num + 1,
                "current_volume": volume_num
            },
            "antipatterns": self.master_setting.get("antipatterns", [])
        }
        
        # 保存审查合同
        review_file = self.story_system_path / "reviews" / f"ch{chapter_num}_contract.json"
        with open(review_file, 'w', encoding='utf-8') as f:
            json.dump(runtime_contract, f, ensure_ascii=False, indent=2)
        
        return {"status": "completed", "contract": runtime_contract}
    
    # ================ Phase 3: 章节提交链 ================
    
    def chapter_commit(self, chapter_num: int, content: str) -> Dict[str, Any]:
        """章节提交（Phase 3）"""
        # 验证运行时合同存在
        review_file = self.story_system_path / "reviews" / f"ch{chapter_num}_contract.json"
        if not review_file.exists():
            return {"status": "failed", "error": "运行时合同不存在，请先调用 emit_runtime_contracts"}
        
        # 读取运行时合同
        with open(review_file, 'r', encoding='utf-8') as f:
            runtime_contract = json.load(f)
        
        # 生成提交记录
        commit = {
            "id": self._generate_contract_id(),
            "type": "commit",
            "chapter": chapter_num,
            "timestamp": datetime.now().isoformat(),
            "content_hash": hashlib.sha256(content.encode()).hexdigest(),
            "word_count": len(content),
            "constraints_met": True,  # 后续由 Reviewer 验证
            "events": [],  # 后续由 Data Agent 填充
            "state_deltas": {},  # 后续由 Data Agent 填充
            "entity_deltas": {}  # 后续由 Data Agent 填充
        }
        
        # 保存提交记录
        commit_file = self.story_system_path / "commits" / f"chapter_{chapter_num:03d}.commit.json"
        with open(commit_file, 'w', encoding='utf-8') as f:
            json.dump(commit, f, ensure_ascii=False, indent=2)
        
        # 投影写入
        self._project_write(chapter_num, content, commit)
        
        return {"status": "completed", "commit": commit}
    
    def _project_write(self, chapter_num: int, content: str, commit: Dict[str, Any]):
        """投影写入（Phase 3 关键步骤）"""
        # 1. 更新 state.json
        state_file = self.webnovel_path / "state.json"
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
        else:
            state = {"current_chapter": 0, "total_chapters": 0, "last_updated": ""}
        
        state["current_chapter"] = chapter_num
        state["total_chapters"] = max(state.get("total_chapters", 0), chapter_num)
        state["last_updated"] = datetime.now().isoformat()
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        # 2. 生成章节摘要
        summary = self._generate_summary(content)
        summary_file = self.webnovel_path / "summaries" / f"ch{chapter_num}_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        # 3. 更新长期记忆（由 Memory Agent 完成）
    
    def _generate_summary(self, content: str) -> Dict[str, Any]:
        """生成章节摘要"""
        lines = content.split('\n')
        first_paragraph = ""
        for line in lines:
            if line.strip() and not line.startswith('#'):
                first_paragraph = line.strip()[:200]
                break
        
        return {
            "chapter": None,
            "title": "",
            "summary": first_paragraph,
            "word_count": len(content),
            "characters": [],
            "locations": [],
            "events": [],
            "hooks": [],
            "cool_points": []
        }
    
    # ================ Phase 4: 事件审计链 ================
    
    def story_events(self, chapter_num: int) -> Dict[str, Any]:
        """事件审计（Phase 4）"""
        # 读取提交记录
        commit_file = self.story_system_path / "commits" / f"chapter_{chapter_num:03d}.commit.json"
        if not commit_file.exists():
            return {"status": "failed", "error": "提交记录不存在"}
        
        with open(commit_file, 'r', encoding='utf-8') as f:
            commit = json.load(f)
        
        # 生成事件记录
        events = {
            "id": self._generate_contract_id(),
            "type": "event_audit",
            "chapter": chapter_num,
            "timestamp": datetime.now().isoformat(),
            "commit_id": commit["id"],
            "events": [],
            "revisions": [],
            "ledger": []
        }
        
        # 保存事件记录
        event_file = self.story_system_path / "events" / f"chapter_{chapter_num:03d}.events.json"
        with open(event_file, 'w', encoding='utf-8') as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
        
        return {"status": "completed", "events": events}
    
    # ================ Phase 5: 旧链路降级 ================
    
    def migrate_to_contract_first(self):
        """迁移到合同优先模式（Phase 5）"""
        # 检查是否需要迁移
        state_file = self.webnovel_path / "state.json"
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            if state.get("contract_first_migrated", False):
                return {"status": "completed", "message": "已迁移到合同优先模式"}
        
        # 标记已迁移
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
        else:
            state = {}
        
        state["contract_first_migrated"] = True
        state["migration_timestamp"] = datetime.now().isoformat()
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        return {"status": "completed", "message": "成功迁移到合同优先模式"}
    
    # ================ 健康检查（Phase 5） ================

    def health_check(self) -> Dict[str, Any]:
        """执行完整健康检查 - Phase 5"""
        report = {
            "status": "healthy",
            "phases": {},
            "issues": [],
            "timestamp": datetime.now().isoformat()
        }

        # Phase 1: 检查合同种子
        report["phases"]["Phase 1: 合同种子"] = self._check_phase1_seed()

        # Phase 2: 检查运行时合同
        report["phases"]["Phase 2: 运行时合同"] = self._check_phase2_runtime()

        # Phase 3: 检查章节提交
        report["phases"]["Phase 3: 章节提交链"] = self._check_phase3_commit()

        # Phase 4: 检查事件审计
        report["phases"]["Phase 4: 事件审计链"] = self._check_phase4_events()

        # Phase 5: 检查投影一致性
        report["phases"]["Phase 5: 真源管理"] = self._check_phase5_projection()

        # 收集所有问题
        for phase_name, phase_result in report["phases"].items():
            if phase_result.get("issues"):
                report["issues"].extend([f"{phase_name}: {i}" for i in phase_result["issues"]])

        # 确定总体状态
        if any(p.get("status") == "error" for p in report["phases"].values()):
            report["status"] = "error"
        elif any(p.get("status") == "warning" for p in report["phases"].values()):
            report["status"] = "warning"
        else:
            report["status"] = "healthy"

        return report

    def _check_phase1_seed(self) -> Dict[str, Any]:
        """检查 Phase 1: 合同种子"""
        issues = []

        master_file = self.story_system_path / "MASTER_SETTING.json"
        if not master_file.exists():
            return {"status": "error", "issues": ["主设定文件 MASTER_SETTING.json 不存在"]}

        try:
            with open(master_file, 'r', encoding='utf-8') as f:
                master_data = json.load(f)

            required_fields = ["project_name", "genre", "main_character"]
            for field in required_fields:
                if not master_data.get(field):
                    issues.append(f"缺少必要字段: {field}")
        except Exception as e:
            return {"status": "error", "issues": [f"主设定文件格式错误: {str(e)}"]}

        return {"status": "ok" if not issues else "warning", "issues": issues}

    def _check_phase2_runtime(self) -> Dict[str, Any]:
        """检查 Phase 2: 运行时合同"""
        issues = []

        volumes_dir = self.story_system_path / "volumes"
        if not volumes_dir.exists():
            return {"status": "error", "issues": ["卷目录不存在"]}

        volume_files = list(volumes_dir.glob("volume_*.json"))
        if not volume_files:
            issues.append("尚未创建任何卷合同")

        return {"status": "ok" if not issues else "warning", "issues": issues}

    def _check_phase3_commit(self) -> Dict[str, Any]:
        """检查 Phase 3: 章节提交链"""
        issues = []

        commits_dir = self.story_system_path / "commits"
        if not commits_dir.exists():
            return {"status": "error", "issues": ["提交目录不存在"]}

        commit_files = list(commits_dir.glob("*.commit.json"))
        if not commit_files:
            issues.append("尚未提交任何章节")

        # 检查章节文件是否与提交一致
        chapters_dir = Path(self.project_path) / "章节"
        if chapters_dir.exists():
            chapter_files = list(chapters_dir.glob("Ch*.md"))
            if len(chapter_files) != len(commit_files):
                issues.append(f"章节文件数 ({len(chapter_files)}) 与提交数 ({len(commit_files)}) 不一致")

        return {"status": "ok" if not issues else "warning", "issues": issues}

    def _check_phase4_events(self) -> Dict[str, Any]:
        """检查 Phase 4: 事件审计链"""
        issues = []

        events_dir = self.story_system_path / "events"
        if not events_dir.exists():
            return {"status": "warning", "issues": ["事件审计目录不存在"]}

        event_files = list(events_dir.glob("*.events.json"))
        if not event_files:
            issues.append("尚未生成任何事件审计")

        return {"status": "ok" if not issues else "warning", "issues": issues}

    def _check_phase5_projection(self) -> Dict[str, Any]:
        """检查 Phase 5: 真源管理"""
        issues = []

        # 检查 state.json 与实际章节数是否一致
        state_file = self.webnovel_path / "state.json"
        if not state_file.exists():
            return {"status": "warning", "issues": ["state.json 不存在"]}

        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)

            actual_chapters = 0
            chapters_dir = Path(self.project_path) / "章节"
            if chapters_dir.exists():
                actual_chapters = len(list(chapters_dir.glob("Ch*.md")))

            state_chapters = state.get("total_chapters", 0)

            if actual_chapters != state_chapters:
                issues.append(f"state.json 记录 {state_chapters} 章，实际 {actual_chapters} 章")

            if not state.get("contract_first_migrated"):
                issues.append("尚未迁移到合同优先模式")
        except Exception as e:
            return {"status": "error", "issues": [f"state.json 读取错误: {str(e)}"]}

        # 检查 index.db
        index_db = self.webnovel_path / "index.db"
        if not index_db.exists():
            issues.append("索引数据库 index.db 不存在")

        # 检查 memory_scratchpad.json
        memory_file = self.webnovel_path / "memory_scratchpad.json"
        if not memory_file.exists():
            issues.append("长期记忆文件 memory_scratchpad.json 不存在")

        return {"status": "ok" if not issues else "warning", "issues": issues}
    
    # ================ 辅助方法 ================
    
    def get_chapter_contract(self, chapter_num: int) -> Dict[str, Any]:
        """获取章节合同"""
        contract_file = self.story_system_path / "chapters" / f"chapter_{chapter_num:03d}.json"
        if contract_file.exists():
            with open(contract_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def list_volumes(self) -> List[Dict[str, Any]]:
        """列出所有卷合同"""
        volumes = []
        for vol_file in (self.story_system_path / "volumes").glob("volume_*.json"):
            with open(vol_file, 'r', encoding='utf-8') as f:
                volumes.append(json.load(f))
        return volumes
    
    def list_chapters(self, volume_num: int = None) -> List[Dict[str, Any]]:
        """列出章节"""
        chapters = []
        if volume_num:
            vol_file = self.story_system_path / "volumes" / f"volume_{volume_num:03d}.json"
            if vol_file.exists():
                with open(vol_file, 'r', encoding='utf-8') as f:
                    vol_data = json.load(f)
                    chapters = vol_data.get("chapters", [])
        else:
            for ch_file in (self.story_system_path / "chapters").glob("chapter_*.json"):
                with open(ch_file, 'r', encoding='utf-8') as f:
                    chapters.append(json.load(f))
        return chapters