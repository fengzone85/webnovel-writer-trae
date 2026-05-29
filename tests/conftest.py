#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试配置文件
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

@pytest.fixture
def temp_project():
    """创建临时测试项目"""
    temp_dir = tempfile.mkdtemp()
    project_path = Path(temp_dir)

    (project_path / ".story-system").mkdir()
    (project_path / ".webnovel").mkdir()
    (project_path / "章节").mkdir()
    (project_path / "设定集").mkdir()
    (project_path / "大纲").mkdir()

    yield project_path

    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def sample_chapter():
    """示例章节内容"""
    return """# 第一章 觉醒

这一天，天气晴朗。

主角张三走在回家的路上，突然一道闪电劈中了他。

## 情节发展

就在这时，他发现自己获得了异能。

### 获得能力

```
- 火球术：可以发射火球
- 冰冻术：可以冰冻敌人
```

> "我居然获得了异能！" 张三兴奋地想到。

## 钩子

就在张三以为自己要起飞的时候，一个神秘的声音在他脑海中响起：
"想要变强吗？完成任务吧！"

## 爽点

张三一挥手，一个巨大的火球出现在手中。
"这就是力量的感觉吗？"
"""

@pytest.fixture
def sample_master_setting():
    """示例主设定"""
    return {
        "project_name": "测试小说",
        "genre": "都市异能",
        "main_character": "张三",
        "golden_finger": "超级系统",
        "strand_config": {
            "quest_ratio": 0.6,
            "fire_ratio": 0.25,
            "constellation_ratio": 0.15
        }
    }
