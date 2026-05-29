#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误处理模块
提供统一的错误处理和日志记录
"""

import logging
import traceback
from typing import Optional, Callable, Any
from functools import wraps
from pathlib import Path

class WebnovelError(Exception):
    """基础异常类"""
    def __init__(self, message: str, code: str = "UNKNOWN", details: Optional[dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

class ProjectNotFoundError(WebnovelError):
    """项目未找到"""
    def __init__(self, path: str):
        super().__init__(
            f"项目未找到: {path}",
            code="PROJECT_NOT_FOUND",
            details={"path": path}
        )

class ChapterNotFoundError(WebnovelError):
    """章节未找到"""
    def __init__(self, chapter: str):
        super().__init__(
            f"章节未找到: {chapter}",
            code="CHAPTER_NOT_FOUND",
            details={"chapter": chapter}
        )

class StorySystemError(WebnovelError):
    """Story System 错误"""
    def __init__(self, message: str, phase: Optional[str] = None):
        super().__init__(
            message,
            code="STORY_SYSTEM_ERROR",
            details={"phase": phase} if phase else {}
        )

class RAGError(WebnovelError):
    """RAG 错误"""
    def __init__(self, message: str, api: Optional[str] = None):
        super().__init__(
            message,
            code="RAG_ERROR",
            details={"api": api} if api else {}
        )

class BackupError(WebnovelError):
    """备份错误"""
    def __init__(self, message: str, backup_id: Optional[str] = None):
        super().__init__(
            message,
            code="BACKUP_ERROR",
            details={"backup_id": backup_id} if backup_id else {}
        )

class ValidationError(WebnovelError):
    """验证错误"""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message,
            code="VALIDATION_ERROR",
            details={"field": field} if field else {}
        )


class ErrorHandler:
    """错误处理器"""

    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir
        if log_dir:
            log_dir.mkdir(parents=True, exist_ok=True)

        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """设置日志器"""
        logger = logging.getLogger("webnovel_writer")
        logger.setLevel(logging.DEBUG)

        if not logger.handlers:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

            if self.log_dir:
                file_handler = logging.FileHandler(
                    self.log_dir / "error.log",
                    encoding='utf-8'
                )
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)

        return logger

    def handle_error(self, error: Exception, context: Optional[dict] = None) -> dict:
        """处理错误"""
        if isinstance(error, WebnovelError):
            error_info = {
                "type": error.code,
                "message": error.message,
                "details": error.details,
                "context": context
            }
        else:
            error_info = {
                "type": "INTERNAL_ERROR",
                "message": str(error),
                "details": {"traceback": traceback.format_exc()},
                "context": context
            }

        self.logger.error(f"[{error_info['type']}] {error_info['message']}", extra=context)

        return error_info

    def log_warning(self, message: str, context: Optional[dict] = None):
        """记录警告"""
        self.logger.warning(message, extra=context or {})

    def log_info(self, message: str):
        """记录信息"""
        self.logger.info(message)

    def log_debug(self, message: str):
        """记录调试信息"""
        self.logger.debug(message)


def error_handler(func: Callable) -> Callable:
    """错误处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except WebnovelError:
            raise
        except Exception as e:
            logger = logging.getLogger("webnovel_writer")
            logger.error(f"Error in {func.__name__}: {e}")
            raise WebnovelError(
                f"执行失败: {str(e)}",
                code="EXECUTION_ERROR",
                details={"function": func.__name__}
            )
    return wrapper


def safe_execute(func: Callable, default: Any = None, *args, **kwargs) -> Any:
    """安全执行函数"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger = logging.getLogger("webnovel_writer")
        logger.error(f"Safe execute failed for {func.__name__}: {e}")
        return default


_global_error_handler: Optional[ErrorHandler] = None

def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler

def set_error_handler(handler: ErrorHandler):
    """设置全局错误处理器"""
    global _global_error_handler
    _global_error_handler = handler
