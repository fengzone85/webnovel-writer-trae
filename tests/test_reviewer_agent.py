#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reviewer Agent 单元测试
"""

import pytest
from pathlib import Path
from agents.reviewer_agent import ReviewerAgent

class TestReviewerAgent:
    """审查代理测试类"""

    def test_init(self, temp_project):
        """测试初始化"""
        agent = ReviewerAgent(str(temp_project))
        assert agent.project_path == temp_project

    def test_review_chapter(self, temp_project, sample_chapter):
        """测试章节审查"""
        agent = ReviewerAgent(str(temp_project))

        chapter_file = temp_project / "章节" / "Ch001.md"
        chapter_file.write_text(sample_chapter, encoding='utf-8')

        result = agent.review_chapter(1)
        assert isinstance(result, dict)
        assert "scores" in result or "issues" in result

    def test_check_high_point(self, temp_project, sample_chapter):
        """测试爽点检查"""
        agent = ReviewerAgent(str(temp_project))
        result = agent._check_high_point(sample_chapter)

        assert "density" in result or "score" in result

    def test_check_consistency(self, temp_project):
        """测试一致性检查"""
        agent = ReviewerAgent(str(temp_project))
        result = agent._check_consistency({})

        assert "status" in result

    def test_check_pacing(self, temp_project, sample_chapter):
        """测试节奏检查"""
        agent = ReviewerAgent(str(temp_project))
        result = agent._check_pacing(sample_chapter, {})

        assert isinstance(result, dict)


class TestSixDimensionReview:
    """六维审查测试"""

    def test_all_dimensions(self, temp_project, sample_chapter):
        """测试所有维度"""
        agent = ReviewerAgent(str(temp_project))

        result = agent.review_chapter(1)

        assert isinstance(result, dict)

    def test_dimension_scoring(self, temp_project):
        """测试维度评分"""
        agent = ReviewerAgent(str(temp_project))

        sample_content = "这是一个测试章节。主角获得了异能，非常开心！"

        scores = {
            "high_point": agent._check_high_point(sample_content),
            "consistency": agent._check_consistency({}),
            "pacing": agent._check_pacing(sample_content, {}),
        }

        for dimension, score in scores.items():
            assert isinstance(score, dict), f"{dimension} should return dict"
