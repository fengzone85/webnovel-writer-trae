#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Config Synchronizer - 配置文件同步模块
支持：环境变量处理、配置模板、配置差异合并
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any

class ConfigSynchronizer:
    """配置同步器"""
    
    def __init__(self, config: Dict[str, Any], log):
        self.config = config
        self.source_path = Path(config['source_path']).resolve()
        self.target_path = Path(config['target_path']).resolve()
        self.log = log
        
        # 配置文件列表
        self.config_files = [
            'package.json',
            'package-lock.json',
            'requirements.txt',
            'pyproject.toml',
            'setup.py',
            'setup.cfg',
            '.env',
            '.env.example',
            'config.json',
            'settings.json',
            '.trae/config.json'
        ]
        
        # 环境变量映射
        self.env_mappings = {
            'development': {},
            'staging': {},
            'production': {}
        }
        
        self.stats = {
            'files_synchronized': 0,
            'files_updated': 0,
            'templates_generated': 0,
            'errors': []
        }
    
    def _load_json_config(self, file_path: Path) -> Dict[str, Any]:
        """加载 JSON 配置文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.log.warning(f"加载配置文件失败 {file_path}: {str(e)}")
            return {}
    
    def _save_json_config(self, file_path: Path, data: Dict[str, Any]):
        """保存 JSON 配置文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log.error(f"保存配置文件失败 {file_path}: {str(e)}")
    
    def _merge_configs(self, source: Dict[str, Any], target: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置（深度合并）"""
        result = target.copy()
        
        for key, value in source.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(value, result[key])
            else:
                result[key] = value
        
        return result
    
    def _process_env_file(self, source_file: Path, target_file: Path):
        """处理环境变量文件"""
        try:
            # 读取源文件
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 如果目标存在，进行差异处理
            if target_file.exists():
                with open(target_file, 'r', encoding='utf-8') as f:
                    target_content = f.read()
                
                # 合并内容（保留目标文件中的自定义值）
                source_lines = {line.split('=')[0].strip(): line for line in content.split('\n') if '=' in line}
                target_lines = {line.split('=')[0].strip(): line for line in target_lines.split('\n') if '=' in line}
                
                # 合并：目标值优先
                merged_lines = {**source_lines, **target_lines}
                merged_content = '\n'.join(merged_lines.values())
                
                with open(target_file, 'w', encoding='utf-8') as f:
                    f.write(merged_content)
                
                self.stats['files_updated'] += 1
                self.log.debug(f"合并环境配置: {target_file}")
            
            else:
                # 直接复制
                shutil.copy2(source_file, target_file)
                self.stats['files_synchronized'] += 1
                self.log.debug(f"同步环境配置: {source_file} -> {target_file}")
                
        except Exception as e:
            error = f"处理环境文件失败 {source_file}: {str(e)}"
            self.log.error(error)
            self.stats['errors'].append(error)
    
    def _process_package_json(self, source_file: Path, target_file: Path):
        """处理 package.json"""
        try:
            source_config = self._load_json_config(source_file)
            
            if target_file.exists():
                target_config = self._load_json_config(target_file)
                merged = self._merge_configs(source_config, target_config)
                
                # 更新脚本命令
                if 'scripts' in source_config:
                    merged['scripts'] = source_config['scripts']
                
                self._save_json_config(target_file, merged)
                self.stats['files_updated'] += 1
                self.log.debug(f"更新 package.json: {target_file}")
            
            else:
                shutil.copy2(source_file, target_file)
                self.stats['files_synchronized'] += 1
                self.log.debug(f"同步 package.json: {source_file} -> {target_file}")
                
        except Exception as e:
            error = f"处理 package.json 失败: {str(e)}"
            self.log.error(error)
            self.stats['errors'].append(error)
    
    def _generate_env_template(self, source_file: Path):
        """生成环境变量模板"""
        template_file = self.target_path / '.env.template'
        
        if source_file.exists():
            shutil.copy2(source_file, template_file)
            self.stats['templates_generated'] += 1
            self.log.debug(f"生成环境模板: {template_file}")
    
    def synchronize(self) -> Dict[str, Any]:
        """执行配置同步"""
        self.log.info("开始配置文件同步...")
        
        try:
            for config_file in self.config_files:
                source_file = self.source_path / config_file
                
                if not source_file.exists():
                    continue
                
                target_file = self.target_path / config_file
                
                # 根据文件类型进行处理
                if config_file == 'package.json':
                    self._process_package_json(source_file, target_file)
                elif config_file == '.env':
                    self._process_env_file(source_file, target_file)
                    self._generate_env_template(source_file)
                else:
                    # 其他配置文件直接复制
                    shutil.copy2(source_file, target_file)
                    self.stats['files_synchronized'] += 1
                    self.log.debug(f"同步配置: {source_file} -> {target_file}")
            
            self.log.info(f"配置同步完成")
            self.log.info(f"  - 同步文件: {self.stats['files_synchronized']}")
            self.log.info(f"  - 更新文件: {self.stats['files_updated']}")
            self.log.info(f"  - 生成模板: {self.stats['templates_generated']}")
            
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