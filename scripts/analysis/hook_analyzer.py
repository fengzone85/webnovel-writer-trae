#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
钩子与爽点分析器
分析文本中的钩子和爽点
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class HookType(Enum):
    """钩子类型"""
    CLIFF_HANGER = "cliff_hanger"
    SUSPENSE = "suspense"
    REVERSAL = "reversal"
    TEASER = "teaser"
    MYSTERY = "mystery"
    EMOTIONAL = "emotional"
    CONFLICT = "conflict"
    foreshadow = "foreshadow"


class CoolPointType(Enum):
    """爽点类型"""
    SLAP_FACE = "slap_face"
    CRUSHING = "crushing"
    REVERSE_OPPORTUNE = "reverse_opportune"
    RARE_MONOPOLY = "rare_monopoly"
    BEAUTY_FAVOR = "beauty_favor"
    BREAKTHROUGH = "breakthrough"
    REVENGE = "revenge"
    FAME = "fame"
    WEALTH = "wealth"
    POWER = "power"


@dataclass
class Hook:
    """钩子"""
    type: HookType
    content: str
    position: int
    intensity: float
    description: str


@dataclass
class CoolPoint:
    """爽点"""
    type: CoolPointType
    content: str
    position: int
    intensity: float
    description: str


class HookPattern:
    """钩子模式"""
    PATTERNS = [
        (HookType.CLIFF_HANGER, r"(但是|然而|就在这时|突然|没想 到|谁知道|就在这时|结果|没想到)", 0.9),
        (HookType.SUSPENSE, r"(到底|究竟|是不是|会不会|秘密是|真相是)", 0.8),
        (HookType.REVERSAL, r"(没想到|出人意料|反转|意想不到|惊天逆转)", 0.9),
        (HookType.TEASER, r"(欲知后事|敬请期待|且听下回|悬念|吊胃口)", 0.7),
        (HookType.MYSTERY, r"(神秘|未知|隐藏|不为人知|秘密)", 0.8),
        (HookType.EMOTIONAL, r"(心动|心疼|感人|泪目|热血|激动)", 0.7),
        (HookType.CONFLICT, r"(冲突|矛盾|对立|对抗|较量|争夺)", 0.8),
        (HookType.foreshadow, r"(预示|征兆|暗示|伏笔|埋伏|铺垫)", 0.7),
    ]


class CoolPointPattern:
    """爽点模式"""
    PATTERNS = [
        (CoolPointType.SLAP_FACE, r"(打脸|装逼|打脸|狠狠打脸|piapia打脸)", 0.9),
        (CoolPointType.CRUSHING, r"(碾压|秒杀|一击必杀|秒杀|碾压局)", 0.9),
        (CoolPointType.REVERSE_OPPORTUNE, r"(逆袭|翻身|咸鱼翻身|逆天改命)", 0.9),
        (CoolPointType.RARE_MONOPOLY, r"(唯一|独有|稀有|独一份|独占|仅此一家)", 0.8),
        (CoolPointType.BEAUTY_FAVOR, r"(美人倾心|美女环绕|桃花运|倾慕)", 0.7),
        (CoolPointType.BREAKTHROUGH, r"(突破|晋升|升级|觉醒|顿悟|进化)", 0.8),
        (CoolPointType.REVENGE, r"(报仇|复仇|雪恨|报应|还回来)", 0.8),
        (CoolPointType.FAME, r"(成名|出名|闻名|声望|地位提升)", 0.7),
        (CoolPointType.WEALTH, r"(发财|赚钱|财富|暴富|金银财宝)", 0.7),
        (CoolPointType.POWER, r"(力量|实力|强大|称霸|制霸|无敌)", 0.8),
    ]


