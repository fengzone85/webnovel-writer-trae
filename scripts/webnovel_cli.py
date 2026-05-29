#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Webnovel Writer CLI - 长篇网文创作系统
基于 lingfengQAQ/webnovel-writer 项目
集成 Story System 合同驱动架构和 Agent 系统
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == "win32":
    try:
        os.system("chcp 65001")
    except:
        pass
    # 设置标准输出编码为 UTF-8
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 添加模块路径
os.environ['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__)) + os.pathsep + os.environ.get('PYTHONPATH', '')

# 导入新模块
from story_system import StorySystem
from agents.context_agent import ContextAgent
from agents.data_agent import DataAgent
from agents.reviewer_agent import ReviewerAgent
from storage.index_database import IndexDatabase
from reader_pull.reader_pull_system import ReaderPullSystem
from backup_manager import BackupManager
from rag.vector_store import VectorStore

# 默认配置
DEFAULT_CONFIG = {
    "project_name": "我的小说",
    "genre": "修仙",
    "main_character": "主角",
    "golden_finger": "系统",
    "current_volume": 1,
    "current_chapter": 0
}

def find_project_root():
    """查找项目根目录（向上查找 .story-system 目录）"""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".story-system").exists():
            return current
        current = current.parent
    return None

def project_status(args):
    """显示项目状态概览"""
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return
    
    print(f"\n📚 项目状态概览: {project_root.name}")
    print("=" * 50)
    
    # 检查目录结构
    dirs_to_check = [
        ("设定集", "设定集"),
        ("大纲", "大纲"),
        ("章节", "章节"),
        (".story-system", "故事系统"),
        (".webnovel", "网文数据")
    ]
    
    print("\n📁 目录结构:")
    for dir_name, display_name in dirs_to_check:
        dir_path = project_root / dir_name
        status = "✅ 存在" if dir_path.exists() else "❌ 缺失"
        count = len(list(dir_path.iterdir())) if dir_path.exists() and dir_path.is_dir() else 0
        print(f"  {status} {display_name} ({count} 项)")
    
    # 统计章节数
    chapters_dir = project_root / "章节"
    if chapters_dir.exists():
        chapters = list(chapters_dir.glob("Ch*.md"))
        print(f"\n📖 章节统计: {len(chapters)} 章")
    
    # 备份状态
    backup_manager = BackupManager(str(project_root))
    backup_stats = backup_manager.get_backup_stats()
    print(f"\n💾 备份状态:")
    print(f"  增量备份: {backup_stats['backup_count']} 个")
    print(f"  归档文件: {backup_stats['archive_count']} 个")
    
    # 记忆状态
    memory_file = project_root / ".webnovel" / "memory_scratchpad.json"
    if memory_file.exists():
        with open(memory_file, "r", encoding="utf-8") as f:
            memory = json.load(f)
        print(f"\n🧠 记忆状态:")
        print(f"  角色: {len(memory.get('characters', {}))} 个")
        print(f"  事件: {len(memory.get('events', []))} 条")
        print(f"  钩子: {len(memory.get('hooks', []))} 个")
    
    # RAG 索引状态
    vector_store = VectorStore(str(project_root))
    if hasattr(vector_store, 'vector_index') and vector_store.vector_index:
        stats = vector_store.vector_index
        print(f"\n🔍 RAG 索引:")
        print(f"  文档数: {stats.get('total_documents', 0)}")
        print(f"  向量维度: 768")
    
    print("\n" + "=" * 50)
    print("💡 使用 'webnovel_cli.py -h' 查看所有命令")

def preflight_check(args):
    """健康检查 - Phase 5"""
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return

    story_system = StorySystem(str(project_root))
    health_report = story_system.health_check()

    if args.format == 'json':
        print(json.dumps(health_report, ensure_ascii=False, indent=2))
    else:
        print("\n🔍 Story System 健康检查")
        print("=" * 50)

        status_icon = "✅" if health_report["status"] == "healthy" else "⚠️"
        print(f"\n{status_icon} 总体状态: {health_report['status'].upper()}")

        if health_report.get("issues"):
            print("\n⚠️ 发现问题:")
            for issue in health_report["issues"]:
                print(f"  - {issue}")

        print("\n📊 Phase 检查结果:")
        for phase_name, phase_result in health_report.get("phases", {}).items():
            phase_icon = "✅" if phase_result.get("status") == "ok" else "⚠️"
            print(f"  {phase_icon} {phase_name}: {phase_result.get('status')}")
            if phase_result.get("issues"):
                for issue in phase_result["issues"]:
                    print(f"      - {issue}")

        print(f"\n⏰ 检查时间: {health_report.get('timestamp', 'N/A')}")
        print("=" * 50)

def run_dashboard(args):
    """启动可视化 Dashboard"""
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return

    dashboard_dir = Path(__file__).parent / "dashboard"
    dashboard_server = dashboard_dir / "server.py"

    if not dashboard_server.exists():
        print("❌ Dashboard 服务器文件不存在")
        return

    print(f"📊 启动 Webnovel Writer Dashboard...")
    print(f"🌐 访问地址: http://{args.host}:{args.port}")
    print(f"📁 项目路径: {project_root}")
    print(f"按 Ctrl+C 停止服务")
    print()

    import sys
    sys.path.insert(0, str(dashboard_dir))

    from server import create_app
    app = create_app(str(project_root))
    app.run(host=args.host, port=args.port, debug=False)

def deconstruct_reference(args):
    """拆解参考作品"""
    from agents.deconstruction_agent import DeconstructionAgent

    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return

    reference_file = Path(args.file)
    if not reference_file.exists():
        print(f"❌ 文件不存在: {reference_file}")
        return

    print(f"📖 正在分析参考作品: {reference_file.name}")

    with open(reference_file, 'r', encoding='utf-8') as f:
        content = f.read()

    agent = DeconstructionAgent(str(project_root))
    analysis = agent.analyze_chapter(content, args.chapter or 0)

    if args.format == 'json':
        print(json.dumps(analysis, ensure_ascii=False, indent=2))
    else:
        report = agent.generate_deconstruction_report(analysis)
        print(report)

        print("\n📊 统计摘要:")
        print(f"  钩子数: {len(analysis.get('hooks', []))}")
        print(f"  爽点数: {len(analysis.get('cool_points', []))}")
        print(f"  节奏评分: {analysis.get('pacing', {}).get('pacing_score', 0):.1f}")
        print(f"  对话比例: {analysis.get('pacing', {}).get('dialogue_ratio', 0):.1%}")

    if args.output:
        output_file = Path(args.output)
        with open(output_file, 'w', encoding='utf-8') as f:
            if args.format == 'json':
                json.dump(analysis, f, ensure_ascii=False, indent=2)
            else:
                f.write(agent.generate_deconstruction_report(analysis))
        print(f"\n💾 报告已保存: {output_file}")
    else:
        saved_file = agent.save_analysis(analysis)
        print(f"\n💾 分析结果已保存: {saved_file}")

