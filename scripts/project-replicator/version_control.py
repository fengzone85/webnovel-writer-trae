#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Version Control Integration - 版本控制集成模块
支持：Git 仓库初始化、提交历史记录、分支管理
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, Any

class VersionControlIntegration:
    """版本控制集成"""
    
    def __init__(self, config: Dict[str, Any], log):
        self.config = config
        self.source_path = Path(config['source_path']).resolve()
        self.target_path = Path(config['target_path']).resolve()
        self.log = log
        
        # 源项目是否有 git 仓库
        self.source_has_git = (self.source_path / '.git').exists()
        
        self.stats = {
            'repository_created': False,
            'initial_commit_made': False,
            'branches_created': 0,
            'tags_created': 0,
            'errors': []
        }
    
    def _run_git_command(self, command: str) -> Dict[str, Any]:
        """运行 git 命令"""
        self.log.debug(f"执行 git 命令: {command}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.target_path,
                capture_output=True,
                text=True
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }
    
    def _initialize_repository(self) -> Dict[str, Any]:
        """初始化 git 仓库"""
        self.log.info("初始化 git 仓库...")
        
        # 检查是否已存在 git 仓库
        if (self.target_path / '.git').exists():
            self.log.info("目标目录已存在 git 仓库")
            return {'success': True, 'message': '已存在 git 仓库'}
        
        # 初始化仓库
        result = self._run_git_command('git init')
        
        if result['success']:
            self.stats['repository_created'] = True
            self.log.info("git 仓库初始化成功")
            return {'success': True, 'message': 'git 仓库初始化成功'}
        else:
            self.stats['errors'].append(result['stderr'])
            self.log.error(f"git 仓库初始化失败: {result['stderr']}")
            return {'success': False, 'error': result['stderr']}
    
    def _configure_git(self) -> Dict[str, Any]:
        """配置 git 用户信息"""
        self.log.info("配置 git 用户信息...")
        
        # 读取源项目的 git 配置
        if self.source_has_git:
            result = subprocess.run(
                'git config --get user.name',
                shell=True,
                cwd=self.source_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                self._run_git_command(f'git config user.name "{result.stdout.strip()}"')
            
            result = subprocess.run(
                'git config --get user.email',
                shell=True,
                cwd=self.source_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                self._run_git_command(f'git config user.email "{result.stdout.strip()}"')
        
        # 设置默认配置
        self._run_git_command('git config user.name "Project Replicator"')
        self._run_git_command('git config user.email "replicator@example.com"')
        
        # 设置其他配置
        self._run_git_command('git config core.autocrlf true')
        self._run_git_command('git config core.ignorecase true')
        
        return {'success': True}
    
    def _create_initial_commit(self) -> Dict[str, Any]:
        """创建初始提交"""
        self.log.info("创建初始提交...")
        
        # 添加所有文件
        result = self._run_git_command('git add .')
        if not result['success']:
            self.stats['errors'].append(result['stderr'])
            return {'success': False, 'error': result['stderr']}
        
        # 创建提交
        result = self._run_git_command('git commit -m "Initial commit - Project replicated"')
        
        if result['success']:
            self.stats['initial_commit_made'] = True
            self.log.info("初始提交创建成功")
            return {'success': True, 'message': '初始提交创建成功'}
        else:
            # 如果没有需要提交的内容
            if "nothing to commit" in result.stderr:
                self.log.info("没有需要提交的内容")
                return {'success': True, 'message': '没有需要提交的内容'}
            
            self.stats['errors'].append(result['stderr'])
            self.log.error(f"创建初始提交失败: {result['stderr']}")
            return {'success': False, 'error': result['stderr']}
    
    def _create_replication_tag(self) -> Dict[str, Any]:
        """创建复制版本标签"""
        self.log.info("创建复制版本标签...")
        
        replication_id = self.config.get('replication_id', 'unknown')
        tag_name = f"replication/{replication_id}"
        
        result = self._run_git_command(f'git tag {tag_name}')
        
        if result['success']:
            self.stats['tags_created'] += 1
            self.log.info(f"创建标签: {tag_name}")
            return {'success': True, 'tag': tag_name}
        else:
            self.log.warning(f"创建标签失败: {result['stderr']}")
            return {'success': False, 'error': result['stderr']}
    
    def _create_branches(self) -> Dict[str, Any]:
        """创建默认分支"""
        self.log.info("创建默认分支...")
        
        branches = ['develop', 'feature/replication']
        created_count = 0
        
        for branch in branches:
            result = self._run_git_command(f'git checkout -b {branch}')
            if result['success']:
                created_count += 1
                self.log.info(f"创建分支: {branch}")
        
        # 切换回主分支
        self._run_git_command('git checkout master')
        
        self.stats['branches_created'] = created_count
        return {'success': True, 'branches': created_count}
    
    def _save_replication_metadata(self) -> Dict[str, Any]:
        """保存复制元数据"""
        self.log.info("保存复制元数据...")
        
        metadata = {
            'replication_id': self.config.get('replication_id', 'unknown'),
            'source_path': str(self.source_path),
            'target_path': str(self.target_path),
            'timestamp': self.config.get('timestamp', ''),
            'version': '1.0.0'
        }
        
        # 创建 .replication 目录
        replication_dir = self.target_path / '.replication'
        replication_dir.mkdir(exist_ok=True)
        
        # 保存元数据
        with open(replication_dir / 'metadata.json', 'w', encoding='utf-8') as f:
            import json
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # 添加到 git
        self._run_git_command('git add .replication/')
        self._run_git_command('git commit -m "Add replication metadata" --no-verify')
        
        self.log.info("复制元数据保存成功")
        return {'success': True}
    
    def setup(self) -> Dict[str, Any]:
        """设置版本控制"""
        self.log.info("开始版本控制集成...")
        
        try:
            # 1. 初始化仓库
            init_result = self._initialize_repository()
            if not init_result['success']:
                return {
                    'status': 'failed',
                    'error': init_result.get('error'),
                    'stats': self.stats
                }
            
            # 2. 配置 git
            self._configure_git()
            
            # 3. 创建初始提交
            commit_result = self._create_initial_commit()
            if not commit_result['success']:
                return {
                    'status': 'failed',
                    'error': commit_result.get('error'),
                    'stats': self.stats
                }
            
            # 4. 创建标签
            self._create_replication_tag()
            
            # 5. 创建分支
            self._create_branches()
            
            # 6. 保存复制元数据
            self._save_replication_metadata()
            
            self.log.info(f"版本控制设置完成")
            self.log.info(f"  - 仓库创建: {'是' if self.stats['repository_created'] else '否'}")
            self.log.info(f"  - 初始提交: {'是' if self.stats['initial_commit_made'] else '否'}")
            self.log.info(f"  - 创建分支: {self.stats['branches_created']}")
            self.log.info(f"  - 创建标签: {self.stats['tags_created']}")
            
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
    
    def get_repository_info(self) -> Dict[str, Any]:
        """获取仓库信息"""
        info = {}
        
        # 获取当前分支
        result = self._run_git_command('git branch --show-current')
        if result['success']:
            info['current_branch'] = result['stdout'].strip()
        
        # 获取提交数
        result = self._run_git_command('git rev-list --count HEAD')
        if result['success']:
            info['commit_count'] = int(result['stdout'].strip())
        
        # 获取标签列表
        result = self._run_git_command('git tag -l')
        if result['success']:
            info['tags'] = [t.strip() for t in result['stdout'].split('\n') if t.strip()]
        
        return info