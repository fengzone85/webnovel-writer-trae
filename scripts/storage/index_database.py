#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite索引数据库模块
存储实体、关系、章节数据，支持高效查询
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

class IndexDatabase:
    """SQLite索引数据库"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.db_path = self.project_path / ".webnovel" / "index.db"
        
        # 确保目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = self._connect()
        self._create_tables()
    
    def _connect(self) -> sqlite3.Connection:
        """连接数据库"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def _create_tables(self):
        """创建表结构"""
        cursor = self.conn.cursor()
        
        # entities 表 - 存储实体信息
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                description TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(name, type)
            )
        ''')
        
        # relationships 表 - 存储实体关系
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_entity_id INTEGER NOT NULL,
                target_entity_id INTEGER NOT NULL,
                relationship_type TEXT NOT NULL,
                description TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(source_entity_id) REFERENCES entities(id),
                FOREIGN KEY(target_entity_id) REFERENCES entities(id)
            )
        ''')
        
        # chapters 表 - 章节索引
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter_number INTEGER NOT NULL UNIQUE,
                title TEXT,
                content TEXT,
                word_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'draft',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                summary TEXT,
                entities TEXT,
                events TEXT
            )
        ''')
        
        # memory 表 - 长期记忆
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                value TEXT NOT NULL,
                category TEXT,
                priority INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                accessed_at TEXT
            )
        ''')
        
        # hooks 表 - 追读力钩子记录
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter_number INTEGER NOT NULL,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                position INTEGER,
                strength INTEGER DEFAULT 0,
                resolved BOOLEAN DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY(chapter_number) REFERENCES chapters(chapter_number)
            )
        ''')
        
        # cool_points 表 - 爽点记录
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cool_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter_number INTEGER NOT NULL,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                intensity INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY(chapter_number) REFERENCES chapters(chapter_number)
            )
        ''')
        
        # debts 表 - 债务追踪
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS debts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter_number INTEGER NOT NULL,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TEXT NOT NULL,
                resolved_at TEXT,
                FOREIGN KEY(chapter_number) REFERENCES chapters(chapter_number)
            )
        ''')
        
        # 索引（使用 IF NOT EXISTS 避免重复创建错误）
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type)')
        except:
            pass
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chapters_number ON chapters(chapter_number)')
        except:
            pass
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_hooks_chapter ON hooks(chapter_number)')
        except:
            pass
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_memory_category ON memory(category)')
        except:
            pass
        
        self.conn.commit()
    
    def add_entity(self, name: str, type: str, description: str = "", metadata: Dict = None) -> int:
        """添加实体"""
        timestamp = datetime.now().isoformat()
        metadata_str = json.dumps(metadata or {}, ensure_ascii=False)
        
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO entities (name, type, description, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, type, description, metadata_str, timestamp, timestamp))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # 实体已存在，更新
            cursor.execute('''
                UPDATE entities SET description = ?, metadata = ?, updated_at = ?
                WHERE name = ? AND type = ?
            ''', (description, metadata_str, timestamp, name, type))
            self.conn.commit()
            return self.get_entity_id(name, type)
    
    def get_entity_id(self, name: str, type: str) -> Optional[int]:
        """获取实体ID"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM entities WHERE name = ? AND type = ?', (name, type))
        row = cursor.fetchone()
        return row['id'] if row else None
    
    def get_entity(self, entity_id: int) -> Optional[Dict]:
        """获取实体信息"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM entities WHERE id = ?', (entity_id,))
        row = cursor.fetchone()
        if row:
            return {
                'id': row['id'],
                'name': row['name'],
                'type': row['type'],
                'description': row['description'],
                'metadata': json.loads(row['metadata']),
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
        return None
    
    def search_entities(self, keyword: str = None, type_filter: str = None) -> List[Dict]:
        """搜索实体"""
        cursor = self.conn.cursor()
        query = 'SELECT * FROM entities WHERE 1=1'
        params = []
        
        if keyword:
            query += ' AND (name LIKE ? OR description LIKE ?)'
            params.extend([f'%{keyword}%', f'%{keyword}%'])
        
        if type_filter:
            query += ' AND type = ?'
            params.append(type_filter)
        
        cursor.execute(query, params)
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row['id'],
                'name': row['name'],
                'type': row['type'],
                'description': row['description'],
                'metadata': json.loads(row['metadata']),
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        return results
    
    def add_relationship(self, source_id: int, target_id: int, relationship_type: str, description: str = "", metadata: Dict = None):
        """添加关系"""
        timestamp = datetime.now().isoformat()
        metadata_str = json.dumps(metadata or {}, ensure_ascii=False)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO relationships (source_entity_id, target_entity_id, relationship_type, description, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (source_id, target_id, relationship_type, description, metadata_str, timestamp))
        self.conn.commit()
    
    def get_relationships(self, entity_id: int) -> List[Dict]:
        """获取实体的所有关系"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT r.*, e1.name as source_name, e2.name as target_name
            FROM relationships r
            JOIN entities e1 ON r.source_entity_id = e1.id
            JOIN entities e2 ON r.target_entity_id = e2.id
            WHERE r.source_entity_id = ? OR r.target_entity_id = ?
        ''', (entity_id, entity_id))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row['id'],
                'source_id': row['source_entity_id'],
                'source_name': row['source_name'],
                'target_id': row['target_entity_id'],
                'target_name': row['target_name'],
                'relationship_type': row['relationship_type'],
                'description': row['description'],
                'metadata': json.loads(row['metadata']),
                'created_at': row['created_at']
            })
        return results
    
    def add_chapter(self, chapter_number: int, title: str = "", content: str = "", summary: str = "", entities: List = None, events: List = None):
        """添加章节索引"""
        timestamp = datetime.now().isoformat()
        word_count = len(content.replace('\n', '').replace('\r', '')) if content else 0
        entities_str = json.dumps(entities or [], ensure_ascii=False)
        events_str = json.dumps(events or [], ensure_ascii=False)
        
        cursor = self.conn.cursor()
        
        # 检查是否已存在
        cursor.execute('SELECT id FROM chapters WHERE chapter_number = ?', (chapter_number,))
        if cursor.fetchone():
            # 更新
            cursor.execute('''
                UPDATE chapters SET title = ?, content = ?, word_count = ?, summary = ?, 
                entities = ?, events = ?, updated_at = ?
                WHERE chapter_number = ?
            ''', (title, content, word_count, summary, entities_str, events_str, timestamp, chapter_number))
        else:
            # 插入
            cursor.execute('''
                INSERT INTO chapters (chapter_number, title, content, word_count, summary, 
                entities, events, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (chapter_number, title, content, word_count, summary, entities_str, events_str, timestamp, timestamp))
        
        self.conn.commit()
    
    def get_chapter(self, chapter_number: int) -> Optional[Dict]:
        """获取章节信息"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM chapters WHERE chapter_number = ?', (chapter_number,))
        row = cursor.fetchone()
        if row:
            return {
                'id': row['id'],
                'chapter_number': row['chapter_number'],
                'title': row['title'],
                'content': row['content'],
                'word_count': row['word_count'],
                'status': row['status'],
                'summary': row['summary'],
                'entities': json.loads(row['entities']),
                'events': json.loads(row['events']),
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
        return None
    
    def list_chapters(self) -> List[Dict]:
        """列出所有章节"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM chapters ORDER BY chapter_number')
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'chapter_number': row['chapter_number'],
                'title': row['title'],
                'word_count': row['word_count'],
                'status': row['status'],
                'created_at': row['created_at']
            })
        return results
    
    def add_memory(self, key: str, value: Any, category: str = "", priority: int = 0):
        """添加记忆"""
        timestamp = datetime.now().isoformat()
        value_str = json.dumps(value, ensure_ascii=False)
        
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO memory (key, value, category, priority, created_at, accessed_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (key, value_str, category, priority, timestamp, timestamp))
        except sqlite3.IntegrityError:
            # 更新已有记忆
            cursor.execute('''
                UPDATE memory SET value = ?, category = ?, priority = ?, accessed_at = ?
                WHERE key = ?
            ''', (value_str, category, priority, timestamp, key))
        self.conn.commit()
    
    def get_memory(self, key: str) -> Optional[Any]:
        """获取记忆"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT value FROM memory WHERE key = ?', (key,))
        row = cursor.fetchone()
        if row:
            # 更新访问时间
            cursor.execute('UPDATE memory SET accessed_at = ? WHERE key = ?', (datetime.now().isoformat(), key))
            self.conn.commit()
            return json.loads(row['value'])
        return None
    
    def search_memory(self, keyword: str = None, category: str = None) -> List[Dict]:
        """搜索记忆"""
        cursor = self.conn.cursor()
        query = 'SELECT * FROM memory WHERE 1=1'
        params = []
        
        if keyword:
            query += ' AND (key LIKE ? OR value LIKE ?)'
            params.extend([f'%{keyword}%', f'%{keyword}%'])
        
        if category:
            query += ' AND category = ?'
            params.append(category)
        
        query += ' ORDER BY priority DESC, accessed_at DESC'
        cursor.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'key': row['key'],
                'value': json.loads(row['value']),
                'category': row['category'],
                'priority': row['priority'],
                'created_at': row['created_at'],
                'accessed_at': row['accessed_at']
            })
        return results
    
    def add_hook(self, chapter_number: int, hook_type: str, content: str, position: int = 0, strength: int = 0):
        """添加钩子"""
        timestamp = datetime.now().isoformat()
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO hooks (chapter_number, type, content, position, strength, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (chapter_number, hook_type, content, position, strength, timestamp))
        self.conn.commit()
    
    def resolve_hook(self, hook_id: int):
        """标记钩子已解决"""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE hooks SET resolved = 1 WHERE id = ?', (hook_id,))
        self.conn.commit()
    
    def get_chapter_hooks(self, chapter_number: int) -> List[Dict]:
        """获取章节钩子"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM hooks WHERE chapter_number = ? ORDER BY position', (chapter_number,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row['id'],
                'type': row['type'],
                'content': row['content'],
                'position': row['position'],
                'strength': row['strength'],
                'resolved': bool(row['resolved']),
                'created_at': row['created_at']
            })
        return results
    
    def add_cool_point(self, chapter_number: int, point_type: str, content: str, intensity: int = 0):
        """添加爽点"""
        timestamp = datetime.now().isoformat()
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO cool_points (chapter_number, type, content, intensity, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (chapter_number, point_type, content, intensity, timestamp))
        self.conn.commit()
    
    def get_chapter_cool_points(self, chapter_number: int) -> List[Dict]:
        """获取章节爽点"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM cool_points WHERE chapter_number = ?', (chapter_number,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row['id'],
                'type': row['type'],
                'content': row['content'],
                'intensity': row['intensity'],
                'created_at': row['created_at']
            })
        return results
    
    def add_debt(self, chapter_number: int, debt_type: str, content: str):
        """添加债务"""
        timestamp = datetime.now().isoformat()
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO debts (chapter_number, type, content, status, created_at)
            VALUES (?, ?, ?, 'active', ?)
        ''', (chapter_number, debt_type, content, timestamp))
        self.conn.commit()
    
    def resolve_debt(self, debt_id: int):
        """标记债务已解决"""
        timestamp = datetime.now().isoformat()
        cursor = self.conn.cursor()
        cursor.execute('UPDATE debts SET status = ?, resolved_at = ? WHERE id = ?', ('resolved', timestamp, debt_id))
        self.conn.commit()
    
    def get_active_debts(self) -> List[Dict]:
        """获取未解决的债务"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT d.*, c.title as chapter_title
            FROM debts d
            LEFT JOIN chapters c ON d.chapter_number = c.chapter_number
            WHERE d.status = 'active'
            ORDER BY d.created_at
        ''')
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row['id'],
                'chapter_number': row['chapter_number'],
                'chapter_title': row['chapter_title'],
                'type': row['type'],
                'content': row['content'],
                'status': row['status'],
                'created_at': row['created_at']
            })
        return results
    
    def get_stats(self) -> Dict[str, int]:
        """获取数据库统计信息"""
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM entities')
        entity_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM relationships')
        relationship_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM chapters')
        chapter_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM memory')
        memory_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM hooks WHERE resolved = 0')
        active_hook_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM debts WHERE status = "active"')
        active_debt_count = cursor.fetchone()[0]
        
        return {
            'entities': entity_count,
            'relationships': relationship_count,
            'chapters': chapter_count,
            'memories': memory_count,
            'active_hooks': active_hook_count,
            'active_debts': active_debt_count
        }
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()