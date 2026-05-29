#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sync System - 自动化定时任务系统主入口
整合同步调度、测试、依赖管理和通知功能
"""

import os
import sys
import json
import configparser
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
import threading
import time

sys.path.insert(0, str(Path(__file__).parent))

from sync_scheduler import SyncScheduler, SyncResult, SyncStatus
from compatibility_tester import CompatibilityTester, TestSuiteResult, TestStatus
from dependency_manager import DependencyManager, DependencyReport
from notification import NotificationManager, NotificationType


class SyncSystem:
    """同步系统"""

    def __init__(self, config_path: str, project_path: str):
        self.config_path = config_path
        self.project_path = project_path
        self.config = configparser.ConfigParser()

        if Path(config_path).exists():
            self.config.read(config_path, encoding='utf-8')
        else:
            print(f"警告: 配置文件不存在 {config_path}")
            self._set_defaults()

        self.log_dir = Path('scripts/sync_system/logs')
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logger = self._setup_logger()

        self.scheduler = None
        self.tester = None
        self.dep_manager = None
        self.notifier = None

        self._running = False
        self._main_thread: Optional[threading.Thread] = None

    def _set_defaults(self):
        """设置默认配置"""
        self.config['sync_source'] = {
            'repo_url': 'https://github.com/lingfengQAQ/webnovel-writer',
            'branch': 'master',
            'docs_paths': 'docs, webnovel-writer/docs, webnovel-writer/scripts',
            'ignore_patterns': '*.tmp, *.bak, __pycache__, .git'
        }
        self.config['schedule'] = {
            'frequency': 'daily',
            'weekly_day': '0',
            'daily_time': '03:00'
        }
        self.config['testing'] = {
            'trigger': 'on_change',
            'timeout_seconds': '300',
            'parallel_workers': '4'
        }
        self.config['notifications'] = {
            'enabled': 'true',
            'channels': 'console, file'
        }
        self.config['error_handling'] = {
            'max_retries': '3',
            'retry_interval': '300'
        }

    def _setup_logger(self) -> logging.Logger:
        """设置日志器"""
        logger = logging.getLogger("SyncSystem")
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        log_file = self.log_dir / f"sync_system_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger

    def initialize(self):
        """初始化各组件"""
        self.logger.info("初始化同步系统...")

        try:
            self.scheduler = SyncScheduler(self.config_path, self.project_path)
            self.logger.info("✓ 同步调度器已初始化")
        except Exception as e:
            self.logger.error(f"同步调度器初始化失败: {e}")
            raise

        try:
            self.tester = CompatibilityTester(self.project_path, self.config_path)
            self.logger.info("✓ 兼容性测试器已初始化")
        except Exception as e:
            self.logger.warning(f"兼容性测试器初始化失败: {e}")

        try:
            self.dep_manager = DependencyManager(self.project_path, self.config_path)
            self.logger.info("✓ 依赖管理器已初始化")
        except Exception as e:
            self.logger.warning(f"依赖管理器初始化失败: {e}")

        try:
            self.notifier = NotificationManager(self.config_path)
            self.notifier.start()
            self.logger.info("✓ 通知管理器已初始化")
        except Exception as e:
            self.logger.warning(f"通知管理器初始化失败: {e}")

    def shutdown(self):
        """关闭系统"""
        self.logger.info("关闭同步系统...")

        if self.notifier:
            self.notifier.stop()

        if self.scheduler:
            self.scheduler.stop_scheduler()

        self.logger.info("同步系统已关闭")

    def run_sync(self, force: bool = False) -> SyncResult:
        """执行同步"""
        if not self.scheduler:
            raise RuntimeError("同步调度器未初始化")

        self.logger.info(f"开始同步 (force={force})")
        result = self.scheduler.run_sync(force=force)

        if result.status == SyncStatus.SUCCESS:
            self.notifier.notify_sync_success({
                'files_updated': result.files_updated,
                'files_added': result.files_added,
                'version': result.version,
                'duration': result.duration_seconds
            })
        elif result.status == SyncStatus.FAILED:
            state = self.scheduler.version_tracker.load_state()
            self.notifier.notify_sync_failure(
                result.errors[0] if result.errors else "未知错误",
                state.failure_count
            )

        return result

    def run_tests(self, paths: Optional[List[str]] = None) -> TestSuiteResult:
        """运行测试"""
        if not self.tester:
            raise RuntimeError("兼容性测试器未初始化")

        self.logger.info("开始兼容性测试...")
        result = self.tester.run_tests(paths)

        passed = result.failed == 0
        self.notifier.notify_test_result(passed, {
            'total': result.total_tests,
            'passed': result.passed,
            'failed': result.failed,
            'warnings': result.warnings,
            'pass_rate': f"{result.passed / max(1, result.total_tests) * 100:.1f}%",
            'duration': result.duration_seconds,
            'report': result.report_path
        })

        return result

    def check_dependencies(self) -> DependencyReport:
        """检查依赖"""
        if not self.dep_manager:
            raise RuntimeError("依赖管理器未初始化")

        self.logger.info("检查依赖状态...")
        report = self.dep_manager.check_dependencies()

        if report.missing > 0:
            missing = [d.name for d in report.dependencies if d.status.value == 'missing']
            self.notifier.notify_dependency_issue(missing)

        return report

    def run_full_cycle(self, force_sync: bool = False) -> Dict[str, Any]:
        """运行完整周期"""
        self.logger.info("开始完整同步周期")
        cycle_start = datetime.now()

        results = {
            'cycle_start': cycle_start.isoformat(),
            'sync': None,
            'tests': None,
            'dependencies': None,
            'success': True,
            'errors': []
        }

        try:
            sync_result = self.run_sync(force=force_sync)
            results['sync'] = {
                'status': sync_result.status.value,
                'files_updated': sync_result.files_updated,
                'version': sync_result.version,
                'duration': sync_result.duration_seconds
            }

            if sync_result.status == SyncStatus.SUCCESS:
                if self.config.get('testing', 'trigger', fallback='on_change') in ['always', 'on_change']:
                    try:
                        test_result = self.run_tests()
                        results['tests'] = {
                            'total': test_result.total_tests,
                            'passed': test_result.passed,
                            'failed': test_result.failed,
                            'pass_rate': f"{test_result.passed / max(1, test_result.total_tests) * 100:.1f}%",
                            'report': test_result.report_path
                        }
                    except Exception as e:
                        self.logger.error(f"测试执行失败: {e}")
                        results['errors'].append(f"测试失败: {e}")

            elif sync_result.status == SyncStatus.FAILED:
                results['success'] = False

        except Exception as e:
            self.logger.error(f"同步失败: {e}")
            results['success'] = False
            results['errors'].append(str(e))

        try:
            dep_report = self.check_dependencies()
            results['dependencies'] = {
                'total': dep_report.total,
                'installed': dep_report.installed,
                'missing': dep_report.missing,
                'recommendations': dep_report.recommendations
            }
        except Exception as e:
            self.logger.error(f"依赖检查失败: {e}")
            results['errors'].append(f"依赖检查: {e}")

        cycle_end = datetime.now()
        results['cycle_end'] = cycle_end.isoformat()
        results['duration_seconds'] = (cycle_end - cycle_start).total_seconds()

        self._save_cycle_result(results)

        self.logger.info(
            f"完整周期完成: 耗时 {results['duration_seconds']:.2f}秒, "
            f"成功: {results['success']}"
        )

        return results

    def _save_cycle_result(self, results: Dict[str, Any]):
        """保存周期结果"""
        history_dir = Path('.sync_status')
        history_dir.mkdir(parents=True, exist_ok=True)

        history_file = history_dir / 'cycle_history.json'

        history = []
        if history_file.exists():
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)

        history.append(results)
        history = history[-100:]

        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def start_scheduler(self):
        """启动调度器"""
        if self._running:
            self.logger.warning("系统已在运行")
            return

        self._running = True
        self._main_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._main_thread.start()
        self.logger.info("同步系统调度器已启动")

    def stop_scheduler(self):
        """停止调度器"""
        self._running = False
        if self._main_thread:
            self._main_thread.join(timeout=10)
        self.logger.info("同步系统调度器已停止")

    def _scheduler_loop(self):
        """调度器主循环"""
        while self._running:
            try:
                if self.scheduler and self.scheduler.should_sync():
                    self.run_full_cycle()

                check_interval = self.config.getint('version_tracking', 'check_interval', fallback=60)
                for _ in range(check_interval * 60):
                    if not self._running:
                        break
                    time.sleep(1)

            except Exception as e:
                self.logger.error(f"调度器异常: {e}")
                time.sleep(60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Webnovel Writer Sync System - 自动化定时任务系统"
    )

    parser.add_argument('--config', '-c', default='config/sync_config.ini',
                       help='配置文件路径')
    parser.add_argument('--project', '-p', default='../..',
                       help='项目路径')

    subparsers = parser.add_subparsers(dest='command', help='命令')

    sync_parser = subparsers.add_parser('sync', help='执行同步')
    sync_parser.add_argument('--force', '-f', action='store_true',
                             help='强制同步')

    test_parser = subparsers.add_parser('test', help='运行测试')
    test_parser.add_argument('--paths', nargs='+', default=None,
                            help='指定测试路径')

    dep_parser = subparsers.add_parser('dep', help='检查依赖')
    dep_parser.add_argument('--manifest', '-m', action='store_true',
                           help='生成依赖清单')

    run_parser = subparsers.add_parser('run', help='运行完整周期')
    run_parser.add_argument('--force', '-f', action='store_true',
                          help='强制同步')

    start_parser = subparsers.add_parser('start', help='启动调度器')
    start_parser.add_argument('--daemon', '-d', action='store_true',
                             help='后台运行')

    status_parser = subparsers.add_parser('status', help='查看状态')

    args = parser.parse_args()

    project_path = Path(__file__).parent.parent.parent / args.project
    config_path = Path(__file__).parent / args.config

    system = SyncSystem(str(config_path), str(project_path))

    if args.command == 'status':
        system.initialize()
        if system.scheduler:
            state = system.scheduler.version_tracker.load_state()
            print(f"\n{'='*60}")
            print(f"同步系统状态")
            print(f"{'='*60}")
            print(f"最后同步时间: {state.last_sync_time or '从未同步'}")
            print(f"最后同步状态: {state.last_sync_status.value}")
            print(f"最后版本: {state.last_version or 'N/A'}")
            print(f"同步次数: {state.sync_count}")
            print(f"失败次数: {state.failure_count}")
            if state.last_error:
                print(f"最后错误: {state.last_error}")
        return

    if args.command == 'sync':
        system.initialize()
        result = system.run_sync(force=args.force)
        print(f"\n同步状态: {result.status.value}")
        print(f"更新文件: {result.files_updated}")
        print(f"新增文件: {result.files_added}")
        print(f"版本: {result.version or 'N/A'}")
        print(f"耗时: {result.duration_seconds:.2f}秒")
        if result.errors:
            print(f"错误: {result.errors}")
        return

    if args.command == 'test':
        system.initialize()
        result = system.run_tests(paths=args.paths)
        print(f"\n测试完成: {result.total_tests} 个测试")
        print(f"通过: {result.passed} ✅")
        print(f"失败: {result.failed} ❌")
        print(f"警告: {result.warnings} ⚠️")
        print(f"报告: {result.report_path}")
        return

    if args.command == 'dep':
        system.initialize()
        report = system.check_dependencies()
        print(f"\n依赖检查:")
        print(f"总计: {report.total}")
        print(f"已安装: {report.installed}")
        print(f"缺失: {report.missing}")
        if report.recommendations:
            print(f"\n建议:")
            for rec in report.recommendations:
                print(f"  ⚠️ {rec}")

        if args.manifest:
            manifest_path = system.dep_manager.generate_manifest()
            print(f"\n依赖清单: {manifest_path}")
        return

    if args.command == 'run':
        system.initialize()
        results = system.run_full_cycle(force_sync=args.force)
        print(f"\n{'='*60}")
        print(f"完整周期执行结果")
        print(f"{'='*60}")
        print(f"开始时间: {results['cycle_start']}")
        print(f"结束时间: {results['cycle_end']}")
        print(f"总耗时: {results['duration_seconds']:.2f}秒")
        print(f"成功: {results['success']}")

        if results.get('sync'):
            print(f"\n同步结果:")
            print(f"  状态: {results['sync']['status']}")
            print(f"  更新文件: {results['sync']['files_updated']}")
            print(f"  版本: {results['sync']['version']}")

        if results.get('tests'):
            print(f"\n测试结果:")
            print(f"  总计: {results['tests']['total']}")
            print(f"  通过: {results['tests']['passed']}")
            print(f"  失败: {results['tests']['failed']}")
            print(f"  通过率: {results['tests']['pass_rate']}")

        if results.get('dependencies'):
            print(f"\n依赖状态:")
            print(f"  总计: {results['dependencies']['total']}")
            print(f"  已安装: {results['dependencies']['installed']}")
            print(f"  缺失: {results['dependencies']['missing']}")

        if results.get('errors'):
            print(f"\n错误:")
            for err in results['errors']:
                print(f"  ❌ {err}")
        return

    if args.command == 'start':
        system.initialize()
        if args.daemon:
            system.start_scheduler()
            print("调度器已在后台启动，按 Ctrl+C 停止")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                system.stop_scheduler()
        else:
            system.run_full_cycle()
        return

    parser.print_help()


if __name__ == "__main__":
    main()
