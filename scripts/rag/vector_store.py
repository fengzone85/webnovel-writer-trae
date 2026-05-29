#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG Vector Store - 向量检索模块
集成 ModelScope Embedding API 和 Jina AI Rerank API
"""

import json
import os
import sys
import urllib.request
import urllib.error
import urllib.parse
import gzip
from io import BytesIO
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# 修复 Windows 编码问题
if sys.platform == "win32":
    try:
        os.system("chcp 65001")
    except:
        pass
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass


class VectorStore:
    """向量存储与检索系统"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        self.vector_dir = self.project_path / ".webnovel" / "vectors"
        self.vector_dir.mkdir(parents=True, exist_ok=True)

        # 加载配置
        self.config = self._load_config()

        # API 配置
        self.embed_base_url = self.config.get("EMBED_BASE_URL", "https://api-inference.modelscope.cn/v1")
        self.embed_model = self.config.get("EMBED_MODEL", "Qwen/Qwen3-Embedding-8B")
        self.embed_api_key = self.config.get("EMBED_API_KEY", "")

        self.rerank_base_url = self.config.get("RERANK_BASE_URL", "https://api.jina.ai")
        self.rerank_model = self.config.get("RERANK_MODEL", "jina-reranker-v3")
        self.rerank_api_key = self.config.get("RERANK_API_KEY", "")

        # Jina AI 专用代理
        self.jina_proxy = self.config.get("JINA_PROXY", "")

        # 向量索引
        self.vector_index = self._load_vector_index()

        # 标记是否使用模拟模式
        self.use_mock = False
        if not self.embed_api_key or "your_" in self.embed_api_key.lower():
            self.use_mock = True
            print("INFO: EMBED_API_KEY not configured, will use mock embedding")

    def _load_config(self) -> Dict[str, str]:
        """加载配置"""
        config = {}
        env_file = self.project_path / ".env"
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        return config

    def _load_vector_index(self) -> Dict[str, Any]:
        """加载向量索引"""
        index_file = self.vector_dir / "vector_index.json"
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "documents": [],
            "index_version": "1.0",
            "last_updated": ""
        }

    def _save_vector_index(self):
        """保存向量索引"""
        index_file = self.vector_dir / "vector_index.json"
        self.vector_index["last_updated"] = datetime.now().isoformat()
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(self.vector_index, f, ensure_ascii=False, indent=2)

    def _make_api_request(self, url: str, headers: dict, payload: dict = None, timeout: int = 60, use_proxy: bool = False) -> Dict[str, Any]:
        """发送 API 请求

        Args:
            url: 请求 URL
            headers: 请求头
            payload: 请求数据
            timeout: 超时时间
            use_proxy: 是否使用代理（用于 Jina AI）
        """
        try:
            if payload:
                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            else:
                req = urllib.request.Request(url, headers=headers, method='GET')

            # 如果需要使用代理，设置代理处理器
            if use_proxy and self.jina_proxy:
                proxy_handler = urllib.request.ProxyHandler({
                    'http': self.jina_proxy,
                    'https': self.jina_proxy
                })
                opener = urllib.request.build_opener(proxy_handler)
            else:
                opener = urllib.request.build_opener()

            with opener.open(req, timeout=timeout) as response:
                # 处理 gzip 压缩响应
                content_encoding = response.headers.get('Content-Encoding', '')
                response_bytes = response.read()
                
                if content_encoding == 'gzip':
                    response_data = gzip.GzipFile(fileobj=BytesIO(response_bytes)).read().decode('utf-8')
                else:
                    response_data = response_bytes.decode('utf-8')
                
                return {
                    "status": "success",
                    "data": json.loads(response_data)
                }
        except urllib.error.HTTPError as e:
            try:
                details = e.read().decode('utf-8') if e.fp else ""
            except:
                details = ""
            return {
                "status": "error",
                "error": f"HTTP Error {e.code}: {e.reason}",
                "http_status": e.code,
                "details": details
            }
        except urllib.error.URLError as e:
            return {
                "status": "error",
                "error": f"Connection Error: {e.reason}"
            }
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "error": f"JSON Decode Error: {e}"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Unexpected error: {type(e).__name__}: {e}"
            }

    def _get_embedding(self, text: str) -> List[float]:
        """获取文本嵌入向量"""
        # 如果使用模拟模式，返回模拟向量
        if self.use_mock:
            return [0.0] * 768

        try:
            url = f"{self.embed_base_url}/embeddings"
            headers = {
                "Authorization": f"Bearer {self.embed_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.embed_model,
                "input": text,
                "encoding_format": "float"
            }

            # ModelScope 不使用代理
            result = self._make_api_request(url, headers, payload, use_proxy=False)

            if result["status"] == "success":
                response_data = result["data"]
                if "data" in response_data and len(response_data["data"]) > 0:
                    return response_data["data"][0]["embedding"]
                else:
                    print(f"ERROR: Invalid response format from embedding API: {response_data}")
            else:
                print(f"ERROR: Embedding API request failed: {result.get('error')}")
                # 如果是 503 错误，切换到模拟模式
                if result.get("http_status") == 503:
                    print("INFO: Service temporarily unavailable, switching to mock embedding")
                    self.use_mock = True

        except Exception as e:
            print(f"ERROR in _get_embedding: {type(e).__name__}: {e}")

        # 返回默认向量
        return [0.0] * 768

    def _rerank(self, query: str, documents: List[str], top_k: int = 5) -> List[Tuple[int, float]]:
        """重排序文档 - 使用 Jina AI Rerank API"""
        if self.use_mock or not self.rerank_api_key or "your_" in self.rerank_api_key.lower() or len(documents) == 0:
            return [(i, 1.0 - i * 0.1) for i in range(min(top_k, len(documents)))]
        
        try:
            # Jina AI Rerank API 正确端点: /v1/rerank
            url = f"{self.rerank_base_url}/v1/rerank"

            headers = {
                "Authorization": f"Bearer {self.rerank_api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Origin": "https://jina.ai",
                "Referer": "https://jina.ai/"
            }

            # Jina AI rerank API 使用 POST 请求
            payload = {
                "model": self.rerank_model,
                "query": query,
                "documents": documents,
                "top_n": top_k
            }

            # Jina AI 使用代理（如果配置了）
            use_proxy = bool(self.jina_proxy)
            result = self._make_api_request(url, headers, payload, use_proxy=use_proxy)

            if result["status"] == "success":
                response_data = result["data"]
                if "results" in response_data:
                    return [(r["index"], r["relevance_score"]) for r in response_data["results"]]
                elif "data" in response_data and isinstance(response_data["data"], list):
                    return [(r["index"], r["relevance_score"]) for r in response_data["data"]]
                else:
                    print(f"ERROR: Invalid response format from rerank API: {response_data}")
            else:
                print(f"ERROR: Rerank API request failed: {result.get('error')}")
                if use_proxy:
                    print("      代理可能有问题，请检查 JINA_PROXY 配置")

        except Exception as e:
            print(f"ERROR in _rerank: {type(e).__name__}: {e}")

        return [(i, 1.0 - i * 0.1) for i in range(min(top_k, len(documents)))]

    def add_document(self, content: str, metadata: Dict[str, Any]):
        """添加文档到向量存储"""
        embedding = self._get_embedding(content)

        doc_id = f"doc_{len(self.vector_index['documents'])}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        document = {
            "id": doc_id,
            "content": content[:500],
            "full_content": content,
            "embedding": embedding,
            "metadata": metadata,
            "created_at": datetime.now().isoformat()
        }

        self.vector_index["documents"].append(document)
        self._save_vector_index()

        return doc_id

    def add_chapter(self, chapter_num: int, content: str):
        """添加章节到向量存储"""
        metadata = {
            "type": "chapter",
            "chapter": chapter_num,
            "source": "chapter"
        }
        return self.add_document(content, metadata)

    def add_setting(self, setting_type: str, content: str):
        """添加设定到向量存储"""
        metadata = {
            "type": "setting",
            "setting_type": setting_type,
            "source": "setting"
        }
        return self.add_document(content, metadata)

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if not vec1 or not vec2 or len(vec1) == 0 or len(vec2) == 0:
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def search(self, query: str, top_k: int = 5, use_rerank: bool = True) -> List[Dict[str, Any]]:
        """搜索相关文档"""
        if not self.vector_index["documents"]:
            return []

        query_embedding = self._get_embedding(query)

        results = []
        for doc in self.vector_index["documents"]:
            similarity = self._cosine_similarity(query_embedding, doc["embedding"])
            if similarity > 0.01:  # 降低阈值以获取更多结果
                results.append({
                    "document": doc,
                    "similarity": similarity
                })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        top_results = results[:top_k * 2]

        if use_rerank and top_results and not self.use_mock:
            documents = [r["document"]["full_content"] for r in top_results]
            rerank_results = self._rerank(query, documents, top_k)

            final_results = []
            for idx, score in rerank_results:
                doc_info = top_results[idx]["document"]
                final_results.append({
                    "id": doc_info["id"],
                    "content": doc_info["content"],
                    "metadata": doc_info["metadata"],
                    "similarity": score,
                    "source": doc_info["metadata"].get("source", "unknown")
                })
        else:
            final_results = [{
                "id": r["document"]["id"],
                "content": r["document"]["content"],
                "metadata": r["document"]["metadata"],
                "similarity": r["similarity"],
                "source": r["document"]["metadata"].get("source", "unknown")
            } for r in top_results[:top_k]]

        return final_results

    def search_by_type(self, query: str, doc_type: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """按类型搜索"""
        results = self.search(query, top_k * 2)
        filtered = [r for r in results if r["metadata"].get("type") == doc_type]
        return filtered[:top_k]

    def search_characters(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """搜索角色相关信息"""
        return self.search_by_type(query, "setting", top_k)

    def search_chapters(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索章节相关内容"""
        return self.search_by_type(query, "chapter", top_k)

    def build_index(self):
        """构建向量索引（从现有文件）"""
        settings_dir = self.project_path / "设定集"
        if settings_dir.exists():
            count = 0
            for setting_file in settings_dir.glob("*.md"):
                try:
                    with open(setting_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        self.add_setting(setting_file.stem, content)
                        count += 1
                except Exception as e:
                    print(f"ERROR: Failed to index {setting_file}: {e}")
            print(f"Indexed {count} setting files")

        chapters_dir = self.project_path / "章节"
        if chapters_dir.exists():
            count = 0
            for chapter_file in chapters_dir.glob("Ch*.md"):
                try:
                    chapter_num = int(chapter_file.stem[2:])
                    with open(chapter_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        self.add_chapter(chapter_num, content)
                        count += 1
                except Exception as e:
                    print(f"ERROR: Failed to index {chapter_file}: {e}")
            print(f"Indexed {count} chapters")

        print(f"Vector index built successfully, {len(self.vector_index['documents'])} documents total")

    def get_index_stats(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        docs = self.vector_index["documents"]
        by_type = {}
        for doc in docs:
            doc_type = doc["metadata"].get("type", "unknown")
            by_type[doc_type] = by_type.get(doc_type, 0) + 1

        return {
            "total_documents": len(docs),
            "by_type": by_type,
            "last_updated": self.vector_index["last_updated"],
            "index_version": self.vector_index["index_version"],
            "use_mock": self.use_mock,
            "jina_proxy_configured": bool(self.jina_proxy)
        }


def test_vector_store():
    """测试向量存储"""
    vs = VectorStore(".")
    print("Vector Store initialized")
    print(f"Config loaded: {vs.config}")
    print(f"Using mock mode: {vs.use_mock}")
    print(f"Jina proxy configured: {bool(vs.jina_proxy)}")
    print(f"Index stats: {vs.get_index_stats()}")

    # 测试构建索引
    vs.build_index()
    print(f"After build: {vs.get_index_stats()}")

    # 测试搜索
    results = vs.search("主角")
    print(f"Search results for '主角': {len(results)}")
    for i, result in enumerate(results[:3]):
        print(f"  {i+1}. Similarity: {result['similarity']:.4f}, Type: {result['metadata'].get('type')}")


if __name__ == "__main__":
    test_vector_store()
