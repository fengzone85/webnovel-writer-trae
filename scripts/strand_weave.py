#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Strand Weave - 节奏系统模块
由 Quest（主线剧情）、Fire（感情线）、Constellation（世界观扩展）三股故事线交织而成
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

class StrandWeave:
    """Strand Weave 节奏系统"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        self.story_system_path = self.project_path / ".story-system"
        self.webnovel_path = self.project_path / ".webnovel"
        
        # Strand 定义
        self.strands = {
            "quest": {
                "name": "Quest",
                "description": "主线剧情",
                "keywords": ["主线", "任务", "剧情", "目标", "挑战", "冒险", "战斗"],
                "icon": "⚔️"
            },
            "fire": {
                "name": "Fire",
                "description": "感情线",
                "keywords": ["感情", "爱情", "友情", "亲情", "情感", "心动", "暧昧"],
                "icon": "❤️"
            },
            "constellation": {
                "name": "Constellation",
                "description": "世界观扩展",
                "keywords": ["设定", "世界", "背景", "势力", "规则", "历史", "传说"],
                "icon": "⭐"
            }
        }
        
        # 加载主设定获取比例配置
        self.master_setting = self._load_master_setting()
        
    def _load_master_setting(self) -> Dict[str, Any]:
        """加载主设定"""
        master_file = self.story_system_path / "MASTER_SETTING.json"
        if master_file.exists():
            with open(master_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def analyze_strand_ratio(self, content: str) -> Dict[str, float]:
        """分析内容中的 Strand 比例"""
        # 统计各 Strand 关键词出现次数
        counts = {
            "quest": 0,
            "fire": 0,
            "constellation": 0
        }
        
        for strand, config in self.strands.items():
            for keyword in config["keywords"]:
                counts[strand] += len(re.findall(keyword, content))
        
        # 计算比例
        total = sum(counts.values())
        if total == 0:
            total = 1
        
        return {
            "quest": counts["quest"] / total,
            "fire": counts["fire"] / total,
            "constellation": counts["constellation"] / total,
            "raw_counts": counts
        }
    
    def validate_strand_ratio(self, chapter_num: int, content: str) -> Dict[str, Any]:
        """验证 Strand 比例是否符合要求"""
        # 获取目标比例
        volume_num = (chapter_num - 1) // 10 + 1
        volume_file = self.story_system_path / "volumes" / f"volume_{volume_num:03d}.json"
        
        if volume_file.exists():
            with open(volume_file, 'r', encoding='utf-8') as f:
                volume_data = json.load(f)
            
            # 查找章节信息
            chapter_info = None
            for ch in volume_data.get("chapters", []):
                if ch["chapter"] == chapter_num:
                    chapter_info = ch
                    break
            
            if chapter_info:
                target_ratio = {
                    "quest": chapter_info.get("quest_ratio", 0.6),
                    "fire": chapter_info.get("fire_ratio", 0.2),
                    "constellation": chapter_info.get("constellation_ratio", 0.2)
                }
            else:
                target_ratio = self.master_setting.get("strand_config", {
                    "quest_ratio": 0.6,
                    "fire_ratio": 0.2,
                    "constellation_ratio": 0.2
                })
        else:
            target_ratio = self.master_setting.get("strand_config", {
                "quest_ratio": 0.6,
                "fire_ratio": 0.2,
                "constellation_ratio": 0.2
            })
        
        # 分析实际比例
        actual_ratio = self.analyze_strand_ratio(content)
        
        # 计算偏差
        deviations = {
            "quest": abs(actual_ratio["quest"] - target_ratio["quest_ratio"]),
            "fire": abs(actual_ratio["fire"] - target_ratio["fire_ratio"]),
            "constellation": abs(actual_ratio["constellation"] - target_ratio["constellation_ratio"])
        }
        
        # 判断是否符合要求（允许 0.15 的偏差）
        is_valid = all(d <= 0.15 for d in deviations.values())
        
        return {
            "chapter": chapter_num,
            "target_ratio": {
                "quest": target_ratio["quest_ratio"],
                "fire": target_ratio["fire_ratio"],
                "constellation": target_ratio["constellation_ratio"]
            },
            "actual_ratio": actual_ratio,
            "deviations": deviations,
            "is_valid": is_valid,
            "message": "比例符合要求" if is_valid else "比例偏差较大，建议调整"
        }
    
    def generate_strand_suggestion(self, chapter_num: int) -> Dict[str, Any]:
        """生成 Strand 比例建议"""
        volume_num = (chapter_num - 1) // 10 + 1
        
        # 根据章节位置确定建议比例
        chapter_in_volume = (chapter_num - 1) % 10 + 1
        
        # 默认比例配置
        base_ratio = {
            "quest": 0.6,
            "fire": 0.2,
            "constellation": 0.2
        }
        
        # 根据章节位置调整
        if chapter_in_volume == 1:
            # 卷首：更多设定介绍
            base_ratio["constellation"] = 0.3
            base_ratio["quest"] = 0.5
        
        elif chapter_in_volume == 5:
            # 卷中：适当增加感情线
            base_ratio["fire"] = 0.3
            base_ratio["quest"] = 0.5
        
        elif chapter_in_volume == 10:
            # 卷末：高潮战斗
            base_ratio["quest"] = 0.7
            base_ratio["fire"] = 0.1
            base_ratio["constellation"] = 0.2
        
        # 根据题材调整
        genre = self.master_setting.get("genre", "修仙")
        if genre in ["都市", "言情", "校园"]:
            base_ratio["fire"] = min(base_ratio["fire"] + 0.1, 0.4)
            base_ratio["quest"] = max(base_ratio["quest"] - 0.1, 0.4)
        
        elif genre in ["玄幻", "仙侠", "末世"]:
            base_ratio["quest"] = min(base_ratio["quest"] + 0.1, 0.7)
            base_ratio["fire"] = max(base_ratio["fire"] - 0.05, 0.1)
        
        return {
            "chapter": chapter_num,
            "chapter_in_volume": chapter_in_volume,
            "suggested_ratio": base_ratio,
            "genre": genre,
            "explanation": self._generate_ratio_explanation(base_ratio, chapter_in_volume)
        }
    
    def _generate_ratio_explanation(self, ratio: Dict[str, float], position: int) -> str:
        """生成比例解释"""
        explanations = []
        
        if position == 1:
            explanations.append("本章为卷首，建议适当增加世界观设定介绍")
        elif position == 10:
            explanations.append("本章为卷末高潮，建议集中主线剧情")
        elif position == 5:
            explanations.append("本章为卷中过渡，可适当增加感情线")
        
        if ratio["quest"] >= 0.7:
            explanations.append("主线剧情占比较高，适合推进核心任务")
        if ratio["fire"] >= 0.3:
            explanations.append("感情线占比较高，适合发展人物关系")
        if ratio["constellation"] >= 0.3:
            explanations.append("世界观扩展占比较高，适合介绍背景设定")
        
        return "; ".join(explanations)
    
    def analyze_volume_strands(self, volume_num: int) -> Dict[str, Any]:
        """分析整卷的 Strand 分布"""
        volume_file = self.story_system_path / "volumes" / f"volume_{volume_num:03d}.json"
        if not volume_file.exists():
            return {"status": "failed", "error": "卷合同不存在"}
        
        with open(volume_file, 'r', encoding='utf-8') as f:
            volume_data = json.load(f)
        
        # 计算整卷的平均比例
        total_ratio = {"quest": 0, "fire": 0, "constellation": 0}
        chapter_count = len(volume_data.get("chapters", []))
        
        for ch in volume_data.get("chapters", []):
            total_ratio["quest"] += ch.get("quest_ratio", 0.6)
            total_ratio["fire"] += ch.get("fire_ratio", 0.2)
            total_ratio["constellation"] += ch.get("constellation_ratio", 0.2)
        
        avg_ratio = {k: v / chapter_count for k, v in total_ratio.items()}
        
        return {
            "status": "completed",
            "volume": volume_num,
            "title": volume_data.get("title", f"第{volume_num}卷"),
            "chapter_count": chapter_count,
            "average_ratio": avg_ratio,
            "chapters": volume_data.get("chapters", [])
        }
    
    def check_strand_balance(self, start_chapter: int, end_chapter: int) -> Dict[str, Any]:
        """检查多个章节的 Strand 平衡"""
        results = []
        overall_ratio = {"quest": 0, "fire": 0, "constellation": 0}
        chapter_count = 0
        
        for chapter_num in range(start_chapter, end_chapter + 1):
            chapter_file = self.project_path / "章节" / f"Ch{chapter_num:03d}.md"
            if chapter_file.exists():
                with open(chapter_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                analysis = self.analyze_strand_ratio(content)
                validation = self.validate_strand_ratio(chapter_num, content)
                
                results.append({
                    "chapter": chapter_num,
                    "analysis": analysis,
                    "validation": validation
                })
                
                overall_ratio["quest"] += analysis["quest"]
                overall_ratio["fire"] += analysis["fire"]
                overall_ratio["constellation"] += analysis["constellation"]
                chapter_count += 1
        
        if chapter_count > 0:
            overall_ratio = {k: v / chapter_count for k, v in overall_ratio.items()}
        
        # 检查是否有断档（连续3章某条线为0）
        strand_gaps = self._detect_strand_gaps(results)
        
        return {
            "start_chapter": start_chapter,
            "end_chapter": end_chapter,
            "analyzed_chapters": chapter_count,
            "overall_ratio": overall_ratio,
            "chapter_results": results,
            "strand_gaps": strand_gaps,
            "suggestions": self._generate_balance_suggestions(overall_ratio, strand_gaps)
        }
    
    def _detect_strand_gaps(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """检测 Strand 断档"""
        gaps = []
        consecutive_zero = {"quest": 0, "fire": 0, "constellation": 0}
        
        for result in results:
            ratio = result["analysis"]
            chapter = result["chapter"]
            
            for strand in ["quest", "fire", "constellation"]:
                if ratio[strand] == 0:
                    consecutive_zero[strand] += 1
                    if consecutive_zero[strand] == 3:
                        gaps.append({
                            "strand": strand,
                            "start_chapter": chapter - 2,
                            "end_chapter": chapter,
                            "message": f"{self.strands[strand]['name']}线连续3章缺失"
                        })
                else:
                    consecutive_zero[strand] = 0
        
        return gaps
    
    def _generate_balance_suggestions(self, overall_ratio: Dict[str, float], gaps: List[Dict[str, Any]]) -> List[str]:
        """生成平衡建议"""
        suggestions = []
        
        # 检查比例是否失衡
        if overall_ratio["quest"] < 0.4:
            suggestions.append("主线剧情占比过低，建议增加主线推进")
        elif overall_ratio["quest"] > 0.8:
            suggestions.append("主线剧情占比过高，建议适当加入其他元素")
        
        if overall_ratio["fire"] < 0.1:
            suggestions.append("感情线占比过低，建议增加人物互动")
        elif overall_ratio["fire"] > 0.4:
            suggestions.append("感情线占比过高，建议平衡主线剧情")
        
        if overall_ratio["constellation"] < 0.1:
            suggestions.append("世界观设定介绍不足，建议适当补充")
        elif overall_ratio["constellation"] > 0.4:
            suggestions.append("世界观设定过多，建议聚焦剧情")
        
        # 检查断档
        for gap in gaps:
            suggestions.append(gap["message"])
        
        return suggestions
    
    def get_strand_summary(self) -> Dict[str, Any]:
        """获取 Strand 整体概览"""
        # 统计所有章节
        chapters_dir = self.project_path / "章节"
        if not chapters_dir.exists():
            return {"status": "failed", "error": "章节目录不存在"}
        
        chapter_files = sorted(chapters_dir.glob("Ch*.md"))
        if not chapter_files:
            return {"status": "failed", "error": "未找到章节文件"}
        
        first_chapter = int(chapter_files[0].stem[2:])
        last_chapter = int(chapter_files[-1].stem[2:])
        
        return self.check_strand_balance(first_chapter, last_chapter)