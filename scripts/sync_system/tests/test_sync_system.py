#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite for Sync System
测试同步系统的各项功能
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from sync_scheduler import SyncScheduler, SyncStatus, VersionTracker, SyncState
from compatibility_tester import MarkdownValidator, LinkChecker, CompatibilityTester
from dependency_manager import DependencyParser, DependencyMetadata, DependencyManager
from notification import Notification, NotificationType, NotificationManager


class TestSyncScheduler(unittest.TestCase):
    """同步调度器测试"""

    def setUp(self):
        """测试前准备"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.state_dir = self.test_dir / ".sync_status"
        self.state_dir.mkdir()

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_version_tracker_save_load(self):
        """测试版本跟踪器保存和加载"""
        tracker = VersionTracker(self.state_dir)

        state = SyncState()
        state.last_sync_time = datetime.now().isoformat()
        state.last_sync_status = SyncStatus.SUCCESS
        state.last_version = "v1.0.0"
        state.sync_count = 1

        tracker.save_state(state)

        loaded = tracker.load_state()
        self.assertEqual(loaded.last_version, "v1.0.0")
        self.assertEqual(loaded.sync_count, 1)
        self.assertEqual(loaded.last_sync_status, SyncStatus.SUCCESS)


class TestMarkdownValidator(unittest.TestCase):
    """Markdown 验证器测试"""

    def setUp(self):
        """测试前准备"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.validator = MarkdownValidator()

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_validate_empty_file(self):
        """测试空文件"""
        test_file = self.test_dir / "empty.md"
        test_file.write_text("", encoding='utf-8')

        results = self.validator.validate_file(test_file)
        self.assertTrue(any(r.status.value == 'warning' for r in results))

    def test_validate_headings(self):
        """测试标题验证"""
        test_file = self.test_dir / "headings.md"
        content = "# Heading 1\n## Heading 2\n### Heading 3\n"
        test_file.write_text(content, encoding='utf-8')

        results = self.validator.validate_file(test_file)
        self.assertTrue(any(r.status.value == 'passed' for r in results if 'heading' in r.name.lower()))

    def test_validate_links(self):
        """测试链接验证"""
        test_file = self.test_dir / "links.md"
        content = "[Link 1](https://example.com)\n[Link 2](/path/to/file)\n"
        test_file.write_text(content, encoding='utf-8')

        results = self.validator.validate_file(test_file)
        self.assertTrue(any('link' in r.name.lower() for r in results))


class TestDependencyParser(unittest.TestCase):
    """依赖解析器测试"""

    def test_parse_requirements(self):
        """测试 requirements 解析"""
        content = """
        aiohttp>=3.8.0
        filelock==3.0.0
        pydantic>=2.0.0
        # 这是注释
        pytest
        """

        deps = DependencyParser.parse_requirements(content)
        self.assertEqual(len(deps), 4)
        self.assertIn(('aiohttp', '3.8.0'), deps)
        self.assertIn(('filelock', '3.0.0'), deps)


class TestDependencyMetadata(unittest.TestCase):
    """依赖元数据测试"""

    def test_known_dependencies(self):
        """测试已知依赖"""
        aiohttp_meta = DependencyMetadata.get_metadata('aiohttp')
        self.assertEqual(aiohttp_meta['category'].value, 'required')
        self.assertIn('use_case', aiohttp_meta)

    def test_unknown_dependencies(self):
        """测试未知依赖"""
        unknown_meta = DependencyMetadata.get_metadata('nonexistent-package')
        self.assertEqual(unknown_meta, {})


class TestNotification(unittest.TestCase):
    """通知测试"""

    def test_notification_creation(self):
        """测试通知创建"""
        notification = Notification(
            type=NotificationType.SYNC_SUCCESS,
            title="Test Title",
            message="Test Message",
            timestamp=datetime.now().isoformat(),
            data={'key': 'value'}
        )

        self.assertEqual(notification.type, NotificationType.SYNC_SUCCESS)
        self.assertEqual(notification.title, "Test Title")
        self.assertEqual(notification.data['key'], 'value')


class TestCompatibilityTester(unittest.TestCase):
    """兼容性测试器测试"""

    def setUp(self):
        """测试前准备"""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_compatibility_tester_init(self):
        """测试测试器初始化"""
        tester = CompatibilityTester(str(self.test_dir))
        self.assertIsNotNone(tester.markdown_validator)
        self.assertIsNotNone(tester.link_checker)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestSyncScheduler))
    suite.addTests(loader.loadTestsFromTestCase(TestMarkdownValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestDependencyParser))
    suite.addTests(loader.loadTestsFromTestCase(TestDependencyMetadata))
    suite.addTests(loader.loadTestsFromTestCase(TestNotification))
    suite.addTests(loader.loadTestsFromTestCase(TestCompatibilityTester))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