class HookCoolPointAnalyzer:
    """钩子与爽点分析器"""

    def __init__(self):
        self.hook_patterns = HookPattern.PATTERNS
        self.coolpoint_patterns = CoolPointPattern.PATTERNS

    def analyze_hooks(self, text: str) -> List[Hook]:
        """分析钩子"""
        hooks = []

        for hook_type, pattern, base_intensity in self.hook_patterns:
            for match in re.finditer(pattern, text):
                position = match.start()
                content = match.group()

                context_start = max(0, position - 20)
                context_end = min(len(text), position + len(content) + 20)
                context = text[context_start:context_end]

                hook = Hook(
                    type=hook_type,
                    content=content,
                    position=position,
                    intensity=base_intensity,
                    description=f"在位置{position}发现{hook_type.value}钩子"
                )
                hooks.append(hook)

        hooks.sort(key=lambda x: x.position)
        return hooks

    def analyze_coolpoints(self, text: str) -> List[CoolPoint]:
        """分析爽点"""
        coolpoints = []

        for cp_type, pattern, base_intensity in self.coolpoint_patterns:
            for match in re.finditer(pattern, text):
                position = match.start()
                content = match.group()

                context_start = max(0, position - 20)
                context_end = min(len(text), position + len(content) + 20)
                context = text[context_start:context_end]

                coolpoint = CoolPoint(
                    type=cp_type,
                    content=content,
                    position=position,
                    intensity=base_intensity,
                    description=f"在位置{position}发现{cp_type.value}爽点"
                )
                coolpoints.append(coolpoint)

        coolpoints.sort(key=lambda x: x.position)
        return coolpoints

    def analyze(self, text: str) -> Dict[str, Any]:
        """综合分析"""
        hooks = self.analyze_hooks(text)
        coolpoints = self.analyze_coolpoints(text)

        hook_density = len(hooks) / (len(text) / 1000)
        coolpoint_density = len(coolpoints) / (len(text) / 1000)

        hook_type_counts = {}
        for hook in hooks:
            hook_type_counts[hook.type.value] = hook_type_counts.get(hook.type.value, 0) + 1

        coolpoint_type_counts = {}
        for cp in coolpoints:
            coolpoint_type_counts[cp.type.value] = coolpoint_type_counts.get(cp.type.value, 0) + 1

        return {
            "hooks": [self._hook_to_dict(h) for h in hooks],
            "coolpoints": [self._coolpoint_to_dict(c) for c in coolpoints],
            "stats": {
                "hook_count": len(hooks),
                "coolpoint_count": len(coolpoints),
                "hook_density": round(hook_density, 2),
                "coolpoint_density": round(coolpoint_density, 2),
                "hook_type_distribution": hook_type_counts,
                "coolpoint_type_distribution": coolpoint_type_counts,
                "total_word_count": len(text),
            },
            "summary": self._generate_summary(hooks, coolpoints, hook_density, coolpoint_density)
        }

    def _hook_to_dict(self, hook: Hook) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "type": hook.type.value,
            "content": hook.content,
            "position": hook.position,
            "intensity": hook.intensity,
            "description": hook.description
        }

    def _coolpoint_to_dict(self, cp: CoolPoint) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "type": cp.type.value,
            "content": cp.content,
            "position": cp.position,
            "intensity": cp.intensity,
            "description": cp.description
        }

    def _generate_summary(
        self,
        hooks: List[Hook],
        coolpoints: List[CoolPoint],
        hook_density: float,
        coolpoint_density: float
    ) -> str:
        """生成摘要"""
        parts = []

        if len(hooks) == 0:
            parts.append("⚠️ 无明显钩子，建议增加悬念或冲突")
        elif hook_density < 2:
            parts.append(f"⚠️ 钩子密度偏低({hook_density}/千字)，建议增加")
        else:
            parts.append(f"✅ 钩子密度正常({hook_density}/千字)")

        if len(coolpoints) == 0:
            parts.append("⚠️ 无明显爽点，建议增加打脸、突破等情节")
        elif coolpoint_density < 3:
            parts.append(f"⚠️ 爽点密度偏低({coolpoint_density}/千字)，建议增加")
        else:
            parts.append(f"✅ 爽点密度正常({coolpoint_density}/千字)")

        return "; ".join(parts)


def analyze_text(text: str) -> Dict[str, Any]:
    """便捷函数"""
    analyzer = HookCoolPointAnalyzer()
    return analyzer.analyze(text)
