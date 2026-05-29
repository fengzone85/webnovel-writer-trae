#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compatibility Tester - 兼容性测试套件
用于验证文档同步后的兼容性和准确性
"""

import os
import re
import json
import time
import hashlib
import configparser
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.parse


class TestStatus(Enum):
    """测试状态"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    ERROR = "error"


class TestCategory(Enum):
    """测试类别"""
    CONTENT_ACCURACY = "content_accuracy"
    FORMAT_COMPATIBILITY = "format_compatibility"
    LINK_VALIDITY = "link_validity"
    CODE_SYNTAX = "code_syntax"
    IMAGE_REFS = "image_refs"
    DEPENDENCY_CHECK = "dependency_check"


@dataclass
class TestResult:
    """测试结果"""
    name: str
    category: TestCategory
    status: TestStatus
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    details: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0


@dataclass
class TestSuiteResult:
    """测试套件结果"""
    timestamp: str
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    skipped: int = 0
    duration_seconds: float = 0
    results: List[TestResult] = field(default_factory=list)
    report_path: Optional[str] = None


class MarkdownValidator:
    """Markdown 格式验证器"""

    MARKDOWN_PATTERNS = {
        'heading': r'^#{1,6}\s+.+$',
        'bold': r'\*\*.+?\*\*|__.+?__',
        'italic': r'\*.+?\*|_.+?_',
        'code_block': r'```[\s\S]*?```',
        'inline_code': r'`[^`]+`',
        'link': r'\[.+?\]\(.+?\)',
        'image': r'!\[.*?\]\(.+?\)',
        'table': r'\|.+\|.+\n\|[-:]+\|([-:]+\|)+',
        'blockquote': r'^>\s+.+$',
        'list': r'^[\s]*[-*+]\s+|^\s+\d+\.\s+',
    }

    def __init__(self):
        self.errors = []

    def validate_file(self, file_path: Path) -> List[TestResult]:
        """验证 Markdown 文件"""
        results = []

        if not file_path.exists():
            results.append(TestResult(
                name=f"文件存在性: {file_path.name}",
                category=TestCategory.FORMAT_COMPATIBILITY,
                status=TestStatus.ERROR,
                message=f"文件不存在: {file_path}",
                file_path=str(file_path)
            ))
            return results

        try:
            content = file_path.read_text(encoding='utf-8')

            if not content.strip():
                results.append(TestResult(
                    name=f"内容非空: {file_path.name}",
                    category=TestCategory.CONTENT_ACCURACY,
                    status=TestStatus.WARNING,
                    message="文件内容为空",
                    file_path=str(file_path)
                ))
                return results

            line_count = content.count('\n') + 1
            results.append(TestResult(
                name=f"行数检查: {file_path.name}",
                category=TestCategory.CONTENT_ACCURACY,
                status=TestStatus.PASSED,
                message=f"文件包含 {line_count} 行",
                file_path=str(file_path),
                details={'line_count': line_count}
            ))

            results.extend(self._validate_headings(content, str(file_path)))
            results.extend(self._validate_links(content, str(file_path)))
            results.extend(self._validate_code_blocks(content, str(file_path)))
            results.extend(self._validate_images(content, str(file_path)))

        except Exception as e:
            results.append(TestResult(
                name=f"文件读取: {file_path.name}",
                category=TestCategory.FORMAT_COMPATIBILITY,
                status=TestStatus.ERROR,
                message=f"读取文件失败: {str(e)}",
                file_path=str(file_path)
            ))

        return results

    def _validate_headings(self, content: str, file_path: str) -> List[TestResult]:
        """验证标题结构"""
        results = []
        lines = content.split('\n')
        heading_levels = []

        for i, line in enumerate(lines, 1):
            if re.match(r'^#{1,6}\s+', line):
                level = len(re.match(r'^(#+)\s+', line).group(1))
                heading_levels.append((i, level))

                if len(heading_levels) > 1:
                    prev_level = heading_levels[-2][1]
                    if level > prev_level + 1:
                        results.append(TestResult(
                            name=f"标题层级: 第{i}行",
                            category=TestCategory.FORMAT_COMPATIBILITY,
                            status=TestStatus.WARNING,
                            message=f"标题层级跳跃: {prev_level} -> {level}",
                            file_path=file_path,
                            line_number=i,
                            details={'level': level, 'prev_level': prev_level}
                        ))

        if heading_levels:
            results.append(TestResult(
                name=f"标题结构: {len(heading_levels)} 个标题",
                category=TestCategory.FORMAT_COMPATIBILITY,
                status=TestStatus.PASSED,
                message=f"发现 {len(heading_levels)} 个标题，结构正常"
            ))

        return results

    def _validate_links(self, content: str, file_path: str) -> List[TestResult]:
        """验证链接格式"""
        results = []
        links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', content)

        if not links:
            return results

        for i, (text, url) in enumerate(links):
            if not text.strip():
                results.append(TestResult(
                    name=f"链接文本: 第{i+1}个",
                    category=TestCategory.FORMAT_COMPATIBILITY,
                    status=TestStatus.WARNING,
                    message=f"链接文本为空",
                    file_path=file_path,
                    details={'url': url}
                ))

            if url.startswith('http'):
                if not self._is_valid_url_format(url):
                    results.append(TestResult(
                        name=f"URL格式: 第{i+1}个",
                        category=TestCategory.LINK_VALIDITY,
                        status=TestStatus.WARNING,
                        message=f"URL格式可能不正确: {url}",
                        file_path=file_path,
                        details={'url': url}
                    ))

        results.append(TestResult(
            name=f"链接数量: {len(links)} 个",
            category=TestCategory.LINK_VALIDITY,
            status=TestStatus.PASSED,
            message=f"发现 {len(links)} 个链接"
        ))

        return results

    def _validate_code_blocks(self, content: str, file_path: str) -> List[TestResult]:
        """验证代码块"""
        results = []
        code_blocks = re.findall(r'```(\w*)\n([\s\S]*?)```', content)

        for i, (lang, code) in enumerate(code_blocks):
            if not lang:
                results.append(TestResult(
                    name=f"代码语言: 第{i+1}个",
                    category=TestCategory.CODE_SYNTAX,
                    status=TestStatus.WARNING,
                    message="代码块未指定语言",
                    file_path=file_path,
                    details={'block_num': i + 1}
                ))

            if lang in ['python', 'py']:
                if not self._validate_python_syntax(code):
                    results.append(TestResult(
                        name=f"Python语法: 第{i+1}个",
                        category=TestCategory.CODE_SYNTAX,
                        status=TestStatus.WARNING,
                        message="Python 代码块可能存在语法问题",
                        file_path=file_path,
                        details={'block_num': i + 1}
                    ))

        return results

    def _validate_images(self, content: str, file_path: str) -> List[TestResult]:
        """验证图片引用"""
        results = []
        images = re.findall(r'!\[([^\]]*)\]\(([^\)]+)\)', content)

        for i, (alt, url) in enumerate(images):
            if not alt.strip():
                results.append(TestResult(
                    name=f"图片ALT: 第{i+1}个",
                    category=TestCategory.IMAGE_REFS,
                    status=TestStatus.WARNING,
                    message="图片缺少 ALT 文本",
                    file_path=file_path,
                    details={'url': url}
                ))

        return results

    def _is_valid_url_format(self, url: str) -> bool:
        """验证 URL 格式"""
        try:
            result = urllib.parse.urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def _validate_python_syntax(self, code: str) -> bool:
        """验证 Python 语法"""
        try:
            compile(code, '<string>', 'exec')
            return True
        except SyntaxError:
            return False


