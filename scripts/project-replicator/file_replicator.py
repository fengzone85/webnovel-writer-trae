#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Replicator - 文件系统复制模块
支持：源码复制、目录结构保持、过滤规则、符号链接处理
"""

import os
import shutil
import fnmatch
from pathlib import Path
from typing import Dict, List, Any

class FileReplicator:
    """文件复制器"""
    
    def __init__(self, config: Dict[str, Any], log):
        self.config = config
        self.source_path = Path(config['source_path']).resolve()
        self.target_path = Path(config['target_path']).resolve()
        self.log = log
        
        # 默认过滤规则
        self.default_excludes = [
            # 版本控制
            '.git/', '.svn/', '.hg/', '.gitignore', '.gitattributes',
            # 依赖目录
            'node_modules/', 'venv/', '.venv/', '__pycache__/', '*.pyc', '*.pyo',
            # 构建产物
            'dist/', 'build/', 'out/', '*.log',
            # 编辑器
            '.vscode/', '.idea/', '.trae/', '*.swp', '*.swo',
            # 操作系统
            'Thumbs.db', '.DS_Store',
            # 临时文件
            '*.tmp', '*.bak', '*.backup'
        ]
        
        # 自定义过滤规则
        self.excludes = self.config.get('exclude_patterns', []) + self.default_excludes
        self.includes = self.config.get('include_patterns', [])
        
        # 统计信息
        self.stats = {
            'files_copied': 0,
            'directories_created': 0,
            'symlinks_handled': 0,
            'files_skipped': 0,
            'errors': []
        }
    
    def _should_copy(self, relative_path: str) -> bool:
        """判断是否应该复制文件"""
        # 检查包含规则（优先）
        for pattern in self.includes:
            if fnmatch.fnmatch(relative_path, pattern):
                return True
        
        # 检查排除规则
        for pattern in self.excludes:
            if fnmatch.fnmatch(relative_path, pattern) or \
               fnmatch.fnmatch(os.path.basename(relative_path), pattern):
                return False
        
        return True
    
    def _copy_file(self, source_file: Path, target_file: Path):
        """复制单个文件"""
        try:
            # 确保目标目录存在
            target_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 处理符号链接
            if source_file.is_symlink():
                target_link = os.readlink(source_file)
                if os.path.isabs(target_link):
                    # 绝对路径链接，转换为相对路径或跳过
                    self.log.warning(f"跳过绝对路径符号链接: {source_file}")
                    self.stats['files_skipped'] += 1
                else:
                    # 创建相对路径链接
                    target_file.symlink_to(target_link)
                    self.stats['symlinks_handled'] += 1
                    self.log.debug(f"创建符号链接: {source_file} -> {target_file}")
            
            else:
                # 复制文件内容
                shutil.copy2(source_file, target_file)
                self.stats['files_copied'] += 1
                self.log.debug(f"复制文件: {source_file} -> {target_file}")
                
        except Exception as e:
            error = f"复制文件失败 {source_file}: {str(e)}"
            self.log.error(error)
            self.stats['errors'].append(error)
    
    def _copy_directory(self, source_dir: Path, target_dir: Path):
        """递归复制目录"""
        try:
            # 确保目标目录存在
            target_dir.mkdir(parents=True, exist_ok=True)
            self.stats['directories_created'] += 1
            
            # 遍历目录内容
            for item in source_dir.iterdir():
                relative_path = item.relative_to(self.source_path)
                relative_path_str = str(relative_path).replace('\\', '/')
                
                # 检查过滤规则
                if not self._should_copy(relative_path_str):
                    self.log.debug(f"跳过: {relative_path_str}")
                    self.stats['files_skipped'] += 1
                    continue
                
                target_item = target_dir / relative_path
                
                if item.is_dir():
                    self._copy_directory(item, target_item)
                else:
                    self._copy_file(item, target_item)
                    
        except Exception as e:
            error = f"复制目录失败 {source_dir}: {str(e)}"
            self.log.error(error)
            self.stats['errors'].append(error)
    
    def replicate(self) -> Dict[str, Any]:
        """执行文件复制"""
        self.log.info("开始文件系统复制...")
        self.log.info(f"源目录: {self.source_path}")
        self.log.info(f"目标目录: {self.target_path}")
        
        try:
            # 开始递归复制
            self._copy_directory(self.source_path, self.target_path)
            
            # 输出统计
            self.log.info(f"文件复制完成")
            self.log.info(f"  - 复制文件: {self.stats['files_copied']}")
            self.log.info(f"  - 创建目录: {self.stats['directories_created']}")
            self.log.info(f"  - 处理符号链接: {self.stats['symlinks_handled']}")
            self.log.info(f"  - 跳过文件: {self.stats['files_skipped']}")
            
            if self.stats['errors']:
                return {
                    'status': 'completed_with_errors',
                    'stats': self.stats,
                    'errors': self.stats['errors']
                }
            else:
                return {
                    'status': 'completed',
                    'stats': self.stats
                }
                
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'stats': self.stats
            }