#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
写作流程集成测试
"""

import pytest
from pathlib import Path
from story_system import StorySystem
from agents.context_agent import ContextAgent
from agents.data_agent import DataAgent
from agents.reviewer_agent import ReviewerAgent

class TestWriteFlow:
    """写作流程集成测试"""

    def test_full_write_flow(self, temp_project, sample_master_setting, sample_chapter):
        """测试完整写作流程"""
        ss = StorySystem(str(temp_project))

        ss.create_seed(sample_master_setting)

        volume_result = ss.create_volume_contract(1, "第一卷")
        assert volume_result["status"] == "success"

        plan_result = ss.plan_chapter(1, {
            "title": "第一章 觉醒",
            "word_target": 3000,
            "key_events": ["获得异能", "系统激活"],
            "hooks": ["神秘声音"]
        })
        assert plan_result["status"] == "success"

        chapter_file = temp_project / "章节" / "Ch001.md"
        chapter_file.write_text(sample_chapter, encoding='utf-8')

        commit_result = ss.commit_chapter(1)
        assert commit_result["status"] in ["success", "completed"]

        agent = ReviewerAgent(str(temp_project))
        review_result = agent.review_chapter(1)
        assert isinstance(review_result, dict)

    def test_plan_commit_review_flow(self, temp_project, sample_master_setting):
        """测试计划-提交-审查流程"""
        ss = StorySystem(str(temp_project))
        ss.create_seed(sample_master_setting)

        ss.create_volume_contract(1, "第一卷")

        chapter_plan = {
            "title": "第二章 修炼",
            "word_target": 3000,
            "key_events": ["开始修炼"],
            "hooks": []
        }
        ss.plan_chapter(2, chapter_plan)

        chapter_file = temp_project / "章节" / "Ch002.md"
        chapter_file.write_text("# 第二章 修炼\n\n内容...", encoding='utf-8')

        ss.commit_chapter(2)

        agent = ReviewerAgent(str(temp_project))
        review = agent.review_chapter(2)
        assert isinstance(review, dict)


class TestEventFlow:
    """事件流程集成测试"""

    def test_event_extraction_flow(self, temp_project, sample_chapter):
        """测试事件提取流程"""
        agent = DataAgent(str(temp_project))

        chapter_file = temp_project / "章节" / "Ch001.md"
        chapter_file.write_text(sample_chapter, encoding='utf-8')

        events = agent.extract_events_from_chapter(1)
        assert isinstance(events, list)

    def test_memory_update_flow(self, temp_project):
        """测试记忆更新流程"""
        agent = DataAgent(str(temp_project))

        event = {
            "type": "获得能力",
            "chapter": 1,
            "description": "主角获得火球术"
        }

        result = agent.add_event(event)
        assert result["status"] in ["success", "completed"]
