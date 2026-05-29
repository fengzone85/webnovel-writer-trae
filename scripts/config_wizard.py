#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目配置向导
交互式引导用户完成项目配置
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass


@dataclass
class WizardStep:
    """向导步骤"""
    key: str
    question: str
    options: Optional[list] = None
    default: Optional[str] = None
    validator: Optional[Callable] = None
    is_password: bool = False


class ConfigWizard:
    """配置向导"""

    STEPS = [
        WizardStep(
            key="project_name",
            question="请输入项目名称：",
            validator=lambda x: len(x) >= 2 and len(x) <= 50
        ),
        WizardStep(
            key="genre",
            question="请选择题材（输入数字）：",
            options=[
                "1. 都市异能",
                "2. 都市重生",
                "3. 玄幻",
                "4. 修仙",
                "5. 科幻",
                "6. 末世",
                "7. 洪荒",
                "8. 武侠",
                "9. 奇幻",
                "10. 体育",
                "11. 军事",
                "12. 娱乐圈",
                "13. 校园",
                "14. 其他"
            ]
        ),
        WizardStep(
            key="main_character",
            question="请输入主角名字：",
            validator=lambda x: len(x) >= 1 and len(x) <= 20
        ),
        WizardStep(
            key="finger",
            question="请选择金手指类型（输入数字）：",
            options=[
                "1. 系统流",
                "2. 重生先知",
                "3. 血脉传承",
                "4. 异能觉醒",
                "5. 随身空间",
                "6. 无（无金手指）"
            ],
            default="1"
        ),
        WizardStep(
            key="writing_mode",
            question="请选择写作模式（输入数字）：",
            options=[
                "1. 合同驱动（推荐）",
                "2. 自由写作",
                "3. 混合模式"
            ],
            default="1"
        ),
        WizardStep(
            key="embed_api",
            question="请输入ModelScope Embedding API Key（可跳过）：",
            default=""
        ),
        WizardStep(
            key="rerank_api",
            question="请输入Jina AI Rerank API Key（可跳过）：",
            default=""
        ),
        WizardStep(
            key="proxy",
            question="请输入代理地址（如：http://127.0.0.1:10809，可跳过）：",
            default=""
        ),
    ]

    GENRE_MAP = {
        "1": "都市异能",
        "2": "都市重生",
        "3": "玄幻",
        "4": "修仙",
        "5": "科幻",
        "6": "末世",
        "7": "洪荒",
        "8": "武侠",
        "9": "奇幻",
        "10": "体育",
        "11": "军事",
        "12": "娱乐圈",
        "13": "校园",
        "14": "其他"
    }

    FINGER_MAP = {
        "1": "系统流",
        "2": "重生先知",
        "3": "血脉传承",
        "4": "异能觉醒",
        "5": "随身空间",
        "6": "无"
    }

    MODE_MAP = {
        "1": "contract",
        "2": "free",
        "3": "mixed"
    }

    def __init__(self):
        self.answers: Dict[str, Any] = {}
        self.step_index = 0

    def print_welcome(self):
        """打印欢迎信息"""
        print("=" * 60)
        print("🎭 Webnovel Writer 项目配置向导")
        print("=" * 60)
        print()
        print("本向导将帮助您配置项目参数。")
        print("按 Ctrl+C 可随时退出。")
        print()

    def print_progress(self):
        """打印进度"""
        total = len(self.STEPS)
        current = self.step_index + 1
        bar_length = 30
        filled = int(bar_length * current / total)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"\n[{bar}] {current}/{total}")
        print("-" * 60)

    def get_input(self, step: WizardStep) -> str:
        """获取用户输入"""
        print(f"\n{step.question}")

        if step.options:
            for opt in step.options:
                print(f"  {opt}")

        if step.default:
            prompt = f"（默认: {step.default}）"
        else:
            prompt = ""

        if step.is_password:
            import getpass
            value = getpass.getpass(f"请输入{prompt}: ").strip()
        else:
            value = input(f"请输入{prompt}: ").strip()

        return value or step.default or ""

    def validate(self, step: WizardStep, value: str) -> bool:
        """验证输入"""
        if step.validator:
            return step.validator(value)
        return True

    def process_value(self, step: WizardStep, value: str) -> Any:
        """处理输入值"""
        if step.key == "genre" and value in self.GENRE_MAP:
            return self.GENRE_MAP[value]
        elif step.key == "finger" and value in self.FINGER_MAP:
            return self.FINGER_MAP[value]
        elif step.key == "writing_mode" and value in self.MODE_MAP:
            return self.MODE_MAP[value]
        return value

    def run(self) -> Dict[str, Any]:
        """运行向导"""
        self.print_welcome()

        for self.step_index, step in enumerate(self.STEPS):
            self.print_progress()
            print(f"\n📌 {step.question}")

            if step.options:
                for opt in step.options:
                    print(f"   {opt}")

            while True:
                value = input(f"\n请输入: ").strip()

                if not value and step.default:
                    value = step.default
                    print(f"（使用默认值: {value}）")
                    break
                elif not value:
                    print("⚠️ 请输入有效值")
                    continue

                if step.validator and not step.validator(value):
                    print("⚠️ 输入无效，请重新输入")
                    continue

                break

            self.answers[step.key] = self.process_value(step, value)

        self.print_result()
        return self.answers

    def print_result(self):
        """打印结果"""
        print("\n" + "=" * 60)
        print("✅ 配置完成！")
        print("=" * 60)

        for key, value in self.answers.items():
            print(f"  {key}: {value}")

    def generate_config(self) -> Dict[str, Any]:
        """生成配置"""
        return {
            "project": {
                "name": self.answers.get("project_name", "未命名项目"),
                "genre": self.answers.get("genre", "其他"),
                "main_character": self.answers.get("main_character", ""),
                "finger": self.answers.get("finger", "无"),
                "writing_mode": self.answers.get("writing_mode", "contract")
            },
            "api": {
                "embed_api_key": self.answers.get("embed_api", ""),
                "rerank_api_key": self.answers.get("rerank_api", ""),
                "proxy": self.answers.get("proxy", "")
            }
        }

    def save_config(self, output_path: Path):
        """保存配置"""
        config = self.generate_config()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"\n💾 配置已保存到: {output_path}")


def run_wizard() -> Dict[str, Any]:
    """运行配置向导"""
    wizard = ConfigWizard()
    return wizard.run()


if __name__ == "__main__":
    result = run_wizard()
    print("\n最终配置：")
    print(json.dumps(result, ensure_ascii=False, indent=2))
