#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
国际化模块
支持多语言切换
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache


class I18n:
    """国际化类"""

    SUPPORTED_LANGUAGES = ["zh_CN", "en_US"]
    DEFAULT_LANGUAGE = "zh_CN"

    def __init__(self, language: Optional[str] = None):
        self.language = language or self._detect_language()
        self.translations: Dict[str, Any] = {}
        self._load_translations()

    def _detect_language(self) -> str:
        """检测系统语言"""
        locale = os.environ.get("LANG", "").split(".")[0]
        if locale.startswith("zh"):
            return "zh_CN"
        elif locale.startswith("en"):
            return "en_US"
        return self.DEFAULT_LANGUAGE

    def _load_translations(self):
        """加载翻译文件"""
        i18n_dir = Path(__file__).parent

        for lang in [self.language, self.DEFAULT_LANGUAGE]:
            trans_file = i18n_dir / f"{lang}.json"
            if trans_file.exists():
                with open(trans_file, 'r', encoding='utf-8') as f:
                    self.translations.update(json.load(f))

    def get(self, key: str, default: Optional[str] = None) -> str:
        """获取翻译"""
        keys = key.split(".")
        value = self.translations

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default or key

        return value if isinstance(value, str) else (default or key)

    def t(self, key: str, **kwargs) -> str:
        """翻译并格式化"""
        template = self.get(key)
        if kwargs:
            try:
                return template.format(**kwargs)
            except (KeyError, ValueError):
                return template
        return template

    def set_language(self, language: str):
        """设置语言"""
        if language in self.SUPPORTED_LANGUAGES:
            self.language = language
            self.translations.clear()
            self._load_translations()

    @classmethod
    def list_languages(cls) -> list:
        """列出支持的语言"""
        return cls.SUPPORTED_LANGUAGES


@lru_cache(maxsize=1)
def get_i18n(language: Optional[str] = None) -> I18n:
    """获取国际化实例"""
    return I18n(language)


def t(key: str, language: Optional[str] = None, **kwargs) -> str:
    """便捷翻译函数"""
    i18n = get_i18n(language)
    return i18n.t(key, **kwargs)


def set_language(language: str):
    """设置语言"""
    i18n = get_i18n()
    i18n.set_language(language)
    get_i18n.cache_clear()
    get_i18n(language)


def get_current_language() -> str:
    """获取当前语言"""
    return get_i18n().language
