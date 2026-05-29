#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChromaDB 向量存储后端（可选）
需要安装: pip install chromadb
"""

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from typing import Dict, Any, List, Optional
from pathlib import Path

class ChromaVectorStore:
    """ChromaDB 向量存储后端"""

    def __init__(self, project_path: str, collection_name: str = "webnovel"):
        if not CHROMADB_AVAILABLE:
            raise ImportError(
                "ChromaDB is not installed. "
                "Please install it with: pip install chromadb"
            )

        self.project_path = Path(project_path).resolve()
        self.persist_dir = self.project_path / ".chromadb"
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False)
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"project": str(self.project_path)}
        )

    def add_documents(
        self,
        documents: List[str],
        ids: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ):
        """添加文档到向量库"""
        if metadata is None:
            metadata = [{}] * len(documents)

        self.collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadata
        )

    def query(
        self,
        query_texts: List[str],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """查询向量库"""
        results = self.collection.query(
            query_texts=query_texts,
            n_results=n_results,
            where=where,
            where_document=where_document
        )

        return results

    def get(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取文档"""
        return self.collection.get(
            ids=ids,
            where=where,
            limit=limit
        )

    def delete(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None
    ):
        """删除文档"""
        self.collection.delete(ids=ids, where=where)

    def count(self) -> int:
        """获取文档数量"""
        return self.collection.count()

    def peek(self, limit: int = 10) -> Dict[str, Any]:
        """预览文档"""
        return self.collection.peek(limit=limit)


class VectorStoreAdapter:
    """向量存储适配器 - 支持多种后端"""

    def __init__(self, project_path: str, backend: str = "simple"):
        self.project_path = Path(project_path).resolve()
        self.backend = backend

        if backend == "chromadb":
            if not CHROMADB_AVAILABLE:
                print("WARNING: ChromaDB not available, falling back to simple backend")
                self.backend = "simple"
            else:
                self.chroma = ChromaVectorStore(project_path)
        else:
            self.chroma = None

    def add_documents(
        self,
        documents: List[str],
        ids: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ):
        """添加文档"""
        if self.backend == "chromadb" and self.chroma:
            self.chroma.add_documents(documents, ids, metadata)

    def query(
        self,
        query_texts: List[str],
        n_results: int = 10
    ) -> Dict[str, Any]:
        """查询文档"""
        if self.backend == "chromadb" and self.chroma:
            return self.chroma.query(query_texts, n_results)
        return {"results": [], "distances": []}

    def get(self, ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """获取文档"""
        if self.backend == "chromadb" and self.chroma:
            return self.chroma.get(ids=ids)
        return {"documents": [], "ids": [], "metadatas": []}

    def delete(self, ids: Optional[List[str]] = None):
        """删除文档"""
        if self.backend == "chromadb" and self.chroma:
            self.chroma.delete(ids=ids)

    def count(self) -> int:
        """获取文档数量"""
        if self.backend == "chromadb" and self.chroma:
            return self.chroma.count()
        return 0


def is_chromadb_available() -> bool:
    """检查 ChromaDB 是否可用"""
    return CHROMADB_AVAILABLE


if __name__ == "__main__":
    print(f"ChromaDB available: {is_chromadb_available()}")

    if CHROMADB_AVAILABLE:
        print("Testing ChromaDB backend...")
        adapter = VectorStoreAdapter("/tmp/test", backend="chromadb")
        print(f"Documents: {adapter.count()}")
