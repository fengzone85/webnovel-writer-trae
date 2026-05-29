#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utils - 工具函数模块
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

def setup_logging(name: str = "replicator") -> logging.Logger:
    """设置日志系统"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 创建文件处理器
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_dir / f"{name}.log", encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def get_project_info(path: Path) -> Dict[str, Any]:
    """获取项目信息"""
    info = {
        'path': str(path),
        'name': path.name,
        'type': 'unknown',
        'has_package_json': False,
        'has_requirements_txt': False,
        'has_git': False,
        'file_count': 0,
        'dir_count': 0,
        'size_bytes': 0
    }
    
    try:
        # 检查文件和目录数量
        files = []
        dirs = []
        
        for item in path.rglob('*'):
            if item.is_file():
                files.append(item)
                info['size_bytes'] += item.stat().st_size
            elif item.is_dir():
                dirs.append(item)
        
        info['file_count'] = len(files)
        info['dir_count'] = len(dirs)
        
        # 检查 package.json
        if (path / 'package.json').exists():
            info['has_package_json'] = True
            info['type'] = 'nodejs'
            
            with open(path / 'package.json', 'r', encoding='utf-8') as f:
                pkg = json.load(f)
                info['package_name'] = pkg.get('name', '')
                info['package_version'] = pkg.get('version', '')
        
        # 检查 requirements.txt
        if (path / 'requirements.txt').exists():
            info['has_requirements_txt'] = True
            if info['type'] == 'nodejs':
                info['type'] = 'hybrid'
            else:
                info['type'] = 'python'
        
        # 检查 .git
        if (path / '.git').exists():
            info['has_git'] = True
        
        # 检查 .trae
        if (path / '.trae').exists():
            info['has_trae'] = True
        
        # 检查 .story-system
        if (path / '.story-system').exists():
            info['is_webnovel_project'] = True
        
    except Exception as e:
        info['error'] = str(e)
    
    return info

def format_size(bytes_size: int) -> str:
    """格式化文件大小"""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.2f} KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.2f} MB"
    else:
        return f"{bytes_size / (1024 * 1024 * 1024):.2f} GB"

def validate_path(path_str: str) -> bool:
    """验证路径是否有效"""
    try:
        path = Path(path_str)
        return path.exists()
    except Exception:
        return False

def generate_replication_id() -> str:
    """生成唯一复制ID"""
    import hashlib
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    hash_val = hashlib.md5(timestamp.encode()).hexdigest()[:8]
    return f"repl_{timestamp}_{hash_val}"

def load_config(config_path: str) -> Dict[str, Any]:
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return {}

def save_config(config: Dict[str, Any], config_path: str):
    """保存配置文件"""
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存配置文件失败: {e}")

def create_directory(path: str):
    """创建目录"""
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"创建目录失败: {e}")