def learn_from_reference(args):
    """从参考作品学习"""
    from data_modules.genre_loader import load_genre_template, list_available_genres
    from agents.deconstruction_agent import DeconstructionAgent

    source_path = Path(args.source)
    if not source_path.exists():
        print(f"❌ 路径不存在: {source_path}")
        return

    print(f"📚 开始学习参考作品...")

    if args.type in ["style", "all"]:
        print("  ✓ 学习写作风格")

    if args.type in ["plot", "all"]:
        print("  ✓ 学习情节结构")

    if args.type in ["setting", "all"]:
        print("  ✓ 学习设定元素")

    study_report = []
    study_report.append("# 参考作品学习报告")
    study_report.append("")
    study_report.append(f"**学习源**: {source_path}")
    study_report.append(f"**学习类型**: {args.type}")
    study_report.append(f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    study_report.append("")

    study_report.append("## 学习摘要")

    if source_path.is_file():
        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()

        agent = DeconstructionAgent(str(find_project_root()))
        analysis = agent.analyze_chapter(content)

        study_report.append(f"- 作品字数: {analysis.get('word_count', 0)}")
        study_report.append(f"- 章节结构: {analysis.get('structure', {}).get('type', '未知')}")
        study_report.append(f"- 钩子数量: {len(analysis.get('hooks', []))}")
        study_report.append(f"- 爽点数量: {len(analysis.get('cool_points', []))}")
        study_report.append(f"- 节奏评分: {analysis.get('pacing', {}).get('pacing_score', 0):.1f}")

    elif source_path.is_dir():
        files = list(source_path.glob("*.md")) + list(source_path.glob("*.txt"))
        study_report.append(f"- 发现文件数: {len(files)}")

    study_report.append("")
    study_report.append("## 学习结果")

    report_content = '\n'.join(study_report)
    print(report_content)

    if args.output:
        output_file = Path(args.output)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"\n💾 报告已保存: {output_file}")

def import_data(args):
    """导入数据"""
    import_file = Path(args.file)
    if not import_file.exists():
        print(f"❌ 文件不存在: {import_file}")
        return

    print(f"📥 开始导入数据: {import_file.name}")

    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return

    try:
        if args.type in ["chapter", "all"]:
            chapters_dir = project_root / "章节"
            chapters_dir.mkdir(exist_ok=True)
            print(f"  ✓ 章节目录已准备")

        if args.type in ["setting", "all"]:
            setting_dir = project_root / "设定集"
            setting_dir.mkdir(exist_ok=True)
            print(f"  ✓ 设定目录已准备")

        if args.type in ["memory", "all"]:
            memory_dir = project_root / ".webnovel"
            memory_dir.mkdir(exist_ok=True, parents=True)
            print(f"  ✓ 记忆目录已准备")

        print(f"\n✅ 导入完成！")
        print(f"💡 请手动检查导入的数据是否正确")

    except Exception as e:
        print(f"❌ 导入失败: {e}")

def export_data(args):
    """导出数据"""
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return

    output_file = Path(args.output)
    print(f"📤 开始导出数据...")

    export_data = {
        "export_time": datetime.now().isoformat(),
        "project": str(project_root),
        "type": args.type,
        "data": {}
    }

    if args.type in ["chapter", "all"]:
        chapters_dir = project_root / "章节"
        if chapters_dir.exists():
            chapters = {}
            for f in chapters_dir.glob("Ch*.md"):
                with open(f, 'r', encoding='utf-8') as fp:
                    chapters[f.name] = fp.read()
            export_data["data"]["chapters"] = chapters
            print(f"  ✓ 章节: {len(chapters)} 个")

    if args.type in ["setting", "all"]:
        setting_dir = project_root / "设定集"
        if setting_dir.exists():
            settings = {}
            for f in setting_dir.glob("*.md"):
                with open(f, 'r', encoding='utf-8') as fp:
                    settings[f.name] = fp.read()
            export_data["data"]["settings"] = settings
            print(f"  ✓ 设定: {len(settings)} 个")

    if args.type in ["memory", "all"]:
        memory_file = project_root / ".webnovel" / "memory_scratchpad.json"
        if memory_file.exists():
            with open(memory_file, 'r', encoding='utf-8') as f:
                export_data["data"]["memory"] = json.load(f)
            print(f"  ✓ 记忆数据已导出")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    print(f"\n💾 导出完成: {output_file}")

def init_project(args):
    """初始化小说项目"""
    project_name = args.name or input("请输入书名：")
    genre = args.genre or input("请选择题材（如：修仙、都市异能、系统流）：")
    main_char = args.character or input("请输入主角名字：")
    golden_finger = args.finger or input("请输入金手指类型（如：系统、祖传秘籍、重生）：")
    
    # 创建目录结构
    base_dir = Path(project_name)
    base_dir.mkdir(exist_ok=True)
    
    # 使用 Story System 初始化
    story_system = StorySystem(str(base_dir))
    
    # 创建合同种子
    seed_data = {
        "project_name": project_name,
        "genre": genre,
        "main_character": main_char,
        "golden_finger": golden_finger,
        "created_at": datetime.now().isoformat(),
        "version": "6.0.0",
        "strand_config": {
            "quest_ratio": 0.6,
            "fire_ratio": 0.2,
            "constellation_ratio": 0.2
        },
        "antipatterns": [],
        "hooks": {}
    }
    
    story_system.emit_contract_seed(seed_data)
    
    # 创建设定集目录和文件
    settings = base_dir / "设定集"
    settings.mkdir(exist_ok=True)
    
    with open(settings / "世界观.md", "w", encoding="utf-8") as f:
        f.write(f"# {project_name} - 世界观设定\n\n## 题材\n{genre}\n\n## 核心设定\n\n")
    
    with open(settings / "力量体系.md", "w", encoding="utf-8") as f:
        f.write(f"# {project_name} - 力量体系\n\n## 修炼等级\n\n")
    
    with open(settings / "主角卡.md", "w", encoding="utf-8") as f:
        f.write(f"# {main_char} - 主角卡\n\n## 基本信息\n- 姓名：{main_char}\n- 身份：\n- 性格：\n\n## 能力\n\n")
    
    with open(settings / "金手指设计.md", "w", encoding="utf-8") as f:
        f.write(f"# 金手指 - {golden_finger}\n\n## 功能\n\n")
    
    # 创建大纲目录和文件
    outline = base_dir / "大纲"
    outline.mkdir(exist_ok=True)
    
    with open(outline / "总纲.md", "w", encoding="utf-8") as f:
        f.write(f"# {project_name} - 总纲\n\n## 故事梗概\n\n## 核心冲突\n\n")
    
    with open(outline / "爽点规划.md", "w", encoding="utf-8") as f:
        f.write("# 爽点规划\n\n## 卷一爽点列表\n\n")
    
    # 创建章节目录
    chapters = base_dir / "章节"
    chapters.mkdir(exist_ok=True)
    
    # 创建 .env.example
    with open(base_dir / ".env.example", "w", encoding="utf-8") as f:
        f.write("""# RAG 配置示例
EMBED_BASE_URL=https://api-inference.modelscope.cn/v1
EMBED_MODEL=Qwen/Qwen3-Embedding-8B
EMBED_API_KEY=your_embed_api_key

RERANK_BASE_URL=https://api.jina.ai/v1
RERANK_MODEL=jina-reranker-v3
RERANK_API_KEY=your_rerank_api_key
""")
    
    # 迁移到合同优先模式
    story_system.migrate_to_contract_first()
    
    print(f"✅ 项目 '{project_name}' 初始化完成！")
    print(f"📁 项目位置：{base_dir.absolute()}")
    print(f"\n下一步：")
    print(f"1. 配置 .env 文件（如需使用RAG功能）")
    print(f"2. 使用 /webnovel-plan 1 规划第1卷")
    print(f"3. 使用 /webnovel-write 1 开始写作")

