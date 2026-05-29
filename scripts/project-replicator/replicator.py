#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project Replicator - 全面项目复制系统
支持：源码复制、配置同步、依赖管理、数据库复制、验证检查、版本控制集成
"""

import os
import sys
import json
import shutil
import subprocess
import hashlib
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from file_replicator import FileReplicator
from config_synchronizer import ConfigSynchronizer
from dependency_manager import DependencyManager
from database_replicator import DatabaseReplicator
from validation_checker import ValidationChecker
from version_control import VersionControlIntegration
from utils import setup_logging, get_project_info

class ProjectReplicator:
    """主复制器类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.source_path = Path(config['source_path']).resolve()
        self.target_path = Path(config['target_path']).resolve()
        self.replication_id = config.get('replication_id', self._generate_replication_id())
        self.history_path = Path(config.get('history_path', '.replication-history'))
        self.log = setup_logging(f"replicator_{self.replication_id}")
        
        # 初始化子模块
        self.file_replicator = FileReplicator(config, self.log)
        self.config_synchronizer = ConfigSynchronizer(config, self.log)
        self.dependency_manager = DependencyManager(config, self.log)
        self.database_replicator = DatabaseReplicator(config, self.log)
        self.validation_checker = ValidationChecker(config, self.log)
        self.version_control = VersionControlIntegration(config, self.log)
        
        # 复制状态
        self.status = {
            'id': self.replication_id,
            'start_time': None,
            'end_time': None,
            'status': 'pending',
            'steps': [],
            'errors': [],
            'warnings': [],
            'source_info': {},
            'target_info': {},
            'validation_results': {}
        }
    
    def _generate_replication_id(self) -> str:
        """生成唯一复制ID"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        hash_val = hashlib.md5(timestamp.encode()).hexdigest()[:8]
        return f"repl_{timestamp}_{hash_val}"
    
    def _record_step(self, step_name: str, status: str, details: str = ""):
        """记录复制步骤"""
        self.status['steps'].append({
            'step': step_name,
            'status': status,
            'timestamp': datetime.datetime.now().isoformat(),
            'details': details
        })
    
    def _record_error(self, error: str):
        """记录错误"""
        self.status['errors'].append({
            'timestamp': datetime.datetime.now().isoformat(),
            'message': error
        })
    
    def _record_warning(self, warning: str):
        """记录警告"""
        self.status['warnings'].append({
            'timestamp': datetime.datetime.now().isoformat(),
            'message': warning
        })
    
    def _validate_source(self) -> bool:
        """验证源项目"""
        self.log.info("验证源项目...")
        
        if not self.source_path.exists():
            error = f"源路径不存在: {self.source_path}"
            self.log.error(error)
            self._record_error(error)
            return False
        
        if not self.source_path.is_dir():
            error = f"源路径不是目录: {self.source_path}"
            self.log.error(error)
            self._record_error(error)
            return False
        
        # 检查必要文件
        required_files = ['package.json', 'README.md']
        missing_files = []
        for f in required_files:
            if not (self.source_path / f).exists():
                missing_files.append(f)
        
        if missing_files:
            warning = f"缺少可选文件: {', '.join(missing_files)}"
            self.log.warning(warning)
            self._record_warning(warning)
        
        return True
    
    def _prepare_target(self) -> bool:
        """准备目标目录"""
        self.log.info(f"准备目标目录: {self.target_path}")
        
        try:
            if self.target_path.exists():
                # 如果目标已存在，根据配置决定是否覆盖
                if self.config.get('overwrite_existing', False):
                    self.log.warning(f"目标目录已存在，将被覆盖: {self.target_path}")
                    shutil.rmtree(self.target_path)
                else:
                    error = f"目标目录已存在: {self.target_path}。请设置 overwrite_existing=true 或选择其他路径。"
                    self.log.error(error)
                    self._record_error(error)
                    return False
            
            self.target_path.mkdir(parents=True, exist_ok=True)
            self.log.info(f"目标目录已创建: {self.target_path}")
            return True
            
        except Exception as e:
            error = f"创建目标目录失败: {str(e)}"
            self.log.error(error)
            self._record_error(error)
            return False
    
    def replicate(self) -> Dict[str, Any]:
        """执行完整复制流程"""
        self.status['start_time'] = datetime.datetime.now().isoformat()
        self.status['status'] = 'running'
        
        self.log.info("="*60)
        self.log.info(f"开始项目复制 - ID: {self.replication_id}")
        self.log.info(f"源路径: {self.source_path}")
        self.log.info(f"目标路径: {self.target_path}")
        self.log.info("="*60)
        
        try:
            # 1. 验证源项目
            if not self._validate_source():
                self.status['status'] = 'failed'
                return self.status
            
            # 2. 准备目标目录
            if not self._prepare_target():
                self.status['status'] = 'failed'
                return self.status
            
            # 3. 获取源项目信息
            self.status['source_info'] = get_project_info(self.source_path)
            self.log.info(f"源项目信息: {json.dumps(self.status['source_info'], ensure_ascii=False, indent=2)}")
            
            # 4. 复制文件系统
            self._record_step('file_replication', 'running')
            file_result = self.file_replicator.replicate()
            self._record_step('file_replication', file_result['status'], str(file_result))
            
            if file_result['status'] == 'failed':
                self._record_error(f"文件复制失败: {file_result.get('error')}")
                self.status['status'] = 'failed'
                return self.status
            
            # 5. 同步配置文件
            self._record_step('config_synchronization', 'running')
            config_result = self.config_synchronizer.synchronize()
            self._record_step('config_synchronization', config_result['status'], str(config_result))
            
            if config_result['status'] == 'failed':
                self._record_error(f"配置同步失败: {config_result.get('error')}")
                self.status['status'] = 'failed'
                return self.status
            
            # 6. 管理依赖
            self._record_step('dependency_management', 'running')
            dep_result = self.dependency_manager.install()
            self._record_step('dependency_management', dep_result['status'], str(dep_result))
            
            if dep_result['status'] == 'failed':
                self._record_error(f"依赖安装失败: {dep_result.get('error')}")
                self.status['status'] = 'failed'
                return self.status
            
            # 7. 复制数据库
            if self.config.get('include_database', True):
                self._record_step('database_replication', 'running')
                db_result = self.database_replicator.replicate()
                self._record_step('database_replication', db_result['status'], str(db_result))
                
                if db_result['status'] == 'failed':
                    self._record_warning(f"数据库复制失败（非致命）: {db_result.get('error')}")
            
            # 8. 验证复制结果
            self._record_step('validation', 'running')
            validation_result = self.validation_checker.validate()
            self._record_step('validation', validation_result['status'], str(validation_result))
            self.status['validation_results'] = validation_result
            
            if validation_result['status'] == 'failed':
                self._record_warning(f"验证未完全通过: {validation_result.get('issues')}")
            
            # 9. 版本控制集成
            if self.config.get('version_control', True):
                self._record_step('version_control', 'running')
                vc_result = self.version_control.setup()
                self._record_step('version_control', vc_result['status'], str(vc_result))
                
                if vc_result['status'] == 'failed':
                    self._record_warning(f"版本控制设置失败: {vc_result.get('error')}")
            
            # 10. 保存复制历史
            self._save_replication_history()
            
            # 更新目标项目信息
            self.status['target_info'] = get_project_info(self.target_path)
            
            # 完成
            self.status['status'] = 'completed'
            self.log.info("="*60)
            self.log.info("项目复制完成！")
            self.log.info(f"复制ID: {self.replication_id}")
            self.log.info(f"目标位置: {self.target_path}")
            self.log.info("="*60)
            
        except Exception as e:
            error = f"复制过程发生未预期错误: {str(e)}"
            self.log.error(error)
            self._record_error(error)
            self.status['status'] = 'failed'
        
        finally:
            self.status['end_time'] = datetime.datetime.now().isoformat()
        
        return self.status
    
    def _save_replication_history(self):
        """保存复制历史记录"""
        try:
            self.history_path.mkdir(parents=True, exist_ok=True)
            history_file = self.history_path / f"{self.replication_id}.json"
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.status, f, ensure_ascii=False, indent=2)
            
            # 更新索引文件
            index_file = self.history_path / 'index.json'
            if index_file.exists():
                with open(index_file, 'r', encoding='utf-8') as f:
                    index = json.load(f)
            else:
                index = []
            
            index.append({
                'id': self.replication_id,
                'source': str(self.source_path),
                'target': str(self.target_path),
                'status': self.status['status'],
                'timestamp': self.status['start_time']
            })
            
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, ensure_ascii=False, indent=2)
            
            self.log.info(f"复制历史已保存: {history_file}")
            
        except Exception as e:
            self.log.warning(f"保存复制历史失败: {str(e)}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前复制状态"""
        return self.status
    
    def get_replication_history(self) -> List[Dict[str, Any]]:
        """获取复制历史记录"""
        index_file = self.history_path / 'index.json'
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Project Replicator - 全面项目复制系统")
    parser.add_argument("source", help="源项目路径")
    parser.add_argument("target", help="目标路径")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已存在的目标目录")
    parser.add_argument("--skip-db", action="store_true", help="跳过数据库复制")
    parser.add_argument("--skip-vc", action="store_true", help="跳过版本控制设置")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    # 构建配置
    config = {
        'source_path': args.source,
        'target_path': args.target,
        'overwrite_existing': args.overwrite,
        'include_database': not args.skip_db,
        'version_control': not args.skip_vc,
        'verbose': args.verbose
    }
    
    # 加载外部配置
    if args.config:
        with open(args.config, 'r', encoding='utf-8') as f:
            config.update(json.load(f))
    
    # 创建并执行复制器
    replicator = ProjectReplicator(config)
    result = replicator.replicate()
    
    # 输出结果
    print("\n" + "="*60)
    print(f"复制结果: {result['status'].upper()}")
    print(f"复制ID: {result['id']}")
    print(f"源路径: {result['source_info'].get('path', 'N/A')}")
    print(f"目标路径: {result['target_info'].get('path', 'N/A')}")
    
    if result['errors']:
        print("\n❌ 错误:")
        for err in result['errors']:
            print(f"  - {err['message']}")
    
    if result['warnings']:
        print("\n⚠️ 警告:")
        for warn in result['warnings']:
            print(f"  - {warn['message']}")
    
    # 验证结果摘要
    if result['validation_results']:
        vr = result['validation_results']
        print(f"\n✅ 验证结果: {vr.get('status', 'N/A')}")
        if vr.get('checks'):
            for check in vr['checks']:
                status = "✓" if check['passed'] else "✗"
                print(f"  {status} {check['name']}: {check['message']}")
    
    print("="*60)
    
    return 0 if result['status'] == 'completed' else 1

if __name__ == "__main__":
    sys.exit(main())