class LinkChecker:
    """链接有效性检查器"""

    def __init__(self, base_path: Path, timeout: int = 10, max_workers: int = 4):
        self.base_path = base_path
        self.timeout = timeout
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Webnovel-Writer-Sync/1.0'
        })

    def check_link(self, url: str, file_path: str, line_num: int) -> TestResult:
        """检查单个链接"""
        start_time = time.time()

        if url.startswith('#') or url.startswith('mailto:'):
            return TestResult(
                name=f"内部链接: {url[:50]}",
                category=TestCategory.LINK_VALIDITY,
                status=TestStatus.PASSED,
                message="内部链接无需检查",
                file_path=file_path,
                line_number=line_num,
                duration_ms=(time.time() - start_time) * 1000
            )

        if url.startswith('/') or not url.startswith('http'):
            local_path = self.base_path / url.split('#')[0].lstrip('/')
            exists = local_path.exists()

            return TestResult(
                name=f"本地链接: {url[:50]}",
                category=TestCategory.LINK_VALIDITY,
                status=TestStatus.PASSED if exists else TestStatus.FAILED,
                message="文件存在" if exists else f"文件不存在: {local_path}",
                file_path=file_path,
                line_number=line_num,
                duration_ms=(time.time() - start_time) * 1000,
                details={'checked_path': str(local_path), 'exists': exists}
            )

        try:
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                return TestResult(
                    name=f"外部链接: {url[:50]}",
                    category=TestCategory.LINK_VALIDITY,
                    status=TestStatus.PASSED,
                    message=f"链接有效 (HTTP {response.status_code})",
                    file_path=file_path,
                    line_number=line_num,
                    duration_ms=duration_ms,
                    details={'status_code': response.status_code, 'url': url}
                )
            else:
                return TestResult(
                    name=f"外部链接: {url[:50]}",
                    category=TestCategory.LINK_VALIDITY,
                    status=TestStatus.FAILED,
                    message=f"链接返回 HTTP {response.status_code}",
                    file_path=file_path,
                    line_number=line_num,
                    duration_ms=duration_ms,
                    details={'status_code': response.status_code, 'url': url}
                )

        except requests.exceptions.Timeout:
            return TestResult(
                name=f"外部链接超时: {url[:50]}",
                category=TestCategory.LINK_VALIDITY,
                status=TestStatus.WARNING,
                message=f"链接检查超时 ({self.timeout}秒)",
                file_path=file_path,
                line_number=line_num,
                duration_ms=(time.time() - start_time) * 1000
            )
        except requests.exceptions.RequestException as e:
            return TestResult(
                name=f"外部链接错误: {url[:50]}",
                category=TestCategory.LINK_VALIDITY,
                status=TestStatus.FAILED,
                message=f"链接检查失败: {str(e)}",
                file_path=file_path,
                line_number=line_num,
                duration_ms=(time.time() - start_time) * 1000,
                details={'error': str(e)}
            )

    def check_file_links(self, file_path: Path) -> List[TestResult]:
        """检查文件中的所有链接"""
        results = []
        links_to_check = []

        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                urls = re.findall(r'https?://[^\s\)\"\'\>\]]+', line)
                for url in urls:
                    url = url.rstrip('.,;:!?')
                    links_to_check.append((url, str(file_path), line_num))

        except Exception as e:
            results.append(TestResult(
                name=f"链接检查: {file_path.name}",
                category=TestCategory.LINK_VALIDITY,
                status=TestStatus.ERROR,
                message=f"读取文件失败: {str(e)}",
                file_path=str(file_path)
            ))
            return results

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.check_link, url, fp, ln): (url, fp, ln)
                for url, fp, ln in links_to_check
            }

            for future in as_completed(futures):
                results.append(future.result())

        return results


