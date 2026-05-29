#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
追读力系统模块
量化 Hook、Cool-point、微兑现、债务追踪
"""

import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

class ReaderPullSystem:
    """追读力系统 - 量化读者粘性指标"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        self.webnovel_path = self.project_path / ".webnovel"
        self.reader_pull_path = self.webnovel_path / "reader_pull.json"
        
        # 确保目录存在
        self.webnovel_path.mkdir(parents=True, exist_ok=True)
        
        # 加载追读力数据
        self.data = self._load_data()
    
    def _load_data(self) -> Dict[str, Any]:
        """加载追读力数据"""
        if self.reader_pull_path.exists():
            with open(self.reader_pull_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            "hooks": [],
            "cool_points": [],
            "debts": [],
            "micro_deliveries": [],
            "scores": {},
            "history": [],
            "trend": {
                "average_scores": [],
                "hook_counts": [],
                "cool_point_counts": [],
                "debt_counts": []
            }
        }
    
    def _save_data(self):
        """保存追读力数据"""
        with open(self.reader_pull_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def analyze_chapter(self, chapter_num: int, content: str, chapter_title: str = "") -> Dict[str, Any]:
        """分析章节的追读力指标"""
        result = {
            "chapter": chapter_num,
            "title": chapter_title,
            "timestamp": datetime.now().isoformat(),
            "hooks": [],
            "cool_points": [],
            "debts": [],
            "micro_deliveries": [],
            "score": 0.0,
            "breakdown": {},
            "grade": "",
            "suggestions": [],
            "reader_pull_metrics": {}
        }
        
        # 识别 Hooks
        hooks = self._identify_hooks(content, chapter_num)
        result["hooks"] = hooks
        
        # 识别爽点
        cool_points = self._identify_cool_points(content, chapter_num)
        result["cool_points"] = cool_points
        
        # 识别债务（悬念/伏笔）
        debts = self._identify_debts(content, chapter_num)
        result["debts"] = debts
        
        # 识别微兑现
        micro_deliveries = self._identify_micro_deliveries(content, chapter_num)
        result["micro_deliveries"] = micro_deliveries
        
        # 计算评分
        score, breakdown = self._calculate_score(hooks, cool_points, debts, micro_deliveries)
        result["score"] = score
        result["breakdown"] = breakdown
        
        # 评级
        result["grade"] = self._get_grade(score)
        
        # 生成建议
        result["suggestions"] = self._generate_suggestions(hooks, cool_points, debts, micro_deliveries)
        
        # 计算追读力指标
        result["reader_pull_metrics"] = self._calculate_reader_pull_metrics(
            hooks, cool_points, debts, micro_deliveries, content
        )
        
        # 保存结果
        self.data["hooks"].extend(hooks)
        self.data["cool_points"].extend(cool_points)
        self.data["debts"].extend(debts)
        self.data["micro_deliveries"].extend(micro_deliveries)
        self.data["scores"][f"chapter_{chapter_num}"] = result
        self.data["history"].append({
            "chapter": chapter_num,
            "score": score,
            "timestamp": datetime.now().isoformat(),
            "hook_count": len(hooks),
            "cool_point_count": len(cool_points),
            "debt_count": len(debts),
            "delivery_count": len(micro_deliveries)
        })
        
        # 更新趋势数据
        self._update_trend_data()
        
        self._save_data()
        
        return result
    
    def _identify_hooks(self, content: str, chapter_num: int) -> List[Dict[str, Any]]:
        """识别钩子（Hook）"""
        hooks = []
        
        # Hook 模式（增强版）
        hook_patterns = [
            # 悬念类
            {"pattern": r"(没想到|不料|谁知道|出乎意料|意外的是|震惊的是|愕然发现)", "type": "surprise", "weight": 0.8},
            {"pattern": r"(究竟|到底|为什么|怎么回事|难道|莫非)", "type": "question", "weight": 0.7},
            {"pattern": r"(神秘|诡异|奇怪|不对劲|异常|蹊跷)", "type": "mystery", "weight": 0.75},
            {"pattern": r"(真相|秘密|隐藏|惊人发现|惊天秘密)", "type": "reveal", "weight": 0.9},
            
            # 危机类
            {"pattern": r"(危机|危险|绝境|生死|挑战|千钧一发|命悬一线)", "type": "danger", "weight": 0.85},
            {"pattern": r"(突然|猛地|骤然|陡然|猝不及防)", "type": "sudden", "weight": 0.7},
            
            # 系统类
            {"pattern": r"(系统提示|任务发布|奖励发放|等级提升|技能解锁)", "type": "system", "weight": 0.8},
            
            # 预告类
            {"pattern": r"(未完待续|下一章|敬请期待|后续更精彩|且看下回分解)", "type": "teaser", "weight": 0.6},
            
            # 冲突类
            {"pattern": r"(挑战|对决|宣战|挑衅|不服)", "type": "conflict", "weight": 0.75},
            
            # 情感类
            {"pattern": r"(泪流满面|心如刀割|悲痛欲绝|喜极而泣|震惊全场)", "type": "emotion", "weight": 0.65}
        ]
        
        for pattern_info in hook_patterns:
            matches = re.findall(pattern_info["pattern"], content)
            for match in matches:
                hooks.append({
                    "id": f"hook_{chapter_num}_{len(hooks)}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "chapter": chapter_num,
                    "type": pattern_info["type"],
                    "content": match,
                    "weight": pattern_info["weight"],
                    "position": content.find(match),
                    "created_at": datetime.now().isoformat()
                })
        
        return hooks
    
    def _identify_cool_points(self, content: str, chapter_num: int) -> List[Dict[str, Any]]:
        """识别爽点（Cool Point）"""
        cool_points = []
        
        # 爽点模式（增强版）
        cool_patterns = [
            # 战斗碾压类
            {"pattern": r"(秒杀|完虐|碾压|吊打|轻松击败|横扫|无人能敌)", "type": "dominate", "weight": 0.9},
            
            # 升级进阶类
            {"pattern": r"(升级|突破|进阶|觉醒|顿悟|突破桎梏|超凡入圣)", "type": "level_up", "weight": 0.85},
            
            # 打脸逆袭类
            {"pattern": r"(打脸|反击|逆转|反杀|扬眉吐气|啪啪打脸|实力打脸)", "type": "revenge", "weight": 0.95},
            
            # 获得类
            {"pattern": r"(获得|得到|领悟|习得|融合|觉醒|继承)", "type": "gain", "weight": 0.75},
            
            # 震惊效果类
            {"pattern": r"(震惊|震撼|目瞪口呆|难以置信|哗然|全场哗然|倒吸冷气)", "type": "shock", "weight": 0.7},
            
            # 装逼类
            {"pattern": r"(嘲讽|冷笑|不屑|轻蔑|无视|淡然一笑|从容不迫)", "type": "arrogance", "weight": 0.6},
            
            # 神器宝物类
            {"pattern": r"(神器|神级|逆天|无敌|最强|至宝|绝世)", "type": "overpower", "weight": 0.8},
            
            # 美女情缘类
            {"pattern": r"(美女|女神|倾心|爱慕|投怀送抱|芳心暗许|以身相许)", "type": "romance", "weight": 0.65},
            
            # 财富资源类
            {"pattern": r"(财富|宝藏|金币|灵石|资源|富可敌国|一夜暴富)", "type": "wealth", "weight": 0.55},
            
            # 传承类
            {"pattern": r"(传承|秘籍|功法|血脉|体质|上古传承|至尊体质)", "type": "legacy", "weight": 0.8},
            
            # 装逼打脸类
            {"pattern": r"(扮猪吃虎|深藏不露|震惊四座|一鸣惊人|实力打脸)", "type": "pretend", "weight": 0.85},
            
            # 扮猪吃虎类
            {"pattern": r"(隐藏实力|低调行事|不鸣则已|厚积薄发)", "type": "hidden_power", "weight": 0.7}
        ]
        
        for pattern_info in cool_patterns:
            matches = re.findall(pattern_info["pattern"], content)
            for match in matches:
                cool_points.append({
                    "id": f"cp_{chapter_num}_{len(cool_points)}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "chapter": chapter_num,
                    "type": pattern_info["type"],
                    "content": match,
                    "weight": pattern_info["weight"],
                    "position": content.find(match),
                    "created_at": datetime.now().isoformat()
                })
        
        return cool_points
    
    def _identify_debts(self, content: str, chapter_num: int) -> List[Dict[str, Any]]:
        """识别债务（悬念/伏笔）"""
        debts = []
        
        # 债务模式（增强版）
        debt_patterns = [
            {"pattern": r"(伏笔|悬念|秘密|未解|谜团|未解之谜)", "type": "foreshadowing", "weight": 0.8},
            {"pattern": r"(以后|将来|迟早|总有一天|来日|终有一日)", "type": "promise", "weight": 0.7},
            {"pattern": r"(约定|誓言|承诺|保证|立誓|发誓)", "type": "oath", "weight": 0.85},
            {"pattern": r"(身世|来历|背景|身份|神秘身份)", "type": "mystery_identity", "weight": 0.9},
            {"pattern": r"(敌人|仇|恨|誓杀|报复|不共戴天|血海深仇)", "type": "vengeance", "weight": 0.8},
            {"pattern": r"(秘密|隐瞒|隐藏|不为人知|不告人)", "type": "secret", "weight": 0.75},
            {"pattern": r"(使命|宿命|注定|天命|天选)", "type": "destiny", "weight": 0.8},
            {"pattern": r"(预言|预示|征兆|异象|天机)", "type": "prophecy", "weight": 0.7}
        ]
        
        for pattern_info in debt_patterns:
            matches = re.findall(pattern_info["pattern"], content)
            for match in matches:
                debts.append({
                    "id": f"debt_{chapter_num}_{len(debts)}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "chapter": chapter_num,
                    "type": pattern_info["type"],
                    "content": match,
                    "weight": pattern_info["weight"],
                    "status": "active",
                    "created_at": datetime.now().isoformat()
                })
        
        return debts
    
    def _identify_micro_deliveries(self, content: str, chapter_num: int) -> List[Dict[str, Any]]:
        """识别微兑现"""
        deliveries = []
        
        # 微兑现模式（增强版）
        delivery_patterns = [
            {"pattern": r"(终于|总算|最终|终究|果然|如期而至)", "type": "resolution", "weight": 0.8},
            {"pattern": r"(真相大白|水落石出|揭晓|揭晓答案|真相浮出水面)", "type": "reveal", "weight": 0.9},
            {"pattern": r"(兑现|实现|达成|完成|圆满完成|如期完成)", "type": "fulfillment", "weight": 0.85},
            {"pattern": r"(报仇|雪恨|复仇|清算|血债血偿|大仇得报)", "type": "revenge_fulfill", "weight": 0.95},
            {"pattern": r"(重逢|相见|团聚|相遇|久别重逢|再次相遇)", "type": "reunion", "weight": 0.7},
            {"pattern": r"(成功|胜利|凯旋|功成|达成目标|圆满成功)", "type": "success", "weight": 0.75},
            {"pattern": r"(证明|证实|验证|应验|预言成真)", "type": "prove", "weight": 0.7},
            {"pattern": r"(回报|报答|感恩|报恩|滴水之恩涌泉相报)", "type": "reward", "weight": 0.65}
        ]
        
        for pattern_info in delivery_patterns:
            matches = re.findall(pattern_info["pattern"], content)
            for match in matches:
                deliveries.append({
                    "id": f"md_{chapter_num}_{len(deliveries)}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "chapter": chapter_num,
                    "type": pattern_info["type"],
                    "content": match,
                    "weight": pattern_info["weight"],
                    "position": content.find(match),
                    "created_at": datetime.now().isoformat()
                })
        
        return deliveries
    
    def _calculate_score(self, hooks: List, cool_points: List, debts: List, deliveries: List) -> tuple:
        """计算追读力评分"""
        # 基础权重（优化版）
        weights = {
            "hooks": 0.3,       # 钩子占 30% - 吸引读者继续阅读
            "cool_points": 0.35, # 爽点占 35% - 直接的阅读快感
            "debts": 0.2,       # 债务占 20% - 长期吸引力
            "deliveries": 0.15  # 兑现占 15% - 满足感和信任感
        }
        
        # 计算各项得分
        hook_score = sum(h["weight"] for h in hooks) * 10 if hooks else 0
        cool_score = sum(cp["weight"] for cp in cool_points) * 10 if cool_points else 0
        debt_score = sum(d["weight"] for d in debts) * 10 if debts else 0
        delivery_score = sum(md["weight"] for md in deliveries) * 10 if deliveries else 0
        
        # 归一化（每项满分 25 分）
        hook_score = min(hook_score, 25)
        cool_score = min(cool_score, 25)
        debt_score = min(debt_score, 25)
        delivery_score = min(delivery_score, 25)
        
        # 综合得分
        total_score = (
            hook_score * weights["hooks"] +
            cool_score * weights["cool_points"] +
            debt_score * weights["debts"] +
            delivery_score * weights["deliveries"]
        )
        
        breakdown = {
            "hooks": {
                "score": round(hook_score, 2),
                "count": len(hooks),
                "weight": weights["hooks"],
                "max_score": 25
            },
            "cool_points": {
                "score": round(cool_score, 2),
                "count": len(cool_points),
                "weight": weights["cool_points"],
                "max_score": 25
            },
            "debts": {
                "score": round(debt_score, 2),
                "count": len(debts),
                "weight": weights["debts"],
                "max_score": 25
            },
            "deliveries": {
                "score": round(delivery_score, 2),
                "count": len(deliveries),
                "weight": weights["deliveries"],
                "max_score": 25
            }
        }
        
        return round(total_score, 2), breakdown
    
    def _get_grade(self, score: float) -> str:
        """根据评分给出等级"""
        if score >= 90:
            return "S"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        else:
            return "D"
    
    def _generate_suggestions(self, hooks: List, cool_points: List, debts: List, deliveries: List) -> List[str]:
        """根据分析结果生成建议"""
        suggestions = []
        
        # 钩子建议
        if len(hooks) < 2:
            suggestions.append(f"⚠️ 钩子数量较少（当前{len(hooks)}个），建议增加悬念设置和情节转折")
        elif len(hooks) >= 5:
            suggestions.append("✅ 钩子丰富，保持良好的悬念设置")
        
        # 爽点建议
        if len(cool_points) < 2:
            suggestions.append(f"⚠️ 爽点数量较少（当前{len(cool_points)}个），建议增加打脸、升级等情节")
        elif len(cool_points) >= 4:
            suggestions.append("✅ 爽点充足，阅读体验良好")
        
        # 债务建议
        if len(debts) == 0:
            suggestions.append("⚠️ 未设置叙事债务，建议增加伏笔和悬念")
        elif len(debts) > 10:
            suggestions.append("⚠️ 债务数量较多，注意及时兑现避免读者遗忘")
        
        # 兑现建议
        if len(deliveries) == 0 and len(debts) > 0:
            suggestions.append("⚠️ 有未兑现的债务，建议适时安排兑现情节")
        
        # 平衡建议
        if len(cool_points) > 0 and len(debts) == 0:
            suggestions.append("💡 建议在爽点之外增加悬念设置，提升长期追读力")
        
        if len(debts) > 0 and len(deliveries) == 0:
            suggestions.append("💡 注意债务与兑现的平衡，避免只挖坑不填坑")
        
        return suggestions
    
    def _calculate_reader_pull_metrics(self, hooks: List, cool_points: List, debts: List, deliveries: List, content: str) -> Dict[str, float]:
        """计算追读力详细指标"""
        word_count = len(content.replace('\n', '').replace('\r', ''))
        
        return {
            "hook_density": round(len(hooks) / max(word_count, 1) * 1000, 2),  # 每千字钩子数
            "cool_point_density": round(len(cool_points) / max(word_count, 1) * 1000, 2),  # 每千字爽点数
            "debt_density": round(len(debts) / max(word_count, 1) * 1000, 2),  # 每千字债务数
            "delivery_rate": round(len(deliveries) / max(len(debts), 1) * 100, 2) if debts else 0,  # 债务兑现率
            "hook_to_cool_ratio": round(len(hooks) / max(len(cool_points), 1), 2) if cool_points else 0
        }
    
    def _update_trend_data(self):
        """更新趋势数据"""
        history = self.data.get("history", [])
        if len(history) >= 5:
            recent = history[-5:]
            avg_score = sum(h["score"] for h in recent) / len(recent)
            self.data["trend"]["average_scores"].append(avg_score)
            self.data["trend"]["hook_counts"].append(sum(h["hook_count"] for h in recent))
            self.data["trend"]["cool_point_counts"].append(sum(h["cool_point_count"] for h in recent))
            self.data["trend"]["debt_counts"].append(sum(h["debt_count"] for h in recent))
            
            # 保持趋势数据不超过 20 个点
            max_points = 20
            self.data["trend"]["average_scores"] = self.data["trend"]["average_scores"][-max_points:]
            self.data["trend"]["hook_counts"] = self.data["trend"]["hook_counts"][-max_points:]
            self.data["trend"]["cool_point_counts"] = self.data["trend"]["cool_point_counts"][-max_points:]
            self.data["trend"]["debt_counts"] = self.data["trend"]["debt_counts"][-max_points:]
    
    def get_score_history(self) -> List[Dict[str, Any]]:
        """获取评分历史"""
        return self.data.get("history", [])
    
    def get_debt_status(self) -> Dict[str, Any]:
        """获取债务状态"""
        active_debts = [d for d in self.data.get("debts", []) if d.get("status") == "active"]
        resolved_debts = [d for d in self.data.get("debts", []) if d.get("status") == "resolved"]
        
        return {
            "total": len(self.data.get("debts", [])),
            "active": len(active_debts),
            "resolved": len(resolved_debts),
            "resolution_rate": round(len(resolved_debts) / max(len(self.data.get("debts", [])), 1) * 100, 2),
            "debt_list": active_debts[:10]
        }
    
    def resolve_debt(self, debt_id: str) -> bool:
        """标记债务已解决"""
        for debt in self.data.get("debts", []):
            if debt["id"] == debt_id:
                debt["status"] = "resolved"
                debt["resolved_at"] = datetime.now().isoformat()
                self._save_data()
                return True
        return False
    
    def get_overall_score(self) -> float:
        """获取总体追读力评分"""
        scores = [h["score"] for h in self.data.get("history", [])]
        if not scores:
            return 0.0
        return round(sum(scores) / len(scores), 2)
    
    def get_chapter_score(self, chapter_num: int) -> Optional[Dict[str, Any]]:
        """获取特定章节的评分"""
        return self.data.get("scores", {}).get(f"chapter_{chapter_num}")
    
    def get_trend_analysis(self) -> Dict[str, Any]:
        """获取趋势分析"""
        history = self.data.get("history", [])
        if not history:
            return {
                "status": "no_data",
                "message": "暂无足够数据进行趋势分析"
            }
        
        recent_scores = [h["score"] for h in history[-5:]]
        earlier_scores = [h["score"] for h in history[-10:-5]] if len(history) >= 10 else []
        
        trend_score = 0
        trend_message = ""
        
        if len(recent_scores) >= 3:
            recent_avg = sum(recent_scores) / len(recent_scores)
            if earlier_scores:
                earlier_avg = sum(earlier_scores) / len(earlier_scores)
                diff = recent_avg - earlier_avg
                trend_score = diff
                if diff > 5:
                    trend_message = "📈 追读力显著上升"
                elif diff > 2:
                    trend_message = "📈 追读力略有上升"
                elif diff < -5:
                    trend_message = "📉 追读力显著下降"
                elif diff < -2:
                    trend_message = "📉 追读力略有下降"
                else:
                    trend_message = "➡️ 追读力保持稳定"
            else:
                trend_message = "📊 数据积累中"
        
        return {
            "status": "ok",
            "trend_score": round(trend_score, 2),
            "trend_message": trend_message,
            "recent_average": round(sum(recent_scores) / len(recent_scores), 2) if recent_scores else 0,
            "total_chapters": len(history),
            "history": history[-10:]
        }