#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dependency Manager - 依赖管理器
用于分类、管理和验证项目依赖
"""

import os
import re
import json
import configparser
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
import subprocess


class DependencyCategory(Enum):
    """依赖类别"""
    REQUIRED = "required"
    OPTIONAL = "optional"
    DEVELOPMENT = "development"
    CLOUD_SERVICES = "cloud_services"


class DependencyStatus(Enum):
    """依赖状态"""
    INSTALLED = "installed"
    MISSING = "missing"
    OUTDATED = "outdated"
    CONFLICT = "conflict"


@dataclass
class Dependency:
    """依赖项"""
    name: str
    version: Optional[str] = None
    category: DependencyCategory = DependencyCategory.REQUIRED
    source: str = "requirements.txt"
    description: Optional[str] = None
    use_case: Optional[str] = None
    conditions: Optional[str] = None
    limitations: Optional[str] = None
    status: DependencyStatus = DependencyStatus.MISSING
    installed_version: Optional[str] = None
    latest_version: Optional[str] = None


@dataclass
class DependencyReport:
    """依赖报告"""
    timestamp: str
    total: int = 0
    installed: int = 0
    missing: int = 0
    outdated: int = 0
    conflicts: int = 0
    by_category: Dict[str, int] = field(default_factory=dict)
    dependencies: List[Dependency] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class DependencyParser:
    """依赖解析器"""

    REQUIREMENTS_PATTERNS = {
        'version_spec': r'([a-zA-Z0-9_-]+)\s*([><=!~]+)?\s*([0-9a-zA-Z._-]+)?',
        ' extras': r'([a-zA-Z0-9_-]+)\[([^\]]+)\]',
        ' comment': r'#.*$',
    }

    @staticmethod
    def parse_requirements(content: str) -> List[Tuple[str, Optional[str]]]:
        """解析 requirements.txt 内容"""
        deps = []
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            line = re.sub(r'#.*$', '', line)

            match = re.match(r'([a-zA-Z0-9_-]+)\s*([><=!~]+)?\s*([0-9a-zA-Z._-]+)?', line)
            if match:
                name = match.group(1)
                version = match.group(3) if match.group(3) else None
                deps.append((name, version))

        return deps

    @staticmethod
    def parse_setup_py(content: str) -> List[Tuple[str, Optional[str]]]:
        """解析 setup.py 依赖"""
        deps = []
        patterns = [
            r"install_requires\s*=\s*\[(.*?)\]",
            r"extras_require\s*=\s*\{(.*?)\}",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                deps_str = re.findall(r'["\']([^"\']+)["\']', match)
                for dep in deps_str:
                    parts = dep.split('==')
                    name = parts[0].strip()
                    version = parts[1].strip() if len(parts) > 1 else None
                    deps.append((name, version))

        return deps


class DependencyMetadata:
    """依赖元数据"""

    KNOWN_DEPENDENCIES = {
        'aiohttp': {
            'category': DependencyCategory.REQUIRED,
            'description': '异步 HTTP 客户端/服务器',
            'use_case': '用于 RAG API 调用、远程服务交互',
            'conditions': 'Python 3.6+ 环境',
            'limitations': '不支持 Python 2.7'
        },
        'filelock': {
            'category': DependencyCategory.REQUIRED,
            'description': '文件锁实现',
            'use_case': '多进程环境下的文件并发控制',
            'conditions': '需要文件系统支持锁机制',
            'limitations': '网络文件系统可能不支持'
        },
        'pydantic': {
            'category': DependencyCategory.REQUIRED,
            'description': '数据验证库',
            'use_case': 'Story System 合同数据模型定义',
            'conditions': 'Python 3.6+',
            'limitations': 'V2 版本 API 有变化'
        },
        'chromadb': {
            'category': DependencyCategory.OPTIONAL,
            'description': '向量数据库',
            'use_case': 'RAG 向量存储后端，支持本地向量检索',
            'conditions': '需要 4GB+ 内存用于向量索引',
            'limitations': '大型部署需要更多资源'
        },
        'flask': {
            'category': DependencyCategory.OPTIONAL,
            'description': 'Web 微框架',
            'use_case': 'Dashboard 可视化面板',
            'conditions': '可选，CLI 模式不需要',
            'limitations': '生产环境建议使用 gunicorn'
        },
        'flask-cors': {
            'category': DependencyCategory.OPTIONAL,
            'description': 'CORS 支持',
            'use_case': 'Dashboard API 跨域支持',
            'conditions': '仅在使用 Dashboard 时需要',
            'limitations': '仅与 Flask 配合使用'
        },
        'pytest': {
            'category': DependencyCategory.DEVELOPMENT,
            'description': '测试框架',
            'use_case': '单元测试和集成测试',
            'conditions': '开发环境必需',
            'limitations': '仅开发环境使用'
        },
        'pytest-cov': {
            'category': DependencyCategory.DEVELOPMENT,
            'description': '覆盖率报告',
            'use_case': '生成测试覆盖率报告',
            'conditions': '开发环境可选',
            'limitations': '需要配合 pytest 使用'
        },
        'requests': {
            'category': DependencyCategory.CLOUD_SERVICES,
            'description': 'HTTP 请求库',
            'use_case': 'GitHub API 调用、RAG 服务通信',
            'conditions': '网络环境必需',
            'limitations': '同步调用可能阻塞'
        },
        'openai': {
            'category': DependencyCategory.CLOUD_SERVICES,
            'description': 'OpenAI API 客户端',
            'use_case': 'GPT 模型调用（可选）',
            'conditions': '需要 OpenAI API Key',
            'limitations': '需要付费，有调用配额限制'
        },
        'jina': {
            'category': DependencyCategory.CLOUD_SERVICES,
            'description': 'Jina AI SDK',
            'use_case': 'Rerank API 调用',
            'conditions': '需要 Jina AI API Key',
            'limitations': '有免费额度限制'
        },
    }

    @classmethod
    def get_metadata(cls, package_name: str) -> Dict[str, Any]:
        """获取依赖元数据"""
        return cls.KNOWN_DEPENDENCIES.get(package_name, {})


class DependencyChecker:
    """依赖检查器"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)

    def check_installed(self, package_name: str) -> Optional[str]:
        """检查包是否已安装"""
        try:
            result = subprocess.run(
                ['pip', 'show', package_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                match = re.search(r'Version:\s*([0-9a-zA-Z._-]+)', result.stdout)
                return match.group(1) if match else None
        except Exception:
            pass
        return None

    def check_updates(self, package_name: str) -> Optional[str]:
        """检查包是否有更新"""
        try:
            result = subprocess.run(
                ['pip', 'index', 'versions', package_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                match = re.search(r'Available versions:\s*([0-9a-zA-Z._,\s-]+)', result.stdout)
                if match:
                    versions = match.group(1).split(',')
                    return versions[-1].strip() if versions else None
        except Exception:
            pass
        return None

    def get_installed_packages(self) -> Set[str]:
        """获取已安装的包列表"""
        packages = set()
        try:
            result = subprocess.run(
                ['pip', 'list', '--format=freeze'],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if '==' in line:
                        pkg = line.split('==')[0].strip().lower()
                        packages.add(pkg)
        except Exception:
            pass
        return packages


class DependencyManager:
    """依赖管理器"""

    def __init__(self, project_path: str, config_path: Optional[str] = None):
        self.project_path = Path(project_path)
        self.config = configparser.ConfigParser()

        if config_path and Path(config_path).exists():
            self.config.read(config_path, encoding='utf-8')

        self.log_dir = Path('scripts/sync_system/logs')
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logger = self._setup_logger()

        self.parser = DependencyParser()
        self.metadata = DependencyMetadata()
        self.checker = DependencyChecker(project_path)

    def _setup_logger(self) -> logging.Logger:
        """设置日志器"""
        logger = logging.getLogger("DependencyManager")
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        log_file = self.log_dir / f"dependency_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    def load_dependencies(self) -> List[Dependency]:
        """加载项目依赖"""
        dependencies = []

        req_file = self.project_path / 'requirements.txt'
        if req_file.exists():
            content = req_file.read_text(encoding='utf-8')
            for name, version in self.parser.parse_requirements(content):
                dep = self._create_dependency(name, version, 'requirements.txt')
                dependencies.append(dep)

        opt_req_file = self.project_path / 'requirements-optional.txt'
        if opt_req_file.exists():
            content = opt_req_file.read_text(encoding='utf-8')
            for name, version in self.parser.parse_requirements(content):
                dep = self._create_dependency(
                    name, version, 'requirements-optional.txt',
                    category=DependencyCategory.OPTIONAL
                )
                dependencies.append(dep)

        setup_py = self.project_path / 'setup.py'
        if setup_py.exists():
            content = setup_py.read_text(encoding='utf-8')
            for name, version in self.parser.parse_setup_py(content):
                dep = self._create_dependency(name, version, 'setup.py')
                if dep not in dependencies:
                    dependencies.append(dep)

        return dependencies

    def _create_dependency(
        self,
        name: str,
        version: Optional[str],
        source: str,
        category: DependencyCategory = DependencyCategory.REQUIRED
    ) -> Dependency:
        """创建依赖项"""
        metadata = self.metadata.get_metadata(name)

        if metadata:
            category = metadata.get('category', category)

        dep = Dependency(
            name=name,
            version=version,
            category=category,
            source=source,
            description=metadata.get('description'),
            use_case=metadata.get('use_case'),
            conditions=metadata.get('conditions'),
            limitations=metadata.get('limitations')
        )

        installed_version = self.checker.check_installed(name)
        if installed_version:
            dep.status = DependencyStatus.INSTALLED
            dep.installed_version = installed_version

            if version and installed_version != version:
                dep.status = DependencyStatus.OUTDATED

            latest = self.checker.check_updates(name)
            if latest and installed_version != latest:
                dep.latest_version = latest
                dep.status = DependencyStatus.OUTDATED
        else:
            dep.status = DependencyStatus.MISSING

        return dep

    def check_dependencies(self) -> DependencyReport:
        """检查依赖状态"""
        report = DependencyReport(timestamp=datetime.now().isoformat())
        dependencies = self.load_dependencies()

        installed = self.checker.get_installed_packages()

        for dep in dependencies:
            if dep.name.lower() in installed:
                dep.status = DependencyStatus.INSTALLED
                report.installed += 1
            else:
                dep.status = DependencyStatus.MISSING
                report.missing += 1

            category_key = dep.category.value
            report.by_category[category_key] = report.by_category.get(category_key, 0) + 1

            report.dependencies.append(dep)

        report.total = len(dependencies)

        report.recommendations = self._generate_recommendations(report)

        self.logger.info(
            f"依赖检查完成: 总计 {report.total}, "
            f"已安装 {report.installed}, 缺失 {report.missing}"
        )

        return report

    def _generate_recommendations(self, report: DependencyReport) -> List[str]:
        """生成建议"""
        recommendations = []

        if report.missing > 0:
            missing_required = [
                d.name for d in report.dependencies
                if d.status == DependencyStatus.MISSING
                and d.category == DependencyCategory.REQUIRED
            ]
            if missing_required:
                recommendations.append(
                    f"缺少必选依赖: {', '.join(missing_required)}"
                )

        outdated = [
            d.name for d in report.dependencies
            if d.status == DependencyStatus.OUTDATED
        ]
        if outdated:
            recommendations.append(
                f"以下依赖有新版本可用: {', '.join(outdated)}"
            )

        return recommendations

    def generate_manifest(self, output_path: Optional[str] = None) -> str:
        """生成依赖清单"""
        report = self.check_dependencies()

        manifest = {
            'generated_at': report.timestamp,
            'summary': {
                'total': report.total,
                'installed': report.installed,
                'missing': report.missing,
                'by_category': report.by_category
            },
            'categories': {
                'required': [],
                'optional': [],
                'development': [],
                'cloud_services': []
            },
            'recommendations': report.recommendations
        }

        for dep in report.dependencies:
            dep_data = {
                'name': dep.name,
                'version': dep.version,
                'status': dep.status.value,
                'installed_version': dep.installed_version,
                'latest_version': dep.latest_version,
                'source': dep.source,
                'description': dep.description,
                'use_case': dep.use_case,
                'conditions': dep.conditions,
                'limitations': dep.limitations
            }
            manifest['categories'][dep.category.value].append(dep_data)

        if output_path is None:
            output_path = 'scripts/sync_system/dependency_manifest.json'

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        return str(output_file)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Dependency Manager")
    parser.add_argument('--project', '-p', default='../..',
                       help='项目路径')
    parser.add_argument('--check', '-c', action='store_true',
                       help='检查依赖状态')
    parser.add_argument('--manifest', '-m', action='store_true',
                       help='生成依赖清单')
    parser.add_argument('--output', '-o', default=None,
                       help='输出路径')

    args = parser.parse_args()

    project_path = Path(__file__).parent.parent.parent / args.project

    manager = DependencyManager(str(project_path))

    if args.check or args.manifest:
        report = manager.check_dependencies()

        print(f"\n{'='*60}")
        print(f"依赖检查报告")
        print(f"{'='*60}")
        print(f"生成时间: {report.timestamp}")
        print(f"总计依赖: {report.total}")
        print(f"已安装: {report.installed} ✅")
        print(f"缺失: {report.missing} ❌")

        print(f"\n按类别:")
        for category, count in report.by_category.items():
            print(f"  - {category}: {count}")

        if report.recommendations:
            print(f"\n建议:")
            for rec in report.recommendations:
                print(f"  ⚠️ {rec}")

        print(f"\n依赖详情:")
        for dep in report.dependencies:
            status_icon = {
                DependencyStatus.INSTALLED: '✅',
                DependencyStatus.MISSING: '❌',
                DependencyStatus.OUTDATED: '🔄',
                DependencyStatus.CONFLICT: '⚠️'
            }.get(dep.status, '❓')

            print(f"  {status_icon} {dep.name}")
            if dep.version:
                print(f"      要求版本: {dep.version}")
            if dep.installed_version:
                print(f"      已安装: {dep.installed_version}")
            if dep.latest_version:
                print(f"      最新版本: {dep.latest_version}")

    if args.manifest:
        manifest_path = manager.generate_manifest(args.output)
        print(f"\n依赖清单已生成: {manifest_path}")


if __name__ == "__main__":
    main()
