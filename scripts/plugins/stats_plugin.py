#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例插件 - 统计信息插件
"""

from dataclasses import dataclass
from plugins.plugin_system import Plugin, PluginInfo, HookType, hook


@dataclass
class WritingStats:
    """写作统计"""
    total_words: int = 0
    total_chapters: int = 0
    total_hooks: int = 0
    total_coolpoints: int = 0


class StatsPlugin(Plugin):
    """统计信息插件"""

    info = PluginInfo(
        name="stats",
        version="1.0.0",
        author="Webnovel Writer",
        description="收集和显示写作统计信息",
        hooks=[
            HookType.POST_WRITE,
            HookType.POST_COMMIT,
            HookType.POST_REVIEW
        ],
        commands=["stats"]
    )

    def __init__(self):
        super().__init__()
        self.stats = WritingStats()

    def on_load(self):
        """加载时初始化"""
        print(f"📊 StatsPlugin loaded")

    def execute(self, hook: HookType, *args, **kwargs) -> Any:
        """执行钩子"""
        if hook == HookType.POST_WRITE:
            return self.on_post_write(*args, **kwargs)
        elif hook == HookType.POST_COMMIT:
            return self.on_post_commit(*args, **kwargs)
        elif hook == HookType.POST_REVIEW:
            return self.on_post_review(*args, **kwargs)
        return None

    def on_post_write(self, chapter: int, word_count: int, **kwargs):
        """写作后钩子"""
        self.stats.total_words += word_count
        self.stats.total_chapters += 1
        print(f"📝 Chapter {chapter} written: {word_count} words")

    def on_post_commit(self, chapter: int, **kwargs):
        """提交后钩子"""
        print(f"✅ Chapter {chapter} committed")

    def on_post_review(self, chapter: int, result: dict, **kwargs):
        """审查后钩子"""
        print(f"🔍 Chapter {chapter} reviewed")

    def get_stats(self) -> WritingStats:
        """获取统计信息"""
        return self.stats

    def print_stats(self):
        """打印统计信息"""
        print("\n📊 Writing Statistics:")
        print(f"  Total Words: {self.stats.total_words}")
        print(f"  Total Chapters: {self.stats.total_chapters}")
        print(f"  Average Words/Chapter: {self.stats.total_words // max(1, self.stats.total_chapters)}")


def get_plugin():
    """获取插件实例"""
    return StatsPlugin()
