#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reviewer Agent - 六维审查执行模块
执行：爽点检查、一致性检查、节奏检查、OOC检查、连贯性检查、追读力检查
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

class ReviewerAgent:
    """审查代理 - 六维审查系统"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        self.story_system_path = self.project_path / ".story-system"
        self.webnovel_path = self.project_path / ".webnovel"
        
        # 加载主设定和记忆
        self.master_setting = self._load_master_setting()
        self.memory = self._load_memory()
        
        # 爽点关键词
        self.cool_point_keywords = [
            "突破", "晋级", "获得", "打败", "斩杀", "羞辱", "打脸",
            "震惊", "震撼", "惊讶", "狂喜", "激动", "兴奋",
            "秘籍", "法宝", "神器", "传承", "奇遇", "机缘"
        ]
        
        # Hook关键词
        self.hook_keywords = [
            "却见", "只见", "原来", "竟然", "究竟", "真相",
            "危机", "危险", "陷阱", "阴谋", "谜团", "悬念"
        ]
    
    def _load_master_setting(self) -> Dict[str, Any]:
        """加载主设定"""
        master_file = self.story_system_path / "MASTER_SETTING.json"
        if master_file.exists():
            with open(master_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _load_memory(self) -> Dict[str, Any]:
        """加载长期记忆"""
        memory_file = self.webnovel_path / "memory_scratchpad.json"
        if memory_file.exists():
            with open(memory_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _load_chapter_content(self, chapter_num: int) -> str:
        """加载章节内容"""
        chapter_file = self.project_path / "章节" / f"Ch{chapter_num:03d}.md"
        if chapter_file.exists():
            with open(chapter_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def _load_runtime_contract(self, chapter_num: int) -> Dict[str, Any]:
        """加载运行时合同"""
        contract_file = self.story_system_path / "reviews" / f"ch{chapter_num}_contract.json"
        if contract_file.exists():
            with open(contract_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def review(self, chapter_num: int) -> Dict[str, Any]:
        """执行六维审查"""
        content = self._load_chapter_content(chapter_num)
        if not content:
            return {"status": "failed", "error": "章节内容为空"}
        
        runtime_contract = self._load_runtime_contract(chapter_num)
        
        # 执行各项审查
        review = {
            "chapter": chapter_num,
            "timestamp": datetime.now().isoformat(),
            "word_count": len(content),
            "high_point": self._check_high_point(content),
            "consistency": self._check_consistency(chapter_num, content),
            "pacing": self._check_pacing(chapter_num, content, runtime_contract),
            "ooc": self._check_ooc(chapter_num, content),
            "continuity": self._check_continuity(chapter_num, content),
            "reader_pull": self._check_reader_pull(chapter_num, content)
        }
        
        # 计算综合评分
        review["overall_score"] = self._calculate_overall_score(review)
        review["suggestions"] = self._generate_suggestions(review)
        
        # 保存审查结果
        self._save_review(chapter_num, review)
        
        return review
    
    def _check_high_point(self, content: str) -> Dict[str, Any]:
        """爽点密度检查"""
        cool_points = []
        
        # 查找爽点关键词
        for keyword in self.cool_point_keywords:
            matches = re.findall(keyword, content)
            if matches:
                cool_points.append({
                    "keyword": keyword,
                    "count": len(matches),
                    "positions": [i.start() for i in re.finditer(keyword, content)]
                })
        
        # 计算爽点密度（每千字爽点数量）
        word_count = len(content)
        density = len(cool_points) / (word_count / 1000) if word_count > 0 else 0
        
        # 评估结果
        if density >= 1:
            score = 80 + min(density * 20, 20)
            status = "优秀"
        elif density >= 0.5:
            score = 60 + (density - 0.5) * 40
            status = "良好"
        else:
            score = density * 120
            status = "待提升"
        
        return {
            "score": min(int(score), 100),
            "status": status,
            "cool_points": cool_points,
            "density": round(density, 2),
            "message": f"爽点密度: {round(density, 2)} 个/千字"
        }
    
    def _check_consistency(self, chapter_num: int, content: str) -> Dict[str, Any]:
        """设定一致性检查"""
        issues = []
        warnings = []
        
        # 检查角色一致性
        characters = self.memory.get("characters", {})
        for char_name in characters:
            # 检查角色是否在本章出现
            if char_name in content:
                # 检查是否有矛盾描述
                pass
        
        # 检查地点一致性
        locations = self.memory.get("locations", {})
        
        # 检查战力体系
        power_levels = ["筑基", "金丹", "元婴", "化神", "渡劫"]
        for level in power_levels:
            if level in content:
                # 检查是否有越级挑战的合理性
                pass
        
        # 检查时间线
        if "三年后" in content or "三个月后" in content:
            warnings.append("时间跳跃较大，请注意时间线一致性")
        
        score = 100 - len(issues) * 20 - len(warnings) * 5
        
        return {
            "score": max(0, score),
            "status": "优秀" if score >= 80 else "良好" if score >= 60 else "待检查",
            "issues": issues,
            "warnings": warnings,
            "message": f"发现 {len(issues)} 个问题，{len(warnings)} 个警告"
        }
    
    def _check_pacing(self, chapter_num: int, content: str, runtime_contract: Dict[str, Any]) -> Dict[str, Any]:
        """节奏检查（Strand Weave）"""
        # 计算各 Strand 比例
        quest_count = len(re.findall(r"(【主线】|主线任务|剧情)", content))
        fire_count = len(re.findall(r"(【感情】|情感|爱意|喜欢)", content))
        constellation_count = len(re.findall(r"(【设定】|世界|背景|势力)", content))
        
        total = quest_count + fire_count + constellation_count
        if total == 0:
            total = 1
        
        quest_ratio = quest_count / total
        fire_ratio = fire_count / total
        constellation_ratio = constellation_count / total
        
        # 获取目标比例
        target_ratio = runtime_contract.get("constraints", {}).get("strand_ratio", {
            "quest": 0.6,
            "fire": 0.2,
            "constellation": 0.2
        })
        
        # 计算偏差
        quest_dev = abs(quest_ratio - target_ratio["quest"])
        fire_dev = abs(fire_ratio - target_ratio["fire"])
        constellation_dev = abs(constellation_ratio - target_ratio["constellation"])
        
        # 计算分数
        avg_dev = (quest_dev + fire_dev + constellation_dev) / 3
        score = max(0, 100 - avg_dev * 200)
        
        return {
            "score": int(score),
            "status": "优秀" if score >= 80 else "良好" if score >= 60 else "待调整",
            "strand_ratio": {
                "quest": round(quest_ratio, 2),
                "fire": round(fire_ratio, 2),
                "constellation": round(constellation_ratio, 2)
            },
            "target_ratio": target_ratio,
            "message": f"Quest:{round(quest_ratio*100)}% Fire:{round(fire_ratio*100)}% Constellation:{round(constellation_ratio*100)}%"
        }
    
    def _check_ooc(self, chapter_num: int, content: str) -> Dict[str, Any]:
        """OOC（人物行为偏离人设）检查"""
        issues = []
        
        # 检查角色行为
        characters = self.memory.get("characters", {})
        for char_name, char_info in characters.items():
            if char_name in content:
                # 检查是否有OOC行为
                # 这是简化版，实际需要更多人设信息
                if "愤怒地说" in content and "温柔" in str(char_info.get("personality", "")):
                    issues.append(f"{char_name} 的行为可能不符合温柔的人设")
        
        score = 100 - len(issues) * 20
        
        return {
            "score": max(0, score),
            "status": "优秀" if score >= 80 else "良好" if score >= 60 else "待检查",
            "issues": issues,
            "message": f"发现 {len(issues)} 个可能的OOC行为"
        }
    
    def _check_continuity(self, chapter_num: int, content: str) -> Dict[str, Any]:
        """叙事连贯性检查"""
        issues = []
        
        # 检查场景转换
        scene_changes = len(re.findall(r"(【场景转换】|镜头一转|画面切换)", content))
        
        # 检查时间描述
        time_markers = len(re.findall(r"(清晨|中午|傍晚|深夜|第二天)", content))
        
        # 检查逻辑连接词
        connectives = len(re.findall(r"(于是|因此|但是|然而|接着)", content))
        
        # 评估连贯性
        if scene_changes > 5:
            issues.append("场景转换过于频繁")
        if time_markers == 0 and len(content) > 3000:
            issues.append("缺乏时间标记，可能影响连贯性")
        if connectives < len(content) / 500:
            warnings = ["逻辑连接词较少，建议增加"]
        
        score = 100 - len(issues) * 15
        
        return {
            "score": max(0, score),
            "status": "优秀" if score >= 80 else "良好" if score >= 60 else "待提升",
            "issues": issues,
            "scene_changes": scene_changes,
            "time_markers": time_markers,
            "message": f"场景转换: {scene_changes} 次，时间标记: {time_markers} 处"
        }
    
    def _check_reader_pull(self, chapter_num: int, content: str) -> Dict[str, Any]:
        """追读力检查"""
        # 检查Hook
        hooks = []
        for keyword in self.hook_keywords:
            if keyword in content:
                hooks.append(keyword)
        
        # 检查结尾悬念
        last_paragraph = content.split('\n')[-1] if content else ""
        has_cliffhanger = any(word in last_paragraph for word in ["究竟", "竟然", "真相", "危机", "陷阱"])
        
        # 检查爽点分布
        cool_points = self._check_high_point(content)
        
        # 评估追读力
        hook_score = min(len(hooks) * 10, 40)
        cliffhanger_score = 20 if has_cliffhanger else 0
        cool_score = min(cool_points["density"] * 20, 40)
        
        total_score = hook_score + cliffhanger_score + cool_score
        
        return {
            "score": int(total_score),
            "status": "优秀" if total_score >= 80 else "良好" if total_score >= 60 else "待提升",
            "hooks": hooks,
            "has_cliffhanger": has_cliffhanger,
            "cool_density": cool_points["density"],
            "message": f"Hooks: {len(hooks)} 个，结尾悬念: {'有' if has_cliffhanger else '无'}"
        }
    
    def _calculate_overall_score(self, review: Dict[str, Any]) -> int:
        """计算综合评分"""
        weights = {
            "high_point": 0.2,
            "consistency": 0.2,
            "pacing": 0.2,
            "ooc": 0.15,
            "continuity": 0.15,
            "reader_pull": 0.1
        }
        
        total = 0
        for key, weight in weights.items():
            total += review[key]["score"] * weight
        
        return int(total)
    
    def _generate_suggestions(self, review: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        if review["high_point"]["score"] < 60:
            suggestions.append("建议增加爽点密度，提升读者阅读体验")
        
        if review["consistency"]["score"] < 60:
            suggestions.append("请检查设定一致性，避免出现矛盾")
        
        if review["pacing"]["score"] < 60:
            suggestions.append(f"建议调整故事节奏，当前比例: Quest{review['pacing']['strand_ratio']['quest']*100:.0f}% Fire{review['pacing']['strand_ratio']['fire']*100:.0f}%")
        
        if review["ooc"]["score"] < 60:
            suggestions.append("请检查人物行为是否符合人设")
        
        if review["continuity"]["score"] < 60:
            suggestions.append("建议增加场景转换的过渡描述")
        
        if review["reader_pull"]["score"] < 60:
            suggestions.append("建议增加钩子和悬念，提升追读力")
        
        return suggestions
    
    def _save_review(self, chapter_num: int, review: Dict[str, Any]):
        """保存审查结果"""
        review_file = self.story_system_path / "reviews" / f"ch{chapter_num}_review.json"
        with open(review_file, 'w', encoding='utf-8') as f:
            json.dump(review, f, ensure_ascii=False, indent=2)
    
    def batch_review(self, start_chapter: int, end_chapter: int) -> Dict[str, Any]:
        """批量审查"""
        results = []
        for chapter_num in range(start_chapter, end_chapter + 1):
            result = self.review(chapter_num)
            results.append(result)
        
        # 计算总体统计
        avg_score = sum(r["overall_score"] for r in results) / len(results) if results else 0
        
        return {
            "status": "completed",
            "start_chapter": start_chapter,
            "end_chapter": end_chapter,
            "total_chapters": len(results),
            "average_score": int(avg_score),
            "reviews": results
        }