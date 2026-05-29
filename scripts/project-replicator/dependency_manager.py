#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dependency Manager - 依赖管理模块
支持：npm/yarn/pip 依赖安装、版本锁定、依赖检查
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List

class DependencyManager:
    """依赖管理器"""
    
    def __init__(self, config: Dict[str, Any], log):
        self.config = config
        self.source_path = Path(config['source_path']).resolve()
        self.target_path = Path(config['target_path']).resolve()
        self.log = log
        
        # 依赖类型检测
        self.dependency_types = []
        self.stats = {
            'npm_installed': False,
            'pip_installed': False,
            'npm_errors': [],
            'pip_errors': [],
            'npm_packages': 0,
            'pip_packages': 0
        }
    
    def _detect_dependency_types(self) -> List[str]:
        """检测项目依赖类型"""
        types = []
        
        if (self.target_path / 'package.json').exists():
            types.append('npm')
        
        if (self.target_path / 'requirements.txt').exists():
            types.append('pip')
        
        if (self.target_path / 'pyproject.toml').exists():
            types.append('pip')
        
        return types
    
    def _run_command(self, command: str, cwd: Path) -> Dict[str, Any]:
        """运行命令并返回结果"""
        self.log.debug(f"执行命令: {command}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': '命令执行超时',
                'returncode': -1
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -2
            }
    
    def _install_npm_dependencies(self) -> Dict[str, Any]:
        """安装 npm 依赖"""
        self.log.info("安装 npm 依赖...")
        
        package_json_path = self.target_path / 'package.json'
        if not package_json_path.exists():
            return {'success': True, 'message': '无 package.json，跳过 npm 安装'}
        
        # 读取 package.json 获取依赖数量
        with open(package_json_path, 'r', encoding='utf-8') as f:
            package_data = json.load(f)
        
        deps_count = len(package_data.get('dependencies', {})) + len(package_data.get('devDependencies', {}))
        
        # 检查是否有 package-lock.json
        if (self.target_path / 'package-lock.json').exists():
            command = 'npm ci'
            self.log.info("使用 npm ci 安装（锁定版本）")
        else:
            command = 'npm install'
            self.log.info("使用 npm install 安装")
        
        result = self._run_command(command, self.target_path)
        
        if result['success']:
            self.stats['npm_installed'] = True
            self.stats['npm_packages'] = deps_count
            self.log.info(f"npm 依赖安装成功，共 {deps_count} 个包")
            return {'success': True, 'packages': deps_count}
        else:
            self.stats['npm_errors'].append(result['stderr'])
            self.log.error(f"npm 依赖安装失败: {result['stderr']}")
            return {'success': False, 'error': result['stderr']}
    
    def _install_pip_dependencies(self) -> Dict[str, Any]:
        """安装 pip 依赖"""
        self.log.info("安装 pip 依赖...")
        
        requirements_path = self.target_path / 'requirements.txt'
        
        if not requirements_path.exists():
            return {'success': True, 'message': '无 requirements.txt，跳过 pip 安装'}
        
        # 统计依赖数量
        with open(requirements_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            packages_count = len([line for line in lines if line.strip() and not line.startswith('#')])
        
        # 使用 pip install
        command = f'pip install -r requirements.txt'
        result = self._run_command(command, self.target_path)
        
        if result['success']:
            self.stats['pip_installed'] = True
            self.stats['pip_packages'] = packages_count
            self.log.info(f"pip 依赖安装成功，共 {packages_count} 个包")
            return {'success': True, 'packages': packages_count}
        else:
            self.stats['pip_errors'].append(result['stderr'])
            self.log.error(f"pip 依赖安装失败: {result['stderr']}")
            return {'success': False, 'error': result['stderr']}
    
    def _install_poetry_dependencies(self) -> Dict[str, Any]:
        """安装 Poetry 依赖"""
        self.log.info("安装 Poetry 依赖...")
        
        pyproject_path = self.target_path / 'pyproject.toml'
        if not pyproject_path.exists():
            return {'success': True, 'message': '无 pyproject.toml，跳过 Poetry 安装'}
        
        # 检查是否有 poetry.lock
        if (self.target_path / 'poetry.lock').exists():
            command = 'poetry install'
        else:
            command = 'poetry install --no-interaction'
        
        result = self._run_command(command, self.target_path)
        
        if result['success']:
            self.log.info("Poetry 依赖安装成功")
            return {'success': True}
        else:
            self.log.warning(f"Poetry 安装失败（尝试 pip）: {result['stderr']}")
            return {'success': False, 'error': result['stderr']}
    
    def install(self) -> Dict[str, Any]:
        """执行依赖安装"""
        self.log.info("开始依赖管理...")
        
        try:
            # 检测依赖类型
            dependency_types = self._detect_dependency_types()
            self.log.info(f"检测到依赖类型: {', '.join(dependency_types)}")
            
            results = []
            
            # 安装 npm 依赖
            if 'npm' in dependency_types:
                npm_result = self._install_npm_dependencies()
                results.append(('npm', npm_result))
            
            # 安装 pip 依赖
            if 'pip' in dependency_types:
                pip_result = self._install_pip_dependencies()
                if not pip_result['success']:
                    # 尝试 Poetry
                    poetry_result = self._install_poetry_dependencies()
                    results.append(('poetry', poetry_result))
                else:
                    results.append(('pip', pip_result))
            
            # 检查结果
            all_success = all(r[1]['success'] for r in results)
            
            if all_success:
                self.log.info(f"依赖安装完成")
                self.log.info(f"  - npm 包: {self.stats['npm_packages']}")
                self.log.info(f"  - pip 包: {self.stats['pip_packages']}")
                
                return {
                    'status': 'completed',
                    'stats': self.stats,
                    'results': results
                }
            else:
                # 如果有部分失败，返回警告
                failed_types = [r[0] for r in results if not r[1]['success']]
                self.log.warning(f"部分依赖安装失败: {', '.join(failed_types)}")
                
                return {
                    'status': 'completed_with_warnings',
                    'stats': self.stats,
                    'results': results,
                    'failed_types': failed_types
                }
                
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'stats': self.stats
            }