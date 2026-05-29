#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notification System - 通知系统
用于同步状态、测试结果、异常情况的通知
"""

import os
import json
import smtplib
import configparser
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import threading
import time
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from queue import Queue


class NotificationType(Enum):
    """通知类型"""
    SYNC_SUCCESS = "sync_success"
    SYNC_FAILURE = "sync_failure"
    TEST_PASSED = "test_passed"
    TEST_FAILED = "test_failed"
    VERSION_MISMATCH = "version_mismatch"
    DEPENDENCY_ISSUE = "dependency_issue"
    ERROR = "error"
    INFO = "info"
    WARNING = "warning"


class NotificationChannel(Enum):
    """通知渠道"""
    CONSOLE = "console"
    FILE = "file"
    WEBHOOK = "webhook"
    EMAIL = "email"


@dataclass
class Notification:
    """通知"""
    type: NotificationType
    title: str
    message: str
    timestamp: str
    data: Dict[str, Any] = field(default_factory=dict)
    channel: NotificationChannel = NotificationChannel.CONSOLE
    retry_count: int = 0


@dataclass
class NotificationResult:
    """通知结果"""
    success: bool
    channel: NotificationChannel
    message: str
    error: Optional[str] = None


class ConsoleNotifier:
    """控制台通知"""

    TYPE_COLORS = {
        NotificationType.SYNC_SUCCESS: "\033[92m",
        NotificationType.SYNC_FAILURE: "\033[91m",
        NotificationType.TEST_PASSED: "\033[92m",
        NotificationType.TEST_FAILED: "\033[91m",
        NotificationType.VERSION_MISMATCH: "\033[93m",
        NotificationType.DEPENDENCY_ISSUE: "\033[93m",
        NotificationType.ERROR: "\033[91m",
        NotificationType.WARNING: "\033[93m",
        NotificationType.INFO: "\033[94m",
    }
    COLOR_RESET = "\033[0m"

    def send(self, notification: Notification) -> NotificationResult:
        """发送控制台通知"""
        try:
            color = self.TYPE_COLORS.get(notification.type, "")
            print(f"{color}[{notification.type.value.upper()}]{self.COLOR_RESET} {notification.title}")
            print(f"  {notification.message}")
            if notification.data:
                print(f"  详情: {json.dumps(notification.data, ensure_ascii=False, indent=2)}")
            return NotificationResult(
                success=True,
                channel=NotificationChannel.CONSOLE,
                message="已发送到控制台"
            )
        except Exception as e:
            return NotificationResult(
                success=False,
                channel=NotificationChannel.CONSOLE,
                message="",
                error=str(e)
            )


class FileNotifier:
    """文件通知"""

    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.notification_file = self.log_dir / "notifications.json"

    def send(self, notification: Notification) -> NotificationResult:
        """发送文件通知"""
        try:
            notifications = []
            if self.notification_file.exists():
                with open(self.notification_file, 'r', encoding='utf-8') as f:
                    notifications = json.load(f)

            notifications.append({
                'type': notification.type.value,
                'title': notification.title,
                'message': notification.message,
                'timestamp': notification.timestamp,
                'data': notification.data,
                'channel': notification.channel.value
            })

            with open(self.notification_file, 'w', encoding='utf-8') as f:
                json.dump(notifications[-1000:], f, ensure_ascii=False, indent=2)

            return NotificationResult(
                success=True,
                channel=NotificationChannel.FILE,
                message=f"已保存到 {self.notification_file}"
            )
        except Exception as e:
            return NotificationResult(
                success=False,
                channel=NotificationChannel.FILE,
                message="",
                error=str(e)
            )


class WebhookNotifier:
    """Webhook 通知"""

    def __init__(self, url: str, auth_token: Optional[str] = None, retry_count: int = 3):
        self.url = url
        self.auth_token = auth_token
        self.retry_count = retry_count

    def send(self, notification: Notification) -> NotificationResult:
        """发送 Webhook 通知"""
        if not self.url:
            return NotificationResult(
                success=False,
                channel=NotificationChannel.WEBHOOK,
                message="",
                error="Webhook URL 未配置"
            )

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Webnovel-Writer-Sync/1.0"
        }
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        payload = {
            "type": notification.type.value,
            "title": notification.title,
            "message": notification.message,
            "timestamp": notification.timestamp,
            "data": notification.data
        }

        for attempt in range(self.retry_count):
            try:
                response = requests.post(
                    self.url,
                    json=payload,
                    headers=headers,
                    timeout=10
                )

                if response.status_code in [200, 201, 202, 204]:
                    return NotificationResult(
                        success=True,
                        channel=NotificationChannel.WEBHOOK,
                        message=f"Webhook 发送成功 (HTTP {response.status_code})"
                    )
                else:
                    last_error = f"HTTP {response.status_code}"

            except requests.exceptions.Timeout:
                last_error = "请求超时"
            except requests.exceptions.RequestException as e:
                last_error = str(e)

            if attempt < self.retry_count - 1:
                time.sleep(2 ** attempt)

        return NotificationResult(
            success=False,
            channel=NotificationChannel.WEBHOOK,
            message="",
            error=f"重试 {self.retry_count} 次后失败: {last_error}"
        )


class EmailNotifier:
    """邮件通知"""

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        use_tls: bool,
        sender: str,
        recipients: List[str],
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.use_tls = use_tls
        self.sender = sender
        self.recipients = recipients
        self.username = username or sender
        self.password = password

    def send(self, notification: Notification) -> NotificationResult:
        """发送邮件通知"""
        if not self.smtp_server:
            return NotificationResult(
                success=False,
                channel=NotificationChannel.EMAIL,
                message="",
                error="SMTP 服务器未配置"
            )

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{notification.type.value.upper()}] {notification.title}"
            msg['From'] = self.sender
            msg['To'] = ', '.join(self.recipients)

            html_content = self._generate_html(notification)
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                if self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)

            return NotificationResult(
                success=True,
                channel=NotificationChannel.EMAIL,
                message=f"邮件已发送到 {', '.join(self.recipients)}"
            )

        except Exception as e:
            return NotificationResult(
                success=False,
                channel=NotificationChannel.EMAIL,
                message="",
                error=str(e)
            )

    def _generate_html(self, notification: Notification) -> str:
        """生成 HTML 内容"""
        type_colors = {
            NotificationType.SYNC_SUCCESS: "#28a745",
            NotificationType.SYNC_FAILURE: "#dc3545",
            NotificationType.TEST_PASSED: "#28a745",
            NotificationType.TEST_FAILED: "#dc3545",
            NotificationType.VERSION_MISMATCH: "#ffc107",
            NotificationType.DEPENDENCY_ISSUE: "#ffc107",
            NotificationType.ERROR: "#dc3545",
            NotificationType.WARNING: "#ffc107",
            NotificationType.INFO: "#17a2b8",
        }
        color = type_colors.get(notification.type, "#6c757d")

        data_str = json.dumps(notification.data, ensure_ascii=False, indent=2)

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .header {{ background-color: {color}; color: white; padding: 20px; }}
                .content {{ padding: 20px; }}
                .data {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; }}
                .footer {{ padding: 20px; color: #6c757d; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>{notification.title}</h2>
            </div>
            <div class="content">
                <p>{notification.message}</p>
                <p><strong>时间:</strong> {notification.timestamp}</p>
                <p><strong>类型:</strong> {notification.type.value}</p>
                <div class="data">
                    <h4>详细信息:</h4>
                    <pre>{data_str}</pre>
                </div>
            </div>
            <div class="footer">
                <p>此邮件由 Webnovel Writer Sync System 自动发送</p>
            </div>
        </body>
        </html>
        """


