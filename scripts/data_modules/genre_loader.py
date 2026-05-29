#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
题材加载器模块
支持按名称加载题材模板
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional

REFERENCES_DIR = Path(__file__).parent.parent.parent / "references"
GENRES_DIR = REFERENCES_DIR / "genres"

class GenreTemplate:
    """题材模板类"""

    def __init__(self, name: str, content: Dict[str, Any]):
        self.name = name
        self.content = content

    @property
    def strand_config(self) -> Dict[str, float]:
        """获取Strand配置"""
        return self.content.get("strand_config", {
            "quest_ratio": 0.6,
            "fire_ratio": 0.2,
            "constellation_ratio": 0.2
        })

    @property
    def cool_point_types(self) -> List[str]:
        """获取爽点类型列表"""
        return self.content.get("cool_points", [])

    @property
    def hook_types(self) -> List[str]:
        """获取钩子类型列表"""
        return self.content.get("hooks", [])

    def __str__(self):
        return f"GenreTemplate({self.name})"

    def __repr__(self):
        return self.__str__()

def load_genre_template(genre_name: str) -> Optional[GenreTemplate]:
    """
    加载指定题材模板

    Args:
        genre_name: 题材名称（如：都市异能、修仙、玄幻）

    Returns:
        GenreTemplate 对象，失败返回 None
    """
    genre_file = GENRES_DIR / f"{genre_name}.md"

    if not genre_file.exists():
        return None

    try:
        content = parse_genre_template(genre_file)
        return GenreTemplate(genre_name, content)
    except Exception as e:
        print(f"Error loading genre {genre_name}: {e}")
        return None

def parse_genre_template(file_path: Path) -> Dict[str, Any]:
    """
    解析题材模板文件

    Args:
        file_path: 题材模板文件路径

    Returns:
        解析后的字典
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_content = f.read()

    result = {
        "name": file_path.stem,
        "raw_content": raw_content
    }

    current_section = None
    sections = {}

    for line in raw_content.split('\n'):
        line = line.strip()

        if line.startswith('# ') and not line.startswith('##'):
            result["title"] = line[2:].strip()

        elif line.startswith('## '):
            current_section = line[3:].strip().lower()
            sections[current_section] = []

        elif current_section and line:
            sections[current_section].append(line)

    if 'strand 比例建议' in sections:
        strand_text = '\n'.join(sections['strand 比例建议'])
        strand_config = parse_strand_config(strand_text)
        result["strand_config"] = strand_config

    if '爽点类型' in sections:
        result["cool_points"] = parse_bullet_list(sections['爽点类型'])

    if '钩子类型' in sections:
        result["hooks"] = parse_bullet_list(sections['钩子类型'])

    if '核心元素' in sections:
        result["core_elements"] = parse_bullet_list(sections['核心元素'])

    if '常见金手指' in sections:
        result["golden_fingers"] = parse_bullet_list(sections['常见金手指'])

    if '节奏模式' in sections:
        result["pacing_pattern"] = '\n'.join(sections['节奏模式'])

    if '参考作品' in sections:
        result["references"] = parse_bullet_list(sections['参考作品'])

    if '题材特征' in sections:
        result["features"] = parse_bullet_list(sections['题材特征'])

    return result

def parse_strand_config(text: str) -> Dict[str, float]:
    """解析Strand配置"""
    config = {"quest_ratio": 0.6, "fire_ratio": 0.2, "constellation_ratio": 0.2}

    patterns = [
        (r'Quest线.*?(\d+)%', 'quest_ratio'),
        (r'Fire线.*?(\d+)%', 'fire_ratio'),
        (r'Constellation线.*?(\d+)%', 'constellation_ratio'),
    ]

    for pattern, key in patterns:
        match = re.search(pattern, text)
        if match:
            config[key] = int(match.group(1)) / 100.0

    return config

def parse_bullet_list(lines: List[str]) -> List[str]:
    """解析列表项"""
    items = []
    for line in lines:
        line = line.strip()
        if line.startswith('- ') or line.startswith('* '):
            items.append(line[2:].strip())
        elif line.startswith('1.') or line.startswith('1、'):
            items.append(re.sub(r'^\d+[.)、]\s*', '', line).strip())
        elif line and not line.startswith('#'):
            items.append(line)
    return items

def list_available_genres() -> List[str]:
    """列出所有可用题材"""
    if not GENRES_DIR.exists():
        return []
    return [f.stem for f in GENRES_DIR.glob("*.md")]

def get_genre_summary(genre_name: str) -> Optional[str]:
    """获取题材摘要"""
    template = load_genre_template(genre_name)
    if not template:
        return None

    content = template.content
    summary_parts = [f"## {template.name}"]

    if "title" in content:
        summary_parts.append(f"\n{content['title']}")

    if "core_elements" in content:
        summary_parts.append("\n### 核心元素")
        for elem in content["core_elements"][:5]:
            summary_parts.append(f"- {elem}")

    if "strand_config" in content:
        sc = content["strand_config"]
        summary_parts.append(f"\n### Strand 配置")
        summary_parts.append(f"- Quest: {sc.get('quest_ratio', 0):.0%}")
        summary_parts.append(f"- Fire: {sc.get('fire_ratio', 0):.0%}")
        summary_parts.append(f"- Constellation: {sc.get('constellation_ratio', 0):.0%}")

    return '\n'.join(summary_parts)

if __name__ == "__main__":
    genres = list_available_genres()
    print(f"可用题材 ({len(genres)}):")
    for g in genres:
        print(f"  - {g}")
