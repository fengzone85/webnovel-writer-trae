#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deconstruction Agent - 参考作品拆解模块
负责分析参考作品结构、人物、情节等要素
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

class DeconstructionAgent:
    """拆解代理 - 分析参考作品"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        self.analysis_dir = self.project_path / ".webnovel" / "reference_analysis"
        self.analysis_dir.mkdir(parents=True, exist_ok=True)

    def analyze_chapter(self, chapter_text: str, chapter_num: int = 0) -> Dict[str, Any]:
        """分析单章结构"""
        analysis = {
            "chapter_num": chapter_num,
            "word_count": len(chapter_text),
            "structure": self._analyze_structure(chapter_text),
            "hooks": self._extract_hooks(chapter_text),
            "cool_points": self._extract_cool_points(chapter_text),
            "pacing": self._analyze_pacing(chapter_text),
            "dialogue_ratio": self._calculate_dialogue_ratio(chapter_text),
            "scene_transitions": self._find_scene_transitions(chapter_text),
            "foreshadowing": self._find_foreshadowing(chapter_text),
            "timestamp": datetime.now().isoformat()
        }
        return analysis

    def _analyze_structure(self, text: str) -> Dict[str, Any]:
        """分析章节结构"""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        opening_indicators = ['随着', '这一天', '忽然', '突然', '就在这时', '只见', '突然', '没想到']
        climax_indicators = ['终于', '没想到', '就在这时', '刹那间', '突然', '猛然', '陡然']
        ending_indicators = ['欲知后事', '且听下回', '不由得', '不禁', '让人期待']

        opening_count = sum(1 for p in paragraphs[:3] if any(ind in p for ind in opening_indicators))
        climax_count = sum(1 for p in paragraphs if any(ind in p for ind in climax_indicators))
        ending_count = sum(1 for p in paragraphs[-3:] if any(ind in p for ind in ending_indicators))

        structure_type = "标准起承转合"
        if climax_count >= 3:
            structure_type = "高潮密集型"
        elif opening_count >= 2 and ending_count >= 2:
            structure_type = "完整结构型"
        elif len(paragraphs) < 5:
            structure_type = "简短推进型"

        return {
            "type": structure_type,
            "paragraph_count": len(paragraphs),
            "has_opening": opening_count > 0,
            "has_climax": climax_count > 0,
            "has_ending": ending_count > 0,
            "opening_strength": min(opening_count, 3),
            "climax_density": climax_count,
            "ending_strength": min(ending_count, 2)
        }

    def _extract_hooks(self, text: str) -> List[Dict[str, Any]]:
        """提取钩子"""
        hooks = []

        hook_patterns = [
            (r'就在这时', '转折钩子'),
            (r'突然\s*\S+\s*出现', '意外钩子'),
            (r'难道是', '悬念钩子'),
            (r'没想到', '反转钩子'),
            (r'只见\s*\S+\s*\S+\s*，', '画面钩子'),
            (r'这\S+\s*竟然', '震惊钩子'),
            (r'（[一二三]）', '选项钩子'),
            (r'就在众人以为', '预期打破钩子'),
            (r'然而', '转折钩子'),
            (r'更可怕的是', '升级钩子'),
        ]

        sentences = re.split(r'[。！？\n]', text)
        for i, sentence in enumerate(sentences):
            for pattern, hook_type in hook_patterns:
                if re.search(pattern, sentence):
                    hooks.append({
                        "type": hook_type,
                        "text": sentence.strip()[:100],
                        "position": i / len(sentences) if sentences else 0
                    })
                    break

        return hooks[:10]

    def _extract_cool_points(self, text: str) -> List[Dict[str, Any]]:
        """提取爽点"""
        cool_points = []

        cool_patterns = [
            (r'暴涨|突破|飙升', '实力提升爽点'),
            (r'震惊|惊呆|目瞪口呆', '震惊爽点'),
            (r'逆转|翻盘|绝杀', '逆转爽点'),
            (r'打脸|狠狠.*脸', '打脸爽点'),
            (r'获得.*奖励|得到.*传承', '获得爽点'),
            (r'秒杀|一击必杀|碾压', '碾压爽点'),
            (r'美女|仙子|绝色', '美人爽点'),
            (r'神兽|上古|远古', '稀有爽点'),
            (r'第一|独一无二|史上首次', '独占爽点'),
            (r'领悟|顿悟|觉醒', '觉醒爽点'),
        ]

        sentences = re.split(r'[。！？\n]', text)
        for sentence in sentences:
            for pattern, cool_type in cool_patterns:
                if re.search(pattern, sentence):
                    cool_points.append({
                        "type": cool_type,
                        "text": sentence.strip()[:100]
                    })
                    break

        return cool_points[:10]

    def _analyze_pacing(self, text: str) -> Dict[str, Any]:
        """分析节奏"""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        dialogue_paragraphs = [p for p in paragraphs if '"' in p or '"' in p or '"' in p]
        action_paragraphs = [p for p in paragraphs if any(kw in p for kw in ['一掌', '一拳', '一剑', '飞速', '猛然', '陡然'])]

        avg_para_len = sum(len(p) for p in paragraphs) / len(paragraphs) if paragraphs else 0

        pacing_score = 1.0
        if len(paragraphs) > 20:
            pacing_score = 0.8
        if avg_para_len > 300:
            pacing_score = 0.7
        if len(action_paragraphs) > len(paragraphs) * 0.3:
            pacing_score = 1.2

        return {
            "pacing_score": pacing_score,
            "paragraph_count": len(paragraphs),
            "avg_paragraph_length": int(avg_para_len),
            "dialogue_ratio": len(dialogue_paragraphs) / len(paragraphs) if paragraphs else 0,
            "action_ratio": len(action_paragraphs) / len(paragraphs) if paragraphs else 0,
            "pace_type": "快节奏" if pacing_score >= 1.1 else "慢节奏" if pacing_score < 0.8 else "标准节奏"
        }

    def _calculate_dialogue_ratio(self, text: str) -> float:
        """计算对话比例"""
        dialogue_chars = 0
        in_dialogue = False
        current_quote = '"'

        for char in text:
            if char == current_quote:
                in_dialogue = not in_dialogue
            elif in_dialogue:
                dialogue_chars += 1

        return dialogue_chars / len(text) if len(text) > 0 else 0

    def _find_scene_transitions(self, text: str) -> List[Dict[str, Any]]:
        """查找场景转换"""
        transitions = []

        transition_patterns = [
            (r'时间流逝|转眼间|数日之后|数月之后|一年后', '时间跳转'),
            (r'与此同时|另一边|与此同时', '并行场景'),
            (r'与此同时|镜头一转|画面一转', '镜头切换'),
            (r'回到|回到现实|重新', '回归场景'),
        ]

        sentences = text.split('。')
        for i, sentence in enumerate(sentences):
            for pattern, trans_type in transition_patterns:
                if re.search(pattern, sentence):
                    transitions.append({
                        "type": trans_type,
                        "text": sentence.strip()[:50],
                        "position": i / len(sentences) if sentences else 0
                    })
                    break

        return transitions

    def _find_foreshadowing(self, text: str) -> List[Dict[str, Any]]:
        """查找伏笔"""
        foreshadowings = []

        foreshadow_patterns = [
            (r'似乎.*将要', '预感伏笔'),
            (r'却不知', '悬念伏笔'),
            (r'不知道.*会', '未知伏笔'),
            (r'埋下了.*伏笔', '明示伏笔'),
            (r'当时.*并不知道', '后置伏笔'),
            (r'日后.*必将', '预示伏笔'),
        ]

        sentences = text.split('。')
        for i, sentence in enumerate(sentences):
            for pattern, fore_type in foreshadow_patterns:
                if re.search(pattern, sentence):
                    foreshadowings.append({
                        "type": fore_type,
                        "text": sentence.strip()[:80],
                        "position": i / len(sentences) if sentences else 0
                    })
                    break

        return foreshadowings

    def analyze_character_arc(self, character_name: str, chapters: List[str]) -> Dict[str, Any]:
        """分析人物成长弧线"""
        arc_points = []

        for i, chapter_text in enumerate(chapters):
            if character_name in chapter_text:
                emotional_markers = self._extract_emotional_markers(chapter_text, character_name)
                if emotional_markers:
                    arc_points.append({
                        "chapter": i + 1,
                        "emotions": emotional_markers
                    })

        if len(arc_points) < 2:
            return {"status": "insufficient_data", "arc_points": arc_points}

        growth_direction = self._determine_growth_direction(arc_points)

        return {
            "character": character_name,
            "arc_points": arc_points,
            "growth_direction": growth_direction,
            "arc_type": self._classify_arc(arc_points),
            "timestamp": datetime.now().isoformat()
        }

    def _extract_emotional_markers(self, text: str, character: str) -> List[str]:
        """提取情感标记"""
        emotions = []

        emotion_patterns = [
            (r'愤怒|怒火|大怒', '愤怒'),
            (r'悲伤|痛苦|伤心', '悲伤'),
            (r'喜悦|高兴|开心', '喜悦'),
            (r'恐惧|害怕|胆怯', '恐惧'),
            (r'坚定|毫不犹豫', '坚定'),
            (r'犹豫|迟疑', '犹豫'),
        ]

        for pattern, emotion in emotion_patterns:
            if re.search(pattern, text):
                emotions.append(emotion)

        return emotions

    def _determine_growth_direction(self, arc_points: List[Dict[str, Any]]) -> str:
        """判断成长方向"""
        if not arc_points:
            return "未知"

        positive_count = sum(1 for p in arc_points if '坚定' in str(p.get('emotions', [])) or '喜悦' in str(p.get('emotions', [])))
        negative_count = sum(1 for p in arc_points if '愤怒' in str(p.get('emotions', [])) or '恐惧' in str(p.get('emotions', [])))

        if positive_count > negative_count:
            return "正向成长"
        elif negative_count > positive_count:
            return "负向发展"
        else:
            return "平稳发展"

    def _classify_arc(self, arc_points: List[Dict[str, Any]]) -> str:
        """分类成长弧线"""
        if len(arc_points) < 3:
            return "简单弧线"

        emotion_changes = []
        for p in arc_points:
            emotion_changes.extend(p.get('emotions', []))

        if '坚定' in emotion_changes and '犹豫' in emotion_changes:
            return "克服犹豫型"
        elif '喜悦' in emotion_changes and '悲伤' in emotion_changes:
            return "悲喜交加型"
        else:
            return "渐进型"

    def generate_deconstruction_report(self, analysis: Dict[str, Any]) -> str:
        """生成拆解报告"""
        report = []
        report.append("# 参考作品拆解报告")
        report.append("")
        report.append(f"**分析时间**: {analysis.get('timestamp', 'N/A')}")
        report.append("")

        report.append("## 1. 基本信息")
        report.append(f"- 字数: {analysis.get('word_count', 0)}")
        report.append(f"- 段落数: {analysis.get('structure', {}).get('paragraph_count', 0)}")
        report.append(f"- 结构类型: {analysis.get('structure', {}).get('type', '未知')}")
        report.append("")

        report.append("## 2. 章节结构")
        struct = analysis.get('structure', {})
        report.append(f"- 开篇强度: {'★' * struct.get('opening_strength', 0)}")
        report.append(f"- 高潮密度: {struct.get('climax_density', 0)}")
        report.append(f"- 结尾强度: {'★' * struct.get('ending_strength', 0)}")
        report.append("")

        report.append("## 3. 钩子分析")
        hooks = analysis.get('hooks', [])
        if hooks:
            for hook in hooks[:5]:
                report.append(f"- [{hook.get('type', '未知')}] {hook.get('text', '')}")
        else:
            report.append("未发现明显钩子")
        report.append("")

        report.append("## 4. 爽点分析")
        cool_points = analysis.get('cool_points', [])
        if cool_points:
            cool_types = {}
            for cp in cool_points:
                t = cp.get('type', '其他')
                cool_types[t] = cool_types.get(t, 0) + 1
            for t, c in cool_types.items():
                report.append(f"- {t}: {c}处")
        else:
            report.append("未发现明显爽点")
        report.append("")

        report.append("## 5. 节奏分析")
        pacing = analysis.get('pacing', {})
        report.append(f"- 节奏类型: {pacing.get('pace_type', '未知')}")
        report.append(f"- 对话比例: {pacing.get('dialogue_ratio', 0):.1%}")
        report.append(f"- 动作比例: {pacing.get('action_ratio', 0):.1%}")
        report.append("")

        return '\n'.join(report)

    def save_analysis(self, analysis: Dict[str, Any], filename: str = None) -> Path:
        """保存分析结果"""
        if filename is None:
            filename = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        output_file = self.analysis_dir / filename
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)

        return output_file
