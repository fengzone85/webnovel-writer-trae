#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Webnovel Writer Dashboard Server
Flask 后端 API 服务
"""

import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, render_template, request

app = Flask(__name__, template_folder='templates', static_folder='static')

def find_project_root():
    """查找项目根目录"""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".story-system").exists():
            return current
        current = current.parent
    return Path.cwd()

def get_project_path():
    """获取项目路径"""
    if hasattr(app, 'project_path'):
        return Path(app.project_path)
    return find_project_root()

def load_state():
    """加载项目状态"""
    state_file = get_project_path() / ".webnovel" / "state.json"
    if state_file.exists():
        with open(state_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"current_chapter": 0, "total_chapters": 0}

def load_master_setting():
    """加载主设定"""
    setting_file = get_project_path() / ".story-system" / "MASTER_SETTING.json"
    if setting_file.exists():
        with open(setting_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def load_memory():
    """加载长期记忆"""
    memory_file = get_project_path() / ".webnovel" / "memory_scratchpad.json"
    if memory_file.exists():
        with open(memory_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"characters": {}, "events": [], "hooks": [], "foreshadowings": [], "cool_points": []}

def get_chapters():
    """获取章节列表"""
    chapters_dir = get_project_path() / "章节"
    if not chapters_dir.exists():
        return []
    chapters = []
    for f in sorted(chapters_dir.glob("Ch*.md")):
        chapters.append({
            "name": f.name,
            "path": str(f),
            "size": f.stat().st_size,
            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
        })
    return chapters

def get_commit_history():
    """获取提交历史"""
    commits_dir = get_project_path() / ".story-system" / "commits"
    if not commits_dir.exists():
        return []
    commits = []
    for f in sorted(commits_dir.glob("*.commit.json"), reverse=True)[:20]:
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
                commits.append(data)
        except:
            pass
    return commits

def get_review_stats():
    """获取审查统计"""
    reviews_dir = get_project_path() / ".story-system" / "reviews"
    if not reviews_dir.exists():
        return {"total": 0, "passed": 0, "failed": 0}
    reviews = list(reviews_dir.glob("*.json"))
    return {"total": len(reviews), "passed": len([r for r in reviews if "contract" in r.name])}

def query_index_db(query, top_k=10):
    """查询索引数据库"""
    db_path = get_project_path() / ".webnovel" / "index.db"
    if not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(query, (top_k,))
        results = cursor.fetchall()
        conn.close()
        return results
    except:
        return []

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/stats/overview')
def stats_overview():
    """项目状态概览"""
    state = load_state()
    setting = load_master_setting()
    memory = load_memory()
    chapters = get_chapters()

    return jsonify({
        "project_name": setting.get("project_name", "未命名项目"),
        "genre": setting.get("genre", "未知题材"),
        "main_character": setting.get("main_character", ""),
        "golden_finger": setting.get("golden_finger", ""),
        "current_chapter": state.get("current_chapter", 0),
        "total_chapters": len(chapters),
        "characters_count": len(memory.get("characters", {})),
        "events_count": len(memory.get("events", [])),
        "hooks_count": len(memory.get("hooks", [])),
        "foreshadowings_count": len(memory.get("foreshadowings", [])),
        "cool_points_count": len(memory.get("cool_points", [])),
        "strand_config": setting.get("strand_config", {}),
        "last_updated": state.get("last_updated", "")
    })

@app.route('/api/stats/chapter-trend')
def chapter_trend():
    """章节趋势"""
    chapters = get_chapters()
    trend = []
    for i, ch in enumerate(chapters):
        trend.append({
            "chapter": i + 1,
            "name": ch["name"],
            "word_count": ch["size"] // 2
        })
    return jsonify({"trend": trend})

@app.route('/api/commits')
def commits():
    """提交历史"""
    commit_list = get_commit_history()
    return jsonify({"commits": commit_list})

@app.route('/api/contracts/summary')
def contracts_summary():
    """合同树概览"""
    story_system_path = get_project_path() / ".story-system"

    summary = {
        "volumes": [],
        "chapters": [],
        "events": [],
        "reviews": []
    }

    volumes_dir = story_system_path / "volumes"
    if volumes_dir.exists():
        for f in sorted(volumes_dir.glob("volume_*.json")):
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                    summary["volumes"].append({
                        "name": f.name,
                        "volume": data.get("volume"),
                        "chapters_count": len(data.get("chapters", []))
                    })
            except:
                pass

    chapters_dir = story_system_path / "chapters"
    if chapters_dir.exists():
        summary["chapters"] = [f.name for f in sorted(chapters_dir.glob("*.json"))]

    events_dir = story_system_path / "events"
    if events_dir.exists():
        summary["events"] = [f.name for f in sorted(events_dir.glob("*.events.json"))]

    reviews_dir = story_system_path / "reviews"
    if reviews_dir.exists():
        summary["reviews"] = [f.name for f in sorted(reviews_dir.glob("*.json"))]

    return jsonify(summary)

@app.route('/api/env-status')
def env_status():
    """环境状态"""
    project_path = get_project_path()
    env_file = project_path / ".env"

    env_status = {
        "project_path": str(project_path),
        "env_exists": env_file.exists(),
        "directories": {
            "设定集": (project_path / "设定集").exists(),
            "大纲": (project_path / "大纲").exists(),
            "章节": (project_path / "章节").exists(),
            ".story-system": (project_path / ".story-system").exists(),
            ".webnovel": (project_path / ".webnovel").exists()
        },
        "key_files": {
            "state.json": (project_path / ".webnovel" / "state.json").exists(),
            "memory_scratchpad.json": (project_path / ".webnovel" / "memory_scratchpad.json").exists(),
            "index.db": (project_path / ".webnovel" / "index.db").exists(),
            "MASTER_SETTING.json": (project_path / ".story-system" / "MASTER_SETTING.json").exists()
        },
        "chapter_count": len(get_chapters()),
        "timestamp": datetime.now().isoformat()
    }

    return jsonify(env_status)

@app.route('/api/memory')
def memory():
    """记忆数据"""
    memory = load_memory()
    return jsonify(memory)

@app.route('/api/reader-pull')
def reader_pull():
    """追读力数据"""
    memory = load_memory()

    hooks = memory.get("hooks", [])
    cool_points = memory.get("cool_points", [])

    return jsonify({
        "hooks": hooks,
        "cool_points": cool_points,
        "summary": {
            "total_hooks": len(hooks),
            "total_cool_points": len(cool_points)
        }
    })

@app.route('/api/health')
def health():
    """健康检查"""
    project_path = get_project_path()
    issues = []

    if not (project_path / ".story-system").exists():
        issues.append("缺少 .story-system 目录")

    if not (project_path / ".webnovel").exists():
        issues.append("缺少 .webnovel 目录")

    state = load_state()
    if state.get("current_chapter", 0) == 0:
        issues.append("尚未提交任何章节")

    status = "healthy" if not issues else "warning"

    return jsonify({
        "status": status,
        "issues": issues,
        "timestamp": datetime.now().isoformat()
    })

def create_app(project_path=None):
    """创建 Flask 应用"""
    global app
    if project_path:
        app.project_path = project_path
    return app

def run_server(host='127.0.0.1', port=5000, project_path=None):
    """运行服务器"""
    if project_path:
        app.project_path = project_path
    app.run(host=host, port=port, debug=True)

if __name__ == '__main__':
    run_server()