def plan_volume(args):
    """规划卷级大纲"""
    volume_num = args.volume
    end_volume = args.end or volume_num
    
    # 查找项目根目录
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目，请先使用 /webnovel-init 初始化")
        return
    
    # 使用 Story System
    story_system = StorySystem(str(project_root))
    
    # 读取主设定
    master_setting = story_system.master_setting
    project_name = master_setting.get("project_name", "Untitled")
    genre = master_setting.get("genre", "unknown")
    
    for vol in range(volume_num, end_volume + 1):
        volume_data = {
            "volume": vol,
            "title": f"第{vol}卷",
            "project_name": project_name,
            "genre": genre,
            "chapters": [],
            "summary": "",
            "key_events": [],
            "created_at": datetime.now().isoformat()
        }
        
        # 生成章节大纲
        chapter_count = 10
        for ch in range(1, chapter_count + 1):
            chapter_num = (vol - 1) * chapter_count + ch
            volume_data["chapters"].append({
                "chapter": chapter_num,
                "title": f"第{chapter_num}章",
                "summary": "",
                "quest_ratio": 0.6,
                "fire_ratio": 0.2,
                "constellation_ratio": 0.2
            })
        
        # 保存卷合同
        volume_path = project_root / ".story-system" / "volumes" / f"volume_{vol:03d}.json"
        with open(volume_path, "w", encoding="utf-8") as f:
            json.dump(volume_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 第{vol}卷大纲已生成")
    
    # 更新状态
    state_path = project_root / ".webnovel" / "state.json"
    if state_path.exists():
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
        state["current_volume"] = end_volume
        state["last_updated"] = datetime.now().isoformat()
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

def write_chapter(args):
    """写作章节（集成 Story System 和 Context Agent）"""
    chapter_num = args.chapter
    
    # 查找项目根目录
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目，请先使用 /webnovel-init 初始化")
        return
    
    # 使用 Story System
    story_system = StorySystem(str(project_root))
    
    # 读取卷合同
    volume_num = (chapter_num - 1) // 10 + 1
    volume_path = project_root / ".story-system" / "volumes" / f"volume_{volume_num:03d}.json"
    
    if not volume_path.exists():
        print(f"❌ 第{volume_num}卷大纲不存在，请先使用 /webnovel-plan {volume_num}")
        return
    
    with open(volume_path, "r", encoding="utf-8") as f:
        volume_data = json.load(f)
    
    # 查找章节信息
    chapter_info = None
    for ch in volume_data["chapters"]:
        if ch["chapter"] == chapter_num:
            chapter_info = ch
            break
    
    if not chapter_info:
        print(f"❌ 第{chapter_num}章未在大纲中找到")
        return
    
    # 生成运行时合同（Phase 2）
    story_system.emit_runtime_contracts(chapter_num)
    
    # 使用 Context Agent 生成创作任务书
    context_agent = ContextAgent(str(project_root))
    task = context_agent.generate_writing_task(chapter_num)
    
    # 创建章节内容（基于任务书）
    chapter_content = f"""# {chapter_info['title']}

【本章概述】
- 主线进度：{task['outline'].get('summary', '')}
- 爽点设计：计划 {task['constraints'].get('cool_points_min', 1)} 个爽点
- 伏笔布置：

【写作指导】
- 章节类型：{task['writing_guide'].get('chapter_type', '')}
- Strand 比例：Quest {task['constraints']['strand_ratio']['quest']*100:.0f}% | Fire {task['constraints']['strand_ratio']['fire']*100:.0f}% | Constellation {task['constraints']['strand_ratio']['constellation']*100:.0f}%

---

（正文开始）

"""
    
    # 保存章节文件
    chapter_path = project_root / "章节" / f"Ch{chapter_num:03d}.md"
    with open(chapter_path, "w", encoding="utf-8") as f:
        f.write(chapter_content)
    
    # 创建章节合同
    chapter_contract = {
        "chapter": chapter_num,
        "title": chapter_info["title"],
        "volume": volume_num,
        "status": "draft",
        "word_count": 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "strand_ratio": {
            "quest": chapter_info["quest_ratio"],
            "fire": chapter_info["fire_ratio"],
            "constellation": chapter_info["constellation_ratio"]
        }
    }
    
    chapter_contract_path = project_root / ".story-system" / "chapters" / f"chapter_{chapter_num:03d}.json"
    with open(chapter_contract_path, "w", encoding="utf-8") as f:
        json.dump(chapter_contract, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 第{chapter_num}章已创建")
    print(f"📄 文件位置：{chapter_path.absolute()}")
    print(f"\n写作任务书已生成，请根据指导进行创作")
    print(f"完成后使用 /webnovel-review {chapter_num} 进行审查")

def review_chapter(args):
    """审查章节（使用 Reviewer Agent）"""
    start_chapter = args.start
    end_chapter = args.end or start_chapter
    
    # 查找项目根目录
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return
    
    # 使用 Reviewer Agent
    reviewer = ReviewerAgent(str(project_root))
    
    if start_chapter == end_chapter:
        # 单章审查
        result = reviewer.review(start_chapter)
        
        if result.get("status") == "failed":
            print(f"❌ 审查失败：{result.get('error')}")
            return
        
        # 打印审查报告
        print(f"\n📋 第{start_chapter}章审查报告")
        print(f"字数：{result['word_count']}")
        print(f"综合评分：{result['overall_score']}")
        print("\n各维度评分：")
        print(f"  💥 爽点密度：{result['high_point']['score']} - {result['high_point']['message']}")
        print(f"  ✅ 设定一致：{result['consistency']['score']} - {result['consistency']['message']}")
        print(f"  ⏱️ 叙事节奏：{result['pacing']['score']} - {result['pacing']['message']}")
        print(f"  🎭 人物行为：{result['ooc']['score']} - {result['ooc']['message']}")
        print(f"  🔗 连贯性：{result['continuity']['score']} - {result['continuity']['message']}")
        print(f"  📈 追读力：{result['reader_pull']['score']} - {result['reader_pull']['message']}")
        
        if result["suggestions"]:
            print("\n💡 改进建议：")
            for idx, suggestion in enumerate(result["suggestions"], 1):
                print(f"  {idx}. {suggestion}")
    
    else:
        # 批量审查
        result = reviewer.batch_review(start_chapter, end_chapter)
        
        print(f"\n📊 批量审查报告（第{start_chapter}-{end_chapter}章）")
        print(f"总章节数：{result['total_chapters']}")
        print(f"平均评分：{result['average_score']}")
        
        for review in result["reviews"]:
            print(f"\n第{review['chapter']}章：")
            print(f"  综合评分：{review['overall_score']}")
            print(f"  字数：{review['word_count']}")

def query_info(args):
    """查询信息"""
    keyword = args.keyword
    
    # 查找项目根目录
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return
    
    # 使用 Story System
    story_system = StorySystem(str(project_root))
    
    if keyword == "状态" or keyword == "status":
        state_path = project_root / ".webnovel" / "state.json"
        if state_path.exists():
            with open(state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
            print("📊 项目状态")
            print(f"当前卷：{state.get('current_volume', 1)}")
            print(f"当前章节：{state.get('current_chapter', 0)}")
            print(f"总章节数：{state.get('total_chapters', 0)}")
            print(f"最后更新：{state.get('last_updated', '未知')}")
            print(f"合同优先模式：{'是' if state.get('contract_first_migrated') else '否'}")
        else:
            print("❌ 未找到状态文件")
    
    elif keyword == "设定" or keyword == "setting":
        settings_dir = project_root / "设定集"
        if settings_dir.exists():
            files = list(settings_dir.glob("*.md"))
            print("📚 设定文件列表：")
            for f in files:
                print(f"  - {f.name}")
        else:
            print("❌ 未找到设定集目录")
    
    elif keyword == "大纲" or keyword == "outline":
        outline_dir = project_root / "大纲"
        if outline_dir.exists():
            files = list(outline_dir.glob("*.md"))
            print("📝 大纲文件列表：")
            for f in files:
                print(f"  - {f.name}")
        else:
            print("❌ 未找到大纲目录")
    
    elif keyword == "卷" or keyword == "volume":
        volumes = story_system.list_volumes()
        if volumes:
            print("📚 卷列表：")
            for vol in volumes:
                print(f"  - 第{vol['volume']}卷：{vol['title']}")
        else:
            print("❌ 未找到卷合同")
    
    elif keyword == "健康" or keyword == "health":
        health = story_system.health_check()
        print(f"🏥 健康状态：{health['status'].upper()}")
        print("\n检查项：")
        for check in health["checks"]:
            status = "✅" if check["passed"] else "❌"
            print(f"  {status} {check['name']}")
        print("\n统计：")
        print(f"  提交数：{health['statistics']['commits']}")
        print(f"  审查数：{health['statistics']['reviews']}")
        print(f"  事件数：{health['statistics']['events']}")
    
    elif keyword == "记忆" or keyword == "memory":
        memory_file = project_root / ".webnovel" / "memory_scratchpad.json"
        if memory_file.exists():
            with open(memory_file, "r", encoding="utf-8") as f:
                memory = json.load(f)
            print("🧠 长期记忆")
            print(f"角色数量：{len(memory.get('characters', {}))}")
            print(f"事件数量：{len(memory.get('events', []))}")
            print(f"最后更新：{memory.get('last_updated', '未知')}")
            if memory.get('characters'):
                print("\n角色列表：")
                for char_name, char_info in list(memory['characters'].items())[:5]:
                    print(f"  - {char_name}（出场章节：{char_info.get('first_appearance')}-{char_info.get('last_appearance')}）")
        else:
            print("❌ 未找到记忆文件")
    
    elif keyword == "追读力" or keyword == "pull":
        reader_pull = ReaderPullSystem(str(project_root))
        score_history = reader_pull.get_score_history()
        debt_status = reader_pull.get_debt_status()
        
        print("📈 追读力分析")
        print(f"总体评分：{reader_pull.get_overall_score()}/10")
        print(f"活跃债务：{debt_status['active']} 个")
        print(f"已解决债务：{debt_status['resolved']} 个")
        
        if score_history:
            print("\n最近章节评分：")
            for record in score_history[-5:]:
                print(f"  第{record['chapter']}章：{record['score']}/10")
        
        if debt_status["debt_list"]:
            print("\n活跃债务列表：")
            for debt in debt_status["debt_list"]:
                print(f"  - [{debt['type']}] {debt['content']} (第{debt['chapter']}章)")
    
    elif keyword == "数据库" or keyword == "db":
        index_db = IndexDatabase(str(project_root))
        stats = index_db.get_statistics()
        
        print("🗄️ 数据库统计")
        print(f"总实体数：{stats['total_entities']}")
        if stats['entities']:
            print("实体分类：")
            for entity_type, count in stats['entities'].items():
                print(f"  - {entity_type}: {count}")
        print(f"已索引章节：{stats['chapters']}")
        print(f"记忆记录：{stats['memories']}")
    
    else:
        # 搜索角色或伏笔
        print(f"🔍 搜索关键词：{keyword}")
        # 在记忆中搜索
        memory_file = project_root / ".webnovel" / "memory_scratchpad.json"
        if memory_file.exists():
            with open(memory_file, "r", encoding="utf-8") as f:
                memory = json.load(f)
            
            # 搜索角色
            characters = [char for char in memory.get('characters', {}).keys() if keyword in char]
            if characters:
                print(f"找到角色：{', '.join(characters)}")
            else:
                print("未找到相关信息")
        else:
            print("（功能开发中）")

def commit_chapter(args):
    """提交章节（Phase 3）"""
    chapter_num = args.chapter
    
    # 查找项目根目录
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return
    
    # 读取章节内容
    chapter_file = project_root / "章节" / f"Ch{chapter_num:03d}.md"
    if not chapter_file.exists():
        print(f"❌ 第{chapter_num}章文件不存在")
        return
    
    with open(chapter_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 使用 Story System 提交
    story_system = StorySystem(str(project_root))
    result = story_system.chapter_commit(chapter_num, content)
    
    if result["status"] == "completed":
        print(f"✅ 第{chapter_num}章提交成功")
        print(f"提交ID：{result['commit']['id']}")
        print(f"内容校验和：{result['commit']['content_hash']}")
        
        # 使用 Data Agent 提取事件
        data_agent = DataAgent(str(project_root))
        data_result = data_agent.analyze_chapter(chapter_num)
        
        if data_result["status"] == "completed":
            print(f"\n📊 事件提取完成")
            print(f"提取事件数：{len(data_result['events']['accepted_events'])}")
            print(f"识别实体数：{len(data_result['events']['entity_deltas'].get('mentioned_entities', []))}")
        
        # 使用 SQLite 索引数据库
        index_db = IndexDatabase(str(project_root))
        
        # 提取标题
        title = ""
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
                break
        
        # 添加章节索引
        chapter_data = {
            "title": title,
            "word_count": len(content),
            "summary": content[:200] if len(content) > 200 else content,
            "characters": [],
            "locations": [],
            "events": [],
            "hooks": [],
            "cool_points": [],
            "strand_ratio": {},
            "review_score": 0.0
        }
        
        index_db.add_chapter(chapter_num, chapter_data)
        print(f"\n🗄️ SQLite 索引已更新")
        
        # 使用追读力系统分析
        reader_pull = ReaderPullSystem(str(project_root))
        pull_result = reader_pull.analyze_chapter(chapter_num, content, title)
        
        print(f"\n📈 追读力分析完成")
        print(f"综合评分：{pull_result['score']}/10")
        print(f"  钩子数：{len(pull_result['hooks'])}")
        print(f"  爽点数：{len(pull_result['cool_points'])}")
        print(f"  债务数：{len(pull_result['debts'])}")
        print(f"  微兑现：{len(pull_result['micro_deliveries'])}")
        
    else:
        print(f"❌ 提交失败：{result.get('error')}")

def story_events(args):
    """事件审计（Phase 4）"""
    chapter_num = args.chapter
    
    # 查找项目根目录
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return
    
    # 使用 Story System
    story_system = StorySystem(str(project_root))
    result = story_system.story_events(chapter_num)
    
    if result["status"] == "completed":
        print(f"✅ 第{chapter_num}章事件审计完成")
        print(f"事件ID：{result['events']['id']}")
    else:
        print(f"❌ 事件审计失败：{result.get('error')}")

def get_task(args):
    """获取创作任务书"""
    chapter_num = args.chapter
    
    # 查找项目根目录
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return
    
    # 使用 Context Agent
    context_agent = ContextAgent(str(project_root))
    task = context_agent.generate_writing_task(chapter_num)
    
    print(f"📋 第{chapter_num}章创作任务书")
    print(f"任务ID：{task['id']}")
    print(f"\n📚 项目信息")
    print(f"书名：{task['project_name']}")
    print(f"题材：{task['genre']}")
    print(f"卷号：第{task['volume']['volume']}卷 - {task['volume']['title']}")
    
    print(f"\n📝 章节大纲")
    print(f"标题：{task['outline']['title']}")
    print(f"概述：{task['outline']['summary']}")
    
    print(f"\n⚙️ 约束条件")
    print(f"Strand 比例：Quest {task['constraints']['strand_ratio']['quest']*100:.0f}% | Fire {task['constraints']['strand_ratio']['fire']*100:.0f}% | Constellation {task['constraints']['strand_ratio']['constellation']*100:.0f}%")
    print(f"字数范围：{task['constraints']['word_count']['min']}-{task['constraints']['word_count']['max']}字")
    print(f"要求爽点：至少{task['constraints']['cool_points_min']}个")
    
    if task['writing_guide']['key_points']:
        print(f"\n💡 写作要点")
        for idx, point in enumerate(task['writing_guide']['key_points'], 1):
            print(f"  {idx}. {point}")
    
    if task['writing_guide']['avoid_points']:
        print(f"\n⚠️ 避免事项")
        for idx, point in enumerate(task['writing_guide']['avoid_points'], 1):
            print(f"  {idx}. {point}")

def backup_create(args):
    """创建备份"""
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return
    
    backup_manager = BackupManager(str(project_root))
    description = args.description or ""
    
    backup_path = backup_manager.create_backup(description)
    print(f"✅ 备份创建成功")
    print(f"备份位置：{backup_path}")

def backup_list(args):
    """列出备份"""
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return
    
    backup_manager = BackupManager(str(project_root))
    
    if args.type == "all":
        print("📦 所有备份：")
        print("\n--- 增量备份 ---")
        backups = backup_manager.list_backups()
        if backups:
            for backup in backups[:5]:
                print(f"  - {backup['name']} ({backup['timestamp'][:19]})")
        else:
            print("  暂无备份")
        
        print("\n--- 归档备份 ---")
        archives = backup_manager.list_archives()
        if archives:
            for archive in archives[:5]:
                size = archive.get('file_size', 0) / 1024 / 1024
                print(f"  - {archive['name']} ({archive['timestamp'][:19]}, {size:.2f} MB)")
        else:
            print("  暂无归档")
    
    elif args.type == "backup":
        print("📦 增量备份列表：")
        backups = backup_manager.list_backups()
        if backups:
            for backup in backups:
                print(f"  - {backup['name']}")
                print(f"    时间：{backup['timestamp']}")
                print(f"    描述：{backup.get('description', '无')}")
                print(f"    文件数：{backup.get('file_count', 0)}")
        else:
            print("  暂无增量备份")
    
    elif args.type == "archive":
        print("📦 归档列表：")
        archives = backup_manager.list_archives()
        if archives:
            for archive in archives:
                size = archive.get('file_size', 0) / 1024 / 1024
                print(f"  - {archive['name']}")
                print(f"    时间：{archive['timestamp']}")
                print(f"    大小：{size:.2f} MB")
                print(f"    描述：{archive.get('description', '无')}")
        else:
            print("  暂无归档")

def backup_restore(args):
    """恢复备份"""
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return
    
    backup_manager = BackupManager(str(project_root))
    
    if args.type == "backup":
        success = backup_manager.restore_backup(args.name)
    else:
        success = backup_manager.restore_archive(args.name)
    
    if success:
        print(f"✅ 恢复成功")
    else:
        print(f"❌ 恢复失败，备份不存在")

def backup_delete(args):
    """删除备份"""
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return
    
    backup_manager = BackupManager(str(project_root))
    
    if args.type == "backup":
        success = backup_manager.delete_backup(args.name)
    else:
        success = backup_manager.delete_archive(args.name)
    
    if success:
        print(f"✅ 删除成功")
    else:
        print(f"❌ 删除失败，备份不存在")

def backup_stats(args):
    """备份统计"""
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return
    
    backup_manager = BackupManager(str(project_root))
    stats = backup_manager.get_backup_stats()
    
    print("📊 备份统计")
    print(f"增量备份数：{stats['backup_count']}")
    print(f"归档数量：{stats['archive_count']}")
    print(f"备份总大小：{stats['total_backup_size'] / 1024 / 1024:.2f} MB")
    print(f"归档总大小：{stats['total_archive_size'] / 1024 / 1024:.2f} MB")
    print(f"自动备份：{'开启' if stats['auto_backup_enabled'] else '关闭'}")
    print(f"备份间隔：{stats['backup_interval_hours']} 小时")
    print(f"保留备份数：{stats['keep_backups']}")

def backup_archive(args):
    """创建归档"""
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return
    
    backup_manager = BackupManager(str(project_root))
    description = args.description or ""
    
    archive_path = backup_manager.create_archive(description)
    print(f"✅ 归档创建成功")
    print(f"归档位置：{archive_path}")

def db_stats(args):
    """数据库统计"""
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return
    
    db = IndexDatabase(str(project_root))
    stats = db.get_stats()
    db.close()
    
    print("🗄️ 数据库统计")
    print(f"实体数量：{stats['entities']}")
    print(f"关系数量：{stats['relationships']}")
    print(f"章节数量：{stats['chapters']}")
    print(f"记忆数量：{stats['memories']}")
    print(f"活跃钩子：{stats['active_hooks']}")
    print(f"活跃债务：{stats['active_debts']}")

def db_search_entity(args):
    """搜索实体"""
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return
    
    db = IndexDatabase(str(project_root))
    entities = db.search_entities(args.keyword, args.type)
    db.close()
    
    print(f"🔍 搜索结果（共 {len(entities)} 个）")
    for entity in entities:
        print(f"\n📌 {entity['name']} ({entity['type']})")
        if entity['description']:
            print(f"   描述：{entity['description']}")

def db_list_chapters(args):
    """列出章节索引"""
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return
    
    db = IndexDatabase(str(project_root))
    chapters = db.list_chapters()
    db.close()
    
    print("📚 章节列表")
    for chapter in chapters:
        print(f"第{chapter['chapter_number']}章: {chapter['title']} ({chapter['word_count']}字)")

def db_list_debts(args):
    """列出未解决的债务"""
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return
    
    db = IndexDatabase(str(project_root))
    debts = db.get_active_debts()
    db.close()
    
    print("💰 未解决的叙事债务")
    if not debts:
        print("  暂无未解决的债务")
        return
    
    for debt in debts:
        print(f"\n📋 [{debt['type']}] 第{debt['chapter_number']}章")
        print(f"   内容：{debt['content']}")

def reader_pull_analyze(args):
    """分析章节追读力"""
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return
    
    chapter_num = args.chapter
    
    # 读取章节内容
    chapter_dir = project_root / "章节"
    
    # 支持多种章节文件命名格式
    possible_formats = [
        f"Ch{chapter_num:03d}.md",
        f"第{chapter_num}章.md",
        f"第{chapter_num:03d}章.md",
        f"Chapter{chapter_num:03d}.md",
        f"{chapter_num:03d}.md"
    ]
    
    chapter_file = None
    for fmt in possible_formats:
        candidate = chapter_dir / fmt
        if candidate.exists():
            chapter_file = candidate
            break
    
    if not chapter_file:
        print(f"❌ 未找到第{chapter_num}章")
        print(f"   尝试的文件格式：{', '.join(possible_formats)}")
        return
    
    with open(chapter_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取标题
    lines = content.split('\n')
    title = lines[0].replace('#', '').strip() if lines else ""
    
    # 分析追读力
    reader_pull = ReaderPullSystem(str(project_root))
    result = reader_pull.analyze_chapter(chapter_num, content, title)
    
    print(f"📊 第{chapter_num}章追读力分析")
    print(f"标题：{title}")
    print(f"评分：{result['score']} 分")
    print(f"评级：{result['grade']}")
    
    print("\n📈 评分构成")
    breakdown = result["breakdown"]
    for key, value in breakdown.items():
        print(f"  {key}: {value['score']}/{value['max_score']} ({value['count']}个)")
    
    print("\n📋 追读力指标")
    metrics = result["reader_pull_metrics"]
    print(f"  钩子密度：{metrics['hook_density']} 个/千字")
    print(f"  爽点密度：{metrics['cool_point_density']} 个/千字")
    print(f"  债务密度：{metrics['debt_density']} 个/千字")
    print(f"  债务兑现率：{metrics['delivery_rate']}%")
    print(f"  钩爽比：{metrics['hook_to_cool_ratio']}")
    
    if result["hooks"]:
        print(f"\n🎣 识别到 {len(result['hooks'])} 个钩子")
        for hook in result["hooks"][:3]:
            print(f"  • [{hook['type']}] {hook['content']}")
    
    if result["cool_points"]:
        print(f"\n🔥 识别到 {len(result['cool_points'])} 个爽点")
        for cp in result["cool_points"][:3]:
            print(f"  • [{cp['type']}] {cp['content']}")
    
    if result["suggestions"]:
        print("\n💡 写作建议")
        for suggestion in result["suggestions"]:
            print(f"  {suggestion}")

def reader_pull_history(args):
    """查看追读力历史"""
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return
    
    reader_pull = ReaderPullSystem(str(project_root))
    history = reader_pull.get_score_history()
    
    print("📈 追读力历史记录")
    if not history:
        print("  暂无数据")
        return
    
    for record in history[-10:]:
        print(f"  第{record['chapter']}章: {record['score']}分 (钩子:{record['hook_count']}, 爽点:{record['cool_point_count']})")
    
    trend = reader_pull.get_trend_analysis()
    print(f"\n📊 趋势分析")
    print(f"  {trend['trend_message']}")
    print(f"  最近平均: {trend['recent_average']}分")
    print(f"  总章节数: {trend['total_chapters']}")

def reader_pull_debts(args):
    """查看追读力债务状态"""
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return
    
    reader_pull = ReaderPullSystem(str(project_root))
    status = reader_pull.get_debt_status()
    
    print("💰 叙事债务状态")
    print(f"  总债务: {status['total']}")
    print(f"  活跃: {status['active']}")
    print(f"  已解决: {status['resolved']}")
    print(f"  解决率: {status['resolution_rate']}%")
    
    if status["debt_list"]:
        print("\n  活跃债务列表:")
        for debt in status["debt_list"]:
            print(f"    • [{debt['type']}] 第{debt['chapter']}章: {debt['content']}")

def memory_show(args):
    """显示记忆摘要"""
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return
    
    memory_file = project_root / ".webnovel" / "memory_scratchpad.json"
    if not memory_file.exists():
        print("❌ 未找到记忆文件，请先运行 commit 命令")
        return
    
    with open(memory_file, "r", encoding="utf-8") as f:
        memory = json.load(f)
    
    print("🧠 长期记忆摘要")
    print(f"  角色数量: {len(memory.get('characters', {}))}")
    print(f"  事件数量: {len(memory.get('events', []))}")
    print(f"  钩子数量: {len(memory.get('hooks', []))}")
    print(f"  伏笔数量: {len(memory.get('foreshadowings', []))}")
    print(f"  爽点数量: {len(memory.get('cool_points', []))}")
    print(f"  最后更新: {memory.get('last_updated', '未知')}")

def memory_characters(args):
    """显示角色记忆"""
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return
    
    memory_file = project_root / ".webnovel" / "memory_scratchpad.json"
    if not memory_file.exists():
        print("❌ 未找到记忆文件")
        return
    
    with open(memory_file, "r", encoding="utf-8") as f:
        memory = json.load(f)
    
    characters = memory.get("characters", {})
    if not characters:
        print("📝 暂无角色记忆")
        return
    
    print(f"👥 角色记忆 ({len(characters)} 个角色)")
    for char_name, char_info in characters.items():
        first = char_info.get("first_appearance", "?")
        last = char_info.get("last_appearance", "?")
        appearances = len(char_info.get("appearances", []))
        print(f"  • {char_name}")
        print(f"    出场: 第{first}章 → 第{last}章 (共{appearances}次)")

def memory_events(args):
    """显示事件记忆"""
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return
    
    memory_file = project_root / ".webnovel" / "memory_scratchpad.json"
    if not memory_file.exists():
        print("❌ 未找到记忆文件")
        return
    
    with open(memory_file, "r", encoding="utf-8") as f:
        memory = json.load(f)
    
    events = memory.get("events", [])
    if not events:
        print("📝 暂无事件记忆")
        return
    
    print(f"📜 事件记忆 ({len(events)} 条)")
    for event in events[-20:]:
        chapter = event.get("chapter", "?")
        event_type = event.get("event_type", "unknown")
        content = event.get("content", "")[:50]
        importance = event.get("importance", "normal")
        print(f"  • [第{chapter}章|{event_type}|{importance}] {content}...")

def memory_hooks(args):
    """显示钩子记忆"""
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return
    
    memory_file = project_root / ".webnovel" / "memory_scratchpad.json"
    if not memory_file.exists():
        print("❌ 未找到记忆文件")
        return
    
    with open(memory_file, "r", encoding="utf-8") as f:
        memory = json.load(f)
    
    hooks = memory.get("hooks", [])
    foreshadowings = memory.get("foreshadowings", [])
    
    print("🪝 钩子与伏笔")
    if hooks:
        print(f"\n  活跃钩子 ({len(hooks)} 个):")
        for hook in hooks:
            print(f"    • {hook.get('content', '')[:50]}...")
    else:
        print("\n  暂无钩子记录")
    
    if foreshadowings:
        print(f"\n  伏笔 ({len(foreshadowings)} 个):")
        for fs in foreshadowings:
            print(f"    • {fs.get('content', '')[:50]}...")
    else:
        print("\n  暂无伏笔记录")

def memory_update(args):
    """更新记忆"""
    from agents.data_agent import DataAgent
    
    project_root = find_project_root()
    if not project_root:
        print("❌ 未找到项目")
        return
    
    chapter_num = args.chapter
    print(f"📝 正在更新第 {chapter_num} 章的记忆...")
    
    data_agent = DataAgent(str(project_root))
    data_agent.update_memory(chapter_num)
    
    print(f"✅ 第 {chapter_num} 章记忆已更新")

def main():
    parser = argparse.ArgumentParser(description="Webnovel Writer CLI - 长篇网文创作系统")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # init 命令
    init_parser = subparsers.add_parser("init", help="初始化小说项目")
    init_parser.add_argument("--name", "-n", help="书名")
    init_parser.add_argument("--genre", "-g", help="题材")
    init_parser.add_argument("--character", "-c", help="主角名字")
    init_parser.add_argument("--finger", "-f", help="金手指类型")
    
    # status 命令
    status_parser = subparsers.add_parser("status", help="项目状态概览")

    # preflight 命令
    preflight_parser = subparsers.add_parser("preflight", help="健康检查（Phase 5）")
    preflight_parser.add_argument("--format", "-f", choices=["text", "json"], default="text", help="输出格式")

    # plan 命令
    plan_parser = subparsers.add_parser("plan", help="规划卷级大纲")
    plan_parser.add_argument("volume", type=int, help="卷号")
    plan_parser.add_argument("--end", "-e", type=int, help="结束卷号")
    
    # write 命令
    write_parser = subparsers.add_parser("write", help="写作章节")
    write_parser.add_argument("chapter", type=int, help="章节号")
    
    # review 命令
    review_parser = subparsers.add_parser("review", help="审查章节")
    review_parser.add_argument("start", type=int, help="起始章节")
    review_parser.add_argument("--end", "-e", type=int, help="结束章节")
    
    # query 命令
    query_parser = subparsers.add_parser("query", help="查询信息")
    query_parser.add_argument("keyword", help="查询关键词（状态/设定/大纲/卷/健康/记忆）")
    
    # commit 命令（新增）
    commit_parser = subparsers.add_parser("commit", help="提交章节（Phase 3）")
    commit_parser.add_argument("chapter", type=int, help="章节号")
    
    # events 命令（新增）
    events_parser = subparsers.add_parser("events", help="事件审计（Phase 4）")
    events_parser.add_argument("chapter", type=int, help="章节号")
    
    # task 命令（新增）
    task_parser = subparsers.add_parser("task", help="获取创作任务书")
    task_parser.add_argument("chapter", type=int, help="章节号")

    # dashboard 命令
    dashboard_parser = subparsers.add_parser("dashboard", help="启动可视化面板")
    dashboard_parser.add_argument("--host", default="127.0.0.1", help="监听主机")
    dashboard_parser.add_argument("--port", type=int, default=5000, help="监听端口")

    # deconstruct 命令
    deconstruct_parser = subparsers.add_parser("deconstruct", help="拆解参考作品")
    deconstruct_parser.add_argument("file", help="参考作品文件路径")
    deconstruct_parser.add_argument("--chapter", "-c", type=int, help="分析指定章节号")
    deconstruct_parser.add_argument("--output", "-o", help="输出报告文件路径")
    deconstruct_parser.add_argument("--format", "-f", choices=["text", "json"], default="text", help="输出格式")

    # learn 命令
    learn_parser = subparsers.add_parser("learn", help="学习参考作品")
    learn_parser.add_argument("--source", "-s", required=True, help="学习源文件或目录")
    learn_parser.add_argument("--type", "-t", choices=["style", "plot", "setting", "all"], default="all", help="学习类型")
    learn_parser.add_argument("--output", "-o", help="输出报告文件路径")

    # import 命令
    import_parser = subparsers.add_parser("import", help="导入数据")
    import_parser.add_argument("file", help="导入文件路径")
    import_parser.add_argument("--type", "-t", choices=["chapter", "setting", "memory", "all"], default="all", help="导入类型")

    # export 命令
    export_parser = subparsers.add_parser("export", help="导出数据")
    export_parser.add_argument("--type", "-t", choices=["chapter", "setting", "memory", "all"], default="all", help="导出类型")
    export_parser.add_argument("--output", "-o", required=True, help="输出文件路径")

    # backup 命令组
    backup_parser = subparsers.add_parser("backup", help="备份管理")
    backup_subparsers = backup_parser.add_subparsers(dest="backup_command", help="备份子命令")
    
    # backup create
    backup_create_parser = backup_subparsers.add_parser("create", help="创建增量备份")
    backup_create_parser.add_argument("--description", "-d", help="备份描述")
    
    # backup list
    backup_list_parser = backup_subparsers.add_parser("list", help="列出备份")
    backup_list_parser.add_argument("type", nargs="?", default="all", choices=["all", "backup", "archive"], help="备份类型")
    
    # backup restore
    backup_restore_parser = backup_subparsers.add_parser("restore", help="恢复备份")
    backup_restore_parser.add_argument("type", choices=["backup", "archive"], help="备份类型")
    backup_restore_parser.add_argument("name", help="备份名称")
    
    # backup delete
    backup_delete_parser = backup_subparsers.add_parser("delete", help="删除备份")
    backup_delete_parser.add_argument("type", choices=["backup", "archive"], help="备份类型")
    backup_delete_parser.add_argument("name", help="备份名称")
    
    # backup stats
    backup_stats_parser = backup_subparsers.add_parser("stats", help="备份统计")
    
    # backup archive
    backup_archive_parser = backup_subparsers.add_parser("archive", help="创建归档")
    backup_archive_parser.add_argument("--description", "-d", help="归档描述")
    
    # db 命令组
    db_parser = subparsers.add_parser("db", help="数据库管理")
    db_subparsers = db_parser.add_subparsers(dest="db_command", help="数据库子命令")
    
    # db stats
    db_stats_parser = db_subparsers.add_parser("stats", help="数据库统计")
    
    # db search
    db_search_parser = db_subparsers.add_parser("search", help="搜索实体")
    db_search_parser.add_argument("keyword", help="搜索关键词")
    db_search_parser.add_argument("--type", "-t", help="实体类型过滤")
    
    # db chapters
    db_chapters_parser = db_subparsers.add_parser("chapters", help="列出章节索引")
    
    # db debts
    db_debts_parser = db_subparsers.add_parser("debts", help="列出未解决债务")
    
    # reader-pull 命令组
    rp_parser = subparsers.add_parser("reader-pull", help="追读力分析")
    rp_subparsers = rp_parser.add_subparsers(dest="rp_command", help="追读力子命令")
    
    # reader-pull analyze
    rp_analyze_parser = rp_subparsers.add_parser("analyze", help="分析章节追读力")
    rp_analyze_parser.add_argument("chapter", type=int, help="章节号")
    
    # reader-pull history
    rp_history_parser = rp_subparsers.add_parser("history", help="查看追读力历史")
    
    # reader-pull debts
    rp_debts_parser = rp_subparsers.add_parser("debts", help="查看债务状态")
    
    # memory 命令组
    memory_parser = subparsers.add_parser("memory", help="长期记忆管理")
    memory_subparsers = memory_parser.add_subparsers(dest="memory_command", help="记忆子命令")
    
    # memory show
    memory_show_parser = memory_subparsers.add_parser("show", help="显示记忆摘要")
    
    # memory characters
    memory_chars_parser = memory_subparsers.add_parser("characters", help="显示角色记忆")
    
    # memory events
    memory_events_parser = memory_subparsers.add_parser("events", help="显示事件记忆")
    
    # memory hooks
    memory_hooks_parser = memory_subparsers.add_parser("hooks", help="显示钩子记忆")
    
    # memory update
    memory_update_parser = memory_subparsers.add_parser("update", help="更新记忆")
    memory_update_parser.add_argument("chapter", type=int, help="章节号")
    
    args = parser.parse_args()
    
    if args.command == "init":
        init_project(args)
    elif args.command == "status":
        project_status(args)
    elif args.command == "preflight":
        preflight_check(args)
    elif args.command == "plan":
        plan_volume(args)
    elif args.command == "write":
        write_chapter(args)
    elif args.command == "review":
        review_chapter(args)
    elif args.command == "query":
        query_info(args)
    elif args.command == "commit":
        commit_chapter(args)
    elif args.command == "events":
        story_events(args)
    elif args.command == "task":
        get_task(args)
    elif args.command == "dashboard":
        run_dashboard(args)
    elif args.command == "deconstruct":
        deconstruct_reference(args)
    elif args.command == "learn":
        learn_from_reference(args)
    elif args.command == "import":
        import_data(args)
    elif args.command == "export":
        export_data(args)
    elif args.command == "backup":
        if args.backup_command == "create":
            backup_create(args)
        elif args.backup_command == "list":
            backup_list(args)
        elif args.backup_command == "restore":
            backup_restore(args)
        elif args.backup_command == "delete":
            backup_delete(args)
        elif args.backup_command == "stats":
            backup_stats(args)
        elif args.backup_command == "archive":
            backup_archive(args)
        else:
            backup_parser.print_help()
    elif args.command == "db":
        if args.db_command == "stats":
            db_stats(args)
        elif args.db_command == "search":
            db_search_entity(args)
        elif args.db_command == "chapters":
            db_list_chapters(args)
        elif args.db_command == "debts":
            db_list_debts(args)
        else:
            db_parser.print_help()
    elif args.command == "reader-pull":
        if args.rp_command == "analyze":
            reader_pull_analyze(args)
        elif args.rp_command == "history":
            reader_pull_history(args)
        elif args.rp_command == "debts":
            reader_pull_debts(args)
        else:
            rp_parser.print_help()
    elif args.command == "memory":
        if args.memory_command == "show":
            memory_show(args)
        elif args.memory_command == "characters":
            memory_characters(args)
        elif args.memory_command == "events":
            memory_events(args)
        elif args.memory_command == "hooks":
            memory_hooks(args)
        elif args.memory_command == "update":
            memory_update(args)
        else:
            memory_parser.print_help()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()