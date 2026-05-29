#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation Checker - 验证检查模块
支持：功能验证、性能测试、安全检查、配置验证
"""

import os
import json
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List, Any

class ValidationChecker:
    """验证检查器"""
    
    def __init__(self, config: Dict[str, Any], log):
        self.config = config
        self.source_path = Path(config['source_path']).resolve()
        self.target_path = Path(config['target_path']).resolve()
        self.log = log
        
        # 检查项配置
        self.checks = [
            {'name': 'file_structure', 'description': '文件结构完整性', 'required': True},
            {'name': 'config_files', 'description': '配置文件存在性', 'required': True},
            {'name': 'dependency_availability', 'description': '依赖可用性', 'required': True},
            {'name': 'checksum_validation', 'description': '文件校验和验证', 'required': False},
            {'name': 'build_test', 'description': '构建测试', 'required': False},
            {'name': 'security_scan', 'description': '安全扫描', 'required': False},
            {'name': 'performance_check', 'description': '性能检查', 'required': False}
        ]
        
        self.results = {
            'checks': [],
            'passed_count': 0,
            'failed_count': 0,
            'warnings': [],
            'errors': []
        }
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """计算文件校验和"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception:
            return ''
    
    def _check_file_structure(self) -> Dict[str, Any]:
        """检查文件结构完整性"""
        self.log.info("检查文件结构...")
        
        required_dirs = ['章节', '大纲', '设定集', '.story-system', '.webnovel']
        missing_dirs = []
        
        for dir_name in required_dirs:
            if not (self.target_path / dir_name).exists():
                missing_dirs.append(dir_name)
        
        if missing_dirs:
            return {
                'name': 'file_structure',
                'passed': False,
                'message': f"缺少必要目录: {', '.join(missing_dirs)}",
                'severity': 'error'
            }
        
        # 统计文件数量
        total_files = sum(1 for _ in self.target_path.rglob('*') if _.is_file())
        total_dirs = sum(1 for _ in self.target_path.rglob('*') if _.is_dir())
        
        return {
            'name': 'file_structure',
            'passed': True,
            'message': f"文件结构完整，共 {total_files} 个文件，{total_dirs} 个目录",
            'severity': 'success'
        }
    
    def _check_config_files(self) -> Dict[str, Any]:
        """检查配置文件存在性"""
        self.log.info("检查配置文件...")
        
        required_files = ['package.json', 'README.md']
        important_files = ['.env', '.env.example', 'config.json']
        
        missing_required = []
        missing_important = []
        
        for f in required_files:
            if not (self.target_path / f).exists():
                missing_required.append(f)
        
        for f in important_files:
            if not (self.target_path / f).exists():
                missing_important.append(f)
        
        if missing_required:
            return {
                'name': 'config_files',
                'passed': False,
                'message': f"缺少必要配置文件: {', '.join(missing_required)}",
                'severity': 'error'
            }
        
        if missing_important:
            return {
                'name': 'config_files',
                'passed': True,
                'message': f"配置文件基本完整，缺少可选文件: {', '.join(missing_important)}",
                'severity': 'warning'
            }
        
        return {
            'name': 'config_files',
            'passed': True,
            'message': '所有配置文件齐全',
            'severity': 'success'
        }
    
    def _check_dependency_availability(self) -> Dict[str, Any]:
        """检查依赖可用性"""
        self.log.info("检查依赖可用性...")
        
        checks = []
        
        # 检查 npm
        result = subprocess.run('npm --version', shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            checks.append(f"npm: {result.stdout.strip()}")
        else:
            checks.append("npm: 未安装")
        
        # 检查 pip
        result = subprocess.run('pip --version', shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            checks.append(f"pip: {result.stdout.strip().split()[1]}")
        else:
            checks.append("pip: 未安装")
        
        # 检查 git
        result = subprocess.run('git --version', shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            checks.append(f"git: {result.stdout.strip().split()[2]}")
        else:
            checks.append("git: 未安装")
        
        # 检查 sqlite3
        result = subprocess.run('sqlite3 --version', shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            checks.append(f"sqlite3: 已安装")
        else:
            checks.append("sqlite3: 未安装")
        
        message = "; ".join(checks)
        
        if "未安装" in message:
            return {
                'name': 'dependency_availability',
                'passed': False,
                'message': f"部分依赖未安装: {message}",
                'severity': 'warning'
            }
        
        return {
            'name': 'dependency_availability',
            'passed': True,
            'message': f"所有依赖已安装: {message}",
            'severity': 'success'
        }
    
    def _check_checksum_validation(self) -> Dict[str, Any]:
        """验证文件校验和"""
        self.log.info("验证文件校验和...")
        
        source_files = [f for f in self.source_path.rglob('*') if f.is_file()]
        target_files = [f for f in self.target_path.rglob('*') if f.is_file()]
        
        source_count = len(source_files)
        target_count = len(target_files)
        
        if source_count != target_count:
            return {
                'name': 'checksum_validation',
                'passed': False,
                'message': f"文件数量不一致: 源 {source_count} 个，目标 {target_count} 个",
                'severity': 'error'
            }
        
        # 随机检查部分文件的校验和
        files_to_check = min(10, source_count)
        mismatches = []
        
        for i in range(files_to_check):
            source_file = source_files[i]
            relative_path = source_file.relative_to(self.source_path)
            target_file = self.target_path / relative_path
            
            if target_file.exists():
                source_checksum = self._calculate_checksum(source_file)
                target_checksum = self._calculate_checksum(target_file)
                
                if source_checksum != target_checksum:
                    mismatches.append(str(relative_path))
        
        if mismatches:
            return {
                'name': 'checksum_validation',
                'passed': False,
                'message': f"校验和不匹配的文件: {', '.join(mismatches)}",
                'severity': 'error'
            }
        
        return {
            'name': 'checksum_validation',
            'passed': True,
            'message': f"校验和验证通过，检查了 {files_to_check} 个文件",
            'severity': 'success'
        }
    
    def _check_build_test(self) -> Dict[str, Any]:
        """执行构建测试"""
        self.log.info("执行构建测试...")
        
        if not (self.target_path / 'package.json').exists():
            return {
                'name': 'build_test',
                'passed': True,
                'message': '无 package.json，跳过构建测试',
                'severity': 'info'
            }
        
        # 读取 package.json 检查是否有 build 脚本
        with open(self.target_path / 'package.json', 'r', encoding='utf-8') as f:
            package_data = json.load(f)
        
        scripts = package_data.get('scripts', {})
        
        if 'build' not in scripts:
            return {
                'name': 'build_test',
                'passed': True,
                'message': '无 build 脚本，跳过构建测试',
                'severity': 'info'
            }
        
        # 执行构建
        result = subprocess.run(
            'npm run build',
            shell=True,
            cwd=self.target_path,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            return {
                'name': 'build_test',
                'passed': True,
                'message': '构建成功',
                'severity': 'success'
            }
        else:
            error_msg = result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr
            return {
                'name': 'build_test',
                'passed': False,
                'message': f"构建失败: {error_msg}",
                'severity': 'error'
            }
    
    def _check_security_scan(self) -> Dict[str, Any]:
        """执行安全扫描"""
        self.log.info("执行安全扫描...")
        
        # 检查敏感文件
        sensitive_files = ['.env', '.env.local', 'secrets.json', 'config.prod.json']
        found_sensitive = []
        
        for f in sensitive_files:
            if (self.target_path / f).exists():
                found_sensitive.append(f)
        
        if found_sensitive:
            return {
                'name': 'security_scan',
                'passed': False,
                'message': f"发现敏感配置文件，建议检查是否包含敏感信息: {', '.join(found_sensitive)}",
                'severity': 'warning'
            }
        
        return {
            'name': 'security_scan',
            'passed': True,
            'message': '安全扫描通过，未发现明显安全风险',
            'severity': 'success'
        }
    
    def _check_performance(self) -> Dict[str, Any]:
        """检查性能相关配置"""
        self.log.info("检查性能配置...")
        
        issues = []
        
        # 检查是否有构建产物目录
        build_dirs = ['dist', 'build', 'out']
        for dir_name in build_dirs:
            if (self.target_path / dir_name).exists():
                size = sum(f.stat().st_size for f in (self.target_path / dir_name).rglob('*') if f.is_file())
                if size > 100 * 1024 * 1024:  # 大于 100MB
                    issues.append(f"{dir_name} 目录过大 ({size / (1024*1024):.1f} MB)")
        
        if issues:
            return {
                'name': 'performance_check',
                'passed': False,
                'message': f"性能问题: {', '.join(issues)}",
                'severity': 'warning'
            }
        
        return {
            'name': 'performance_check',
            'passed': True,
            'message': '性能检查通过',
            'severity': 'success'
        }
    
    def validate(self) -> Dict[str, Any]:
        """执行所有验证检查"""
        self.log.info("开始验证检查...")
        
        for check_config in self.checks:
            check_name = check_config['name']
            
            try:
                if check_name == 'file_structure':
                    result = self._check_file_structure()
                elif check_name == 'config_files':
                    result = self._check_config_files()
                elif check_name == 'dependency_availability':
                    result = self._check_dependency_availability()
                elif check_name == 'checksum_validation':
                    result = self._check_checksum_validation()
                elif check_name == 'build_test':
                    result = self._check_build_test()
                elif check_name == 'security_scan':
                    result = self._check_security_scan()
                elif check_name == 'performance_check':
                    result = self._check_performance()
                
                self.results['checks'].append(result)
                
                if result['passed']:
                    self.results['passed_count'] += 1
                else:
                    self.results['failed_count'] += 1
                    if result['severity'] == 'error':
                        self.results['errors'].append(result['message'])
                    else:
                        self.results['warnings'].append(result['message'])
                
                self.log.info(f"  {check_config['description']}: {'通过' if result['passed'] else '失败'}")
                
            except Exception as e:
                error = f"执行 {check_name} 检查时出错: {str(e)}"
                self.log.error(error)
                self.results['errors'].append(error)
        
        # 确定整体状态
        if self.results['failed_count'] == 0:
            status = 'completed'
        elif any(c['severity'] == 'error' for c in self.results['checks']):
            status = 'failed'
        else:
            status = 'completed_with_warnings'
        
        self.results['status'] = status
        
        self.log.info(f"验证完成: {self.results['passed_count']} 通过, {self.results['failed_count']} 失败")
        
        return self.results