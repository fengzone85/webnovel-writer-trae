#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
备份管理模块
支持自动备份、归档管理、恢复功能
"""

import os
import json
import shutil
import zipfile
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

class BackupManager:
    """备份管理器"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        self.backup_path = self.project_path / ".webnovel" / "backups"
        self.archive_path = self.project_path / ".webnovel" / "archive"
        
        # 确保目录存在
        self.backup_path.mkdir(parents=True, exist_ok=True)
        self.archive_path.mkdir(parents=True, exist_ok=True)
        
        # 备份配置
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载备份配置"""
        config_file = self.project_path / ".webnovel" / "backup_config.json"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            "auto_backup": True,
            "backup_interval_hours": 24,
            "keep_backups": 7,
            "archive_interval_days": 7
        }
    
    def _save_config(self):
        """保存备份配置"""
        config_file = self.project_path / ".webnovel" / "backup_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def _is_excluded(self, path: Path) -> bool:
        """检查路径是否应该被排除"""
        # 排除备份和归档目录
        if self.backup_path in path.parents or self.archive_path in path.parents:
            return True
        
        # 排除路径本身
        if path == self.backup_path or path == self.archive_path:
            return True
        
        # 排除 __pycache__
        if "__pycache__" in path.parts:
            return True
        
        # 排除 .git
        if ".git" in path.parts:
            return True
        
        # 排除 .pyc 文件
        if path.suffix == ".pyc":
            return True
        
        return False
    
    def create_backup(self, description: str = "") -> str:
        """创建备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        
        # 创建备份目录
        backup_dir = self.backup_path / backup_name
        backup_dir.mkdir()
        
        # 需要备份的顶级目录
        include_dirs = [
            "设定集",
            "大纲", 
            "章节",
            ".story-system",
            ".webnovel"
        ]
        
        file_count = 0
        
        for dir_name in include_dirs:
            src_dir = self.project_path / dir_name
            if not src_dir.exists():
                continue
            
            dest_dir = backup_dir / dir_name
            dest_dir.mkdir(exist_ok=True)
            
            # 递归复制
            file_count += self._copy_dir(src_dir, dest_dir)
        
        # 创建备份信息文件
        backup_info = {
            "name": backup_name,
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "file_count": file_count,
            "project_name": self.project_path.name,
            "version": "6.0.0"
        }
        
        with open(backup_dir / "backup_info.json", 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, ensure_ascii=False, indent=2)
        
        # 清理旧备份
        self._cleanup_old_backups()
        
        return str(backup_dir)
    
    def _copy_dir(self, src_dir: Path, dest_dir: Path) -> int:
        """递归复制目录，返回复制的文件数"""
        file_count = 0
        
        for item in src_dir.iterdir():
            # 检查是否排除
            if self._is_excluded(item):
                continue
            
            dest_item = dest_dir / item.name
            
            if item.is_file():
                shutil.copy2(item, dest_item)
                file_count += 1
            elif item.is_dir():
                dest_item.mkdir(exist_ok=True)
                file_count += self._copy_dir(item, dest_item)
        
        return file_count
    
    def _cleanup_old_backups(self):
        """清理旧备份"""
        keep_count = self.config["keep_backups"]
        
        # 获取所有备份目录
        backups = sorted(
            [d for d in self.backup_path.iterdir() if d.is_dir() and d.name.startswith("backup_")],
            key=lambda x: x.name,
            reverse=True
        )
        
        # 删除超过保留数量的旧备份
        for backup in backups[keep_count:]:
            shutil.rmtree(backup)
    
    def create_archive(self, description: str = "") -> str:
        """创建归档（压缩包）"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"archive_{timestamp}.zip"
        archive_path = self.archive_path / archive_name
        
        # 需要备份的顶级目录
        include_dirs = [
            "设定集",
            "大纲", 
            "章节",
            ".story-system",
            ".webnovel"
        ]
        
        file_count = 0
        
        # 创建 ZIP 文件
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for dir_name in include_dirs:
                src_dir = self.project_path / dir_name
                if not src_dir.exists():
                    continue
                
                for item in src_dir.rglob("*"):
                    if self._is_excluded(item):
                        continue
                    
                    if item.is_file():
                        rel_path = item.relative_to(self.project_path)
                        zipf.write(item, rel_path)
                        file_count += 1
            
            # 添加归档信息
            archive_info = {
                "name": archive_name,
                "timestamp": datetime.now().isoformat(),
                "description": description,
                "file_count": file_count,
                "project_name": self.project_path.name,
                "version": "6.0.0"
            }
            zipf.writestr("archive_info.json", json.dumps(archive_info, ensure_ascii=False))
        
        return str(archive_path)
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份"""
        backups = []
        
        for backup_dir in self.backup_path.iterdir():
            if backup_dir.is_dir() and backup_dir.name.startswith("backup_"):
                info_file = backup_dir / "backup_info.json"
                if info_file.exists():
                    with open(info_file, 'r', encoding='utf-8') as f:
                        info = json.load(f)
                    backups.append(info)
        
        return sorted(backups, key=lambda x: x["timestamp"], reverse=True)
    
    def list_archives(self) -> List[Dict[str, Any]]:
        """列出所有归档"""
        archives = []
        
        for archive_file in self.archive_path.glob("archive_*.zip"):
            try:
                with zipfile.ZipFile(archive_file, 'r') as zipf:
                    if "archive_info.json" in zipf.namelist():
                        info = json.loads(zipf.read("archive_info.json").decode('utf-8'))
                        info["file_size"] = archive_file.stat().st_size
                        archives.append(info)
            except:
                pass
        
        return sorted(archives, key=lambda x: x["timestamp"], reverse=True)
    
    def restore_backup(self, backup_name: str) -> bool:
        """从备份恢复"""
        backup_dir = self.backup_path / backup_name
        
        if not backup_dir.exists() or not backup_dir.is_dir():
            return False
        
        # 递归复制回项目目录
        for item in backup_dir.iterdir():
            if item.name == "backup_info.json":
                continue
            
            dest_item = self.project_path / item.name
            
            if item.is_file():
                shutil.copy2(item, dest_item)
            elif item.is_dir():
                if dest_item.exists():
                    shutil.rmtree(dest_item)
                shutil.copytree(item, dest_item)
        
        return True
    
    def restore_archive(self, archive_name: str) -> bool:
        """从归档恢复"""
        archive_path = self.archive_path / archive_name
        
        if not archive_path.exists():
            return False
        
        try:
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                zipf.extractall(self.project_path)
            return True
        except:
            return False
    
    def delete_backup(self, backup_name: str) -> bool:
        """删除备份"""
        backup_dir = self.backup_path / backup_name
        
        if backup_dir.exists() and backup_dir.is_dir():
            shutil.rmtree(backup_dir)
            return True
        
        return False
    
    def delete_archive(self, archive_name: str) -> bool:
        """删除归档"""
        archive_path = self.archive_path / archive_name
        
        if archive_path.exists():
            archive_path.unlink()
            return True
        
        return False
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """获取备份统计信息"""
        backups = self.list_backups()
        archives = self.list_archives()
        
        total_backup_size = 0
        for b in backups:
            backup_dir = self.backup_path / b["name"]
            if backup_dir.exists():
                for f in backup_dir.rglob("*"):
                    if f.is_file():
                        total_backup_size += f.stat().st_size
        
        total_archive_size = sum(a.get("file_size", 0) for a in archives)
        
        return {
            "backup_count": len(backups),
            "archive_count": len(archives),
            "total_backup_size": total_backup_size,
            "total_archive_size": total_archive_size,
            "auto_backup_enabled": self.config["auto_backup"],
            "backup_interval_hours": self.config["backup_interval_hours"],
            "keep_backups": self.config["keep_backups"]
        }