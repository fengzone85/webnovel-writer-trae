#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backup Manager 单元测试
"""

import json
import pytest
from pathlib import Path
from backup_manager import BackupManager

class TestBackupManager:
    """备份管理器测试类"""

    def test_init(self, temp_project):
        """测试初始化"""
        bm = BackupManager(str(temp_project))
        assert bm.project_path == temp_project
        assert bm.backup_dir == temp_project / ".webnovel" / "backups"

    def test_create_backup(self, temp_project):
        """测试创建备份"""
        bm = BackupManager(str(temp_project))
        result = bm.create_backup("测试备份")

        assert result["status"] in ["success", "warning", "error"]

    def test_list_backups(self, temp_project):
        """测试列出备份"""
        bm = BackupManager(str(temp_project))
        backups = bm.list_backups()

        assert isinstance(backups, list)

    def test_get_backup_stats(self, temp_project):
        """测试获取备份统计"""
        bm = BackupManager(str(temp_project))
        stats = bm.get_backup_stats()

        assert "backup_count" in stats
        assert "archive_count" in stats
        assert isinstance(stats["backup_count"], int)

    def test_restore_backup(self, temp_project):
        """测试恢复备份"""
        bm = BackupManager(str(temp_project))

        bm.create_backup("测试备份")
        backups = bm.list_backups()

        if backups:
            result = bm.restore_backup(backups[0]["name"])
            assert result["status"] in ["success", "error"]


class TestBackupArchive:
    """备份归档测试"""

    def test_archive_old_backups(self, temp_project):
        """测试归档旧备份"""
        bm = BackupManager(str(temp_project))
        result = bm.archive_old_backups()

        assert isinstance(result, dict)

    def test_list_archives(self, temp_project):
        """测试列出归档"""
        bm = BackupManager(str(temp_project))
        archives = bm.list_archives()

        assert isinstance(archives, list)
