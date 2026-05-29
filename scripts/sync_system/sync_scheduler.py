#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sync Scheduler - 自动化定时同步调度器
用于定期同步原项目文档更新
"""

import os
import sys
import json
import time
import hashlib
import configparser
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
import threading
import subprocess
import requests
from urllib.parse import urljoin


class SyncStatus(Enum):
    """同步状态"""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class ScheduleFrequency(Enum):
    """同步频率"""
    MANUAL = "manual"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


@dataclass
class SyncVersion:
    """版本信息"""
    tag: str
    version: str
    commit_hash: str
    timestamp: str
    message: str


@dataclass
class SyncState:
    """同步状态"""
    last_sync_time: Optional[str] = None
    last_sync_status: SyncStatus = SyncStatus.IDLE
    last_version: Optional[str] = None
    last_commit_hash: Optional[str] = None
    sync_count: int = 0
    failure_count: int = 0
    last_error: Optional[str] = None


@dataclass
class SyncResult:
    """同步结果"""
    status: SyncStatus
    timestamp: str
    duration_seconds: float
    files_updated: int = 0
    files_added: int = 0
    files_deleted: int = 0
    version: Optional[str] = None
    changes: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ConfigLoader:
    """配置加载器"""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = configparser.ConfigParser()
        self._load()

    def _load(self):
        """加载配置文件"""
        if self.config_path.exists():
            self.config.read(self.config_path, encoding='utf-8')
        else:
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """获取配置值"""
        try:
            return self.config.get(section, key)
        except:
            return fallback

    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        try:
            return self.config.getint(section, key)
        except:
            return fallback

    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        try:
            return self.config.getboolean(section, key)
        except:
            return fallback

    def get_list(self, section: str, key: str, fallback: List = None) -> List:
        value = self.get(section, key, "")
        if value:
            return [item.strip() for item in value.split(",")]
        return fallback or []


class VersionTracker:
    """版本跟踪器"""

    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.version_file = state_dir / "version.json"
        self.sync_history_file = state_dir / "sync_history.json"

    def load_state(self) -> SyncState:
        """加载同步状态"""
        if self.version_file.exists():
            with open(self.version_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['last_sync_status'] = SyncStatus(data.get('last_sync_status', 'idle'))
                return SyncState(**data)
        return SyncState()

    def save_state(self, state: SyncState):
        """保存同步状态"""
        data = asdict(state)
        data['last_sync_status'] = state.last_sync_status.value
        with open(self.version_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_history(self) -> List[SyncResult]:
        """加载同步历史"""
        if self.sync_history_file.exists():
            with open(self.sync_history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    item['status'] = SyncStatus(item['status'])
                return [SyncResult(**item) for item in data]
        return []

    def save_history(self, history: List[SyncResult]):
        """保存同步历史"""
        data = []
        for item in history[-100:]:
            d = asdict(item)
            d['status'] = item.status.value
            data.append(d)
        with open(self.sync_history_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class GitHubSync:
    """GitHub 同步器"""

    def __init__(self, repo_url: str, branch: str, token: Optional[str] = None):
        self.repo_url = repo_url
        self.branch = branch
        self.token = token
        self.api_base = "https://api.github.com"

        parts = repo_url.rstrip('/').replace('https://github.com/', '').replace('http://github.com/', '')
        self.owner, self.repo = parts.split('/')

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Webnovel-Writer-Sync/1.0"
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    def get_latest_commit(self) -> Dict[str, Any]:
        """获取最新提交"""
        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/commits/{self.branch}"
        response = requests.get(url, headers=self._get_headers(), timeout=30)
        response.raise_for_status()
        return response.json()

    def get_commits_since(self, since: datetime) -> List[Dict[str, Any]]:
        """获取指定时间后的提交"""
        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/commits"
        params = {
            "sha": self.branch,
            "since": since.isoformat(),
            "per_page": 100
        }
        response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def get_file_content(self, file_path: str, ref: str = None) -> bytes:
        """获取文件内容"""
        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/contents/{file_path}"
        params = {"ref": ref or self.branch}
        response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        if data.get('encoding') == 'base64':
            import base64
            return base64.b64decode(data['content'])
        return data['content'].encode('utf-8')

    def get_directory_contents(self, path: str = "") -> List[Dict[str, Any]]:
        """获取目录内容"""
        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/contents/{path}"
        params = {"ref": self.branch}
        response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def get_tags(self) -> List[Dict[str, Any]]:
        """获取版本标签"""
        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/tags"
        response = requests.get(url, headers=self._get_headers(), timeout=30)
        response.raise_for_status()
        return response.json()

    def get_latest_release(self) -> Optional[Dict[str, Any]]:
        """获取最新 release"""
        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/releases/latest"
        response = requests.get(url, headers=self._get_headers(), timeout=30)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()


class SyncScheduler:
    """同步调度器"""

    def __init__(self, config_path: str, local_project_path: str):
        self.config = ConfigLoader(config_path)
        self.local_project_path = Path(local_project_path)

        self.sync_source = self.config.get('sync_source', 'repo_url')
        self.sync_branch = self.config.get('sync_source', 'branch', fallback='master')
        self.docs_paths = self.config.get_list('sync_source', 'docs_paths', fallback=['docs'])

        self.frequency = ScheduleFrequency(self.config.get('schedule', 'frequency', fallback='daily'))
        self.weekly_day = self.config.get_int('schedule', 'weekly_day', fallback=0)
        self.daily_time = self.config.get('schedule', 'daily_time', fallback='03:00')

        self.state_dir = Path(self.config.get('storage', 'state_dir', fallback='.sync_status'))
        self.cache_dir = Path(self.config.get('storage', 'cache_dir', fallback='.sync_cache'))
        self.log_dir = Path(self.config.get('logging', 'log_dir', fallback='scripts/sync_system/logs'))

        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.version_tracker = VersionTracker(self.state_dir)
        self.github_sync = GitHubSync(self.sync_source, self.sync_branch)

        self.logger = self._setup_logger()
        self._running = False
        self._scheduler_thread: Optional[threading.Thread] = None

    def _setup_logger(self) -> logging.Logger:
        """设置日志器"""
        logger = logging.getLogger("SyncScheduler")
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            self.config.get('logging', 'format', fallback='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )

        log_file = self.log_dir / f"sync_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        if self.config.get_bool('logging', 'console_output', True):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        return logger

    def should_sync(self) -> bool:
        """检查是否应该同步"""
        if self.frequency == ScheduleFrequency.MANUAL:
            return False

        state = self.version_tracker.load_state()
        if not state.last_sync_time:
            return True

        last_sync = datetime.fromisoformat(state.last_sync_time)
        now = datetime.now()

        if self.frequency == ScheduleFrequency.HOURLY:
            return (now - last_sync) >= timedelta(hours=1)
        elif self.frequency == ScheduleFrequency.DAILY:
            return (now - last_sync) >= timedelta(days=1)
        elif self.frequency == ScheduleFrequency.WEEKLY:
            return (now - last_sync) >= timedelta(weeks=1)

        return True

    def get_pending_changes(self) -> List[Dict[str, Any]]:
        """获取待同步的变更"""
        state = self.version_tracker.load_state()
        changes = []

        if state.last_sync_time:
            last_sync = datetime.fromisoformat(state.last_sync_time)
            commits = self.github_sync.get_commits_since(last_sync)

            for commit in commits:
                commit_date = datetime.fromisoformat(
                    commit['commit']['committer']['date'].replace('Z', '+00:00')
                )
                if commit_date > last_sync:
                    changes.append({
                        'sha': commit['sha'],
                        'message': commit['commit']['message'],
                        'date': commit['commit']['committer']['date'],
                        'author': commit['commit']['author']['name']
                    })

        return changes

    def sync_file(self, remote_path: str, local_path: Path) -> bool:
        """同步单个文件"""
        try:
            content = self.github_sync.get_file_content(remote_path)
            local_path.parent.mkdir(parents=True, exist_ok=True)

            with open(local_path, 'wb') as f:
                f.write(content)

            self.logger.info(f"已同步: {remote_path} -> {local_path}")
            return True
        except Exception as e:
            self.logger.error(f"同步文件失败 {remote_path}: {e}")
            return False

    def sync_directory(self, remote_path: str, local_path: Path) -> Dict[str, Any]:
        """同步目录"""
        results = {
            'updated': 0,
            'added': 0,
            'deleted': 0,
            'errors': []
        }

        try:
            contents = self.github_sync.get_directory_contents(remote_path)

            for item in contents:
                item_remote_path = item['path']
                item_local_path = local_path / Path(item['name'])

                if item['type'] == 'file':
                    if self.sync_file(item_remote_path, item_local_path):
                        results['updated'] += 1
                    else:
                        results['errors'].append(f"文件同步失败: {item_remote_path}")
                elif item['type'] == 'dir':
                    sub_results = self.sync_directory(item_remote_path, item_local_path)
                    results['updated'] += sub_results['updated']
                    results['added'] += sub_results['added']
                    results['errors'].extend(sub_results['errors'])

        except Exception as e:
            self.logger.error(f"同步目录失败 {remote_path}: {e}")
            results['errors'].append(f"目录同步失败: {remote_path} - {str(e)}")

        return results

    def run_sync(self, force: bool = False) -> SyncResult:
        """执行同步"""
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        result = SyncResult(
            status=SyncStatus.RUNNING,
            timestamp=timestamp,
            duration_seconds=0
        )

        self.logger.info(f"开始同步任务 at {timestamp}")

        if not force and not self.should_sync():
            result.status = SyncStatus.SKIPPED
            result.duration_seconds = time.time() - start_time
            self.logger.info("跳过同步 - 未到预定时间")
            return result

        try:
            changes = self.get_pending_changes()
            self.logger.info(f"发现 {len(changes)} 个待同步变更")

            if len(changes) == 0:
                result.status = SyncStatus.SUCCESS
                result.duration_seconds = time.time() - start_time
                self.logger.info("没有需要同步的更新")
                return result

            total_results = {'updated': 0, 'added': 0, 'deleted': 0, 'errors': []}

            for docs_path in self.docs_paths:
                local_path = self.local_project_path / docs_path
                sync_results = self.sync_directory(docs_path, local_path)
                total_results['updated'] += sync_results['updated']
                total_results['added'] += sync_results['added']
                total_results['errors'].extend(sync_results['errors'])

            latest_commit = self.github_sync.get_latest_commit()
            latest_version = latest_commit['sha'][:7]

            state = self.version_tracker.load_state()
            state.last_sync_time = timestamp
            state.last_sync_status = SyncStatus.SUCCESS
            state.last_version = latest_version
            state.last_commit_hash = latest_commit['sha']
            state.sync_count += 1
            state.failure_count = 0
            self.version_tracker.save_state(state)

            result.status = SyncStatus.SUCCESS if not total_results['errors'] else SyncStatus.PARTIAL
            result.files_updated = total_results['updated']
            result.files_added = total_results['added']
            result.version = latest_version
            result.errors = total_results['errors']
            result.changes = changes

            self.logger.info(
                f"同步完成: {result.files_updated} 个文件更新, "
                f"版本 {latest_version}, 耗时 {result.duration_seconds:.2f}秒"
            )

        except Exception as e:
            result.status = SyncStatus.FAILED
            result.errors.append(str(e))
            self.logger.error(f"同步失败: {e}")

            state = self.version_tracker.load_state()
            state.last_sync_status = SyncStatus.FAILED
            state.failure_count += 1
            state.last_error = str(e)
            self.version_tracker.save_state(state)

        result.duration_seconds = time.time() - start_time
        return result

    def start_scheduler(self):
        """启动调度器"""
        if self._running:
            self.logger.warning("调度器已在运行")
            return

        self._running = True
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        self.logger.info("调度器已启动")

    def stop_scheduler(self):
        """停止调度器"""
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=10)
        self.logger.info("调度器已停止")

    def _scheduler_loop(self):
        """调度器主循环"""
        while self._running:
            try:
                if self.should_sync():
                    result = self.run_sync()
                    self._on_sync_complete(result)

                check_interval = self.config.get_int('version_tracking', 'check_interval', 60)
                for _ in range(check_interval * 60):
                    if not self._running:
                        break
                    time.sleep(1)

            except Exception as e:
                self.logger.error(f"调度器异常: {e}")
                time.sleep(60)

    def _on_sync_complete(self, result: SyncResult):
        """同步完成回调"""
        history = self.version_tracker.load_history()
        history.append(result)
        self.version_tracker.save_history(history)

        if result.status == SyncStatus.FAILED:
            self._handle_sync_failure(result)
        elif result.status == SyncStatus.SUCCESS:
            self._handle_sync_success(result)

    def _handle_sync_success(self, result: SyncResult):
        """处理同步成功"""
        self.logger.info(f"同步成功通知: {result.files_updated} 个文件更新")

    def _handle_sync_failure(self, result: SyncResult):
        """处理同步失败"""
        max_retries = self.config.get_int('error_handling', 'max_retries', 3)
        state = self.version_tracker.load_state()

        if state.failure_count < max_retries:
            self.logger.info(f"尝试自动重试 ({state.failure_count}/{max_retries})")
            retry_interval = self.config.get_int('error_handling', 'retry_interval', 300)
            time.sleep(retry_interval)
            retry_result = self.run_sync(force=True)
            self._on_sync_complete(retry_result)
        else:
            self.logger.error(f"同步失败已达到最大重试次数 ({max_retries})")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Webnovel Writer Sync Scheduler")
    parser.add_argument('--config', '-c', default='config/sync_config.ini',
                       help='配置文件路径')
    parser.add_argument('--project', '-p', default='../..',
                       help='本地项目路径')
    parser.add_argument('--sync', '-s', action='store_true',
                       help='立即执行同步')
    parser.add_argument('--status', action='store_true',
                       help='显示同步状态')
    parser.add_argument('--start', action='store_true',
                       help='启动调度器')
    parser.add_argument('--stop', action='store_true',
                       help='停止调度器')
    parser.add_argument('--force', '-f', action='store_true',
                       help='强制同步')

    args = parser.parse_args()

    config_path = Path(__file__).parent / args.config
    project_path = Path(__file__).parent / args.project

    scheduler = SyncScheduler(str(config_path), str(project_path))

    if args.status:
        state = scheduler.version_tracker.load_state()
        print(f"\n=== 同步状态 ===")
        print(f"最后同步时间: {state.last_sync_time or '从未同步'}")
        print(f"最后同步状态: {state.last_sync_status.value}")
        print(f"最后版本: {state.last_version or 'N/A'}")
        print(f"同步次数: {state.sync_count}")
        print(f"失败次数: {state.failure_count}")
        if state.last_error:
            print(f"最后错误: {state.last_error}")
        return

    if args.sync:
        result = scheduler.run_sync(force=args.force)
        print(f"\n=== 同步结果 ===")
        print(f"状态: {result.status.value}")
        print(f"更新时间: {result.timestamp}")
        print(f"耗时: {result.duration_seconds:.2f}秒")
        print(f"文件更新: {result.files_updated}")
        print(f"文件新增: {result.files_added}")
        print(f"版本: {result.version or 'N/A'}")
        if result.errors:
            print(f"错误: {result.errors}")
        return

    if args.start:
        scheduler.start_scheduler()
        print("调度器已在后台启动，按 Ctrl+C 停止")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            scheduler.stop_scheduler()
        return

    parser.print_help()


if __name__ == "__main__":
    main()
