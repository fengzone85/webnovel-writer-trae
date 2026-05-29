#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Story System 单元测试
"""

import json
import pytest
from pathlib import Path
from story_system import StorySystem

class TestStorySystem:
    """Story System 测试类"""

    def test_init(self, temp_project):
        """测试初始化"""
        ss = StorySystem(str(temp_project))
        assert ss.project_path == temp_project
        assert ss.story_system_path == temp_project / ".story-system"
        assert ss.webnovel_path == temp_project / ".webnovel"

    def test_create_seed(self, temp_project, sample_master_setting):
        """测试创建合同种子"""
        ss = StorySystem(str(temp_project))
        result = ss.create_seed(sample_master_setting)

        assert result["status"] == "success"
        assert (temp_project / ".story-system" / "MASTER_SETTING.json").exists()

    def test_load_master_setting(self, temp_project, sample_master_setting):
        """测试加载主设定"""
        ss = StorySystem(str(temp_project))
        ss.create_seed(sample_master_setting)

        master = ss.load_master_setting()
        assert master["project_name"] == sample_master_setting["project_name"]
        assert master["genre"] == sample_master_setting["genre"]

    def test_health_check(self, temp_project, sample_master_setting):
        """测试健康检查"""
        ss = StorySystem(str(temp_project))

        result = ss.health_check()
        assert "phases" in result
        assert "status" in result

    def test_get_chapter_contract(self, temp_project):
        """测试获取章节合同"""
        ss = StorySystem(str(temp_project))
        contract = ss.get_chapter_contract(1)
        assert isinstance(contract, dict)

    def test_list_volumes(self, temp_project):
        """测试列出卷"""
        ss = StorySystem(str(temp_project))
        volumes = ss.list_volumes()
        assert isinstance(volumes, list)


class TestHealthCheck:
    """健康检查测试"""

    def test_phase1_check(self, temp_project):
        """测试 Phase 1 检查"""
        ss = StorySystem(str(temp_project))
        result = ss._check_phase1_seed()

        assert "status" in result
        assert result["status"] in ["ok", "warning", "error"]

    def test_phase2_check(self, temp_project):
        """测试 Phase 2 检查"""
        ss = StorySystem(str(temp_project))
        result = ss._check_phase2_runtime()

        assert "status" in result

    def test_phase3_check(self, temp_project):
        """测试 Phase 3 检查"""
        ss = StorySystem(str(temp_project))
        result = ss._check_phase3_commit()

        assert "status" in result

    def test_phase4_check(self, temp_project):
        """测试 Phase 4 检查"""
        ss = StorySystem(str(temp_project))
        result = ss._check_phase4_events()

        assert "status" in result

    def test_phase5_check(self, temp_project):
        """测试 Phase 5 检查"""
        ss = StorySystem(str(temp_project))
        result = ss._check_phase5_projection()

        assert "status" in result
