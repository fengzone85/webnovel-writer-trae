#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Replicator - 数据库复制模块
支持：SQLite、MySQL、PostgreSQL 数据库复制、数据迁移
"""

import os
import shutil
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List

class DatabaseReplicator:
    """数据库复制器"""
    
    def __init__(self, config: Dict[str, Any], log):
        self.config = config
        self.source_path = Path(config['source_path']).resolve()
        self.target_path = Path(config['target_path']).resolve()
        self.log = log
        
        # 数据库配置
        self.db_config = config.get('database', {})
        self.stats = {
            'databases_found': 0,
            'databases_copied': 0,
            'tables_copied': 0,
            'rows_copied': 0,
            'errors': []
        }
    
    def _detect_databases(self) -> List[Dict[str, Any]]:
        """检测项目中的数据库文件"""
        databases = []
        
        # 查找 SQLite 数据库
        for db_file in self.source_path.rglob('*.db'):
            if not str(db_file).endswith('_test.db'):  # 跳过测试数据库
                databases.append({
                    'type': 'sqlite',
                    'path': db_file,
                    'name': db_file.name
                })
        
        # 查找 JSON 数据文件
        for json_file in self.source_path.rglob('*.json'):
            if 'data' in json_file.name.lower() or 'db' in json_file.name.lower():
                databases.append({
                    'type': 'json',
                    'path': json_file,
                    'name': json_file.name
                })
        
        # 查找 data 目录
        data_dirs = ['data', 'database', 'db', '.webnovel']
        for dir_name in data_dirs:
            data_path = self.source_path / dir_name
            if data_path.is_dir():
                databases.append({
                    'type': 'directory',
                    'path': data_path,
                    'name': dir_name
                })
        
        return databases
    
    def _copy_sqlite_database(self, source_db: Path, target_db: Path):
        """复制 SQLite 数据库"""
        try:
            # 确保目标目录存在
            target_db.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制数据库文件
            shutil.copy2(source_db, target_db)
            self.stats['databases_copied'] += 1
            
            # 尝试获取表信息
            try:
                result = subprocess.run(
                    ['sqlite3', str(target_db), ".tables"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    tables = [t.strip() for t in result.stdout.split() if t.strip()]
                    self.stats['tables_copied'] += len(tables)
                    
                    # 获取行数
                    total_rows = 0
                    for table in tables:
                        count_result = subprocess.run(
                            ['sqlite3', str(target_db), f"SELECT COUNT(*) FROM {table};"],
                            capture_output=True,
                            text=True
                        )
                        if count_result.returncode == 0:
                            total_rows += int(count_result.stdout.strip())
                    
                    self.stats['rows_copied'] += total_rows
                
                self.log.info(f"复制 SQLite 数据库: {source_db.name} -> {target_db.name}")
                
            except Exception as e:
                self.log.warning(f"无法获取 SQLite 表信息: {str(e)}")
                
        except Exception as e:
            error = f"复制 SQLite 数据库失败 {source_db}: {str(e)}"
            self.log.error(error)
            self.stats['errors'].append(error)
    
    def _copy_json_database(self, source_file: Path, target_file: Path):
        """复制 JSON 数据文件"""
        try:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, target_file)
            
            # 统计数据
            with open(source_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                self.stats['rows_copied'] += len(data)
            elif isinstance(data, dict):
                self.stats['rows_copied'] += len(data)
            
            self.stats['databases_copied'] += 1
            self.log.info(f"复制 JSON 数据: {source_file.name} -> {target_file.name}")
            
        except Exception as e:
            error = f"复制 JSON 数据失败 {source_file}: {str(e)}"
            self.log.error(error)
            self.stats['errors'].append(error)
    
    def _copy_data_directory(self, source_dir: Path, target_dir: Path):
        """复制数据目录"""
        try:
            if target_dir.exists():
                shutil.rmtree(target_dir)
            
            shutil.copytree(source_dir, target_dir)
            self.stats['databases_copied'] += 1
            
            # 统计文件数量
            file_count = sum(1 for _ in target_dir.rglob('*') if _.is_file())
            self.log.info(f"复制数据目录: {source_dir.name} -> {target_dir.name} ({file_count} 个文件)")
            
        except Exception as e:
            error = f"复制数据目录失败 {source_dir}: {str(e)}"
            self.log.error(error)
            self.stats['errors'].append(error)
    
    def replicate(self) -> Dict[str, Any]:
        """执行数据库复制"""
        self.log.info("开始数据库复制...")
        
        try:
            databases = self._detect_databases()
            self.stats['databases_found'] = len(databases)
            
            if not databases:
                self.log.info("未检测到数据库文件")
                return {
                    'status': 'completed',
                    'message': '未检测到数据库文件',
                    'stats': self.stats
                }
            
            self.log.info(f"检测到 {len(databases)} 个数据库/数据文件")
            
            for db in databases:
                relative_path = db['path'].relative_to(self.source_path)
                target_path = self.target_path / relative_path
                
                if db['type'] == 'sqlite':
                    self._copy_sqlite_database(db['path'], target_path)
                elif db['type'] == 'json':
                    self._copy_json_database(db['path'], target_path)
                elif db['type'] == 'directory':
                    self._copy_data_directory(db['path'], target_path)
            
            self.log.info(f"数据库复制完成")
            self.log.info(f"  - 发现数据库: {self.stats['databases_found']}")
            self.log.info(f"  - 复制数据库: {self.stats['databases_copied']}")
            self.log.info(f"  - 复制表数: {self.stats['tables_copied']}")
            self.log.info(f"  - 复制行数: {self.stats['rows_copied']}")
            
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