class NotificationManager:
    """通知管理器"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = configparser.ConfigParser()
        if config_path and Path(config_path).exists():
            self.config.read(config_path, encoding='utf-8')

        self.log_dir = Path(self.config.get('logging', 'log_dir', fallback='scripts/sync_system/logs'))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logger = self._setup_logger()

        self.channels: Dict[NotificationChannel, Any] = {}
        self.notification_queue: Queue = Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._running = False

        self._init_channels()

    def _setup_logger(self) -> logging.Logger:
        """设置日志器"""
        logger = logging.getLogger("NotificationManager")
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        log_file = self.log_dir / f"notification_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    def _init_channels(self):
        """初始化通知渠道"""
        enabled_channels = self.config.get('notifications', 'channels', fallback='console,file')
        channel_list = [ch.strip() for ch in enabled_channels.split(',')]

        if 'console' in channel_list:
            self.channels[NotificationChannel.CONSOLE] = ConsoleNotifier()

        if 'file' in channel_list:
            self.channels[NotificationChannel.FILE] = FileNotifier(self.log_dir)

        if 'webhook' in channel_list:
            webhook_url = self.config.get('notifications', 'webhook_url', fallback='')
            webhook_token = self.config.get('notifications', 'webhook_token', fallback='')
            webhook_retry = self.config.getint('notifications', 'webhook_retry_count', fallback=3)
            self.channels[NotificationChannel.WEBHOOK] = WebhookNotifier(
                webhook_url, webhook_token, webhook_retry
            )

        if 'email' in channel_list:
            email_config = {
                'smtp_server': self.config.get('notifications', 'email_smtp_server', fallback=''),
                'smtp_port': self.config.getint('notifications', 'email_smtp_port', fallback=587),
                'use_tls': self.config.getboolean('notifications', 'email_use_tls', fallback=True),
                'sender': self.config.get('notifications', 'email_sender', fallback=''),
                'recipients': self.config.get('notifications', 'email_recipients', fallback='').split(',') if self.config.get('notifications', 'email_recipients', fallback='') else [],
            }
            if email_config['smtp_server']:
                self.channels[NotificationChannel.EMAIL] = EmailNotifier(**email_config)

    def start(self):
        """启动通知管理器"""
        if self._running:
            return

        self._running = True
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()
        self.logger.info("通知管理器已启动")

    def stop(self):
        """停止通知管理器"""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        self.logger.info("通知管理器已停止")

    def _process_queue(self):
        """处理通知队列"""
        while self._running:
            try:
                notification = self.notification_queue.get(timeout=1)
                self._send_notification(notification)
            except:
                continue

    def _send_notification(self, notification: Notification):
        """发送通知"""
        results = []

        for channel_type, channel in self.channels.items():
            notification.channel = channel_type
            result = channel.send(notification)
            results.append(result)

            if result.success:
                self.logger.info(f"通知发送成功 [{channel_type.value}]: {result.message}")
            else:
                self.logger.error(f"通知发送失败 [{channel_type.value}]: {result.error}")

    def notify(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        immediate: bool = False
    ):
        """发送通知"""
        notification = Notification(
            type=notification_type,
            title=title,
            message=message,
            timestamp=datetime.now().isoformat(),
            data=data or {}
        )

        if immediate:
            self._send_notification(notification)
        else:
            self.notification_queue.put(notification)

    def notify_sync_success(self, result: Dict[str, Any]):
        """通知同步成功"""
        self.notify(
            NotificationType.SYNC_SUCCESS,
            "文档同步成功",
            f"成功同步 {result.get('files_updated', 0)} 个文件",
            result
        )

    def notify_sync_failure(self, error: str, retry_count: int = 0):
        """通知同步失败"""
        self.notify(
            NotificationType.SYNC_FAILURE,
            "文档同步失败",
            f"同步失败: {error}",
            {'retry_count': retry_count}
        )

    def notify_test_result(self, passed: bool, result: Dict[str, Any]):
        """通知测试结果"""
        if passed:
            self.notify(
                NotificationType.TEST_PASSED,
                "兼容性测试通过",
                f"测试通过率: {result.get('pass_rate', 'N/A')}",
                result
            )
        else:
            self.notify(
                NotificationType.TEST_FAILED,
                "兼容性测试失败",
                f"失败项: {result.get('failed', 0)}",
                result
            )

    def notify_version_mismatch(self, expected: str, actual: str):
        """通知版本不匹配"""
        self.notify(
            NotificationType.VERSION_MISMATCH,
            "版本不匹配",
            f"期望版本 {expected}，实际版本 {actual}",
            {'expected': expected, 'actual': actual}
        )

    def notify_dependency_issue(self, missing: List[str]):
        """通知依赖问题"""
        self.notify(
            NotificationType.DEPENDENCY_ISSUE,
            "依赖问题",
            f"缺少 {len(missing)} 个依赖项",
            {'missing': missing}
        )


def main():
    """主函数 - 测试通知系统"""
    import argparse

    parser = argparse.ArgumentParser(description="Notification System Test")
    parser.add_argument('--config', '-c', default='../config/sync_config.ini',
                       help='配置文件路径')
    parser.add_argument('--type', '-t', default='info',
                       choices=['sync_success', 'sync_failure', 'test_passed',
                               'test_failed', 'version_mismatch', 'dependency_issue',
                               'error', 'info', 'warning'],
                       help='通知类型')
    parser.add_argument('--title', default='测试通知',
                       help='通知标题')
    parser.add_argument('--message', '-m', default='这是一条测试通知',
                       help='通知消息')

    args = parser.parse_args()

    config_path = Path(__file__).parent / args.config
    manager = NotificationManager(str(config_path) if config_path.exists() else None)

    notif_type = NotificationType(args.type)
    manager.notify(
        notif_type,
        args.title,
        args.message,
        {'test': True},
        immediate=True
    )

    print("通知已发送")


if __name__ == "__main__":
    main()