class CompatibilityTester:
    """兼容性测试套件"""

    def __init__(self, project_path: str, config_path: Optional[str] = None):
        self.project_path = Path(project_path)
        self.config = configparser.ConfigParser()

        if config_path and Path(config_path).exists():
            self.config.read(config_path, encoding='utf-8')
        else:
            self._set_defaults()

        self.log_dir = Path(self.config.get('logging', 'log_dir', fallback='scripts/sync_system/logs'))
        self.report_dir = Path('scripts/sync_system/tests/reports')
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)

        self.logger = self._setup_logger()
        self.markdown_validator = MarkdownValidator()
        self.link_checker = LinkChecker(
            self.project_path,
            timeout=self.config.getint('testing', 'timeout_seconds', fallback=10),
            max_workers=self.config.getint('testing', 'parallel_workers', fallback=4)
        )

    def _set_defaults(self):
        """设置默认值"""
        self.config['testing'] = {
            'scope_check_content_accuracy': 'true',
            'scope_check_format_compatibility': 'true',
            'scope_check_link_validity': 'true',
            'scope_check_code_syntax': 'true',
            'scope_check_image_refs': 'true',
        }

    def _setup_logger(self) -> logging.Logger:
        """设置日志器"""
        logger = logging.getLogger("CompatibilityTester")
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        log_file = self.log_dir / f"test_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    def _should_check(self, category: TestCategory) -> bool:
        """检查是否应该执行该测试"""
        section = 'testing_scope'
        key = f"check_{category.value}"
        return self.config.getboolean(section, key, fallback=True)

    def run_tests(self, test_paths: Optional[List[str]] = None) -> TestSuiteResult:
        """运行测试套件"""
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        result = TestSuiteResult(timestamp=timestamp)

        if test_paths is None:
            test_paths = ['docs', 'scripts']

        test_files = []
        for path in test_paths:
            full_path = self.project_path / path
            if full_path.is_dir():
                test_files.extend(list(full_path.rglob('*.md')))
            elif full_path.is_file() and full_path.suffix == '.md':
                test_files.append(full_path)

        self.logger.info(f"发现 {len(test_files)} 个待测试文件")

        for file_path in test_files:
            self.logger.debug(f"测试文件: {file_path}")

            if self._should_check(TestCategory.FORMAT_COMPATIBILITY) or \
               self._should_check(TestCategory.CONTENT_ACCURACY):
                result.results.extend(self.markdown_validator.validate_file(file_path))

            if self._should_check(TestCategory.LINK_VALIDITY):
                result.results.extend(self.link_checker.check_file_links(file_path))

        for test_result in result.results:
            result.total_tests += 1
            if test_result.status == TestStatus.PASSED:
                result.passed += 1
            elif test_result.status == TestStatus.FAILED:
                result.failed += 1
            elif test_result.status == TestStatus.WARNING:
                result.warnings += 1
            elif test_result.status == TestStatus.SKIPPED:
                result.skipped += 1

        result.duration_seconds = time.time() - start_time
        result.report_path = self._generate_report(result)

        self.logger.info(
            f"测试完成: 总计 {result.total_tests}, "
            f"通过 {result.passed}, 失败 {result.failed}, "
            f"警告 {result.warnings}, 耗时 {result.duration_seconds:.2f}秒"
        )

        return result

    def _generate_report(self, result: TestSuiteResult) -> str:
        """生成测试报告"""
        report_path = self.report_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        report_data = {
            'timestamp': result.timestamp,
            'summary': {
                'total_tests': result.total_tests,
                'passed': result.passed,
                'failed': result.failed,
                'warnings': result.warnings,
                'skipped': result.skipped,
                'duration_seconds': result.duration_seconds,
                'pass_rate': f"{(result.passed / max(1, result.total_tests) * 100):.1f}%"
            },
            'results': [
                {
                    'name': r.name,
                    'category': r.category.value,
                    'status': r.status.value,
                    'message': r.message,
                    'file_path': r.file_path,
                    'line_number': r.line_number,
                    'details': r.details,
                    'duration_ms': r.duration_ms
                }
                for r in result.results
            ]
        }

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        return str(report_path)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Compatibility Tester")
    parser.add_argument('--project', '-p', default='../..',
                       help='项目路径')
    parser.add_argument('--config', '-c', default='../config/sync_config.ini',
                       help='配置文件路径')
    parser.add_argument('--paths', nargs='+', default=None,
                       help='指定测试路径')
    parser.add_argument('--output', '-o', default=None,
                       help='报告输出路径')

    args = parser.parse_args()

    project_path = Path(__file__).parent.parent.parent / args.project
    config_path = Path(__file__).parent / args.config

    tester = CompatibilityTester(str(project_path), str(config_path) if config_path.exists() else None)

    print("开始运行兼容性测试...")
    result = tester.run_tests(test_paths=args.paths)

    print(f"\n{'='*60}")
    print(f"测试结果摘要")
    print(f"{'='*60}")
    print(f"总测试数: {result.total_tests}")
    print(f"通过: {result.passed} ✅")
    print(f"失败: {result.failed} ❌")
    print(f"警告: {result.warnings} ⚠️")
    print(f"跳过: {result.skipped} ⏭️")
    print(f"通过率: {result.passed / max(1, result.total_tests) * 100:.1f}%")
    print(f"耗时: {result.duration_seconds:.2f}秒")
    print(f"报告: {result.report_path}")

    if result.failed > 0:
        print(f"\n失败项:")
        for r in result.results:
            if r.status == TestStatus.FAILED:
                print(f"  - [{r.category.value}] {r.name}")
                print(f"    {r.message}")
                if r.file_path:
                    print(f"    文件: {r.file_path}:{r.line_number}")


if __name__ == "__main__":
    main()
